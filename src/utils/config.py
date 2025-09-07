"""
Configuration management for the F1 RAG Chatbot
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the F1 RAG Chatbot"""
    
    # API Keys
    GOOGLE_API_KEY: str = ""
    PINECONE_API_KEY: str = ""
    
    # Pinecone Configuration
    PINECONE_INDEX_NAME: str = "f1-rag-chatbot"
    
    # App Configuration
    APP_TITLE: str = "F1 RAG Chat"
    DEBUG: bool = False
    LOG_LEVEL: str = "ERROR"
    
    # Embedding Configuration
    EMBEDDING_MODEL: str = "models/embedding-001"
    EMBEDDING_DIMENSION: int = 768
    
    # Text Splitting Configuration
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # Retrieval Configuration
    TOP_K_RESULTS: int = 5
    SIMILARITY_THRESHOLD: float = 0.7
    
    # LLM Configuration
    LLM_MODEL: str = "gemini-1.5-flash"
    LLM_TEMPERATURE: float = 0.3
    MAX_TOKENS: int = 1000
    
    def __init__(self):
        """Initialize configuration from environment variables or Streamlit secrets"""
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment variables or Streamlit secrets"""
        # Try to load from Streamlit secrets first (for deployment)
        try:
            self.GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", "")
            self.PINECONE_API_KEY = st.secrets.get("PINECONE_API_KEY", "")
            self.PINECONE_INDEX_NAME = st.secrets.get("PINECONE_INDEX_NAME", self.PINECONE_INDEX_NAME)
        except:
            # Fall back to environment variables (for local development)
            self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
            self.PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
            self.PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", self.PINECONE_INDEX_NAME)
        
        # Load other configuration
        self.DEBUG = os.getenv("DEBUG", "False").lower() == "true"
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", self.LOG_LEVEL)
    
    def validate(self) -> Dict[str, Any]:
        """Validate configuration and return status"""
        errors = []
        warnings = []
        
        # Check required API keys
        if not self.GOOGLE_API_KEY:
            errors.append("Google API Key is required")
        
        if not self.PINECONE_API_KEY:
            errors.append("Pinecone API Key is required")
        
        # Check configuration values
        if self.CHUNK_SIZE < 100:
            warnings.append("Chunk size is very small, might affect performance")
        
        if self.TOP_K_RESULTS > 10:
            warnings.append("High top-k value might slow down responses")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive data)"""
        return {
            "pinecone_index_name": self.PINECONE_INDEX_NAME,
            "embedding_model": self.EMBEDDING_MODEL,
            "embedding_dimension": self.EMBEDDING_DIMENSION,
            "chunk_size": self.CHUNK_SIZE,
            "chunk_overlap": self.CHUNK_OVERLAP,
            "top_k_results": self.TOP_K_RESULTS,
            "similarity_threshold": self.SIMILARITY_THRESHOLD,
            "llm_model": self.LLM_MODEL,
            "llm_temperature": self.LLM_TEMPERATURE,
            "max_tokens": self.MAX_TOKENS,
            "debug": self.DEBUG,
            "log_level": self.LOG_LEVEL
        }

# Global configuration instance
config = Config()   