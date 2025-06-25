# Content Filtering System

This document describes the content filtering system implemented in the Sat Vision customer support bot to prevent inappropriate content and handle speech recognition errors.

## Overview

The system implements multiple layers of content filtering to ensure the bot doesn't process or respond to inappropriate content:

1. **Text Preprocessing**: Filters out inappropriate words from transcribed speech
2. **Content Detection**: Identifies potentially inappropriate queries using regex patterns
3. **Silence Detection**: Identifies when silence or background noise is misinterpreted as inappropriate content
4. **Response Handling**: Provides appropriate responses when inappropriate content is detected
5. **Logging**: Logs filtered content for monitoring and improvement

## Implementation Details

### 1. Text Preprocessing

Both transcription systems (Transcriber and RealTimeTranscriber) implement a `_post_process_transcript` method that:

- Checks if the transcript is likely from silence misinterpretation
- Removes known inappropriate words
- Cleans up extra spaces
- Applies technical term corrections

```python
def _post_process_transcript(self, text: str) -> str:
    # Skip processing if the text is likely from silence
    if self._is_likely_silence(text):
        logger.info("Detected likely silence misinterpretation, ignoring transcript")
        return ""
    
    # Content filtering - remove inappropriate words
    inappropriate_words = ["സെക്സ്", "sex"]
    for word in inappropriate_words:
        text = text.replace(word, "")
    
    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
```

### 2. Silence Detection

The system implements silence detection to identify when silence or background noise is misinterpreted as inappropriate content:

```python
def _is_likely_silence(self, text: str) -> bool:
    # Check if the text only contains the commonly misinterpreted word
    if text.strip() in ["സെക്സ്", "sex"]:
        return True
        
    # Check if the text is very short (1-2 words) and contains the problematic word
    if len(text.split()) <= 2 and ("സെക്സ്" in text or "sex" in text):
        return True
        
    # If the audio level was very low, and we got one of these words, it's likely silence
    if self.last_audio_level < self.silence_threshold and ("സെക്സ്" in text or "sex" in text):
        return True
        
    return False
```

The RealTimeTranscriber class also measures audio levels to help determine if the audio contains actual speech:

```python
def add_audio(self, base64_audio: str):
    try:
        audio_bytes = base64.b64decode(base64_audio)
        if not self.stop_flag:
            # Calculate audio level (simple RMS)
            if len(audio_bytes) > 0:
                # Convert bytes to 16-bit integers
                try:
                    import numpy as np
                    audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
                    # Calculate RMS
                    self.last_audio_level = np.sqrt(np.mean(np.square(audio_data)))
                except ImportError:
                    # If numpy is not available, use a simpler method
                    self.last_audio_level = sum(abs(int.from_bytes(audio_bytes[i:i+2], byteorder='little', signed=True)) 
                                            for i in range(0, min(len(audio_bytes), 1000), 2)) / min(len(audio_bytes)//2, 500)
                    
            self.audio_queue.put(audio_bytes)
    except Exception as e:
        logger.error(f"Error adding audio: {e}")
```

### 3. Content Detection

The ExotelBot class implements an `is_inappropriate_content` method that:

- Uses regex patterns to identify inappropriate content
- Handles both English and Malayalam inappropriate words
- Logs detected inappropriate content

```python
def is_inappropriate_content(self, text: str) -> bool:
    inappropriate_patterns = [
        r'സെക്സ്',  # Malayalam word
        r'\bsex\b',
        r'\bporn\b',
        r'\bxxx\b',
    ]
    
    for pattern in inappropriate_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            # Log and return True if inappropriate
            return True
    
    return False
```

### 4. Response Handling

When inappropriate content is detected, the bot:

- Does not process the query through the RAG system
- Does not send the query to the Gemini model
- Responds with a polite message redirecting the conversation:

```
"ക്ഷമിക്കണം, എനിക്ക് ടെക്നിക്കൽ സഹായം മാത്രമേ നൽകാൻ കഴിയൂ. നിങ്ങളുടെ ടിവി അല്ലെങ്കിൽ ഇന്റർനെറ്റ് പ്രശ്നങ്ങളെക്കുറിച്ച് ചോദിക്കാം."
```

(Translation: "Sorry, I can only provide technical assistance. You can ask about your TV or internet problems.")

### 5. Logging

The system logs filtered content to:

- Application logs with WARNING level
- A dedicated `content_filter.log` file with:
  - Timestamp
  - Call ID
  - Phone number (if available)
  - The filtered text

## Testing

Two test scripts are provided to verify the content filtering functionality:

1. `test_content_filter.py` - Tests the basic content filtering functionality
2. `test_silence_detection.py` - Tests the silence detection functionality

```bash
python test_content_filter.py
python test_silence_detection.py
```

## Common Speech Recognition Issues

The system specifically addresses a common issue where the speech recognition system incorrectly transcribes silence or background noise as the word "സെക്സ്" (sex). This is handled by:

1. Detecting when silence is likely misinterpreted as inappropriate content
2. Measuring audio levels to help determine if the audio contains actual speech
3. Filtering out this word in the preprocessing step
4. Detecting it as inappropriate content if it passes preprocessing
5. Logging these occurrences for monitoring

## Maintenance

To update or expand the content filtering system:

1. Add new patterns to the `inappropriate_patterns` list in `is_inappropriate_content`
2. Add new words to the `inappropriate_words` list in `_post_process_transcript`
3. Adjust the silence detection parameters if needed
4. Review the `content_filter.log` regularly to identify new patterns 