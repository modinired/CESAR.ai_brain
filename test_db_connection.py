#!/usr/bin/env python3
"""
CockroachDB Connection Test Script
===================================
Tests both sync and async database connections to verify setup.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment
load_dotenv()
load_dotenv(".env.cockroach")

print("=" * 80)
print("CESAR ECOSYSTEM - DATABASE CONNECTION TEST")
print("=" * 80)

# Add api directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "api"))

def test_sync_connection():
    """Test synchronous database connection (database_v2)"""
    print("\n🔍 Testing Synchronous Database Connection (database_v2.py)...")
    print("-" * 80)

    try:
        from api.database_v2 import init_database, check_database_connection, USE_COCKROACH, SQLALCHEMY_DATABASE_URL

        print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
        print(f"Using CockroachDB: {USE_COCKROACH}")
        print(f"Connection URL: {SQLALCHEMY_DATABASE_URL.split('@')[1] if '@' in SQLALCHEMY_DATABASE_URL else 'local'}")
        print()

        # Initialize and check health
        health = init_database()

        if health['status'] == 'healthy':
            print(f"✅ SYNC CONNECTION SUCCESSFUL")
            print(f"   Database: {health['database']}")
            print(f"   Latency: {health.get('latency_ms', 'N/A')}ms")
            print(f"   Endpoint: {health.get('url', 'N/A')}")
            return True
        else:
            print(f"❌ SYNC CONNECTION FAILED")
            print(f"   Error: {health.get('error', 'Unknown')}")
            return False

    except Exception as e:
        print(f"❌ SYNC CONNECTION ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_async_connection():
    """Test asynchronous database connection (database_async)"""
    print("\n🔍 Testing Asynchronous Database Connection (database_async.py)...")
    print("-" * 80)

    try:
        from api.database_async import create_pool, check_database_health, close_pool, USE_COCKROACH, DATABASE_URL

        print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
        print(f"Using CockroachDB: {USE_COCKROACH}")
        print(f"Connection URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}")
        print()

        # Create pool and check health
        await create_pool()
        health = await check_database_health()

        if health['status'] == 'healthy':
            print(f"✅ ASYNC CONNECTION SUCCESSFUL")
            print(f"   Database: {health['database']}")
            print(f"   Pool Size: {health.get('pool_size', 'N/A')}/{health.get('pool_max', 'N/A')}")
            print(f"   Pool Free: {health.get('pool_free', 'N/A')}")
            print(f"   Ping: {health.get('ping_ms', 'N/A')}ms")
            print(f"   Endpoint: {health.get('url', 'N/A')}")

            # Clean up
            await close_pool()
            return True
        else:
            print(f"❌ ASYNC CONNECTION FAILED")
            print(f"   Error: {health.get('error', 'Unknown')}")
            await close_pool()
            return False

    except Exception as e:
        print(f"❌ ASYNC CONNECTION ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_simple_query():
    """Test a simple query to verify database is accessible"""
    print("\n🔍 Testing Simple Query Execution...")
    print("-" * 80)

    try:
        from api.database_async import create_pool, get_db_connection, close_pool

        await create_pool()

        async with get_db_connection() as conn:
            # Test basic query
            result = await conn.fetchval("SELECT 1 + 1")
            print(f"✅ Query Test: SELECT 1 + 1 = {result}")

            # Test version query
            version = await conn.fetchval("SELECT version()")
            print(f"✅ Database Version: {version[:80]}...")

            # Try to list tables (might fail if schema not set up)
            try:
                tables = await conn.fetch("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    LIMIT 5
                """)
                print(f"✅ Found {len(tables)} tables in public schema")
                for row in tables:
                    print(f"   - {row['table_name']}")
            except Exception as e:
                print(f"⚠️  Could not list tables (schema may not be initialized): {e}")

        await close_pool()
        return True

    except Exception as e:
        print(f"❌ QUERY TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print()

    # Test 1: Sync connection
    sync_ok = test_sync_connection()

    # Test 2: Async connection
    async_ok = await test_async_connection()

    # Test 3: Query execution
    query_ok = await test_simple_query()

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Synchronous Connection:  {'✅ PASS' if sync_ok else '❌ FAIL'}")
    print(f"Asynchronous Connection: {'✅ PASS' if async_ok else '❌ FAIL'}")
    print(f"Query Execution:         {'✅ PASS' if query_ok else '❌ FAIL'}")
    print("=" * 80)

    if sync_ok and async_ok and query_ok:
        print("🎉 ALL TESTS PASSED! Database is ready for CESAR Ecosystem.")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED. Check configuration and CockroachDB connection.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
