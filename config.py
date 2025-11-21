"""
CESAR Ecosystem - Centralized Configuration Management
======================================================

PhD-quality configuration management with:
- Type-safe configuration using Pydantic
- Environment variable validation
- Secure credential handling
- Configuration inheritance
- Clear error messages for missing values

Usage:
    from config import get_config

    config = get_config()
    db_url = config.database.url
    api_key = config.external_apis.openai_key
"""

import os
import sys
from typing import Optional
from pathlib import Path
from pydantic import BaseSettings, Field, validator, PostgresDsn, RedisDsn
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION SECTIONS
# =============================================================================

class DatabaseConfig(BaseSettings):
    """Database connection configuration"""

    host: str = Field(default="localhost", env="POSTGRES_HOST")
    port: int = Field(default=5432, env="POSTGRES_PORT")
    db: str = Field(..., env="POSTGRES_DB")  # Required
    user: str = Field(..., env="POSTGRES_USER")  # Required
    password: str = Field(..., env="POSTGRES_PASSWORD")  # Required

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def url(self) -> str:
        """Construct PostgreSQL connection URL"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"

    @property
    def async_url(self) -> str:
        """Construct async PostgreSQL connection URL"""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class RedisConfig(BaseSettings):
    """Redis connection configuration"""

    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    db: int = Field(default=0, env="REDIS_DB")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def url(self) -> str:
        """Construct Redis connection URL"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class APIConfig(BaseSettings):
    """API server configuration"""

    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    base_url: str = Field(default="http://localhost:8000", env="API_BASE_URL")

    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        env="CORS_ORIGINS"
    )

    # Security
    jwt_secret: str = Field(..., env="JWT_SECRET_KEY")  # Required
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")

    # API Keys
    api_key_enabled: bool = Field(default=True, env="API_KEY_ENABLED")
    api_key_header: str = Field(default="X-API-Key", env="API_KEY_HEADER")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins into list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]


class ExternalAPIConfig(BaseSettings):
    """External API credentials"""

    # OpenAI
    openai_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=2000, env="OPENAI_MAX_TOKENS")

    # Google Gemini
    gemini_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")

    # Financial Data
    fred_key: Optional[str] = Field(default=None, env="FRED_API_KEY")
    alpha_vantage_key: Optional[str] = Field(default=None, env="ALPHA_VANTAGE_API_KEY")

    # Patent/Innovation
    patent_key: Optional[str] = Field(default=None, env="INNO_PATENT_API_KEY")

    # Supabase
    supabase_url: Optional[str] = Field(default=None, env="SUPABASE_URL")
    supabase_key: Optional[str] = Field(default=None, env="SUPABASE_KEY")
    supabase_service_key: Optional[str] = Field(default=None, env="SUPABASE_SERVICE_KEY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class EmailAgentConfig(BaseSettings):
    """Email agent configuration"""

    user: str = Field(..., env="EMAIL_AGENT_USER")  # Required
    password: str = Field(..., env="EMAIL_AGENT_PASSWORD")  # Required
    imap_host: str = Field(default="imap.gmail.com", env="EMAIL_AGENT_IMAP_HOST")
    smtp_host: str = Field(default="smtp.gmail.com", env="EMAIL_AGENT_SMTP_HOST")
    smtp_port: int = Field(default=587, env="EMAIL_AGENT_SMTP_PORT")
    check_interval: int = Field(default=30, env="EMAIL_AGENT_CHECK_INTERVAL")
    trigger_subject: str = Field(default="CESAR.ai Agent", env="EMAIL_TRIGGER_SUBJECT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class MonitoringConfig(BaseSettings):
    """Monitoring and observability configuration"""

    # Prometheus
    prometheus_enabled: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")

    # Grafana
    grafana_port: int = Field(default=3001, env="GRAFANA_PORT")
    grafana_admin_password: str = Field(default="admin", env="GRAFANA_ADMIN_PASSWORD")

    # Sentry
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    sentry_environment: str = Field(default="production", env="SENTRY_ENVIRONMENT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class FeatureFlagsConfig(BaseSettings):
    """Feature flags and toggles"""

    # Core features
    security_headers_enabled: bool = Field(default=True, env="SECURITY_HEADERS_ENABLED")
    websocket_enabled: bool = Field(default=True, env="WEBSOCKET_ENABLED")
    hybrid_memory_enabled: bool = Field(default=True, env="HYBRID_MEMORY_ENABLED")
    plugin_system_enabled: bool = Field(default=True, env="PLUGIN_SYSTEM_ENABLED")

    # Chat features
    chat_caching_enabled: bool = Field(default=True, env="CHAT_CACHING_ENABLED")
    chat_cache_ttl: int = Field(default=300, env="CHAT_CACHE_TTL_SECONDS")

    # MCP systems
    finpsy_enabled: bool = Field(default=True, env="MCP_FINPSY_ENABLED")
    pydini_enabled: bool = Field(default=True, env="MCP_PYDINI_ENABLED")
    lex_enabled: bool = Field(default=True, env="MCP_LEX_ENABLED")
    inno_enabled: bool = Field(default=True, env="MCP_INNO_ENABLED")
    creative_enabled: bool = Field(default=True, env="MCP_CREATIVE_ENABLED")
    edu_enabled: bool = Field(default=True, env="MCP_EDU_ENABLED")
    omnicognition_enabled: bool = Field(default=True, env="MCP_OMNICOGNITION_ENABLED")
    security_enabled: bool = Field(default=True, env="MCP_SECURITY_ENABLED")
    protocol_enabled: bool = Field(default=True, env="MCP_PROTOCOL_ENABLED")
    skillforge_enabled: bool = Field(default=True, env="MCP_SKILLFORGE_ENABLED")
    central_enabled: bool = Field(default=True, env="MCP_CENTRAL_ENABLED")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class AppConfig(BaseSettings):
    """Application-level configuration"""

    environment: str = Field(default="production", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    testing: bool = Field(default=False, env="TESTING")

    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")

    orchestrator_api: str = Field(default="http://localhost:8000", env="ORCHESTRATOR_API")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @validator("log_level")
    def validate_log_level(cls, v):
        """Ensure log level is valid"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()


# =============================================================================
# MAIN CONFIGURATION CLASS
# =============================================================================

class CESARConfig:
    """
    Main configuration container for CESAR ecosystem.

    Loads all configuration sections and provides validation.
    """

    def __init__(self):
        """Initialize configuration with validation"""

        # Load environment file if it exists
        env_file = Path(__file__).parent / ".env"
        if not env_file.exists():
            logger.warning(f"⚠️  .env file not found at {env_file}")
            logger.warning("   Using environment variables and defaults")

        try:
            self.database = DatabaseConfig()
            self.redis = RedisConfig()
            self.api = APIConfig()
            self.external_apis = ExternalAPIConfig()
            self.email_agent = EmailAgentConfig()
            self.monitoring = MonitoringConfig()
            self.features = FeatureFlagsConfig()
            self.app = AppConfig()

        except Exception as e:
            logger.error(f"❌ Configuration validation failed: {e}")
            logger.error("   Check your .env file and environment variables")
            logger.error(f"   Required variables: POSTGRES_PASSWORD, JWT_SECRET_KEY, EMAIL_AGENT_PASSWORD")
            raise

        # Log configuration status
        self._log_config_status()

    def _log_config_status(self):
        """Log configuration loading status"""
        logger.info("✅ Configuration loaded successfully")
        logger.info(f"   Environment: {self.app.environment}")
        logger.info(f"   Database: {self.database.host}:{self.database.port}/{self.database.db}")
        logger.info(f"   Redis: {self.redis.host}:{self.redis.port}")
        logger.info(f"   API: {self.api.host}:{self.api.port}")

        # Warn about missing optional APIs
        if not self.external_apis.openai_key:
            logger.warning("⚠️  OpenAI API key not configured")
        if not self.external_apis.gemini_key:
            logger.warning("⚠️  Gemini API key not configured")

    def to_dict(self) -> dict:
        """Convert configuration to dictionary (excluding sensitive values)"""
        return {
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "db": self.database.db,
                "user": self.database.user,
            },
            "redis": {
                "host": self.redis.host,
                "port": self.redis.port,
            },
            "api": {
                "host": self.api.host,
                "port": self.api.port,
                "base_url": self.api.base_url,
            },
            "features": {
                "chat_caching": self.features.chat_caching_enabled,
                "websocket": self.features.websocket_enabled,
                "mcp_systems": {
                    "finpsy": self.features.finpsy_enabled,
                    "pydini": self.features.pydini_enabled,
                    "lex": self.features.lex_enabled,
                },
            },
            "app": {
                "environment": self.app.environment,
                "debug": self.app.debug,
                "log_level": self.app.log_level,
            }
        }


# =============================================================================
# SINGLETON ACCESSOR
# =============================================================================

@lru_cache(maxsize=1)
def get_config() -> CESARConfig:
    """
    Get singleton configuration instance.

    Uses LRU cache to ensure configuration is loaded only once.

    Returns:
        CESARConfig: Fully loaded and validated configuration

    Raises:
        ValidationError: If required environment variables are missing

    Example:
        >>> from config import get_config
        >>> config = get_config()
        >>> print(config.database.url)
        postgresql://user:password@localhost:5432/cesar_src
    """
    return CESARConfig()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_database_url() -> str:
    """Get database URL (synchronous)"""
    return get_config().database.url


def get_async_database_url() -> str:
    """Get async database URL"""
    return get_config().database.async_url


def get_redis_url() -> str:
    """Get Redis URL"""
    return get_config().redis.url


def is_feature_enabled(feature_name: str) -> bool:
    """
    Check if a feature is enabled.

    Args:
        feature_name: Name of the feature (e.g., 'chat_caching_enabled', 'finpsy_enabled')

    Returns:
        bool: True if feature is enabled

    Example:
        >>> from config import is_feature_enabled
        >>> if is_feature_enabled('chat_caching_enabled'):
        ...     print("Chat caching is ON")
    """
    config = get_config()
    return getattr(config.features, feature_name, False)


# =============================================================================
# INITIALIZATION
# =============================================================================

if __name__ == "__main__":
    """Test configuration loading"""
    print("🔧 Testing CESAR Configuration...")
    print()

    try:
        config = get_config()
        print("✅ Configuration loaded successfully!")
        print()
        print("📊 Configuration Summary:")
        print(f"   Environment: {config.app.environment}")
        print(f"   Database: {config.database.host}:{config.database.port}/{config.database.db}")
        print(f"   Redis: {config.redis.host}:{config.redis.port}")
        print(f"   API: {config.api.host}:{config.api.port}")
        print(f"   Chat Caching: {'✅ Enabled' if config.features.chat_caching_enabled else '❌ Disabled'}")
        print()
        print("🔑 External APIs:")
        print(f"   OpenAI: {'✅ Configured' if config.external_apis.openai_key else '❌ Not configured'}")
        print(f"   Gemini: {'✅ Configured' if config.external_apis.gemini_key else '❌ Not configured'}")
        print()

    except Exception as e:
        print(f"❌ Configuration loading failed:")
        print(f"   {e}")
        print()
        print("📝 Check your .env file and ensure all required variables are set:")
        print("   - POSTGRES_PASSWORD")
        print("   - JWT_SECRET_KEY")
        print("   - EMAIL_AGENT_PASSWORD")
        sys.exit(1)
