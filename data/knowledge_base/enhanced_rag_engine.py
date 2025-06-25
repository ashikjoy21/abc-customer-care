"""Enhanced RAG engine for network troubleshooting with semantic search and multilingual support"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
import json
import time
import hashlib
from dataclasses import dataclass, field
from enum import Enum

import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

# Configure logging
logger = logging.getLogger(__name__)

class DocumentType(Enum):
    """Types of documents in the knowledge base"""
    SCENARIO = "scenario"
    MANUAL = "manual"
    FAQ = "faq"
    TICKET = "ticket"
    PROCEDURE = "procedure"

class UrgencyLevel(Enum):
    """Urgency levels for troubleshooting scenarios"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Document:
    """Document in the knowledge base"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None
    doc_type: DocumentType = DocumentType.SCENARIO
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary"""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "doc_type": self.doc_type.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """Create document from dictionary"""
        return cls(
            id=data["id"],
            content=data["content"],
            metadata=data["metadata"],
            doc_type=DocumentType(data["doc_type"])
        )

@dataclass
class QueryResult:
    """Result of a query to the knowledge base"""
    document: Document
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)

class EmbeddingModel:
    """Wrapper for embedding model"""
    
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        """Initialize embedding model"""
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.cache = {}  # Simple in-memory cache
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text with caching"""
        # Create cache key
        cache_key = hashlib.md5(text.encode()).hexdigest()
        
        # Check cache
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Generate embedding
        embedding = self.model.encode(text)
        
        # Cache embedding
        self.cache[cache_key] = embedding
        
        return embedding

class VectorStore:
    """Vector store for document embeddings"""
    
    def __init__(self, dimension: int, index_path: Optional[str] = None):
        """Initialize vector store"""
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)  # Inner product index
        self.documents: List[Document] = []
        self.index_path = index_path
        
        # Load index if exists
        if index_path and os.path.exists(index_path):
            self.load_index()
    
    def add_document(self, document: Document) -> None:
        """Add document to vector store"""
        if document.embedding is None:
            raise ValueError("Document must have embedding")
        
        # Add to index
        self.index.add(np.array([document.embedding]))
        self.documents.append(document)
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[Document, float]]:
        """Search for similar documents"""
        if len(self.documents) == 0:
            return []
        
        # Search index
        scores, indices = self.index.search(np.array([query_embedding]), top_k)
        
        # Get documents
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.documents) and idx >= 0:
                results.append((self.documents[idx], float(scores[0][i])))
        
        return results
    
    def save_index(self) -> None:
        """Save index to disk"""
        if not self.index_path:
            return
        
        # Create directory if not exists
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, f"{self.index_path}.faiss")
        
        # Save documents
        with open(f"{self.index_path}.json", "w", encoding="utf-8") as f:
            json.dump([doc.to_dict() for doc in self.documents], f, ensure_ascii=False, indent=2)
    
    def load_index(self) -> None:
        """Load index from disk"""
        if not self.index_path:
            return
        
        # Load FAISS index
        if os.path.exists(f"{self.index_path}.faiss"):
            self.index = faiss.read_index(f"{self.index_path}.faiss")
        
        # Load documents
        if os.path.exists(f"{self.index_path}.json"):
            with open(f"{self.index_path}.json", "r", encoding="utf-8") as f:
                self.documents = [Document.from_dict(doc) for doc in json.load(f)]

class SimpleCache:
    """Simple in-memory cache implementation"""
    
    def __init__(self, ttl: int = 3600):
        """Initialize cache with time-to-live in seconds"""
        self.cache = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self.cache:
            return None
        
        value, timestamp = self.cache[key]
        
        # Check if expired
        if time.time() - timestamp > self.ttl:
            del self.cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache"""
        self.cache[key] = (value, time.time())
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if key not in self.cache:
            return False
        
        # Check if expired
        _, timestamp = self.cache[key]
        if time.time() - timestamp > self.ttl:
            del self.cache[key]
            return False
        
        return True

class DocumentProcessor:
    """Process documents for the knowledge base"""
    
    def __init__(self, embedding_model: EmbeddingModel):
        """Initialize document processor"""
        self.embedding_model = embedding_model
    
    def process_json(self, json_path: str) -> List[Document]:
        """Process JSON document"""
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            documents = []
            
            # Process knowledge base
            if "knowledge_base" in data:
                kb = data["knowledge_base"]
                
                # Process scenarios
                if "scenarios" in kb:
                    for scenario in kb["scenarios"]:
                        # Create document for each scenario
                        doc_id = scenario.get("id", f"scenario_{len(documents)}")
                        
                        # Create content in both languages if available
                        content_parts = []
                        
                        # Add title
                        if "title" in scenario:
                            if "malayalam" in scenario["title"]:
                                content_parts.append(f"Title (Malayalam): {scenario['title']['malayalam']}")
                            if "english" in scenario["title"]:
                                content_parts.append(f"Title (English): {scenario['title']['english']}")
                        
                        # Add symptoms
                        if "symptoms" in scenario:
                            if "malayalam" in scenario["symptoms"]:
                                content_parts.append(f"Symptoms (Malayalam): {', '.join(scenario['symptoms']['malayalam'])}")
                            if "english" in scenario["symptoms"]:
                                content_parts.append(f"Symptoms (English): {', '.join(scenario['symptoms']['english'])}")
                        
                        # Add solution steps
                        if "solution" in scenario and "steps" in scenario["solution"]:
                            content_parts.append("Solution Steps:")
                            for step in scenario["solution"]["steps"]:
                                step_num = step.get("step", "")
                                step_ml = step.get("malayalam", "")
                                step_en = step.get("english", "")
                                content_parts.append(f"{step_num}. {step_ml} / {step_en}")
                        
                        # Join content
                        content = "\n".join(content_parts)
                        
                        # Create metadata
                        metadata = {
                            "id": doc_id,
                            "urgency": scenario.get("urgency", "medium"),
                            "category": scenario.get("category", "general"),
                            "device_types": scenario.get("device_types", []),
                            "keywords": scenario.get("keywords", []),
                            "success_indicators": scenario.get("success_indicators", []),
                            "resolution_time": scenario.get("resolution_time", "unknown")
                        }
                        
                        # Create document
                        doc = Document(
                            id=doc_id,
                            content=content,
                            metadata=metadata,
                            doc_type=DocumentType.SCENARIO
                        )
                        
                        # Add embedding
                        doc.embedding = self.embedding_model.get_embedding(content)
                        
                        documents.append(doc)
            
            return documents
        except Exception as e:
            logger.error(f"Error processing JSON document {json_path}: {e}")
            # Return an empty list if there's an error
            return []

    def create_sample_documents(self) -> List[Document]:
        """Create sample documents for testing"""
        documents = []
        
        # Sample document 1
        doc1 = Document(
            id="NET_001",
            content=(
                "Title (Malayalam): മോഡം പവർ പ്രശ്‌നം\n"
                "Title (English): Modem Power Issue\n"
                "Symptoms (Malayalam): മോഡത്തിൽ ലൈറ്റ് വരുന്നില്ല, മോഡം ഓൺ ആകുന്നില്ല, പവർ ഇല്ല\n"
                "Symptoms (English): no lights on modem, modem not turning on, no power\n"
                "Solution Steps:\n"
                "1. മോഡം പ്ലഗ് സ്വിച്ച് വഴി ഓഫ് ചെയ്ത് ഓൺ ചെയ്യുക / Power off and on the modem through the plug switch\n"
                "2. വൈദ്യുതി സപ്ലൈ പരിശോധിക്കുക / Check power supply\n"
                "3. മോഡം കംപ്ലൈന്റ് രജിസ്റ്റർ ചെയ്യുക / Register modem complaint"
            ),
            metadata={
                "id": "NET_001",
                "urgency": "high",
                "category": "hardware",
                "device_types": ["fiber_modem", "adsl_modem"],
                "keywords": ["modem", "power", "light", "adapter", "ലൈറ്റ്", "പവർ", "മോഡം", "അഡാപ്റ്റർ"],
                "success_indicators": ["മോഡം ലൈറ്റുകൾ തെളിയുന്നു", "പവർ സ്റ്റേബിൾ ആണ്"],
                "resolution_time": "immediate_or_technician"
            },
            doc_type=DocumentType.SCENARIO
        )
        
        # Sample document 2
        doc2 = Document(
            id="NET_002",
            content=(
                "Title (Malayalam): ഫൈബർ ബ്രേക്ക് പ്രശ്‌നം\n"
                "Title (English): Fiber Break Issue\n"
                "Symptoms (Malayalam): റെഡ് ലൈറ്റ് തെളിയുന്നു, ചുവന്ന ലൈറ്റ് കാണുന്നു, സിഗ്നൽ ഇല്ല\n"
                "Symptoms (English): red light showing, fiber signal lost, no connection\n"
                "Solution Steps:\n"
                "1. ഫൈബർ ബ്രേക്ക് കംപ്ലൈന്റ് രജിസ്റ്റർ ചെയ്യുക / Register fiber break complaint\n"
                "2. ടെക്‌നീഷ്യൻ വിസിറ്റ് ഷെഡ്യൂൾ ചെയ്യുക / Schedule technician visit"
            ),
            metadata={
                "id": "NET_002",
                "urgency": "critical",
                "category": "infrastructure",
                "device_types": ["fiber_modem"],
                "keywords": ["red light", "fiber", "break", "signal", "റെഡ് ലൈറ്റ്", "ഫൈബർ", "സിഗ്നൽ"],
                "success_indicators": ["റെഡ് ലൈറ്റ് ഓഫ് ആകുന്നു", "നോർമൽ കണക്റ്റിവിറ്റി പുനഃസ്ഥാപിക്കപ്പെടുന്നു"],
                "resolution_time": "4-24_hours"
            },
            doc_type=DocumentType.SCENARIO
        )
        
        # Sample document 3
        doc3 = Document(
            id="NET_004",
            content=(
                "Title (Malayalam): സ്ലോ ഇന്റർനെറ്റ് പ്രശ്‌നം\n"
                "Title (English): Slow Internet Issue\n"
                "Symptoms (Malayalam): നെറ്റ് സ്ലോ ആണ്, പേജ് കയറ്റിക്കൊണ്ടിരിക്കുന്നു, സ്പീഡ് കുറവാണ്\n"
                "Symptoms (English): internet is slow, pages loading slowly, low speed\n"
                "Solution Steps:\n"
                "1. മോഡം പ്ലഗ് സ്വിച്ച് വഴി ഓഫ് ചെയ്ത് ഓൺ ചെയ്യുക / Power off and on the modem through the plug switch\n"
                "2. കണക്റ്റ് ചെയ്ത ഡിവൈസുകളുടെ എണ്ണം പരിശോധിക്കുക / Check number of connected devices\n"
                "3. വയർഡ് കണക്ഷൻ ടെസ്റ്റ് ചെയ്യുക / Test wired connection"
            ),
            metadata={
                "id": "NET_004",
                "urgency": "medium",
                "category": "performance",
                "device_types": ["fiber_modem", "wifi_router"],
                "keywords": ["slow", "speed", "performance", "loading", "സ്ലോ", "സ്പീഡ്", "പേജ്"],
                "success_indicators": ["നോർമൽ സ്പീഡ് ലഭിക്കുന്നു", "പേജുകൾ വേഗത്തിൽ ലോഡ് ആകുന്നു"],
                "resolution_time": "15-30_minutes_or_technician"
            },
            doc_type=DocumentType.SCENARIO
        )
        
        # Sample document 4 - Normal lights but no internet
        doc4 = Document(
            id="NET_006",
            content=(
                "Title (Malayalam): മോഡം ലൈറ്റ് ശരിയാണെങ്കിലും ഇന്റർനെറ്റ് കിട്ടുന്നില്ല\n"
                "Title (English): No Internet Despite Normal Modem Lights\n"
                "Symptoms (Malayalam): മോഡത്തിൽ ലൈറ്റ് ശരിയാണ്, ബ്ലൂ/ഗ്രീൻ ലൈറ്റ് കാണുന്നു, എന്നാൽ ഇന്റർനെറ്റ് കിട്ടുന്നില്ല\n"
                "Symptoms (English): modem lights are normal, blue/green lights showing, but no internet\n"
                "Solution Steps:\n"
                "1. മോഡം പ്ലഗ് സ്വിച്ച് വഴി ഓഫ് ചെയ്ത് ഓൺ ചെയ്യുക / Power off and on the modem through the plug switch\n"
                "2. ഫോണിലെ WiFi ലിസ്റ്റിൽ നിങ്ങളുടെ സാധാരണ WiFi പേര് പരിശോധിക്കുക / Check if your usual WiFi name appears in your phone's WiFi list"
            ),
            metadata={
                "id": "NET_006",
                "urgency": "medium",
                "category": "configuration",
                "device_types": ["fiber_modem", "wifi_router"],
                "keywords": ["normal lights", "blue light", "green light", "no internet", "ലൈറ്റ് ശരിയാണ്", "ബ്ലൂ ലൈറ്റ്", "ഗ്രീൻ ലൈറ്റ്", "ഇന്റർനെറ്റ് ഇല്ല"],
                "success_indicators": ["ഇന്റർനെറ്റ് കണക്ഷൻ പുനഃസ്ഥാപിക്കപ്പെടുന്നു"],
                "resolution_time": "technician_visit_required"
            },
            doc_type=DocumentType.SCENARIO
        )
        
        # Add embeddings to sample documents
        for doc in [doc1, doc2, doc3, doc4]:
            doc.embedding = self.embedding_model.get_embedding(doc.content)
            documents.append(doc)
        
        return documents

class EnhancedRAG:
    """Enhanced RAG system for network troubleshooting"""
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        index_path: Optional[str] = None
    ):
        """Initialize RAG system"""
        self.embedding_model = EmbeddingModel(model_name)
        self.vector_store = VectorStore(
            dimension=self.embedding_model.dimension,
            index_path=index_path
        )
        self.document_processor = DocumentProcessor(self.embedding_model)
        
        # Set up simple cache
        self.cache = SimpleCache(ttl=3600)  # 1 hour TTL
        
        # Initialize with sample documents if no index exists
        if index_path and not os.path.exists(f"{index_path}.faiss"):
            logger.info("No existing index found. Creating sample documents.")
            self._initialize_with_samples()
    
    def _initialize_with_samples(self):
        """Initialize with sample documents"""
        sample_docs = self.document_processor.create_sample_documents()
        for doc in sample_docs:
            self.vector_store.add_document(doc)
        
        logger.info(f"Added {len(sample_docs)} sample documents to the vector store.")
        
        # Save the index
        self.save()
    
    def add_knowledge_source(self, source_path: str) -> None:
        """Add knowledge source to the system"""
        try:
            # Process based on file type
            if source_path.endswith(".json") or source_path.endswith(".md"):
                documents = self.document_processor.process_json(source_path)
                
                # Add documents to vector store
                for doc in documents:
                    self.vector_store.add_document(doc)
                
                logger.info(f"Added {len(documents)} documents from {source_path}")
            else:
                logger.warning(f"Unsupported file type: {source_path}")
        except Exception as e:
            logger.error(f"Error adding knowledge source {source_path}: {e}")
    
    def save(self) -> None:
        """Save the RAG system state"""
        self.vector_store.save_index()
    
    def query(
        self,
        query_text: str,
        top_k: int = 5,
        customer_info: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> List[QueryResult]:
        """Query the knowledge base"""
        start_time = time.time()
        
        try:
            # Check cache
            cache_key = f"query:{hashlib.md5(query_text.encode()).hexdigest()}"
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.info("Using cached query result")
                return cached_result
            
            # Enhance query with conversation history if available
            enhanced_query = query_text
            if conversation_history:
                # Add last user message for context
                last_messages = [msg["user"] for msg in conversation_history[-3:] if "user" in msg]
                if last_messages:
                    enhanced_query = f"{query_text} {' '.join(last_messages)}"
            
            # Check if query mentions lights are on but doesn't specify color
            if (("lights are on" in query_text.lower() or "light is on" in query_text.lower() or 
                "ലൈറ്റ് കത്തുന്നു" in query_text or "ലൈറ്റ് ഓൺ ആണ്" in query_text) and
                not any(color in query_text.lower() for color in ["red", "green", "blue", "ചുവപ്പ്", "പച്ച", "നീല", "los"])):
                # Prioritize NET_006 scenario for this case
                for doc in self.vector_store.documents:
                    if doc.id == "NET_006":
                        # Create a high-scoring result
                        result = QueryResult(
                            document=doc,
                            score=0.95,  # High score to ensure it's the top result
                            metadata={
                                "retrieval_time": time.time() - start_time,
                                "source": "light_status_query"
                            }
                        )
                        return [result]
            
            # Get query embedding
            query_embedding = self.embedding_model.get_embedding(enhanced_query)
            
            # Search vector store
            vector_results = self.vector_store.search(query_embedding, top_k=top_k)
            
            # Create results
            results = []
            for doc, score in vector_results:
                # Apply metadata filtering
                if customer_info and doc.metadata.get("device_types"):
                    # Filter by device type if customer has device info
                    customer_device = customer_info.get("device_type")
                    if customer_device and customer_device not in doc.metadata["device_types"]:
                        # Reduce score for non-matching devices
                        score *= 0.8
                
                # Create result
                result = QueryResult(
                    document=doc,
                    score=score,
                    metadata={
                        "retrieval_time": time.time() - start_time,
                        "source": "vector_search"
                    }
                )
                results.append(result)
            
            # Cache results
            self.cache.set(cache_key, results)
            
            return results
        
        except Exception as e:
            logger.error(f"Error querying knowledge base: {e}")
            return []
    
    def get_troubleshooting_response(
        self,
        query: str,
        customer_info: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Get troubleshooting response for a query"""
        try:
            # Check for no light/power issues - likely adapter problem
            if any(term in query.lower() for term in ["no light", "no power", "ലൈറ്റ് ഇല്ല", "ലൈറ്റ് വരുന്നില്ല", "പവർ ഇല്ല", 
                                                     "ഓൺ ആകുന്നില്ല", "not turning on", "won't turn on", "dead"]):
                # Immediately handle as adapter/power supply issue
                adapter_issue_msg = "മോഡത്തിൽ ലൈറ്റ് വരുന്നില്ലെങ്കിൽ അത് പവർ അഡാപ്റ്റർ പ്രശ്നമാകാൻ സാധ്യതയുണ്ട്. ദയവായി ഇനിപ്പറയുന്ന കാര്യങ്ങൾ പരിശോധിക്കുക:\n\n1. അഡാപ്റ്റർ പ്ലഗ് ശരിയായി കണക്റ്റ് ചെയ്തിട്ടുണ്ടോ എന്ന് പരിശോധിക്കുക\n2. വേറൊരു സോക്കറ്റിൽ അഡാപ്റ്റർ പ്ലഗ് ചെയ്ത് നോക്കുക\n3. അഡാപ്റ്റർ കേബിൾ വളഞ്ഞോ കേടായോ എന്ന് പരിശോധിക്കുക\n\nഇവ പരിശോധിച്ച ശേഷം, മോഡം പ്ലഗ് സ്വിച്ച് വഴി ഓഫ് ചെയ്ത് ഓൺ ചെയ്യുക (മോഡത്തിലെ റീസ്റ്റാർട്ട് ബട്ടൺ അമർത്തരുത്). ഇവയൊന്നും പ്രശ്നം പരിഹരിക്കുന്നില്ലെങ്കിൽ, അഡാപ്റ്റർ കേടായതാകാം. ഞങ്ങൾ നേരിട്ട് ടെക്നീഷ്യനെ അയക്കുന്നതാണ്, പുതിയ അഡാപ്റ്റർ കൊണ്ടുവരാൻ ടെക്നീഷ്യനോട് പറയുന്നതാണ്. / If there are no lights on the modem, it's likely a power adapter issue. Please check the following:\n\n1. Verify the adapter is properly plugged in\n2. Try plugging the adapter into a different socket\n3. Check if the adapter cable is bent or damaged\n\nAfter checking these, turn off and on the modem through the plug socket switch (DO NOT press the restart button on the modem). If none of these resolve the issue, the adapter may be faulty. We will send a technician directly with a replacement adapter."
                
                # Return direct response without querying the knowledge base
                return {
                    "response": adapter_issue_msg,
                    "source_nodes": [],
                    "metadata": {
                        "is_power_issue": True,
                        "needs_technician": True,
                        "urgent": True,
                        "adapter_problem": True,
                        "context": {
                            "status": "adapter_issue_detected"
                        }
                    }
                }
                
            # Check for red light indicator in query - DIRECT FIBER CUT DETECTION
            if ("red light" in query.lower() or "ചുവന്ന ലൈറ്റ്" in query or "റെഡ് ലൈറ്റ്" in query or 
                "los" in query.lower() or "loss" in query.lower() or "los light" in query.lower() or
                "red" in query.lower() or "ചുവന്ന" in query or "ചുവപ്പ്" in query):
                # Immediately handle as fiber cut without asking about WiFi name or other troubleshooting
                fiber_cut_msg = "ചുവന്ന ലൈറ്റ് കാണുന്നത് ഫൈബർ കട്ട് പ്രശ്നം സൂചിപ്പിക്കുന്നു. ആദ്യം മോഡം പവർ ഓഫ് ചെയ്യുക (പ്ലഗ് സ്വിച്ച് വഴി ഓഫ് ചെയ്ത് ഓൺ ചെയ്യുക, മോഡത്തിലെ റീസ്റ്റാർട്ട് ബട്ടൺ അമർത്തരുത്). മോഡം പൂർണ്ണമായും ഓൺലൈൻ ആകാൻ 5 മിനിറ്റ് എടുക്കും. ദയവായി 5 മിനിറ്റ് കാത്തിരിക്കുക. 5 മിനിറ്റിനു ശേഷവും പ്രശ്നം നിലനിൽക്കുന്നുവെങ്കിൽ മാത്രം ഞങ്ങളെ വീണ്ടും വിളിക്കുക. ഞങ്ങൾ നേരിട്ട് ടെക്നീഷ്യനെ അയക്കുന്നതാണ്, ടെക്നീഷ്യൻ നിങ്ങളെ വിളിക്കേണ്ട ആവശ്യമില്ല. / Red light indicates a fiber cut issue. First turn off the modem (power off and on through the plug socket switch, DO NOT press the restart button on the modem). The modem takes about 5 minutes to be fully online. Please wait for 5 minutes. ONLY call us back if the issue persists after 5 minutes. We will directly send a technician to fix the fiber cut, the technician does not need to call you first."
                
                # Return direct response without querying the knowledge base
                return {
                    "response": fiber_cut_msg,
                    "source_nodes": [],
                    "metadata": {
                        "is_red_light": True,
                        "needs_technician": True,
                        "urgent": True,
                        "restart_first": True,
                        "skip_further_troubleshooting": True,
                        "context": {
                            "status": "fiber_cut_detected"
                        }
                    }
                }
            
            # Query knowledge base
            results = self.query(query, customer_info=customer_info, conversation_history=conversation_history)
            
            if not results:
                return {
                    "response": "Sorry, I couldn't find any relevant information.",
                    "source_nodes": []
                }
            
            # Get best matching scenario
            best_match = results[0]
            
            # Format response based on document type
            if best_match.document.doc_type == DocumentType.SCENARIO:
                # Extract scenario details
                scenario_id = best_match.document.metadata.get("id", "unknown")
                urgency = best_match.document.metadata.get("urgency", "medium")
                
                # Format response
                response = best_match.document.content
                
                # Check if technician visit is needed
                if "technician_visit" in response.lower() or "ടെക്‌നീഷ്യൻ" in response:
                    # Add standard technician visit timing information
                    technician_info = "\n\nThe technician will reach before evening or tomorrow morning. Please note that our Sky Vision shop works between 10 AM to 5 PM."
                    response += technician_info
                    
                    # Remove any text asking for preferred time
                    response = response.replace("What time would be convenient for you?", "")
                    response = response.replace("When would you prefer the technician to visit?", "")
                    response = response.replace("What time works best for you?", "")
                    response = response.replace("നിങ്ങൾക്ക് ഏത് സമയം അനുയോജ്യമാണ്?", "")
                    response = response.replace("ടെക്നീഷ്യൻ എപ്പോൾ വരണമെന്ന് നിങ്ങൾക്ക് ഇഷ്ടമാണ്?", "")
                
                # Remove any password-related questions
                response = response.replace("പാസ്‌വേഡ് വർക്ക് ആകുന്നില്ല", "")
                response = response.replace("password not working", "")
                
                # If query mentions restarting modem, emphasize 5-minute wait time
                if "restart" in query.lower() or "reboot" in query.lower() or "power off" in query.lower() or "turn off" in query.lower() or "റീസ്റ്റാർട്ട്" in query or "റീബൂട്ട്" in query:
                    wait_time_reminder = "\n\nമോഡം പൂർണ്ണമായും ഓൺലൈൻ ആകാൻ 5 മിനിറ്റ് എടുക്കും. ദയവായി 5 മിനിറ്റ് കാത്തിരിക്കുക. 5 മിനിറ്റിനു ശേഷവും പ്രശ്നം നിലനിൽക്കുന്നുവെങ്കിൽ മാത്രം, ഞങ്ങളെ വീണ്ടും വിളിക്കുക. / The modem takes about 5 minutes to be fully online. Please wait for 5 minutes. ONLY call us back if the issue persists after 5 minutes."
                    response += wait_time_reminder
                
                # If query mentions WiFi name is visible but cannot connect
                if ("cannot connect" in query.lower() or "can't connect" in query.lower() or 
                    "not connecting" in query.lower() or "കണക്റ്റ് ആവുന്നില്ല" in query or 
                    "കണക്റ്റ് ആകുന്നില്ല" in query) and ("name" in query.lower() or "പേര്" in query):
                    # Add specific response for this case
                    technician_visit_msg = "\n\nWiFi പേര് കാണുന്നുണ്ടെങ്കിലും കണക്റ്റ് ആകുന്നില്ലെങ്കിൽ ടെക്നീഷ്യനെ അയക്കേണ്ടതാണ്. / If WiFi name is visible but cannot connect, a technician needs to visit."
                    response += technician_visit_msg
                
                # Add customer-specific information if available
                if customer_info:
                    customer_name = customer_info.get("name", "")
                    if customer_name:
                        response = f"Hello {customer_name}, here's the solution for your issue:\n\n{response}"
            else:
                response = best_match.document.content
            
            return {
                "response": response,
                "source_nodes": [r.document.to_dict() for r in results],
                "scores": [r.score for r in results],
                "metadata": {
                    "query_time": best_match.metadata.get("retrieval_time", 0),
                    "context": {
                        "status": "pending"
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting troubleshooting response: {e}")
            return {
                "response": "Sorry, an error occurred while processing your request.",
                "source_nodes": [],
                "error": str(e)
            }

# Create singleton instance
_rag_engine = None

def get_enhanced_rag_engine() -> EnhancedRAG:
    """Get RAG engine singleton instance"""
    global _rag_engine
    if _rag_engine is None:
        # Initialize with default settings
        index_path = os.path.join(os.path.dirname(__file__), "storage", "enhanced_index")
        _rag_engine = EnhancedRAG(index_path=index_path)
        
        # Try to load knowledge base file if it exists
        kb_path = os.path.join(os.path.dirname(__file__), "internet_down.md")
        if os.path.exists(kb_path):
            try:
                _rag_engine.add_knowledge_source(kb_path)
            except Exception as e:
                logger.error(f"Error loading knowledge base: {e}")
                # Continue with sample documents
    
    return _rag_engine 