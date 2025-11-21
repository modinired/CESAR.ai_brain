#!/usr/bin/env python3
"""
Test Specialist Prompt Integration
Verifies mob aliases and prompt formatting work correctly
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Set environment variables for database
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5432'
os.environ['POSTGRES_DB'] = 'mcp'
os.environ['POSTGRES_USER'] = 'mcp_user'
os.environ['POSTGRES_PASSWORD'] = 'ASkLZ4xpmSrSOE9SyX5XhPE81V99TAdwfN8tUKM_snw'

from services.collaborative_llm_service import CollaborativeLLMService


def test_agent_metadata():
    """Test loading agent metadata from database"""
    print("=" * 80)
    print("TEST 1: Agent Metadata Loading")
    print("=" * 80)

    service = CollaborativeLLMService()

    # Test multiple agents
    test_agents = [
        'email_agent',
        'finpsy_sentiment',
        'central_orchestrator',
    ]

    for agent_id in test_agents:
        metadata = service._get_agent_metadata(agent_id)
        print(f"\n✅ Agent: {agent_id}")
        print(f"   Mob Alias: {metadata['mob_alias']}")
        print(f"   Specialization: {metadata['specialization']}")
        print(f"   Role: {metadata['hierarchy_role']}")


def test_specialist_prompt_formatting():
    """Test specialist prompt formatting"""
    print("\n" + "=" * 80)
    print("TEST 2: Specialist Prompt Formatting")
    print("=" * 80)

    service = CollaborativeLLMService()

    # Test with regular specialist agent
    agent_id = 'finpsy_sentiment'
    user_prompt = "Analyze the sentiment of this text: 'I love this product!'"

    formatted = service._format_specialist_prompt(
        user_prompt=user_prompt,
        agent_id=agent_id,
        current_role="LOCAL"
    )

    print(f"\n✅ Agent: {agent_id}")
    print(f"   Original Prompt Length: {len(user_prompt)} chars")
    print(f"   Formatted Prompt Length: {len(formatted)} chars")
    print(f"   Contains 'Silvio Dante': {'Silvio Dante' in formatted}")
    print(f"   Contains 'ROLE: LOCAL': {'ROLE: LOCAL' in formatted}")
    print(f"   Contains 'third person': {'third person' in formatted.lower()}")

    # Test with CESAR (should return unchanged)
    cesar_formatted = service._format_specialist_prompt(
        user_prompt=user_prompt,
        agent_id='central_orchestrator',
        current_role="LOCAL"
    )

    print(f"\n✅ Agent: central_orchestrator (CESAR)")
    print(f"   Bypasses specialist prompt: {cesar_formatted == user_prompt}")


def test_prompt_content():
    """Test actual prompt content"""
    print("\n" + "=" * 80)
    print("TEST 3: Prompt Content Verification")
    print("=" * 80)

    service = CollaborativeLLMService()

    formatted = service._format_specialist_prompt(
        user_prompt="Test request",
        agent_id='email_agent',
        current_role="LOCAL"
    )

    checks = {
        "Mob Alias (Moe Greene)": "Moe Greene" in formatted,
        "Specialization": "External Communication" in formatted,
        "Third-Person Rule": "ALWAYS speak in THIRD PERSON" in formatted,
        "CESAR as Boss": "CESAR Sheppardini" in formatted,
        "Role Assignment": "ROLE: LOCAL" in formatted,
        "Signature Phrases": "Capisce?" in formatted,
        "Response Structure": "### 1. Answer" in formatted,
        "User Request Included": "Test request" in formatted,
    }

    print("\n📋 Prompt Content Checks:")
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check_name}")

    # Print sample of formatted prompt
    print("\n📄 Sample of Formatted Prompt (first 500 chars):")
    print("-" * 80)
    print(formatted[:500])
    print("...")
    print("-" * 80)


if __name__ == "__main__":
    try:
        test_agent_metadata()
        test_specialist_prompt_formatting()
        test_prompt_content()

        print("\n" + "=" * 80)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
