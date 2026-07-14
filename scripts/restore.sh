#!/bin/bash
# TURBO-CDI Disaster Recovery — Database Restore Script
# Usage: ./scripts/restore.sh <backup_file.dump>
#   or set RESTORE_FILE env var: RESTORE_FILE=/backups/turbo-cdi/turbo_cdi_20261028_020000.dump ./scripts/restore.sh

set -euo pipefail

DB_NAME="${DB_NAME:-turbo_cdi}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-turbo_cdi}"
BACKUP_DIR="${BACKUP_DIR:-/backups/turbo-cdi}"

RESTORE_FILE="${1:-${RESTORE_FILE:-}}"

if [ -z "$RESTORE_FILE" ]; then
    echo "No restore file provided. Searching $BACKUP_DIR for latest backup..."
    RESTORE_FILE=$(ls -1t "$BACKUP_DIR"/${DB_NAME}_*.dump 2>/dev/null | head -1)
    if [ -z "$RESTORE_FILE" ]; then
        echo "ERROR: No backup files found in $BACKUP_DIR" >&2
        exit 1
    fi
    echo "Found latest backup: $RESTORE_FILE"
fi

if [ ! -f "$RESTORE_FILE" ]; then
    echo "ERROR: Backup file not found: $RESTORE_FILE" >&2
    exit 1
fi

echo "=== RESTORE STARTED at $(date) ==="
echo "Target DB: $DB_HOST:$DB_PORT/$DB_NAME"
echo "Backup file: $RESTORE_FILE ($(du -h "$RESTORE_FILE" | cut -f1))"

echo "Dropping and recreating database..."
PGPASSWORD="${DB_PASSWORD}" dropdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" --if-exists "$DB_NAME"
PGPASSWORD="${DB_PASSWORD}" createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"

echo "Restoring from backup..."
PGPASSWORD="${DB_PASSWORD}" pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v "$RESTORE_FILE"

if [ $? -eq 0 ]; then
    echo "=== RESTORE COMPLETED SUCCESSFULLY at $(date) ==="
else
    echo "=== RESTORE FAILED at $(date) ===" >&2
    exit 1
fi
