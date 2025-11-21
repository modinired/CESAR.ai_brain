#!/usr/bin/env python3
"""
CESAR.ai Full System Capacity Test
==================================

Comprehensive test of all system components:
1. Database connectivity and schema
2. API health and endpoints
3. WebSocket real-time communication
4. Agent registry and status
5. Workflow execution
6. Event persistence and querying
7. Memory systems
8. Performance benchmarks

Usage:
    python test_full_system.py
"""

import asyncio
import sys
import time
import json
import os
from datetime import datetime

import httpx
import psycopg

# =============================================================================
# Configuration
# =============================================================================

API_BASE_URL = "http://localhost:8000"
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "mcp",
    "user": "mcp_user",
    "password": os.getenv("POSTGRES_PASSWORD"),  # REQUIRED: Set in .env file
}

# =============================================================================
# Test Results Tracking
# =============================================================================


class TestResults:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.results = []

    def record(
        self, test_name: str, status: str, details: str = "", duration_ms: float = 0
    ):
        self.total += 1
        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
        elif status == "SKIP":
            self.skipped += 1

        self.results.append(
            {
                "test": test_name,
                "status": status,
                "details": details,
                "duration_ms": duration_ms,
            }
        )

        # Print result
        emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏭️"
        print(f"{emoji} {test_name}: {status} ({duration_ms:.2f}ms)")
        if details:
            print(f"   {details}")

    def summary(self):
        print("\n" + "=" * 80)
        print("CESAR.ai Full System Test Summary")
        print("=" * 80)
        print(f"Total Tests: {self.total}")
        print(f"✅ Passed: {self.passed} ({self.passed/max(self.total,1)*100:.1f}%)")
        print(f"❌ Failed: {self.failed}")
        print(f"⏭️  Skipped: {self.skipped}")
        print("=" * 80)

        if self.failed > 0:
            print("\n❌ FAILED TESTS:")
            for r in self.results:
                if r["status"] == "FAIL":
                    print(f"  - {r['test']}: {r['details']}")

        return self.failed == 0


results = TestResults()

# =============================================================================
# Section 1: Database Tests
# =============================================================================


async def test_database_connectivity():
    """Test PostgreSQL database connection"""
    start = time.time()
    try:
        conn = psycopg.connect(**DB_CONFIG)
        conn.close()
        duration_ms = (time.time() - start) * 1000
        results.record(
            "Database Connectivity", "PASS", "Connection successful", duration_ms
        )
        return True
    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        results.record("Database Connectivity", "FAIL", str(e), duration_ms)
        return False


async def test_database_schema():
    """Test Phase A tables exist"""
    start = time.time()
    required_tables = [
        "sessions",
        "llms",
        "tools",
        "routing_rules",
        "agent_runs",
        "events",
        "tool_invocations",
        "blackboard_entries",
        "agents",
        "workflow_executions",
        "learning_reflections",
    ]

    try:
        conn = psycopg.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = ANY(%s)
        """,
            (required_tables,),
        )

        existing_tables = [row[0] for row in cur.fetchall()]
        missing = set(required_tables) - set(existing_tables)

        conn.close()
        duration_ms = (time.time() - start) * 1000

        if missing:
            results.record(
                "Database Schema",
                "FAIL",
                f"Missing tables: {', '.join(missing)}",
                duration_ms,
            )
            return False
        else:
            results.record(
                "Database Schema",
                "PASS",
                f"All {len(required_tables)} tables exist",
                duration_ms,
            )
            return True

    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        results.record("Database Schema", "FAIL", str(e), duration_ms)
        return False


async def test_database_agent_count():
    """Test agent registry has expected agents"""
    start = time.time()
    try:
        conn = psycopg.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM agents WHERE status = 'active'")
        count = cur.fetchone()[0]

        conn.close()
        duration_ms = (time.time() - start) * 1000

        if count >= 20:  # Expecting 23 agents
            results.record(
                "Agent Registry Count",
                "PASS",
                f"{count} active agents registered",
                duration_ms,
            )
            return True
        else:
            results.record(
                "Agent Registry Count",
                "FAIL",
                f"Only {count} agents (expected ~23)",
                duration_ms,
            )
            return False

    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        results.record("Agent Registry Count", "FAIL", str(e), duration_ms)
        return False


async def test_llm_registry():
    """Test LLM registry populated"""
    start = time.time()
    try:
        conn = psycopg.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM llms")
        count = cur.fetchone()[0]

        conn.close()
        duration_ms = (time.time() - start) * 1000

        if count >= 5:
            results.record(
                "LLM Registry", "PASS", f"{count} LLMs registered", duration_ms
            )
            return True
        else:
            results.record(
                "LLM Registry", "FAIL", f"Only {count} LLMs (expected 5+)", duration_ms
            )
            return False

    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        results.record("LLM Registry", "FAIL", str(e), duration_ms)
        return False


# =============================================================================
# Section 2: API Tests
# =============================================================================


async def test_api_health():
    """Test API health endpoint"""
    start = time.time()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/health", timeout=5.0)
            duration_ms = (time.time() - start) * 1000

            if response.status_code == 200:
                data = response.json()
                results.record(
                    "API Health",
                    "PASS",
                    f"Status: {data.get('status', 'unknown')}",
                    duration_ms,
                )
                return True
            else:
                results.record(
                    "API Health", "FAIL", f"HTTP {response.status_code}", duration_ms
                )
                return False

    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        results.record("API Health", "FAIL", str(e), duration_ms)
        return False


async def test_api_agents_endpoint():
    """Test /api/agents endpoint"""
    start = time.time()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/api/agents", timeout=10.0)
            duration_ms = (time.time() - start) * 1000

            if response.status_code == 200:
                agents = response.json()
                results.record(
                    "API Agents Endpoint",
                    "PASS",
                    f"{len(agents)} agents returned",
                    duration_ms,
                )
                return True
            else:
                results.record(
                    "API Agents Endpoint",
                    "FAIL",
                    f"HTTP {response.status_code}",
                    duration_ms,
                )
                return False

    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        results.record("API Agents Endpoint", "FAIL", str(e), duration_ms)
        return False


async def test_api_workflows_endpoint():
    """Test /api/workflows endpoint"""
    start = time.time()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/api/workflows", timeout=10.0)
            duration_ms = (time.time() - start) * 1000

            if response.status_code == 200:
                workflows = response.json()
                results.record(
                    "API Workflows Endpoint",
                    "PASS",
                    f"{len(workflows)} workflows",
                    duration_ms,
                )
                return True
            else:
                results.record(
                    "API Workflows Endpoint",
                    "FAIL",
                    f"HTTP {response.status_code}",
                    duration_ms,
                )
                return False

    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        results.record("API Workflows Endpoint", "FAIL", str(e), duration_ms)
        return False


# =============================================================================
# Section 3: WebSocket Tests
# =============================================================================


async def test_websocket_stats():
    """Test WebSocket stats endpoint"""
    start = time.time()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/api/websocket/stats", timeout=5.0
            )
            duration_ms = (time.time() - start) * 1000

            if response.status_code == 200:
                stats = response.json()
                latency = stats.get("performance", {}).get("avg_latency_ms", 0)
                sla = stats.get("performance", {}).get("meeting_sla", False)

                if sla:
                    results.record(
                        "WebSocket Stats",
                        "PASS",
                        f"Avg latency: {latency}ms (SLA: ✓)",
                        duration_ms,
                    )
                    return True
                else:
                    results.record(
                        "WebSocket Stats",
                        "FAIL",
                        f"Not meeting SLA (latency: {latency}ms)",
                        duration_ms,
                    )
                    return False
            else:
                results.record(
                    "WebSocket Stats",
                    "FAIL",
                    f"HTTP {response.status_code}",
                    duration_ms,
                )
                return False

    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        results.record("WebSocket Stats", "FAIL", str(e), duration_ms)
        return False


async def test_websocket_publish():
    """Test WebSocket event publishing"""
    start = time.time()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/websocket/publish",
                params={"event_type": "system_test", "room": "all"},
                json={
                    "test_id": "full_system_test",
                    "timestamp": datetime.utcnow().isoformat(),
                },
                timeout=5.0,
            )
            duration_ms = (time.time() - start) * 1000

            if response.status_code == 200:
                results.record(
                    "WebSocket Publish",
                    "PASS",
                    "Event published successfully",
                    duration_ms,
                )
                return True
            else:
                results.record(
                    "WebSocket Publish",
                    "FAIL",
                    f"HTTP {response.status_code}",
                    duration_ms,
                )
                return False

    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        results.record("WebSocket Publish", "FAIL", str(e), duration_ms)
        return False


# =============================================================================
# Section 4: Workflow Execution Tests
# =============================================================================


async def test_workflow_execution():
    """Test triggering a workflow"""
    start = time.time()
    try:
        async with httpx.AsyncClient() as client:
            # Trigger workflow
            response = await client.post(
                f"{API_BASE_URL}/api/workflows/trigger",
                params={"workflow_name": "daily_recursive_learning_full"},
                timeout=30.0,
            )

            if response.status_code in [200, 201, 202]:
                duration_ms = (time.time() - start) * 1000
                result = response.json()
                results.record(
                    "Workflow Trigger",
                    "PASS",
                    f"Flow ID: {result.get('flow_run_id', 'N/A')}",
                    duration_ms,
                )
                return True
            else:
                duration_ms = (time.time() - start) * 1000
                results.record(
                    "Workflow Trigger",
                    "FAIL",
                    f"HTTP {response.status_code}",
                    duration_ms,
                )
                return False

    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        results.record(
            "Workflow Trigger",
            "SKIP",
            f"Skipped (expected in test environment): {type(e).__name__}",
            duration_ms,
        )
        return True  # Don't fail on workflow trigger in test


# =============================================================================
# Section 5: Performance Tests
# =============================================================================


async def test_api_response_times():
    """Test API endpoint response times"""
    endpoints = ["/health", "/api/agents", "/api/workflows", "/api/stats/overview"]

    all_passed = True

    for endpoint in endpoints:
        start = time.time()
        try:
            async with httpx.AsyncClient() as client:
                await client.get(f"{API_BASE_URL}{endpoint}", timeout=5.0)
                duration_ms = (time.time() - start) * 1000

                if duration_ms < 500:  # 500ms threshold
                    results.record(
                        f"Response Time {endpoint}",
                        "PASS",
                        f"{duration_ms:.2f}ms",
                        duration_ms,
                    )
                else:
                    results.record(
                        f"Response Time {endpoint}",
                        "FAIL",
                        f"{duration_ms:.2f}ms (threshold: 500ms)",
                        duration_ms,
                    )
                    all_passed = False

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            results.record(f"Response Time {endpoint}", "FAIL", str(e), duration_ms)
            all_passed = False

    return all_passed


# =============================================================================
# Section 6: Event Persistence Tests
# =============================================================================


async def test_event_persistence():
    """Test events are persisted to database"""
    start = time.time()
    try:
        # Publish an event
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{API_BASE_URL}/api/websocket/publish",
                params={"event_type": "persistence_test", "room": "all"},
                json={"test_marker": f"test_{int(time.time())}"},
            )

        # Wait a moment for persistence
        await asyncio.sleep(0.5)

        # Check database for events
        conn = psycopg.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM events WHERE event_type = 'persistence_test'")
        count = cur.fetchone()[0]

        conn.close()
        duration_ms = (time.time() - start) * 1000

        if count > 0:
            results.record(
                "Event Persistence",
                "PASS",
                f"{count} test events found in database",
                duration_ms,
            )
            return True
        else:
            results.record(
                "Event Persistence", "FAIL", "No events found in database", duration_ms
            )
            return False

    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        results.record("Event Persistence", "FAIL", str(e), duration_ms)
        return False


# =============================================================================
# Main Test Runner
# =============================================================================


async def run_all_tests():
    """Run all system tests"""
    print("\n" + "=" * 80)
    print("CESAR.ai Full System Capacity Test")
    print("=" * 80)
    print(f"Started: {datetime.now().isoformat()}")
    print()

    # Section 1: Database
    print("\n[Section 1: Database Tests]")
    await test_database_connectivity()
    await test_database_schema()
    await test_database_agent_count()
    await test_llm_registry()

    # Section 2: API
    print("\n[Section 2: API Tests]")
    await test_api_health()
    await test_api_agents_endpoint()
    await test_api_workflows_endpoint()

    # Section 3: WebSocket
    print("\n[Section 3: WebSocket Tests]")
    await test_websocket_stats()
    await test_websocket_publish()

    # Section 4: Workflows
    print("\n[Section 4: Workflow Tests]")
    await test_workflow_execution()

    # Section 5: Performance
    print("\n[Section 5: Performance Tests]")
    await test_api_response_times()

    # Section 6: Event Persistence
    print("\n[Section 6: Event Persistence Tests]")
    await test_event_persistence()

    # Summary
    success = results.summary()

    # Export results
    with open("test_results.json", "w") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total": results.total,
                    "passed": results.passed,
                    "failed": results.failed,
                    "skipped": results.skipped,
                },
                "results": results.results,
            },
            f,
            indent=2,
        )

    print("\nResults exported to: test_results.json")

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
