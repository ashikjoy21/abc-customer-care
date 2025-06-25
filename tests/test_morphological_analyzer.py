import unittest
from utils import MalayalamMorphologicalAnalyzer, TranscriptEnhancer

class TestMalayalamMorphologicalAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = MalayalamMorphologicalAnalyzer()
        self.enhancer = TranscriptEnhancer()
    
    def test_noun_analysis(self):
        """Test noun analysis with different case suffixes"""
        test_cases = [
            # Word, expected stem, expected type, expected case
            ("വീട്", "വീട്", "unknown", None),
            ("വീടിൽ", "വീട്", "noun", "locative"),
            ("വീടിന്റെ", "വീട്", "noun", "genitive"),
            ("വീടിന്", "വീട്", "noun", "dative"),
            ("വീടിനെ", "വീട്", "noun", "accusative"),
            ("വീടിനോട്", "വീട്", "noun", "sociative"),
            ("വീടിനാൽ", "വീട്", "noun", "instrumental"),
        ]
        
        for word, expected_stem, expected_type, expected_case in test_cases:
            analysis = self.analyzer.analyze_word(word)
            self.assertEqual(analysis["stem"], expected_stem, f"Failed on word: {word}")
            self.assertEqual(analysis["type"], expected_type, f"Failed on word: {word}")
            if expected_case:
                self.assertEqual(analysis["case"], expected_case, f"Failed on word: {word}")
    
    def test_verb_analysis(self):
        """Test verb analysis with different tense suffixes"""
        test_cases = [
            # Word, expected stem, expected type, expected tense
            ("ചെയ്യുക", "ചെയ്യുക", "unknown", None),
            ("ചെയ്യുന്നു", "ചെയ്യുക", "verb", "present"),
            ("ചെയ്തു", "ചെയ്യുക", "verb", "past"),
            ("ചെയ്യും", "ചെയ്യുക", "verb", "future"),
            ("ചെയ്യുന്നില്ല", "ചെയ്യുക", "verb", "negative_present"),
        ]
        
        for word, expected_stem, expected_type, expected_tense in test_cases:
            analysis = self.analyzer.analyze_word(word)
            self.assertEqual(analysis["stem"], expected_stem, f"Failed on word: {word}")
            self.assertEqual(analysis["type"], expected_type, f"Failed on word: {word}")
            if expected_tense:
                self.assertEqual(analysis["tense"], expected_tense, f"Failed on word: {word}")
    
    def test_technical_term_analysis(self):
        """Test technical term analysis"""
        test_cases = [
            # Word, expected stem, expected type
            ("വൈഫൈ", "വൈഫൈ", "technical"),
            ("വൈഫൈയുടെ", "വൈഫൈ", "technical"),
            ("വൈഫൈയിൽ", "വൈഫൈ", "technical"),
            ("ഇന്റർനെറ്റ്", "ഇന്റർനെറ്റ്", "technical"),
            ("ഇന്റർനെറ്റിന്റെ", "ഇന്റർനെറ്റ്", "technical"),
            ("നെറ്റ്", "ഇന്റർനെറ്റ്", "technical"),
            ("നെറ്റിന്", "ഇന്റർനെറ്റ്", "technical"),
        ]
        
        for word, expected_stem, expected_type in test_cases:
            analysis = self.analyzer.analyze_word(word)
            self.assertEqual(analysis["stem"], expected_stem, f"Failed on word: {word}")
            self.assertEqual(analysis["type"], expected_type, f"Failed on word: {word}")
    
    def test_standardize_technical_terms(self):
        """Test standardization of technical terms"""
        test_cases = [
            # Input text, expected output
            ("നെറ്റ് വരുന്നില്ല", "ഇന്റർനെറ്റ് വരുന്നില്ല"),
            ("വൈഫൈയുടെ സ്പീഡ് കുറവാണ്", "വൈഫൈയുടെ സ്പീഡ് കുറവാണ്"),
            ("നെറ്റിന്റെ സ്പീഡ് കുറവാണ്", "ഇന്റർനെറ്റിന്റെ സ്പീഡ് കുറവാണ്"),
            ("റൗട്ടറിൽ പ്രശ്നമുണ്ട്", "റൗട്ടറിൽ പ്രശ്നമുണ്ട്"),
        ]
        
        for input_text, expected_output in test_cases:
            result = self.analyzer.standardize_technical_terms(input_text)
            self.assertEqual(result, expected_output, f"Failed on: '{input_text}'")
    
    def test_integration_with_enhancer(self):
        """Test integration with the TranscriptEnhancer"""
        test_cases = [
            # Input text, expected output
            ("എന്റെ വൈഫൈയുടെ സ്പീഡ് കുറവാണ്", "എന്റെ വൈഫൈയുടെ സ്പീഡ് കുറവാണ്"),
            ("നെറ്റിന്റെ സ്പീഡ് കുറവാണ്", "ഇന്റർനെറ്റിന്റെ സ്പീഡ് കുറവാണ്"),
            ("നെറ്റ് വരുന്നില്ല", "ഇന്റർനെറ്റ് വരുന്നില്ല"),
            ("വൈഫൈയിൽ പ്രശ്നമുണ്ട്", "വൈഫൈയിൽ പ്രശ്നമുണ്ട്"),
        ]
        
        for input_text, expected_output in test_cases:
            result = self.enhancer.enhance(input_text)
            self.assertEqual(result, expected_output, f"Failed on: '{input_text}'")
    
    def test_complex_sentences(self):
        """Test analysis of complex sentences with multiple inflections"""
        test_cases = [
            # Input text, expected output
            (
                "എന്റെ വീട്ടിലെ വൈഫൈയുടെ സ്പീഡ് കുറവാണ്", 
                "എന്റെ വീട്ടിലെ വൈഫൈയുടെ സ്പീഡ് കുറവാണ്"
            ),
            (
                "നെറ്റിന്റെ സ്പീഡ് കുറവായതിനാൽ വീഡിയോ കാണാൻ കഴിയുന്നില്ല", 
                "ഇന്റർനെറ്റിന്റെ സ്പീഡ് കുറവായതിനാൽ വീഡിയോ കാണാൻ കഴിയുന്നില്ല"
            ),
        ]
        
        for input_text, expected_output in test_cases:
            result = self.analyzer.standardize_technical_terms(input_text)
            self.assertEqual(result, expected_output, f"Failed on: '{input_text}'")

if __name__ == "__main__":
    unittest.main() 