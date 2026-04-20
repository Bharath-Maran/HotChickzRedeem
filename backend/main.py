"""
Hot Chickz Redemption API
FastAPI + asyncpg  •  Supabase (PostgreSQL) backend

Endpoints
---------
GET  /health                         Health check
GET  /api/claim-status?code=…        Query current redemption state
GET  /api/offer-status?code=…        Alias (spec name) — same as claim-status
POST /api/start-timer                Begin the 7-day claim window
POST /api/register                   GHL webhook: pre-register + activate code
POST /api/redeem                     Complete the redemption at the register
POST /api/redeem-offer               Alias (spec name) — same as redeem
"""

import logging
import os
import re
from contextlib import asynccontextmanager

import asyncpg
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("hotchickz")

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

DATABASE_URL: str = os.environ.get("DATABASE_URL", "")
USE_SSL: bool = os.getenv("USE_SSL", "true").lower() == "true"
ALLOWED_ORIGINS: list[str] = [
    o.strip()
    for o in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,https://hotchickzoffer.com"
    ).split(",")
    if o.strip()
]

# Webhook secret — GHL must send this in X-Webhook-Secret header when calling
# /api/register. Prevents arbitrary contact IDs being registered by outsiders.
REGISTER_WEBHOOK_SECRET: str = os.getenv("REGISTER_WEBHOOK_SECRET", "")
if not REGISTER_WEBHOOK_SECRET:
    log.warning(
        "REGISTER_WEBHOOK_SECRET is not set. "
        "/api/register is unprotected — set this env var immediately."
    )

# GHL contact IDs are alphanumeric + hyphens/underscores, up to 255 chars
_CONTACT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,255}$")

# ── Database pool ─────────────────────────────────────────────────────────────

pool: asyncpg.Pool | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool

    if not DATABASE_URL:
        print("STARTUP FAILED: DATABASE_URL environment variable is not set.", flush=True)
        print("Go to Render → your service → Environment tab and add DATABASE_URL.", flush=True)
        raise RuntimeError("DATABASE_URL not set")

    print(f"Connecting to database (SSL={USE_SSL})...", flush=True)
    try:
        ssl_param = "require" if USE_SSL else False
        pool = await asyncpg.create_pool(
            DATABASE_URL, ssl=ssl_param, min_size=1, max_size=5
        )
        print("Database pool ready. Starting server.", flush=True)
    except Exception as exc:
        print(f"STARTUP FAILED: could not connect to database: {exc}", flush=True)
        raise

    yield

    if pool:
        await pool.close()
        print("Database pool closed.", flush=True)


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="Hot Chickz Redemption API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _require_pool() -> asyncpg.Pool:
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not initialised")
    return pool


def _validate_contact_id(contact_id: str) -> str:
    if not _CONTACT_ID_RE.match(contact_id):
        raise HTTPException(status_code=400, detail="Invalid contact ID format")
    return contact_id


# ── Schemas ───────────────────────────────────────────────────────────────────

class ContactPayload(BaseModel):
    contact_id: str

    @field_validator("contact_id")
    @classmethod
    def _validate(cls, v: str) -> str:
        if not _CONTACT_ID_RE.match(v):
            raise ValueError("Invalid contact ID format")
        return v


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/claim-status")
async def claim_status(code: str = Query(..., max_length=255)):
    """
    Return the current state for a GHL contact ID.

    States returned: unclaimed | active_timer | claimed | expired

    Returns 404 if the contact ID was never registered via /api/register
    (i.e. it was not sent by a genuine GHL workflow).

    Side-effects:
    - Transitions 'active_timer' → 'expired' when the timer has elapsed.
    """
    contact_id = _validate_contact_id(code)
    db = _require_pool()

    async with db.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT status, expires_at FROM slider_claims WHERE contact_id = $1",
            contact_id,
        )

        if row is None:
            # Contact ID was never registered by GHL — treat as invalid link.
            # Do NOT auto-insert: that would let anyone claim a free slider
            # with an arbitrary contact ID.
            raise HTTPException(status_code=404, detail="Contact not found")

        # Check for server-side expiry transition
        if row["status"] == "active_timer":
            is_expired: bool = await conn.fetchval(
                "SELECT NOW() > expires_at FROM slider_claims WHERE contact_id = $1",
                contact_id,
            )
            if is_expired:
                await conn.execute(
                    """
                    UPDATE slider_claims
                    SET status = 'expired'
                    WHERE contact_id = $1 AND status = 'active_timer'
                    """,
                    contact_id,
                )
                return {"status": "expired", "expires_at": None}

        return {
            "status": row["status"],
            "expires_at": row["expires_at"].isoformat() if row["expires_at"] else None,
        }


@app.post("/api/start-timer")
async def start_timer(payload: ContactPayload):
    """
    Begin the 7-day claim window.
    Only succeeds when the current status is 'unclaimed'.
    """
    db = _require_pool()

    async with db.acquire() as conn:
        result: str = await conn.execute(
            """
            UPDATE slider_claims
            SET status           = 'active_timer',
                timer_started_at = NOW(),
                expires_at       = NOW() + INTERVAL '7 days'
            WHERE contact_id = $1 AND status = 'unclaimed'
            """,
            payload.contact_id,
        )

        if result == "UPDATE 0":
            row = await conn.fetchrow(
                "SELECT status FROM slider_claims WHERE contact_id = $1",
                payload.contact_id,
            )
            detail = "Contact not found" if row is None else f"Cannot start timer: status is '{row['status']}'"
            raise HTTPException(status_code=409, detail=detail)

        row = await conn.fetchrow(
            "SELECT expires_at FROM slider_claims WHERE contact_id = $1",
            payload.contact_id,
        )
        return {"status": "active_timer", "expires_at": row["expires_at"].isoformat()}


@app.get("/api/offer-status")
async def offer_status(code: str = Query(..., max_length=255)):
    """
    Alias for /api/claim-status — used by the GHL funnel page.
    """
    return await claim_status(code=code)


@app.post("/api/redeem-offer")
async def redeem_offer(payload: ContactPayload):
    """
    Alias for /api/redeem — used by the GHL funnel page.
    """
    return await redeem(payload)


@app.post("/api/register")
async def register(
    payload: ContactPayload,
    x_webhook_secret: str | None = Header(default=None),
):
    """
    Pre-register a contact from a GHL workflow webhook.
    Requires the X-Webhook-Secret header to match REGISTER_WEBHOOK_SECRET.
    Idempotent — safe to call multiple times for the same contact.
    """
    # Enforce webhook secret when one is configured
    if REGISTER_WEBHOOK_SECRET and x_webhook_secret != REGISTER_WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")
    db = _require_pool()

    async with db.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO slider_claims (contact_id, status, timer_started_at, expires_at)
            VALUES ($1, 'active_timer', NOW(), NOW() + INTERVAL '7 days')
            ON CONFLICT (contact_id) DO UPDATE
              SET status           = 'active_timer',
                  timer_started_at = NOW(),
                  expires_at       = NOW() + INTERVAL '7 days'
            WHERE slider_claims.status = 'unclaimed'
            """,
            payload.contact_id,
        )

    return {"status": "registered", "expires_in_days": 7}


@app.post("/api/redeem")
async def redeem(payload: ContactPayload):
    """
    Mark the offer as claimed at the register.
    Only succeeds when status is 'active_timer' AND the timer has not expired.
    """
    db = _require_pool()

    async with db.acquire() as conn:
        result: str = await conn.execute(
            """
            UPDATE slider_claims
            SET status = 'claimed'
            WHERE contact_id = $1
              AND status     = 'active_timer'
              AND NOW()      < expires_at
            """,
            payload.contact_id,
        )

        if result == "UPDATE 0":
            row = await conn.fetchrow(
                "SELECT status, expires_at FROM slider_claims WHERE contact_id = $1",
                payload.contact_id,
            )
            if row is None:
                raise HTTPException(status_code=404, detail="Contact not found")
            if row["status"] == "claimed":
                raise HTTPException(status_code=409, detail="Offer already claimed")
            if row["status"] == "expired" or (
                row["expires_at"] and await conn.fetchval("SELECT NOW() > $1", row["expires_at"])
            ):
                raise HTTPException(status_code=410, detail="Offer has expired")
            raise HTTPException(status_code=409, detail=f"Cannot redeem: status is '{row['status']}'")

        return {"status": "claimed"}
