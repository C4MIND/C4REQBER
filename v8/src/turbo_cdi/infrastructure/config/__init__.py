"""
Configuration settings for TURBO-CDI v8.4
Using pydantic-settings for type-safe configuration.
"""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Database
    database_url: str = "sqlite+aiosqlite:///./turbo_cdi.db"

    # LLM Configuration
    llm_api_key: str = ""
    llm_model: str = "gpt-4"
    llm_timeout: int = 30
    llm_max_tokens: int = 2048

    # Discovery
    discovery_anomaly_threshold: float = 0.7
    discovery_max_gaps: int = 10

    # Application
    log_level: str = "INFO"
    debug_mode: bool = False

    # Paths
    data_dir: Path = Path("./data")
    vector_store_path: Path = Path("./data/vector_store")
    temp_dir: Path = Path("./temp")

    class Config:
        env_file = ".env"
        env_prefix = "TURBO_CDI_"
        case_sensitive = False
