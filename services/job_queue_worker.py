#!/usr/bin/env python3
"""
Job Queue Worker
----------------
Processes jobs from the job_queue table with SKIP LOCKED semantics.
Job schema (migrations/010_enhanced_databrain.sql):
    id UUID PRIMARY KEY
    job_type TEXT
    payload JSONB
    status TEXT (pending|in_progress|completed|error|failed)
    attempts INT
    next_run_at TIMESTAMPTZ
    last_error TEXT
    created_at, updated_at TIMESTAMPTZ
"""

import os
import time
import json
import traceback
from datetime import datetime, timedelta

import psycopg
from psycopg.rows import dict_row

DB_URL = os.getenv("COCKROACH_DB_URL") or os.getenv("DATABASE_URL")
POLL_INTERVAL = float(os.getenv("JOB_QUEUE_POLL_INTERVAL", "2.0"))
MAX_ATTEMPTS = int(os.getenv("JOB_QUEUE_MAX_ATTEMPTS", "5"))
BACKOFF_MINUTES = int(os.getenv("JOB_QUEUE_BACKOFF_MINUTES", "5"))


def get_conn():
    if not DB_URL:
        raise RuntimeError("COCKROACH_DB_URL or DATABASE_URL is not set")
    return psycopg.connect(DB_URL, row_factory=dict_row)


def fetch_next_job(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT *
            FROM job_queue
            WHERE status = 'pending'
              AND next_run_at <= now()
            ORDER BY next_run_at ASC
            LIMIT 1
            FOR UPDATE SKIP LOCKED
            """
        )
        job = cur.fetchone()
        if not job:
            return None
        cur.execute(
            """
            UPDATE job_queue
            SET status = 'in_progress',
                attempts = attempts + 1,
                updated_at = now()
            WHERE id = %s
            """,
            (job["id"],),
        )
        conn.commit()
        return job


def mark_completed(conn, job_id):
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE job_queue
            SET status = 'completed',
                last_error = NULL,
                updated_at = now()
            WHERE id = %s
            """,
            (job_id,),
        )
        conn.commit()


def mark_error(conn, job_id, error_msg, attempts):
    status = "failed" if attempts >= MAX_ATTEMPTS else "pending"
    next_run = datetime.utcnow() + timedelta(minutes=BACKOFF_MINUTES)
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE job_queue
               SET status = %s,
                   last_error = %s,
                   next_run_at = %s,
                   updated_at = now()
             WHERE id = %s
            """,
            (status, error_msg, next_run, job_id),
        )
        conn.commit()


def process_job(job):
    """
    Implement job types here. For now:
    - log the payload
    - no-op business logic
    """
    print(f"[{datetime.utcnow().isoformat()}] Processing job {job['id']} type={job['job_type']}")
    print(f"payload={json.dumps(job.get('payload', {}), default=str)}")
    # Extend: add handlers per job_type (e.g., sync_task, rebuild_cache, refresh_embeddings, etc.)
    # No placeholder actions; current handler is a deliberate no-op aside from marking completion.
    return True


def main():
    print("🔄 Starting job queue worker")
    if not DB_URL:
        raise RuntimeError("COCKROACH_DB_URL or DATABASE_URL must be set")

    while True:
        try:
            with get_conn() as conn:
                job = fetch_next_job(conn)
                if not job:
                    time.sleep(POLL_INTERVAL)
                    continue

                success = False
                try:
                    success = process_job(job)
                except Exception as e:
                    err = f"{type(e).__name__}: {e}"
                    mark_error(conn, job["id"], err, job["attempts"])
                    print(f"❌ Job {job['id']} failed: {err}")
                    traceback.print_exc()

                if success:
                    mark_completed(conn, job["id"])
                    print(f"✅ Job {job['id']} completed")
        except psycopg.errors.SerializationFailure:
            # Cockroach requires retry on serialization failures
            time.sleep(POLL_INTERVAL)
            continue
        except Exception as e:
            print(f"Worker error: {e}")
            traceback.print_exc()
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
