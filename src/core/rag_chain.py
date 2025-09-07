"""
RAG Chain implementation for F1 chatbot
"""

from typing import List, Dict, Optional, Tuple
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from src.core.vector_store import PineconeVectorStore
from src.utils.logger import app_logger
from src.utils.config import config


class F1RAGChain:
    """RAG Chain for Formula 1 question answering"""
    
    def __init__(self):
        self.vector_store = PineconeVectorStore()
        self.llm = ChatGoogleGenerativeAI(
            model=config.LLM_MODEL,
            temperature=config.LLM_TEMPERATURE,
            max_tokens=config.MAX_TOKENS,
            google_api_key=config.GOOGLE_API_KEY
        )
        self.rag_prompt = self._create_rag_prompt()
        self.direct_prompt = self._create_direct_prompt()
        
    def _create_rag_prompt(self) -> PromptTemplate:
        """Create prompt template for RAG responses"""
        template = """You are a knowledgeable Formula 1 expert assistant. Use the provided context to answer the user's question about Formula 1.

Context from F1 knowledge base:
{context}

User Question: {question}

Instructions:
- Answer the question based on the provided context
- If the context doesn't contain enough information, mention what you do know and indicate where information might be limited
- Be specific and detailed when possible
- Include relevant F1 terminology and technical details
- If mentioning statistics, races, or specific events, try to be precise
- Keep your response engaging and informative

Answer:"""
        
        return PromptTemplate(
            input_variables=["context", "question"],
            template=template
        )
    
    def _create_direct_prompt(self) -> PromptTemplate:
        """Create prompt template for direct responses"""
        template = """You are a Formula 1 expert assistant. Answer the user's question about Formula 1 using your general knowledge.

User Question: {question}

Instructions:
- Provide a comprehensive answer about Formula 1
- Include relevant details, statistics, and context where appropriate
- Use F1 terminology and technical details when relevant
- Be engaging and informative
- If you're not certain about specific details, indicate your level of confidence

Answer:"""
        
        return PromptTemplate(
            input_variables=["question"],
            template=template
        )
    
    def _format_context(self, retrieved_docs: List[Dict]) -> str:
        """Format retrieved documents into context string"""
        if not retrieved_docs:
            return "No relevant context found in the knowledge base."
        
        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            source = metadata.get("source", "Unknown source")
            title = metadata.get("title", "Unknown title")
            score = doc.get("score", 0)
            
            # Truncate content if too long
            if len(content) > 500:
                content = content[:500] + "..."
            
            context_parts.append(
                f"Source {i} ({title}):\n{content}\n"
                f"[Relevance: {score:.3f}]\n"
            )
        
        return "\n".join(context_parts)
    
    def get_rag_response(self, question: str) -> Dict:
        """Get response using RAG approach"""
        try:
            app_logger.info(f"Processing RAG query: {question}")
            
            # Retrieve relevant documents
            retrieved_docs = self.vector_store.similarity_search(
                query=question,
                top_k=config.TOP_K_RESULTS
            )
            
            if not retrieved_docs:
                app_logger.warning("No relevant documents found for RAG query")
                return {
                    "success": False,
                    "response": "I couldn't find relevant information in my Formula 1 knowledge base for your question. Please try asking something else or check if the knowledge base has been initialized.",
                    "sources": [],
                    "method": "rag"
                }
            
            # Format context
            context = self._format_context(retrieved_docs)
            
            # Create chain and get response
            chain = LLMChain(llm=self.llm, prompt=self.rag_prompt)
            
            response = chain.run(
                context=context,
                question=question
            )
            
            # Prepare sources information
            sources = []
            for doc in retrieved_docs:
                metadata = doc.get("metadata", {})
                sources.append({
                    "title": metadata.get("title", "Unknown"),
                    "source": metadata.get("source", "Unknown"),
                    "category": metadata.get("category", "general"),
                    "score": doc.get("score", 0),
                    "excerpt": doc.get("content", "")[:200] + "..."
                })
            
            app_logger.success(f"RAG response generated using {len(retrieved_docs)} sources")
            
            return {
                "success": True,
                "response": response.strip(),
                "sources": sources,
                "method": "rag",
                "context_used": len(retrieved_docs)
            }
            
        except Exception as e:
            app_logger.error(f"Error generating RAG response: {e}")
            return {
                "success": False,
                "response": f"Sorry, I encountered an error while processing your question: {str(e)}",
                "sources": [],
                "method": "rag"
            }
    
    def get_direct_response(self, question: str) -> Dict:
        """Get response using direct LLM approach"""
        try:
            app_logger.info(f"Processing direct query: {question}")
            
            # Create chain and get response
            chain = LLMChain(llm=self.llm, prompt=self.direct_prompt)
            
            response = chain.run(question=question)
            
            app_logger.success("Direct response generated")
            
            return {
                "success": True,
                "response": response.strip(),
                "sources": [],
                "method": "direct"
            }
            
        except Exception as e:
            app_logger.error(f"Error generating direct response: {e}")
            return {
                "success": False,
                "response": f"Sorry, I encountered an error while processing your question: {str(e)}",
                "sources": [],
                "method": "direct"
            }
    
    def get_response(self, question: str, use_rag: bool = True) -> Dict:
        """Get response using either RAG or direct approach"""
        if use_rag:
            return self.get_rag_response(question)
        else:
            return self.get_direct_response(question)
    
    def check_system_status(self) -> Dict:
        """Check the status of all system components"""
        try:
            # Check vector store connection
            vector_store_status = self.vector_store.check_connection()
            
            # Check LLM by making a simple query
            try:
                test_response = self.llm.invoke("Test").content
                llm_status = {"connected": True}
            except Exception as e:
                llm_status = {"connected": False, "error": str(e)}
            
            # Get index statistics
            index_stats = self.vector_store.get_index_stats()
            
            return {
                "vector_store": vector_store_status,
                "llm": llm_status,
                "index_stats": index_stats,
                "config": {
                    "rag_enabled": True,
                    "embedding_model": config.EMBEDDING_MODEL,
                    "llm_model": config.LLM_MODEL,
                    "top_k_results": config.TOP_K_RESULTS,
                    "similarity_threshold": config.SIMILARITY_THRESHOLD
                }
            }
            
        except Exception as e:
            app_logger.error(f"Error checking system status: {e}")
            return {"error": str(e)}
    
    def refresh_knowledge_base(self, documents) -> Dict:
        """Refresh the vector store with new documents"""
        try:
            app_logger.info("Refreshing knowledge base...")
            result = self.vector_store.refresh_index(documents)
            
            if result["success"]:
                app_logger.success("Knowledge base refreshed successfully")
            else:
                app_logger.error(f"Failed to refresh knowledge base: {result.get('error')}")
            
            return result
            
        except Exception as e:
            app_logger.error(f"Error refreshing knowledge base: {e}")
            return {"success": False, "error": str(e)}