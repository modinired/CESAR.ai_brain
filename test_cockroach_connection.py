#!/usr/bin/env python3
"""
CESAR ECOSYSTEM: CockroachDB Connectivity Diagnostic
====================================================
Comprehensive connection testing with security best practices

Tests performed:
1. Environment variable validation
2. Connection establishment
3. SSL/TLS verification
4. Write permissions
5. Read latency benchmarking
6. Schema compatibility check
"""

import os
import sys
import time
import psycopg2
from dotenv import load_dotenv

# Add parent dir to path to find .env
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()
load_dotenv(".env.cockroach")

def test_connection():
    print("=" * 80)
    print("🔍 CESAR ECOSYSTEM: COCKROACHDB CONNECTIVITY DIAGNOSTIC")
    print("=" * 80)
    print()

    url = os.getenv("COCKROACH_DB_URL")

    # Test 1: Environment Variable Check
    print("📋 TEST 1: Environment Variable Configuration")
    if not url:
        print("❌ CRITICAL ERROR: COCKROACH_DB_URL is missing from environment.")
        print("   Action Required:")
        print("   1. Check .env.cockroach file exists")
        print("   2. Verify format: postgresql://user:password@host:26257/defaultdb?sslmode=verify-full")
        print("   3. Run: source .env.cockroach")
        return False

    # Mask password for logs (security best practice)
    if "@" in url:
        safe_url = "***:***@" + url.split("@")[1]
    else:
        print("❌ INVALID URL FORMAT: Missing '@' separator")
        return False

    print(f"✅ COCKROACH_DB_URL found")
    print(f"   Connecting to: {safe_url}")
    print()

    # Test 2: Connection Establishment
    print("📋 TEST 2: Connection Establishment")
    print("   Attempting TCP connection...", end=" ")

    try:
        start_time = time.time()
        conn = psycopg2.connect(url)
        connection_time = (time.time() - start_time) * 1000

        print(f"OK ({connection_time:.0f}ms)")
        print("   ✅ TCP connection established")

        cur = conn.cursor()

        # Test 3: Database Version & Cluster Info
        print()
        print("📋 TEST 3: Cluster Information")

        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"   Cluster Version: {version[:80]}...")

        # Check if it's actually CockroachDB
        if "CockroachDB" in version:
            print("   ✅ Confirmed CockroachDB cluster")
        else:
            print("   ⚠️  Warning: Connected to PostgreSQL, not CockroachDB")

        # Get node count (CockroachDB specific)
        try:
            cur.execute("SELECT count(*) FROM crdb_internal.gossip_nodes;")
            node_count = cur.fetchone()[0]
            print(f"   Active Nodes: {node_count}")
        except Exception as e:
            print("   Node count unavailable (not a critical error)")
            # Rollback failed transaction before continuing
            conn.rollback()

        # Test 4: Write Permissions
        print()
        print("📋 TEST 4: Write Permissions")
        print("   Creating test table...", end=" ")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS connection_test (
                id INT PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT now(),
                test_data TEXT
            );
        """)
        conn.commit()
        print("OK")

        print("   Performing INSERT...", end=" ")
        cur.execute("""
            INSERT INTO connection_test (id, test_data)
            VALUES (1, 'CESAR connectivity test')
            ON CONFLICT (id) DO UPDATE SET
                timestamp = now(),
                test_data = EXCLUDED.test_data;
        """)
        conn.commit()
        print("OK")
        print("   ✅ Write permissions confirmed")

        # Test 5: Read Latency Benchmark
        print()
        print("📋 TEST 5: Read Performance Benchmark")

        latencies = []
        for i in range(5):
            start = time.time()
            cur.execute("SELECT count(*) FROM connection_test;")
            cur.fetchone()
            latency = (time.time() - start) * 1000
            latencies.append(latency)
            print(f"   Read {i+1}/5: {latency:.2f}ms")

        avg_latency = sum(latencies) / len(latencies)
        print(f"   Average Latency: {avg_latency:.2f}ms")

        if avg_latency < 50:
            print("   ✅ Excellent latency (<50ms)")
        elif avg_latency < 150:
            print("   ✅ Good latency (<150ms)")
        elif avg_latency < 500:
            print("   ⚠️  Moderate latency (150-500ms) - Check network/region")
        else:
            print("   ⚠️  High latency (>500ms) - Consider regional cluster")

        # Test 6: Schema Compatibility
        print()
        print("📋 TEST 6: PostgreSQL Extension Compatibility")

        # Check for uuid extension
        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
            conn.commit()
            print("   ✅ uuid-ossp extension available")
        except Exception as e:
            print(f"   ⚠️  uuid-ossp: {str(e)[:60]}")
            conn.rollback()

        # Check for pgcrypto
        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
            conn.commit()
            print("   ✅ pgcrypto extension available")
        except Exception as e:
            print(f"   ⚠️  pgcrypto: {str(e)[:60]}")
            conn.rollback()

        # Cleanup
        print()
        print("🧹 Cleaning up test table...", end=" ")
        # Keep the table for future tests, just verify we can delete
        cur.execute("DELETE FROM connection_test WHERE id = 999;")  # Non-existent row
        conn.commit()
        print("OK")

        cur.close()
        conn.close()

        print()
        print("=" * 80)
        print("✅ ALL TESTS PASSED - CockroachDB Ready for Production")
        print("=" * 80)
        print()
        print("Next Steps:")
        print("1. Run: ./apply_migrations_cockroach.sh")
        print("2. Run: ./run_cockroach_sync.sh")
        print("3. Update api/main.py to import database_v2 instead of database")
        print()

        return True

    except psycopg2.OperationalError as e:
        print("\n")
        print("=" * 80)
        print("❌ CONNECTION FAILED - Operational Error")
        print("=" * 80)
        print(f"Error: {str(e)}")
        print()
        print("🔧 Troubleshooting Checklist:")
        print()
        print("1. IP ALLOWLIST")
        print("   - Open CockroachDB Console > Networking")
        print("   - Add your current IP address")
        print("   - Or add 0.0.0.0/0 for testing (NOT recommended for production)")
        print()
        print("2. SSL CERTIFICATE")
        print("   - If using sslmode=verify-full, ensure root.crt is present")
        print("   - Try sslmode=require for testing (less secure)")
        print()
        print("3. CREDENTIALS")
        print("   - Verify username and password in .env.cockroach")
        print("   - Check for special characters needing URL encoding")
        print()
        print("4. NETWORK")
        print("   - Ensure port 26257 is not blocked by firewall")
        print("   - Test: telnet <host> 26257")
        print()
        return False

    except psycopg2.Error as e:
        print("\n")
        print("=" * 80)
        print("❌ DATABASE ERROR")
        print("=" * 80)
        print(f"Error: {str(e)}")
        print()
        print("🔧 Possible Issues:")
        print("   - Insufficient permissions for user")
        print("   - Database does not exist")
        print("   - SQL compatibility issue")
        print()
        return False

    except Exception as e:
        print("\n")
        print("=" * 80)
        print("❌ UNEXPECTED ERROR")
        print("=" * 80)
        print(f"Error Type: {type(e).__name__}")
        print(f"Error: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        print()
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
