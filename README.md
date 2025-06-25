# Malayalam Transcript Enhancer

A comprehensive system for enhancing Malayalam transcripts, particularly focused on customer service conversations related to internet and technical support.

## Features

### 1. N-gram Analysis
- Corrects common internet-related terms and phrases
- Standardizes technical terminology
- Handles special cases like "വൈഫൈ വർക്ക് ചെയ്യുന്നില്ല" → "വൈഫൈ പ്രവർത്തിക്കുന്നില്ല"

### 2. Code-Switching Handling
- Detects and normalizes code-switched text (Malayalam mixed with English)
- Converts English technical terms to Malayalam equivalents when appropriate
- Preserves the grammatical structure of code-switched words

### 3. Romanized Malayalam Handling
- Converts romanized Malayalam words to proper Malayalam script
- Handles common internet-related phrases in romanized form
- Supports multi-word phrase detection and conversion

### 4. Text Normalization
- Preserves important characters in Malayalam
- Standardizes spacing and punctuation
- Corrects common transcription errors

### 5. Fuzzy Matching
- Handles slight variations in spelling and word forms
- Corrects common misspellings in technical terms

## Implementation

The system is implemented in the `utils.py` file, with the main class being `TranscriptEnhancer`. The enhancement pipeline consists of the following steps:

1. Handle romanized Malayalam words
2. Handle code-switched text
3. Normalize text while preserving Malayalam characters
4. Fix Malayalam-specific transcription errors
5. Apply internet-specific n-gram analysis
6. Apply basic error corrections
7. Standardize technical terms
8. Apply fuzzy matching against common phrases
9. Apply context-aware corrections
10. Clean up extra spaces

## Testing

The system has been thoroughly tested with the following test suites:

- `tests/test_internet_ngrams.py`: Tests for internet-related n-gram analysis
- `tests/test_code_switching.py`: Tests for code-switching detection and handling
- `tests/test_romanized_malayalam.py`: Tests for romanized Malayalam word handling

All tests pass successfully, demonstrating the effectiveness of the implementation.

## Usage

```python
from utils import TranscriptEnhancer

enhancer = TranscriptEnhancer()

# Enhance a transcript
enhanced_text = enhancer.enhance("njan ente veetil wifi varunnilla ennu paranju")
print(enhanced_text)  # Output: "ഞാൻ എന്റെ വീട്ടിൽ വൈഫൈ വരുന്നില്ല എന്ന് പറഞ്ഞു"
```

## Future Improvements

- Expand the dictionary of romanized Malayalam words
- Add more context-aware corrections for domain-specific terminology
- Implement more sophisticated fuzzy matching algorithms
- Integrate with speech recognition systems for real-time enhancement
