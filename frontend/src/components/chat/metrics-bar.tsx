"use client";

import type { MetricsData, ResponseMode } from "@/lib/types";
import { Clock, Database, Zap, Hash, FileText } from "lucide-react";

interface Props {
  metrics: MetricsData;
  mode?: ResponseMode;
}

function MetricPill({
  icon: Icon,
  label,
  value,
  unit,
}: {
  icon: React.ComponentType<{ size?: number }>;
  label: string;
  value: string | number;
  unit?: string;
}) {
  return (
    <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-white/[0.04] border border-white/[0.06]">
      <Icon size={12} />
      <span className="text-white/40 text-[10px] uppercase tracking-wider">
        {label}
      </span>
      <span className="text-white/70 text-xs font-mono font-medium">
        {value}
        {unit && <span className="text-white/30 ml-0.5">{unit}</span>}
      </span>
    </div>
  );
}

export function MetricsBar({ metrics, mode }: Props) {
  return (
    <div className="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-white/[0.06]">
      {mode && (
        <div className="flex items-center gap-1 px-2 py-1 rounded bg-white/[0.06] text-[10px] uppercase tracking-wider text-white/40">
          {mode}
        </div>
      )}

      {metrics.retrieval_latency_ms != null && (
        <MetricPill
          icon={Database}
          label="Retrieval"
          value={metrics.retrieval_latency_ms.toFixed(0)}
          unit="ms"
        />
      )}
      {metrics.generation_latency_ms != null && (
        <MetricPill
          icon={Zap}
          label="Generation"
          value={metrics.generation_latency_ms.toFixed(0)}
          unit="ms"
        />
      )}
      {metrics.total_latency_ms != null && (
        <MetricPill
          icon={Clock}
          label="Total"
          value={metrics.total_latency_ms.toFixed(0)}
          unit="ms"
        />
      )}
      {metrics.tokens_estimated > 0 && (
        <MetricPill
          icon={Hash}
          label="Tokens"
          value={metrics.tokens_estimated.toLocaleString()}
        />
      )}
      {metrics.documents_retrieved > 0 && (
        <MetricPill
          icon={FileText}
          label="Docs"
          value={metrics.documents_retrieved}
        />
      )}
      {metrics.avg_similarity_score > 0 && (
        <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-white/[0.04] border border-white/[0.06]">
          <span className="text-white/40 text-[10px] uppercase tracking-wider">
            Sim
          </span>
          <span className="text-white/70 text-xs font-mono font-medium">
            {(metrics.avg_similarity_score * 100).toFixed(1)}
            <span className="text-white/30 ml-0.5">%</span>
          </span>
        </div>
      )}
    </div>
  );
}
