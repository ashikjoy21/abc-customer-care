import os
import sys
import logging
from utils import TranscriptEnhancer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_transcript_enhancer():
    """Test the TranscriptEnhancer with various examples"""
    
    # Initialize the enhancer
    common_phrases_path = os.path.join(os.path.dirname(__file__), "data", "common_phrases.txt")
    enhancer = TranscriptEnhancer(common_phrases_file=common_phrases_path)
    
    # Test cases - pairs of (original, expected) texts
    test_cases = [
        # Inappropriate content misinterpretation
        ("സെക്സ് റൗട്ടർ", "ചെക്ക് റൗട്ടർ"),
        
        # Technical term variations
        ("റീചാർജ്ജ് ചെയ്തു", "റീചാർജ് ചെയ്തു"),
        ("സിഗ്നല്‍ ഇല്ല", "സിഗ്നൽ ഇല്ല"),
        
        # Common word variations
        ("കണക്ഷന്‍ പോയി", "കണക്ഷൻ പോയി"),
        ("നേറ്റ് വർക്ക് കുറവാണ്", "ഇന്റർനെറ്റ്‌വർക്ക് കുറവാണ്"),
        
        # Multiple corrections
        ("സെക്സ് റീചാർജ്ജ് ചെയ്തിട്ടും സിഗ്നല്‍ ഇല്ല", "ചെക്ക് റീചാർജ് ചെയ്തിട്ടും സിഗ്നൽ ഇല്ല")
    ]
    
    # Test with conversation context
    conversation_history = [
        {"user": "മോഡം റീസ്റ്റാർട്ട് ചെയ്തു", "bot": "മോഡം റീസ്റ്റാർട്ട് ചെയ്തിട്ടും പ്രശ്നം തീരുന്നില്ലേ?"},
        {"user": "റെഡ് ലൈറ്റ് കാണിക്കുന്നു", "bot": "റെഡ് ലൈറ്റ് കാണുന്നുണ്ടെങ്കിൽ..."}
    ]
    
    # Update context
    enhancer.update_context(conversation_history)
    
    # Test with context
    context_test_cases = [
        # Should correct to proper technical terms based on context
        ("റെഡി ലൈറ്റ് മിന്നുന്നു", "റെഡ് ലൈറ്റ് മിന്നുന്നു"),
        ("മോടം റീസ്റ്റർട്ട് ചെയ്തു", "മോഡം റീസ്റ്റാർട്ട് ചെയ്തു")
    ]
    
    # Run basic tests
    print("\n=== Basic Enhancement Tests ===\n", flush=True)
    
    all_passed = True
    
    for original, expected in test_cases:
        enhanced = enhancer.enhance(original)
        passed = enhanced == expected
        all_passed = all_passed and passed
        result = "✅ PASS" if passed else f"❌ FAIL (got '{enhanced}')"
        print(f"Original : {original}", flush=True)
        print(f"Enhanced : {enhanced}", flush=True)
        print(f"Expected : {expected}", flush=True)
        print(f"Result   : {result}", flush=True)
        print("", flush=True)
    
    # Run context-aware tests
    print("\n=== Context-Aware Enhancement Tests ===\n", flush=True)
    
    for original, expected in context_test_cases:
        enhanced = enhancer.enhance(original)
        passed = enhanced == expected
        all_passed = all_passed and passed
        result = "✅ PASS" if passed else f"❌ FAIL (got '{enhanced}')"
        print(f"Original : {original}", flush=True)
        print(f"Enhanced : {enhanced}", flush=True)
        print(f"Expected : {expected}", flush=True)
        print(f"Result   : {result}", flush=True)
        print("", flush=True)
    
    # Test with real conversation example from logs
    print("\n=== Real Example from Logs ===\n", flush=True)
    
    real_example = "അവിടെ ചന്ദ്രിക കാണുന്നില്ല എലൈറ്റ് ആണല്ലോ"
    enhanced_real = enhancer.enhance(real_example)
    expected_real = "അവിടെ ചാനൽ കാണുന്നില്ല ഡിഷ് ലൈറ്റ് ആണല്ലോ"
    passed = enhanced_real == expected_real
    all_passed = all_passed and passed
    result = "✅ PASS" if passed else f"❌ FAIL (got '{enhanced_real}')"
    
    print(f"Original : {real_example}", flush=True)
    print(f"Enhanced : {enhanced_real}", flush=True)
    print(f"Expected : {expected_real}", flush=True)
    print(f"Result   : {result}", flush=True)
    print("", flush=True)
    
    # Print overall result
    print("\n=== Overall Result ===\n", flush=True)
    print(f"All tests passed: {'✅ Yes' if all_passed else '❌ No'}", flush=True)
    
    return all_passed

if __name__ == "__main__":
    success = test_transcript_enhancer()
    sys.exit(0 if success else 1) 