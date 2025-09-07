"""
Sidebar components for the F1 RAG chatbot
"""

import streamlit as st
from typing import Dict, Any
from src.utils.logger import app_logger
from src.utils.config import config

class Sidebar:
    """Sidebar component manager"""
    
    def __init__(self):
        pass
    
    def render_rag_toggle(self) -> bool:
        """Render RAG mode toggle"""
        st.subheader("🔄 Response Mode")
        
        rag_mode = st.toggle(
            "🧠 RAG Mode",
            value=st.session_state.get('rag_mode', True),
            help="Toggle between RAG (knowledge-based) and Direct AI responses"
        )
        
        if rag_mode:
            st.success("🔍 **RAG Mode Active**\nUsing F1 knowledge base")
        else:
            st.info("🤖 **Direct Mode Active**\nUsing general AI knowledge")
        
        return rag_mode
    
    def render_system_status(self):
        """Render system status section"""
        st.subheader("📊 System Status")
        
        # Knowledge base status
        if st.session_state.get('knowledge_base_ready', False):
            st.success("✅ Knowledge Base Ready")
            
            # Show stats if available
            if st.session_state.get('scraping_stats'):
                stats = st.session_state.scraping_stats
                with st.expander("📈 KB Statistics"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Scraped", stats.get('successful', 0))
                        st.metric("Failed", stats.get('failed', 0))
                    with col2:
                        st.metric("Total URLs", stats.get('total_urls', 0))
                        st.metric("Skipped", stats.get('skipped', 0))
        else:
            st.warning("⏳ Knowledge Base Not Ready")
            st.info("👆 Initialize KB first")
    
    def render_controls(self):
        """Render control buttons"""
        st.subheader("⚙️ Controls")
        
        col1, col2 = st.columns(2)
        
        with col1:
            init_clicked = st.button(
                "🚀 Init KB", 
                help="Initialize/Refresh Knowledge Base",
                use_container_width=True,
                type="primary"
            )
        
        with col2:
            status_clicked = st.button(
                "📊 Status", 
                help="Check System Status",
                use_container_width=True
            )
        
        return init_clicked, status_clicked
    
    def render_chat_controls(self):
        """Render chat control buttons"""
        st.subheader("💬 Chat Controls")
        
        col1, col2 = st.columns(2)
        
        with col1:
            clear_clicked = st.button("🗑️ Clear", use_container_width=True)
        
        with col2:
            export_clicked = st.button("📥 Export", use_container_width=True)
        
        return clear_clicked, export_clicked
    
    def render_info(self):
        """Render information section"""
        with st.expander("ℹ️ System Info"):
            st.markdown(f"""
            **Configuration:**
            - LLM: `{config.LLM_MODEL}`
            - Embedding: `{config.EMBEDDING_MODEL}`
            - Index: `{config.PINECONE_INDEX_NAME}`
            - Chunk Size: `{config.CHUNK_SIZE}`
            - Top-K: `{config.TOP_K_RESULTS}`
            
            **Status:**
            - App Ready: `{st.session_state.get('app_initialized', False)}`
            - KB Ready: `{st.session_state.get('knowledge_base_ready', False)}`
            """)