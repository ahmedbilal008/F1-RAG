"""
Pinecone vector store management for F1 RAG system
"""

import asyncio
import time
from typing import List, Dict, Optional, Tuple
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pinecone import Pinecone, ServerlessSpec
import numpy as np

from src.utils.logger import app_logger
from src.utils.config import config


class PineconeVectorStore:
    """Pinecone vector store manager for F1 content"""
    
    def __init__(self):
        self.pc = None
        self.index = None
        self.embeddings = None
        self.text_splitter = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Pinecone client and embeddings"""
        try:
            # Handle event loop for Streamlit compatibility
            import nest_asyncio
            nest_asyncio.apply()
            
            # Initialize Pinecone (no environment parameter needed in new API)
            self.pc = Pinecone(api_key=config.PINECONE_API_KEY)
            
            # Initialize embeddings
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=config.EMBEDDING_MODEL,
                google_api_key=config.GOOGLE_API_KEY
            )
            
            # Initialize text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=config.CHUNK_SIZE,
                chunk_overlap=config.CHUNK_OVERLAP,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            
            app_logger.info("Pinecone vector store initialized successfully")
            
        except ImportError:
            # If nest_asyncio is not available, try the asyncio approach
            try:
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Initialize Pinecone
                self.pc = Pinecone(api_key=config.PINECONE_API_KEY)
                
                # Initialize embeddings
                self.embeddings = GoogleGenerativeAIEmbeddings(
                    model=config.EMBEDDING_MODEL,
                    google_api_key=config.GOOGLE_API_KEY
                )
                
                # Initialize text splitter
                self.text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=config.CHUNK_SIZE,
                    chunk_overlap=config.CHUNK_OVERLAP,
                    separators=["\n\n", "\n", ". ", " ", ""]
                )
                
                app_logger.info("Pinecone vector store initialized successfully")
                
            except Exception as e:
                app_logger.error(f"Failed to initialize Pinecone: {e}")
                raise
        except Exception as e:
            app_logger.error(f"Failed to initialize Pinecone: {e}")
            raise
    
    def _get_or_create_index(self) -> bool:
        """Get existing index or create new one"""
        try:
            # Check if index exists by listing all indexes
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            
            if config.PINECONE_INDEX_NAME in existing_indexes:
                app_logger.info(f"Using existing index: {config.PINECONE_INDEX_NAME}")
                self.index = self.pc.Index(config.PINECONE_INDEX_NAME)
                return True
            else:
                app_logger.info(f"Creating new index: {config.PINECONE_INDEX_NAME}")
                
                # Create new index using ServerlessSpec (new API pattern)
                self.pc.create_index(
                    name=config.PINECONE_INDEX_NAME,
                    dimension=config.EMBEDDING_DIMENSION,
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
                
                # Alternative: Use create_index_for_model for integrated embeddings
                # Uncomment the code below and comment the above if you want to use 
                # Pinecone's integrated embedding models instead of Google's embeddings
                # 
                # self.pc.create_index_for_model(
                #     name=config.PINECONE_INDEX_NAME,
                #     cloud="aws",
                #     region="us-east-1",
                #     embed={
                #         "model": "llama-text-embed-v2",
                #         "field_map": {"text": "chunk_text"}
                #     }
                # )
                
                # Wait for index to be ready
                while not self.pc.describe_index(config.PINECONE_INDEX_NAME).status['ready']:
                    app_logger.info("Waiting for index to be ready...")
                    time.sleep(1)
                
                self.index = self.pc.Index(config.PINECONE_INDEX_NAME)
                app_logger.success(f"Index {config.PINECONE_INDEX_NAME} created successfully")
                return True
                
        except Exception as e:
            app_logger.error(f"Error with Pinecone index: {e}")
            return False
    
    def add_documents(self, documents: List[Document], batch_size: int = 50) -> Dict:
        """Add documents to Pinecone vector store"""
        if not self._get_or_create_index():
            return {"success": False, "error": "Failed to initialize index"}
        
        try:
            # Split documents into chunks
            app_logger.info(f"Splitting {len(documents)} documents into chunks...")
            all_chunks = []
            
            for doc in documents:
                chunks = self.text_splitter.split_documents([doc])
                all_chunks.extend(chunks)
            
            app_logger.info(f"Created {len(all_chunks)} chunks from documents")
            
            # Generate embeddings and upsert in batches
            total_chunks = len(all_chunks)
            processed_chunks = 0
            
            for i in range(0, total_chunks, batch_size):
                batch_chunks = all_chunks[i:i + batch_size]
                
                # Prepare batch data
                batch_texts = [chunk.page_content for chunk in batch_chunks]
                batch_metadatas = [chunk.metadata for chunk in batch_chunks]
                
                # Generate embeddings
                app_logger.info(f"Generating embeddings for batch {i//batch_size + 1}...")
                embeddings = self.embeddings.embed_documents(batch_texts)
                
                # Prepare vectors for upsert
                vectors = []
                for j, (text, metadata, embedding) in enumerate(zip(batch_texts, batch_metadatas, embeddings)):
                    vector_id = f"chunk_{i+j}_{hash(text[:100])}"
                    vectors.append({
                        "id": vector_id,
                        "values": embedding,
                        "metadata": {
                            **metadata,
                            "text": text[:1000],  # Store truncated text in metadata
                            "chunk_index": i + j
                        }
                    })
                
                # Upsert to Pinecone
                self.index.upsert(vectors=vectors)
                processed_chunks += len(batch_chunks)
                
                app_logger.info(f"Processed {processed_chunks}/{total_chunks} chunks")
                
                # Small delay to avoid rate limits
                time.sleep(0.5)
            
            # Get final index stats
            stats = self.index.describe_index_stats()
            
            return {
                "success": True,
                "total_chunks": total_chunks,
                "processed_chunks": processed_chunks,
                "index_stats": stats
            }
            
        except Exception as e:
            app_logger.error(f"Error adding documents to Pinecone: {e}")
            return {"success": False, "error": str(e)}
    
    def similarity_search(self, query: str, top_k: int = None) -> List[Dict]:
        """Perform similarity search in Pinecone"""
        if not self.index:
            if not self._get_or_create_index():
                return []
        
        try:
            top_k = top_k or config.TOP_K_RESULTS
            
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Search in Pinecone
            search_results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            # Convert results to documents
            documents = []
            for match in search_results.matches:
                if match.score >= config.SIMILARITY_THRESHOLD:
                    metadata = match.metadata
                    documents.append({
                        "content": metadata.get("text", ""),
                        "metadata": metadata,
                        "score": match.score
                    })
            
            app_logger.info(f"Found {len(documents)} relevant documents for query")
            return documents
            
        except Exception as e:
            app_logger.error(f"Error performing similarity search: {e}")
            return []
    
    def get_index_stats(self) -> Dict:
        """Get Pinecone index statistics"""
        if not self.index:
            if not self._get_or_create_index():
                return {}
        
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": stats.namespaces
            }
        except Exception as e:
            app_logger.error(f"Error getting index stats: {e}")
            return {}
    
    def delete_all_vectors(self) -> bool:
        """Delete all vectors from the index"""
        if not self.index:
            if not self._get_or_create_index():
                return False
        
        try:
            # Check if index has any vectors first
            stats = self.index.describe_index_stats()
            total_vectors = stats.total_vector_count
            
            if total_vectors == 0:
                app_logger.info("Index is already empty, no vectors to delete")
                return True
            
            # Delete all vectors
            self.index.delete(delete_all=True)
            app_logger.info(f"Deleted {total_vectors} vectors from index")
            return True
        except Exception as e:
            # If it's a "not found" error on empty index, that's fine
            if "Namespace not found" in str(e) or "404" in str(e):
                app_logger.info("Index is empty (namespace not found), proceeding...")
                return True
            else:
                app_logger.error(f"Error deleting vectors: {e}")
                return False
    
    def refresh_index(self, documents: List[Document]) -> Dict:
        """Refresh the entire index with new documents"""
        app_logger.info("Refreshing Pinecone index...")
        
        # Delete all existing vectors
        if not self.delete_all_vectors():
            return {"success": False, "error": "Failed to clear existing vectors"}
        
        # Wait a moment for deletion to process
        time.sleep(2)
        
        # Add new documents
        result = self.add_documents(documents)
        
        if result["success"]:
            app_logger.success("Index refreshed successfully")
        
        return result
    
    def check_connection(self) -> Dict:
        """Check Pinecone connection and index status"""
        try:
            # Try to get index stats
            if not self.index:
                if not self._get_or_create_index():
                    return {"connected": False, "error": "Failed to connect to index"}
            
            stats = self.get_index_stats()
            return {
                "connected": True,
                "index_name": config.PINECONE_INDEX_NAME,
                "stats": stats
            }
            
        except Exception as e:
            return {"connected": False, "error": str(e)}