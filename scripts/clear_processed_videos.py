#!/usr/bin/env python3
"""Clear all processed videos from the database.

This script removes all entries from the processed_videos table,
allowing videos to be reprocessed from scratch.

Usage:
    python scripts/clear_processed_videos.py          # Interactive mode
    python scripts/clear_processed_videos.py --force  # Force mode (no confirmation)
"""

import argparse
import os
import sqlite3
import sys
from pathlib import Path


def get_db_path() -> Path:
    """Get the path to the database file."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    return project_root / "data" / "processed_videos.db"


def get_row_count(db_path: Path) -> int:
    """Get the current number of rows in the processed_videos table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM processed_videos")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def clear_table(db_path: Path) -> bool:
    """Delete all rows from the processed_videos table.

    Returns:
        True if successful, False otherwise.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM processed_videos")
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error clearing table: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Clear all processed videos from the database"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt"
    )
    args = parser.parse_args()

    # Get database path
    db_path = get_db_path()

    # Check if database exists
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}", file=sys.stderr)
        sys.exit(1)

    # Show current row count
    print("Checking current database state...")
    try:
        current_count = get_row_count(db_path)
    except Exception as e:
        print(f"Error reading database: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Current rows in processed_videos table: {current_count}")

    # Check if table is already empty
    if current_count == 0:
        print("Table is already empty. Nothing to delete.")
        sys.exit(0)

    # Ask for confirmation unless --force flag is provided
    if not args.force:
        response = input(f"Delete all {current_count} rows? (y/N) ")
        if response.lower() not in ['y', 'yes']:
            print("Cancelled.")
            sys.exit(0)

    # Delete all rows
    print("Deleting all rows from processed_videos table...")
    if not clear_table(db_path):
        print("Failed to clear table", file=sys.stderr)
        sys.exit(1)

    # Verify deletion
    new_count = get_row_count(db_path)
    print(f"Done! Rows remaining: {new_count}")

    if new_count == 0:
        print("✓ All processed videos cleared successfully")
    else:
        print(f"⚠ Warning: Expected 0 rows but found {new_count}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
