import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # --- Relational Database ---
    # PostgreSQL (Supabase) connection string.
    # If password contains special chars (@, :, /, etc.), URL-encode them
    # (e.g., password@123 -> password%40123).
    DATABASE_URL: str = ""

    @property
    def database_url(self) -> str:
        """Returns the database URL, falling back to SQLite if empty or connection fails."""
        return self.DATABASE_URL if self.DATABASE_URL else "sqlite:///./dcpr_dev.db"

    # --- Graph Database (Neo4j) ---
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password123"

    # --- LLM (Ollama) ---
    OLLAMA_URL: str = "http://localhost:11434/api/generate"
    OLLAMA_MODEL: str = "qwen3:8b"
    OLLAMA_TIMEOUT: int = 120  # seconds (qwen3:8b takes ~75s on CPU first load)

    # --- Supabase Storage (optional, falls back to local dir) ---
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    # --- RAG Pipeline ---
    CHUNK_SIZE: int = 1000        # tokens per chunk (dense regulatory text)
    CHUNK_OVERLAP: int = 100      # overlap tokens between chunks
    EMBED_MODEL: str = "all-MiniLM-L6-v2"
    RERANK_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RAG_TOP_K: int = 5            # final results after re-ranking
    RAG_SEARCH_K: int = 20        # candidates before re-ranking
    RAG_MIN_SCORE: float = 0.3    # minimum similarity threshold

    # --- Application ---
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:5173"
    STORAGE_DIR: str = str(Path(__file__).resolve().parent.parent.parent / "storage")

settings = Settings()

# Ensure local storage folder exists
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
