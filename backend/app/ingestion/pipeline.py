"""Ingestion pipeline orchestrator — scrape, chunk, embed, upsert."""

from __future__ import annotations

import time
from typing import Dict, Any, List, Optional

from app.core.logging import get_logger
from app.ingestion.wikipedia_scraper import WikipediaScraper, ScrapedDocument
from app.ingestion.ergast_client import ErgastClient
from app.ingestion.chunker import chunk_text, Chunk
from app.services.vector_store import get_vector_store

logger = get_logger("pipeline")


# Namespace mapping for Ergast categories
ERGAST_NAMESPACE_MAP = {
    "race_results": "ergast-results",
    "standings": "ergast-results",
    "drivers": "ergast-drivers",
    "constructors": "ergast-constructors",
}


def _chunks_to_vectors(
    chunks: List[Chunk],
) -> tuple[List[str], List[Dict[str, Any]]]:
    """Convert Chunk objects to parallel lists of texts and metadatas."""
    texts = [c.text for c in chunks]
    metadatas = [c.metadata for c in chunks]
    return texts, metadatas


def ingest_wikipedia(force_refresh: bool = False) -> Dict[str, Any]:
    """Run the Wikipedia ingestion pipeline."""
    start = time.perf_counter()
    store = get_vector_store()
    scraper = WikipediaScraper()

    # 1. Scrape
    documents, scrape_stats = scraper.scrape_all(force_refresh=force_refresh)

    if not documents:
        return {
            "success": False,
            "source": "wikipedia",
            "error": "No documents scraped",
            "stats": scrape_stats,
        }

    # 2. Optional: clear namespace on force refresh
    if force_refresh:
        store.delete_namespace("wikipedia")
        time.sleep(1)

    # 3. Chunk & upsert
    all_chunks: List[Chunk] = []
    for doc in documents:
        source_meta = {
            "source": doc.url,
            "title": doc.title,
            "category": doc.category,
            "priority": doc.priority,
        }
        chunks = chunk_text(doc.content, source_metadata=source_meta)
        all_chunks.extend(chunks)

    texts, metadatas = _chunks_to_vectors(all_chunks)
    result = store.upsert_documents(texts, metadatas, namespace="wikipedia")

    duration = round(time.perf_counter() - start, 2)
    return {
        "success": result.get("success", False),
        "source": "wikipedia",
        "documents_scraped": len(documents),
        "chunks_created": len(all_chunks),
        "vectors_upserted": result.get("upserted", 0),
        "scrape_stats": scrape_stats,
        "duration_seconds": duration,
    }


def ingest_ergast(force_refresh: bool = False, years: Optional[List[int]] = None) -> Dict[str, Any]:
    """Run the Ergast API ingestion pipeline."""
    start = time.perf_counter()
    store = get_vector_store()
    client = ErgastClient()

    # 1. Fetch
    documents, fetch_stats = client.fetch_all(years=years)

    if not documents:
        return {
            "success": False,
            "source": "ergast",
            "error": "No documents fetched",
            "stats": fetch_stats,
        }

    # 2. Optional: clear relevant namespaces on force refresh
    if force_refresh:
        for ns in set(ERGAST_NAMESPACE_MAP.values()):
            store.delete_namespace(ns)
        time.sleep(1)

    # 3. Group by namespace, chunk, and upsert
    ns_groups: Dict[str, List[Chunk]] = {}

    for doc in documents:
        namespace = ERGAST_NAMESPACE_MAP.get(doc.category, "ergast-results")
        source_meta = {
            "source": doc.url,
            "title": doc.title,
            "category": doc.category,
            "priority": doc.priority,
        }
        chunks = chunk_text(doc.content, source_metadata=source_meta)

        if namespace not in ns_groups:
            ns_groups[namespace] = []
        ns_groups[namespace].extend(chunks)

    total_upserted = 0
    total_chunks = 0
    for namespace, chunks in ns_groups.items():
        texts, metadatas = _chunks_to_vectors(chunks)
        result = store.upsert_documents(texts, metadatas, namespace=namespace)
        total_upserted += result.get("upserted", 0)
        total_chunks += len(chunks)
        logger.info(f"Upserted {result.get('upserted', 0)} vectors to '{namespace}'")

    duration = round(time.perf_counter() - start, 2)
    return {
        "success": True,
        "source": "ergast",
        "documents_fetched": len(documents),
        "chunks_created": total_chunks,
        "vectors_upserted": total_upserted,
        "fetch_stats": fetch_stats,
        "namespaces_used": list(ns_groups.keys()),
        "duration_seconds": duration,
    }


def ingest_all(force_refresh: bool = False) -> Dict[str, Any]:
    """Run all ingestion pipelines."""
    results = {}

    logger.info("Starting full ingestion pipeline...")

    # Wikipedia
    results["wikipedia"] = ingest_wikipedia(force_refresh=force_refresh)

    # Ergast
    results["ergast"] = ingest_ergast(force_refresh=force_refresh)

    # Summary
    total_chunks = sum(r.get("chunks_created", 0) for r in results.values())
    total_vectors = sum(r.get("vectors_upserted", 0) for r in results.values())
    all_success = all(r.get("success", False) for r in results.values())

    logger.info(
        f"Full ingestion complete: {total_chunks} chunks, "
        f"{total_vectors} vectors, success={all_success}"
    )

    return {
        "success": all_success,
        "total_chunks": total_chunks,
        "total_vectors": total_vectors,
        "pipelines": results,
    }
