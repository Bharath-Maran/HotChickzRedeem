# Hot Chickz Redemption System

Full-stack offer redemption app for **Hot Chickz** (Fort Wayne, IN).  
Phases 2–5 of the GHL → SMS → Claim flow.

---

## Architecture

```
GHL (Phase 1) → SMS with ?code={contact_id}
                        │
                        ▼
        hotchickzoffer.com/claim-offer?code=…
                        │
              ┌─────────┴──────────┐
              │  React SPA         │  Vercel
              │  (frontend/)       │
              └─────────┬──────────┘
                        │ /api/*
                        ▼
              ┌─────────────────────┐
              │  FastAPI backend    │  Render.com
              │  (backend/)         │
              └─────────┬───────────┘
                        │
                        ▼
              ┌─────────────────────┐
              │  Supabase           │  PostgreSQL
              │  slider_claims      │
              └─────────────────────┘
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Node.js | 20+ |
| npm | 10+ |

---

## Phase 2 — Database (Supabase)

1. Create a free project at [supabase.com](https://supabase.com).
2. Go to **SQL Editor → New Query**, paste the contents of `database/schema.sql`, and run it.
3. Copy your **Connection String (URI)** from **Settings → Database**. It looks like:
   ```
   postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres
   ```

---

## Phase 3 — Backend (FastAPI)

```bash
cd backend
cp .env.example .env         # fill in DATABASE_URL and ALLOWED_ORIGINS
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload    # http://localhost:8000
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check |
| `GET` | `/api/claim-status?code=…` | Query current state |
| `POST` | `/api/start-timer` | Begin 7-day window |
| `POST` | `/api/redeem` | Complete at register |

---

## Phase 4 — Frontend (React + Vite)

```bash
cd frontend
cp .env.example .env.local   # set VITE_API_URL for production (leave blank for dev)
npm install
npm run dev                  # http://localhost:5173
```

Open `http://localhost:5173/?code=TEST_ID` to test the full flow locally (the Vite proxy routes `/api` to `:8000`).

### Screens

| Status | Screen |
|--------|--------|
| `unclaimed` | Offer details + **Claim Now** button |
| `active_timer` | Live 7-day countdown + **Redeem at Register** → confirmation modal |
| `claimed` | Digital receipt |
| `expired` | Expired message |
| _(invalid URL)_ | Error screen |

---

## Phase 5 — Deployment

### Backend → Render.com

1. Push this repo to GitHub.
2. **New Web Service** on [render.com](https://render.com) → connect the repo.
3. Set the **Root Directory** to `backend/`.
4. Render auto-detects `render.yaml` — review and confirm.
5. Add env vars in **Environment** tab:
   - `DATABASE_URL` — your Supabase URI
   - `ALLOWED_ORIGINS` — `https://hotchickzoffer.com`
   - `USE_SSL` — `true`
6. Note your service URL (e.g. `https://hotchickz-api.onrender.com`).

### Frontend → Vercel

1. **Add New Project** on [vercel.com](https://vercel.com) → import the same repo.
2. Set the **Root Directory** to `frontend/`.
3. Vercel auto-detects Vite — defaults are correct.
4. Add env var:
   - `VITE_API_URL` — your Render backend URL (e.g. `https://hotchickz-api.onrender.com`)
5. Add your custom domain `hotchickzoffer.com` in **Settings → Domains**.

### DNS Configuration

In your domain registrar, add the record Vercel shows you:

```
Type    Name    Value
CNAME   @       cname.vercel-dns.com.   (or A record if registrar requires)
```

> **GHL conflict note:** If GHL also uses `hotchickzoffer.com` for the `/claim` landing page, point GHL to a subdomain (e.g. `lp.hotchickzoffer.com`) so the root domain exclusively serves the React app.

---

## Local End-to-End Test

```bash
# Terminal 1 — backend
cd backend && source .venv/bin/activate && uvicorn main:app --reload

# Terminal 2 — frontend
cd frontend && npm run dev

# Browser
open "http://localhost:5173/?code=TEST_ABC123"
```

Walk through: Claim Now → countdown screen → modal → claimed receipt.

---

## Security Notes

- GHL contact IDs are ≥16-char random alphanumeric strings — brute-force is impractical.
- The backend rejects any `contact_id` that doesn't match `[A-Za-z0-9_-]{1,255}`.
- State transitions are atomic SQL `UPDATE … WHERE status = 'X'` — no race conditions.
- CORS is locked to the domains in `ALLOWED_ORIGINS`.
- `Allow Multiple` is **off** in GHL — one code per phone number.
