from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """TURBO-CDI v8.3 Configuration Settings"""

    # Paths
    data_dir: Path = Path.home() / ".turbo-cdi"
    vector_store_path: Path = Path.home() / ".turbo-cdi" / "chroma"
    temp_dir: Path = Path("/tmp")

    # LLM Providers
    groq_api_key: str = ""
    groq_model_default: str = "llama-3.3-70b-versatile"
    openrouter_api_key: str = ""
    openrouter_model_default: str = "qwen/qwen-2.5-72b-instruct"
    ollama_url: str = "http://localhost:11434"
    ollama_model_default: str = "qwen2.5:14b"

    # Timeouts (seconds)
    llm_timeout: int = 10
    http_timeout: int = 30
    websocket_timeout: int = 30

    # Rate Limits
    ws_rate_limit_per_minute: int = 60
    llm_requests_per_minute: int = 30

    # RAG Configuration
    rag_chunk_size: int = 500
    rag_chunk_overlap: int = 50
    rag_top_k_default: int = 5
    rag_embedding_model: str = "all-MiniLM-L6-v2"

    # Discovery Configuration
    discovery_max_gaps: int = 10
    discovery_corpus_cache_days: int = 7

    # Falsification
    falsification_max_trials: int = 10000
    falsification_min_trials: int = 100

    # Bias Detection
    bias_confidence_threshold: float = 0.7
    bias_severity_threshold: float = 0.5

    class Config:
        env_file = ".env"
        env_prefix = "TURBO_"
        case_sensitive = False
