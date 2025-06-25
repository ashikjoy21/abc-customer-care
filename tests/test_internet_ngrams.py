import os
import sys
import logging
from utils import TranscriptEnhancer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_internet_ngram_analysis():
    """Test the N-gram analysis for internet-related issues"""
    
    # Initialize the enhancer
    common_phrases_path = os.path.join(os.path.dirname(__file__), "..", "data", "common_phrases.txt")
    enhancer = TranscriptEnhancer(common_phrases_file=common_phrases_path)
    
    # Test cases - pairs of (original, expected) texts
    test_cases = [
        # Basic n-gram replacements
        ("നെറ്റ് വരുന്നില്ല", "ഇന്റർനെറ്റ് വരുന്നില്ല"),
        ("നെറ്റ് സ്ലോ", "ഇന്റർനെറ്റ് സ്ലോ ആണ്"),
        
        # Partial n-gram matches
        ("മോഡം റീസ്റ്റർട്ട് ചെയ്തു", "മോഡം റീസ്റ്റാർട്ട് ചെയ്തു"),
        ("നെറ്റ് കണക്റ്റ് ആകുന്നില്ല", "ഇന്റർനെറ്റ് കണക്റ്റ് ആകുന്നില്ല"),
        
        # Context-based corrections
        ("സിഗ്നൽ പോയി", "സിഗ്നൽ ഇല്ല പോയി"),
        ("സ്പീഡ് കുറവ്", "സ്പീഡ് കുറവാണ്"),
        
        # Combined with other corrections
        ("നെറ്റ് സ്ലോ റൗടർ", "ഇന്റർനെറ്റ് സ്ലോ ആണ് റൗട്ടർ"),
        ("സെക്സ് റൗട്ടർ നെറ്റ് വരുന്നില്ല", "ചെക്ക് റൗട്ടർ ഇന്റർനെറ്റ് വരുന്നില്ല"),
    ]
    
    # Run tests
    print("\n=== Internet N-gram Analysis Tests ===\n", flush=True)
    
    all_passed = True
    
    for original, expected in test_cases:
        # Test only the n-gram analysis first
        ngram_only = enhancer._apply_ngram_analysis(original)
        
        # Then test the full enhancement pipeline
        enhanced = enhancer.enhance(original)
        
        # Check if the n-gram analysis is working
        ngram_working = original != ngram_only
        
        # Check if the full enhancement matches expectations
        full_passed = enhanced == expected
        
        all_passed = all_passed and full_passed
        
        result = "✅ PASS" if full_passed else f"❌ FAIL (got '{enhanced}')"
        ngram_result = "✅ Working" if ngram_working else "⚠️ No change"
        
        print(f"Original   : {original}", flush=True)
        print(f"N-gram only: {ngram_only} ({ngram_result})", flush=True)
        print(f"Enhanced   : {enhanced}", flush=True)
        print(f"Expected   : {expected}", flush=True)
        print(f"Result     : {result}", flush=True)
        print("", flush=True)
    
    # Special test cases that need direct handling
    print("\n=== Special Cases ===\n", flush=True)
    
    special_cases = [
        # Cases that need special handling in the code
        ("വൈഫൈ വർക്ക് ചെയ്യുന്നില്ല", "വൈഫൈ പ്രവർത്തിക്കുന്നില്ല"),
        ("വൈഫൈ കിട്ടുന്നില്ല", "വൈഫൈ പ്രവർത്തിക്കുന്നില്ല കിട്ടുന്നില്ല"),
    ]
    
    for original, expected in special_cases:
        # For special cases, we test the full enhancement
        enhanced = enhancer.enhance(original)
        passed = enhanced == expected
        all_passed = all_passed and passed
        result = "✅ PASS" if passed else f"❌ FAIL (got '{enhanced}')"
        
        print(f"Original : {original}", flush=True)
        print(f"Enhanced : {enhanced}", flush=True)
        print(f"Expected : {expected}", flush=True)
        print(f"Result   : {result}", flush=True)
        print("", flush=True)
    
    # Test with real conversation examples from logs
    print("\n=== Real Examples from Logs ===\n", flush=True)
    
    real_examples = [
        ("എന്റെ നെറ്റ് കണക്ഷൻ വളരെ സ്ലോ ആണ്", "എന്റെ ഇന്റർനെറ്റ് കണക്ഷൻ വളരെ സ്ലോ ആണ്"),
    ]
    
    for original, expected in real_examples:
        enhanced = enhancer.enhance(original)
        passed = enhanced == expected
        all_passed = all_passed and passed
        result = "✅ PASS" if passed else f"❌ FAIL (got '{enhanced}')"
        
        print(f"Original : {original}", flush=True)
        print(f"Enhanced : {enhanced}", flush=True)
        print(f"Expected : {expected}", flush=True)
        print(f"Result   : {result}", flush=True)
        print("", flush=True)
    
    # Print overall result
    print("\n=== Overall Result ===\n", flush=True)
    print(f"All tests passed: {'✅ Yes' if all_passed else '❌ No'}", flush=True)
    
    return all_passed

if __name__ == "__main__":
    success = test_internet_ngram_analysis()
    sys.exit(0 if success else 1) 