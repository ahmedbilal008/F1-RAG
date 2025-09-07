"""
F1 RAG Chatbot - Main Streamlit Application
"""

import streamlit as st
import os
from datetime import datetime
from streamlit_option_menu import option_menu

# Import our custom modules
from src.utils.config import config
from src.utils.logger import app_logger
from src.core.scraper import F1ContentScraper
from src.core.rag_chain import F1RAGChain
from src.components.chat_interface import ChatInterface, QuickExamples, ResponseComparison

# Page configuration
st.set_page_config(
    page_title="F1 RAG Chat",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/f1-rag-chatbot',
        'Report a bug': "https://github.com/your-repo/f1-rag-chatbot/issues",
        'About': "F1 RAG Chat powered by Pinecone & Google Gemini"
    }
)

# Force sidebar to always be expanded by clearing any sidebar state
if 'sidebar_state' in st.session_state:
    del st.session_state['sidebar_state']

# Custom CSS
def load_custom_css():
    """Load custom CSS for carbon fiber dark theme"""
    st.markdown("""
    <style>
        /* Import professional fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
        
        /* Global dark theme */
        .stApp {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #111111 100%);
            color: #ffffff;
        }
        
        /* Remove default Streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display: none;}
        header[data-testid="stHeader"] {display: none;}
        
        /* Force sidebar to always be visible - hide collapse button */
        button[data-testid="collapsedControl"] {
            display: none !important;
            visibility: hidden !important;
        }
        
        /* Hide any sidebar collapse/expand buttons */
        .css-1d391kg button[kind="header"],
        .css-1y4p8pa button[kind="header"],
        button[data-testid="baseButton-header"] {
            display: none !important;
            visibility: hidden !important;
        }
        
        /* Force sidebar to stay expanded */
        section[data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
        }
        
        .css-1d391kg {
            display: block !important;
        }
        
        /* Carbon fiber header */
        .main-header {
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 50%, #1f1f1f 100%);
            border: 1px solid #333333;
            padding: 2rem;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 1.5rem;
            color: #ffffff;
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
            position: relative;
            overflow: hidden;
        }
        
        .main-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-image: 
                repeating-linear-gradient(
                    45deg,
                    transparent,
                    transparent 2px,
                    rgba(255,255,255,0.03) 2px,
                    rgba(255,255,255,0.03) 4px
                );
            pointer-events: none;
        }
        
        .main-header h1 {
            margin: 0;
            font-size: 2.2rem;
            font-weight: 600;
            letter-spacing: -0.02em;
            color: #ffffff;
            text-shadow: 0 2px 4px rgba(0,0,0,0.5);
            position: relative;
            z-index: 1;
        }
        
        .main-header p {
            margin: 0.5rem 0 0 0;
            font-size: 1rem;
            color: #cccccc;
            font-weight: 400;
            position: relative;
            z-index: 1;
        }
        
        .header-badges {
            margin-top: 1rem;
            display: flex;
            justify-content: center;
            gap: 0.5rem;
            flex-wrap: wrap;
            position: relative;
            z-index: 1;
        }
        
        .badge {
            background: rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
            border: 1px solid #333333;
            padding: 0.4rem 0.8rem;
            border-radius: 16px;
            font-size: 0.75rem;
            font-weight: 500;
            color: #cccccc;
        }
        
        /* Dark carbon cards */
        .info-card {
            background: linear-gradient(135deg, #1f1f1f 0%, #2a2a2a 100%);
            border: 1px solid #333333;
            padding: 1.2rem;
            border-radius: 8px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.3);
            margin: 1rem 0;
            transition: all 0.2s ease;
            color: #ffffff;
        }
        
        .info-card:hover {
            border-color: #555555;
            box-shadow: 0 6px 20px rgba(0,0,0,0.4);
        }
        
        .info-card h3 {
            margin: 0 0 0.3rem 0;
            font-size: 0.75rem;
            font-weight: 500;
            color: #999999;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .info-card .value {
            font-size: 1rem;
            font-weight: 600;
            color: #ffffff;
        }
        
        /* Dark status indicators */
        .status-ready {
            background: linear-gradient(135deg, #2d5a2d, #1e3e1e);
            color: #ffffff;
            padding: 0.6rem 1rem;
            border-radius: 6px;
            font-weight: 500;
            text-align: center;
            margin: 0.5rem 0;
            font-size: 0.8rem;
            border: 1px solid #3d6a3d;
        }
        
        .status-pending {
            background: linear-gradient(135deg, #5a4d2d, #3e2f1e);
            color: #ffffff;
            padding: 0.6rem 1rem;
            border-radius: 6px;
            font-weight: 500;
            text-align: center;
            margin: 0.5rem 0;
            font-size: 0.8rem;
            border: 1px solid #6a5d3d;
        }
        
        .status-error {
            background: linear-gradient(135deg, #5a2d2d, #3e1e1e);
            color: #ffffff;
            padding: 0.6rem 1rem;
            border-radius: 6px;
            font-weight: 500;
            text-align: center;
            margin: 0.5rem 0;
            font-size: 0.8rem;
            border: 1px solid #6a3d3d;
        }
        
        /* Dark sidebar */
        .sidebar-section {
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            border: 1px solid #333333;
            padding: 1.2rem;
            border-radius: 8px;
            margin: 1rem 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            color: #ffffff;
        }
        
        .sidebar-header {
            font-size: 0.9rem;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 0.8rem;
            padding-bottom: 0.4rem;
            border-bottom: 1px solid #333333;
        }
        
        /* Dark buttons */
        .stButton > button {
            background: linear-gradient(135deg, #2a2a2a 0%, #1f1f1f 100%);
            border: 1px solid #444444;
            color: #ffffff;
            border-radius: 6px;
            font-weight: 500;
            font-size: 0.8rem;
            transition: all 0.2s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        .stButton > button:hover {
            border-color: #666666;
            background: linear-gradient(135deg, #333333 0%, #2a2a2a 100%);
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }
        
        .stButton > button:focus {
            border-color: #666666;
            box-shadow: 0 0 0 2px rgba(102, 102, 102, 0.2);
        }
        
        /* Dark toggles and inputs */
        .stToggle {
            margin: 1rem 0;
        }
        
        .stToggle > div > div {
            background-color: #2a2a2a !important;
        }
        
        /* Dark expander */
        .streamlit-expanderHeader {
            background: linear-gradient(135deg, #1f1f1f 0%, #2a2a2a 100%);
            border: 1px solid #333333;
            border-radius: 6px;
            font-weight: 500;
            color: #ffffff;
        }
        
        /* Dark alerts */
        .stAlert {
            border-radius: 6px;
            border: 1px solid #333333;
            background: linear-gradient(135deg, #1f1f1f 0%, #2a2a2a 100%);
            color: #ffffff;
        }
        
        /* Chat improvements */
        .chat-container {
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            border: 1px solid #333333;
            border-radius: 8px;
            padding: 1.2rem;
            box-shadow: 0 4px 16px rgba(0,0,0,0.3);
            color: #ffffff;
        }
        
        /* Dark metric cards */
        .metric-card {
            background: linear-gradient(135deg, #1f1f1f 0%, #2a2a2a 100%);
            border: 1px solid #333333;
            padding: 1rem;
            border-radius: 6px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            color: #ffffff;
        }
        
        .metric-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: #ffffff;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .metric-label {
            font-size: 0.7rem;
            color: #999999;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-top: 0.2rem;
        }
        
        /* Override Streamlit text colors */
        .stMarkdown, .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            color: #ffffff !important;
        }
        
        .stSelectbox label, .stTextInput label, .stTextArea label {
            color: #ffffff !important;
        }
        
        /* Dark chat input */
        .stTextInput > div > div > input {
            background-color: #2a2a2a !important;
            border-color: #444444 !important;
            color: #ffffff !important;
        }
        
        /* Dark option menu - Chat/Compare/Analytics bar */
        .nav-link {
            background-color: #1a1a1a !important;
            color: #ffffff !important;
            border: 1px solid #333333 !important;
        }
        
        .nav-link.active {
            background-color: #2a2a2a !important;
            color: #ffffff !important;
        }
        
        /* Override option menu styling */
        div[data-baseweb="tab-list"] {
            background-color: #1a1a1a !important;
            border-radius: 8px !important;
            border: 1px solid #333333 !important;
        }
        
        div[data-baseweb="tab"] {
            background-color: transparent !important;
            color: #ffffff !important;
        }
        
        div[data-baseweb="tab"][aria-selected="true"] {
            background-color: #2a2a2a !important;
            color: #ffffff !important;
        }
        
        /* Streamlit option menu override */
        .streamlit-option-menu {
            background-color: #1a1a1a !important;
        }
        
        .streamlit-option-menu .nav-link {
            background-color: transparent !important;
            color: #ffffff !important;
        }
        
        .streamlit-option-menu .nav-link.active {
            background-color: #2a2a2a !important;
            color: #ffffff !important;
        }
        
        /* Mobile responsive */
        @media (max-width: 768px) {
            .main-header h1 {
                font-size: 1.8rem;
            }
            .main-header p {
                font-size: 0.9rem;
            }
            .badge {
                font-size: 0.7rem;
                padding: 0.3rem 0.6rem;
            }
            .sidebar-toggle {
                width: 36px;
                height: 36px;
                font-size: 1rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)


class F1RAGApp:
    """Main application class"""
    
    def __init__(self):
        self.chat_interface = ChatInterface()
        self.scraper = None
        self.rag_chain = None
        self.initialize_session_state()
        
    def initialize_session_state(self):
        """Initialize session state variables"""
        if "app_initialized" not in st.session_state:
            st.session_state.app_initialized = False
        
        if "knowledge_base_ready" not in st.session_state:
            st.session_state.knowledge_base_ready = False
        
        if "rag_mode" not in st.session_state:
            st.session_state.rag_mode = True
        
        if "system_status" not in st.session_state:
            st.session_state.system_status = {}
        
        if "scraping_stats" not in st.session_state:
            st.session_state.scraping_stats = {}
        
        # Reset sidebar state to always show sidebar
        st.session_state.sidebar_collapsed = False
    
    def check_configuration(self) -> bool:
        """Check if configuration is valid"""
        validation = config.validate()
        
        if not validation["valid"]:
            st.error("❌ Configuration Error")
            for error in validation["errors"]:
                st.error(f"• {error}")
            
            st.info("**Setup Instructions:**")
            st.markdown("""
            1. **Get Google AI API Key**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
            2. **Get Pinecone API Key**: Visit [Pinecone Console](https://app.pinecone.io/)
            3. **Add to Streamlit Secrets** or create `.env` file:
               ```
               GOOGLE_API_KEY=your_google_api_key
               PINECONE_API_KEY=your_pinecone_api_key
               ```
            """)
            return False
        
        if validation["warnings"]:
            with st.expander("⚠️ Configuration Warnings"):
                for warning in validation["warnings"]:
                    st.warning(f"• {warning}")
        
        return True
    
    def initialize_components(self):
        """Initialize core components"""
        try:
            if not st.session_state.app_initialized:
                with st.spinner("🚀 Initializing F1 RAG System..."):
                    self.scraper = F1ContentScraper()
                    self.rag_chain = F1RAGChain()
                    st.session_state.app_initialized = True
                    app_logger.info("F1 RAG App initialized successfully")
            else:
                self.scraper = F1ContentScraper()
                self.rag_chain = F1RAGChain()
        except Exception as e:
            st.error(f"❌ Failed to initialize components: {e}")
            app_logger.error(f"Component initialization error: {e}")
            return False
        
        return True
    
    def render_header(self):
        """Render main application header"""
        st.markdown("""
        <div class="main-header">
            <h1>F1 RAG Chat</h1>
            <p>Simple Formula 1 chatbot with RAG technology</p>
            <div class="header-badges">
                <span class="badge">RAG</span>
                <span class="badge">AI Chat</span>
                <span class="badge">F1 Data</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick status indicators
        if st.session_state.get('knowledge_base_ready', False) or st.session_state.get('rag_mode', True):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                status = "Ready" if st.session_state.knowledge_base_ready else "Pending"
                status_class = "status-ready" if st.session_state.knowledge_base_ready else "status-pending"
                st.markdown(f"""
                <div class="{status_class}">
                    Knowledge Base: {status}
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                mode = "RAG Mode" if st.session_state.rag_mode else "Direct Mode"
                st.markdown(f"""
                <div class="info-card" style="text-align: center;">
                    <h3>Response Mode</h3>
                    <div class="value">{mode}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                chat_stats = self.chat_interface.get_chat_stats() if hasattr(self, 'chat_interface') else {}
                msg_count = chat_stats.get('total_messages', 0)
                st.markdown(f"""
                <div class="info-card" style="text-align: center;">
                    <h3>Chat Messages</h3>
                    <div class="value">{msg_count} total</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                # System health indicator
                st.markdown(f"""
                <div class="status-ready">
                    System Status: Operational
                </div>
                """, unsafe_allow_html=True)
    
    def render_sidebar(self):
        """Render sidebar with controls and status"""
        with st.sidebar:
            # Sidebar Header
            st.markdown("""
            <div class="sidebar-section" style="text-align: center; border-bottom: 1px solid #333333;">
                <h2 style="color: #ffffff; margin: 0; font-weight: 600;">Control Panel</h2>
                <p style="color: #cccccc; margin: 0.5rem 0 0 0; font-size: 0.875rem;">Manage your F1 chat</p>
            </div>
            """, unsafe_allow_html=True)
            
            # RAG Mode Toggle Section
            with st.container():
                st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
                st.markdown('<p class="sidebar-header">Response Mode</p>', unsafe_allow_html=True)
                
                rag_mode = st.toggle(
                    "Enable RAG Mode",
                    value=st.session_state.rag_mode,
                    help="Toggle between RAG (knowledge-based) and Direct AI responses",
                    key="rag_toggle"
                )
                st.session_state.rag_mode = rag_mode
                
                if rag_mode:
                    st.markdown("""
                    <div class="status-ready">
                        RAG Mode Active<br>
                        <small>Using F1 knowledge base</small>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="status-pending">
                        Direct Mode Active<br>
                        <small>Using general AI knowledge</small>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Knowledge Base Management Section
            with st.container():
                st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
                st.markdown('<p class="sidebar-header">📚 Knowledge Base</p>', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🚀 Initialize", use_container_width=True, type="primary"):
                        self.initialize_knowledge_base(force_refresh=False)
                
                with col2:
                    if st.button("🔄", help="Refresh", use_container_width=True):
                        self.initialize_knowledge_base(force_refresh=True)
                
                if st.button("System Status", use_container_width=True):
                    self.check_system_status()
                
                # Knowledge Base Status
                if st.session_state.knowledge_base_ready:
                    st.markdown("""
                    <div class="status-ready">
                        Knowledge Base Ready<br>
                        <small>All systems operational</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show stats if available
                    if st.session_state.scraping_stats:
                        stats = st.session_state.scraping_stats
                        with st.expander("Detailed Statistics"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("URLs", stats.get('total_urls', 0))
                                st.metric("Failed", stats.get('failed', 0))
                            with col2:
                                st.metric("Success", stats.get('successful', 0))
                                st.metric("Skipped", stats.get('skipped', 0))
                else:
                    st.markdown("""
                    <div class="status-pending">
                        Knowledge Base Not Ready<br>
                        <small>Click Initialize to set up</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Chat Management Section
            with st.container():
                st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
                st.markdown('<p class="sidebar-header">Chat Management</p>', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️", help="Clear chat", use_container_width=True):
                        self.chat_interface.clear_chat()
                        st.rerun()
                
                with col2:
                    if st.button("📥", help="Export chat", use_container_width=True):
                        self.export_chat_history()
                
                # Chat Statistics
                chat_stats = self.chat_interface.get_chat_stats()
                if chat_stats and chat_stats.get('total_messages', 0) > 0:
                    with st.expander("Chat Analytics"):
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{chat_stats.get('total_messages', 0)}</div>
                            <div class="metric-label">Total Messages</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("RAG", chat_stats.get('rag_responses', 0))
                        with col2:
                            st.metric("Direct", chat_stats.get('direct_responses', 0))
                            
                        if chat_stats.get('avg_sources_per_rag', 0) > 0:
                            st.metric("Avg Sources", f"{chat_stats['avg_sources_per_rag']:.1f}")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Quick Actions Section
            with st.container():
                st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
                st.markdown('<p class="sidebar-header">Quick Actions</p>', unsafe_allow_html=True)
                
                if st.button("🔄 Refresh Page", use_container_width=True):
                    st.rerun()
                    
                if st.button("ℹ️ Show Help", use_container_width=True):
                    st.session_state.show_help = not st.session_state.get('show_help', False)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Footer
            st.markdown("""
            <div style="text-align: center; padding: 1rem 0; margin-top: 2rem; border-top: 1px solid #e9ecef; color: #6c757d; font-size: 0.8rem;">
                <p>🏎️ F1 RAG Chatbot v1.0<br>
                Powered by Pinecone & Gemini AI</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.divider()
            
            # System Information
            with st.expander("ℹ️ System Information"):
                st.markdown(f"""
                **Configuration:**
                - Embedding Model: `{config.EMBEDDING_MODEL}`
                - LLM Model: `{config.LLM_MODEL}`
                - Index Name: `{config.PINECONE_INDEX_NAME}`
                - Top-K Results: `{config.TOP_K_RESULTS}`
                - Chunk Size: `{config.CHUNK_SIZE}`
                
                **Status:**
                - App Initialized: `{st.session_state.app_initialized}`
                - KB Ready: `{st.session_state.knowledge_base_ready}`
                - Debug Mode: `{config.DEBUG}`
                """)
    
    def initialize_knowledge_base(self, force_refresh: bool = False):
        """Initialize or refresh the knowledge base"""
        if not self.scraper or not self.rag_chain:
            st.error("❌ Components not initialized")
            return
        
        # First check if we already have data in Pinecone (unless forcing refresh)
        if not force_refresh:
            with st.spinner("� Checking existing knowledge base..."):
                connection_status = self.rag_chain.vector_store.check_connection()
                if connection_status.get("connected"):
                    stats = connection_status.get("stats", {})
                    vector_count = stats.get("total_vector_count", 0)
                    
                    if vector_count > 0:
                        st.success(f"✅ Found existing knowledge base with {vector_count} vectors!")
                        st.session_state.knowledge_base_ready = True
                        st.info("Use 'Force Refresh' if you want to update with latest content")
                        return

        with st.spinner("�🕷️ Scraping F1 content..."):
            # Show scraping progress
            progress_container = st.container()
            
            with progress_container:
                st.info("📥 Scraping Formula 1 content from Wikipedia...")
                
                # Scrape documents
                documents, scraping_stats = self.scraper.scrape_all_sources(force_refresh=force_refresh)
                
                if not documents:
                    st.error("❌ No documents were scraped successfully")
                    return
                
                st.success(f"✅ Scraped {len(documents)} documents successfully")
                st.session_state.scraping_stats = scraping_stats
                
                # Show failed URLs if any
                if scraping_stats.get('failed_urls'):
                    with st.expander("⚠️ Failed URLs"):
                        for failed in scraping_stats['failed_urls']:
                            st.write(f"❌ {failed['title']}: {failed['error']}")

        with st.spinner("🧠 Creating embeddings and storing in Pinecone..."):
            # Refresh or add to knowledge base
            if force_refresh:
                result = self.rag_chain.refresh_knowledge_base(documents)
            else:
                result = self.rag_chain.vector_store.add_documents(documents)
            
            if result["success"]:
                st.success("🎉 Knowledge Base initialized successfully!")
                st.session_state.knowledge_base_ready = True
                
                # Show statistics
                with st.expander("📊 Knowledge Base Statistics"):
                    st.metric("Documents Processed", len(documents))
                    st.metric("Total Chunks", result.get('total_chunks', 0))
                    
                    index_stats = result.get('index_stats', {})
                    if index_stats:
                        st.metric("Vectors in Index", index_stats.get('total_vector_count', 0))
                        st.metric("Index Dimension", index_stats.get('dimension', 0))
            else:
                st.error(f"❌ Failed to initialize knowledge base: {result.get('error')}")
                st.session_state.knowledge_base_ready = False
    
    def check_system_status(self):
        """Check and display system status"""
        if not self.rag_chain:
            st.error("❌ RAG chain not initialized")
            return
        
        with st.spinner("Checking system status..."):
            status = self.rag_chain.check_system_status()
            st.session_state.system_status = status
            
            # Display status
            st.subheader("🔧 System Status")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Vector Store")
                vs_status = status.get('vector_store', {})
                if vs_status.get('connected'):
                    st.success("✅ Connected to Pinecone")
                    stats = vs_status.get('stats', {})
                    if stats:
                        st.metric("Vector Count", stats.get('total_vector_count', 0))
                        st.metric("Dimension", stats.get('dimension', 0))
                else:
                    st.error(f"❌ Connection failed: {vs_status.get('error', 'Unknown error')}")
            
            with col2:
                st.markdown("### Language Model")
                llm_status = status.get('llm', {})
                if llm_status.get('connected'):
                    st.success("✅ Connected to Gemini AI")
                else:
                    st.error(f"❌ Connection failed: {llm_status.get('error', 'Unknown error')}")
            
            # Configuration info
            with st.expander("🔧 Current Configuration"):
                config_info = status.get('config', {})
                for key, value in config_info.items():
                    st.write(f"**{key.replace('_', ' ').title()}:** `{value}`")
    
    def export_chat_history(self):
        """Export chat history"""
        chat_export = self.chat_interface.export_chat_history()
        
        if chat_export == "No chat history to export.":
            st.warning("⚠️ No chat history to export")
            return
        
        st.download_button(
            label="📥 Download Chat History",
            data=chat_export,
            file_name=f"f1_chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
    
    def handle_user_input(self, user_input: str):
        """Handle user input and generate response"""
        if not user_input.strip():
            return
        
        # Add user message to chat
        self.chat_interface.add_message("user", user_input)
        
        # Check if RAG mode is enabled but knowledge base is not ready
        if st.session_state.rag_mode and not st.session_state.knowledge_base_ready:
            error_msg = "⚠️ RAG mode is enabled but knowledge base is not ready. Please initialize the knowledge base first or switch to Direct mode."
            self.chat_interface.add_message("assistant", error_msg, method="error")
            return
        
        # Generate response
        with st.spinner("Thinking..."):
            try:
                response = self.rag_chain.get_response(
                    question=user_input,
                    use_rag=st.session_state.rag_mode
                )
                
                if response["success"]:
                    self.chat_interface.add_message(
                        "assistant",
                        response["response"],
                        sources=response.get("sources", []),
                        method=response.get("method", "unknown"),
                        metadata={
                            "context_used": response.get("context_used", 0),
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                else:
                    error_msg = f"❌ {response.get('response', 'Unknown error occurred')}"
                    self.chat_interface.add_message("assistant", error_msg, method="error")
                
            except Exception as e:
                error_msg = f"❌ An unexpected error occurred: {str(e)}"
                self.chat_interface.add_message("assistant", error_msg, method="error")
                app_logger.error(f"Error handling user input: {e}")
    
    def render_main_interface(self):
        """Render main chat interface"""
        # Main navigation
        selected = option_menu(
            menu_title=None,
            options=["💬 Chat", "🔄 Compare", "📊 Analytics"],
            icons=['chat', 'arrow-left-right', 'bar-chart'],
            menu_icon="cast",
            default_index=0,
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "#1a1a1a", "border": "1px solid #333333", "border-radius": "8px"},
                "icon": {"color": "#ffffff", "font-size": "18px"},
                "nav-link": {
                    "font-size": "16px", 
                    "text-align": "center", 
                    "margin": "0px", 
                    "background-color": "transparent",
                    "color": "#ffffff",
                    "--hover-color": "#2a2a2a"
                },
                "nav-link-selected": {
                    "background-color": "#2a2a2a",
                    "color": "#ffffff"
                },
            }
        )
        
        if selected == "💬 Chat":
            self.render_chat_tab()
        elif selected == "🔄 Compare":
            self.render_compare_tab()
        elif selected == "📊 Analytics":
            self.render_analytics_tab()
    
    def render_chat_tab(self):
        """Render main chat tab"""
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("💬 Chat with F1 Assistant")
            
            # Chat messages container
            chat_container = st.container()
            with chat_container:
                self.chat_interface.display_chat_messages()
            
            # Chat input
            user_input = st.chat_input(
                "Ask me anything about Formula 1...",
                disabled=st.session_state.rag_mode and not st.session_state.knowledge_base_ready
            )
            
            if user_input:
                # Display user message immediately
                with st.chat_message("user"):
                    st.markdown(user_input)
                
                # Generate and display response
                with st.chat_message("assistant"):
                    self.handle_user_input(user_input)
                    st.rerun()
        
        with col2:
            # Quick examples and tips
            QuickExamples.display_examples(
                on_click_callback=lambda q: self.handle_user_input(q) or st.rerun()
            )
            
            # Tips section
            with st.expander("Tips for Better Results"):
                st.markdown("""
                **For RAG Mode:**
                - Ask specific F1 questions
                - Reference current seasons, drivers, or teams
                - Ask about regulations or technical details
                
                **For Direct Mode:**
                - General F1 knowledge questions
                - Historical comparisons
                - Opinion-based questions
                
                **Examples:**
                - "What happened in the 2024 Monaco GP?"
                - "Compare Lewis Hamilton and Michael Schumacher"
                - "How do F1 engines work?"
                """)
    
    def render_compare_tab(self):
        """Render comparison tab"""
        st.subheader("🔄 RAG vs Direct AI Comparison")
        st.markdown("Compare responses from RAG mode vs Direct AI mode for the same question.")
        
        # Question input
        compare_question = st.text_input(
            "Enter your F1 question:",
            placeholder="e.g., Who won the 2024 F1 championship?",
            key="compare_question"
        )
        
        if st.button("🚀 Generate Both Responses", disabled=not compare_question.strip()):
            if not st.session_state.knowledge_base_ready:
                st.warning("⚠️ Knowledge base not ready. RAG response will fail.")
            
            with st.spinner("Generating responses..."):
                col1, col2 = st.columns(2)
                
                # Generate RAG response
                with col1:
                    st.markdown("### 🧠 RAG Response")
                    try:
                        rag_response = self.rag_chain.get_rag_response(compare_question)
                        if rag_response["success"]:
                            st.success("✅ Generated")
                            st.markdown(rag_response["response"])
                            
                            sources = rag_response.get("sources", [])
                            if sources:
                                with st.expander(f"📚 Sources ({len(sources)})"):
                                    for i, source in enumerate(sources, 1):
                                        st.write(f"{i}. {source.get('title')} (Score: {source.get('score', 0):.3f})")
                        else:
                            st.error("❌ Failed")
                            st.error(rag_response.get("response", "Unknown error"))
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                
                # Generate Direct response
                with col2:
                    st.markdown("### 🤖 Direct AI Response")
                    try:
                        direct_response = self.rag_chain.get_direct_response(compare_question)
                        if direct_response["success"]:
                            st.success("✅ Generated")
                            st.markdown(direct_response["response"])
                            st.info("Based on general AI knowledge")
                        else:
                            st.error("❌ Failed")
                            st.error(direct_response.get("response", "Unknown error"))
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
    
    def render_analytics_tab(self):
        """Render analytics and statistics tab"""
        st.subheader("📊 System Analytics")
        
        # System Status
        if st.session_state.system_status:
            status = st.session_state.system_status
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                vs_connected = status.get('vector_store', {}).get('connected', False)
                st.metric(
                    "Vector Store", 
                    "✅ Connected" if vs_connected else "❌ Disconnected",
                    delta="Pinecone"
                )
            
            with col2:
                llm_connected = status.get('llm', {}).get('connected', False)
                st.metric(
                    "Language Model", 
                    "✅ Connected" if llm_connected else "❌ Disconnected",
                    delta="Gemini AI"
                )
            
            with col3:
                kb_ready = st.session_state.knowledge_base_ready
                st.metric(
                    "Knowledge Base", 
                    "✅ Ready" if kb_ready else "⏳ Not Ready",
                    delta="F1 Data"
                )
        
        st.divider()
        
        # Scraping Statistics
        if st.session_state.scraping_stats:
            st.markdown("### 🕷️ Data Scraping Statistics")
            stats = st.session_state.scraping_stats
            
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
        
        st.divider()
        
        # Chat Analytics
        chat_stats = self.chat_interface.get_chat_stats()
        if chat_stats:
            st.markdown("### 💬 Chat Analytics")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Messages", chat_stats.get('total_messages', 0))
                st.metric("User Messages", chat_stats.get('user_messages', 0))
                st.metric("Assistant Messages", chat_stats.get('assistant_messages', 0))
            
            with col2:
                st.metric("RAG Responses", chat_stats.get('rag_responses', 0))
                st.metric("Direct Responses", chat_stats.get('direct_responses', 0))
                if chat_stats.get('avg_sources_per_rag', 0) > 0:
                    st.metric("Avg Sources per RAG", f"{chat_stats['avg_sources_per_rag']:.1f}")
        else:
            st.info("💬 Start chatting to see analytics!")
    
    def run(self):
        """Run the main application"""
        load_custom_css()
        
        # Check configuration first
        if not self.check_configuration():
            return
        
        # Initialize components
        if not self.initialize_components():
            return
        
        # Render UI
        self.render_header()
        self.render_sidebar()
        self.render_main_interface()


def main():
    """Main application entry point"""
    try:
        app = F1RAGApp()
        app.run()
    except Exception as e:
        st.error(f"❌ Application Error: {e}")
        app_logger.error(f"Application error: {e}")
        
        if config.DEBUG:
            st.exception(e)


if __name__ == "__main__":
    main()