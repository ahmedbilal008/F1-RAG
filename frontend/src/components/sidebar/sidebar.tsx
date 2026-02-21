"use client";

import { useState, useEffect, useCallback } from "react";
import type { ResponseMode, SystemStatus } from "@/lib/types";
import {
  getSystemStatus,
  triggerIngestion,
  runEvaluation,
} from "@/lib/api";
import {
  Database,
  Wifi,
  WifiOff,
  RefreshCw,
  Loader2,
  ChevronDown,
  Activity,
  Layers,
  FlaskConical,
} from "lucide-react";

interface Props {
  mode: ResponseMode;
  onModeChange: (mode: ResponseMode) => void;
  topK: number;
  onTopKChange: (k: number) => void;
  namespaceFilter: string | null;
  onNamespaceFilterChange: (ns: string | null) => void;
}

export function Sidebar({
  mode,
  onModeChange,
  topK,
  onTopKChange,
  namespaceFilter,
  onNamespaceFilterChange,
}: Props) {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [statusLoading, setStatusLoading] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [ingestResult, setIngestResult] = useState<string | null>(null);
  const [evaluating, setEvaluating] = useState(false);
  const [evalResult, setEvalResult] = useState<Record<string, unknown> | null>(
    null
  );

  const fetchStatus = useCallback(async () => {
    setStatusLoading(true);
    try {
      const s = await getSystemStatus();
      setStatus(s);
    } catch {
      setStatus(null);
    } finally {
      setStatusLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const handleIngest = async (source: string) => {
    setIngesting(true);
    setIngestResult(null);
    try {
      const result = await triggerIngestion(source);
      setIngestResult(
        result.success
          ? `Processed ${result.chunks_created} chunks in ${result.duration_seconds.toFixed(1)}s`
          : `Errors: ${result.errors.join(", ")}`
      );
      fetchStatus();
    } catch (e) {
      setIngestResult(`Failed: ${e instanceof Error ? e.message : "unknown"}`);
    } finally {
      setIngesting(false);
    }
  };

  const handleEvaluate = async () => {
    setEvaluating(true);
    setEvalResult(null);
    try {
      const result = await runEvaluation();
      setEvalResult(result);
    } catch (e) {
      setEvalResult({
        error: e instanceof Error ? e.message : "Evaluation failed",
      });
    } finally {
      setEvaluating(false);
    }
  };

  const namespaces = status?.namespaces
    ? Object.entries(status.namespaces)
    : [];

  return (
    <aside className="w-72 shrink-0 border-r border-white/[0.06] bg-black/60 backdrop-blur-xl overflow-y-auto custom-scrollbar flex flex-col">
      {/* Header */}
      <div className="p-5 border-b border-white/[0.06]">
        <h1 className="text-lg font-semibold text-white/90 tracking-tight">
          F1 RAG
        </h1>
        <p className="text-xs text-white/30 mt-0.5">
          Retrieval-Augmented Generation
        </p>
      </div>

      {/* Connection status */}
      <div className="px-5 py-3 border-b border-white/[0.06]">
        <div className="flex items-center justify-between">
          <span className="text-xs text-white/40 uppercase tracking-wider">
            System
          </span>
          <button
            onClick={fetchStatus}
            disabled={statusLoading}
            className="text-white/30 hover:text-white/60 transition-colors"
          >
            {statusLoading ? (
              <Loader2 size={12} className="animate-spin" />
            ) : (
              <RefreshCw size={12} />
            )}
          </button>
        </div>

        {status ? (
          <div className="mt-2 space-y-1.5">
            <StatusDot label="Pinecone" ok={status.pinecone_connected} />
            <StatusDot label="LLM" ok={status.llm_connected} />
            <div className="flex items-center gap-2 text-xs text-white/40">
              <Database size={12} />
              <span>
                {status.total_vectors.toLocaleString()} vectors in{" "}
                <span className="text-white/60">{status.index_name}</span>
              </span>
            </div>
          </div>
        ) : (
          <p className="text-xs text-white/30 mt-2">
            {statusLoading ? "Connecting..." : "Disconnected"}
          </p>
        )}
      </div>

      {/* Mode selector */}
      <div className="px-5 py-4 border-b border-white/[0.06] space-y-3">
        <span className="text-xs text-white/40 uppercase tracking-wider">
          Response Mode
        </span>
        <div className="flex rounded-lg overflow-hidden border border-white/[0.08]">
          {(["rag", "direct", "compare"] as ResponseMode[]).map((m) => (
            <button
              key={m}
              onClick={() => onModeChange(m)}
              className={`flex-1 py-2 text-xs font-medium transition-all ${
                mode === m
                  ? "bg-red-600/80 text-white"
                  : "bg-white/[0.03] text-white/40 hover:text-white/60 hover:bg-white/[0.06]"
              }`}
            >
              {m.toUpperCase()}
            </button>
          ))}
        </div>
        <p className="text-[10px] text-white/25 leading-relaxed">
          {mode === "rag"
            ? "Answers grounded in retrieved documents from Pinecone."
            : mode === "direct"
              ? "Pure LLM response without retrieval context."
              : "Side-by-side comparison of RAG vs Direct answers."}
        </p>
      </div>

      {/* Retrieval settings */}
      <div className="px-5 py-4 border-b border-white/[0.06] space-y-3">
        <span className="text-xs text-white/40 uppercase tracking-wider">
          Retrieval Settings
        </span>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-xs text-white/50">Top-K documents</label>
            <span className="text-xs text-white/70 font-mono">{topK}</span>
          </div>
          <input
            type="range"
            min={1}
            max={15}
            value={topK}
            onChange={(e) => onTopKChange(parseInt(e.target.value))}
            className="w-full h-1 bg-white/10 rounded-lg appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-red-500"
          />
        </div>

        {/* Namespace filter */}
        <div className="space-y-2">
          <label className="text-xs text-white/50">Namespace filter</label>
          <div className="relative">
            <select
              value={namespaceFilter ?? ""}
              onChange={(e) =>
                onNamespaceFilterChange(e.target.value || null)
              }
              className="w-full text-xs bg-white/[0.05] border border-white/[0.08] rounded-lg px-3 py-2 text-white/70 appearance-none cursor-pointer focus:outline-none focus:border-white/20"
            >
              <option value="">All namespaces</option>
              {namespaces.map(([ns]) => (
                <option key={ns} value={ns}>
                  {ns}
                </option>
              ))}
            </select>
            <ChevronDown
              size={12}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 pointer-events-none"
            />
          </div>
        </div>
      </div>

      {/* Namespaces info */}
      {namespaces.length > 0 && (
        <div className="px-5 py-4 border-b border-white/[0.06] space-y-2">
          <span className="text-xs text-white/40 uppercase tracking-wider flex items-center gap-1.5">
            <Layers size={12} /> Namespaces
          </span>
          <div className="space-y-1">
            {namespaces.map(([ns, data]) => (
              <div
                key={ns}
                className="flex items-center justify-between text-xs"
              >
                <span className="text-white/50 truncate">{ns}</span>
                <span className="text-white/30 font-mono">
                  {data.vector_count.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Ingestion */}
      <div className="px-5 py-4 border-b border-white/[0.06] space-y-3">
        <span className="text-xs text-white/40 uppercase tracking-wider flex items-center gap-1.5">
          <Activity size={12} /> Ingestion
        </span>

        <div className="grid grid-cols-2 gap-2">
          {["all", "wikipedia", "ergast"].map((src) => (
            <button
              key={src}
              disabled
              className="text-[11px] px-3 py-2 rounded-lg bg-white/[0.04] border border-white/[0.06] text-white/20 opacity-30 cursor-not-allowed capitalize"
            >
              {src}
            </button>
          ))}
        </div>

        {ingestResult && (
          <p className="text-[10px] text-white/40 leading-relaxed">
            {ingestResult}
          </p>
        )}
      </div>

      {/* Evaluation */}
      <div className="px-5 py-4 space-y-3">
        <span className="text-xs text-white/40 uppercase tracking-wider flex items-center gap-1.5">
          <FlaskConical size={12} /> Evaluation
        </span>

        <button
          onClick={handleEvaluate}
          disabled={evaluating}
          className="w-full text-xs px-3 py-2.5 rounded-lg bg-white/[0.04] border border-white/[0.06] text-white/40 hover:text-white/70 hover:bg-white/[0.08] transition-all disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {evaluating ? (
            <>
              <Loader2 size={12} className="animate-spin" /> Running...
            </>
          ) : (
            "Run RAG Evaluation"
          )}
        </button>

        {evalResult && (
          <div className="text-[10px] text-white/40 space-y-1 font-mono">
            {Object.entries(evalResult).map(([key, val]) => (
              <div key={key} className="flex justify-between">
                <span>{key}:</span>
                <span className="text-white/60">
                  {typeof val === "number" ? val.toFixed(2) : String(val)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}

function StatusDot({ label, ok }: { label: string; ok: boolean }) {
  return (
    <div className="flex items-center gap-2 text-xs text-white/40">
      {ok ? (
        <Wifi size={12} className="text-green-500/70" />
      ) : (
        <WifiOff size={12} className="text-red-500/70" />
      )}
      <span>{label}</span>
      <span
        className={`ml-auto text-[10px] ${ok ? "text-green-500/60" : "text-red-500/60"}`}
      >
        {ok ? "Connected" : "Offline"}
      </span>
    </div>
  );
}
