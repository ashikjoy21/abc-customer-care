"""RAG engine for network troubleshooting"""

import os
from pathlib import Path
from typing import Dict, List, Optional
import json
import logging
from .internet_down import get_kb

logger = logging.getLogger(__name__)

class NetworkTroubleshootingRAG:
    """RAG-based network troubleshooting system"""

    def __init__(self):
        self.kb = get_kb()
        self.persist_dir = Path(__file__).parent / "index"
        self._load_or_create_index()

    def _load_or_create_index(self):
        """Load existing index or create new one"""
        try:
            if os.path.exists(self.persist_dir):
                # Load existing index
                with open(self.persist_dir / "index.json", "r", encoding="utf-8") as f:
                    self.index = json.load(f)
            else:
                # Create new index
                self.index = self.kb.rag_documents
                os.makedirs(self.persist_dir, exist_ok=True)
                with open(self.persist_dir / "index.json", "w", encoding="utf-8") as f:
                    json.dump(self.index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error loading/creating index: {e}")
            self.index = self.kb.rag_documents

    def query(self, query_text: str, top_k: int = 3) -> List[Dict]:
        """Query the knowledge base"""
        try:
            results = self.kb.search_knowledge_base(query_text)
            return results[:top_k]
        except Exception as e:
            logger.error(f"Error querying knowledge base: {e}")
            return []

    def get_troubleshooting_response(self, query: str, chat_history: Optional[List[Dict]] = None) -> Dict:
        """Get troubleshooting response for a query"""
        try:
            # Search knowledge base
            results = self.query(query)
            
            if not results:
                return {
                    "response": self.kb.get_message("error_general"),
                    "source_nodes": []
                }
            
            # Get best matching scenario
            best_match = results[0]
            if best_match["type"] == "scenario":
                scenario = json.loads(best_match["content"])
                response = f"{scenario['issue']}\n\n{scenario.get('cause', '')}\n\n{scenario['solution']}"
            else:
                response = best_match["content"]
            
            return {
                "response": response,
                "source_nodes": results
            }
            
        except Exception as e:
            logger.error(f"Error getting troubleshooting response: {e}")
            return {
                "response": self.kb.get_message("error_general"),
                "source_nodes": []
            }

# Create singleton instance
_rag_engine = None

def get_rag_engine() -> NetworkTroubleshootingRAG:
    """Get RAG engine singleton instance"""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = NetworkTroubleshootingRAG()
    return _rag_engine 