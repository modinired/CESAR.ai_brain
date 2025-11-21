"""
Database connection and utilities
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from contextlib import contextmanager

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mcp_user:change-this-in-production-use-strong-password@postgres:5432/mcp"
)

def get_connection():
    """Get a database connection"""
    return psycopg2.connect(DATABASE_URL)

def get_db():
    """Get a database connection with context management"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

@contextmanager
def get_db_cursor(dict_cursor=False):
    """Context manager for database cursor"""
    conn = get_connection()
    cursor_factory = RealDictCursor if dict_cursor else None
    cursor = conn.cursor(cursor_factory=cursor_factory)
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
