#!/usr/bin/env bash
# Deploy Qora frontend ke Cloudflare Pages (migrasi dari Vercel)
# Usage: deploy/cloudflare/deploy.sh
# Prereq: CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID di env
# Note: wrangler auto-detect functions/ dari CWD — makanya cd ke sini dulu.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DIST="$ROOT/sistemnya/dist"
HERE="$(cd "$(dirname "$0")" && pwd)"

if [ -z "${CLOUDFLARE_API_TOKEN:-}" ]; then
  echo "ERROR: set CLOUDFLARE_API_TOKEN dulu"
  exit 1
fi
# Account ID default (public value, non-secret) — override via env bila perlu.
CLOUDFLARE_ACCOUNT_ID="${CLOUDFLARE_ACCOUNT_ID:-dfb8dfad9b1f5822a996e99cc2c0e9da}"

echo "==> Build frontend (Vite)"
# Guard: dev-only .env.local (VITE_API_BASE=http://localhost:8010) must NOT be
# baked into the production bundle — delete it if present (gitignored, dev-only).
rm -f "$ROOT/sistemnya/.env.local"
(cd "$ROOT/sistemnya" && npm run build)

echo "==> Deploy ke Pages (project: qoramedical)"
cd "$HERE"
npx --yes wrangler@4 pages deploy "$DIST" \
  --project-name qoramedical \
  --branch main

echo "==> Done. Production: https://qoramedical.com"
