import os
import sys
import logging
from utils import TranscriptEnhancer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_malayalam_normalization():
    """Test the Malayalam-specific normalization and error correction"""
    
    # Initialize the enhancer
    common_phrases_path = os.path.join(os.path.dirname(__file__), "..", "data", "common_phrases.txt")
    enhancer = TranscriptEnhancer(common_phrases_file=common_phrases_path)
    
    # Test the problematic cases first
    print("\n=== Problematic Test Cases ===\n", flush=True)
    
    problematic_test_cases = [
        # Case with character confusion and internet terms
        (
            "നെറ്റ് കണക്ഷൻ ഇല്ല അംമയുടെ ഫോണിൽ",
            "ഇന്റർനെറ്റ് കണക്ഷൻ ഇല്ല അമ്മയുടെ ഫോണിൽ"
        ),
        
        # Case with ZWJ/chillu and technical terms
        (
            "റൗടർ റീസ്റ്റർട്ട് ചെയ്തിട്ടും അവര്\u200D വീട്ടിൽ നെറ്റ് വരുന്നില്ല",
            "റൗട്ടർ റീസ്റ്റാർട്ട് ചെയ്തിട്ടും അവർ വീട്ടിൽ ഇന്റർനെറ്റ് വരുന്നില്ല"
        ),
    ]
    
    all_passed = True
    
    for i, (original, expected) in enumerate(problematic_test_cases):
        print(f"Test case #{i+1}:", flush=True)
        
        # Debug each step of the enhancement process
        print("Step 0: Original text", flush=True)
        print(f"  {original}", flush=True)
        
        # Step 1: Normalize text
        normalized = enhancer._normalize_text(original)
        print("Step 1: After normalization", flush=True)
        print(f"  {normalized}", flush=True)
        
        # Step 2: Fix Malayalam-specific errors
        fixed = enhancer._fix_malayalam_specific_errors(normalized)
        print("Step 2: After fixing Malayalam-specific errors", flush=True)
        print(f"  {fixed}", flush=True)
        
        # Step 3: Apply n-gram analysis
        ngram = enhancer._apply_ngram_analysis(fixed)
        print("Step 3: After n-gram analysis", flush=True)
        print(f"  {ngram}", flush=True)
        
        # Step 4: Apply error corrections
        error_corrected = enhancer._apply_error_corrections(ngram)
        print("Step 4: After error corrections", flush=True)
        print(f"  {error_corrected}", flush=True)
        
        # Full enhancement
        enhanced = enhancer.enhance(original)
        passed = enhanced == expected
        all_passed = all_passed and passed
        result = "✅ PASS" if passed else "❌ FAIL"
        
        print("\nFinal result:", flush=True)
        print(f"Original : {original}", flush=True)
        print(f"Enhanced : {enhanced}", flush=True)
        print(f"Expected : {expected}", flush=True)
        print(f"Result   : {result}", flush=True)
        
        if not passed:
            print("\nDetailed comparison:", flush=True)
            print(f"Enhanced length: {len(enhanced)}, Expected length: {len(expected)}", flush=True)
            for j, (e_char, x_char) in enumerate(zip(enhanced, expected)):
                if e_char != x_char:
                    print(f"Mismatch at position {j}: '{e_char}' vs '{x_char}'", flush=True)
                    break
            if len(enhanced) != len(expected):
                if len(enhanced) < len(expected):
                    print(f"Enhanced is missing: '{expected[len(enhanced):]}'", flush=True)
                else:
                    print(f"Enhanced has extra: '{enhanced[len(expected):]}'", flush=True)
        
        print("\n" + "-"*50 + "\n", flush=True)
    
    # Print overall result
    print("\n=== Overall Result ===\n", flush=True)
    print(f"All tests passed: {'✅ Yes' if all_passed else '❌ No'}", flush=True)
    
    return all_passed

if __name__ == "__main__":
    success = test_malayalam_normalization()
    sys.exit(0 if success else 1) 