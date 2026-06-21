# Run Qora locally

A one-machine setup: the AI runs on your local LLM key (DeepSeek via OpenRouter);
no payment/email/OAuth keys are needed to use the prototype.

## Prerequisites (one-time)
- **Backend:** `backend/.venv` with deps installed (`python -m venv .venv` then `pip install -r requirements.txt`).
- **Frontend:** `cd sistemnya && npm install`.
- **Config:** `backend/.env` with `LLM_API_KEY` (real AI; without it the app uses a deterministic StubLLM). `sistemnya/.env` with `VITE_API_BASE=http://localhost:8000`.

## Fastest path
```
# Windows PowerShell
./scripts/dev.ps1
# or Git Bash
bash scripts/dev.sh
```
This seeds a demo user, starts the backend on **:8000**, and the frontend on **:5173**.

## Manual (two terminals)
```
# Terminal 1 — backend
cd backend
./.venv/Scripts/python.exe -m scripts.seed_dev_user          # once: demo@qora.app / demo1234
./.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000

# Terminal 2 — frontend  (sistemnya/.env already sets VITE_API_BASE)
cd sistemnya
npm run dev                                                  # http://localhost:5173
```

## Log in
Open http://localhost:5173 → log in with **demo@qora.app / demo1234** (or sign up).

## Notes
- CORS: the backend allows `http://localhost:5173` by default (`app/config.py` `cors_origins`); keep the frontend on 5173.
- Billing is OFF in the prototype (`billing_enforced=false`) — every case is unlocked.
- External services are deferred plug-ins — see `docs/PROTOTYPE_AND_PLUGINS.md`.
- Backend tests: `cd backend && ./.venv/Scripts/python.exe -m pytest -q`. Case lint: `python -m tools.lint_case --all`.
