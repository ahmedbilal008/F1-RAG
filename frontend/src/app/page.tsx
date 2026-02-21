"use client";

import { useState, useCallback } from "react";
import type { ChatMessage, ResponseMode } from "@/lib/types";
import { sendChat, sendCompare } from "@/lib/api";
import { Sidebar } from "@/components/sidebar/sidebar";
import { MessageList } from "@/components/chat/message-list";
import { ChatInput } from "@/components/chat/chat-input";

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [mode, setMode] = useState<ResponseMode>("rag");
  const [topK, setTopK] = useState(5);
  const [namespaceFilter, setNamespaceFilter] = useState<string | null>(null);

  const handleSend = useCallback(
    async (content: string) => {
      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content,
        mode,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);

      try {
        if (mode === "compare") {
          const result = await sendCompare({
            question: content,
            mode: "compare",
            top_k: topK,
            namespace_filter: namespaceFilter,
          });

          const ragMsg: ChatMessage = {
            id: crypto.randomUUID(),
            role: "assistant",
            content: `**RAG Response:**\n\n${result.rag_response.answer}`,
            mode: "rag",
            sources: result.rag_response.sources,
            metrics: result.rag_response.metrics,
            timestamp: new Date(),
          };

          const directMsg: ChatMessage = {
            id: crypto.randomUUID(),
            role: "assistant",
            content: `**Direct Response:**\n\n${result.direct_response.answer}`,
            mode: "direct",
            sources: [],
            metrics: result.direct_response.metrics,
            timestamp: new Date(),
          };

          setMessages((prev) => [...prev, ragMsg, directMsg]);
        } else {
          const result = await sendChat({
            question: content,
            mode,
            top_k: topK,
            namespace_filter: namespaceFilter,
          });

          const assistantMsg: ChatMessage = {
            id: crypto.randomUUID(),
            role: "assistant",
            content: result.answer,
            mode: result.mode,
            sources: result.sources,
            metrics: result.metrics,
            timestamp: new Date(),
          };

          setMessages((prev) => [...prev, assistantMsg]);
        }
      } catch (error) {
        const errorMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `Something went wrong: ${error instanceof Error ? error.message : "Unknown error"}. Make sure the backend is running on http://localhost:8000.`,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setIsLoading(false);
      }
    },
    [mode, topK, namespaceFilter]
  );

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        mode={mode}
        onModeChange={setMode}
        topK={topK}
        onTopKChange={setTopK}
        namespaceFilter={namespaceFilter}
        onNamespaceFilterChange={setNamespaceFilter}
      />

      <main className="flex-1 flex flex-col min-w-0">
        <MessageList messages={messages} isLoading={isLoading} onSend={handleSend} />
        <ChatInput onSend={handleSend} isLoading={isLoading} />
      </main>
    </div>
  );
}
