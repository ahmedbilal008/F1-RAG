"use client";

import { useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import type { ChatMessage } from "@/lib/types";
import { cn } from "@/lib/utils";
import { SourcePanel } from "./source-panel";
import { MetricsBar } from "./metrics-bar";

interface Props {
  messages: ChatMessage[];
  isLoading: boolean;
  onSend: (q: string) => void;
}

export function MessageList({ messages, isLoading, onSend }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <div className="flex-1 overflow-y-auto custom-scrollbar px-4 py-6 space-y-6">
      {messages.length === 0 && !isLoading && <EmptyState onSend={onSend} />}

      {messages.map((msg) => (
        <div
          key={msg.id}
          className={cn(
            "message-enter flex gap-3 max-w-3xl",
            msg.role === "user" ? "ml-auto flex-row-reverse" : "mr-auto"
          )}
        >
          {/* Avatar */}
          <div
            className={cn(
              "w-8 h-8 rounded-lg flex items-center justify-center shrink-0 text-xs font-semibold",
              msg.role === "user"
                ? "bg-white/10 text-white"
                : "bg-red-600/20 text-red-400"
            )}
          >
            {msg.role === "user" ? "Y" : "F1"}
          </div>

          {/* Bubble */}
          <div
            className={cn(
              "rounded-xl px-4 py-3 text-sm leading-relaxed",
              msg.role === "user"
                ? "bg-white/8 text-white/90"
                : "glass text-white/90"
            )}
          >
            <ReactMarkdown
              className="prose-f1"
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0 text-white/90">{children}</p>,
                ul: ({ children }) => <ul className="list-disc ml-4 mb-2 space-y-0.5 text-white/90">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal ml-4 mb-2 space-y-0.5 text-white/90">{children}</ol>,
                li: ({ children }) => <li>{children}</li>,
                strong: ({ children }) => <strong className="text-white font-semibold">{children}</strong>,
                h1: ({ children }) => <h1 className="text-base font-bold text-white mb-2 mt-1">{children}</h1>,
                h2: ({ children }) => <h2 className="text-sm font-bold text-white mb-1.5 mt-1">{children}</h2>,
                h3: ({ children }) => <h3 className="text-sm font-semibold text-white/80 mb-1 mt-1">{children}</h3>,
                code: ({ children }) => <code className="bg-white/10 rounded px-1 text-xs text-white/80 font-mono">{children}</code>,
              }}
            >
              {msg.content}
            </ReactMarkdown>

            {/* Metrics bar for assistant messages */}
            {msg.role === "assistant" && msg.metrics && (
              <MetricsBar metrics={msg.metrics} mode={msg.mode} />
            )}

            {/* Sources panel for RAG responses */}
            {msg.role === "assistant" &&
              msg.sources &&
              msg.sources.length > 0 && (
                <SourcePanel sources={msg.sources} />
              )}
          </div>
        </div>
      ))}

      {/* Loading indicator */}
      {isLoading && (
        <div className="message-enter flex gap-3 max-w-3xl mr-auto">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 text-xs font-semibold bg-red-600/20 text-red-400">
            F1
          </div>
          <div className="glass rounded-xl px-4 py-3">
            <div className="flex gap-1">
              <span className="typing-dot w-2 h-2 bg-white/40 rounded-full" />
              <span className="typing-dot w-2 h-2 bg-white/40 rounded-full" />
              <span className="typing-dot w-2 h-2 bg-white/40 rounded-full" />
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}

function EmptyState({ onSend }: { onSend: (q: string) => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center py-20 space-y-4">
      <div className="text-4xl font-bold text-white/10">F1</div>
      <h2 className="text-lg font-medium text-white/60">
        F1 RAG Assistant
      </h2>
      <p className="text-sm text-white/40 max-w-md">
        Ask questions about Formula 1 — drivers, teams, regulations, race
        results, and more. Toggle between RAG and Direct mode to compare
        retrieval-augmented answers with pure LLM responses.
      </p>
      <div className="flex flex-wrap gap-2 justify-center mt-4">
        {[
          "Who won the 2025 championship?",
          "Is DRS getting replaced in 2026?",
          "Which new teams are joining F1 in 2026?",
          "What is the driver lineup for Cadillac?",
        ].map((q) => (
          <button
            key={q}
            onClick={() => onSend(q)}
            className="text-xs glass rounded-full px-3 py-1.5 text-white/50 hover:text-white/80 hover:bg-white/10 transition-colors cursor-pointer"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
