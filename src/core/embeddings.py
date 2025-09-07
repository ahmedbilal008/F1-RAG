"""
Embedding generation and management for F1 RAG system
"""

from typing import List, Dict, Optional
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import numpy as np
from src.utils.logger import app_logger
from src.utils.config import config

class EmbeddingManager:
    """Manages embedding generation and operations"""
    
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=config.EMBEDDING_MODEL,
            google_api_key=config.GOOGLE_API_KEY
        )
        self.dimension = config.EMBEDDING_DIMENSION
    
    def generate_embeddings(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        try:
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                app_logger.info(f"Generating embeddings for batch {i//batch_size + 1}")
                
                batch_embeddings = self.embeddings.embed_documents(batch)
                all_embeddings.extend(batch_embeddings)
            
            app_logger.success(f"Generated {len(all_embeddings)} embeddings")
            return all_embeddings
            
        except Exception as e:
            app_logger.error(f"Error generating embeddings: {e}")
            return []
    
    def generate_query_embedding(self, query: str) -> Optional[List[float]]:
        """Generate embedding for a single query"""
        try:
            embedding = self.embeddings.embed_query(query)
            return embedding
        except Exception as e:
            app_logger.error(f"Error generating query embedding: {e}")
            return None
    
    def calculate_similarity(self, emb1: List[float], emb2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            vec1 = np.array(emb1)
            vec2 = np.array(emb2)
            
            # Cosine similarity
            similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            return float(similarity)
            
        except Exception as e:
            app_logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def validate_embedding(self, embedding: List[float]) -> bool:
        """Validate embedding format and dimension"""
        if not embedding:
            return False
        
        if len(embedding) != self.dimension:
            app_logger.warning(f"Embedding dimension mismatch: got {len(embedding)}, expected {self.dimension}")
            return False
        
        # Check for valid values
        if not all(isinstance(x, (int, float)) for x in embedding):
            return False
        
        return True
    
    def get_embedding_stats(self, embeddings: List[List[float]]) -> Dict:
        """Get statistics about a list of embeddings"""
        if not embeddings:
            return {}
        
        embeddings_array = np.array(embeddings)
        
        return {
            "count": len(embeddings),
            "dimension": embeddings_array.shape[1],
            "mean_norm": float(np.mean(np.linalg.norm(embeddings_array, axis=1))),
            "std_norm": float(np.std(np.linalg.norm(embeddings_array, axis=1))),
            "min_value": float(np.min(embeddings_array)),
            "max_value": float(np.max(embeddings_array))
        }