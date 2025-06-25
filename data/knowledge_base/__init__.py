"""Knowledge base module for ABC Angamaly"""

# Import the simple RAG engine instead of the enhanced one that has dependency issues
from .simple_rag import get_simple_rag_engine, get_troubleshooting_response

__all__ = ["get_simple_rag_engine", "get_troubleshooting_response"] 