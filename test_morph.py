"""
Test script for morphological analysis functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import MalayalamMorphologicalAnalyzer

def test_morphological_analysis():
    """Test the morphological analyzer with various Malayalam words"""
    
    analyzer = MalayalamMorphologicalAnalyzer()
    
    # Test cases for different types of words
    test_words = [
        # Nouns with case suffixes
        "വീട്", "വീടിൽ", "വീടിന്", "വീടിന്റെ", "വീടിനെ",
        "ഫോൺ", "ഫോണിൽ", "ഫോണിന്", "ഫോണിന്റെ", "ഫോണിനെ",
        
        # Verbs with tense suffixes
        "പ്രവർത്തിക്കുക", "പ്രവർത്തിക്കുന്നു", "പ്രവർത്തിച്ചു", "പ്രവർത്തിക്കും",
        "വരുക", "വരുന്നു", "വന്നു", "വരും",
        
        # Adjectives
        "നല്ല", "നല്ലത്", "നല്ലതായ", "നല്ലതുള്ള",
        
        # Technical terms
        "വൈഫൈ", "മോഡം", "റൗട്ടർ", "ഇന്റർനെറ്റ്",
        
        # Code-switched words
        "wifi", "modem", "router", "internet"
    ]
    
    print("=== Morphological Analysis Test ===\n")
    
    for word in test_words:
        try:
            analysis = analyzer.analyze_word(word)
            print(f"Word: {word}")
            print(f"  Stem: {analysis.get('stem', 'N/A')}")
            print(f"  Root: {analysis.get('root', 'N/A')}")
            print(f"  Case: {analysis.get('case', 'N/A')}")
            print(f"  Tense: {analysis.get('tense', 'N/A')}")
            print(f"  Type: {analysis.get('word_type', 'N/A')}")
            print(f"  Suffix: {analysis.get('suffix', 'N/A')}")
            print()
        except Exception as e:
            print(f"Error analyzing '{word}': {e}")
            print()
    
    # Test text analysis
    test_text = "എന്റെ വീട്ടിൽ വൈഫൈ പ്രവർത്തിക്കുന്നില്ല"
    print(f"=== Text Analysis Test ===")
    print(f"Text: {test_text}")
    
    try:
        text_analysis = analyzer.analyze_text(test_text)
        print("Word-by-word analysis:")
        for word_analysis in text_analysis:
            word = word_analysis.get('word', '')
            stem = word_analysis.get('stem', '')
            word_type = word_analysis.get('word_type', '')
            print(f"  {word} -> {stem} ({word_type})")
    except Exception as e:
        print(f"Error analyzing text: {e}")
    
    # Test technical term standardization
    print(f"\n=== Technical Term Standardization Test ===")
    test_technical_text = "എന്റെ wifi modem പ്രവർത്തിക്കുന്നില്ല"
    print(f"Original: {test_technical_text}")
    
    try:
        standardized = analyzer.standardize_technical_terms(test_technical_text)
        print(f"Standardized: {standardized}")
    except Exception as e:
        print(f"Error standardizing technical terms: {e}")

if __name__ == "__main__":
    test_morphological_analysis() 