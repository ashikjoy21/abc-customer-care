# Speech-to-Text Enhancement Module

This module implements a post-processing pipeline to improve the quality and accuracy of speech-to-text (STT) transcripts without modifying the underlying STT system itself. The solution is specifically optimized for Malayalam language customer support conversations in the ISP domain.

## Overview

The STT enhancement system works as a middleware between the raw STT output and the language model (LLM) that processes user requests. It applies multiple techniques to correct common errors, standardize technical vocabulary, and leverage conversation context to improve transcript quality.

## Features

1. **Error Pattern Correction**: Fixes common STT errors in Malayalam, especially those related to technical terms and similar-sounding words.

2. **Technical Term Standardization**: Ensures consistent representation of technical terms like "router", "modem", "signal", etc.

3. **Fuzzy Matching**: Compares words against a database of common phrases used in ISP support contexts to find and correct near-matches.

4. **Context-Aware Correction**: Uses the conversation history to improve the accuracy of transcriptions based on previously mentioned technical terms.

5. **Inappropriate Content Filtering**: Detects and cleans up common misinterpretation patterns that might appear in noisy environments.

## Implementation

The system is implemented as a `TranscriptEnhancer` class in `utils.py`, integrated into the `ExotelBot.on_transcription` method.

### Key Components

- **TranscriptEnhancer**: Main class that orchestrates the enhancement pipeline
- **common_phrases.txt**: Database of common phrases for fuzzy matching
- **ExotelBot Integration**: The bot now applies transcript enhancement before sending text to the LLM

## Usage

The enhancement happens automatically as part of the conversation flow. The system logs both original and enhanced transcripts for debugging and quality assessment.

```python
# Example usage within ExotelBot
# This happens automatically in the on_transcription method

original_text = "സെക്സ് റൗട്ടർ ഓഫ് ആയി"  # STT output with common error
enhanced_text = transcript_enhancer.enhance(original_text)
# Result: "റൗട്ടർ ചെക്ക് ഓഫ് ആയി"  # Corrected output
```

## Configuration

The system can be customized in several ways:

1. **Common Phrases**: Add more phrases to `data/common_phrases.txt` to improve fuzzy matching.

2. **Error Patterns**: Extend the `_load_error_patterns()` method with additional known error patterns.

3. **Technical Terms**: Add more technical vocabulary to `_load_technical_term_map()`.

4. **Match Thresholds**: Adjust the similarity thresholds in the fuzzy matching (currently 75% for context terms and 85% for common phrases).

## Benefits

- **Improved User Experience**: More accurate understanding of user requests leads to better responses
- **Higher Completion Rate**: Reduces the number of misunderstandings and repeated requests
- **Consistency**: Ensures technical terms are consistently recognized regardless of minor pronunciation variations
- **Non-Invasive**: Works without modifying the underlying STT system

## Dependencies

- **rapidfuzz**: For fuzzy string matching
- **re**: For pattern-based text processing

## Future Improvements

- **Machine Learning Model**: Train a custom correction model on paired examples of raw and corrected transcripts
- **Domain-Specific Embeddings**: Use embeddings fine-tuned for Malayalam technical support vocabulary
- **User-Specific Adaptation**: Learn from individual user speech patterns over time
- **Automatic Error Pattern Learning**: Analyze logs to identify and correct new error patterns 