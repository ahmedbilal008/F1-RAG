"""API routes for the F1 RAG assistant."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    CompareResponse,
    IngestionRequest,
    IngestionResult,
    SystemStatus,
    ResponseMode,
    MetricsData,
)
from app.retrieval.rag_chain import get_rag_chain
from app.retrieval.live_data import is_live_query, get_openf1_client
from app.services.llm import get_llm_provider
from app.ingestion.pipeline import ingest_all, ingest_wikipedia, ingest_ergast
from app.evaluation.evaluator import run_evaluation
from app.core.logging import get_logger

logger = get_logger("api")

router = APIRouter(prefix="/api/v1", tags=["F1 RAG"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint.

    Supports three modes:
      - RAG: retrieval-augmented generation
      - DIRECT: straight LLM inference
      - COMPARE: returns both (via /compare endpoint)
    """
    try:
        chain = get_rag_chain()

        # Check if this is a live data query
        if is_live_query(request.question):
            logger.info("Detected live data query — augmenting with OpenF1")
            client = get_openf1_client()
            live_context = client.get_live_context()

            # Combine RAG + live data
            if request.mode == ResponseMode.RAG:
                rag_resp = await chain.query_rag(
                    request.question, top_k=request.top_k, namespace=request.namespace_filter
                )
                # Append live context to answer
                if live_context and "No live F1 session data" not in live_context:
                    llm = get_llm_provider()
                    augmented_prompt = (
                        f"Based on the following F1 knowledge and live session data, "
                        f"answer the question.\n\n"
                        f"KNOWLEDGE BASE:\n{rag_resp.answer}\n\n"
                        f"LIVE SESSION DATA:\n{live_context}\n\n"
                        f"QUESTION: {request.question}\n\nANSWER:"
                    )
                    augmented = await llm.agenerate(augmented_prompt)
                    rag_resp.answer = augmented.text
                return rag_resp
            else:
                return await chain.query_direct(request.question)

        # Standard flow
        if request.mode == ResponseMode.RAG:
            return await chain.query_rag(
                request.question, top_k=request.top_k, namespace=request.namespace_filter
            )
        elif request.mode == ResponseMode.DIRECT:
            return await chain.query_direct(request.question)
        else:
            # Compare mode — return RAG response, client calls /compare for both
            return await chain.query_rag(
                request.question, top_k=request.top_k, namespace=request.namespace_filter
            )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        return ChatResponse(
            success=False,
            answer=f"An error occurred: {str(e)}",
            mode=request.mode,
        )


@router.post("/compare", response_model=CompareResponse)
async def compare(request: ChatRequest) -> CompareResponse:
    """Run both RAG and Direct queries for comparison."""
    try:
        chain = get_rag_chain()
        result = await chain.query_compare(request.question, top_k=request.top_k)
        return CompareResponse(
            question=request.question,
            rag_response=result["rag_response"],
            direct_response=result["direct_response"],
        )
    except Exception as e:
        logger.error(f"Compare error: {e}")
        error_resp = ChatResponse(
            success=False, answer=f"Error: {str(e)}", mode=ResponseMode.RAG
        )
        return CompareResponse(
            question=request.question,
            rag_response=error_resp,
            direct_response=error_resp,
        )


@router.post("/ingest", response_model=IngestionResult)
async def ingest(request: IngestionRequest, background_tasks: BackgroundTasks):
    """Trigger data ingestion."""
    raise HTTPException(status_code=403, detail="Ingestion is disabled.")


@router.get("/status", response_model=SystemStatus)
async def status():
    """System health check."""
    try:
        chain = get_rag_chain()
        s = chain.check_status()
        return SystemStatus(**s)
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return SystemStatus()


@router.get("/evaluate")
async def evaluate():
    """Run the evaluation suite against the test dataset."""
    try:
        chain = get_rag_chain()
        results = await run_evaluation(chain)
        return results
    except Exception as e:
        logger.error(f"Evaluation error: {e}")
        return {"error": str(e)}


@router.get("/namespaces")
async def get_namespaces():
    """Get Pinecone namespace statistics."""
    try:
        from app.services.vector_store import get_vector_store
        store = get_vector_store()
        stats = store.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Namespace stats error: {e}")
        return {"error": str(e)}
