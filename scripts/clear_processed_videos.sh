#!/bin/bash
# Clear all processed videos from the database
# This script removes all entries from the processed_videos table,
# allowing videos to be reprocessed from scratch.

set -e

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DB_PATH="$PROJECT_ROOT/data/processed_videos.db"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "Error: Database not found at $DB_PATH"
    exit 1
fi

# Show current row count
echo "Checking current database state..."
CURRENT_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM processed_videos;")
echo "Current rows in processed_videos table: $CURRENT_COUNT"

# Confirm before deleting
if [ "$CURRENT_COUNT" -eq 0 ]; then
    echo "Table is already empty. Nothing to delete."
    exit 0
fi

# Ask for confirmation unless --force flag is provided
if [ "$1" != "--force" ]; then
    read -p "Delete all $CURRENT_COUNT rows? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
fi

# Delete all rows
echo "Deleting all rows from processed_videos table..."
sqlite3 "$DB_PATH" "DELETE FROM processed_videos;"

# Verify deletion
NEW_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM processed_videos;")
echo "Done! Rows remaining: $NEW_COUNT"

if [ "$NEW_COUNT" -eq 0 ]; then
    echo "✓ All processed videos cleared successfully"
else
    echo "⚠ Warning: Expected 0 rows but found $NEW_COUNT"
    exit 1
fi
