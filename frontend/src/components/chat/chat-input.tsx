"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2 } from "lucide-react";

interface Props {
  onSend: (message: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

export function ChatInput({ onSend, isLoading, disabled }: Props) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [input]);

  const handleSubmit = () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading || disabled) return;
    onSend(trimmed);
    setInput("");
    // Reset height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-white/[0.06] bg-black/40 backdrop-blur-xl p-4">
      <div className="max-w-3xl mx-auto flex items-end gap-3">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about F1 history, drivers, regulations..."
            disabled={isLoading || disabled}
            rows={1}
            className="w-full resize-none rounded-xl bg-white/[0.05] border border-white/[0.08] 
              px-4 py-3 text-sm text-white/90 placeholder:text-white/25
              focus:outline-none focus:border-white/20 focus:bg-white/[0.07]
              disabled:opacity-40 disabled:cursor-not-allowed
              transition-all duration-200"
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={!input.trim() || isLoading || disabled}
          className="shrink-0 h-[46px] w-[46px] rounded-xl flex items-center justify-center
            bg-red-600/80 hover:bg-red-600 text-white
            disabled:bg-white/[0.06] disabled:text-white/20
            transition-all duration-200"
        >
          {isLoading ? (
            <Loader2 size={18} className="animate-spin" />
          ) : (
            <Send size={18} />
          )}
        </button>
      </div>

      <div className="max-w-3xl mx-auto mt-2 flex items-center justify-between text-[10px] text-white/20">
        <span>Shift+Enter for new line</span>
        <span>Powered by Gemini 2.5 Flash + Pinecone</span>
      </div>
    </div>
  );
}
