import re
import logging
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class IssueClassificationResult:
    """Result of issue classification"""
    issue_type: str
    confidence: float
    sub_issues: List[str] = field(default_factory=list)
    metadata: Dict[str, any] = field(default_factory=dict)

class IssueClassifier:
    """Advanced issue classifier using keyword analysis and contextual understanding"""
    
    def __init__(self):
        """Initialize the issue classifier with predefined issue types and keywords"""
        # Main issue types with their Malayalam and English keywords
        self.issue_types = {
            "internet_down": {
                "keywords": [
                    "നെറ്റ് കിട്ടുന്നില്ല", "ഇന്റർനെറ്റ് ഇല്ല", "കണക്ഷൻ പോയി", 
                    "internet not working", "no connection", "no internet",
                    "ഇന്റർനെറ്റ് പ്രവർത്തിക്കുന്നില്ല", "നെറ്റ് പോയി", "കണക്റ്റിവിറ്റി ഇല്ല",
                    "offline", "disconnected", "red light", "ചുവന്ന ലൈറ്റ്", "റെഡ് ലൈറ്റ്", 
                    "los", "loss", "los light", "fiber cut", "ഫൈബർ കട്ട്", "fiber break",
                    "ഫൈബർ ബ്രേക്ക്", "signal lost", "സിഗ്നൽ ഇല്ല"
                ],
                "weight": 1.0
            },
            "slow_internet": {
                "keywords": [
                    "വേഗത കുറവ്", "സ്ലോ", "പതുക്കെ", "slow", "buffering", 
                    "lagging", "speed", "മന്ദഗതി", "താമസം", "delay",
                    "loading takes time", "ലോഡിംഗ് സമയമെടുക്കുന്നു", "വേഗത കുറഞ്ഞു"
                ],
                "weight": 0.9
            },
            "wifi_issues": {
                "keywords": [
                    "വൈഫൈ", "wifi", "wireless", "password", "പാസ്‌വേഡ്",
                    "signal", "range", "സിഗ്നൽ", "റേഞ്ച്", "router", "റൗട്ടർ",
                    "devices not connecting", "ഉപകരണങ്ങൾ കണക്റ്റ് ചെയ്യുന്നില്ല",
                    "ssid", "network name", "നെറ്റ്‌വർക്ക് പേര്"
                ],
                "weight": 0.8
            },
            "tv_issues": {
                "keywords": [
                    "ടിവി", "ചാനൽ", "tv", "channel", "സെറ്റ് ടോപ് ബോക്സ്", "set top box",
                    "screen", "display", "സ്ക്രീൻ", "ഡിസ്പ്ലേ", "remote", "റിമോട്ട്",
                    "no signal", "സിഗ്നൽ ഇല്ല", "channels missing", "ചാനലുകൾ കാണുന്നില്ല"
                ],
                "weight": 0.7
            },
            "billing_issues": {
                "keywords": [
                    "ബിൽ", "bill", "payment", "പേയ്മെന്റ്", "recharge", "റീചാർജ്",
                    "overcharged", "അധിക ചാർജ്", "due date", "തീയതി", "amount",
                    "തുക", "plan", "പ്ലാൻ", "subscription", "സബ്സ്ക്രിപ്ഷൻ"
                ],
                "weight": 0.6
            }
        }
        
        # Sub-issues for each main issue type
        self.sub_issues = {
            "internet_down": [
                "modem_issue", "cable_issue", "account_suspended", "area_outage", "fiber_cut"
            ],
            "slow_internet": [
                "peak_hours", "device_issue", "wifi_interference", "plan_limitation"
            ],
            "wifi_issues": [
                "password_forgotten", "range_issue", "device_compatibility", "router_configuration"
            ],
            "tv_issues": [
                "stb_issue", "channel_subscription", "signal_issue", "remote_issue"
            ],
            "billing_issues": [
                "payment_not_reflected", "wrong_amount", "plan_change", "discount_missing"
            ]
        }
        
        # Contextual indicators for sub-issues
        self.sub_issue_indicators = {
            "modem_issue": [
                "light", "blinking", "ലൈറ്റ്", "മിന്നുന്നു", "power", "പവർ", "restart", "റീസ്റ്റാർട്ട്"
            ],
            "cable_issue": [
                "cable", "കേബിൾ", "wire", "വയർ", "cut", "മുറിച്ചു", "damaged", "കേടായി", "loose", "അയഞ്ഞു"
            ],
            "fiber_cut": [
                "red light", "ചുവന്ന ലൈറ്റ്", "റെഡ് ലൈറ്റ്", "los", "loss", "los light", "fiber cut", "ഫൈബർ കട്ട്",
                "fiber break", "ഫൈബർ ബ്രേക്ക്", "signal lost", "സിഗ്നൽ ഇല്ല"
            ],
            "area_outage": [
                "area", "പ്രദേശം", "neighborhood", "അയൽപക്കം", "everyone", "എല്ലാവർക്കും", "outage", "തകരാർ"
            ],
            "peak_hours": [
                "evening", "വൈകുന്നേരം", "night", "രാത്രി", "busy", "തിരക്ക്", "specific time", "പ്രത്യേക സമയം"
            ],
            "wifi_interference": [
                "walls", "ചുമരുകൾ", "distance", "ദൂരം", "devices", "ഉപകരണങ്ങൾ", "microwave", "മൈക്രോവേവ്"
            ]
        }
        
        # Technical terms and their weights
        self.technical_terms = {
            "modem": 1.2, "router": 1.2, "fiber": 1.1, "ethernet": 1.1, "wireless": 1.0,
            "ip address": 1.3, "dns": 1.3, "gateway": 1.2, "bandwidth": 1.1, "signal": 1.0,
            "മോഡം": 1.2, "റൗട്ടർ": 1.2, "ഫൈബർ": 1.1, "എതർനെറ്റ്": 1.1, "വയർലെസ്": 1.0
        }
        
        # Initialize pattern cache
        self._pattern_cache: Dict[str, re.Pattern] = {}
    
    def _get_pattern(self, keyword: str) -> re.Pattern:
        """Get or create a compiled regex pattern for a keyword"""
        if keyword not in self._pattern_cache:
            # Create case-insensitive pattern that matches word boundaries
            self._pattern_cache[keyword] = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
        return self._pattern_cache[keyword]
    
    def _count_keyword_matches(self, text: str, keywords: List[str]) -> int:
        """Count how many keywords from the list appear in the text"""
        return sum(1 for keyword in keywords if self._get_pattern(keyword).search(text))
    
    def _calculate_weighted_score(self, text: str, issue_data: Dict) -> float:
        """Calculate weighted score for an issue type based on keyword matches"""
        keywords = issue_data["keywords"]
        weight = issue_data["weight"]
        
        # Count keyword matches
        matches = self._count_keyword_matches(text, keywords)
        
        # Apply weight
        return matches * weight
    
    def _detect_sub_issues(self, text: str, main_issue: str) -> List[str]:
        """Detect sub-issues for a main issue type"""
        if main_issue not in self.sub_issues:
            return []
            
        detected_sub_issues = []
        
        # Check each sub-issue for this main issue
        for sub_issue in self.sub_issues[main_issue]:
            # If we have indicators for this sub-issue, check them
            if sub_issue in self.sub_issue_indicators:
                indicators = self.sub_issue_indicators[sub_issue]
                if self._count_keyword_matches(text, indicators) > 0:
                    detected_sub_issues.append(sub_issue)
        
        return detected_sub_issues
    
    def _extract_technical_context(self, text: str) -> Dict[str, any]:
        """Extract technical context from text"""
        context = {}
        
        # Check for technical terms
        for term, weight in self.technical_terms.items():
            if self._get_pattern(term).search(text):
                context[f"has_{term.replace(' ', '_')}"] = True
        
        # Extract potential numeric values (e.g., speeds, error codes)
        speed_match = re.search(r'(\d+)\s*(mbps|kbps|gbps)', text, re.IGNORECASE)
        if speed_match:
            context["mentioned_speed"] = {
                "value": int(speed_match.group(1)),
                "unit": speed_match.group(2).lower()
            }
        
        # Extract error codes
        error_match = re.search(r'error\s+code\s*:?\s*([a-z0-9\-]+)', text, re.IGNORECASE)
        if error_match:
            context["error_code"] = error_match.group(1)
        
        return context
    
    def classify(self, text: str, conversation_history: List[Dict[str, str]] = None) -> IssueClassificationResult:
        """Classify the issue based on text and conversation history"""
        # Combine current text with recent conversation history if available
        text_to_analyze = text.lower()
        if conversation_history:
            for entry in conversation_history[-3:]:  # Last 3 exchanges
                if "user" in entry and entry["user"]:
                    text_to_analyze += " " + entry["user"].lower()
        
        # Special case: Immediately detect adapter/power issue
        no_power_indicators = ["no light", "no power", "ലൈറ്റ് ഇല്ല", "ലൈറ്റ് വരുന്നില്ല", "പവർ ഇല്ല", 
                             "ഓൺ ആകുന്നില്ല", "not turning on", "won't turn on", "dead", "adapter", "അഡാപ്റ്റർ"]
        if any(indicator in text_to_analyze for indicator in no_power_indicators):
            logger.info("No power/adapter issue detected - immediately classifying as hardware issue")
            # Return hardware_issue with adapter_issue sub-issue and high confidence
            return IssueClassificationResult(
                issue_type="hardware_issue",
                confidence=0.99,
                sub_issues=["adapter_issue"],
                metadata={
                    "is_power_issue": True,
                    "needs_technician": True,
                    "adapter_problem": True,
                    "technician_needs_adapter": True
                }
            )
        
        # Special case: Immediately detect red light as fiber cut
        red_light_indicators = ["red light", "ചുവന്ന ലൈറ്റ്", "റെഡ് ലൈറ്റ്", "los", "loss", "los light", "red", "ചുവന്ന", "ചുവപ്പ്"]
        if any(indicator in text_to_analyze for indicator in red_light_indicators):
            logger.info("Red light detected - immediately classifying as fiber cut issue")
            # Return internet_down with fiber_cut sub-issue and high confidence
            return IssueClassificationResult(
                issue_type="internet_down",
                confidence=0.99,
                sub_issues=["fiber_cut"],
                metadata={
                    "is_red_light": True,
                    "needs_technician": True,
                    "urgent": True,
                    "restart_first": True,
                    "skip_further_troubleshooting": True
                }
            )
        
        # Calculate scores for each issue type
        scores = {}
        for issue_type, issue_data in self.issue_types.items():
            scores[issue_type] = self._calculate_weighted_score(text_to_analyze, issue_data)
        
        # Find the issue type with the highest score
        if not scores or max(scores.values()) == 0:
            # Default to internet_down if no matches
            best_issue = "internet_down"
            confidence = 0.5
        else:
            best_issue = max(scores.items(), key=lambda x: x[1])[0]
            # Normalize confidence (0.5-1.0 range)
            total_score = sum(scores.values())
            confidence = 0.5 + (0.5 * (scores[best_issue] / total_score)) if total_score > 0 else 0.5
        
        # Detect sub-issues
        sub_issues = self._detect_sub_issues(text_to_analyze, best_issue)
        
        # Extract technical context
        metadata = self._extract_technical_context(text_to_analyze)
        
        # Add confidence and scores to metadata
        metadata["confidence"] = confidence
        metadata["scores"] = scores
        
        logger.info(f"Classified issue as '{best_issue}' with confidence {confidence:.2f}")
        if sub_issues:
            logger.info(f"Detected sub-issues: {sub_issues}")
        
        return IssueClassificationResult(
            issue_type=best_issue,
            confidence=confidence,
            sub_issues=sub_issues,
            metadata=metadata
        ) 