"use client";

import { useState } from "react";
import type { SourceDocument } from "@/lib/types";
import { ChevronDown, ChevronUp, ExternalLink } from "lucide-react";

interface Props {
  sources: SourceDocument[];
}

export function SourcePanel({ sources }: Props) {
  const [isOpen, setIsOpen] = useState(false);

  if (!sources.length) return null;

  return (
    <div className="mt-3 border-t border-white/[0.06] pt-3">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 text-xs text-white/50 hover:text-white/70 transition-colors"
      >
        <span className="font-medium">
          {sources.length} source{sources.length !== 1 ? "s" : ""} retrieved
        </span>
        {isOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {isOpen && (
        <div className="mt-2 space-y-2">
          {sources.map((src, i) => (
            <div
              key={i}
              className="rounded-lg bg-white/[0.03] border border-white/[0.06] p-3 space-y-1.5"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-white/80 truncate">
                      {src.title}
                    </span>
                    <span className="shrink-0 text-[10px] px-1.5 py-0.5 rounded bg-white/[0.06] text-white/40">
                      {src.category}
                    </span>
                  </div>
                </div>
                <div className="shrink-0 text-right">
                  <span className="text-xs font-mono text-white/60">
                    {(src.score * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              {/* Score bar */}
              <div className="w-full h-[3px] rounded bg-white/[0.06]">
                <div
                  className="h-full rounded"
                  style={{
                    width: `${Math.max(src.score * 100, 3)}%`,
                    background: `linear-gradient(90deg, 
                      ${src.score > 0.8 ? "rgba(34, 197, 94, 0.7)" : src.score > 0.6 ? "rgba(234, 179, 8, 0.7)" : "rgba(239, 68, 68, 0.7)"}, 
                      ${src.score > 0.8 ? "rgba(34, 197, 94, 0.3)" : src.score > 0.6 ? "rgba(234, 179, 8, 0.3)" : "rgba(239, 68, 68, 0.3)"})`,
                  }}
                />
              </div>

              {src.excerpt && (
                <p className="text-[11px] text-white/40 line-clamp-2 leading-relaxed">
                  {src.excerpt}
                </p>
              )}

              {src.source && src.source !== "Unknown" && (
                <a
                  href={src.source}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-[10px] text-white/30 hover:text-white/50 transition-colors"
                >
                  <ExternalLink size={10} />
                  <span className="truncate max-w-[200px]">{src.source}</span>
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
