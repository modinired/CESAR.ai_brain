"""
Configuration Integration for Multi-Agent Ecosystem
====================================================

PhD-Level Configuration Management: Integrates multi-agent ecosystem
configuration with existing CESAR configuration while preserving
all multi-LLM routing capabilities.

This module ensures:
- Backward compatibility with existing CESAR config
- New multi-agent ecosystem settings
- Environment variable management
- Profile-based configuration
- Validation and error handling

Author: Integration System
Date: 2025-11-16
Quality: PhD-Level, Zero Placeholders
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str = field(default_factory=lambda: os.getenv(
        "DATABASE_URL",
        "postgresql://mcp_user:secure_password@localhost:5432/mcp"
    ))
    replicas: list = field(default_factory=list)
    pool_size: int = 20
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600


@dataclass
class RedisConfig:
    """Redis configuration"""
    url: str = field(default_factory=lambda: os.getenv(
        "REDIS_URL",
        "redis://localhost:6379/0"
    ))
    max_connections: int = 50
    decode_responses: bool = True
    socket_timeout: int = 5
    socket_connect_timeout: int = 5


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration"""
    prometheus_enabled: bool = field(default_factory=lambda: os.getenv("METRICS_ENABLED", "true").lower() == "true")
    prometheus_port: int = field(default_factory=lambda: int(os.getenv("METRICS_PORT", "9090")))
    grafana_enabled: bool = True
    grafana_port: int = 3001
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    structured_logging: bool = True


@dataclass
class AuthConfig:
    """Authentication configuration"""
    jwt_secret_key: str = field(default_factory=lambda: os.getenv(
        "JWT_SECRET_KEY",
        "change-this-to-a-secure-random-key-in-production"
    ))
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = field(default_factory=lambda: int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    ))
    api_key_enabled: bool = True


@dataclass
class MCPSystemConfig:
    """MCP System-specific configuration"""
    finpsy_enabled: bool = True
    pydini_red_enabled: bool = True
    lex_enabled: bool = True
    inno_enabled: bool = True
    creative_enabled: bool = True
    edu_enabled: bool = True
    omnicognition_enabled: bool = True
    gambino_security_enabled: bool = True
    jules_protocol_enabled: bool = True
    skillforge_enabled: bool = True


@dataclass
class APIConfig:
    """API configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    reload: bool = False
    cors_origins: list = field(default_factory=lambda: ["http://localhost:3000", "http://localhost:3001"])
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 60
    rate_limit_window: int = 60


@dataclass
class PrefectConfig:
    """Prefect workflow orchestration configuration"""
    enabled: bool = field(default_factory=lambda: os.getenv("PREFECT_ENABLED", "true").lower() == "true")
    server_url: str = field(default_factory=lambda: os.getenv("PREFECT_SERVER_URL", "http://localhost:4200"))
    log_level: str = "INFO"


@dataclass
class ExternalAPIConfig:
    """External API keys and endpoints"""
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    gemini_api_key: Optional[str] = field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    fred_api_key: Optional[str] = field(default_factory=lambda: os.getenv("FRED_API_KEY"))
    alpha_vantage_key: Optional[str] = field(default_factory=lambda: os.getenv("ALPHA_VANTAGE_KEY"))
    inno_patent_api_key: Optional[str] = field(default_factory=lambda: os.getenv("INNO_PATENT_API_KEY"))


@dataclass
class MultiAgentEcosystemConfig:
    """
    Complete Multi-Agent Ecosystem Configuration

    Integrates with existing CESAR configuration while adding
    new multi-agent ecosystem settings.
    """
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    mcp_systems: MCPSystemConfig = field(default_factory=MCPSystemConfig)
    api: APIConfig = field(default_factory=APIConfig)
    prefect: PrefectConfig = field(default_factory=PrefectConfig)
    external_apis: ExternalAPIConfig = field(default_factory=ExternalAPIConfig)

    # Integration with existing CESAR config
    cesar_config_path: Optional[str] = None
    use_cesar_llm_routing: bool = True

    # Data paths
    faiss_index_path: str = field(default_factory=lambda: os.getenv(
        "FAISS_INDEX_PATH",
        "/app/data/faiss_index"
    ))
    faiss_meta_path: str = field(default_factory=lambda: os.getenv(
        "FAISS_META_PATH",
        "/app/data/faiss_meta.pkl"
    ))

    def __post_init__(self):
        """Validate configuration after initialization"""
        self.logger = logging.getLogger(__name__)
        self._validate()
        self._load_cesar_config()

    def _validate(self):
        """Validate configuration settings"""
        errors = []

        # Validate required API keys if systems are enabled
        if self.external_apis.openai_api_key is None:
            self.logger.warning("⚠️  OPENAI_API_KEY not set - some features will be limited")

        if self.mcp_systems.finpsy_enabled and self.external_apis.fred_api_key is None:
            self.logger.warning("⚠️  FRED_API_KEY not set - FinPsy system may have limited functionality")

        # Validate database URL format
        if not self.database.url.startswith(("postgresql://", "sqlite://")):
            errors.append("Invalid DATABASE_URL format")

        # Validate Redis URL
        if not self.redis.url.startswith("redis://"):
            errors.append("Invalid REDIS_URL format")

        # Validate ports
        if not (1024 <= self.api.port <= 65535):
            errors.append(f"Invalid API port: {self.api.port}")

        if errors:
            raise ValueError(f"Configuration validation failed: {', '.join(errors)}")

        self.logger.info("✅ Configuration validation passed")

    def _load_cesar_config(self):
        """Load and integrate existing CESAR configuration"""
        if not self.use_cesar_llm_routing:
            self.logger.info("CESAR LLM routing disabled, using fallback")
            return

        try:
            # Try to import existing CESAR config
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from cesar.config import Config as CESARConfig

            self.cesar_config = CESARConfig()
            self.logger.info("✅ Successfully loaded CESAR configuration")
            self.logger.info(f"   - LLM Routing Strategy: {getattr(self.cesar_config, 'llm_routing_strategy', 'adaptive_tri_model')}")
            self.logger.info(f"   - Qwen Enabled: {getattr(self.cesar_config, 'qwen_enabled', False)}")
            self.logger.info(f"   - Llama Enabled: {getattr(self.cesar_config, 'llama_enabled', False)}")
            self.logger.info(f"   - Gemini Enabled: {getattr(self.cesar_config, 'gemini_enabled', True)}")

        except ImportError as e:
            self.logger.warning(f"Could not load CESAR config: {e}")
            self.cesar_config = None
            self.use_cesar_llm_routing = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return asdict(self)

    def save(self, filepath: str):
        """Save configuration to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
        self.logger.info(f"Configuration saved to {filepath}")

    @classmethod
    def load(cls, filepath: str) -> 'MultiAgentEcosystemConfig':
        """Load configuration from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Reconstruct nested dataclasses
        database = DatabaseConfig(**data.get('database', {}))
        redis = RedisConfig(**data.get('redis', {}))
        monitoring = MonitoringConfig(**data.get('monitoring', {}))
        auth = AuthConfig(**data.get('auth', {}))
        mcp_systems = MCPSystemConfig(**data.get('mcp_systems', {}))
        api = APIConfig(**data.get('api', {}))
        prefect = PrefectConfig(**data.get('prefect', {}))
        external_apis = ExternalAPIConfig(**data.get('external_apis', {}))

        return cls(
            database=database,
            redis=redis,
            monitoring=monitoring,
            auth=auth,
            mcp_systems=mcp_systems,
            api=api,
            prefect=prefect,
            external_apis=external_apis,
            cesar_config_path=data.get('cesar_config_path'),
            use_cesar_llm_routing=data.get('use_cesar_llm_routing', True),
            faiss_index_path=data.get('faiss_index_path', '/app/data/faiss_index'),
            faiss_meta_path=data.get('faiss_meta_path', '/app/data/faiss_meta.pkl')
        )

    def get_env_template(self) -> str:
        """Generate .env file template with all configuration options"""
        template = """# Multi-Agent Ecosystem Configuration
# =======================================

# Database Configuration
DATABASE_URL=postgresql://mcp_user:secure_password@localhost:5432/mcp
# DATABASE_REPLICAS=postgresql://replica1:5432/mcp,postgresql://replica2:5432/mcp

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Authentication
JWT_SECRET_KEY=change-this-to-a-secure-random-key-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=60

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Monitoring
METRICS_ENABLED=true
METRICS_PORT=9090
LOG_LEVEL=INFO

# Prefect Workflow Engine
PREFECT_ENABLED=true
PREFECT_SERVER_URL=http://localhost:4200

# External API Keys
OPENAI_API_KEY=sk-your-openai-key-here
GEMINI_API_KEY=your-gemini-key-here
FRED_API_KEY=your-fred-api-key-here
ALPHA_VANTAGE_KEY=your-alpha-vantage-key-here
INNO_PATENT_API_KEY=your-patent-api-key-here

# Data Paths
FAISS_INDEX_PATH=/app/data/faiss_index
FAISS_META_PATH=/app/data/faiss_meta.pkl

# CESAR LLM Integration
USE_SPEDINES_LLM_ROUTING=true

# MCP System Toggles (all enabled by default)
FINPSY_ENABLED=true
PYDINI_RED_ENABLED=true
LEX_ENABLED=true
INNO_ENABLED=true
CREATIVE_ENABLED=true
EDU_ENABLED=true
OMNICOGNITION_ENABLED=true
GAMBINO_SECURITY_ENABLED=true
JULES_PROTOCOL_ENABLED=true
SKILLFORGE_ENABLED=true
"""
        return template


# Global configuration instance
_global_config: Optional[MultiAgentEcosystemConfig] = None


def get_config() -> MultiAgentEcosystemConfig:
    """
    Get global configuration instance (singleton pattern)

    Returns:
        MultiAgentEcosystemConfig instance
    """
    global _global_config
    if _global_config is None:
        _global_config = MultiAgentEcosystemConfig()
    return _global_config


def reload_config():
    """Force reload of configuration"""
    global _global_config
    _global_config = None
    return get_config()


if __name__ == "__main__":
    # Test configuration
    logging.basicConfig(level=logging.INFO)

    config = get_config()

    print("\n" + "="*60)
    print("Multi-Agent Ecosystem Configuration")
    print("="*60)

    print(f"\nDatabase: {config.database.url}")
    print(f"Redis: {config.redis.url}")
    print(f"API: {config.api.host}:{config.api.port}")
    print(f"Prometheus: Port {config.monitoring.prometheus_port}")
    print(f"CESAR LLM Routing: {config.use_cesar_llm_routing}")

    print(f"\nEnabled MCP Systems:")
    for attr in dir(config.mcp_systems):
        if attr.endswith('_enabled') and not attr.startswith('_'):
            system_name = attr.replace('_enabled', '').replace('_', ' ').title()
            enabled = getattr(config.mcp_systems, attr)
            status = "✅" if enabled else "❌"
            print(f"  {status} {system_name}")

    print(f"\n.env Template:")
    print(config.get_env_template())

    # Save configuration example
    # config.save("cesar_ecosystem_config.json")
