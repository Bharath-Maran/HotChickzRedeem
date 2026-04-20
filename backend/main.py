"""
Hot Chickz Redemption API
FastAPI + asyncpg  •  Supabase (PostgreSQL) backend

Endpoints
---------
GET  /health                          Health check
POST /api/pre-register                GHL workflow webhook: whitelist a contact
GET  /api/status?code=…               Query current redemption state
GET  /api/offer-status?code=…         Alias — same as /api/status
GET  /api/claim-status?code=…         Alias — same as /api/status
POST /api/start-timer                 Begin the 7-day claim window
POST /api/redeem                      Complete the redemption at the register
POST /api/redeem-offer                Alias — same as /api/redeem

Table: offer_claims
  contact_id       VARCHAR(255) PRIMARY KEY
  status           VARCHAR(50)  DEFAULT 'unclaimed'  -- unclaimed | active_timer | claimed | expired
  timer_started_at TIMESTAMP WITH TIME ZONE
  expires_at       TIMESTAMP WITH TIME ZONE
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

# Shared secret between GHL workflow Action 1 and this API.
# GHL workflow → Webhook action → Headers → Key: x-api-key | Value: <this>
# Set PRE_REGISTER_API_KEY on Render → Environment to the same value.
PRE_REGISTER_API_KEY: str = os.getenv("PRE_REGISTER_API_KEY", "")
if not PRE_REGISTER_API_KEY:
    log.warning(
        "PRE_REGISTER_API_KEY is not set — /api/pre-register is unprotected. "
        "Set this env var on Render immediately."
    )

# GHL contact IDs: alphanumeric + hyphens/underscores, 1–255 chars
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


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/pre-register  — The Bouncer
#
# Called by GHL workflow Action 1 immediately after the Facebook Lead Form is
# submitted, BEFORE the SMS/email is sent. Whitelists the contact_id with
# status 'unclaimed' so the frontend will accept it when the user clicks.
#
# Security: x-api-key header must match PRE_REGISTER_API_KEY.
# Idempotent — safe to call multiple times for the same contact.
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/pre-register")
async def pre_register(
    payload: ContactPayload,
    x_api_key: str | None = Header(default=None),
):
    if PRE_REGISTER_API_KEY and x_api_key != PRE_REGISTER_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    db = _require_pool()
    async with db.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO offer_claims (contact_id, status)
            VALUES ($1, 'unclaimed')
            ON CONFLICT (contact_id) DO NOTHING
            """,
            payload.contact_id,
        )
    log.info("pre-register: whitelisted contact %s", payload.contact_id)
    return {"status": "registered"}


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/status  — The Checker
#
# Called by the frontend on page load to determine which screen to show.
# Returns 404 for any contact_id not in the database (= fabricated link).
# Automatically transitions active_timer → expired server-side.
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/status")
async def get_status(code: str = Query(..., max_length=255)):
    contact_id = _validate_contact_id(code)
    db = _require_pool()

    async with db.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT status, expires_at FROM offer_claims WHERE contact_id = $1",
            contact_id,
        )

        # Not in DB → never pre-registered by GHL → fabricated link
        if row is None:
            raise HTTPException(status_code=404, detail="Contact not found")

        # Server-side expiry transition
        if row["status"] == "active_timer":
            is_expired: bool = await conn.fetchval(
                "SELECT NOW() > expires_at FROM offer_claims WHERE contact_id = $1",
                contact_id,
            )
            if is_expired:
                await conn.execute(
                    """
                    UPDATE offer_claims
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


# Aliases — frontend calls /api/offer-status; both work without code changes
@app.get("/api/offer-status")
async def offer_status(code: str = Query(..., max_length=255)):
    return await get_status(code=code)

@app.get("/api/claim-status")
async def claim_status(code: str = Query(..., max_length=255)):
    return await get_status(code=code)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/start-timer  — The Trigger
#
# Fired when the user taps "Claim My Free Slider".
# Only succeeds when status is 'unclaimed' — prevents double-activation.
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/start-timer")
async def start_timer(payload: ContactPayload):
    db = _require_pool()

    async with db.acquire() as conn:
        result: str = await conn.execute(
            """
            UPDATE offer_claims
            SET status           = 'active_timer',
                timer_started_at = NOW(),
                expires_at       = NOW() + INTERVAL '7 days'
            WHERE contact_id = $1 AND status = 'unclaimed'
            """,
            payload.contact_id,
        )

        if result == "UPDATE 0":
            row = await conn.fetchrow(
                "SELECT status FROM offer_claims WHERE contact_id = $1",
                payload.contact_id,
            )
            detail = (
                "Contact not found" if row is None
                else f"Cannot start timer: status is '{row['status']}'"
            )
            raise HTTPException(status_code=409, detail=detail)

        row = await conn.fetchrow(
            "SELECT expires_at FROM offer_claims WHERE contact_id = $1",
            payload.contact_id,
        )
        return {"status": "active_timer", "expires_at": row["expires_at"].isoformat()}


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/redeem  — The Lockout
#
# Fired when the user confirms redemption at the register.
# Only succeeds when status = 'active_timer' AND timer has not expired.
# Once claimed the row is permanently locked — the link cannot be reused.
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/redeem")
async def redeem(payload: ContactPayload):
    db = _require_pool()

    async with db.acquire() as conn:
        result: str = await conn.execute(
            """
            UPDATE offer_claims
            SET status = 'claimed'
            WHERE contact_id = $1
              AND status     = 'active_timer'
              AND NOW()      < expires_at
            """,
            payload.contact_id,
        )

        if result == "UPDATE 0":
            row = await conn.fetchrow(
                "SELECT status, expires_at FROM offer_claims WHERE contact_id = $1",
                payload.contact_id,
            )
            if row is None:
                raise HTTPException(status_code=404, detail="Contact not found")
            if row["status"] == "claimed":
                raise HTTPException(status_code=409, detail="Offer already claimed")
            if row["status"] == "expired" or (
                row["expires_at"] and await conn.fetchval(
                    "SELECT NOW() > $1", row["expires_at"]
                )
            ):
                raise HTTPException(status_code=410, detail="Offer has expired")
            raise HTTPException(
                status_code=409, detail=f"Cannot redeem: status is '{row['status']}'"
            )

        log.info("redeemed: contact %s", payload.contact_id)
        return {"status": "claimed"}


# Alias — frontend calls /api/redeem-offer
@app.post("/api/redeem-offer")
async def redeem_offer(payload: ContactPayload):
    return await redeem(payload)
