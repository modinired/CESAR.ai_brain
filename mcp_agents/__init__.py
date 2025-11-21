"""MCP Agents module with lazy-loading exports."""

import importlib
from typing import Any

__all__ = [
    'BaseMCPAgent',
    'PydiniRedOrchestrator',
    'FinPsyOrchestrator',
    'LexOrchestrator',
    'InnoOrchestrator',
    'CreativeOrchestrator',
    'EduOrchestrator',
    'CentralMCPOrchestrator'
]

_LAZY_IMPORTS = {
    'BaseMCPAgent': 'base_agent',
    'PydiniRedOrchestrator': 'pydini_red',
    'FinPsyOrchestrator': 'finpsy',
    'LexOrchestrator': 'lex',
    'InnoOrchestrator': 'inno',
    'CreativeOrchestrator': 'creative',
    'EduOrchestrator': 'edu',
    'CentralMCPOrchestrator': 'central_orchestrator'
}

__version__ = '1.0.0'


def __getattr__(name: str) -> Any:
    if name in _LAZY_IMPORTS:
        module = importlib.import_module(f"{__name__}.{_LAZY_IMPORTS[name]}")
        attr = getattr(module, name)
        globals()[name] = attr
        return attr
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
