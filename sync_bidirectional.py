#!/usr/bin/env python3
"""
CESAR Ecosystem: Bi-Directional Database Synchronization
========================================================
Syncs data between Local PostgreSQL and CockroachDB with conflict resolution

FEATURES:
- Two-way sync (Local ↔ CockroachDB)
- Timestamp-based conflict resolution
- Incremental sync (only changed records)
- Dry-run mode for safety
- Detailed sync statistics

USAGE:
    python3 sync_bidirectional.py                    # Normal sync
    python3 sync_bidirectional.py --dry-run          # Preview changes
    python3 sync_bidirectional.py --direction=up     # Local → CockroachDB only
    python3 sync_bidirectional.py --direction=down   # CockroachDB → Local only
    python3 sync_bidirectional.py --table=agents     # Sync single table

SCHEDULING:
    Add to crontab for automatic sync:
    */5 * * * * cd /path/to/cesar_ecosystem && python3 sync_bidirectional.py >> /var/log/cesar_sync.log 2>&1
"""

import os
import sys
import argparse
from datetime import datetime, timezone
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment
load_dotenv()
load_dotenv(".env.cockroach")

# Configuration
LOCAL_DB = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "dbname": os.getenv("POSTGRES_DB", "mcp"),
    "user": os.getenv("POSTGRES_USER", "mcp_user"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}

COCKROACH_URL = os.getenv("COCKROACH_DB_URL")

# Tables to sync (in dependency order)
SYNC_TABLES = [
    "agents",
    "sessions",
    "a2a_conversations",
    "a2a_messages",
    "llm_collaborations",
    "tasks",
]

class SyncStats:
    def __init__(self):
        self.uploaded = 0
        self.downloaded = 0
        self.conflicts = 0
        self.skipped = 0
        self.errors = 0

    def report(self):
        print("\n" + "=" * 80)
        print("SYNCHRONIZATION COMPLETE")
        print("=" * 80)
        print(f"  ⬆️  Uploaded (Local → CockroachDB):   {self.uploaded}")
        print(f"  ⬇️  Downloaded (CockroachDB → Local): {self.downloaded}")
        print(f"  ⚔️  Conflicts Resolved:               {self.conflicts}")
        print(f"  ⏭️  Skipped (No Changes):             {self.skipped}")
        print(f"  ❌ Errors:                            {self.errors}")
        print("=" * 80)

def get_last_sync_time(conn, table_name, direction):
    """Get timestamp of last sync for a table"""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sync_state (
                    table_name VARCHAR(255),
                    direction VARCHAR(10),
                    last_sync_at TIMESTAMPTZ,
                    PRIMARY KEY (table_name, direction)
                )
            """)
            conn.commit()

            cur.execute(
                "SELECT last_sync_at FROM sync_state WHERE table_name = %s AND direction = %s",
                (table_name, direction)
            )
            result = cur.fetchone()
            return result[0] if result else None
    except Exception as e:
        print(f"   Warning: Could not read sync state: {e}")
        return None

def update_sync_time(conn, table_name, direction):
    """Update last sync timestamp"""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO sync_state (table_name, direction, last_sync_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (table_name, direction) DO UPDATE
                SET last_sync_at = EXCLUDED.last_sync_at
            """, (table_name, direction, datetime.now(timezone.utc)))
            conn.commit()
    except Exception as e:
        print(f"   Warning: Could not update sync state: {e}")

def get_changed_records(conn, table_name, since):
    """Fetch records changed since last sync"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        if since:
            cur.execute(
                f"SELECT * FROM {table_name} WHERE updated_at > %s",
                (since,)
            )
        else:
            # First sync - get all records
            cur.execute(f"SELECT * FROM {table_name}")

        return cur.fetchall()

def upsert_record(conn, table_name, record, stats, dry_run=False):
    """Insert or update a record with conflict resolution"""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if record exists
            primary_key = get_primary_key(table_name)
            cur.execute(
                f"SELECT updated_at FROM {table_name} WHERE {primary_key} = %s",
                (record[primary_key],)
            )
            existing = cur.fetchone()

            if existing:
                # Conflict resolution: Use most recent timestamp
                local_time = record.get('updated_at')
                remote_time = existing['updated_at']

                if local_time and remote_time:
                    if local_time <= remote_time:
                        stats.skipped += 1
                        return  # Remote is newer, skip
                    else:
                        stats.conflicts += 1

            # Build UPSERT query
            columns = list(record.keys())
            placeholders = ", ".join(["%s"] * len(columns))
            column_names = ", ".join(columns)

            update_clause = ", ".join([f"{col} = EXCLUDED.{col}" for col in columns if col != primary_key])

            query = f"""
                INSERT INTO {table_name} ({column_names})
                VALUES ({placeholders})
                ON CONFLICT ({primary_key}) DO UPDATE SET {update_clause}
            """

            if dry_run:
                print(f"   [DRY RUN] Would upsert {primary_key}={record[primary_key]}")
            else:
                cur.execute(query, list(record.values()))
                conn.commit()

    except Exception as e:
        print(f"   ❌ Error upserting record: {e}")
        stats.errors += 1
        conn.rollback()

def get_primary_key(table_name):
    """Get primary key column name for a table"""
    # Simple mapping (could be enhanced to query INFORMATION_SCHEMA)
    pk_map = {
        "agents": "id",
        "sessions": "id",
        "a2a_messages": "id",
        "a2a_conversations": "id",
        "llm_collaborations": "id",
        "tasks": "id",
    }
    return pk_map.get(table_name, "id")

def sync_table(local_conn, cloud_conn, table_name, direction, stats, dry_run=False):
    """Sync a single table in specified direction"""
    print(f"\n📦 Syncing table: {table_name}")

    if direction in ["up", "both"]:
        # Local → CockroachDB
        print("   ⬆️  Uploading changes to CockroachDB...")

        last_sync = get_last_sync_time(local_conn, table_name, "up")
        if last_sync:
            print(f"      Last sync: {last_sync}")

        changed_records = get_changed_records(local_conn, table_name, last_sync)
        print(f"      Found {len(changed_records)} changed records")

        for record in changed_records:
            upsert_record(cloud_conn, table_name, record, stats, dry_run)
            stats.uploaded += 1

        if not dry_run:
            update_sync_time(local_conn, table_name, "up")

    if direction in ["down", "both"]:
        # CockroachDB → Local
        print("   ⬇️  Downloading changes from CockroachDB...")

        last_sync = get_last_sync_time(cloud_conn, table_name, "down")
        if last_sync:
            print(f"      Last sync: {last_sync}")

        changed_records = get_changed_records(cloud_conn, table_name, last_sync)
        print(f"      Found {len(changed_records)} changed records")

        for record in changed_records:
            upsert_record(local_conn, table_name, record, stats, dry_run)
            stats.downloaded += 1

        if not dry_run:
            update_sync_time(cloud_conn, table_name, "down")

def main():
    parser = argparse.ArgumentParser(description="CESAR Bi-Directional Database Sync")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    parser.add_argument("--direction", choices=["up", "down", "both"], default="both", help="Sync direction")
    parser.add_argument("--table", help="Sync only specified table")
    args = parser.parse_args()

    # Validate configuration
    if not COCKROACH_URL or COCKROACH_URL == "pending":
        print("❌ Error: COCKROACH_DB_URL not configured")
        sys.exit(1)

    print("=" * 80)
    print("CESAR ECOSYSTEM: BI-DIRECTIONAL DATABASE SYNC")
    print("=" * 80)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Direction: {args.direction.upper()}")
    if args.table:
        print(f"Table Filter: {args.table}")
    print("")

    stats = SyncStats()

    try:
        # Connect to databases
        print("🔌 Connecting to Local PostgreSQL...")
        local_conn = psycopg2.connect(**LOCAL_DB)
        print("✅ Connected")

        print("🔌 Connecting to CockroachDB...")
        cloud_conn = psycopg2.connect(COCKROACH_URL)
        print("✅ Connected")

        # Determine tables to sync
        tables_to_sync = [args.table] if args.table else SYNC_TABLES

        # Sync each table
        for table in tables_to_sync:
            try:
                sync_table(local_conn, cloud_conn, table, args.direction, stats, args.dry_run)
            except Exception as e:
                print(f"   ❌ Error syncing {table}: {e}")
                stats.errors += 1

        # Close connections
        local_conn.close()
        cloud_conn.close()

        # Report statistics
        stats.report()

        if args.dry_run:
            print("\nℹ️  This was a DRY RUN. No changes were made.")
            print("   Remove --dry-run flag to perform actual sync.")

        sys.exit(0 if stats.errors == 0 else 1)

    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
