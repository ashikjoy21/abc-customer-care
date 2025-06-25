import os
from utils import TranscriptEnhancer

def test_real_example():
    """Test the TranscriptEnhancer with a real example"""
    
    # Initialize the enhancer
    common_phrases_path = os.path.join(os.path.dirname(__file__), "data", "common_phrases.txt")
    enhancer = TranscriptEnhancer(common_phrases_file=common_phrases_path)
    
    # Real example from logs
    real_example = "അവിടെ ചന്ദ്രിക കാണുന്നില്ല എലൈറ്റ് ആണല്ലോ"
    
    # Enhance the example
    enhanced = enhancer.enhance(real_example)
    
    # Expected result
    expected = "അവിടെ ചാനൽ കാണുന്നില്ല ഡിഷ് ലൈറ്റ് ആണല്ലോ"
    
    # Print results
    print("\n=== Real Example Test ===\n")
    print(f"Original : {real_example}")
    print(f"Enhanced : {enhanced}")
    print(f"Expected : {expected}")
    print(f"Result   : {'✅ PASS' if enhanced == expected else '❌ FAIL'}")

if __name__ == "__main__":
    test_real_example() 