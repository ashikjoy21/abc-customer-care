from utils import MalayalamMorphologicalAnalyzer, TranscriptEnhancer
import re  # Add import for re module

def test_analyzer():
    analyzer = MalayalamMorphologicalAnalyzer()
    
    # Test noun analysis
    print("Testing noun analysis:")
    words = ["വീട്", "വീടിൽ", "വീടിന്റെ", "വീടിന്", "വീടിനെ"]
    for word in words:
        analysis = analyzer.analyze_word(word)
        print(f"{word} -> stem: {analysis['stem']}, type: {analysis['type']}")
    
    # Test verb analysis
    print("\nTesting verb analysis:")
    words = ["ചെയ്യുക", "ചെയ്തു", "ചെയ്യുന്നു", "ചെയ്യും"]
    for word in words:
        analysis = analyzer.analyze_word(word)
        print(f"{word} -> stem: {analysis['stem']}, type: {analysis['type']}")
    
    # Test technical term analysis
    print("\nTesting technical term analysis:")
    words = ["വൈഫൈ", "നെറ്റ്", "നെറ്റിന്റെ", "ഇന്റർനെറ്റ്"]
    for word in words:
        analysis = analyzer.analyze_word(word)
        print(f"{word} -> stem: {analysis['stem']}, type: {analysis['type']}")
    
    # Test standardization
    print("\nTesting standardization:")
    sentences = [
        "നെറ്റ് വരുന്നില്ല",
        "നെറ്റിന്റെ സ്പീഡ് കുറവാണ്",
        "എന്റെ വീട്ടിലെ വൈഫൈയുടെ സ്പീഡ് കുറവാണ്"
    ]
    for sentence in sentences:
        standardized = analyzer.standardize_technical_terms(sentence)
        print(f"Original: {sentence}")
        print(f"Standardized: {standardized}")

def test_enhancer():
    enhancer = TranscriptEnhancer()
    
    # Test enhancement with detailed steps
    print("\nTesting enhancement with detailed steps:")
    test_case = "നെറ്റിന്റെ സ്പീഡ് കുറവാണ്"
    print(f"Original: {test_case}")
    
    # Step 0: Handle romanized Malayalam
    step0 = enhancer._handle_romanized_malayalam(test_case)
    print(f"Step 0 (Romanized): {step0}")
    
    # Step 1: Handle code-switched text
    step1 = enhancer._handle_code_switched_text(step0)
    print(f"Step 1 (Code-switched): {step1}")
    
    # Step 2: Normalize text
    step2 = enhancer._normalize_text(step1)
    print(f"Step 2 (Normalized): {step2}")
    
    # Step 3: Fix Malayalam-specific errors
    step3 = enhancer._fix_malayalam_specific_errors(step2)
    print(f"Step 3 (Fixed errors): {step3}")
    
    # Step 4: Special case handling
    step4 = step3
    for term, replacement in enhancer.morphological_analyzer.special_case_mappings.items():
        if term in step4:
            step4 = step4.replace(term, replacement)
    print(f"Step 4 (Special cases): {step4}")
    
    # Step 5: Apply n-gram analysis
    step5 = enhancer._apply_ngram_analysis(step4)
    print(f"Step 5 (N-gram): {step5}")
    
    # Step 6: Basic error corrections
    step6 = enhancer._apply_error_corrections(step5)
    print(f"Step 6 (Error corrections): {step6}")
    
    # Step 7: Technical term standardization
    step7 = step6
    if "ഇന്റർനെറ്റ്" not in step7 and "നെറ്റ്" in step7:
        step7 = step7.replace("നെറ്റ്", "ഇന്റർനെറ്റ്")
    
    # Handle other technical terms
    for term, standard in enhancer.technical_term_map.items():
        if term == "നെറ്റ്" or standard in step7 or term not in step7:
            continue
        step7 = step7.replace(term, standard)
    print(f"Step 7 (Technical terms): {step7}")
    
    # Step 8: Fuzzy matching
    step8 = enhancer._apply_fuzzy_matching(step7)
    print(f"Step 8 (Fuzzy matching): {step8}")
    
    # Step 9: Context-aware corrections
    step9 = enhancer._apply_context_aware_corrections(step8)
    print(f"Step 9 (Context-aware): {step9}")
    
    # Step 10: Clean up spaces
    step10 = re.sub(r'\s+', ' ', step9).strip()
    print(f"Step 10 (Clean spaces): {step10}")
    
    # Final check
    final = step10.replace("ഇന്റർഇന്റർനെറ്റ്", "ഇന്റർനെറ്റ്")
    print(f"Final: {final}")
    
    # Standard test cases
    print("\nTesting standard enhancement:")
    sentences = [
        "നെറ്റ് വരുന്നില്ല",
        "നെറ്റിന്റെ സ്പീഡ് കുറവാണ്",
        "എന്റെ വീട്ടിലെ വൈഫൈയുടെ സ്പീഡ് കുറവാണ്"
    ]
    for sentence in sentences:
        enhanced = enhancer.enhance(sentence)
        print(f"Original: {sentence}")
        print(f"Enhanced: {enhanced}")

if __name__ == "__main__":
    print("Testing Morphological Analyzer:")
    test_analyzer()
    
    print("\n\nTesting Transcript Enhancer:")
    test_enhancer() 