"""
Chat interface components for the F1 RAG chatbot
"""

import streamlit as st
from typing import List, Dict, Optional
from datetime import datetime

from src.utils.logger import app_logger


class ChatInterface:
    """Chat interface manager"""
    
    def __init__(self):
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize chat-related session state"""
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []
        
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
    
    def display_chat_messages(self):
        """Display all chat messages"""
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Display sources if available
                if message.get("sources") and message["role"] == "assistant":
                    self._display_sources(message["sources"], message.get("method", "unknown"))
    
    def _display_sources(self, sources: List[Dict], method: str):
        """Display sources used for the response"""
        if not sources:
            return
        
        with st.expander(f"📚 Sources Used ({method.upper()} mode) - {len(sources)} sources"):
            for i, source in enumerate(sources, 1):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**{i}. {source.get('title', 'Unknown Title')}**")
                    st.markdown(f"*Category: {source.get('category', 'general')}*")
                    if source.get('excerpt'):
                        st.markdown(f"```\n{source['excerpt']}\n```")
                
                with col2:
                    score = source.get('score', 0)
                    if score > 0:
                        st.metric("Relevance", f"{score:.3f}")
                    
                    if source.get('source'):
                        st.markdown(f"[🔗 Source]({source['source']})")
                
                if i < len(sources):
                    st.divider()
    
    def add_message(self, role: str, content: str, sources: Optional[List[Dict]] = None, 
                   method: Optional[str] = None, metadata: Optional[Dict] = None):
        """Add a message to the chat"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "sources": sources or [],
            "method": method,
            "metadata": metadata or {}
        }
        
        st.session_state.chat_messages.append(message)
        
        # Also add to history for analytics
        st.session_state.chat_history.append(message)
        
        app_logger.info(f"Added {role} message to chat")
    
    def clear_chat(self):
        """Clear all chat messages"""
        st.session_state.chat_messages = []
        app_logger.info("Chat cleared")
    
    def export_chat_history(self) -> str:
        """Export chat history as formatted text"""
        if not st.session_state.chat_messages:
            return "No chat history to export."
        
        export_text = f"F1 RAG Chatbot - Chat Export\n"
        export_text += f"Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        export_text += "=" * 50 + "\n\n"
        
        for i, message in enumerate(st.session_state.chat_messages, 1):
            role = message["role"].upper()
            content = message["content"]
            timestamp = message.get("timestamp", "")
            method = message.get("method", "")
            
            export_text += f"{i}. [{role}] {timestamp}\n"
            if method and role == "ASSISTANT":
                export_text += f"   Method: {method.upper()}\n"
            export_text += f"   {content}\n"
            
            # Add sources if available
            sources = message.get("sources", [])
            if sources and role == "ASSISTANT":
                export_text += f"   Sources ({len(sources)}):\n"
                for j, source in enumerate(sources, 1):
                    export_text += f"     {j}. {source.get('title', 'Unknown')} ({source.get('score', 0):.3f})\n"
            
            export_text += "\n" + "-" * 30 + "\n\n"
        
        return export_text
    
    def get_chat_stats(self) -> Dict:
        """Get chat statistics"""
        if not st.session_state.chat_messages:
            return {}
        
        total_messages = len(st.session_state.chat_messages)
        user_messages = len([m for m in st.session_state.chat_messages if m["role"] == "user"])
        assistant_messages = len([m for m in st.session_state.chat_messages if m["role"] == "assistant"])
        
        rag_responses = len([m for m in st.session_state.chat_messages 
                            if m.get("method") == "rag"])
        direct_responses = len([m for m in st.session_state.chat_messages 
                              if m.get("method") == "direct"])
        
        return {
            "total_messages": total_messages,
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "rag_responses": rag_responses,
            "direct_responses": direct_responses,
            "avg_sources_per_rag": sum(len(m.get("sources", [])) for m in st.session_state.chat_messages 
                                      if m.get("method") == "rag") / max(rag_responses, 1)
        }


class QuickExamples:
    """Quick example questions component"""
    
    EXAMPLE_QUESTIONS = [
        {
            "question": "Who won the 2024 F1 World Championship?",
            "category": "Current Season",
            "icon": "🏆"
        },
        {
            "question": "What are the current F1 regulations?",
            "category": "Regulations",
            "icon": "📋"
        },
        {
            "question": "How does the F1 points system work?",
            "category": "Rules",
            "icon": "🏁"
        },
        {
            "question": "List all F1 World Champions",
            "category": "History",
            "icon": "📜"
        },
        {
            "question": "What teams compete in Formula 1?",
            "category": "Teams",
            "icon": "🏎️"
        },
        {
            "question": "Explain DRS in Formula 1",
            "category": "Technology",
            "icon": "⚙️"
        },
        {
            "question": "What are the F1 circuit requirements?",
            "category": "Circuits",
            "icon": "🏁"
        },
        {
            "question": "How do F1 qualifying sessions work?",
            "category": "Format",
            "icon": "⏱️"
        }
    ]
    
    @staticmethod
    def display_examples(on_click_callback=None):
        """Display quick example questions"""
        st.subheader("🎯 Quick Examples")
        st.markdown("*Click any question to ask it:*")
        
        # Group examples by category
        categories = {}
        for example in QuickExamples.EXAMPLE_QUESTIONS:
            category = example["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(example)
        
        # Display by category
        for category, examples in categories.items():
            with st.expander(f"{category} Questions"):
                for example in examples:
                    col1, col2 = st.columns([1, 10])
                    with col1:
                        st.write(example["icon"])
                    with col2:
                        if st.button(
                            example["question"],
                            key=f"example_{hash(example['question'])}",
                            use_container_width=True,
                            help=f"Category: {example['category']}"
                        ):
                            if on_click_callback:
                                on_click_callback(example["question"])
    
    @staticmethod
    def get_random_question() -> str:
        """Get a random example question"""
        import random
        return random.choice(QuickExamples.EXAMPLE_QUESTIONS)["question"]


class ResponseComparison:
    """Component to compare RAG vs Direct responses"""
    
    @staticmethod
    def display_comparison(rag_response: Dict, direct_response: Dict, question: str):
        """Display side-by-side comparison of RAG vs Direct responses"""
        st.subheader("🔄 Response Comparison")
        st.markdown(f"**Question:** {question}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🧠 RAG Response")
            if rag_response.get("success"):
                st.success("✅ RAG Response Generated")
                st.markdown(rag_response["response"])
                
                sources = rag_response.get("sources", [])
                if sources:
                    st.markdown(f"**Sources Used:** {len(sources)}")
                    for i, source in enumerate(sources[:3], 1):
                        st.markdown(f"{i}. {source.get('title', 'Unknown')} (Score: {source.get('score', 0):.3f})")
            else:
                st.error("❌ RAG Response Failed")
                st.markdown(rag_response.get("response", "No response"))
        
        with col2:
            st.markdown("### 🤖 Direct AI Response")
            if direct_response.get("success"):
                st.success("✅ Direct Response Generated")
                st.markdown(direct_response["response"])
                st.info("💡 Based on general AI knowledge")
            else:
                st.error("❌ Direct Response Failed")
                st.markdown(direct_response.get("response", "No response"))
        
        # Comparison metrics
        st.markdown("### 📊 Comparison Metrics")
        col3, col4, col5 = st.columns(3)
        
        with col3:
            rag_length = len(rag_response.get("response", "")) if rag_response.get("success") else 0
            st.metric("RAG Response Length", f"{rag_length} chars")
        
        with col4:
            direct_length = len(direct_response.get("response", "")) if direct_response.get("success") else 0
            st.metric("Direct Response Length", f"{direct_length} chars")
        
        with col5:
            sources_count = len(rag_response.get("sources", []))
            st.metric("Sources Used", sources_count)