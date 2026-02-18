"""Pinecone vector store with namespace-based isolation."""

from __future__ import annotations

import time
import hashlib
from typing import List, Dict, Any, Optional

from pinecone import Pinecone, ServerlessSpec

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.embeddings import get_embedding_provider

logger = get_logger("vector_store")


class VectorStore:
    """Manages the Pinecone vector index with namespace support."""

    def __init__(self):
        settings = get_settings()
        self._pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self._index_name = settings.PINECONE_INDEX_NAME
        self._dimension = settings.EMBEDDING_DIMENSION
        self._cloud = settings.PINECONE_CLOUD
        self._region = settings.PINECONE_REGION
        self._index = None
        self._embedding_provider = get_embedding_provider()
        logger.info(f"VectorStore created for index={self._index_name}")

    def _ensure_index(self) -> bool:
        """Create the index if it doesn't exist, then cache the Index handle."""
        if self._index is not None:
            return True

        try:
            existing = [idx.name for idx in self._pc.list_indexes()]

            if self._index_name not in existing:
                logger.info(f"Creating new index: {self._index_name}")
                self._pc.create_index(
                    name=self._index_name,
                    dimension=self._dimension,
                    metric="cosine",
                    spec=ServerlessSpec(cloud=self._cloud, region=self._region),
                )
                # Wait until ready
                while not self._pc.describe_index(self._index_name).status["ready"]:
                    logger.debug("Waiting for index to be ready...")
                    time.sleep(1)
                logger.info(f"Index {self._index_name} created successfully")
            else:
                logger.info(f"Using existing index: {self._index_name}")

            self._index = self._pc.Index(self._index_name)
            return True
        except Exception as e:
            logger.error(f"Failed to ensure index: {e}")
            return False

    def upsert_documents(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        namespace: str,
        batch_size: int = 100,
    ) -> Dict[str, Any]:
        """
        Embed and upsert a batch of text chunks into a specific namespace.

        Each vector ID is a deterministic hash of (namespace + text[:200]),
        which means re-ingesting the same content is idempotent.
        """
        if not self._ensure_index():
            return {"success": False, "error": "Index not available"}

        try:
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(texts)} chunks (ns={namespace})")
            embeddings = self._embedding_provider.embed_documents(texts)

            if len(embeddings) != len(texts):
                return {"success": False, "error": "Embedding count mismatch"}

            upserted = 0
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i : i + batch_size]
                batch_embeddings = embeddings[i : i + batch_size]
                batch_metadatas = metadatas[i : i + batch_size]

                vectors = []
                for j, (txt, emb, meta) in enumerate(
                    zip(batch_texts, batch_embeddings, batch_metadatas)
                ):
                    # Deterministic ID for idempotent upserts
                    raw_id = f"{namespace}:{txt[:200]}"
                    vector_id = hashlib.sha256(raw_id.encode()).hexdigest()[:16]

                    # Pinecone metadata must be flat & <40KB
                    clean_meta = {
                        "text": txt[:3000],  # store text for retrieval display
                        "namespace": namespace,
                        **{k: v for k, v in meta.items() if isinstance(v, (str, int, float, bool))},
                    }

                    vectors.append(
                        {"id": vector_id, "values": emb, "metadata": clean_meta}
                    )

                self._index.upsert(vectors=vectors, namespace=namespace)
                upserted += len(vectors)
                logger.debug(f"Upserted batch {i // batch_size + 1}: {upserted}/{len(texts)}")
                time.sleep(0.3)  # rate-limit courtesy

            stats = self._index.describe_index_stats()
            return {
                "success": True,
                "upserted": upserted,
                "namespace": namespace,
                "total_vectors": stats.total_vector_count,
            }

        except Exception as e:
            logger.error(f"Upsert failed for ns={namespace}: {e}")
            return {"success": False, "error": str(e)}

    def delete_namespace(self, namespace: str) -> bool:
        """Delete all vectors in a namespace."""
        if not self._ensure_index():
            return False
        try:
            self._index.delete(delete_all=True, namespace=namespace)
            logger.info(f"Deleted namespace: {namespace}")
            return True
        except Exception as e:
            if "Namespace not found" in str(e) or "404" in str(e):
                logger.info(f"Namespace {namespace} already empty")
                return True
            logger.error(f"Delete namespace failed: {e}")
            return False

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def similarity_search(
        self,
        query: str,
        top_k: int = 5,
        namespace: Optional[str] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search.

        When namespace is None, queries ALL namespaces and merges results
        (Pinecone SDK v5 defaults to "" namespace, which is NOT "all").

        Args:
            query: Natural language query
            top_k: Number of results
            namespace: Pinecone namespace to search (None = search all)
            filter_dict: Metadata filter (e.g., {"category": "race_results"})
            score_threshold: Minimum similarity score to include
        """
        if not self._ensure_index():
            return []

        try:
            settings = get_settings()
            threshold = score_threshold or settings.SIMILARITY_THRESHOLD

            query_embedding = self._embedding_provider.embed_query(query)

            # Determine which namespaces to search
            if namespace:
                namespaces_to_search = [namespace]
            else:
                # Search all populated namespaces
                stats = self._index.describe_index_stats()
                namespaces_to_search = list(stats.namespaces.keys()) if stats.namespaces else [""]

            all_matches = []
            for ns in namespaces_to_search:
                kwargs: Dict[str, Any] = {
                    "vector": query_embedding,
                    "top_k": top_k,
                    "include_metadata": True,
                    "namespace": ns,
                }
                if filter_dict:
                    kwargs["filter"] = filter_dict

                results = self._index.query(**kwargs)
                for match in results.matches:
                    all_matches.append((match, ns))

            # Sort all matches by score descending and take top_k
            all_matches.sort(key=lambda x: x[0].score, reverse=True)
            top_matches = all_matches[:top_k]

            documents = []
            for match, ns in top_matches:
                if match.score >= threshold:
                    meta = match.metadata or {}
                    documents.append(
                        {
                            "id": match.id,
                            "content": meta.get("text", ""),
                            "score": round(match.score, 4),
                            "metadata": {
                                k: v for k, v in meta.items() if k != "text"
                            },
                        }
                    )

            logger.info(
                f"Search returned {len(documents)} documents "
                f"(query='{query[:50]}...', ns={namespace}, top_k={top_k}, "
                f"searched {len(namespaces_to_search)} namespace(s))"
            )
            return documents

        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        if not self._ensure_index():
            return {}
        try:
            stats = self._index.describe_index_stats()
            ns_info = {}
            if stats.namespaces:
                ns_info = {
                    ns: {"vector_count": data.vector_count}
                    for ns, data in stats.namespaces.items()
                }
            return {
                "total_vectors": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": ns_info,
            }
        except Exception as e:
            logger.error(f"Stats retrieval failed: {e}")
            return {}

    def check_connection(self) -> Dict[str, Any]:
        """Test Pinecone connectivity."""
        try:
            if not self._ensure_index():
                return {"connected": False, "error": "Index creation failed"}
            stats = self.get_stats()
            return {"connected": True, "index_name": self._index_name, "stats": stats}
        except Exception as e:
            return {"connected": False, "error": str(e)}


_store_instance: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create the singleton vector store."""
    global _store_instance
    if _store_instance is None:
        _store_instance = VectorStore()
    return _store_instance
