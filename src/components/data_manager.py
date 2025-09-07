"""
Data management components for the F1 RAG chatbot
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List
from src.utils.logger import app_logger

class DataManager:
    """Data management interface"""
    
    def __init__(self):
        pass
    
    def render_scraping_progress(self, progress: float, status: str):
        """Render scraping progress"""
        progress_bar = st.progress(progress)
        status_text = st.text(status)
        return progress_bar, status_text
    
    def render_scraping_results(self, stats: Dict):
        """Render scraping results"""
        if not stats:
            return
        
        st.subheader("🕷️ Scraping Results")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total URLs", stats.get('total_urls', 0))
        
        with col2:
            st.metric("Successful", stats.get('successful', 0))
        
        with col3:
            st.metric("Failed", stats.get('failed', 0))
        
        with col4:
            st.metric("Skipped", stats.get('skipped', 0))
        
        # Success rate
        total = stats.get('total_urls', 1)
        success_rate = (stats.get('successful', 0) / total) * 100
        
        st.progress(success_rate / 100)
        st.caption(f"Success Rate: {success_rate:.1f}%")
        
        # Failed URLs
        failed_urls = stats.get('failed_urls', [])
        if failed_urls:
            with st.expander(f"⚠️ Failed URLs ({len(failed_urls)})"):
                for failed in failed_urls:
                    st.write(f"❌ {failed.get('title', 'Unknown')}: {failed.get('error', 'Unknown error')}")
    
    def render_knowledge_base_stats(self, vector_count: int, chunk_count: int):
        """Render knowledge base statistics"""
        st.subheader("🧠 Knowledge Base Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Chunks", chunk_count)
        
        with col2:
            st.metric("Vector Count", vector_count)
        
        # Storage usage (approximate)
        storage_mb = (vector_count * 768 * 4) / (1024 * 1024)  # 768 dim, 4 bytes per float
        st.metric("Approx. Storage", f"{storage_mb:.1f} MB")
        
        # Pinecone free tier info
        st.info("📊 **Pinecone Free Tier**: 1GB storage, ~100K vectors max")
        
        if vector_count > 90000:
            st.warning("⚠️ Approaching Pinecone free tier limit!")
    
    def render_refresh_options(self):
        """Render data refresh options"""
        st.subheader("🔄 Refresh Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Refresh All", help="Re-scrape all sources", use_container_width=True):
                return "refresh_all"
        
        with col2:
            if st.button("➕ Add New Only", help="Only scrape new/failed sources", use_container_width=True):
                return "add_new"
        
        return None
    
    def render_data_sources(self, sources: List[Dict]):
        """Render data sources information"""
        st.subheader("📚 Data Sources")
        
        if not sources:
            st.warning("No data sources configured")
            return
        
        # Group by category
        categories = {}
        for source in sources:
            category = source.get('category', 'general')
            if category not in categories:
                categories[category] = []
            categories[category].append(source)
        
        # Display by category
        for category, cat_sources in categories.items():
            with st.expander(f"{category.title()} Sources ({len(cat_sources)})"):
                for source in cat_sources:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"**{source.get('title', 'Unknown')}**")
                        st.caption(source.get('url', 'No URL'))
                    
                    with col2:
                        priority = source.get('priority', 3)
                        st.metric("Priority", priority)
                    
                    with col3:
                        if st.button(f"🔗 Visit", key=f"visit_{hash(source.get('url', ''))}"):
                            st.write(f"[Open]({source.get('url', '#')})")