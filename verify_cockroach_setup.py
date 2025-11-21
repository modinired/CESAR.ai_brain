#!/usr/bin/env python3
"""
CockroachDB Setup Verification
==============================
Verifies that the CESAR ecosystem is correctly configured for CockroachDB.
"""

import os
import sys
import psycopg
from dotenv import load_dotenv

# Load environment
load_dotenv()
load_dotenv(".env.cockroach")

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_cockroach_connection():
    """Test CockroachDB connection"""
    print_section("1. CockroachDB Connection Test")

    url = os.getenv("COCKROACH_DB_URL")

    if not url:
        print("❌ COCKROACH_DB_URL not found in environment")
        return False

    # Mask password for display
    display_url = "..." + url.split("@")[1] if "@" in url else "INVALID"
    print(f"📡 Connection String: {display_url}")

    try:
        conn = psycopg.connect(url)
        cur = conn.cursor()

        # Test query
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"✅ Connected successfully")
        print(f"   Version: {version[:80]}...")

        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_database_schema():
    """Test that all required tables exist"""
    print_section("2. Database Schema Verification")

    url = os.getenv("COCKROACH_DB_URL")
    required_tables = [
        'agents', 'a2a_messages', 'a2a_conversations',
        'llm_collaborations', 'sessions', 'tasks'
    ]

    try:
        conn = psycopg.connect(url)
        cur = conn.cursor()

        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)

        existing_tables = [row[0] for row in cur.fetchall()]

        print(f"📋 Found {len(existing_tables)} tables:")
        for table in existing_tables:
            status = "✅" if table in required_tables else "ℹ️"
            print(f"   {status} {table}")

        missing = set(required_tables) - set(existing_tables)
        if missing:
            print(f"\n⚠️  Missing required tables: {', '.join(missing)}")
            return False

        cur.close()
        conn.close()
        print("\n✅ All required tables present")
        return True
    except Exception as e:
        print(f"❌ Schema check failed: {e}")
        return False

def test_agent_data():
    """Test that agent data was synced"""
    print_section("3. Agent Data Verification")

    url = os.getenv("COCKROACH_DB_URL")

    try:
        conn = psycopg.connect(url)
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM agents;")
        count = cur.fetchone()[0]

        print(f"🤖 Total agents in CockroachDB: {count}")

        if count > 0:
            cur.execute("""
                SELECT agent_id, name, metadata->>'mob_alias' as mob_alias
                FROM agents
                ORDER BY created_at
                LIMIT 5;
            """)

            print("\n📋 Sample agents:")
            for row in cur.fetchall():
                agent_id, name, alias = row
                print(f"   • {name:40} → {alias or 'N/A'}")

            print(f"\n✅ {count} agents synced successfully")
        else:
            print("⚠️  No agents found. Run sync_to_cockroach.py to populate data.")

        cur.close()
        conn.close()
        return count > 0
    except Exception as e:
        print(f"❌ Agent data check failed: {e}")
        return False

def test_api_configuration():
    """Verify API is configured to use CockroachDB"""
    print_section("4. API Configuration Check")

    try:
        # Check if database_v2.py exists and has correct imports
        if os.path.exists("api/database_v2.py"):
            print("✅ api/database_v2.py exists")

            with open("api/database_v2.py", "r") as f:
                content = f.read()
                if "COCKROACH_DB_URL" in content:
                    print("✅ CockroachDB configuration present")
                    if "USE_COCKROACH" in content:
                        print("✅ Cockroach priority logic implemented")
                    return True
                else:
                    print("❌ CockroachDB configuration missing")
                    return False
        else:
            print("❌ api/database_v2.py not found")
            return False
    except Exception as e:
        print(f"❌ API config check failed: {e}")
        return False

def main():
    print("\n" + "🚀 " * 25)
    print("CESAR ECOSYSTEM: COCKROACHDB SETUP VERIFICATION")
    print("🚀 " * 25)

    results = []

    # Run tests
    results.append(("CockroachDB Connection", test_cockroach_connection()))
    results.append(("Database Schema", test_database_schema()))
    results.append(("Agent Data", test_agent_data()))
    results.append(("API Configuration", test_api_configuration()))

    # Summary
    print_section("VERIFICATION SUMMARY")

    passed = sum(1 for _, status in results if status)
    total = len(results)

    for test_name, status in results:
        emoji = "✅" if status else "❌"
        print(f"{emoji} {test_name}")

    print(f"\n📊 Score: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 SUCCESS! Your CESAR ecosystem is fully configured for CockroachDB.")
        print("\nNext steps:")
        print("  1. Start the API: python3 api/main.py")
        print("  2. Start the sync daemon: python3 sync_bidirectional.py")
        print("  3. Access the API: http://localhost:8000/docs")
    else:
        print("\n⚠️  Some checks failed. Review the errors above and:")
        print("  1. Verify .env.cockroach has correct COCKROACH_DB_URL")
        print("  2. Run: bash apply_migrations_cockroach.sh")
        print("  3. Run: python3 sync_to_cockroach.py")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
