#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"
export PYTHONDONTWRITEBYTECODE=1

if [ ! -f "$ROOT_DIR/db/progress.sqlite" ]; then
  echo "[init] Building & verifying local SQLite database..."
  python3 scripts/build_and_verify.py
fi

# Load optional .env keys if present
if [ -f "$ROOT_DIR/.env" ]; then
  set -a
  source "$ROOT_DIR/.env"
  set +a
fi

echo "[start] Launching FastAPI backend on http://127.0.0.1:8000 ..."
uvicorn backend.main:app --host 127.0.0.1 --port 8000 &
BACK_PID=$!

echo "[start] Launching Next.js frontend on http://localhost:3000 ..."
(cd "$ROOT_DIR/frontend" && NEXT_TELEMETRY_DISABLED=1 npx next dev --turbopack -p 3000 --disable-source-maps) &
FRONT_PID=$!

cleanup() {
  echo ""
  echo "[stop] Shutting down local ML Command Center..."
  kill "$BACK_PID" "$FRONT_PID" 2>/dev/null || true
}
trap cleanup INT TERM

echo ""
echo "=============================================================="
echo "  ML Command Center (Local-First Private Mode)"
echo "  App:     http://localhost:3000"
echo "  API:     http://127.0.0.1:8000/docs"
echo "  Press Ctrl+C to stop both servers cleanly."
echo "=============================================================="
wait
