"""
Hot Chickz Redemption API
FastAPI + asyncpg  •  Supabase (PostgreSQL) backend

Endpoints
---------
GET  /health                    Health check
GET  /api/claim-status?code=…   Query current redemption state
POST /api/start-timer           Begin the 7-day claim window
POST /api/redeem                Complete the redemption at the register
"""

import os
import re
import ssl as _ssl
from contextlib import asynccontextmanager

import asyncpg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

DATABASE_URL: str = os.environ["DATABASE_URL"]  # fail fast if missing
USE_SSL: bool = os.getenv("USE_SSL", "true").lower() == "true"
ALLOWED_ORIGINS: list[str] = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]

# GHL contact IDs are alphanumeric + hyphens/underscores, up to 255 chars
_CONTACT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,255}$")

# ── Database pool ─────────────────────────────────────────────────────────────

pool: asyncpg.Pool | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    ssl_param: str | bool = "require" if USE_SSL else False
    pool = await asyncpg.create_pool(DATABASE_URL, ssl=ssl_param, min_size=1, max_size=5)
    yield
    if pool:
        await pool.close()


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

    Side-effects:
    - Inserts an 'unclaimed' row the first time a valid code is seen.
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
            # First visit — create the record
            await conn.execute(
                """
                INSERT INTO slider_claims (contact_id, status)
                VALUES ($1, 'unclaimed')
                ON CONFLICT DO NOTHING
                """,
                contact_id,
            )
            return {"status": "unclaimed", "expires_at": None}

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
