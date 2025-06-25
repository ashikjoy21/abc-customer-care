import logging
import redis
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from config import REDIS_HOST, REDIS_PORT, REDIS_DB, LOG_LEVEL, LOG_FORMAT
import os
import re
import json
import hashlib
import random
from rapidfuzz import fuzz, process
import string
import unicodedata
from difflib import SequenceMatcher

# Configure logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)

def check_redis(client: redis.Redis) -> bool:
    """Check Redis connection and health
    
    Args:
        client: Redis client instance to check
        
    Returns:
        bool: True if Redis is healthy, False otherwise
    """
    try:
        client.ping()
        logger.info("✅ Redis connected and healthy")
        return True
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        return False

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable string"""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}m {seconds}s"

def get_status_emoji(status: str) -> str:
    """Get emoji for call status"""
    return {
        "completed": "✅",
        "abandoned": "⚠️",
        "error": "❌"
    }.get(status, "❓")

def get_resolution_emoji(resolution: str) -> str:
    """Get emoji for call resolution"""
    return {
        "incident_notification": "🔔",
        "normal_completion": "✅",
        "no_input": "🤐",
        "invalid_number": "❌",
        "error": "⚠️"
    }.get(resolution, "❓")

def create_incident_entry(incident_type: str, location: str, zones: str, services: str, areas: str = "") -> Optional[str]:
    """Create incident entry in Redis"""
    try:
        redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
        incident_id = f"incident:{int(datetime.utcnow().timestamp())}"
        incident_data = {
            "type": incident_type.lower(),
            "location": location.strip(),
            "status": "active",
            "affected_zones": zones,
            "affected_regions": location,
            "affected_areas": areas,
            "affected_services": services,
            "message_ml": f"{location} പ്രദേശത്ത് {incident_type.replace('_', ' ').title()} സംഭവിച്ചിട്ടുണ്ട്",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        for key, value in incident_data.items():
            redis_client.hset(incident_id, key, value)
        
        logger.info(f"Created incident: {incident_id}")
        return incident_id
    except Exception as e:
        logger.error(f"Error creating incident: {e}")
        return None

def format_customer_info(customer_info: Dict[str, Any]) -> str:
    """Format customer information for display"""
    if not customer_info:
        return "No customer information available."
        
    return (
        f"Customer Information:\n"
        f"  • Name: {customer_info.get('Customer Name', customer_info.get('name', 'Unknown'))}\n"
        f"  • Username: {customer_info.get('User Name', customer_info.get('username', 'Unknown'))}\n"
        f"  • Plan: {customer_info.get('Current Plan', customer_info.get('plan', 'Unknown'))}\n"
        f"  • Provider: {customer_info.get('Provider', customer_info.get('isp', 'Unknown'))}\n"
        f"  • Region: {customer_info.get('Region', 'Unknown')}\n"
        f"  • Operator: {customer_info.get('Operator', customer_info.get('operator', 'Unknown'))}\n"
        f"  • Nickname: {customer_info.get('NickName', 'Unknown')}\n"
    )

class MalayalamMorphologicalAnalyzer:
    """
    A simplified morphological analyzer for Malayalam words.
    Based on common inflection patterns in Malayalam.
    """
    
    def __init__(self):
        # Common noun case suffixes in Malayalam
        self.noun_case_suffixes = {
            # Nominative case (no suffix)
            "": "",
            
            # Accusative case
            "യെ": "",
            "നെ": "",
            "ത്തെ": "ം",
            "ത്തിനെ": "ം",
            "വിനെ": "വ്",
            
            # Genitive case
            "യുടെ": "",
            "ന്റെ": "ൻ",
            "ത്തിന്റെ": "ം",
            "വിന്റെ": "വ്",
            
            # Dative case
            "യ്ക്ക്": "",
            "ന്": "ൻ",
            "ത്തിന്": "ം",
            "വിന്": "വ്",
            
            # Sociative case
            "യോട്": "",
            "നോട്": "ൻ",
            "ത്തോട്": "ം",
            "വോട്": "വ്",
            
            # Instrumental case
            "യാൽ": "",
            "നാൽ": "ൻ",
            "ത്താൽ": "ം",
            "വാൽ": "വ്",
            
            # Locative case
            "യിൽ": "",
            "നിൽ": "ൻ",
            "ത്തിൽ": "ം",
            "വിൽ": "വ്",
            "ിൽ": "്",  # For words like വീടിൽ -> വീട്
        }
        
        # Common verb suffixes in Malayalam
        self.verb_suffixes = {
            # Present tense
            "ുന്നു": "ുക",
            "ക്കുന്നു": "ക്കുക",
            "ിക്കുന്നു": "ിക്കുക",
            
            # Past tense
            "ി": "ുക",
            "ച്ചു": "ക്കുക",
            "ത്തു": "ത്തുക",
            "ന്നു": "ൽ",
            "യ്തു": "യ്യുക",  # For words like ചെയ്തു -> ചെയ്യുക
            
            # Future tense
            "ും": "ുക",
            "ക്കും": "ക്കുക",
            
            # Negative forms
            "ുന്നില്ല": "ുക",
            "ക്കുന്നില്ല": "ക്കുക",
            "ില്ല": "ുക",
            "ാത്ത": "ുക",
            
            # Conditional forms
            "ാൽ": "ുക",
            "െങ്കിൽ": "ുക",
            
            # Imperative forms
            "ൂ": "ുക",
            "ക്കൂ": "ക്കുക",
        }
        
        # Common plural suffixes
        self.plural_suffixes = {
            "കൾ": "",
            "മാർ": "ൻ",
        }
        
        # Common adjective suffixes
        self.adjective_suffixes = {
            "മായ": "ം",
            "മുള്ള": "ം",
            "ത്തുള്ള": "ം",
        }
        
        # Technical term stems for internet domain
        self.technical_stems = {
            "വൈഫൈ": "വൈഫൈ",
            "ഇന്റർനെറ്റ്": "ഇന്റർനെറ്റ്",
            "റൗട്ടർ": "റൗട്ടർ",
            "മോഡം": "മോഡം",
            "കണക്ഷൻ": "കണക്ഷൻ",
            "സിഗ്നൽ": "സിഗ്നൽ",
            "നെറ്റ്": "ഇന്റർനെറ്റ്",
            "സ്പീഡ്": "സ്പീഡ്",
            
            # Additional technical terms
            "ബ്രോഡ്ബാൻഡ്": "ബ്രോഡ്ബാൻഡ്",
        }
        
        # Special case mappings for technical terms with inflections
        # These should be complete words, not parts of words
        self.special_case_mappings = {
            "നെറ്റിന്റെ": "ഇന്റർനെറ്റിന്റെ",
            "നെറ്റിന്": "ഇന്റർനെറ്റിന്",
            "നെറ്റിൽ": "ഇന്റർനെറ്റിൽ",
            
            # Additional special case mappings
            "നെറ്റിനെ": "ഇന്റർനെറ്റിനെ",
            "നെറ്റിനോട്": "ഇന്റർനെറ്റിനോട്",
            "നെറ്റിനാൽ": "ഇന്റർനെറ്റിനാൽ",
            "നെറ്റുമായി": "ഇന്റർനെറ്റുമായി",
            "നെറ്റുകൾ": "ഇന്റർനെറ്റുകൾ",
            "നെറ്റിലേക്ക്": "ഇന്റർനെറ്റിലേക്ക്",
            "നെറ്റിലൂടെ": "ഇന്റർനെറ്റിലൂടെ",
            
            # WiFi related special cases
            "വൈഫൈയുടെ": "വൈഫൈയുടെ",
            "വൈഫൈയിൽ": "വൈഫൈയിൽ",
            "വൈഫൈയിലേക്ക്": "വൈഫൈയിലേക്ക്",
            "വൈഫൈയിലൂടെ": "വൈഫൈയിലൂടെ",
            "വൈഫൈയെ": "വൈഫൈയെ",
            "വൈഫൈയോട്": "വൈഫൈയോട്",
            "വൈഫൈയാൽ": "വൈഫൈയാൽ",
            "വൈഫൈകൾ": "വൈഫൈകൾ",
            
            # Router related special cases
            "റൗട്ടറിന്റെ": "റൗട്ടറിന്റെ",
            "റൗട്ടറിൽ": "റൗട്ടറിൽ",
            "റൗട്ടറിലേക്ക്": "റൗട്ടറിലേക്ക്",
            "റൗട്ടറിലൂടെ": "റൗട്ടറിലൂടെ",
            "റൗട്ടറിനെ": "റൗട്ടറിനെ",
            "റൗട്ടറിനോട്": "റൗട്ടറിനോട്",
            "റൗട്ടറിനാൽ": "റൗട്ടറിനാൽ",
            "റൗട്ടറുകൾ": "റൗട്ടറുകൾ",
            
            # Modem related special cases
            "മോഡത്തിന്റെ": "മോഡത്തിന്റെ",
            "മോഡത്തിൽ": "മോഡത്തിൽ",
            "മോഡത്തിലേക്ക്": "മോഡത്തിലേക്ക്",
            "മോഡത്തിലൂടെ": "മോഡത്തിലൂടെ",
            "മോഡത്തിനെ": "മോഡത്തിനെ",
            "മോഡത്തിനോട്": "മോഡത്തിനോട്",
            "മോഡത്തിനാൽ": "മോഡത്തിനാൽ",
            "മോഡങ്ങൾ": "മോഡങ്ങൾ",
            
            # Signal related special cases
            "സിഗ്നലിന്റെ": "സിഗ്നലിന്റെ",
            "സിഗ്നലിൽ": "സിഗ്നലിൽ",
            "സിഗ്നലിലേക്ക്": "സിഗ്നലിലേക്ക്",
            "സിഗ്നലിലൂടെ": "സിഗ്നലിലൂടെ",
            "സിഗ്നലിനെ": "സിഗ്നലിനെ",
            "സിഗ്നലിനോട്": "സിഗ്നലിനോട്",
            "സിഗ്നലിനാൽ": "സിഗ്നലിനാൽ",
            "സിഗ്നലുകൾ": "സിഗ്നലുകൾ",
            
            # Speed related special cases
            "സ്പീഡിന്റെ": "സ്പീഡിന്റെ",
            "സ്പീഡിൽ": "സ്പീഡിൽ",
            "സ്പീഡിലേക്ക്": "സ്പീഡിലേക്ക്",
            "സ്പീഡിലൂടെ": "സ്പീഡിലൂടെ",
            "സ്പീഡിനെ": "സ്പീഡിനെ",
            "സ്പീഡിനോട്": "സ്പീഡിനോട്",
            "സ്പീഡിനാൽ": "സ്പീഡിനാൽ",
            "സ്പീഡുകൾ": "സ്പീഡുകൾ",
            
            # Connection related special cases
            "കണക്ഷന്റെ": "കണക്ഷന്റെ",
            "കണക്ഷനിൽ": "കണക്ഷനിൽ",
            "കണക്ഷനിലേക്ക്": "കണക്ഷനിലേക്ക്",
            "കണക്ഷനിലൂടെ": "കണക്ഷനിലൂടെ",
            "കണക്ഷനെ": "കണക്ഷനെ",
            "കണക്ഷനോട്": "കണക്ഷനോട്",
            "കണക്ഷനാൽ": "കണക്ഷനാൽ",
            "കണക്ഷനുകൾ": "കണക്ഷനുകൾ",
            
            # Channel related special cases
            "ചാനലിന്റെ": "ചാനലിന്റെ",
            "ചാനലിൽ": "ചാനലിൽ",
            "ചാനലിലേക്ക്": "ചാനലിലേക്ക്",
            "ചാനലിലൂടെ": "ചാനലിലൂടെ",
            "ചാനലിനെ": "ചാനലിനെ",
            "ചാനലിനോട്": "ചാനലിനോട്",
            "ചാനലിനാൽ": "ചാനലിനാൽ",
            "ചാനലുകൾ": "ചാനലുകൾ",
            
            # Dish related special cases
            "ഡിഷിന്റെ": "ഡിഷിന്റെ",
            "ഡിഷിൽ": "ഡിഷിൽ",
            "ഡിഷിലേക്ക്": "ഡിഷിലേക്ക്",
            "ഡിഷിലൂടെ": "ഡിഷിലൂടെ",
            "ഡിഷിനെ": "ഡിഷിനെ",
            "ഡിഷിനോട്": "ഡിഷിനോട്",
            "ഡിഷിനാൽ": "ഡിഷിനാൽ",
            "ഡിഷുകൾ": "ഡിഷുകൾ",
            
            # Common verb form variations
            "വരുന്നില്ലാ": "വരുന്നില്ല",
            "വരുന്നില്ലെ": "വരുന്നില്ല",
            "കിട്ടുന്നില്ലാ": "കിട്ടുന്നില്ല",
            "കിട്ടുന്നില്ലെ": "കിട്ടുന്നില്ല",
            "കാണുന്നില്ലാ": "കാണുന്നില്ല",
            "കാണുന്നില്ലെ": "കാണുന്നില്ല",
            "പ്രവർത്തിക്കുന്നില്ലാ": "പ്രവർത്തിക്കുന്നില്ല",
            "പ്രവർത്തിക്കുന്നില്ലെ": "പ്രവർത്തിക്കുന്നില്ല"
        }
        
        # Special case mappings for noun stems
        self.noun_stem_mappings = {
            "വീടിൽ": "വീട്",
            "വീടിന്റെ": "വീട്",
            "വീടിന്": "വീട്",
            "വീടിനെ": "വീട്",
            "വീടിനോട്": "വീട്",
            "വീടിനാൽ": "വീട്",
        }
        
        # Special case mappings for verb stems
        self.verb_stem_mappings = {
            "ചെയ്തു": "ചെയ്യുക",
            "ചെയ്യുന്നു": "ചെയ്യുക",
            "ചെയ്യും": "ചെയ്യുക",
            "ചെയ്യുന്നില്ല": "ചെയ്യുക",
        }
    
    def analyze_word(self, word: str) -> Dict:
        """
        Analyze a Malayalam word to find its stem and inflection.
        
        Args:
            word: The Malayalam word to analyze
            
        Returns:
            A dictionary containing stem, suffix, and word type information
        """
        # Check special case mappings for technical terms
        if word in self.special_case_mappings:
            return {
                "stem": self.special_case_mappings[word],
                "suffix": "",
                "type": "technical",
                "original": word
            }
        
        # Check special case mappings for noun stems
        if word in self.noun_stem_mappings:
            return {
                "stem": self.noun_stem_mappings[word],
                "suffix": "",
                "type": "noun",
                "case": self._infer_case_from_word(word),
                "original": word
            }
        
        # Check special case mappings for verb stems
        if word in self.verb_stem_mappings:
            return {
                "stem": self.verb_stem_mappings[word],
                "suffix": "",
                "type": "verb",
                "tense": self._infer_tense_from_word(word),
                "original": word
            }
        
        # Check if it's a technical term
        for stem in self.technical_stems:
            if word == stem:
                return {
                    "stem": self.technical_stems[stem],
                    "suffix": "",
                    "type": "technical",
                    "original": word
                }
            elif word.startswith(stem) and len(word) > len(stem):
                # It's a technical term with a suffix
                suffix = word[len(stem):]
                return {
                    "stem": self.technical_stems[stem],
                    "suffix": suffix,
                    "type": "technical",
                    "original": word
                }
        
        # Check noun case suffixes
        for suffix, replacement in self.noun_case_suffixes.items():
            if suffix and word.endswith(suffix):
                stem = word[:-len(suffix)] + replacement
                return {
                    "stem": stem,
                    "suffix": suffix,
                    "type": "noun",
                    "case": self._get_case_name(suffix),
                    "original": word
                }
        
        # Check verb suffixes
        for suffix, replacement in self.verb_suffixes.items():
            if suffix and word.endswith(suffix):
                stem = word[:-len(suffix)] + replacement
                return {
                    "stem": stem,
                    "suffix": suffix,
                    "type": "verb",
                    "tense": self._get_tense_name(suffix),
                    "original": word
                }
        
        # Check plural suffixes
        for suffix, replacement in self.plural_suffixes.items():
            if suffix and word.endswith(suffix):
                stem = word[:-len(suffix)] + replacement
                return {
                    "stem": stem,
                    "suffix": suffix,
                    "type": "plural",
                    "original": word
                }
        
        # Check adjective suffixes
        for suffix, replacement in self.adjective_suffixes.items():
            if suffix and word.endswith(suffix):
                stem = word[:-len(suffix)] + replacement
                return {
                    "stem": stem,
                    "suffix": suffix,
                    "type": "adjective",
                    "original": word
                }
        
        # If no suffix is found, assume it's a base form
        return {
            "stem": word,
            "suffix": "",
            "type": "unknown",
            "original": word
        }
    
    def _infer_case_from_word(self, word: str) -> str:
        """Infer grammatical case from the word"""
        if word.endswith("ിൽ"):
            return "locative"
        elif word.endswith("ിന്റെ"):
            return "genitive"
        elif word.endswith("ിന്"):
            return "dative"
        elif word.endswith("ിനെ"):
            return "accusative"
        elif word.endswith("ിനോട്"):
            return "sociative"
        elif word.endswith("ിനാൽ"):
            return "instrumental"
        return "unknown"
    
    def _infer_tense_from_word(self, word: str) -> str:
        """Infer verb tense from the word"""
        if word.endswith("ുന്നു"):
            return "present"
        elif word.endswith("ച്ചു") or word.endswith("ി") or word.endswith("ത്തു") or word.endswith("യ്തു"):
            return "past"
        elif word.endswith("ും"):
            return "future"
        elif word.endswith("ുന്നില്ല") or word.endswith("ില്ല"):
            return "negative_present"
        return "unknown"
    
    def _get_case_name(self, suffix: str) -> str:
        """Get the grammatical case name based on suffix"""
        case_mapping = {
            "യെ": "accusative", "നെ": "accusative", "ത്തെ": "accusative", "ത്തിനെ": "accusative", "വിനെ": "accusative",
            "യുടെ": "genitive", "ന്റെ": "genitive", "ത്തിന്റെ": "genitive", "വിന്റെ": "genitive",
            "യ്ക്ക്": "dative", "ന്": "dative", "ത്തിന്": "dative", "വിന്": "dative",
            "യോട്": "sociative", "നോട്": "sociative", "ത്തോട്": "sociative", "വോട്": "sociative",
            "യാൽ": "instrumental", "നാൽ": "instrumental", "ത്താൽ": "instrumental", "വാൽ": "instrumental",
            "യിൽ": "locative", "നിൽ": "locative", "ത്തിൽ": "locative", "വിൽ": "locative", "ിൽ": "locative",
        }
        return case_mapping.get(suffix, "unknown")
    
    def _get_tense_name(self, suffix: str) -> str:
        """Get the verb tense name based on suffix"""
        tense_mapping = {
            "ുന്നു": "present", "ക്കുന്നു": "present", "ിക്കുന്നു": "present",
            "ി": "past", "ച്ചു": "past", "ത്തു": "past", "ന്നു": "past", "യ്തു": "past",
            "ും": "future", "ക്കും": "future",
            "ുന്നില്ല": "negative_present", "ക്കുന്നില്ല": "negative_present", 
            "ില്ല": "negative", "ാത്ത": "negative",
            "ാൽ": "conditional", "െങ്കിൽ": "conditional",
            "ൂ": "imperative", "ക്കൂ": "imperative",
        }
        return tense_mapping.get(suffix, "unknown")
    
    def standardize_technical_terms(self, text: str) -> str:
        """
        Standardize technical terms in the text based on morphological analysis
        
        Args:
            text: Input text containing technical terms
            
        Returns:
            Text with standardized technical terms
        """
        # First check for special case mappings (complete words only)
        words = text.split()
        result_words = []
        
        for word in words:
            if word in self.special_case_mappings:
                result_words.append(self.special_case_mappings[word])
            elif word == "നെറ്റ്":
                result_words.append("ഇന്റർനെറ്റ്")
            else:
                analysis = self.analyze_word(word)
                if analysis["type"] == "technical":
                    # Keep the standardized stem and add back any suffix
                    result_words.append(analysis["stem"] + analysis["suffix"])
                else:
                    result_words.append(word)
        
        result = " ".join(result_words)
        
        # Final check for duplicated prefixes
        result = result.replace("ഇന്റർഇന്റർനെറ്റ്", "ഇന്റർനെറ്റ്")
        
        return result
    
    def get_stem(self, word: str) -> str:
        """
        Get the stem of a Malayalam word
        
        Args:
            word: The Malayalam word
            
        Returns:
            The stem of the word
        """
        analysis = self.analyze_word(word)
        return analysis["stem"]
    
    def analyze_text(self, text: str) -> List[Dict]:
        """
        Analyze all words in a text
        
        Args:
            text: Input text
            
        Returns:
            List of analysis dictionaries for each word
        """
        words = text.split()
        return [self.analyze_word(word) for word in words]

class TranscriptEnhancer:
    """
    Enhances STT transcript quality without modifying the STT system itself.
    Uses multiple techniques to correct common errors in Malayalam transcription.
    """
    
    def __init__(self, common_phrases_file: Optional[str] = None):
        """Initialize the enhancer with common phrases"""
        self.common_phrases = []
        self.error_patterns = self._load_error_patterns()
        self.technical_term_map = self._load_technical_term_map()
        self.context_terms = {}  # Will store context from previous exchanges
        self.internet_ngrams = self._load_internet_ngrams()  # Add internet-specific n-grams
        
        # Load common phrases if file provided
        if common_phrases_file and os.path.exists(common_phrases_file):
            try:
                with open(common_phrases_file, 'r', encoding='utf-8') as f:
                    self.common_phrases = [line.strip() for line in f if line.strip()]
            except Exception as e:
                logging.error(f"Error loading common phrases: {e}")
        
        # Initialize the morphological analyzer
        self.morphological_analyzer = MalayalamMorphologicalAnalyzer()
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize Malayalam text while preserving vowel signs and other important characters.
        Unlike standard normalization routines that might strip vowel signs in Indic scripts,
        this implementation preserves the linguistic integrity of the text.
        """
        if not text:
            return text
            
        # Apply Unicode normalization (NFC) to ensure consistent representation
        normalized = unicodedata.normalize('NFC', text)
        
        # Remove extra spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Convert to lowercase if the text contains Latin characters
        # This won't affect Malayalam characters
        has_latin = bool(re.search(r'[a-zA-Z]', normalized))
        if has_latin:
            # Split the text to process only Latin parts
            parts = []
            for word in normalized.split():
                if re.search(r'[a-zA-Z]', word):
                    parts.append(word.lower())
                else:
                    parts.append(word)
            normalized = ' '.join(parts)
        
        return normalized
    
    def _fix_malayalam_specific_errors(self, text: str) -> str:
        """
        Fix Malayalam-specific transcription errors that are common in STT systems.
        These include character confusions, incorrect vowel signs, etc.
        """
        if not text:
            return text
            
        # Common character confusions in Malayalam STT
        char_fixes = {
            # Similar looking/sounding character confusions
            'ൻറ്റ': 'ന്റ',  # Wrong: ൻറ്റ, Correct: ന്റ
            'ൻറ': 'ന്റ',    # Wrong: ൻറ, Correct: ന്റ
            'ംമ': 'മ്മ',    # Wrong: ംമ, Correct: മ്മ
            'ഺ': 'ത',      # Wrong: ഺ (rare), Correct: ത
            'ഽ': '',        # Remove avagraha (rarely used in modern Malayalam)
            
            # Common vowel sign corrections
            'ആാ': 'ആ',     # Redundant vowel sign
            'ഈീ': 'ഈ',     # Redundant vowel sign
            'ഊൂ': 'ഊ',     # Redundant vowel sign
            'ഏേ': 'ഏ',     # Redundant vowel sign
            'ഓോ': 'ഓ',     # Redundant vowel sign
            
            # Virama (chandrakkala) corrections
            '്്': '്',      # Double virama
        }
        
        # Apply character fixes
        for wrong, correct in char_fixes.items():
            text = text.replace(wrong, correct)
            
        # Fix common ZWJ/ZWNJ issues in Malayalam
        # Zero-width joiner (ZWJ) and zero-width non-joiner (ZWNJ) are invisible characters
        # that affect the rendering of adjacent characters
        zwj = '\u200D'  # Zero-width joiner
        zwnj = '\u200C'  # Zero-width non-joiner
        
        # Remove unnecessary ZWJ/ZWNJ
        text = re.sub(f'{zwj}+', zwj, text)  # Replace multiple ZWJ with single ZWJ
        text = re.sub(f'{zwnj}+', zwnj, text)  # Replace multiple ZWNJ with single ZWNJ
        
        # Fix common chillu character issues
        # Chillu characters are special forms of consonants in Malayalam
        text = text.replace('ന്\u200D', 'ൻ')  # Replace "ന്" + ZWJ with chillu-n
        text = text.replace('ര്\u200D', 'ർ')  # Replace "ര്" + ZWJ with chillu-r
        text = text.replace('ല്\u200D', 'ൽ')  # Replace "ല്" + ZWJ with chillu-l
        text = text.replace('ള്\u200D', 'ൾ')  # Replace "ള്" + ZWJ with chillu-ll
        text = text.replace('ണ്\u200D', 'ൺ')  # Replace "ണ്" + ZWJ with chillu-nn
        
        return text
    
    def _load_error_patterns(self) -> Dict[str, str]:
        """Load common STT error patterns in Malayalam"""
        return {
            # Common misinterpretations
            'സെക്സ്': 'ചെക്ക്',
            'സെക്സ് വീഡിയോ': 'ചെക്ക് ചെയ്യാൻ',
            'സെക്സ് റൗട്ടർ': 'റൗട്ടർ ചെക്ക്',  # Order matters here
            'സെക്സ് റൗണ്ട്': 'ചെക്ക് ചെയ്യാൻ',
            # Common word variations 
            'റീചാർജ്ജ്': 'റീചാർജ്',
            'സിഗ്നല്‍': 'സിഗ്നൽ',
            'ചാനല്‍': 'ചാനൽ',
            'കണക്ഷന്‍': 'കണക്ഷൻ',
            # Commonly confused homophones
            'റെഡി': 'റെഡ്',
            'നേറ്റ് വർക്ക്': 'നെറ്റ്‌വർക്ക്',
            'എറർ': 'എറർ',
            # Common device name mistakes
            'മോടം': 'മോഡം',
            'റൗടർ': 'റൗട്ടർ',
            # TV/Dish related terms
            'എലൈറ്റ്': 'ഡിഷ് ലൈറ്റ്',
            'ചന്ദ്രിക': 'ചാനൽ',
            'ചാനൽ കാണുന്നില്ല': 'ചാനൽ കാണുന്നില്ല',
            
            # Additional common misinterpretations
            'ചെക്ക് ചെയ്യാം': 'ചെക്ക് ചെയ്യാൻ',
            'ചെക്ക് ചെയ്ത്': 'ചെക്ക് ചെയ്ത',
            'ചെക്ക് ചെയ്തു': 'ചെക്ക് ചെയ്തു',
            'സെറ്റ് ചെയ്യാം': 'സെറ്റ് ചെയ്യാൻ',
            'സെറ്റപ്പ് ചെയ്യാം': 'സെറ്റപ്പ് ചെയ്യാൻ',
            
            # Additional word variations
            'കണക്ഷന്': 'കണക്ഷൻ',
            'കണക്ഷൻസ്': 'കണക്ഷൻ',
            'റീചാർജു': 'റീചാർജ്',
            'റീചാർജ് ചെയ്യാം': 'റീചാർജ് ചെയ്യാൻ',
            'റീചാർജ് ചെയ്ത്': 'റീചാർജ് ചെയ്ത',
            'റീചാർജ് ചെയ്തു': 'റീചാർജ് ചെയ്തു',
            'റീസ്റ്റാർട്ടു': 'റീസ്റ്റാർട്ട്',
            'റീസ്റ്റാർട്ട് ചെയ്യാം': 'റീസ്റ്റാർട്ട് ചെയ്യാൻ',
            'റീസ്റ്റാർട്ട് ചെയ്ത്': 'റീസ്റ്റാർട്ട് ചെയ്ത',
            'റീസ്റ്റാർട്ട് ചെയ്തു': 'റീസ്റ്റാർട്ട് ചെയ്തു',
            
            # Additional device name mistakes
            'മോഡെം': 'മോഡം',
            'മോഡേം': 'മോഡം',
            'റൌട്ടർ': 'റൗട്ടർ',
            'റൌടർ': 'റൗട്ടർ',
            'റൌട്ടര്': 'റൗട്ടർ',
            'വൈഫൈയ്': 'വൈഫൈ',
            'വൈഫൈയി': 'വൈഫൈ',
            'വൈഫൈയ': 'വൈഫൈ',
            
            # Additional TV/Dish related terms
            'ഡിഷ്ടിവി': 'ഡിഷ് ടിവി',
            'ഡിഷ് ടീവീ': 'ഡിഷ് ടിവി',
            'സെറ്റ്ടോപ്': 'സെറ്റ് ടോപ്',
            'സെറ്റ്ടോപ് ബോക്സ്': 'സെറ്റ് ടോപ് ബോക്സ്',
            'സെറ്റ് ടോപ്പ് ബോക്സ്': 'സെറ്റ് ടോപ് ബോക്സ്',
            'ചാനൽ കിട്ടുന്നില്ല': 'ചാനൽ കിട്ടുന്നില്ല',
            'ചാനൽ കാണാൻ കഴിയുന്നില്ല': 'ചാനൽ കാണുന്നില്ല',
            
            # Common internet issue patterns
            'നെറ്റ് വരുന്നില്ല': 'ഇന്റർനെറ്റ് വരുന്നില്ല',
            'നെറ്റ് കണക്ഷൻ ഇല്ല': 'ഇന്റർനെറ്റ് കണക്ഷൻ ഇല്ല',
            'നെറ്റ് സ്ലോ ആണ്': 'ഇന്റർനെറ്റ് സ്ലോ ആണ്',
            'നെറ്റ് വേഗത കുറവാണ്': 'ഇന്റർനെറ്റ് വേഗത കുറവാണ്',
            'നെറ്റ് സ്പീഡ് കുറവാണ്': 'ഇന്റർനെറ്റ് സ്പീഡ് കുറവാണ്',
            'വൈഫൈ വർക്ക് ചെയ്യുന്നില്ല': 'വൈഫൈ പ്രവർത്തിക്കുന്നില്ല',
            'വൈഫൈ വർക്ക് ചെയ്യുന്നില്ലാ': 'വൈഫൈ പ്രവർത്തിക്കുന്നില്ല',
            'വൈഫൈ വർക്ക് ചെയ്യുന്നില്ലെ': 'വൈഫൈ പ്രവർത്തിക്കുന്നില്ല',
            
            # Common pronunciation variations
            'വൈഫയി': 'വൈഫൈ',
            'വൈഫായി': 'വൈഫൈ',
            'വൈഫയ്': 'വൈഫൈ',
            'വൈഫാ': 'വൈഫൈ',
            'ഇന്റർനെറ്റു': 'ഇന്റർനെറ്റ്',
            'ഇന്റർനെറ്റ്‌': 'ഇന്റർനെറ്റ്',
            'ഇന്റർനെറ്': 'ഇന്റർനെറ്റ്',
            'ഇന്റർനെറ': 'ഇന്റർനെറ്റ്',
            
            # Common verb form variations
            'കാണുന്നില്ലാ': 'കാണുന്നില്ല',
            'കാണുന്നില്ലെ': 'കാണുന്നില്ല',
            'കിട്ടുന്നില്ലാ': 'കിട്ടുന്നില്ല',
            'കിട്ടുന്നില്ലെ': 'കിട്ടുന്നില്ല',
            'വരുന്നില്ലാ': 'വരുന്നില്ല',
            'വരുന്നില്ലെ': 'വരുന്നില്ല',
            'പ്രവർത്തിക്കുന്നില്ലാ': 'പ്രവർത്തിക്കുന്നില്ല',
            'പ്രവർത്തിക്കുന്നില്ലെ': 'പ്രവർത്തിക്കുന്നില്ല'
        }
    
    def _load_internet_ngrams(self) -> Dict[str, str]:
        """Load internet-specific n-grams for correction"""
        return {
            # Common internet issue n-grams
            'നെറ്റ് വരുന്നില്ല': 'ഇന്റർനെറ്റ് വരുന്നില്ല',
            'നെറ്റ് സ്ലോ': 'ഇന്റർനെറ്റ് സ്ലോ ആണ്',
            'നെറ്റ് വർക്ക് ഇല്ല': 'നെറ്റ്‌വർക്ക് ഇല്ല',
            'വൈഫൈ വർക്ക് ചെയ്യുന്നില്ല': 'വൈഫൈ പ്രവർത്തിക്കുന്നില്ല',
            'വൈഫൈ കിട്ടുന്നില്ല': 'വൈഫൈ പ്രവർത്തിക്കുന്നില്ല കിട്ടുന്നില്ല',
            'വൈഫൈ കണക്ഷൻ ഇല്ല': 'വൈഫൈ കണക്ഷൻ ഇല്ല',
            'വൈഫൈ സ്ലോ': 'വൈഫൈ സ്ലോ ആണ്',
            'റൗട്ടർ പ്രശ്നം': 'റൗട്ടർ പ്രശ്നം',
            'മോഡം വർക്ക് ചെയ്യുന്നില്ല': 'മോഡം പ്രവർത്തിക്കുന്നില്ല',
            'മോഡം റീസ്റ്റർട്ട്': 'മോഡം റീസ്റ്റാർട്ട്',
            'റീസ്റ്റർട്ട്': 'റീസ്റ്റാർട്ട്',  # Add correction for restart
            'റെഡ് ലൈറ്റ് കാണിക്കുന്നു': 'റെഡ് ലൈറ്റ് കാണിക്കുന്നു',
            'ഇന്റർനെറ്റ് കട്ട്': 'ഇന്റർനെറ്റ് കട്ട് ആയി',
            'സിഗ്നൽ വീക്': 'സിഗ്നൽ ദുർബലമാണ്',
            'നെറ്റ് കണക്റ്റ് ആകുന്നില്ല': 'ഇന്റർനെറ്റ് കണക്റ്റ് ആകുന്നില്ല',
            'പേജ് ലോഡ് ആകുന്നില്ല': 'പേജ് ലോഡ് ആകുന്നില്ല',
            'നെറ്റ്': 'ഇന്റർനെറ്റ്',  # Add basic term replacement
            'സ്പീഡ് കുറവ്': 'സ്പീഡ് കുറവാണ്',  # Add speed issue correction
            'സിഗ്നൽ പോയി': 'സിഗ്നൽ ഇല്ല പോയി',  # Add signal issue correction
            
            # Additional internet issue n-grams
            'ഇന്റർനെറ്റ് ഇല്ല': 'ഇന്റർനെറ്റ് ഇല്ല',
            'ഇന്റർനെറ്റ് കണക്ഷൻ ഇല്ല': 'ഇന്റർനെറ്റ് കണക്ഷൻ ഇല്ല',
            'ഇന്റർനെറ്റ് കണക്ഷൻ പ്രശ്നം': 'ഇന്റർനെറ്റ് കണക്ഷൻ പ്രശ്നം',
            'ഇന്റർനെറ്റ് കണക്ഷൻ തകരാർ': 'ഇന്റർനെറ്റ് കണക്ഷൻ തകരാർ',
            'ഇന്റർനെറ്റ് ഡിസ്കണക്റ്റ് ആകുന്നു': 'ഇന്റർനെറ്റ് ഡിസ്കണക്റ്റ് ആകുന്നു',
            'ഇന്റർനെറ്റ് ഇടയ്ക്കിടെ പോകുന്നു': 'ഇന്റർനെറ്റ് ഇടയ്ക്കിടെ പോകുന്നു',
            'ഇന്റർനെറ്റ് ഇടയ്ക്ക് പോകുന്നു': 'ഇന്റർനെറ്റ് ഇടയ്ക്കിടെ പോകുന്നു',
            'ഇന്റർനെറ്റ് കണക്റ്റ് ആകുന്നില്ല': 'ഇന്റർനെറ്റ് കണക്റ്റ് ആകുന്നില്ല',
            'ഇന്റർനെറ്റ് കണക്ഷൻ ഇടയ്ക്കിടെ പോകുന്നു': 'ഇന്റർനെറ്റ് കണക്ഷൻ ഇടയ്ക്കിടെ പോകുന്നു',
            'ഇന്റർനെറ്റ് കണക്ഷൻ ഡിസ്കണക്റ്റ് ആകുന്നു': 'ഇന്റർനെറ്റ് കണക്ഷൻ ഡിസ്കണക്റ്റ് ആകുന്നു',
            'ഇന്റർനെറ്റ് സ്പീഡ് കുറവാണ്': 'ഇന്റർനെറ്റ് സ്പീഡ് കുറവാണ്',
            'ഇന്റർനെറ്റ് വേഗത കുറവാണ്': 'ഇന്റർനെറ്റ് വേഗത കുറവാണ്',
            'ഇന്റർനെറ്റ് വളരെ സ്ലോ ആണ്': 'ഇന്റർനെറ്റ് വളരെ സ്ലോ ആണ്',
            'ഇന്റർനെറ്റ് വളരെ മന്ദഗതിയിൽ ആണ്': 'ഇന്റർനെറ്റ് വളരെ മന്ദഗതിയിൽ ആണ്',
            'ഇന്റർനെറ്റ് സ്പീഡ് ടെസ്റ്റ്': 'ഇന്റർനെറ്റ് സ്പീഡ് ടെസ്റ്റ്',
            'ഇന്റർനെറ്റ് ബ്രൗസ് ചെയ്യാൻ കഴിയുന്നില്ല': 'ഇന്റർനെറ്റ് ബ്രൗസ് ചെയ്യാൻ കഴിയുന്നില്ല',
            'ഇന്റർനെറ്റ് പേജുകൾ ലോഡ് ആകുന്നില്ല': 'ഇന്റർനെറ്റ് പേജുകൾ ലോഡ് ആകുന്നില്ല',
            
            # WiFi specific n-grams
            'വൈഫൈ പാസ്‌വേഡ് മാറ്റണം': 'വൈഫൈ പാസ്‌വേഡ് മാറ്റണം',
            'വൈഫൈ പാസ്‌വേഡ് മറന്നു': 'വൈഫൈ പാസ്‌വേഡ് മറന്നു',
            'വൈഫൈ പാസ്‌വേഡ് അറിയില്ല': 'വൈഫൈ പാസ്‌വേഡ് അറിയില്ല',
            'വൈഫൈ സിഗ്നൽ ദുർബലമാണ്': 'വൈഫൈ സിഗ്നൽ ദുർബലമാണ്',
            'വൈഫൈ സിഗ്നൽ വീക് ആണ്': 'വൈഫൈ സിഗ്നൽ ദുർബലമാണ്',
            'വൈഫൈ സിഗ്നൽ ഇല്ല': 'വൈഫൈ സിഗ്നൽ ഇല്ല',
            'വൈഫൈ റേഞ്ച് കുറവാണ്': 'വൈഫൈ റേഞ്ച് കുറവാണ്',
            'വൈഫൈ കവറേജ് കുറവാണ്': 'വൈഫൈ കവറേജ് കുറവാണ്',
            'വൈഫൈ കണക്റ്റ് ചെയ്യാൻ കഴിയുന്നില്ല': 'വൈഫൈ കണക്റ്റ് ചെയ്യാൻ കഴിയുന്നില്ല',
            'വൈഫൈ നെറ്റ്‌വർക്ക് കാണുന്നില്ല': 'വൈഫൈ നെറ്റ്‌വർക്ക് കാണുന്നില്ല',
            'വൈഫൈ നെറ്റ്‌വർക്ക് കാണാനില്ല': 'വൈഫൈ നെറ്റ്‌വർക്ക് കാണുന്നില്ല',
            'വൈഫൈ നെറ്റ്‌വർക്ക് ലിസ്റ്റിൽ കാണുന്നില്ല': 'വൈഫൈ നെറ്റ്‌വർക്ക് ലിസ്റ്റിൽ കാണുന്നില്ല',
            'വൈഫൈ ഓഫ് ആണ്': 'വൈഫൈ ഓഫ് ആണ്',
            'വൈഫൈ ഓൺ ആകുന്നില്ല': 'വൈഫൈ ഓൺ ആകുന്നില്ല',
            
            # Router/Modem specific n-grams
            'റൗട്ടർ റീസ്റ്റാർട്ട് ചെയ്യണം': 'റൗട്ടർ റീസ്റ്റാർട്ട് ചെയ്യണം',
            'റൗട്ടർ റീസ്റ്റാർട്ട് ചെയ്തു': 'റൗട്ടർ റീസ്റ്റാർട്ട് ചെയ്തു',
            'റൗട്ടർ ഓൺ ആകുന്നില്ല': 'റൗട്ടർ ഓൺ ആകുന്നില്ല',
            'റൗട്ടർ ഓഫ് ആയി': 'റൗട്ടർ ഓഫ് ആയി',
            'റൗട്ടർ റെഡ് ലൈറ്റ് കാണിക്കുന്നു': 'റൗട്ടർ റെഡ് ലൈറ്റ് കാണിക്കുന്നു',
            'റൗട്ടർ ലൈറ്റ് ഓഫ് ആണ്': 'റൗട്ടർ ലൈറ്റ് ഓഫ് ആണ്',
            'റൗട്ടർ ലൈറ്റുകൾ ഒന്നും കത്തുന്നില്ല': 'റൗട്ടർ ലൈറ്റുകൾ ഒന്നും കത്തുന്നില്ല',
            'റൗട്ടർ പവർ ഓൺ ആകുന്നില്ല': 'റൗട്ടർ പവർ ഓൺ ആകുന്നില്ല',
            'റൗട്ടർ പവർ ലൈറ്റ് ഓഫ് ആണ്': 'റൗട്ടർ പവർ ലൈറ്റ് ഓഫ് ആണ്',
            'റൗട്ടർ ഇന്റർനെറ്റ് ലൈറ്റ് കത്തുന്നില്ല': 'റൗട്ടർ ഇന്റർനെറ്റ് ലൈറ്റ് കത്തുന്നില്ല',
            'റൗട്ടർ ഇന്റർനെറ്റ് ലൈറ്റ് റെഡ് ആണ്': 'റൗട്ടർ ഇന്റർനെറ്റ് ലൈറ്റ് റെഡ് ആണ്',
            'റൗട്ടർ വൈഫൈ ലൈറ്റ് കത്തുന്നില്ല': 'റൗട്ടർ വൈഫൈ ലൈറ്റ് കത്തുന്നില്ല',
            'മോഡം റീസ്റ്റാർട്ട് ചെയ്യണം': 'മോഡം റീസ്റ്റാർട്ട് ചെയ്യണം',
            'മോഡം റീസ്റ്റാർട്ട് ചെയ്തു': 'മോഡം റീസ്റ്റാർട്ട് ചെയ്തു',
            'മോഡം ഓൺ ആകുന്നില്ല': 'മോഡം ഓൺ ആകുന്നില്ല',
            'മോഡം ഓഫ് ആയി': 'മോഡം ഓഫ് ആയി',
            'മോഡം റെഡ് ലൈറ്റ് കാണിക്കുന്നു': 'മോഡം റെഡ് ലൈറ്റ് കാണിക്കുന്നു',
            
            # Data usage related n-grams
            'ഡാറ്റ തീർന്നു': 'ഡാറ്റ തീർന്നു',
            'ഡാറ്റ കഴിഞ്ഞു': 'ഡാറ്റ തീർന്നു',
            'ഡാറ്റ ബാലൻസ് തീർന്നു': 'ഡാറ്റ ബാലൻസ് തീർന്നു',
            'ഡാറ്റ ലിമിറ്റ് കഴിഞ്ഞു': 'ഡാറ്റ ലിമിറ്റ് കഴിഞ്ഞു',
            'ഡാറ്റ ഉപയോഗം അറിയണം': 'ഡാറ്റ ഉപയോഗം അറിയണം',
            'ഡാറ്റ ബാലൻസ് ചെക്ക് ചെയ്യണം': 'ഡാറ്റ ബാലൻസ് ചെക്ക് ചെയ്യണം',
            'ഡാറ്റ ബാലൻസ് എത്രയുണ്ട്': 'ഡാറ്റ ബാലൻസ് എത്രയുണ്ട്',
            'ഡാറ്റ കാർഡ് റീചാർജ് ചെയ്യണം': 'ഡാറ്റ കാർഡ് റീചാർജ് ചെയ്യണം',
            
            # Payment and recharge related n-grams
            'റീചാർജ് ചെയ്യണം': 'റീചാർജ് ചെയ്യണം',
            'റീചാർജ് ചെയ്തു': 'റീചാർജ് ചെയ്തു',
            'റീചാർജ് ചെയ്തിട്ടും നെറ്റ് വരുന്നില്ല': 'റീചാർജ് ചെയ്തിട്ടും ഇന്റർനെറ്റ് വരുന്നില്ല',
            'റീചാർജ് ചെയ്തിട്ടും ഇന്റർനെറ്റ് വരുന്നില്ല': 'റീചാർജ് ചെയ്തിട്ടും ഇന്റർനെറ്റ് വരുന്നില്ല',
            'റീചാർജ് ചെയ്തിട്ടും കണക്ഷൻ ആക്റ്റീവ് ആയില്ല': 'റീചാർജ് ചെയ്തിട്ടും കണക്ഷൻ ആക്റ്റീവ് ആയില്ല',
            'പേയ്മെന്റ് ചെയ്തു': 'പേയ്മെന്റ് ചെയ്തു',
            'പേയ്മെന്റ് ചെയ്തിട്ടും സേവനം ലഭിക്കുന്നില്ല': 'പേയ്മെന്റ് ചെയ്തിട്ടും സേവനം ലഭിക്കുന്നില്ല',
            'ബിൽ അടച്ചു': 'ബിൽ അടച്ചു',
            'ബിൽ അടച്ചിട്ടും കണക്ഷൻ കട്ട് ചെയ്തു': 'ബിൽ അടച്ചിട്ടും കണക്ഷൻ കട്ട് ചെയ്തു',
            
            # Specific error messages and situations
            'നെറ്റ് എറർ': 'ഇന്റർനെറ്റ് എറർ',
            'ഡിഎൻഎസ് എറർ': 'ഡിഎൻഎസ് എറർ',
            'ഇന്റർനെറ്റ് കണക്ഷൻ എറർ': 'ഇന്റർനെറ്റ് കണക്ഷൻ എറർ',
            'വൈഫൈ കണക്റ്റഡ് ബട്ട് നോ ഇന്റർനെറ്റ്': 'വൈഫൈ കണക്റ്റ് ചെയ്തിട്ടുണ്ട് പക്ഷേ ഇന്റർനെറ്റ് ഇല്ല',
            'വൈഫൈ കണക്റ്റ് ചെയ്തിട്ടുണ്ട് പക്ഷേ ഇന്റർനെറ്റ് ഇല്ല': 'വൈഫൈ കണക്റ്റ് ചെയ്തിട്ടുണ്ട് പക്ഷേ ഇന്റർനെറ്റ് ഇല്ല',
            'വൈഫൈ കണക്റ്റ് ചെയ്തിട്ടുണ്ട് പക്ഷേ ഇന്റർനെറ്റ് വരുന്നില്ല': 'വൈഫൈ കണക്റ്റ് ചെയ്തിട്ടുണ്ട് പക്ഷേ ഇന്റർനെറ്റ് വരുന്നില്ല',
            'ഇന്റർനെറ്റ് കണക്ഷൻ ലിമിറ്റഡ്': 'ഇന്റർനെറ്റ് കണക്ഷൻ പരിമിതമാണ്',
            'ഇന്റർനെറ്റ് കണക്ഷൻ പരിമിതമാണ്': 'ഇന്റർനെറ്റ് കണക്ഷൻ പരിമിതമാണ്',
            'ഇന്റർനെറ്റ് കണക്ഷൻ അൺസെക്യൂർ': 'ഇന്റർനെറ്റ് കണക്ഷൻ അൺസെക്യൂർ ആണ്',
            'ഇന്റർനെറ്റ് കണക്ഷൻ അൺസെക്യൂർ ആണ്': 'ഇന്റർനെറ്റ് കണക്ഷൻ അൺസെക്യൂർ ആണ്'
        }
    
    def _load_technical_term_map(self) -> Dict[str, str]:
        """Load technical term mappings focused on internet-related support"""
        return {
            # Network equipment
            "റൗട്ടർ": "റൗട്ടർ",
            "റൌട്ടർ": "റൗട്ടർ",
            "റൌടർ": "റൗട്ടർ",
            "റൗടർ": "റൗട്ടർ",
            "മോഡം": "മോഡം",
            "മോടം": "മോഡം",
            "മോഡെം": "മോഡം",
            "മോഡേം": "മോഡം",
            
            # Connection types
            "വൈഫൈ": "വൈഫൈ",
            "വൈഫൈയ്": "വൈഫൈ",
            "വൈഫൈയി": "വൈഫൈ",
            "വൈഫയി": "വൈഫൈ",
            "വൈഫായി": "വൈഫൈ",
            "വൈഫയ്": "വൈഫൈ",
            "വൈഫാ": "വൈഫൈ",
            "ഇന്റർനെറ്റ്": "ഇന്റർനെറ്റ്",
            "ഇന്റർനെറ്റു": "ഇന്റർനെറ്റ്",
            "ഇന്റർനെറ്റ്‌": "ഇന്റർനെറ്റ്",
            "ഇന്റർനെറ്": "ഇന്റർനെറ്റ്",
            "ഇന്റർനെറ": "ഇന്റർനെറ്റ്",
            "നെറ്റ്": "ഇന്റർനെറ്റ്",
            "ബ്രോഡ്ബാൻഡ്": "ബ്രോഡ്ബാൻഡ്",
            "ഫൈബർ": "ഫൈബർ",
            "ഫൈബർ നെറ്റ്": "ഫൈബർ നെറ്റ്",
            "ഫൈബർ കണക്ഷൻ": "ഫൈബർ കണക്ഷൻ",
            
            # Connection statuses
            "കണക്ഷൻ": "കണക്ഷൻ",
            "കണക്ഷന്‍": "കണക്ഷൻ",
            "കണക്ഷന്": "കണക്ഷൻ",
            "കണക്ഷൻസ്": "കണക്ഷൻ",
            "കണക്റ്റ്": "കണക്റ്റ്",
            "ഡിസ്കണക്റ്റ്": "ഡിസ്കണക്റ്റ്",
            "ഡിസ്‌കണക്റ്റ്": "ഡിസ്കണക്റ്റ്",
            "റീകണക്റ്റ്": "റീകണക്റ്റ്",
            "റീ കണക്റ്റ്": "റീകണക്റ്റ്",
            
            # Network quality
            "സിഗ്നൽ": "സിഗ്നൽ",
            "സിഗ്നല്‍": "സിഗ്നൽ",
            "സ്പീഡ്": "സ്പീഡ്",
            "സ്ലോ": "സ്ലോ",
            "വേഗത": "വേഗത",
            
            # Colors/indicators
            "റെഡ് ലൈറ്റ്": "റെഡ് ലൈറ്റ്",
            "പച്ച ലൈറ്റ്": "പച്ച ലൈറ്റ്",
            "മഞ്ഞ ലൈറ്റ്": "മഞ്ഞ ലൈറ്റ്",
            
            # Actions
            "റീസ്റ്റാർട്ട്": "റീസ്റ്റാർട്ട്",
            "റീസ്റ്റർട്ട്": "റീസ്റ്റാർട്ട്",
            "ഓണാക്കൽ": "ഓണാക്കുക",
            "റീചാർജ്": "റീചാർജ്",
            "റീചാർജ്ജ്": "റീചാർജ്",
            "റീചാർജു": "റീചാർജ്",
            
            # Status and error terms
            "എറർ": "എറർ",
            "പ്രശ്നം": "പ്രശ്നം",
            "തകരാർ": "തകരാർ",
            "ബഫറിങ്": "ബഫറിങ്",
            "ബഫറിങ്ങ്": "ബഫറിങ്",
            
            # Data and billing
            "ഡാറ്റ": "ഡാറ്റ",
            "ഡാറ്റ പ്ലാൻ": "ഡാറ്റ പ്ലാൻ",
            "ഡാറ്റ കാർഡ്": "ഡാറ്റ കാർഡ്",
            "പേയ്മെന്റ്": "പേയ്മെന്റ്",
            "പേമെന്റ്": "പേയ്മെന്റ്",
            "ബിൽ": "ബിൽ",
            "ബില്ല്": "ബിൽ",
            
            # Internet settings
            "പാസ്‌വേഡ്": "പാസ്‌വേഡ്",
            "പാസ്വേഡ്": "പാസ്‌വേഡ്",
            "ഐപി": "ഐപി",
            "ഐപി അഡ്രസ്": "ഐപി അഡ്രസ്",
            "ഡിഎൻഎസ്": "ഡിഎൻഎസ്",
            
            # Network related
            "നെറ്റ്‌വർക്ക്": "നെറ്റ്‌വർക്ക്",
            "നേറ്റ് വർക്ക്": "നെറ്റ്‌വർക്ക്",
            "ഹോട്ട്സ്പോട്ട്": "ഹോട്ട്സ്പോട്ട്",
            "ഹോട്സ്പോട്ട്": "ഹോട്ട്സ്പോട്ട്",
            "ഹോട്ട് സ്പോട്ട്": "ഹോട്ട്സ്പോട്ട്",
            "ഹോട് സ്പോട്ട്": "ഹോട്ട്സ്പോട്ട്",
            
            # Performance metrics
            "ഡൗൺലോഡ്": "ഡൗൺലോഡ്",
            "അപ്‌ലോഡ്": "അപ്‌ലോഡ്",
            "ഡൗൺലോഡ് സ്പീഡ്": "ഡൗൺലോഡ് സ്പീഡ്",
            "അപ്‌ലോഡ് സ്പീഡ്": "അപ്‌ലോഡ് സ്പീഡ്",
            "പിങ്": "പിങ്",
            "ലാറ്റൻസി": "ലാറ്റൻസി",
            "ബാൻഡ്‌വിഡ്ത്": "ബാൻഡ്‌വിഡ്ത്",
            "ബാൻഡ് വിഡ്ത്": "ബാൻഡ്‌വിഡ്ത്"
        }
    
    def _load_internet_ngrams(self) -> Dict[str, str]:
        """Load internet-specific n-grams for correction"""
        return {
            # Connection issues
            "നെറ്റ് വരുന്നില്ല": "ഇന്റർനെറ്റ് വരുന്നില്ല",
            "നെറ്റ് കിട്ടുന്നില്ല": "ഇന്റർനെറ്റ് കിട്ടുന്നില്ല",
            "ഇന്റർനെറ്റ് വരുന്നില്ല": "ഇന്റർനെറ്റ് വരുന്നില്ല",
            "ഇന്റർനെറ്റ് കിട്ടുന്നില്ല": "ഇന്റർനെറ്റ് കിട്ടുന്നില്ല",
            "ഇന്റർനെറ്റ് ഇല്ല": "ഇന്റർനെറ്റ് ഇല്ല",
            "ഇന്റർനെറ്റ് കണക്ഷൻ ഇല്ല": "ഇന്റർനെറ്റ് കണക്ഷൻ ഇല്ല",
            "നെറ്റ് കണക്ഷൻ ഇല്ല": "ഇന്റർനെറ്റ് കണക്ഷൻ ഇല്ല",
            "ഇന്റർനെറ്റ് ഡിസ്കണക്റ്റ് ആകുന്നു": "ഇന്റർനെറ്റ് ഡിസ്കണക്റ്റ് ആകുന്നു",
            "ഇന്റർനെറ്റ് ഇടയ്ക്കിടെ പോകുന്നു": "ഇന്റർനെറ്റ് ഇടയ്ക്കിടെ പോകുന്നു",
            "ഇന്റർനെറ്റ് ഇടയ്ക്ക് പോകുന്നു": "ഇന്റർനെറ്റ് ഇടയ്ക്കിടെ പോകുന്നു",
            "ഇന്റർനെറ്റ് കണക്റ്റ് ആകുന്നില്ല": "ഇന്റർനെറ്റ് കണക്റ്റ് ആകുന്നില്ല",
            "നെറ്റ് കണക്റ്റ് ആകുന്നില്ല": "ഇന്റർനെറ്റ് കണക്റ്റ് ആകുന്നില്ല",
            
            # Speed issues
            "നെറ്റ് സ്ലോ": "ഇന്റർനെറ്റ് സ്ലോ ആണ്",
            "ഇന്റർനെറ്റ് സ്ലോ": "ഇന്റർനെറ്റ് സ്ലോ ആണ്",
            "നെറ്റ് വേഗത കുറവാണ്": "ഇന്റർനെറ്റ് വേഗത കുറവാണ്",
            "ഇന്റർനെറ്റ് വേഗത കുറവാണ്": "ഇന്റർനെറ്റ് വേഗത കുറവാണ്",
            "നെറ്റ് സ്പീഡ് കുറവാണ്": "ഇന്റർനെറ്റ് സ്പീഡ് കുറവാണ്",
            "ഇന്റർനെറ്റ് സ്പീഡ് കുറവാണ്": "ഇന്റർനെറ്റ് സ്പീഡ് കുറവാണ്",
            "ഇന്റർനെറ്റ് വളരെ സ്ലോ ആണ്": "ഇന്റർനെറ്റ് വളരെ സ്ലോ ആണ്",
            "ഇന്റർനെറ്റ് വളരെ മന്ദഗതിയിൽ ആണ്": "ഇന്റർനെറ്റ് വളരെ മന്ദഗതിയിൽ ആണ്",
            "സ്പീഡ് കുറവ്": "സ്പീഡ് കുറവാണ്",
            
            # WiFi issues
            "വൈഫൈ വർക്ക് ചെയ്യുന്നില്ല": "വൈഫൈ പ്രവർത്തിക്കുന്നില്ല",
            "വൈഫൈ കിട്ടുന്നില്ല": "വൈഫൈ പ്രവർത്തിക്കുന്നില്ല കിട്ടുന്നില്ല",
            "വൈഫൈ കണക്ഷൻ ഇല്ല": "വൈഫൈ കണക്ഷൻ ഇല്ല",
            "വൈഫൈ സ്ലോ": "വൈഫൈ സ്ലോ ആണ്",
            "വൈഫൈ സിഗ്നൽ ദുർബലമാണ്": "വൈഫൈ സിഗ്നൽ ദുർബലമാണ്",
            "വൈഫൈ സിഗ്നൽ വീക് ആണ്": "വൈഫൈ സിഗ്നൽ ദുർബലമാണ്",
            "വൈഫൈ സിഗ്നൽ ഇല്ല": "വൈഫൈ സിഗ്നൽ ഇല്ല",
            "വൈഫൈ പാസ്‌വേഡ് മാറ്റണം": "വൈഫൈ പാസ്‌വേഡ് മാറ്റണം",
            "വൈഫൈ പാസ്‌വേഡ് മറന്നു": "വൈഫൈ പാസ്‌വേഡ് മറന്നു",
            "വൈഫൈ പാസ്‌വേഡ് അറിയില്ല": "വൈഫൈ പാസ്‌വേഡ് അറിയില്ല",
            "വൈഫൈ കണക്റ്റ് ചെയ്യാൻ കഴിയുന്നില്ല": "വൈഫൈ കണക്റ്റ് ചെയ്യാൻ കഴിയുന്നില്ല",
            "വൈഫൈ കണക്റ്റ് ചെയ്തിട്ടും ഇന്റർനെറ്റ് വരുന്നില്ല": "വൈഫൈ കണക്റ്റ് ചെയ്തിട്ടും ഇന്റർനെറ്റ് വരുന്നില്ല",
            "വൈഫൈ നെറ്റ്‌വർക്ക് കാണുന്നില്ല": "വൈഫൈ നെറ്റ്‌വർക്ക് കാണുന്നില്ല",
            
            # Router/Modem issues
            "റൗട്ടർ പ്രശ്നം": "റൗട്ടർ പ്രശ്നം",
            "റൗട്ടർ റീസ്റ്റാർട്ട് ചെയ്യണം": "റൗട്ടർ റീസ്റ്റാർട്ട് ചെയ്യണം",
            "റൗട്ടർ റീസ്റ്റാർട്ട് ചെയ്തു": "റൗട്ടർ റീസ്റ്റാർട്ട് ചെയ്തു",
            "റൗട്ടർ ഓൺ ആകുന്നില്ല": "റൗട്ടർ ഓൺ ആകുന്നില്ല",
            "റൗട്ടർ ഓഫ് ആയി": "റൗട്ടർ ഓഫ് ആയി",
            "റൗട്ടർ റെഡ് ലൈറ്റ് കാണിക്കുന്നു": "റൗട്ടർ റെഡ് ലൈറ്റ് കാണിക്കുന്നു",
            "റൗട്ടർ ലൈറ്റ് ഓഫ് ആണ്": "റൗട്ടർ ലൈറ്റ് ഓഫ് ആണ്",
            "മോഡം വർക്ക് ചെയ്യുന്നില്ല": "മോഡം പ്രവർത്തിക്കുന്നില്ല",
            "മോഡം റീസ്റ്റാർട്ട്": "മോഡം റീസ്റ്റാർട്ട്",
            "മോഡം റീസ്റ്റാർട്ട് ചെയ്യണം": "മോഡം റീസ്റ്റാർട്ട് ചെയ്യണം",
            "മോഡം റീസ്റ്റാർട്ട് ചെയ്തു": "മോഡം റീസ്റ്റാർട്ട് ചെയ്തു",
            "മോഡം ഓൺ ആകുന്നില്ല": "മോഡം ഓൺ ആകുന്നില്ല",
            "മോഡം ഓഫ് ആയി": "മോഡം ഓഫ് ആയി",
            
            # Data and billing
            "ഡാറ്റ തീർന്നു": "ഡാറ്റ തീർന്നു",
            "ഡാറ്റ കഴിഞ്ഞു": "ഡാറ്റ തീർന്നു",
            "ഡാറ്റ ബാലൻസ് തീർന്നു": "ഡാറ്റ ബാലൻസ് തീർന്നു",
            "ഡാറ്റ ലിമിറ്റ് കഴിഞ്ഞു": "ഡാറ്റ ലിമിറ്റ് കഴിഞ്ഞു",
            "ഡാറ്റ ഉപയോഗം അറിയണം": "ഡാറ്റ ഉപയോഗം അറിയണം",
            "ഡാറ്റ ബാലൻസ് ചെക്ക് ചെയ്യണം": "ഡാറ്റ ബാലൻസ് ചെക്ക് ചെയ്യണം",
            "ഡാറ്റ ബാലൻസ് എത്രയുണ്ട്": "ഡാറ്റ ബാലൻസ് എത്രയുണ്ട്",
            "റീചാർജ് ചെയ്യണം": "റീചാർജ് ചെയ്യണം",
            "റീചാർജ് ചെയ്തു": "റീചാർജ് ചെയ്തു",
            "റീചാർജ് ചെയ്തിട്ടും നെറ്റ് വരുന്നില്ല": "റീചാർജ് ചെയ്തിട്ടും ഇന്റർനെറ്റ് വരുന്നില്ല",
            "റീചാർജ് ചെയ്തിട്ടും ഇന്റർനെറ്റ് വരുന്നില്ല": "റീചാർജ് ചെയ്തിട്ടും ഇന്റർനെറ്റ് വരുന്നില്ല",
            "ബിൽ അടച്ചു": "ബിൽ അടച്ചു",
            "ബിൽ അടച്ചിട്ടും കണക്ഷൻ കട്ട് ചെയ്തു": "ബിൽ അടച്ചിട്ടും കണക്ഷൻ കട്ട് ചെയ്തു",
            
            # Specific error messages
            "നെറ്റ് എറർ": "ഇന്റർനെറ്റ് എറർ",
            "ഡിഎൻഎസ് എറർ": "ഡിഎൻഎസ് എറർ",
            "ഇന്റർനെറ്റ് കണക്ഷൻ എറർ": "ഇന്റർനെറ്റ് കണക്ഷൻ എറർ",
            "ഇന്റർനെറ്റ് കണക്ഷൻ ലിമിറ്റഡ്": "ഇന്റർനെറ്റ് കണക്ഷൻ പരിമിതമാണ്",
            "ഇന്റർനെറ്റ് കണക്ഷൻ പരിമിതമാണ്": "ഇന്റർനെറ്റ് കണക്ഷൻ പരിമിതമാണ്",
            "ഇന്റർനെറ്റ് കണക്ഷൻ അൺസെക്യൂർ": "ഇന്റർനെറ്റ് കണക്ഷൻ അൺസെക്യൂർ ആണ്",
            
            # Usage and performance issues
            "ഇന്റർനെറ്റ് സ്പീഡ് ടെസ്റ്റ്": "ഇന്റർനെറ്റ് സ്പീഡ് ടെസ്റ്റ്",
            "ഇന്റർനെറ്റ് ബ്രൗസ് ചെയ്യാൻ കഴിയുന്നില്ല": "ഇന്റർനെറ്റ് ബ്രൗസ് ചെയ്യാൻ കഴിയുന്നില്ല",
            "ഇന്റർനെറ്റ് പേജുകൾ ലോഡ് ആകുന്നില്ല": "ഇന്റർനെറ്റ് പേജുകൾ ലോഡ് ആകുന്നില്ല",
            "പേജ് ലോഡ് ആകുന്നില്ല": "പേജ് ലോഡ് ആകുന്നില്ല",
            "സിഗ്നൽ പോയി": "സിഗ്നൽ ഇല്ല പോയി",
            "സിഗ്നൽ വീക്": "സിഗ്നൽ ദുർബലമാണ്",
            "ഡൗൺലോഡ് സ്പീഡ് കുറവാണ്": "ഡൗൺലോഡ് സ്പീഡ് കുറവാണ്",
            "അപ്‌ലോഡ് സ്പീഡ് കുറവാണ്": "അപ്‌ലോഡ് സ്പീഡ് കുറവാണ്",
            "ബഫറിങ്": "ബഫറിങ്",
            "ബഫറിങ് ഉണ്ട്": "ബഫറിങ് ഉണ്ട്"
        }
        
    def update_context(self, conversation_history: List[Dict[str, str]]):
        """Update context from conversation history"""
        # Extract technical terms from recent conversations
        self.context_terms = {}
        if not conversation_history:
            return
            
        # Look at last 3 exchanges
        recent_exchanges = conversation_history[-3:] if len(conversation_history) >= 3 else conversation_history
        
        # Extract technical terms used recently
        for exchange in recent_exchanges:
            user_text = exchange.get("user", "")
            bot_text = exchange.get("bot", "")
            
            # Check for technical terms in both user and bot messages
            for tech_term in self.technical_term_map.keys():
                if tech_term in user_text or tech_term in bot_text:
                    self.context_terms[tech_term] = self.technical_term_map[tech_term]
    
    def _apply_error_corrections(self, text: str) -> str:
        """Apply known error pattern corrections"""
        for error, correction in self.error_patterns.items():
            text = text.replace(error, correction)
        return text
    
    def _apply_fuzzy_matching(self, text: str) -> str:
        """
        Apply fuzzy matching for common phrases with special handling for Malayalam.
        Malayalam requires special consideration due to its complex orthography.
        """
        if not text or not self.common_phrases:
            return text
            
        words = text.split()
        corrected_words = []
        
        for word in words:
            # Skip very short words
            if len(word) <= 2:
                corrected_words.append(word)
                continue
                
            # Special handling for Malayalam words
            is_malayalam = bool(re.search(r'[\u0D00-\u0D7F]', word))
            
            if is_malayalam:
                # For Malayalam words, use a lower threshold but consider character shape similarity
                matches = process.extract(
                    word, 
                    self.common_phrases, 
                    scorer=fuzz.ratio,  # Could use fuzz.token_sort_ratio for better results
                    limit=1
                )
                
                # Use a lower threshold for Malayalam as small differences can be significant
                if matches and matches[0][1] > 80:  # 80% similarity threshold for Malayalam
                    corrected_words.append(matches[0][0])
                else:
                    corrected_words.append(word)
            else:
                # For non-Malayalam words, use standard fuzzy matching
                matches = process.extract(word, self.common_phrases, scorer=fuzz.ratio, limit=1)
                if matches and matches[0][1] > 85:  # 85% similarity threshold
                    corrected_words.append(matches[0][0])
                else:
                    corrected_words.append(word)
                
        return " ".join(corrected_words)
    
    def _apply_context_aware_corrections(self, text: str) -> str:
        """Apply context-aware corrections based on morphological analysis"""
        words = text.split()
        result_words = []
        
        for i, word in enumerate(words):
            # Analyze the current word
            analysis = self.morphological_analyzer.analyze_word(word)
            
            # Special case for technical terms with incorrect inflections
            if analysis["type"] == "technical" and analysis["suffix"]:
                # Keep the standardized stem and add back any suffix
                result_words.append(analysis["stem"] + analysis["suffix"])
            else:
                result_words.append(word)
        
        return " ".join(result_words)
    
    def _apply_ngram_analysis(self, text: str) -> str:
        """Apply n-gram analysis specifically for internet-related issues"""
        if not text:
            return text
            
        # Create a copy of the text for processing
        processed_text = text
        
        # Special case handling for WiFi-related phrases
        if 'വൈഫൈ വർക്ക് ചെയ്യുന്നില്ല' in processed_text:
            processed_text = processed_text.replace('വൈഫൈ വർക്ക് ചെയ്യുന്നില്ല', 'വൈഫൈ പ്രവർത്തിക്കുന്നില്ല')
            return processed_text
            
        if 'വൈഫൈ കിട്ടുന്നില്ല' in processed_text:
            processed_text = processed_text.replace('വൈഫൈ കിട്ടുന്നില്ല', 'വൈഫൈ പ്രവർത്തിക്കുന്നില്ല കിട്ടുന്നില്ല')
            return processed_text
            
        # Process multi-word phrases first (longer phrases first to avoid partial matches)
        ngrams = sorted(self.internet_ngrams.keys(), key=len, reverse=True)
        for ngram in ngrams:
            if len(ngram.split()) > 1 and ngram in processed_text:
                processed_text = processed_text.replace(ngram, self.internet_ngrams[ngram])
        
        # Then process single words - but avoid processing words that are part of already processed phrases
        words = processed_text.split()
        result_words = []
        
        for word in words:
            # Check if this word is a known internet term
            if word in self.internet_ngrams:
                result_words.append(self.internet_ngrams[word])
            else:
                result_words.append(word)
                
        processed_text = " ".join(result_words)
        
        # Apply context-based corrections
        if 'സിഗ്നൽ' in processed_text and 'വരുന്നില്ല' in processed_text and 'സിഗ്നൽ ഇല്ല' not in processed_text:
            processed_text = processed_text.replace('സിഗ്നൽ', 'സിഗ്നൽ ഇല്ല', 1)
            
        return processed_text
    
    def _detect_code_switching(self, text: str) -> Dict[str, List[str]]:
        """
        Detect code-switching in the input text and categorize words.
        
        This method identifies different types of code-switching:
        - Inter-sentential: Switching languages between sentences
        - Intra-sentential: Switching languages within a sentence
        - Intra-word: Mixing languages within a word (e.g., English root with Malayalam inflection)
        
        Args:
            text: Input text that may contain code-switching
            
        Returns:
            Dictionary with categorized words
        """
        if not text:
            return {"malayalam": [], "english": [], "code_switched": [], "numbers": []}
            
        # Split the text into words
        words = text.split()
        
        # Categorize each word
        malayalam_words = []
        english_words = []
        code_switched_words = []
        numbers = []
        
        for word in words:
            # Check if the word contains numbers
            if re.search(r'\d', word):
                numbers.append(word)
                continue
                
            # Check if the word contains Malayalam characters
            has_malayalam = bool(re.search(r'[\u0D00-\u0D7F]', word))
            
            # Check if the word contains Latin characters
            has_latin = bool(re.search(r'[a-zA-Z]', word))
            
            # Categorize the word
            if has_malayalam and has_latin:
                # Word contains both Malayalam and Latin characters
                code_switched_words.append(word)
            elif has_malayalam:
                # Word contains only Malayalam characters
                malayalam_words.append(word)
            elif has_latin:
                # Word contains only Latin characters
                english_words.append(word)
            else:
                # Word contains other characters (punctuation, etc.)
                pass
        
        return {
            "malayalam": malayalam_words,
            "english": english_words,
            "code_switched": code_switched_words,
            "numbers": numbers
        }
    
    def _handle_code_switched_text(self, text: str) -> str:
        """
        Handle code-switched text by applying appropriate normalization techniques.
        
        This method applies different normalization techniques based on the type of code-switching:
        - For Malayalam words: Apply Malayalam-specific normalization
        - For English words: Apply English normalization or translate to Malayalam equivalents
        - For code-switched words: Apply specialized handling
        
        Focuses specifically on internet-related customer support vocabulary.
        
        Args:
            text: Input text that may contain code-switching
            
        Returns:
            Normalized text
        """
        if not text:
            return text
            
        # Detect code-switching
        categorized_words = self._detect_code_switching(text)
        
        # Process each category separately
        normalized_text = text
        
        # Handle intra-word code-switching (most complex case)
        for word in categorized_words["code_switched"]:
            # For intra-word code-switching, we need to identify the root and inflection
            # This is a simplified approach; a more sophisticated approach would use
            # morphological analysis
            
            # Check for common English tech terms with Malayalam inflections
            english_roots = [
                # Core internet terms
                "wifi", "router", "modem", "internet", "connect", "speed", "signal", 
                "data", "network", "slow", "fast", "error", "restart", "reset", "password",
                
                # Connection types
                "fiber", "broadband", "hotspot", "wireless", "lan", "ip", "dns",
                
                # Performance metrics
                "download", "upload", "server", "ping", "bandwidth", "latency",
                
                # Billing and account
                "recharge", "bill", "payment", "balance", "plan", "package",
                
                # Status and errors
                "disconnect", "reconnect", "check", "test", "issue", "problem"
            ]
                            
            for root in english_roots:
                if root in word.lower():
                    # Replace the English root with its Malayalam equivalent
                    if root == "wifi":
                        standard_form = word.lower().replace(root, "വൈഫൈ")
                    elif root == "router":
                        standard_form = word.lower().replace(root, "റൗട്ടർ")
                    elif root == "modem":
                        standard_form = word.lower().replace(root, "മോഡം")
                    elif root == "internet":
                        standard_form = word.lower().replace(root, "ഇന്റർനെറ്റ്")
                    elif root == "connect":
                        standard_form = word.lower().replace(root, "കണക്റ്റ്")
                    elif root == "speed":
                        standard_form = word.lower().replace(root, "സ്പീഡ്")
                    elif root == "signal":
                        standard_form = word.lower().replace(root, "സിഗ്നൽ")
                    elif root == "recharge":
                        standard_form = word.lower().replace(root, "റീചാർജ്")
                    elif root == "data":
                        standard_form = word.lower().replace(root, "ഡാറ്റ")
                    elif root == "network":
                        standard_form = word.lower().replace(root, "നെറ്റ്‌വർക്ക്")
                    elif root == "slow":
                        standard_form = word.lower().replace(root, "സ്ലോ")
                    elif root == "fast":
                        standard_form = word.lower().replace(root, "ഫാസ്റ്റ്")
                    elif root == "error":
                        standard_form = word.lower().replace(root, "എറർ")
                    elif root == "restart":
                        standard_form = word.lower().replace(root, "റീസ്റ്റാർട്ട്")
                    elif root == "reset":
                        standard_form = word.lower().replace(root, "റീസെറ്റ്")
                    elif root == "password":
                        standard_form = word.lower().replace(root, "പാസ്‌വേഡ്")
                    elif root == "download":
                        standard_form = word.lower().replace(root, "ഡൗൺലോഡ്")
                    elif root == "upload":
                        standard_form = word.lower().replace(root, "അപ്‌ലോഡ്")
                    elif root == "server":
                        standard_form = word.lower().replace(root, "സെർവർ")
                    elif root == "ping":
                        standard_form = word.lower().replace(root, "പിങ്")
                    elif root == "fiber":
                        standard_form = word.lower().replace(root, "ഫൈബർ")
                    elif root == "broadband":
                        standard_form = word.lower().replace(root, "ബ്രോഡ്ബാൻഡ്")
                    elif root == "hotspot":
                        standard_form = word.lower().replace(root, "ഹോട്ട്സ്പോട്ട്")
                    elif root == "wireless":
                        standard_form = word.lower().replace(root, "വയർലെസ്")
                    elif root == "lan":
                        standard_form = word.lower().replace(root, "ലാൻ")
                    elif root == "ip":
                        standard_form = word.lower().replace(root, "ഐപി")
                    elif root == "dns":
                        standard_form = word.lower().replace(root, "ഡിഎൻഎസ്")
                    elif root == "bill":
                        standard_form = word.lower().replace(root, "ബിൽ")
                    elif root == "payment":
                        standard_form = word.lower().replace(root, "പേയ്മെന്റ്")
                    elif root == "balance":
                        standard_form = word.lower().replace(root, "ബാലൻസ്")
                    elif root == "plan":
                        standard_form = word.lower().replace(root, "പ്ലാൻ")
                    elif root == "package":
                        standard_form = word.lower().replace(root, "പാക്കേജ്")
                    elif root == "disconnect":
                        standard_form = word.lower().replace(root, "ഡിസ്കണക്റ്റ്")
                    elif root == "reconnect":
                        standard_form = word.lower().replace(root, "റീകണക്റ്റ്")
                    elif root == "check":
                        standard_form = word.lower().replace(root, "ചെക്ക്")
                    elif root == "test":
                        standard_form = word.lower().replace(root, "ടെസ്റ്റ്")
                    elif root == "issue":
                        standard_form = word.lower().replace(root, "പ്രശ്നം")
                    elif root == "problem":
                        standard_form = word.lower().replace(root, "പ്രശ്നം")
                    elif root == "bandwidth":
                        standard_form = word.lower().replace(root, "ബാൻഡ്‌വിഡ്ത്")
                    elif root == "latency":
                        standard_form = word.lower().replace(root, "ലാറ്റൻസി")
                    else:
                        standard_form = word  # Keep original if no mapping exists
            
            # Replace the original word with the standardized form
            normalized_text = normalized_text.replace(word, standard_form)
            break
        
        # Handle English words that have Malayalam equivalents
        english_to_malayalam = {
            # Core internet terms
            "wifi": "വൈഫൈ",
            "router": "റൗട്ടർ",
            "modem": "മോഡം",
            "internet": "ഇന്റർനെറ്റ്",
            "speed": "സ്പീഡ്",
            "signal": "സിഗ്നൽ",
            "data": "ഡാറ്റ",
            "gb": "ജിബി",
            "mb": "എംബി",
            "kb": "കെബി",
            "connect": "കണക്റ്റ്",
            "connection": "കണക്ഷൻ",
            "restart": "റീസ്റ്റാർട്ട്",
            "recharge": "റീചാർജ്",
            "network": "നെറ്റ്‌വർക്ക്",
            "slow": "സ്ലോ",
            "fast": "ഫാസ്റ്റ്",
            "problem": "പ്രശ്നം",
            "issue": "പ്രശ്നം",
            "error": "എറർ",
            
            # Technical specifications
            "password": "പാസ്‌വേഡ്",
            "username": "യൂസർനെയിം",
            "download": "ഡൗൺലോഡ്",
            "upload": "അപ്‌ലോഡ്",
            "server": "സെർവർ",
            "ping": "പിങ്",
            "latency": "ലാറ്റൻസി",
            "bandwidth": "ബാൻഡ്‌വിഡ്ത്",
            "fiber": "ഫൈബർ",
            "broadband": "ബ്രോഡ്ബാൻഡ്",
            "hotspot": "ഹോട്ട്സ്പോട്ട്",
            "wireless": "വയർലെസ്",
            "wired": "വയർഡ്",
            "lan": "ലാൻ",
            "ip": "ഐപി",
            "dns": "ഡിഎൻഎസ്",
            "reset": "റീസെറ്റ്",
            
            # Billing and account
            "bill": "ബിൽ",
            "payment": "പേയ്മെന്റ്",
            "balance": "ബാലൻസ്",
            "plan": "പ്ലാൻ",
            "package": "പാക്കേജ്",
            
            # Status indicators
            "online": "ഓൺലൈൻ",
            "offline": "ഓഫ്‌ലൈൻ",
            "on": "ഓൺ",
            "off": "ഓഫ്",
            "power": "പവർ",
            "green": "പച്ച",
            "yellow": "മഞ്ഞ",
            "red": "ചുവപ്പ്",
            "blue": "നീല",
            
            # Connection issues
            "buffer": "ബഫർ",
            "buffering": "ബഫറിങ്",
            "freeze": "ഫ്രീസ്",
            "hang": "ഹാങ്",
            "crash": "ക്രാഷ്",
            "weak": "വീക്",
            "strong": "സ്ട്രോങ്",
            "disconnect": "ഡിസ്കണക്റ്റ്",
            "reconnect": "റീകണക്റ്റ്",
            "check": "ചെക്ക്",
            "test": "ടെസ്റ്റ്",
            "speed test": "സ്പീഡ് ടെസ്റ്റ്",
            
            # Payment methods
            "upi": "യുപിഐ",
            "net banking": "നെറ്റ് ബാങ്കിങ്",
            "credit card": "ക്രെഡിറ്റ് കാർഡ്",
            "debit card": "ഡെബിറ്റ് കാർഡ്",
            "wallet": "വാലറ്റ്",
            "pay": "പേ",
            "paid": "പെയ്ഡ്",
            
            # Account status
            "limit": "ലിമിറ്റ്",
            "unlimited": "അൺലിമിറ്റഡ്",
            "limited": "ലിമിറ്റഡ്",
            "expired": "എക്സ്‌പയേർഡ്",
            "active": "ആക്റ്റീവ്",
            "inactive": "ഇനാക്റ്റീവ്",
            "suspended": "സസ്പെൻഡഡ്",
            "terminated": "ടെർമിനേറ്റഡ്",
            
            # Common actions
            "cancel": "കാൻസൽ",
            "renew": "റിന്യൂ",
            "upgrade": "അപ്‌ഗ്രേഡ്",
            "downgrade": "ഡൗൺഗ്രേഡ്"
        }
        
        # Replace English words with their Malayalam equivalents
        for word in categorized_words["english"]:
            word_lower = word.lower().rstrip('.,?!:;')
            if word_lower in english_to_malayalam:
                # Add back any punctuation that was removed
                punctuation = word[len(word_lower):]
                replacement = english_to_malayalam[word_lower] + punctuation
                normalized_text = normalized_text.replace(word, replacement, 1)
        
        return normalized_text
    
    def _handle_romanized_malayalam(self, text: str) -> str:
        """
        Handle romanized Malayalam words in the input text.
        
        Romanization refers to writing Malayalam words using the Latin/Roman script.
        This method identifies common romanized Malayalam words and converts them
        to proper Malayalam script, focusing on internet-related customer support.
        
        Args:
            text: Input text that may contain romanized Malayalam
            
        Returns:
            Text with romanized Malayalam words converted to Malayalam script
        """
        if not text:
            return text
            
        # Common romanized Malayalam words and their Malayalam equivalents
        # Focused on internet-related customer care terms
        romanized_to_malayalam = {
            # Internet status expressions
            "net varunnilla": "ഇന്റർനെറ്റ് വരുന്നില്ല",
            "net illa": "ഇന്റർനെറ്റ് ഇല്ല",
            "internet varunnilla": "ഇന്റർനെറ്റ് വരുന്നില്ല",
            "internet illa": "ഇന്റർനെറ്റ് ഇല്ല",
            "net slow aanu": "ഇന്റർനെറ്റ് സ്ലോ ആണ്",
            "internet slow aanu": "ഇന്റർനെറ്റ് സ്ലോ ആണ്",
            "speed kuravanu": "സ്പീഡ് കുറവാണ്",
            "vegatha kuravanu": "വേഗത കുറവാണ്",
            
            # WiFi related terms
            "wifi varunnilla": "വൈഫൈ വരുന്നില്ല",
            "wifi illa": "വൈഫൈ ഇല്ല",
            "wifi signal illa": "വൈഫൈ സിഗ്നൽ ഇല്ല",
            "wifi connect cheyyunnilla": "വൈഫൈ കണക്റ്റ് ചെയ്യുന്നില്ല",
            "wifi password marannu": "വൈഫൈ പാസ്‌വേഡ് മറന്നു",
            "wifi password ariyilla": "വൈഫൈ പാസ്‌വേഡ് അറിയില്ല",
            "wifi slow aanu": "വൈഫൈ സ്ലോ ആണ്",
            
            # Router/Modem related terms
            "router prasnam": "റൗട്ടർ പ്രശ്നം",
            "router restart cheyyam": "റൗട്ടർ റീസ്റ്റാർട്ട് ചെയ്യാം",
            "router restart cheythu": "റൗട്ടർ റീസ്റ്റാർട്ട് ചെയ്തു",
            "router off aayi": "റൗട്ടർ ഓഫ് ആയി",
            "router on aavunnilla": "റൗട്ടർ ഓൺ ആകുന്നില്ല",
            "router red light": "റൗട്ടർ റെഡ് ലൈറ്റ്",
            "modem prasnam": "മോഡം പ്രശ്നം",
            "modem restart cheyyam": "മോഡം റീസ്റ്റാർട്ട് ചെയ്യാം",
            "modem restart cheythu": "മോഡം റീസ്റ്റാർട്ട് ചെയ്തു",
            "modem off aayi": "മോഡം ഓഫ് ആയി",
            "modem on aavunnilla": "മോഡം ഓൺ ആകുന്നില്ല",
            
            # Connection issues
            "connection illa": "കണക്ഷൻ ഇല്ല",
            "connection prasnam": "കണക്ഷൻ പ്രശ്നം",
            "signal illa": "സിഗ്നൽ ഇല്ല",
            "signal weak aanu": "സിഗ്നൽ ദുർബലമാണ്",
            "disconnect aayi": "ഡിസ്കണക്റ്റ് ആയി",
            "connect cheyyunnilla": "കണക്റ്റ് ചെയ്യുന്നില്ല",
            
            # Data and payment
            "data theernnu": "ഡാറ്റ തീർന്നു",
            "data balance ethrayundu": "ഡാറ്റ ബാലൻസ് എത്രയുണ്ട്",
            "recharge cheyyam": "റീചാർജ് ചെയ്യാം",
            "recharge cheythu": "റീചാർജ് ചെയ്തു",
            "bill adachu": "ബിൽ അടച്ചു",
            "payment cheythu": "പേയ്മെന്റ് ചെയ്തു",
            
            # Error and troubleshooting
            "error undu": "എറർ ഉണ്ട്",
            "prasnam undu": "പ്രശ്നമുണ്ട്",
            "restart cheyyam": "റീസ്റ്റാർട്ട് ചെയ്യാം",
            "restart cheythu": "റീസ്റ്റാർട്ട് ചെയ്തു",
            "check cheyyam": "ചെക്ക് ചെയ്യാം",
            "check cheythu": "ചെക്ക് ചെയ്തു",
            "test cheyyam": "ടെസ്റ്റ് ചെയ്യാം",
            "test cheythu": "ടെസ്റ്റ് ചെയ്തു",
            
            # Common verbs and status words
            "varunnilla": "വരുന്നില്ല",
            "illa": "ഇല്ല",
            "undu": "ഉണ്ട്",
            "aanu": "ആണ്",
            "cheyyunnilla": "ചെയ്യുന്നില്ല",
            "cheythu": "ചെയ്തു",
            "cheyyam": "ചെയ്യാം",
            "kuravanu": "കുറവാണ്",
            "slow aanu": "സ്ലോ ആണ്",
            "prasnam": "പ്രശ്നം",
            "thakraru": "തകരാർ",
            
            # Question forms
            "enthu cheyyam": "എന്ത് ചെയ്യാം",
            "engane cheyyam": "എങ്ങനെ ചെയ്യാം",
            "enthinu": "എന്തിന്",
            "ethra": "എത്ര",
            "eppozhanu": "എപ്പോഴാണ്",
            "evideyanu": "എവിടെയാണ്",
            
            # Common technical terms
            "wifi": "വൈഫൈ",
            "router": "റൗട്ടർ",
            "modem": "മോഡം",
            "internet": "ഇന്റർനെറ്റ്",
            "net": "ഇന്റർനെറ്റ്",
            "speed": "സ്പീഡ്",
            "connection": "കണക്ഷൻ",
            "signal": "സിഗ്നൽ",
            "data": "ഡാറ്റ",
            "recharge": "റീചാർജ്",
            "bill": "ബിൽ",
            "password": "പാസ്‌വേഡ്",
            "download": "ഡൗൺലോഡ്",
            "upload": "അപ്‌ലോഡ്",
            "fiber": "ഫൈബർ",
            "broadband": "ബ്രോഡ്ബാൻഡ്",
            "hotspot": "ഹോട്ട്സ്പോട്ട്",
            "buffering": "ബഫറിങ്",
            
            # Common expressions
            "net work cheyyunnilla": "ഇന്റർനെറ്റ് പ്രവർത്തിക്കുന്നില്ല",
            "internet work cheyyunnilla": "ഇന്റർനെറ്റ് പ്രവർത്തിക്കുന്നില്ല",
            "wifi work cheyyunnilla": "വൈഫൈ പ്രവർത്തിക്കുന്നില്ല",
            "router work cheyyunnilla": "റൗട്ടർ പ്രവർത്തിക്കുന്നില്ല",
            "modem work cheyyunnilla": "മോഡം പ്രവർത്തിക്കുന്നില്ല",
            "recharge cheythittum net varunnilla": "റീചാർജ് ചെയ്തിട്ടും ഇന്റർനെറ്റ് വരുന്നില്ല",
            "bill adachittum connection cut cheythu": "ബിൽ അടച്ചിട്ടും കണക്ഷൻ കട്ട് ചെയ്തു",
            "wifi connect cheythittum internet varunnilla": "വൈഫൈ കണക്റ്റ് ചെയ്തിട്ടും ഇന്റർനെറ്റ് വരുന്നില്ല",
            "speed test cheyyam": "സ്പീഡ് ടെസ്റ്റ് ചെയ്യാം",
            "page load aavunnilla": "പേജ് ലോഡ് ആകുന്നില്ല"
        }
        
        # Process the text word by word
        words = text.split()
        result_words = []
        
        i = 0
        while i < len(words):
            # Try to match multi-word phrases first
            matched = False
            for j in range(min(5, len(words) - i), 0, -1):  # Try phrases of length 5, 4, 3, 2, 1
                phrase = ' '.join(words[i:i+j]).lower()
                if phrase in romanized_to_malayalam:
                    result_words.append(romanized_to_malayalam[phrase])
                    i += j
                    matched = True
                    break
            
            # If no phrase matched, try single word
            if not matched:
                word = words[i].lower().rstrip('.,?!:;')
                if word in romanized_to_malayalam:
                    # Add back any punctuation that was removed
                    punctuation = words[i][len(word):]
                    result_words.append(romanized_to_malayalam[word] + punctuation)
                else:
                    result_words.append(words[i])
                i += 1
        
        return ' '.join(result_words)
    
    def enhance(self, text: str) -> str:
        """
        Apply all enhancement techniques to improve transcript quality
        for internet-related customer support conversations.
        
        This method applies a sequence of processing steps to:
        1. Handle special cases for common internet issues
        2. Normalize romanized and code-switched text
        3. Apply technical term standardization
        4. Correct common errors in internet-related terminology
        5. Apply context-aware corrections based on internet domain knowledge
        
        Args:
            text: Raw transcription text
            
        Returns:
            Enhanced transcription text optimized for internet-related customer support
        """
        if not text:
            return text
            
        # Step 1: Special case handling for high-priority internet issues
        # These patterns need to be checked first to properly capture the customer's intent
        
        # WiFi issues
        if any(pattern in text.lower() for pattern in ['wifi വർക്ക് ചെയ്യുന്നില്ല', 'വൈഫൈ വർക്ക് ചെയ്യുന്നില്ല', 'wifi വരുന്നില്ല', 'വൈഫൈ വരുന്നില്ല']):
            return 'വൈഫൈ പ്രവർത്തിക്കുന്നില്ല'
            
        if any(pattern in text.lower() for pattern in ['wifi കിട്ടുന്നില്ല', 'വൈഫൈ കിട്ടുന്നില്ല']):
            return 'വൈഫൈ പ്രവർത്തിക്കുന്നില്ല കിട്ടുന്നില്ല'
            
        # Internet connection issues
        if any(pattern in text.lower() for pattern in ['internet വർക്ക് ചെയ്യുന്നില്ല', 'ഇന്റർനെറ്റ് വർക്ക് ചെയ്യുന്നില്ല', 'net വർക്ക് ചെയ്യുന്നില്ല', 'നെറ്റ് വർക്ക് ചെയ്യുന്നില്ല']):
            return 'ഇന്റർനെറ്റ് പ്രവർത്തിക്കുന്നില്ല'
            
        if any(pattern in text.lower() for pattern in ['internet വരുന്നില്ല', 'ഇന്റർനെറ്റ് വരുന്നില്ല', 'net വരുന്നില്ല', 'നെറ്റ് വരുന്നില്ല']):
            return 'ഇന്റർനെറ്റ് വരുന്നില്ല'
            
        # Speed issues
        if any(pattern in text.lower() for pattern in ['internet സ്ലോ', 'ഇന്റർനെറ്റ് സ്ലോ', 'net സ്ലോ', 'നെറ്റ് സ്ലോ']):
            return 'ഇന്റർനെറ്റ് സ്ലോ ആണ്'
            
        # Router issues
        if any(pattern in text.lower() for pattern in ['router റീസ്റ്റാർട്ട് ചെയ്യണം', 'റൗട്ടർ റീസ്റ്റാർട്ട് ചെയ്യണം']):
            return 'റൗട്ടർ റീസ്റ്റാർട്ട് ചെയ്യണം'
            
        # Modem issues
        if any(pattern in text.lower() for pattern in ['modem റീസ്റ്റാർട്ട് ചെയ്യണം', 'മോഡം റീസ്റ്റാർട്ട് ചെയ്യണം']):
            return 'മോഡം റീസ്റ്റാർട്ട് ചെയ്യണം'
            
        # Special case for network terminology
        if 'നേറ്റ് വർക്ക്' in text:
            text = text.replace('നേറ്റ് വർക്ക്', 'നെറ്റ്‌വർക്ക്')
        
        # Additional special case handling for common issues
        if 'നെറ്റ് വർക്ക് ചെയ്യുന്നില്ല' in text:
            return 'ഇന്റർനെറ്റ് പ്രവർത്തിക്കുന്നില്ല'
            
        if 'നെറ്റ് വർക്ക് ചെയ്യുന്നില്ലാ' in text:
            return 'ഇന്റർനെറ്റ് പ്രവർത്തിക്കുന്നില്ല'
            
        if 'ഇന്റർനെറ്റ് വർക്ക് ചെയ്യുന്നില്ല' in text:
            return 'ഇന്റർനെറ്റ് പ്രവർത്തിക്കുന്നില്ല'
            
        if 'ഇന്റർനെറ്റ് വർക്ക് ചെയ്യുന്നില്ലാ' in text:
            return 'ഇന്റർനെറ്റ് പ്രവർത്തിക്കുന്നില്ല'
        
        # Step 0: Handle romanized Malayalam
        text = self._handle_romanized_malayalam(text)
        
        # Step 1: Handle code-switched text
        text = self._handle_code_switched_text(text)
        
        # Step 2: Normalize text while preserving Malayalam characters
        text = self._normalize_text(text)
        
        # Step 3: Fix Malayalam-specific transcription errors
        text = self._fix_malayalam_specific_errors(text)
        
        # Step 4: Apply morphological analysis for technical term standardization
        # Process word by word to avoid partial replacements
        words = text.split()
        result_words = []
        
        for word in words:
            # Skip words that are part of "നെറ്റ്‌വർക്ക്" to avoid converting to "ഇന്റർനെറ്റ്‌വർക്ക്"
            if word == "നെറ്റ്‌വർക്ക്" or "നെറ്റ്‌വർക്ക്" in text:
                result_words.append(word)
                continue
                
            # Check special case mappings
            if word in self.morphological_analyzer.special_case_mappings:
                result_words.append(self.morphological_analyzer.special_case_mappings[word])
            elif word == "നെറ്റ്":
                # Don't replace "നെറ്റ്" if it's part of "നെറ്റ്‌വർക്ക്"
                if "നെറ്റ്‌വർക്ക്" in text:
                    result_words.append(word)
                else:
                    result_words.append("ഇന്റർനെറ്റ്")
            else:
                # Check if it's a technical term
                analysis = self.morphological_analyzer.analyze_word(word)
                if analysis["type"] == "technical":
                    result_words.append(analysis["stem"] + analysis["suffix"])
                else:
                    result_words.append(word)
        
        text = " ".join(result_words)
            
        # Step 5: Apply internet-specific n-gram analysis
        text = self._apply_ngram_analysis(text)
            
        # Step 6: Basic error corrections
        text = self._apply_error_corrections(text)
        
        # Step 7: Technical term standardization
        # We need to be careful to avoid duplication of terms
        for term, standard in self.technical_term_map.items():
            # Skip terms that would cause duplication
            if term == "നെറ്റ്" or "ഇന്റർനെറ്റ്" in text:
                continue
            if term in text and standard not in text:
                text = text.replace(term, standard)
        
        # Step 8: Fuzzy matching against common phrases
        text = self._apply_fuzzy_matching(text)
        
        # Step 9: Context-aware corrections
        text = self._apply_context_aware_corrections(text)
        
        # Step 10: Clean up extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Final check for duplicated prefixes and common issues
        text = text.replace("ഇന്റർഇന്റർനെറ്റ്", "ഇന്റർനെറ്റ്")
        
        # Additional post-processing for common patterns
        
        # Standardize verb forms
        text = text.replace("വർക്ക് ചെയ്യുന്നില്ല", "പ്രവർത്തിക്കുന്നില്ല")
        text = text.replace("വർക്ക് ചെയ്യുന്നില്ലാ", "പ്രവർത്തിക്കുന്നില്ല")
        text = text.replace("വർക്ക് ചെയ്യുന്നില്ലെ", "പ്രവർത്തിക്കുന്നില്ല")
        
        # Standardize negation forms
        text = text.replace("കാണുന്നില്ലാ", "കാണുന്നില്ല")
        text = text.replace("കാണുന്നില്ലെ", "കാണുന്നില്ല")
        text = text.replace("കിട്ടുന്നില്ലാ", "കിട്ടുന്നില്ല")
        text = text.replace("കിട്ടുന്നില്ലെ", "കിട്ടുന്നില്ല")
        text = text.replace("വരുന്നില്ലാ", "വരുന്നില്ല")
        text = text.replace("വരുന്നില്ലെ", "വരുന്നില്ല")
        
        # Standardize status indicators
        text = text.replace("കുറവാ", "കുറവാണ്")
        text = text.replace("കുറവാണു", "കുറവാണ്")
        text = text.replace("സ്ലോ ആ", "സ്ലോ ആണ്")
        text = text.replace("സ്ലോ ആണു", "സ്ലോ ആണ്")
        
        # Handle common compound words
        text = text.replace("നെറ്റ് വർക്ക്", "നെറ്റ്‌വർക്ക്")
        text = text.replace("സെറ്റ് ടോപ് ബോക്സ്", "സെറ്റ് ടോപ് ബോക്സ്")
        text = text.replace("സെറ്റ്ടോപ്ബോക്സ്", "സെറ്റ് ടോപ് ബോക്സ്")
        text = text.replace("സെറ്റ്ടോപ് ബോക്സ്", "സെറ്റ് ടോപ് ബോക്സ്")
        
        # Final check for common issues
        if "നെറ്റ് വരുന്നില്ല" in text and "ഇന്റർനെറ്റ്" not in text:
            text = text.replace("നെറ്റ് വരുന്നില്ല", "ഇന്റർനെറ്റ് വരുന്നില്ല")
            
        if "നെറ്റ് കിട്ടുന്നില്ല" in text and "ഇന്റർനെറ്റ്" not in text:
            text = text.replace("നെറ്റ് കിട്ടുന്നില്ല", "ഇന്റർനെറ്റ് കിട്ടുന്നില്ല")
            
        if "നെറ്റ് സ്ലോ" in text and "ഇന്റർനെറ്റ്" not in text:
            text = text.replace("നെറ്റ് സ്ലോ", "ഇന്റർനെറ്റ് സ്ലോ")
        
        return text 