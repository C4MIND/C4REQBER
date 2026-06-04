#!/bin/bash
# TURBO-CDI Database Backup Script
# Run via cron: 0 2 * * * /app/scripts/backup.sh

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups/turbo-cdi}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="${DB_NAME:-turbo_cdi}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-turbo_cdi}"

mkdir -p "$BACKUP_DIR"

PGPASSWORD="${DB_PASSWORD}" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -Fc \
  > "$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.dump"

if [ $? -eq 0 ]; then
    echo "Backup successful: ${DB_NAME}_${TIMESTAMP}.dump ($(du -h "$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.dump" | cut -f1))"

    find "$BACKUP_DIR" -name "${DB_NAME}_*.dump" -mtime +$RETENTION_DAYS -delete
    echo "Cleaned backups older than $RETENTION_DAYS days"
else
    echo "Backup FAILED at $(date)" >&2
    exit 1
fi
