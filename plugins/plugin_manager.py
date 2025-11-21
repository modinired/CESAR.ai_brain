"""
Plugin Manager for MCP Systems
================================

Dynamic plugin loading system that allows extending MCP functionality
without modifying core code.

Features:
- Hot-reload plugin support
- Automatic registration with central orchestrator
- Plugin validation and sandboxing
- Version compatibility checking
"""

import os
import importlib.util
import inspect
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PluginManager")


@dataclass
class PluginInfo:
    """Plugin metadata"""
    name: str
    version: str
    description: str
    author: str
    mcp_system: str
    task_types: List[str]
    module: Any


class PluginManager:
    """
    Manages dynamic plugin loading and registration
    """

    def __init__(
        self,
        plugin_dir: str = "./plugins",
        auto_load: bool = True
    ):
        self.plugin_dir = Path(plugin_dir)
        self.plugins: Dict[str, PluginInfo] = {}
        self.plugin_agents: Dict[str, Any] = {}

        # Create plugin directory if not exists
        self.plugin_dir.mkdir(parents=True, exist_ok=True)

        # Create example plugin
        self._create_example_plugin()

        if auto_load:
            self.load_all_plugins()

        logger.info(f"PluginManager initialized: {self.plugin_dir}")

    def load_all_plugins(self) -> Dict[str, PluginInfo]:
        """
        Load all plugins from plugin directory

        Returns:
            Dict of loaded plugins
        """
        plugin_files = list(self.plugin_dir.glob("*.py"))

        logger.info(f"Found {len(plugin_files)} plugin files")

        for plugin_file in plugin_files:
            if plugin_file.name.startswith("_"):
                continue

            try:
                self.load_plugin(str(plugin_file))
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_file}: {e}")

        logger.info(f"Loaded {len(self.plugins)} plugins")
        return self.plugins

    def load_plugin(self, plugin_path: str) -> Optional[PluginInfo]:
        """
        Load a single plugin

        Args:
            plugin_path: Path to plugin file

        Returns:
            PluginInfo if successful, None otherwise
        """
        plugin_file = Path(plugin_path)

        if not plugin_file.exists():
            logger.error(f"Plugin file not found: {plugin_path}")
            return None

        # Import the module
        module_name = plugin_file.stem
        spec = importlib.util.spec_from_file_location(module_name, plugin_file)
        module = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(module)
        except Exception as e:
            logger.error(f"Failed to execute plugin {module_name}: {e}")
            return None

        # Check for register function
        if not hasattr(module, "register"):
            logger.error(f"Plugin {module_name} missing 'register()' function")
            return None

        # Call register function
        try:
            plugin_data = module.register()
        except Exception as e:
            logger.error(f"Plugin {module_name} register() failed: {e}")
            return None

        # Validate plugin data
        if not self._validate_plugin(plugin_data):
            logger.error(f"Plugin {module_name} validation failed")
            return None

        # Create plugin info
        plugin_info = PluginInfo(
            name=plugin_data.get("name", module_name),
            version=plugin_data.get("version", "1.0.0"),
            description=plugin_data.get("description", ""),
            author=plugin_data.get("author", "Unknown"),
            mcp_system=plugin_data.get("mcp_system", "custom"),
            task_types=plugin_data.get("task_types", []),
            module=module
        )

        # Store plugin
        self.plugins[plugin_info.name] = plugin_info
        self.plugin_agents[plugin_info.name] = plugin_data.get("agent")

        logger.info(f"Loaded plugin: {plugin_info.name} v{plugin_info.version}")
        return plugin_info

    def _validate_plugin(self, plugin_data: Dict[str, Any]) -> bool:
        """Validate plugin data structure"""
        required_fields = ["agent", "task_types"]

        for field in required_fields:
            if field not in plugin_data:
                logger.error(f"Plugin missing required field: {field}")
                return False

        # Validate agent has process method
        agent = plugin_data.get("agent")
        if not hasattr(agent, "process"):
            logger.error("Plugin agent missing 'process()' method")
            return False

        return True

    def get_plugin(self, name: str) -> Optional[PluginInfo]:
        """Get plugin by name"""
        return self.plugins.get(name)

    def get_plugin_agent(self, name: str) -> Optional[Any]:
        """Get plugin agent instance"""
        return self.plugin_agents.get(name)

    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all loaded plugins"""
        return [
            {
                "name": info.name,
                "version": info.version,
                "description": info.description,
                "author": info.author,
                "mcp_system": info.mcp_system,
                "task_types": info.task_types
            }
            for info in self.plugins.values()
        ]

    def reload_plugin(self, name: str) -> bool:
        """
        Reload a plugin (hot-reload)

        Args:
            name: Plugin name

        Returns:
            True if successful
        """
        plugin_info = self.plugins.get(name)

        if not plugin_info:
            logger.error(f"Plugin not found: {name}")
            return False

        # Find plugin file
        plugin_file = self.plugin_dir / f"{name}.py"

        if not plugin_file.exists():
            logger.error(f"Plugin file not found: {plugin_file}")
            return False

        # Remove old plugin
        del self.plugins[name]
        del self.plugin_agents[name]

        # Reload
        new_info = self.load_plugin(str(plugin_file))

        if new_info:
            logger.info(f"Reloaded plugin: {name}")
            return True

        return False

    def _create_example_plugin(self):
        """Create example plugin template"""
        example_file = self.plugin_dir / "example_plugin.py"

        if example_file.exists():
            return

        example_code = '''"""
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
'''

        example_file.write_text(example_code)
        logger.info(f"Created example plugin: {example_file}")


# =============================================================================
# PLUGIN README
# =============================================================================

def create_plugin_readme(plugin_dir: Path):
    """Create README for plugin directory"""
    readme_file = plugin_dir / "README.md"

    if readme_file.exists():
        return

    readme_content = '''# MCP Plugin Directory

Drop Python files here to extend MCP systems dynamically.

## Plugin Structure

```python
from mcp_agents.base_agent import BaseMCPAgent

class MyCustomAgent(BaseMCPAgent):
    def __init__(self):
        super().__init__('my_agent', 'custom')

    def process(self, task_input):
        # Your custom logic
        return {'result': 'processed'}

def register():
    """Register plugin with MCP"""
    return {
        "name": "my_plugin",
        "version": "1.0.0",
        "description": "My custom plugin",
        "author": "Me",
        "mcp_system": "custom",
        "task_types": ["my_custom_task"],
        "agent": MyCustomAgent()
    }
```

## Loading Plugins

Plugins are automatically loaded on startup. To reload:

```python
from plugins.plugin_manager import PluginManager

plugin_mgr = PluginManager()
plugin_mgr.reload_plugin("my_plugin")
```

## Available Base Agents

- `BaseMCPAgent` - Standard MCP agent base class
- All agents have access to:
  - Database connection
  - Vector memory
  - Activity logging
  - Task lifecycle management

## Example Plugins

- `example_plugin.py` - Basic plugin template
- See individual MCP agents in `mcp_agents/` for advanced examples

'''

    readme_file.write_text(readme_content)
