"""RAG chain — retrieval + generation pipeline."""

from __future__ import annotations

import time
from typing import Dict, Any, List, Optional

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.vector_store import get_vector_store
from app.services.llm import get_llm_provider, LLMResponse
from app.models.schemas import (
    ChatResponse,
    SourceDocument,
    MetricsData,
    ResponseMode,
)

logger = get_logger("rag_chain")


RAG_PROMPT_TEMPLATE = """You are a knowledgeable Formula 1 expert assistant. Answer the user's question using ONLY the provided context from the F1 knowledge base.

CONTEXT FROM F1 KNOWLEDGE BASE:
{context}

USER QUESTION: {question}

INSTRUCTIONS:
- Answer based strictly on the provided context
- If the context contains relevant information, provide a detailed, accurate answer
- If the context is insufficient, clearly state what you know from context and what is missing
- When citing facts, reference the source (e.g., "According to [Source Title]...")
- Use precise F1 terminology (DRS, undercut, dirty air, etc.) when relevant
- For statistics and results, be exact — do not approximate
- Keep responses well-structured and informative
- Do not make up information not present in the context

ANSWER:"""


DIRECT_PROMPT_TEMPLATE = """You are a Formula 1 expert assistant. Answer the user's question using your general knowledge about Formula 1.

USER QUESTION: {question}

INSTRUCTIONS:
- Provide a comprehensive, accurate answer about Formula 1
- Include relevant statistics, history, and technical details
- Use proper F1 terminology
- If you're uncertain about specific details, indicate your confidence level
- Keep responses well-structured and engaging

ANSWER:"""


class RAGChain:
    """Orchestrates retrieval-augmented generation for F1 queries."""

    def __init__(self):
        self._store = get_vector_store()
        self._llm = get_llm_provider()
        self._settings = get_settings()

    def _format_context(self, documents: List[Dict[str, Any]]) -> str:
        """Format retrieved documents into a context string for the prompt."""
        if not documents:
            return "No relevant context found in the knowledge base."

        parts = []
        for i, doc in enumerate(documents, 1):
            content = doc.get("content", "")
            meta = doc.get("metadata", {})
            title = meta.get("title", "Unknown Source")
            score = doc.get("score", 0)

            # Truncate very long chunks to stay within context window
            if len(content) > 1500:
                content = content[:1500] + "..."

            parts.append(
                f"--- Source {i}: {title} (relevance: {score:.3f}) ---\n{content}"
            )

        return "\n\n".join(parts)

    def _build_source_documents(self, docs: List[Dict[str, Any]]) -> List[SourceDocument]:
        """Convert raw search results to SourceDocument schema objects."""
        sources = []
        for doc in docs:
            meta = doc.get("metadata", {})
            sources.append(
                SourceDocument(
                    title=meta.get("title", "Unknown"),
                    source=meta.get("source", "Unknown"),
                    category=meta.get("category", "general"),
                    namespace=meta.get("namespace", ""),
                    score=doc.get("score", 0),
                    excerpt=doc.get("content", "")[:300],
                    metadata={
                        k: v for k, v in meta.items()
                        if k not in ("title", "source", "category", "namespace", "text")
                    },
                )
            )
        return sources

    async def query_rag(
        self,
        question: str,
        top_k: Optional[int] = None,
        namespace: Optional[str] = None,
    ) -> ChatResponse:
        """Execute the full RAG pipeline."""
        k = top_k or self._settings.TOP_K_RESULTS
        total_start = time.perf_counter()

        # --- Retrieval ---
        retrieval_start = time.perf_counter()
        documents = self._store.similarity_search(
            query=question,
            top_k=k,
            namespace=namespace,
            score_threshold=self._settings.SIMILARITY_THRESHOLD,
        )
        retrieval_ms = (time.perf_counter() - retrieval_start) * 1000

        if not documents:
            return ChatResponse(
                success=False,
                answer=(
                    "I couldn't find relevant information in the F1 knowledge base "
                    "for your question. Try rephrasing or check if the knowledge base "
                    "has been initialized."
                ),
                mode=ResponseMode.RAG,
                metrics=MetricsData(
                    retrieval_latency_ms=round(retrieval_ms, 2),
                    total_latency_ms=round((time.perf_counter() - total_start) * 1000, 2),
                ),
            )

        # --- Generation ---
        context = self._format_context(documents)
        prompt = RAG_PROMPT_TEMPLATE.format(context=context, question=question)

        generation_start = time.perf_counter()
        llm_response: LLMResponse = await self._llm.agenerate(prompt)
        generation_ms = (time.perf_counter() - generation_start) * 1000

        total_ms = (time.perf_counter() - total_start) * 1000

        # --- Build response ---
        sources = self._build_source_documents(documents)
        avg_score = sum(d["score"] for d in documents) / len(documents) if documents else 0

        return ChatResponse(
            success=True,
            answer=llm_response.text,
            mode=ResponseMode.RAG,
            sources=sources,
            context_used=len(documents),
            metrics=MetricsData(
                retrieval_latency_ms=round(retrieval_ms, 2),
                generation_latency_ms=round(generation_ms, 2),
                total_latency_ms=round(total_ms, 2),
                tokens_estimated=llm_response.tokens_used,
                documents_retrieved=len(documents),
                avg_similarity_score=round(avg_score, 4),
            ),
        )

    async def query_direct(self, question: str) -> ChatResponse:
        """Query the LLM directly without retrieval."""
        total_start = time.perf_counter()

        prompt = DIRECT_PROMPT_TEMPLATE.format(question=question)
        llm_response: LLMResponse = await self._llm.agenerate(prompt)

        total_ms = (time.perf_counter() - total_start) * 1000

        return ChatResponse(
            success=True,
            answer=llm_response.text,
            mode=ResponseMode.DIRECT,
            metrics=MetricsData(
                generation_latency_ms=round(llm_response.latency_ms, 2),
                total_latency_ms=round(total_ms, 2),
                tokens_estimated=llm_response.tokens_used,
            ),
        )

    async def query_compare(self, question: str, top_k: Optional[int] = None) -> Dict[str, Any]:
        """Run both RAG and Direct queries for comparison."""
        rag_response = await self.query_rag(question, top_k=top_k)
        direct_response = await self.query_direct(question)

        return {
            "question": question,
            "rag_response": rag_response,
            "direct_response": direct_response,
        }

    def check_status(self) -> Dict[str, Any]:
        """Check system component status."""
        # Vector store
        vs_status = self._store.check_connection()

        # LLM
        try:
            test = self._llm.generate("Respond with OK")
            llm_ok = bool(test.text)
        except Exception as e:
            llm_ok = False

        stats = self._store.get_stats()

        return {
            "pinecone_connected": vs_status.get("connected", False),
            "llm_connected": llm_ok,
            "index_name": self._settings.PINECONE_INDEX_NAME,
            "total_vectors": stats.get("total_vectors", 0),
            "namespaces": stats.get("namespaces", {}),
            "config": {
                "embedding_model": self._settings.EMBEDDING_MODEL,
                "llm_model": self._settings.LLM_MODEL,
                "chunk_size": self._settings.CHUNK_SIZE,
                "top_k": self._settings.TOP_K_RESULTS,
                "similarity_threshold": self._settings.SIMILARITY_THRESHOLD,
            },
        }


_chain_instance: Optional[RAGChain] = None


def get_rag_chain() -> RAGChain:
    """Get or create the singleton RAG chain."""
    global _chain_instance
    if _chain_instance is None:
        _chain_instance = RAGChain()
    return _chain_instance
