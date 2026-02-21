"""RAG evaluation module with a curated F1 test dataset."""

from __future__ import annotations

import time
from typing import List, Dict, Any

from app.core.logging import get_logger

logger = get_logger("evaluation")


EVALUATION_DATASET: List[Dict[str, Any]] = [
    {
        "question": "What major regulation changes are coming in 2026?",
        "expected_keywords": ["power unit", "active aerodynamics", "2026"],
        "category": "regulations",
    },
    {
        "question": "Is DRS being removed from Formula 1?",
        "expected_keywords": ["drs", "2026", "active aero"],
        "category": "technical",
    },
    {
        "question": "Which new teams are joining the F1 grid?",
        "expected_keywords": ["cadillac", "audi"],
        "category": "teams",
    },
    {
        "question": "What is Audi's involvement in F1 from 2026?",
        "expected_keywords": ["audi", "sauber", "2026"],
        "category": "teams",
    },
]


def _keyword_score(answer: str, expected_keywords: List[str]) -> float:
    """Calculate keyword coverage score (0.0 to 1.0)."""
    if not expected_keywords:
        return 1.0
    answer_lower = answer.lower()
    hits = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)
    return hits / len(expected_keywords)


async def run_evaluation(rag_chain) -> Dict[str, Any]:
    """
    Run evaluation on the test dataset.

    Returns per-question results and aggregate metrics.
    """
    from app.retrieval.rag_chain import RAGChain

    results: List[Dict[str, Any]] = []
    total_retrieval_ms = 0.0
    total_generation_ms = 0.0
    total_keyword_score = 0.0
    total_sources = 0

    for item in EVALUATION_DATASET:
        question = item["question"]
        expected = item["expected_keywords"]

        try:
            # RAG response
            rag_resp = await rag_chain.query_rag(question)

            keyword_score = _keyword_score(rag_resp.answer, expected)

            result = {
                "question": question,
                "category": item["category"],
                "rag_answer_excerpt": rag_resp.answer[:300],
                "keyword_score": round(keyword_score, 3),
                "sources_found": len(rag_resp.sources),
                "avg_similarity": rag_resp.metrics.avg_similarity_score,
                "retrieval_ms": rag_resp.metrics.retrieval_latency_ms or 0,
                "generation_ms": rag_resp.metrics.generation_latency_ms or 0,
                "total_ms": rag_resp.metrics.total_latency_ms,
                "success": rag_resp.success,
            }

            results.append(result)
            total_retrieval_ms += result["retrieval_ms"]
            total_generation_ms += result["generation_ms"]
            total_keyword_score += keyword_score
            total_sources += result["sources_found"]

        except Exception as e:
            logger.error(f"Evaluation failed for: {question} — {e}")
            results.append({
                "question": question,
                "category": item["category"],
                "error": str(e),
                "success": False,
            })

    n = len(EVALUATION_DATASET)
    successful = [r for r in results if r.get("success")]

    return {
        "total_questions": n,
        "successful": len(successful),
        "failed": n - len(successful),
        "avg_keyword_score": round(total_keyword_score / max(n, 1), 3),
        "avg_retrieval_ms": round(total_retrieval_ms / max(n, 1), 2),
        "avg_generation_ms": round(total_generation_ms / max(n, 1), 2),
        "avg_sources_per_query": round(total_sources / max(n, 1), 2),
        "results": results,
    }
