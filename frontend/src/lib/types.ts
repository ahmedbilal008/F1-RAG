/* -------------------------------------------------------------------
   TypeScript types mirroring the backend Pydantic schemas.
   Keeps frontend/backend in sync.
   ------------------------------------------------------------------- */

export type ResponseMode = "rag" | "direct" | "compare";

export interface ChatRequest {
  question: string;
  mode: ResponseMode;
  top_k?: number;
  namespace_filter?: string | null;
}

export interface SourceDocument {
  title: string;
  source: string;
  category: string;
  namespace: string;
  score: number;
  excerpt: string;
  metadata: Record<string, unknown>;
}

export interface MetricsData {
  retrieval_latency_ms: number | null;
  generation_latency_ms: number | null;
  total_latency_ms: number;
  tokens_estimated: number;
  documents_retrieved: number;
  avg_similarity_score: number;
}

export interface ChatResponse {
  success: boolean;
  answer: string;
  mode: ResponseMode;
  sources: SourceDocument[];
  metrics: MetricsData;
  context_used: number;
}

export interface CompareResponse {
  question: string;
  rag_response: ChatResponse;
  direct_response: ChatResponse;
}

export interface IngestionResult {
  success: boolean;
  source: string;
  documents_processed: number;
  chunks_created: number;
  errors: string[];
  duration_seconds: number;
}

export interface SystemStatus {
  pinecone_connected: boolean;
  llm_connected: boolean;
  index_name: string;
  total_vectors: number;
  namespaces: Record<string, { vector_count: number }>;
  config: Record<string, unknown>;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  mode?: ResponseMode;
  sources?: SourceDocument[];
  metrics?: MetricsData;
  timestamp: Date;
}
