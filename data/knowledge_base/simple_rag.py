"""Simple RAG implementation without external embedding libraries"""

import os
import json
import logging
import hashlib
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
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

class SimpleRAG:
    """Simple RAG system for network troubleshooting without external embedding libraries"""
    
    def __init__(self):
        """Initialize RAG system"""
        self.documents = []
        self.cache = SimpleCache(ttl=3600)  # 1 hour TTL
        
        # Initialize with sample documents
        self._initialize_with_samples()
    
    def _initialize_with_samples(self):
        """Initialize with sample documents"""
        try:
            # Load from internet_down.md file
            kb_path = os.path.join(os.path.dirname(__file__), "internet_down.md")
            if os.path.exists(kb_path):
                logger.info(f"Loading knowledge base from {kb_path}")
                with open(kb_path, "r", encoding="utf-8") as f:
                    kb_data = json.load(f)
                
                # Extract scenarios from the knowledge base
                scenarios = kb_data.get("knowledge_base", {}).get("scenarios", [])
                
                self.documents = []
                for scenario in scenarios:
                    # Create document content
                    content_parts = [
                        f"Title (Malayalam): {scenario.get('title', {}).get('malayalam', '')}",
                        f"Title (English): {scenario.get('title', {}).get('english', '')}",
                        f"Urgency: {scenario.get('urgency', 'medium')}",
                        f"Category: {scenario.get('category', '')}"
                    ]
                    
                    # Add symptoms
                    symptoms_ml = scenario.get('symptoms', {}).get('malayalam', [])
                    symptoms_en = scenario.get('symptoms', {}).get('english', [])
                    
                    content_parts.append(f"Symptoms (Malayalam): {', '.join(symptoms_ml)}")
                    content_parts.append(f"Symptoms (English): {', '.join(symptoms_en)}")
                    content_parts.append("Solution Steps:")
                    
                    # Add solution steps
                    steps = scenario.get('solution', {}).get('steps', [])
                    for step in steps:
                        content_parts.append(f"{step.get('step', '')}. {step.get('malayalam', '')} / {step.get('english', '')}")
                    
                    # Create document
                    doc = Document(
                        id=scenario.get('id', f"DOC_{len(self.documents)}"),
                        content="\n".join(content_parts),
                        metadata={
                            "id": scenario.get('id', ''),
                            "urgency": scenario.get('urgency', 'medium'),
                            "category": scenario.get('category', ''),
                            "device_types": scenario.get('device_types', []),
                            "keywords": scenario.get('keywords', []),
                            "symptoms": {
                                "malayalam": symptoms_ml,
                                "english": symptoms_en
                            },
                            "success_indicators": scenario.get('success_indicators', []),
                            "resolution_time": scenario.get('resolution_time', '')
                        },
                        doc_type=DocumentType.SCENARIO
                    )
                    self.documents.append(doc)
                
                logger.info(f"Loaded {len(self.documents)} documents from knowledge base file")
                return
            else:
                logger.warning(f"Knowledge base file not found at {kb_path}, using sample documents")
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            logger.info("Falling back to sample documents")
        
        # Fallback to sample documents if loading fails
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
        
        self.documents = [doc1, doc2, doc3, doc4]
        logger.info(f"Initialized with {len(self.documents)} sample documents")
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization by splitting on whitespace and punctuation"""
        # Convert to lowercase and replace punctuation with spaces
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Split on whitespace and filter out empty tokens
        tokens = [token for token in text.split() if token]
        
        return tokens
    
    def _calculate_similarity(self, query_tokens: List[str], doc_tokens: List[str]) -> float:
        """Calculate simple token overlap similarity"""
        if not query_tokens or not doc_tokens:
            return 0.0
        
        # Count token occurrences
        query_counts = {}
        for token in query_tokens:
            query_counts[token] = query_counts.get(token, 0) + 1
        
        doc_counts = {}
        for token in doc_tokens:
            doc_counts[token] = doc_counts.get(token, 0) + 1
        
        # Calculate dot product
        dot_product = 0
        for token, count in query_counts.items():
            if token in doc_counts:
                dot_product += count * doc_counts[token]
        
        # Calculate magnitudes
        query_magnitude = math.sqrt(sum(count ** 2 for count in query_counts.values()))
        doc_magnitude = math.sqrt(sum(count ** 2 for count in doc_counts.values()))
        
        # Calculate cosine similarity
        if query_magnitude > 0 and doc_magnitude > 0:
            return dot_product / (query_magnitude * doc_magnitude)
        else:
            return 0.0
    
    def _search_keywords(self, query_tokens: List[str], document: Document) -> float:
        """Search for keywords in document metadata"""
        keywords = document.metadata.get("keywords", [])
        
        if not keywords:
            return 0.0
        
        # Count exact matches with higher weight
        exact_matches = 0
        partial_matches = 0
        
        # Join query tokens to check for multi-word matches
        query_text = " ".join(query_tokens).lower()
        
        # Check for keyword matches
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in query_text:
                exact_matches += 1.5  # Higher weight for exact keyword match
            else:
                # Check for token level matches
                for token in query_tokens:
                    if token == keyword_lower:
                        exact_matches += 1
                    elif token in keyword_lower or keyword_lower in token:
                        partial_matches += 0.5
        
        # Check for symptom matches (higher weight than keywords)
        symptoms = document.metadata.get("symptoms", {})
        symptoms_ml = symptoms.get("malayalam", [])
        symptoms_en = symptoms.get("english", [])
        
        # Look for symptom matches in the query
        for symptom in symptoms_ml + symptoms_en:
            symptom_lower = symptom.lower()
            if symptom_lower in query_text:
                exact_matches += 2.0  # Higher weight for symptom matches
                
        # Special case for red light in fiber modem
        if ("red light" in query_text or "റെഡ് ലൈറ്റ്" in query_text) and document.id == "NET_002":
            exact_matches += 3.0  # Significantly boost the fiber break issue for red light queries
        
        # Calculate score based on weighted matches
        if query_tokens:
            # Give 80% weight to exact matches, 20% to partial matches
            return (0.8 * exact_matches + 0.2 * partial_matches) / len(query_tokens)
        else:
            return 0.0
    
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
                for doc in self.documents:
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
            
            # Extract technical terms to enhance matching
            technical_terms = self._extract_technical_terms(enhanced_query)
            if technical_terms:
                enhanced_query = f"{enhanced_query} {' '.join(technical_terms)}"
                logger.info(f"Enhanced query with technical terms: {technical_terms}")
            
            # Tokenize query
            query_tokens = self._tokenize(enhanced_query)
            
            # Calculate scores for each document
            results = []
            for doc in self.documents:
                # Tokenize document content
                doc_tokens = self._tokenize(doc.content)
                
                # Calculate content similarity
                content_similarity = self._calculate_similarity(query_tokens, doc_tokens)
                
                # Calculate keyword similarity
                keyword_similarity = self._search_keywords(query_tokens, doc)
                
                # Combine scores (60% content, 40% keywords)
                score = 0.6 * content_similarity + 0.4 * keyword_similarity
                
                # Apply metadata filtering
                if customer_info and isinstance(customer_info, dict) and doc.metadata.get("device_types"):
                    # Safely get device type if it exists
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
                        "source": "keyword_search"
                    }
                )
                results.append(result)
            
            # Sort results by score
            results.sort(key=lambda x: x.score, reverse=True)
            
            # Take top-k results
            results = results[:top_k]
            
            # Cache results
            self.cache.set(cache_key, results)
            
            return results
        
        except Exception as e:
            logger.error(f"Error querying knowledge base: {e}")
            return []
    
    def _extract_technical_terms(self, text: str) -> list:
        """Extract technical terms from text to enhance RAG queries"""
        technical_terms = []
        
        # List of technical terms to look for
        term_mapping = {
            "റെഡ് ലൈറ്റ്": "red light",
            "പച്ച ലൈറ്റ്": "green light",
            "മഞ്ഞ ലൈറ്റ്": "yellow light",
            "സിഗ്നൽ": "signal",
            "മോഡം": "modem",
            "റൗട്ടർ": "router",
            "വൈഫൈ": "wifi",
            "ഇന്റർനെറ്റ്": "internet",
            "കണക്ഷൻ": "connection",
            "കേബിൾ": "cable",
            "ചാനൽ": "channel",
            "റീചാർജ്": "recharge",
            "സ്പീഡ്": "speed",
            "സ്ലോ": "slow",
            "ഫൈബർ": "fiber"
        }
        
        # Check for each term
        for term, english in term_mapping.items():
            if term in text:
                technical_terms.append(term)
                technical_terms.append(english)
                
        return technical_terms
    
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
                adapter_issue_msg = "മോഡത്തിൽ ലൈറ്റ് വരുന്നില്ലെങ്കിൽ അത് പവർ അഡാപ്റ്റർ പ്രശ്നമാകാൻ സാധ്യതയുണ്ട്. ദയവായി ഇനിപ്പറയുന്ന കാര്യങ്ങൾ പരിശോധിക്കുക:\n\n1. അഡാപ്റ്റർ പ്ലഗ് ശരിയായി കണക്റ്റ് ചെയ്തിട്ടുണ്ടോ എന്ന് പരിശോധിക്കുക\n2. വേറൊരു സോക്കറ്റിൽ അഡാപ്റ്റർ പ്ലഗ് ചെയ്ത് നോക്കുക\n3. അഡാപ്റ്റർ കേബിൾ വളഞ്ഞോ കേടായോ എന്ന് പരിശോധിക്കുക\n\nഇവയൊന്നും പ്രശ്നം പരിഹരിക്കുന്നില്ലെങ്കിൽ, അഡാപ്റ്റർ കേടായതാകാം. ഞങ്ങൾ നേരിട്ട് ടെക്നീഷ്യനെ അയക്കുന്നതാണ്, പുതിയ അഡാപ്റ്റർ കൊണ്ടുവരാൻ ടെക്നീഷ്യനോട് പറയുന്നതാണ്. / If there are no lights on the modem, it's likely a power adapter issue. Please check the following:\n\n1. Verify the adapter is properly plugged in\n2. Try plugging the adapter into a different socket\n3. Check if the adapter cable is bent or damaged\n\nIf none of these resolve the issue, the adapter may be faulty. We will send a technician directly with a replacement adapter."
                
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
            
            # Ensure customer_info is a dictionary
            if customer_info and not isinstance(customer_info, dict):
                logger.warning(f"customer_info is not a dictionary: {type(customer_info)}. Converting to empty dict.")
                customer_info = {}
            
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
                resolution_time = best_match.document.metadata.get("resolution_time", "")
                success_indicators = best_match.document.metadata.get("success_indicators", [])
                
                # Parse the document content to extract structured information
                content_lines = best_match.document.content.split('\n')
                
                # Initialize response components
                title_ml = ""
                title_en = ""
                symptoms_ml = []
                symptoms_en = []
                solution_steps = []
                
                # Extract components from content
                for line in content_lines:
                    if line.startswith("Title (Malayalam):"):
                        title_ml = line.replace("Title (Malayalam):", "").strip()
                    elif line.startswith("Title (English):"):
                        title_en = line.replace("Title (English):", "").strip()
                    elif line.startswith("Symptoms (Malayalam):"):
                        symptoms_text = line.replace("Symptoms (Malayalam):", "").strip()
                        symptoms_ml = [s.strip() for s in symptoms_text.split(',') if s.strip()]
                    elif line.startswith("Symptoms (English):"):
                        symptoms_text = line.replace("Symptoms (English):", "").strip()
                        symptoms_en = [s.strip() for s in symptoms_text.split(',') if s.strip()]
                    elif line.startswith("Solution Steps:"):
                        continue  # Skip the header
                    elif line and any(c.isdigit() for c in line[:2]):  # Solution step line
                        solution_steps.append(line)
                
                # Format a structured response in Malayalam
                response_parts = []
                
                # Add customer greeting if available
                if customer_info and isinstance(customer_info, dict) and customer_info.get("name"):
                    response_parts.append(f"നമസ്കാരം {customer_info['name']},")
                
                # Add title
                if title_ml:
                    response_parts.append(f"**{title_ml}**")
                
                # Add symptoms section
                if symptoms_ml:
                    response_parts.append("\nലക്ഷണങ്ങൾ:")
                    for symptom in symptoms_ml:
                        response_parts.append(f"- {symptom}")
                
                # Add solution steps
                if solution_steps:
                    response_parts.append("\nപരിഹാര നടപടികൾ:")
                    for step in solution_steps:
                        # Extract just the Malayalam part
                        parts = step.split('/')
                        if len(parts) > 0:
                            ml_step = parts[0].strip()
                            # Remove any step numbers if present
                            if '.' in ml_step[:3]:
                                ml_step = ml_step.split('.', 1)[1].strip()
                            response_parts.append(f"- {ml_step}")
                
                # Add resolution time information
                if resolution_time:
                    resolution_time_info = ""
                    if resolution_time == "immediate_or_technician":
                        resolution_time_info = "ഉടനടി പരിഹരിക്കാവുന്നതാണ്. അല്ലെങ്കിൽ ടെക്നീഷ്യൻ സന്ദർശനം ആവശ്യമാണ്."
                    elif resolution_time == "4-24_hours":
                        resolution_time_info = "പരിഹരിക്കാൻ 4-24 മണിക്കൂർ എടുക്കും."
                    elif resolution_time == "15-30_minutes_or_technician":
                        resolution_time_info = "15-30 മിനിറ്റിനുള്ളിൽ പരിഹരിക്കാവുന്നതാണ്. അല്ലെങ്കിൽ ടെക്നീഷ്യൻ സന്ദർശനം ആവശ്യമാണ്."
                    elif resolution_time == "technician_visit_required":
                        resolution_time_info = "ടെക്നീഷ്യൻ സന്ദർശനം ആവശ്യമാണ്."
                    
                    if resolution_time_info:
                        response_parts.append(f"\nപ്രതീക്ഷിത പരിഹാര സമയം: {resolution_time_info}")
                
                # Add success indicators
                if success_indicators:
                    response_parts.append("\nപരിഹാര സൂചകങ്ങൾ:")
                    for indicator in success_indicators[:2]:  # Show only first 2 indicators
                        response_parts.append(f"- {indicator}")
                
                # Add urgency note
                if urgency == "critical":
                    response_parts.append("\nഇത് ഒരു അടിയന്തിര പ്രശ്നമാണ്. ഉടൻ പരിഹരിക്കേണ്ടതാണ്.")
                elif urgency == "high":
                    response_parts.append("\nഇത് ഒരു ഗുരുതരമായ പ്രശ്നമാണ്. എത്രയും വേഗം പരിഹരിക്കേണ്ടതാണ്.")
                
                # Join all parts
                response = "\n".join(response_parts)
            else:
                response = best_match.document.content
            
            # Check if technician visit is needed
            if "technician_visit" in best_match.document.metadata.get("resolution_time", "") or \
               "ടെക്‌നീഷ്യൻ" in response or "technician" in response.lower():
                # Add standard technician visit timing information in Malayalam and English
                technician_info_ml = "\n\nടെക്‌നീഷ്യൻ വൈകുന്നേരത്തിനു മുമ്പോ അല്ലെങ്കിൽ നാളെ രാവിലെയോ എത്തിച്ചേരും. സ്കൈ വിഷൻ ഷോപ്പ് രാവിലെ 10 മണി മുതൽ വൈകുന്നേരം 5 മണി വരെ പ്രവർത്തിക്കുന്നു."
                technician_info_en = "\n\nThe technician will reach before evening or tomorrow morning. Please note that our Sky Vision shop works between 10 AM to 5 PM."
                
                response += technician_info_ml + "\n" + technician_info_en
                
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
            
            return {
                "response": response,
                "source_nodes": [r.document.to_dict() for r in results],
                "scores": [r.score for r in results],
                "metadata": {
                    "query_time": best_match.metadata.get("retrieval_time", 0),
                    "urgency": best_match.document.metadata.get("urgency", "medium"),
                    "category": best_match.document.metadata.get("category", ""),
                    "resolution_time": best_match.document.metadata.get("resolution_time", ""),
                    "context": {
                        "status": "resolved"
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

def get_simple_rag_engine() -> SimpleRAG:
    """Get RAG engine singleton instance"""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = SimpleRAG()
    
    return _rag_engine

def get_troubleshooting_response(query: str, customer_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get troubleshooting response for a query - simplified version for direct import"""
    try:
        engine = get_simple_rag_engine()
        
        # Ensure customer_info is a dictionary
        if customer_info and not isinstance(customer_info, dict):
            logger.warning(f"get_troubleshooting_response: customer_info is not a dictionary: {type(customer_info)}. Converting to empty dict.")
            customer_info = {}
            
        return engine.get_troubleshooting_response(query, customer_info=customer_info)
    except Exception as e:
        logger.error(f"Error in get_troubleshooting_response: {e}")
        return {
            "response": "Sorry, an error occurred while processing your request.",
            "error": str(e)
        } 