#!/usr/bin/env bash
# Deploy Qora frontend ke Cloudflare Pages (migrasi dari Vercel)
# Usage: deploy/cloudflare/deploy.sh
# Prereq: CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID di env
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DIST="$ROOT/sistemnya/dist"
FUNCS="$(dirname "$0")/functions"

if [ -z "${CLOUDFLARE_API_TOKEN:-}" ] || [ -z "${CLOUDFLARE_ACCOUNT_ID:-}" ]; then
  echo "ERROR: set CLOUDFLARE_API_TOKEN dan CLOUDFLARE_ACCOUNT_ID dulu"
  exit 1
fi

echo "==> Build frontend (Vite)"
(cd "$ROOT/sistemnya" && npm run build)

echo "==> Deploy ke Pages (project: qoramedical)"
npx --yes wrangler@4 pages deploy "$DIST" \
  --project-name qoramedical \
  --branch main \
  --functions "$FUNCS"

echo "==> Done. Production: https://qoramedical.com"
