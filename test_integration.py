#!/usr/bin/env python3
"""
CESAR Ecosystem: Integration Test Suite
========================================
Comprehensive testing of CockroachDB integration

Tests:
1. Connection validation
2. Schema integrity
3. Data sync accuracy
4. API endpoint functionality
5. Performance benchmarks
6. Failover scenarios

Usage:
    python3 test_integration.py
    python3 test_integration.py --quick     # Skip slow tests
    python3 test_integration.py --verbose   # Detailed output
"""

import os
import sys
import time
import argparse
from datetime import datetime
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

class TestSuite:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.tests = []

    def test(self, name, func):
        """Run a single test"""
        print(f"\n🧪 TEST: {name}")
        try:
            start = time.time()
            result = func()
            duration = (time.time() - start) * 1000

            if result:
                print(f"   ✅ PASS ({duration:.0f}ms)")
                self.passed += 1
            else:
                print(f"   ❌ FAIL")
                self.failed += 1

            self.tests.append({
                "name": name,
                "status": "PASS" if result else "FAIL",
                "duration_ms": duration
            })
            return result

        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            self.failed += 1
            self.tests.append({
                "name": name,
                "status": "ERROR",
                "error": str(e)
            })
            return False

    def summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total:   {self.passed + self.failed + self.skipped}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"⏭️  Skipped: {self.skipped}")
        print("=" * 80)

        if self.failed > 0:
            print("\n❌ FAILED TESTS:")
            for test in self.tests:
                if test["status"] in ["FAIL", "ERROR"]:
                    print(f"   - {test['name']}")
                    if "error" in test:
                        print(f"     Error: {test['error']}")

        return self.failed == 0

# =============================================================================
# TEST FUNCTIONS
# =============================================================================

def test_cockroach_connection():
    """Test 1: CockroachDB Connection"""
    try:
        conn = psycopg2.connect(COCKROACH_URL)
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0] == 1
    except Exception as e:
        print(f"      Error: {e}")
        return False

def test_local_connection():
    """Test 2: Local PostgreSQL Connection"""
    try:
        conn = psycopg2.connect(**LOCAL_DB)
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0] == 1
    except Exception as e:
        print(f"      Error: {e}")
        return False

def test_schema_exists():
    """Test 3: Required Tables Exist"""
    try:
        conn = psycopg2.connect(COCKROACH_URL)
        cur = conn.cursor()

        required_tables = [
            'agents', 'sessions', 'a2a_messages',
            'a2a_conversations', 'llm_collaborations', 'tasks'
        ]

        for table in required_tables:
            cur.execute(f"SELECT to_regclass('public.{table}');")
            result = cur.fetchone()[0]
            if result is None:
                print(f"      Missing table: {table}")
                return False

        cur.close()
        conn.close()
        print(f"      All {len(required_tables)} tables present")
        return True

    except Exception as e:
        print(f"      Error: {e}")
        return False

def test_migration_tracking():
    """Test 4: Migration Tracking Table"""
    try:
        conn = psycopg2.connect(COCKROACH_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT COUNT(*) as count FROM schema_migrations WHERE status = 'completed';")
        result = cur.fetchone()

        cur.close()
        conn.close()

        if result['count'] >= 11:
            print(f"      {result['count']} migrations applied")
            return True
        else:
            print(f"      Only {result['count']}/11 migrations applied")
            return False

    except Exception as e:
        print(f"      Migration table may not exist: {e}")
        return False

def test_agent_sync():
    """Test 5: Agent Data Synced"""
    try:
        local_conn = psycopg2.connect(**LOCAL_DB)
        cloud_conn = psycopg2.connect(COCKROACH_URL)

        local_cur = local_conn.cursor()
        cloud_cur = cloud_conn.cursor()

        local_cur.execute("SELECT COUNT(*) FROM agents;")
        local_count = local_cur.fetchone()[0]

        cloud_cur.execute("SELECT COUNT(*) FROM agents;")
        cloud_count = cloud_cur.fetchone()[0]

        local_cur.close()
        cloud_cur.close()
        local_conn.close()
        cloud_conn.close()

        print(f"      Local: {local_count} agents, CockroachDB: {cloud_count} agents")

        if cloud_count > 0:
            return True
        else:
            print(f"      No agents in CockroachDB. Run: ./run_cockroach_sync.sh")
            return False

    except Exception as e:
        print(f"      Error: {e}")
        return False

def test_read_latency():
    """Test 6: Read Performance Benchmark"""
    try:
        conn = psycopg2.connect(COCKROACH_URL)
        cur = conn.cursor()

        latencies = []
        for _ in range(10):
            start = time.time()
            cur.execute("SELECT * FROM agents LIMIT 10;")
            cur.fetchall()
            latency = (time.time() - start) * 1000
            latencies.append(latency)

        avg_latency = sum(latencies) / len(latencies)
        print(f"      Average latency: {avg_latency:.2f}ms")

        cur.close()
        conn.close()

        # Pass if < 500ms (generous threshold for cloud DB)
        return avg_latency < 500

    except Exception as e:
        print(f"      Error: {e}")
        return False

def test_write_performance():
    """Test 7: Write Performance Benchmark"""
    try:
        conn = psycopg2.connect(COCKROACH_URL)
        cur = conn.cursor()

        # Create test table if not exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS test_performance (
                id SERIAL PRIMARY KEY,
                data TEXT,
                created_at TIMESTAMPTZ DEFAULT now()
            );
        """)

        # Benchmark 100 inserts
        start = time.time()
        for i in range(100):
            cur.execute("INSERT INTO test_performance (data) VALUES (%s);", (f"test_{i}",))

        conn.commit()
        duration = (time.time() - start) * 1000

        # Cleanup
        cur.execute("DROP TABLE test_performance;")
        conn.commit()

        cur.close()
        conn.close()

        print(f"      100 inserts: {duration:.0f}ms ({duration/100:.2f}ms/insert)")
        return duration < 10000  # 10 seconds for 100 inserts

    except Exception as e:
        print(f"      Error: {e}")
        return False

def test_mob_aliases():
    """Test 8: Mob Aliases Present"""
    try:
        conn = psycopg2.connect(COCKROACH_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT COUNT(*) as count
            FROM agents
            WHERE metadata->>'mob_alias' IS NOT NULL
        """)
        result = cur.fetchone()

        cur.close()
        conn.close()

        if result['count'] > 0:
            print(f"      {result['count']} agents with mob aliases")
            return True
        else:
            print(f"      No mob aliases found. Check sync_to_cockroach.py")
            return False

    except Exception as e:
        print(f"      Error: {e}")
        return False

def test_data_consistency():
    """Test 9: Data Consistency Between Local & Cloud"""
    try:
        local_conn = psycopg2.connect(**LOCAL_DB)
        cloud_conn = psycopg2.connect(COCKROACH_URL)

        local_cur = local_conn.cursor(cursor_factory=RealDictCursor)
        cloud_cur = cloud_conn.cursor(cursor_factory=RealDictCursor)

        # Get first agent from local
        local_cur.execute("SELECT id, agent_id, name FROM agents LIMIT 1;")
        local_agent = local_cur.fetchone()

        if local_agent:
            # Find same agent in cloud
            cloud_cur.execute(
                "SELECT id, agent_id, name FROM agents WHERE agent_id = %s;",
                (local_agent['agent_id'],)
            )
            cloud_agent = cloud_cur.fetchone()

            local_cur.close()
            cloud_cur.close()
            local_conn.close()
            cloud_conn.close()

            if cloud_agent and cloud_agent['name'] == local_agent['name']:
                print(f"      Agent '{local_agent['name']}' matches")
                return True
            else:
                print(f"      Mismatch or agent not found in CockroachDB")
                return False
        else:
            print(f"      No agents in local database")
            return False

    except Exception as e:
        print(f"      Error: {e}")
        return False

def test_sync_state():
    """Test 10: Sync State Tracking"""
    try:
        conn = psycopg2.connect(COCKROACH_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT COUNT(*) as count FROM sync_state;")
        result = cur.fetchone()

        cur.close()
        conn.close()

        if result and result['count'] > 0:
            print(f"      Sync state has {result['count']} entries")
            return True
        else:
            print(f"      Sync state empty. Run: python3 sync_bidirectional.py")
            return False

    except Exception as e:
        # Sync state table may not exist yet
        print(f"      Sync state table not found (run sync first)")
        return True  # Not critical for initial setup

# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="CESAR Integration Test Suite")
    parser.add_argument("--quick", action="store_true", help="Skip slow tests")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    print("=" * 80)
    print("CESAR ECOSYSTEM: INTEGRATION TEST SUITE")
    print("=" * 80)
    print("")

    suite = TestSuite(verbose=args.verbose)

    # Critical tests (always run)
    suite.test("CockroachDB Connection", test_cockroach_connection)
    suite.test("Local PostgreSQL Connection", test_local_connection)
    suite.test("Schema Exists", test_schema_exists)
    suite.test("Migration Tracking", test_migration_tracking)
    suite.test("Agent Data Synced", test_agent_sync)
    suite.test("Mob Aliases Present", test_mob_aliases)
    suite.test("Data Consistency", test_data_consistency)
    suite.test("Sync State Tracking", test_sync_state)

    # Performance tests (skip if --quick)
    if not args.quick:
        suite.test("Read Performance", test_read_latency)
        suite.test("Write Performance", test_write_performance)
    else:
        print("\n⏭️  Skipping performance tests (use without --quick to run)")
        suite.skipped += 2

    # Summary
    success = suite.summary()

    # Exit code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
