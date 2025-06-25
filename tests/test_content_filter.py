"""
Test script for content filtering functionality
"""

import re
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def is_inappropriate_content(text: str) -> bool:
    """Check if text contains inappropriate content"""
    # List of inappropriate words or patterns to check for
    inappropriate_patterns = [
        r'സെക്സ്',  # No word boundary for non-Latin scripts
        r'\bsex\b',
        r'\bporn\b',
        r'\bxxx\b',
        # Add more patterns as needed
    ]
    
    # Convert to lowercase for case-insensitive matching
    text_lower = text.lower()
    
    # Check each pattern
    for pattern in inappropriate_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            # Log to warning
            logger.warning(f"Detected inappropriate content, filtered: {pattern}")
            
            # Log to separate file for monitoring
            try:
                # Create logs directory if it doesn't exist
                os.makedirs("logs", exist_ok=True)
                
                with open("logs/content_filter.log", "a", encoding="utf-8") as f:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"{timestamp} | Call: test | Phone: test | Filtered: {text}\n")
            except Exception as e:
                logger.error(f"Error logging to content filter log: {e}")
            
            return True
    
    return False

def filter_text(text: str) -> str:
    """Filter inappropriate content from text"""
    # List of inappropriate words to replace
    inappropriate_words = ["സെക്സ്", "sex", "porn", "xxx"]
    
    # Replace inappropriate words
    for word in inappropriate_words:
        text = text.replace(word, "[filtered]")
    
    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def test_filtering():
    """Test content filtering functionality"""
    test_cases = [
        "ഹലോ എന്റെ പേര് രാജേഷ്",  # Hello my name is Rajesh
        "എന്റെ ടിവി സിഗ്നൽ പോയി",  # My TV signal is gone
        "സെക്സ്",  # The problematic word
        "ഞാൻ sex എന്ന് പറഞ്ഞിട്ടില്ല",  # I didn't say sex
        "porn വെബ്സൈറ്റ്",  # porn website
        "xxx വീഡിയോ",  # xxx video
    ]
    
    print("\n=== CONTENT FILTER TEST ===\n")
    
    for i, test in enumerate(test_cases):
        print(f"Test {i+1}: \"{test}\"")
        
        # Check if inappropriate
        is_inappropriate = is_inappropriate_content(test)
        print(f"  Is inappropriate: {is_inappropriate}")
        
        # Filter text
        filtered = filter_text(test)
        print(f"  Filtered result: \"{filtered}\"")
        
        print("")

if __name__ == "__main__":
    test_filtering() 