import os
import sys
import logging
from utils import TranscriptEnhancer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_code_switching():
    """Test the code-switching detection and handling"""
    
    # Initialize the enhancer
    common_phrases_path = os.path.join(os.path.dirname(__file__), "..", "data", "common_phrases.txt")
    enhancer = TranscriptEnhancer(common_phrases_file=common_phrases_path)
    
    # Test cases for code-switching detection
    print("\n=== Code-Switching Detection Tests ===\n", flush=True)
    
    detection_test_cases = [
        # Inter-sentential code-switching (switching between sentences)
        "എന്റെ പേര് രാജു. I am from Kerala.",
        
        # Intra-sentential code-switching (switching within a sentence)
        "ഞാൻ office-ൽ പോകുന്നു.",
        
        # Intra-word code-switching (mixing within words)
        "wifiന്റെ speed കുറവാണ്.",
        
        # Mixed code-switching with technical terms
        "എന്റെ routerൽ red light കാണിക്കുന്നു.",
        
        # Code-switching with numbers
        "എനിക്ക് 2 GB data ബാക്കിയുണ്ട്."
    ]
    
    for i, test_case in enumerate(detection_test_cases):
        print(f"Test case #{i+1}: {test_case}", flush=True)
        
        # Detect code-switching
        categorized = enhancer._detect_code_switching(test_case)
        
        # Print results
        print("  Malayalam words:", categorized["malayalam"], flush=True)
        print("  English words:", categorized["english"], flush=True)
        print("  Code-switched words:", categorized["code_switched"], flush=True)
        print("  Numbers:", categorized["numbers"], flush=True)
        print("", flush=True)
    
    # Test cases for code-switching handling
    print("\n=== Code-Switching Handling Tests ===\n", flush=True)
    
    handling_test_cases = [
        # Intra-word code-switching with technical terms
        (
            "wifiന്റെ speed കുറവാണ്.",
            "വൈഫൈന്റെ സ്പീഡ് കുറവാണ്."
        ),
        
        # Mixed code-switching
        (
            "എന്റെ routerൽ red light കാണിക്കുന്നു.",
            "എന്റെ റൗട്ടർൽ റെഡ് ലൈറ്റ് കാണിക്കുന്നു."
        ),
        
        # Code-switching with internet terms
        (
            "internetന് പ്രശ്നം ഉണ്ട്.",
            "ഇന്റർനെറ്റ്ന് പ്രശ്നം ഉണ്ട്."
        )
    ]
    
    all_passed = True
    
    for i, (original, expected) in enumerate(handling_test_cases):
        print(f"Test case #{i+1}:", flush=True)
        
        # Handle code-switching
        handled = enhancer._handle_code_switched_text(original)
        
        # Check if the result matches the expected output
        passed = handled == expected
        all_passed = all_passed and passed
        result = "✅ PASS" if passed else "❌ FAIL"
        
        print(f"Original : {original}", flush=True)
        print(f"Handled  : {handled}", flush=True)
        print(f"Expected : {expected}", flush=True)
        print(f"Result   : {result}", flush=True)
        
        if not passed:
            print("\nDetailed comparison:", flush=True)
            print(f"Handled length: {len(handled)}, Expected length: {len(expected)}", flush=True)
            for j, (h_char, e_char) in enumerate(zip(handled, expected)):
                if h_char != e_char:
                    print(f"Mismatch at position {j}: '{h_char}' vs '{e_char}'", flush=True)
                    break
            if len(handled) != len(expected):
                if len(handled) < len(expected):
                    print(f"Handled is missing: '{expected[len(handled):]}'", flush=True)
                else:
                    print(f"Handled has extra: '{handled[len(expected):]}'", flush=True)
        
        print("\n" + "-"*50 + "\n", flush=True)
    
    # Test full enhancement pipeline with code-switched text
    print("\n=== Full Enhancement Pipeline with Code-Switching ===\n", flush=True)
    
    pipeline_test_cases = [
        # Code-switched text with internet issues
        (
            "എന്റെ wifiന്റെ speed കുറവാണ്.",
            "എന്റെ വൈഫൈന്റെ സ്പീഡ് കുറവാണ്."
        ),
        
        # Code-switched text with technical terms
        (
            "modemന്റെ red light കാണിക്കുന്നു.",
            "മോഡംന്റെ റെഡ് ലൈറ്റ് കാണിക്കുന്നു."
        )
    ]
    
    for i, (original, expected) in enumerate(pipeline_test_cases):
        print(f"Test case #{i+1}:", flush=True)
        
        # Apply full enhancement pipeline
        enhanced = enhancer.enhance(original)
        
        # Check if the result matches the expected output
        passed = enhanced == expected
        all_passed = all_passed and passed
        result = "✅ PASS" if passed else "❌ FAIL"
        
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
    success = test_code_switching()
    sys.exit(0 if success else 1) 