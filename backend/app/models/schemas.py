"""Pydantic request/response schemas for the API."""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ResponseMode(str, Enum):
    RAG = "rag"
    DIRECT = "direct"
    COMPARE = "compare"


class IngestionSource(str, Enum):
    WIKIPEDIA = "wikipedia"
    ERGAST = "ergast"
    NEWS = "news"
    ALL = "all"


class ChatRequest(BaseModel):
    """Incoming chat request from the frontend."""
    question: str = Field(..., min_length=1, max_length=2000, description="User question about F1")
    mode: ResponseMode = Field(default=ResponseMode.RAG, description="Response mode")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of documents to retrieve")
    namespace_filter: Optional[str] = Field(default=None, description="Filter by Pinecone namespace")


class IngestionRequest(BaseModel):
    """Request to trigger data ingestion."""
    source: IngestionSource = Field(default=IngestionSource.ALL)
    force_refresh: bool = Field(default=False, description="Re-ingest even if data exists")


class SourceDocument(BaseModel):
    """A retrieved source document with metadata."""
    title: str
    source: str
    category: str
    namespace: str = ""
    score: float = Field(ge=0.0, le=1.0)
    excerpt: str = ""
    metadata: Dict[str, Any] = {}


class MetricsData(BaseModel):
    """Performance metrics for a single response."""
    retrieval_latency_ms: Optional[float] = None
    generation_latency_ms: Optional[float] = None
    total_latency_ms: float = 0.0
    tokens_estimated: int = 0
    documents_retrieved: int = 0
    avg_similarity_score: float = 0.0


class ChatResponse(BaseModel):
    """Response returned to the frontend."""
    success: bool
    answer: str
    mode: ResponseMode
    sources: List[SourceDocument] = []
    metrics: MetricsData = MetricsData()
    context_used: int = 0


class CompareResponse(BaseModel):
    """Side-by-side comparison of RAG vs Direct responses."""
    rag_response: ChatResponse
    direct_response: ChatResponse
    question: str


class IngestionResult(BaseModel):
    """Result of a data ingestion operation."""
    success: bool
    source: str
    documents_processed: int = 0
    chunks_created: int = 0
    errors: List[str] = []
    duration_seconds: float = 0.0


class SystemStatus(BaseModel):
    """System health status."""
    pinecone_connected: bool = False
    llm_connected: bool = False
    index_name: str = ""
    total_vectors: int = 0
    namespaces: Dict[str, Any] = {}
    config: Dict[str, Any] = {}


class EvaluationResult(BaseModel):
    """Result of RAG evaluation on a test question."""
    question: str
    expected_answer: str = ""
    rag_answer: str = ""
    direct_answer: str = ""
    retrieval_score: float = 0.0
    sources_found: int = 0
    latency_ms: float = 0.0
