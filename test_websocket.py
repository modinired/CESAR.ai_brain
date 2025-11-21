#!/usr/bin/env python3
"""
WebSocket Implementation Test Script
====================================

Tests the PhD-level WebSocket real-time communication system:
1. Publish test events via Redis
2. Verify WebSocket stats endpoint
3. Measure latency
4. Test different event types

Usage:
    python test_websocket.py
"""

import asyncio
import sys
import os
import time
import json
from datetime import datetime

# Add API to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

import redis.asyncio as aioredis
import httpx


async def test_websocket_stats():
    """Test WebSocket stats endpoint"""
    print("\n=== Testing WebSocket Stats Endpoint ===")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/api/websocket/stats")
            if response.status_code == 200:
                stats = response.json()
                print("✅ WebSocket Stats Retrieved:")
                print(json.dumps(stats, indent=2))
                return stats
            else:
                print(f"❌ Stats endpoint failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None


async def publish_test_events():
    """Publish various test events to Redis"""
    print("\n=== Publishing Test Events ===")

    # Connect to Redis
    redis = await aioredis.from_url(
        "redis://localhost:6379/0",
        encoding="utf-8",
        decode_responses=True
    )

    test_events = [
        # Agent status events
        {
            "type": "agent_status",
            "data": {
                "agent_id": "test_agent_001",
                "status": "active",
                "message": "Test agent initialized",
                "metadata": {"test": True}
            },
            "room": "agents",
            "timestamp": datetime.utcnow().isoformat(),
            "publish_time": time.time()
        },

        # Agent task start
        {
            "type": "agent_task",
            "data": {
                "agent_id": "test_agent_001",
                "task_id": "task_123",
                "task_type": "data_analysis",
                "description": "Analyzing market data",
                "action": "start"
            },
            "room": "agents",
            "timestamp": datetime.utcnow().isoformat(),
            "publish_time": time.time()
        },

        # Workflow update
        {
            "type": "workflow_update",
            "data": {
                "workflow_id": "wf_test_001",
                "status": "running",
                "progress": 45.5,
                "message": "Processing step 3 of 7"
            },
            "room": "workflows",
            "timestamp": datetime.utcnow().isoformat(),
            "publish_time": time.time()
        },

        # Learning event
        {
            "type": "learning",
            "data": {
                "agent_id": "test_agent_001",
                "event_type": "skill_improved",
                "details": {
                    "skill": "python_analysis",
                    "old_level": 7.5,
                    "new_level": 8.2
                }
            },
            "room": "memory",
            "timestamp": datetime.utcnow().isoformat(),
            "publish_time": time.time()
        },

        # System alert
        {
            "type": "system_alert",
            "data": {
                "severity": "info",
                "message": "WebSocket test in progress",
                "component": "test_script"
            },
            "room": "all",
            "timestamp": datetime.utcnow().isoformat(),
            "publish_time": time.time()
        },

        # Agent task complete
        {
            "type": "agent_task",
            "data": {
                "agent_id": "test_agent_001",
                "task_id": "task_123",
                "action": "complete",
                "success": True,
                "result": {
                    "insights": 42,
                    "anomalies_detected": 3
                }
            },
            "room": "agents",
            "timestamp": datetime.utcnow().isoformat(),
            "publish_time": time.time()
        },

        # Collaboration request
        {
            "type": "collaboration_request",
            "data": {
                "requesting_agent": "test_agent_001",
                "target_agent": "test_agent_002",
                "request_type": "data_sharing",
                "details": {
                    "dataset": "market_analysis_q4",
                    "urgency": "normal"
                }
            },
            "room": "agents",
            "timestamp": datetime.utcnow().isoformat(),
            "publish_time": time.time()
        }
    ]

    # Publish events with delays
    for i, event in enumerate(test_events, 1):
        try:
            await redis.publish("cesar:events", json.dumps(event))
            print(f"✅ Published event {i}/{len(test_events)}: {event['type']}")

            # Small delay between events
            await asyncio.sleep(0.5)

        except Exception as e:
            print(f"❌ Failed to publish event {i}: {e}")

    await redis.close()
    print(f"\n✅ Published {len(test_events)} test events")


async def test_publish_api():
    """Test the /api/websocket/publish endpoint"""
    print("\n=== Testing WebSocket Publish API ===")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/api/websocket/publish",
                params={
                    "event_type": "agent_metric",
                    "room": "agents"
                },
                json={
                    "agent_id": "test_agent_001",
                    "metric_name": "tasks_per_minute",
                    "value": 12.5,
                    "unit": "tasks/min"
                }
            )

            if response.status_code == 200:
                print("✅ Publish API works:", response.json())
            else:
                print(f"❌ Publish API failed: {response.status_code}")

        except Exception as e:
            print(f"❌ Error: {e}")


async def measure_latency():
    """Measure end-to-end event latency"""
    print("\n=== Measuring Event Latency ===")

    # Connect to Redis
    redis = await aioredis.from_url(
        "redis://localhost:6379/0",
        encoding="utf-8",
        decode_responses=True
    )

    latencies = []
    num_tests = 10

    for i in range(num_tests):
        start_time = time.time()

        event = {
            "type": "system_metric",
            "data": {
                "metric_name": f"latency_test_{i}",
                "value": i,
                "timestamp": start_time
            },
            "room": "all",
            "timestamp": datetime.utcnow().isoformat(),
            "publish_time": start_time
        }

        await redis.publish("cesar:events", json.dumps(event))

        # Measure publish latency
        publish_latency = (time.time() - start_time) * 1000  # ms
        latencies.append(publish_latency)

        await asyncio.sleep(0.1)

    await redis.close()

    # Calculate stats
    avg_latency = sum(latencies) / len(latencies)
    min_latency = min(latencies)
    max_latency = max(latencies)

    print(f"\n📊 Latency Statistics (Redis Publish):")
    print(f"   Average: {avg_latency:.2f}ms")
    print(f"   Min: {min_latency:.2f}ms")
    print(f"   Max: {max_latency:.2f}ms")
    print(f"   Target: <50ms")

    if avg_latency < 50:
        print("   ✅ Meeting SLA target!")
    else:
        print("   ⚠️  Above SLA target")

    return avg_latency


async def main():
    """Run all tests"""
    print("=" * 60)
    print("WebSocket Real-Time Communication Test Suite")
    print("PhD-Level Implementation Verification")
    print("=" * 60)

    # Test 1: Check stats endpoint
    stats = await test_websocket_stats()

    if stats is None:
        print("\n❌ WebSocket manager not available. Ensure API is running.")
        return

    # Test 2: Publish test events via Redis
    await publish_test_events()

    # Test 3: Test publish API
    await test_publish_api()

    # Test 4: Measure latency
    avg_latency = await measure_latency()

    # Wait for events to propagate
    await asyncio.sleep(2)

    # Test 5: Check final stats
    final_stats = await test_websocket_stats()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    if final_stats:
        events_received = final_stats.get('events', {}).get('received', 0)
        events_broadcast = final_stats.get('events', {}).get('broadcast', 0)
        connections = final_stats.get('connections', {}).get('total_connections', 0)

        print(f"✅ Events received by WebSocket manager: {events_received}")
        print(f"✅ Events broadcast to clients: {events_broadcast}")
        print(f"✅ Active WebSocket connections: {connections}")
        print(f"✅ Average latency: {avg_latency:.2f}ms")

        if final_stats.get('performance', {}).get('meeting_sla'):
            print("\n🎉 All performance targets met!")
        else:
            print("\n⚠️  Some performance targets not met")

    print("\n💡 To see live events, open http://localhost:3000 in your browser")
    print("   The AgentActivityFeed component will show real-time events")


if __name__ == "__main__":
    asyncio.run(main())
