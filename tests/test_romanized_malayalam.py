import unittest
from utils import TranscriptEnhancer

class TestRomanizedMalayalam(unittest.TestCase):
    def setUp(self):
        self.enhancer = TranscriptEnhancer()
    
    def test_romanized_malayalam_handling(self):
        """Test the handling of romanized Malayalam words"""
        test_cases = [
            # Basic word tests
            ("njan ente veedu", "ഞാൻ എന്റെ വീട്"),
            ("athu nalla aanu", "അത് നല്ല ആണ്"),
            ("ithu enthu aanu", "ഇത് എന്ത് ആണ്"),
            
            # Internet-related terms
            ("net varunnilla", "നെറ്റ് വരുന്നില്ല"),
            ("wifi illa", "വൈഫൈ ഇല്ല"),
            ("nalla speed illa", "നല്ല സ്പീഡ് ഇല്ല"),
            ("speed kuravanu", "സ്പീഡ് കുറവാണ്"),
            ("router restart cheythu", "റൗട്ടർ റീസ്റ്റാർട്ട് ചെയ്തു"),
            
            # Mixed romanized and Malayalam
            ("njan വീട്ടിൽ ആണ്", "ഞാൻ വീട്ടിൽ ആണ്"),
            ("ente വൈഫൈ varunnilla", "എന്റെ വൈഫൈ വരുന്നില്ല"),
            
            # Phrases with punctuation
            ("entha, sugalle?", "എന്താ, സുഖമല്ലേ?"),
            ("njan veetil aanu.", "ഞാൻ വീട്ടിൽ ആണ്."),
            
            # Multi-word phrases
            ("nalla speed", "നല്ല സ്പീഡ്"),
            ("modem restart cheythu", "മോഡം റീസ്റ്റാർട്ട് ചെയ്തു")
        ]
        
        for original, expected in test_cases:
            result = self.enhancer._handle_romanized_malayalam(original)
            self.assertEqual(result, expected, f"Failed on: '{original}'\nExpected: '{expected}'\nGot: '{result}'")
    
    def test_full_enhancement_with_romanized(self):
        """Test the full enhancement pipeline with romanized Malayalam input"""
        test_cases = [
            # Basic enhancement with romanized text
            (
                "njan ente veetil wifi varunnilla ennu paranju", 
                "ഞാൻ എന്റെ വീട്ടിൽ വൈഫൈ വരുന്നില്ല എന്ന് പറഞ്ഞു"
            ),
            
            # Mixed romanized, code-switched, and Malayalam
            (
                "ente router-ൽ red light കാണിക്കുന്നു, net varunnilla", 
                "എന്റെ റൗട്ടർ-ൽ റെഡ് ലൈറ്റ് കാണിക്കുന്നു, ഇന്റർനെറ്റ് വരുന്നില്ല"
            ),
            
            # Special case handling with romanized text
            (
                "wifi varunnilla, speed kuravanu", 
                "വൈഫൈ വരുന്നില്ല, സ്പീഡ് കുറവാണ്"
            )
        ]
        
        for original, expected in test_cases:
            result = self.enhancer.enhance(original)
            self.assertEqual(result, expected, f"Failed on: '{original}'\nExpected: '{expected}'\nGot: '{result}'")

if __name__ == "__main__":
    unittest.main() 