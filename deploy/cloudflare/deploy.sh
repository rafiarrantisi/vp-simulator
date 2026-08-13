#!/usr/bin/env bash
# Deploy Qora frontend ke Cloudflare Pages (migrasi dari Vercel)
# Usage: deploy/cloudflare/deploy.sh
# Prereq: CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID di env
# Note: wrangler auto-detect functions/ dari CWD — makanya cd ke sini dulu.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DIST="$ROOT/sistemnya/dist"
HERE="$(cd "$(dirname "$0")" && pwd)"

if [ -z "${CLOUDFLARE_API_TOKEN:-}" ] || [ -z "${CLOUDFLARE_ACCOUNT_ID:-}" ]; then
  echo "ERROR: set CLOUDFLARE_API_TOKEN dan CLOUDFLARE_ACCOUNT_ID dulu"
  exit 1
fi

echo "==> Build frontend (Vite)"
(cd "$ROOT/sistemnya" && npm run build)

echo "==> Deploy ke Pages (project: qoramedical)"
cd "$HERE"
npx --yes wrangler@4 pages deploy "$DIST" \
  --project-name qoramedical \
  --branch main

echo "==> Done. Production: https://qoramedical.com"
