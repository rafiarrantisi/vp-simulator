#!/usr/bin/env bash
# Qora local dev — seeds a demo user, starts backend (:8000) + frontend (:5173).
# Usage:  bash scripts/dev.sh
set -e
root="$(cd "$(dirname "$0")/.." && pwd)"
py="$root/backend/.venv/Scripts/python.exe"   # Windows venv layout
[ -x "$py" ] || py="$root/backend/.venv/bin/python"   # POSIX fallback

echo "[dev] seeding demo user (demo@qora.app / demo1234)..."
( cd "$root/backend" && "$py" -m scripts.seed_dev_user )

echo "[dev] starting backend -> http://localhost:8000"
( cd "$root/backend" && "$py" -m uvicorn app.main:app --port 8000 ) &

echo "[dev] starting frontend -> http://localhost:5173  (login demo@qora.app / demo1234)"
cd "$root/sistemnya"
VITE_API_BASE=http://localhost:8000 npm run dev
