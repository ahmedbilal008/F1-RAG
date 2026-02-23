"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    # --- API Keys ---
    GOOGLE_API_KEY: str
    PINECONE_API_KEY: str

    # --- Pinecone ---
    PINECONE_INDEX_NAME: str = "f1-knowledge-base"
    PINECONE_CLOUD: str = "aws"
    PINECONE_REGION: str = "us-east-1"

    # --- Embedding ---
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    EMBEDDING_DIMENSION: int = 768

    # --- Chunking ---
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 200

    # --- Retrieval ---
    TOP_K_RESULTS: int = 5
    SIMILARITY_THRESHOLD: float = 0.70

    # --- LLM ---
    LLM_MODEL: str = "gemini-2.5-flash"
    LLM_TEMPERATURE: float = 0.3
    MAX_TOKENS: int = 2048

    # --- Application ---
    APP_NAME: str = "F1 RAG Assistant"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:3000,https://localhost:3000"

    # --- Ingestion ---
    SCRAPE_DELAY: float = 1.0
    SCRAPE_TIMEOUT: int = 15
    SCRAPE_RETRIES: int = 3
    ERGAST_BASE_URL: str = "https://api.jolpi.ca/ergast/f1"
    OPENF1_BASE_URL: str = "https://api.openf1.org/v1"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
