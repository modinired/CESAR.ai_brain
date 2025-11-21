"""
Example MCP Plugin
==================

This demonstrates how to create a custom MCP plugin.

Plugin Structure:
- Must have a register() function that returns plugin metadata
- Agent must have a process(task_input) method
- Compatible with existing MCP infrastructure
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from mcp_agents.base_agent import BaseMCPAgent
from typing import Dict, Any


class ExampleAgent(BaseMCPAgent):
    """
    Example custom agent

    Extend this for your own functionality
    """

    def __init__(self, db_dsn: str = None):
        super().__init__(
            agent_id='plugin_example',
            mcp_system='custom',
            db_dsn=db_dsn
        )

    def process(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process custom task

        Args:
            task_input: Task input data

        Returns:
            Processing result
        """
        # Your custom logic here
        data = task_input.get('data', {})

        return {
            'status': 'success',
            'result': f'Processed: {data}',
            'plugin': 'example_plugin'
        }


def register():
    """
    Register plugin with MCP system

    Returns:
        Dict with plugin metadata and agent instance
    """
    return {
        "name": "example_plugin",
        "version": "1.0.0",
        "description": "Example custom MCP plugin",
        "author": "Your Name",
        "mcp_system": "custom",  # or "finpsy", "pydini_red", etc.
        "task_types": ["custom_task", "example_process"],
        "agent": ExampleAgent()
    }
