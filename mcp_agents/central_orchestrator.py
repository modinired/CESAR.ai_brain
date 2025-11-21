"""
Central MCP Orchestrator - Main Overseer of CESAR Agent Ecosystem
=====================================================================

This is the TOP-LEVEL orchestrator that coordinates all MCP systems and
integrates with the existing multi-agent learning ecosystem.

Hierarchy:
----------
Level 1: Central MCP Orchestrator (THIS FILE) - Main Overseer
Level 2: Individual MCP Orchestrators (FinPsy, PydiniRed, Lex, Inno, Creative, Edu)
Level 3: Specialized Agents (30+ agents across all systems)

The Central Orchestrator:
- Routes tasks to appropriate MCP systems
- Coordinates cross-system workflows
- Manages unified vector memory
- Provides centralized logging and metrics
- Integrates with the multi-agent learning ecosystem
"""

import importlib
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import os

from .base_agent import BaseMCPAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class CentralMCPOrchestrator:
    """
    Central MCP Orchestrator - Main overseer of the entire CESAR agent ecosystem

    This orchestrator:
    1. Routes tasks to appropriate MCP systems based on task type
    2. Coordinates complex multi-system workflows
    3. Manages shared resources (vector memory, logging, metrics)
    4. Provides unified API for all MCP operations
    5. Integrates seamlessly with the multi-agent learning ecosystem
    """

    def __init__(
        self,
        db_dsn: str = None,
        openai_api_key: str = None,
        fred_api_key: str = None
    ):
        """
        Initialize the Central MCP Orchestrator

        Args:
            db_dsn: PostgreSQL connection string
            openai_api_key: OpenAI API key for AI operations
            fred_api_key: FRED API key for macro data
        """
        self.db_dsn = db_dsn or os.getenv(
            "DATABASE_URL",
            "postgresql://mcp_user:change-this-in-production-use-strong-password@postgres:5432/mcp"
        )

        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.fred_api_key = fred_api_key or os.getenv("FRED_API_KEY")

        self.logger = logging.getLogger("CentralMCPOrchestrator")
        self.logger.info("Initializing Central MCP Orchestrator - Main Overseer")

        # Initialize all MCP system orchestrators
        self._initialize_mcp_systems()

        # Task routing table
        self._initialize_task_routing()

        self.logger.info(
            f"Central MCP Orchestrator initialized with {len(self.mcp_systems)} systems"
        )

    def _load_orchestrator(self, module_name: str, class_name: str):
        """Dynamically import orchestrator classes to avoid hard dependencies."""
        module = importlib.import_module(f"{__package__}.{module_name}")
        return getattr(module, class_name)

    def _initialize_mcp_systems(self):
        """Initialize all MCP system orchestrators"""
        self.mcp_systems = {}

        try:
            # FinPsy - Financial Psychology & Analytics
            FinPsyOrchestrator = self._load_orchestrator('finpsy', 'FinPsyOrchestrator')
            self.mcp_systems['finpsy'] = FinPsyOrchestrator(
                db_dsn=self.db_dsn,
                fred_api_key=self.fred_api_key
            )
            self.logger.info("✓ FinPsyMCP orchestrator initialized")

        except Exception as e:
            self.logger.error(f"✗ Failed to initialize FinPsyMCP: {e}")

        try:
            # PydiniRed - Workflow Automation
            PydiniRedOrchestrator = self._load_orchestrator('pydini_red', 'PydiniRedOrchestrator')
            self.mcp_systems['pydini_red'] = PydiniRedOrchestrator(
                db_dsn=self.db_dsn
            )
            self.logger.info("✓ PydiniRedMCP orchestrator initialized")

        except Exception as e:
            self.logger.error(f"✗ Failed to initialize PydiniRedMCP: {e}")

        try:
            # Lex - Legal Compliance
            LexOrchestrator = self._load_orchestrator('lex', 'LexOrchestrator')
            self.mcp_systems['lex'] = LexOrchestrator(
                db_dsn=self.db_dsn,
                openai_api_key=self.openai_api_key
            )
            self.logger.info("✓ LexMCP orchestrator initialized")

        except Exception as e:
            self.logger.error(f"✗ Failed to initialize LexMCP: {e}")

        try:
            # Inno - Innovation Management
            InnoOrchestrator = self._load_orchestrator('inno', 'InnoOrchestrator')
            self.mcp_systems['inno'] = InnoOrchestrator(
                db_dsn=self.db_dsn,
                openai_api_key=self.openai_api_key
            )
            self.logger.info("✓ InnoMCP orchestrator initialized")

        except Exception as e:
            self.logger.error(f"✗ Failed to initialize InnoMCP: {e}")

        try:
            # Creative - Creative Content
            CreativeOrchestrator = self._load_orchestrator('creative', 'CreativeOrchestrator')
            self.mcp_systems['creative'] = CreativeOrchestrator(
                db_dsn=self.db_dsn,
                openai_api_key=self.openai_api_key
            )
            self.logger.info("✓ CreativeMCP orchestrator initialized")

        except Exception as e:
            self.logger.error(f"✗ Failed to initialize CreativeMCP: {e}")

        try:
            # Edu - Adaptive Education
            EduOrchestrator = self._load_orchestrator('edu', 'EduOrchestrator')
            self.mcp_systems['edu'] = EduOrchestrator(
                db_dsn=self.db_dsn,
                openai_api_key=self.openai_api_key
            )
            self.logger.info("✓ EduMCP orchestrator initialized")

        except Exception as e:
            self.logger.error(f"✗ Failed to initialize EduMCP: {e}")

    def _initialize_task_routing(self):
        """Initialize task type to MCP system routing"""
        self.task_routing = {
            # Financial tasks -> FinPsy
            'financial_analysis': 'finpsy',
            'stock_analysis': 'finpsy',
            'portfolio_optimization': 'finpsy',
            'market_forecast': 'finpsy',
            'sentiment_analysis': 'finpsy',
            'business_health': 'finpsy',

            # Workflow tasks -> PydiniRed
            'workflow_conversion': 'pydini_red',
            'workflow_automation': 'pydini_red',
            'script_generation': 'pydini_red',

            # Legal tasks -> Lex
            'legal_analysis': 'lex',
            'contract_review': 'lex',
            'compliance_check': 'lex',
            'regulatory_tracking': 'lex',

            # Innovation tasks -> Inno
            'patent_search': 'inno',
            'market_trends': 'inno',
            'idea_generation': 'inno',
            'competitor_analysis': 'inno',

            # Creative tasks -> Creative
            'content_generation': 'creative',
            'script_writing': 'creative',
            'visual_design': 'creative',
            'music_composition': 'creative',

            # Education tasks -> Edu
            'learning_path': 'edu',
            'curriculum_design': 'edu',
            'learner_profiling': 'edu',
            'content_recommendation': 'edu'
        }

    def route_task(
        self,
        task_type: str,
        task_data: Dict[str, Any],
        material_id: Optional[uuid.UUID] = None,
        priority: int = 5
    ) -> Dict[str, Any]:
        """
        Route a task to the appropriate MCP system

        Args:
            task_type: Type of task (determines routing)
            task_data: Task input data
            material_id: Optional related learning material
            priority: Task priority (1-10)

        Returns:
            Dict with task results
        """
        self.logger.info(f"Routing task: {task_type}")

        # Determine target MCP system
        mcp_system = self.task_routing.get(task_type)

        if not mcp_system:
            # Try to infer from task type keywords
            task_lower = task_type.lower()

            if any(kw in task_lower for kw in ['finance', 'stock', 'market', 'portfolio']):
                mcp_system = 'finpsy'
            elif any(kw in task_lower for kw in ['workflow', 'automation', 'script']):
                mcp_system = 'pydini_red'
            elif any(kw in task_lower for kw in ['legal', 'contract', 'compliance']):
                mcp_system = 'lex'
            elif any(kw in task_lower for kw in ['innovation', 'patent', 'idea']):
                mcp_system = 'inno'
            elif any(kw in task_lower for kw in ['creative', 'content', 'script', 'visual']):
                mcp_system = 'creative'
            elif any(kw in task_lower for kw in ['education', 'learning', 'curriculum']):
                mcp_system = 'edu'
            else:
                return {
                    'status': 'error',
                    'error': f'Unknown task type: {task_type}',
                    'available_systems': list(self.mcp_systems.keys())
                }

        if mcp_system not in self.mcp_systems:
            return {
                'status': 'error',
                'error': f'MCP system {mcp_system} not initialized'
            }

        # Route to appropriate orchestrator
        orchestrator = self.mcp_systems[mcp_system]

        try:
            result = orchestrator.execute_task(
                task_type=task_type,
                task_input=task_data,
                material_id=material_id,
                priority=priority
            )

            self.logger.info(f"Task routed to {mcp_system}: {result.get('status')}")

            return {
                'status': 'success',
                'mcp_system': mcp_system,
                'result': result
            }

        except Exception as e:
            self.logger.error(f"Error executing task in {mcp_system}: {e}")
            return {
                'status': 'error',
                'mcp_system': mcp_system,
                'error': str(e)
            }

    def execute_multi_system_workflow(
        self,
        workflow_steps: List[Dict[str, Any]],
        workflow_name: str = "multi_system_workflow"
    ) -> Dict[str, Any]:
        """
        Execute a workflow that spans multiple MCP systems

        Args:
            workflow_steps: List of workflow steps, each containing:
                - task_type: str
                - task_data: Dict
                - depends_on: Optional[int] (index of previous step)
            workflow_name: Name of the workflow

        Returns:
            Dict with workflow results
        """
        self.logger.info(f"Executing multi-system workflow: {workflow_name}")

        workflow_id = str(uuid.uuid4())
        results = []
        context = {}  # Shared context across steps

        for idx, step in enumerate(workflow_steps):
            step_name = step.get('name', f'step_{idx}')
            task_type = step['task_type']
            task_data = step['task_data'].copy()

            # Handle dependencies
            depends_on = step.get('depends_on')
            if depends_on is not None and depends_on < len(results):
                # Merge previous step output into current step input
                prev_result = results[depends_on].get('result', {}).get('output', {})
                task_data['previous_step_output'] = prev_result
                context.update(prev_result)

            # Add shared context
            task_data['workflow_context'] = context

            self.logger.info(f"Executing workflow step {idx + 1}/{len(workflow_steps)}: {step_name}")

            # Execute step
            step_result = self.route_task(
                task_type=task_type,
                task_data=task_data,
                priority=step.get('priority', 5)
            )

            step_result['step_name'] = step_name
            step_result['step_index'] = idx
            results.append(step_result)

            # Update context
            if step_result.get('status') == 'success':
                output = step_result.get('result', {}).get('output', {})
                context[step_name] = output

        # Compile workflow summary
        successful = sum(1 for r in results if r.get('status') == 'success')
        failed = len(results) - successful

        return {
            'workflow_id': workflow_id,
            'workflow_name': workflow_name,
            'total_steps': len(workflow_steps),
            'successful_steps': successful,
            'failed_steps': failed,
            'status': 'completed' if failed == 0 else 'partial_failure',
            'results': results,
            'context': context
        }

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get status of all MCP systems

        Returns:
            Dict with system status
        """
        status = {
            'timestamp': datetime.now().isoformat(),
            'systems': {}
        }

        for system_name, orchestrator in self.mcp_systems.items():
            try:
                # Try to get status from orchestrator
                if hasattr(orchestrator, 'get_status'):
                    status['systems'][system_name] = orchestrator.get_status()
                else:
                    status['systems'][system_name] = {'status': 'active'}
            except Exception as e:
                status['systems'][system_name] = {
                    'status': 'error',
                    'error': str(e)
                }

        return status

    def get_available_tasks(self) -> Dict[str, List[str]]:
        """
        Get list of all available task types across all systems

        Returns:
            Dict mapping system to task types
        """
        available = {}

        for system_name in self.mcp_systems.keys():
            tasks = [
                task_type for task_type, system in self.task_routing.items()
                if system == system_name
            ]
            available[system_name] = tasks

        return available


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_central_orchestrator(
    db_dsn: str = None,
    openai_api_key: str = None,
    fred_api_key: str = None
) -> CentralMCPOrchestrator:
    """
    Factory function to create Central MCP Orchestrator

    Args:
        db_dsn: Database connection string
        openai_api_key: OpenAI API key
        fred_api_key: FRED API key

    Returns:
        CentralMCPOrchestrator instance
    """
    return CentralMCPOrchestrator(
        db_dsn=db_dsn,
        openai_api_key=openai_api_key,
        fred_api_key=fred_api_key
    )


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

if __name__ == "__main__":
    # Initialize the main overseer
    orchestrator = create_central_orchestrator()

    # Example 1: Route a single task
    result = orchestrator.route_task(
        task_type='stock_analysis',
        task_data={'ticker': 'AAPL', 'start_date': '2023-01-01'}
    )
    print("Single Task Result:", result)

    # Example 2: Execute multi-system workflow
    workflow = orchestrator.execute_multi_system_workflow(
        workflow_steps=[
            {
                'name': 'analyze_stock',
                'task_type': 'stock_analysis',
                'task_data': {'ticker': 'AAPL'}
            },
            {
                'name': 'generate_report',
                'task_type': 'content_generation',
                'task_data': {'content_type': 'financial_report'},
                'depends_on': 0  # Depends on first step
            }
        ],
        workflow_name="stock_analysis_with_report"
    )
    print("Workflow Result:", workflow)

    # Example 3: Check system status
    status = orchestrator.get_system_status()
    print("System Status:", status)
