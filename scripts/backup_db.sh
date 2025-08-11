#!/usr/bin/env bash
set -euo pipefail

DB_PATH=${DB_PATH:-"backend/contacts.db"}
BACKUP_DIR=${BACKUP_DIR:-"backups"}
RETENTION=${RETENTION:-7}

mkdir -p "$BACKUP_DIR"

TS=$(date +%Y%m%d-%H%M%S)
BASENAME=$(basename "$DB_PATH")
TARGET="$BACKUP_DIR/${BASENAME%.db}-$TS.db"

if [ ! -f "$DB_PATH" ]; then
  echo "Database not found at $DB_PATH" >&2
  exit 1
fi

# Use sqlite3 backup if available; fallback to copy
if command -v sqlite3 >/dev/null 2>&1; then
  sqlite3 "$DB_PATH" ".backup '$TARGET'"
else
  cp -f "$DB_PATH" "$TARGET"
fi

echo "Created backup: $TARGET"

# Retention: keep newest N backups
ls -1t "$BACKUP_DIR" | grep -E "${BASENAME%.db}-[0-9]{8}-[0-9]{6}\.db$" | tail -n +$((RETENTION+1)) | while read -r f; do
  rm -f "$BACKUP_DIR/$f" || true
  echo "Removed old backup: $BACKUP_DIR/$f"
done