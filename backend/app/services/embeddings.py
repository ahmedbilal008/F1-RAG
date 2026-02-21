"""Embedding provider abstraction layer."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("embeddings")


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    def embed_documents(self, texts: List[str], batch_size: int = 20) -> List[List[float]]:
        """Generate embeddings for a batch of documents."""
        ...

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query."""
        ...

    @abstractmethod
    def get_dimension(self) -> int:
        """Return the embedding vector dimension."""
        ...


class GoogleEmbeddingProvider(EmbeddingProvider):
    """
    Google Generative AI embedding provider.

    Uses the google-generativeai SDK directly (no LangChain dependency)
    for lighter weight and more control.
    """

    def __init__(self):
        settings = get_settings()
        # Import here to keep the dependency isolated to this provider
        import google.generativeai as genai

        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self._model_name = settings.EMBEDDING_MODEL
        self._dimension = settings.EMBEDDING_DIMENSION
        logger.info(f"GoogleEmbeddingProvider initialized (model={self._model_name}, dim={self._dimension})")

    def embed_documents(self, texts: List[str], batch_size: int = 20) -> List[List[float]]:
        """
        Generate embeddings for documents in batches.

        Rate-limit aware: stays under the free-tier limits.
        - 100 RPM (requests per minute)
        - 30K TPM (tokens per minute — ~4K tokens per 20-chunk batch)
        Paces at ~9s/batch to stay under ~7 batches/min (~28K TPM).
        """
        import google.generativeai as genai

        all_embeddings: List[List[float]] = []
        total_batches = (len(texts) + batch_size - 1) // batch_size

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_num = i // batch_size + 1
            logger.info(f"Embedding batch {batch_num}/{total_batches} ({len(batch)} texts)")

            try:
                results = genai.embed_content(
                    model=self._model_name,
                    content=batch,
                    task_type="retrieval_document",
                    output_dimensionality=self._dimension,
                )
                all_embeddings.extend(results["embedding"])
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    # Rate limited — back off and retry
                    logger.warning(f"Rate limited at batch {batch_num}, backing off 60s...")
                    time.sleep(60)
                    results = genai.embed_content(
                        model=self._model_name,
                        content=batch,
                        task_type="retrieval_document",
                        output_dimensionality=self._dimension,
                    )
                    all_embeddings.extend(results["embedding"])
                else:
                    logger.error(f"Embedding batch failed: {e}")
                    raise

            # Pace at ~9s/batch = ~7 batches/min = ~28K TPM (under 30K limit)
            if i + batch_size < len(texts):
                time.sleep(9)

        logger.info(f"Generated {len(all_embeddings)} document embeddings")
        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single search query."""
        import google.generativeai as genai

        try:
            result = genai.embed_content(
                model=self._model_name,
                content=text,
                task_type="retrieval_query",
                output_dimensionality=self._dimension,
            )
            return result["embedding"]
        except Exception as e:
            logger.error(f"Query embedding failed: {e}")
            raise

    def get_dimension(self) -> int:
        return self._dimension


_provider_instance: Optional[EmbeddingProvider] = None


def get_embedding_provider() -> EmbeddingProvider:
    """
    Get or create the singleton embedding provider.
    To switch providers, change this factory function.
    """
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = GoogleEmbeddingProvider()
    return _provider_instance
