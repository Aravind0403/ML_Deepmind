#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$ROOT_DIR/backups"
mkdir -p "$BACKUP_DIR"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="$BACKUP_DIR/ml_command_center_private_${STAMP}.tar.gz"

tar -czf "$OUT" -C "$ROOT_DIR" \
  $( [ -f "$ROOT_DIR/db/progress.sqlite" ] && echo "db/progress.sqlite" ) \
  $( [ -d "$ROOT_DIR/private" ] && echo "private" )

echo "Created local private snapshot: $OUT"
ls -lh "$OUT"
