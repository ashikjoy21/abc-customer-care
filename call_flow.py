import asyncio
import websockets
import json
import logging
import base64
import time
import threading
import queue
import wave
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple, Callable
from enum import Enum
from google.cloud import speech, texttospeech
from google.oauth2 import service_account
import google.generativeai as genai
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.embeddings import BaseEmbedding
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.settings import Settings
import os
import re
import sys
import uuid
import jsonlines
import requests
from dotenv import load_dotenv
from utils import format_customer_info, TranscriptEnhancer
import numpy as np
import hashlib
from escalation_manager import EscalationManager
from supabase_client import SupabaseManager
from transcript_enhancer import TranscriptEnhancer
from troubleshooting_engine import TroubleshootingEngine
from utils import format_duration, get_status_emoji, get_resolution_emoji, format_customer_info

from config import (
    GCP_CREDENTIALS_PATH,
    GEMINI_API_KEY,
    KNOWLEDGE_BASE_PATH,
    SPEECH_LANGUAGE_CODE,
    SPEECH_VOICE_NAME,
    SPEECH_SAMPLE_RATE,
    MAX_PHONE_LENGTH
)
from db import CustomerDatabaseManager
from utils import logger

# Initialize response cache with TTL
RESPONSE_CACHE = {}
RESPONSE_CACHE_TTL = timedelta(minutes=30)  # Cache responses for 30 minutes

# RAG cache for storing knowledge base results
RAG_CACHE = {}
RAG_CACHE_TTL = timedelta(hours=2)  # Cache RAG results longer (2 hours)

# TTS cache for storing synthesized audio
TTS_CACHE = {}
TTS_CACHE_TTL = timedelta(hours=6)  # Cache TTS results even longer (6 hours)

# Explicitly disable OpenAI by setting llm=None globally
Settings.llm = None

# Initialize GCP clients
credentials = service_account.Credentials.from_service_account_file(
    GCP_CREDENTIALS_PATH,
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

speech_client = speech.SpeechClient(credentials=credentials)
tts_client = texttospeech.TextToSpeechClient(credentials=credentials)

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Load RAG knowledge base
chroma_client = chromadb.Client()
collection = chroma_client.create_collection("isp_docs")
documents = SimpleDirectoryReader(KNOWLEDGE_BASE_PATH).load_data()
embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
vector_store = ChromaVectorStore(chroma_collection=collection)
index = VectorStoreIndex.from_documents(documents, embed_model=embed_model, vector_store=vector_store)
query_engine = index.as_query_engine(llm=None)

class CallStatus(Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    DISCONNECTED = "disconnected"

@dataclass
class TroubleshootingStep:
    step: str
    timestamp: datetime
    result: str

@dataclass
class CallMemory:
    call_id: str
    phone_number: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    device_type: Optional[str] = "fiber_modem"  # Default device type
    start_time: datetime = field(default_factory=datetime.now)
    area_issue_status: Optional[str] = None
    troubleshooting_steps: List[TroubleshootingStep] = field(default_factory=list)
    status: CallStatus = CallStatus.ACTIVE
    resolution_notes: Optional[str] = None
    last_interaction: Optional[str] = None
    customer_info: Optional[Dict[str, Any]] = None
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    # Add escalation tracking fields
    escalation_reasons: List[str] = field(default_factory=list)
    issue_type: Optional[str] = None
    sub_issues: List[str] = field(default_factory=list)
    
    def add_troubleshooting_step(self, step: str, result: str):
        """Add a troubleshooting step with timestamp"""
        self.troubleshooting_steps.append(
            TroubleshootingStep(
                step=step,
                timestamp=datetime.now(),
                result=result
            )
        )
        # Also add to conversation history
        self.conversation_history.append({
            "user": step,
            "bot": result,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_call_duration(self) -> int:
        """Get call duration in seconds"""
        return int((datetime.now() - self.start_time).total_seconds())
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate call summary for reporting"""
        return {
            "call_id": self.call_id,
            "phone_number": self.phone_number,
            "customer_name": self.customer_name,
            "duration_seconds": self.get_call_duration(),
            "start_time": self.start_time.isoformat(),
            "status": self.status.value,
            "area_issue_status": self.area_issue_status,
            "troubleshooting_steps": [
                {
                    "step": step.step,
                    "timestamp": step.timestamp.isoformat(),
                    "result": step.result
                }
                for step in self.troubleshooting_steps
            ],
            "resolution_notes": self.resolution_notes,
            "customer_info": self.customer_info,
            "escalation_reasons": self.escalation_reasons,
            "issue_type": self.issue_type,
            "sub_issues": self.sub_issues
        }
        
    def get_model_context(self) -> str:
        """Generate context string for the model"""
        context_parts = []
        
        # Add customer info
        if self.customer_info:
            context_parts.append("Customer Information:")
            context_parts.append(f"- Name: {self.customer_info.get('Customer Name', self.customer_info.get('name', 'Unknown'))}")
            context_parts.append(f"- Provider: {self.customer_info.get('Provider', self.customer_info.get('isp', 'Unknown'))}")
            context_parts.append(f"- Plan: {self.customer_info.get('Current Plan', self.customer_info.get('plan', 'Unknown'))}")
            context_parts.append(f"- Operator: {self.customer_info.get('Operator', self.customer_info.get('operator', 'Unknown'))}")
            context_parts.append(f"- Region: {self.customer_info.get('Region', 'Unknown')}")
        
        # Add only the last 5 exchanges instead of full history
        if self.conversation_history:
            context_parts.append("\nRecent Conversation History:")
            recent_exchanges = self.conversation_history[-5:]  # Get only last 5 exchanges
            for entry in recent_exchanges:
                context_parts.append(f"User: {entry['user']}")
                context_parts.append(f"Bot: {entry['bot']}")
        
        # Add only the most recent troubleshooting steps
        if self.troubleshooting_steps:
            context_parts.append("\nRecent Troubleshooting Steps:")
            recent_steps = self.troubleshooting_steps[-3:]  # Get only last 3 steps
            for step in recent_steps:
                context_parts.append(f"- {step.step} -> {step.result}")
        
        return "\n".join(context_parts)

async def query_gemini(text: str, chat_session, lock: asyncio.Lock, rag_context: str = "") -> str:
    """Query Gemini with context, ensuring thread-safe access to chat_session."""
    # Generate a cache key based on the text and context
    cache_key = hashlib.md5((text + rag_context).encode()).hexdigest()
    
    # Check if we have a cached response that's still valid
    if cache_key in RESPONSE_CACHE:
        cached_entry = RESPONSE_CACHE[cache_key]
        if datetime.now() < cached_entry["expiry"]:
            logger.info(f"Using cached response for query: {text[:50]}...")
            return cached_entry["response"]
    
    async with lock:
        try:
            # Add system prompt to encourage more natural responses
            system_prompt = """
You are Anjali, a customer service agent for an ISP company in Kerala.

IMPORTANT LIMITATIONS:
- You are a voice-only bot on a telephone call - users CANNOT send photos, screenshots, or any visual media
- NEVER ask customers to send photos, images, screenshots, or any visual content
- NEVER mention options that aren't possible over a phone call (like sending links, clicking buttons, etc.)

STRUCTURED TROUBLESHOOTING APPROACH:
Follow these troubleshooting stages in sequence:
1. IDENTIFICATION: First clearly identify the exact problem (red light, no power, WiFi issue, speed, etc.)
2. DIAGNOSIS: Ask targeted questions (ONE at a time) to pinpoint the specific issue
3. SOLUTION: Provide specific, step-by-step instructions once the issue is clear

Common Internet Issues and Diagnostic Steps:
- For RED LIGHT issues: Ask the customer if any light on the modem is red. If yes, proceed with troubleshooting for red light. Do not ask about the color of individual lights (PON, Internet, etc.).
- For NO POWER issues: Check power connections, adapter, and power source
- For WIFI ISSUES: Check if WiFi name appears, password problems, device limitations
- For SLOW SPEED: Check multiple devices, peak usage times, wired vs wireless
- For DISCONNECTION: Check for patterns (time of day, weather, etc.)

Never jump between different problems - stay focused on solving one issue at a time.

Your approach to customer service:
- Listen first, then respond to what the customer actually said
- Only refer to technical information when directly relevant to the conversation
- Treat troubleshooting steps as a reference guide, not a script to follow
- Let the conversation flow naturally based on what the customer is saying
- Only suggest solutions for problems the customer has actually mentioned
- When you don't understand something, respond naturally and ask for clarification in a conversational way
- Never say "I don't understand" - instead say things like "Could you explain that differently?" or "I'm not sure what you mean by that"

Handling poor transcriptions:
- If the transcript seems completely unrelated to ISP services, assume it's a transcription error
- In such cases, continue with the current troubleshooting path instead of starting a new topic
- Never directly state that there was a transcription error or that you didn't understand
- Always assume the customer has an ISP-related query, even if the transcript is unclear

Your responses must sound completely natural in Malayalam, like a real person talking:
- Vary your sentence structures and opening phrases
- Never follow a predictable pattern in your responses
- Avoid starting with the customer's name (use it sparingly, if at all)
- Get straight to the point without unnecessary words
- Provide complete, helpful responses without arbitrary length restrictions
- Use simple, everyday language that flows naturally
- Only ask questions when you genuinely need information
- Don't use the same conversational markers repeatedly
"""
            
            # Add the system prompt and context to the beginning of each query
            full_prompt = f"{system_prompt}\n\n"
            if rag_context:
                full_prompt += f"Context: {rag_context}\n\n"
            full_prompt += text
            
            q = asyncio.Queue()
            loop = asyncio.get_event_loop()

            def producer():
                try:
                    response_stream = chat_session.send_message(full_prompt, stream=True)
                    for chunk in response_stream:
                        if hasattr(chunk, 'text'):
                            loop.call_soon_threadsafe(q.put_nowait, chunk.text)
                except Exception as e:
                    logger.error(f"Error in Gemini stream producer: {e}")
                finally:
                    loop.call_soon_threadsafe(q.put_nowait, None)  # Signal end of stream
            
            # Run the producer in a background thread
            producer_task = loop.run_in_executor(None, producer)

            chunks = []
            while True:
                chunk = await q.get()
                if chunk is None:
                    break
                chunks.append(chunk)
            
            await producer_task

            if not chunks:
                logger.error("Gemini stream returned no chunks.")
                return "ക്ഷമിക്കണം, എനിക്ക് ഒരു ചെറിയ പ്രശ്നം നേരിട്ടു. ഒരു നിമിഷം കാത്തിരിക്കാമോ?"

            response_text = "".join(chunks)
            response_text = _limit_response_length(response_text, 500)
            
            # Cache the response with expiration time
            RESPONSE_CACHE[cache_key] = {
                "response": response_text,
                "expiry": datetime.now() + RESPONSE_CACHE_TTL
            }
            
            return response_text
            
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return "ക്ഷമിക്കണം, എനിക്ക് ഒരു ചെറിയ പ്രശ്നം നേരിട്ടു. ഒരു നിമിഷം കാത്തിരിക്കാമോ?"

def _limit_response_length(text: str, max_length: int = 500) -> str:
    """Limit response length by truncating at sentence boundaries"""
    if len(text) <= max_length:
        return text
        
    # Find a good breaking point - end of sentence
    sentence_endings = [match.start() for match in re.finditer(r'[.!?] ', text[:max_length+50])]
    
    if not sentence_endings:
        # If no sentence endings found, just return the full text
        # This prevents cutting off important information
        return text
        
    # Find the last sentence ending before max_length
    last_ending = max([end for end in sentence_endings if end <= max_length], default=max_length)
    
    # Include the punctuation and space
    return text[:last_ending+2].strip()

def _is_likely_misunderstanding(text: str) -> bool:
    """Check if the text indicates a misunderstanding"""
    misunderstanding_indicators = [
        "മനസ്സിലായില്ല",  # I don't understand
        "എന്താണ് ഉദ്ദേശിച്ചത്",  # What do you mean
        "വ്യക്തമല്ല",  # Not clear
        "എന്ത് പറഞ്ഞു",  # What did you say
        "വീണ്ടും പറയാമോ",  # Can you say again
    ]
    
    return any(indicator in text.lower() for indicator in misunderstanding_indicators)

class Transcriber:
    """Handles speech-to-text transcription using Google Cloud Speech-to-Text"""
    
    def __init__(self, credentials_path: str):
        """Initialize transcriber with Google Cloud credentials"""
        try:
            self.client = speech.SpeechClient.from_service_account_file(credentials_path)
            self.streaming_config = None
            self.audio_generator = None
            self.requests = None
            self.responses = None
            self.transcription_callback = None
            self.last_audio_level = 0
            self._load_speech_context()
            logger.info("Transcriber initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing transcriber: {e}")
            raise
            
    def _load_speech_context(self):
        """Load speech context from file"""
        try:
            context_path = os.path.join(os.path.dirname(__file__), "data", "speech_context.txt")
            with open(context_path, "r", encoding="utf-8") as f:
                # Read all lines and filter out comments and empty lines
                phrases = [line.strip() for line in f.readlines() 
                          if line.strip() and not line.startswith("#")]
                
            # Create speech context
            self.speech_context = speech.SpeechContext(phrases=phrases)
            logger.info(f"Loaded {len(phrases)} phrases for speech context")
        except Exception as e:
            logger.error(f"Error loading speech context: {e}")
            self.speech_context = None
            
    def start_streaming(self, callback: Callable[[str], None]):
        """Start streaming transcription"""
        try:
            self.transcription_callback = callback
            
            # Configure streaming request
            self.streaming_config = speech.StreamingRecognitionConfig(
                config=speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.MULAW,
                    sample_rate_hertz=8000,
                    language_code="ml-IN",
                    enable_automatic_punctuation=True,
                    speech_contexts=[self.speech_context] if self.speech_context else None,
                    model="latest_long",  # Use latest long-form model
                    use_enhanced=True,    # Use enhanced model
                ),
                interim_results=True
            )
            
            self.audio_generator = self._audio_generator()
            self.requests = (
                speech.StreamingRecognizeRequest(audio_content=content)
                for content in self.audio_generator
            )
            
            self.responses = self.client.streaming_recognize(
                self.streaming_config,
                self.requests
            )
            
            logger.info("Started streaming transcription")
            
        except Exception as e:
            logger.error(f"Error starting streaming: {e}")
            raise
            
    def _audio_generator(self):
        """Generate audio chunks from the stream"""
        try:
            for chunk in self.audio_generator:
                if chunk:
                    yield chunk
        except Exception as e:
            logger.error(f"Error in audio generator: {e}")
            raise
            
    def process_responses(self):
        """Process streaming responses"""
        try:
            for response in self.responses:
                if not response.results:
                    continue
                    
                result = response.results[0]
                if not result.alternatives:
                    continue
                    
                transcript = result.alternatives[0].transcript
                
                # Log the raw transcript for debugging
                logger.debug(f"Raw transcript: {transcript}")
                
                # Post-process the transcript
                processed_transcript = self._post_process_transcript(transcript)
                
                # Log the processed transcript
                logger.debug(f"Processed transcript: {processed_transcript}")
                
                if result.is_final:
                    if self.transcription_callback:
                        self.transcription_callback(processed_transcript)
                        
        except Exception as e:
            logger.error(f"Error processing responses: {e}")
            raise
            
    def _post_process_transcript(self, transcript: str) -> str:
        """Post-process the transcript to improve accuracy"""
        try:
            # Skip processing if the text is likely from silence
            if self._is_silence(transcript):
                logger.info("Detected likely silence misinterpretation, ignoring transcript")
                return ""
                
            # Content filtering - remove inappropriate words
            inappropriate_words = ["സെക്സ്", "sex"]
            for word in inappropriate_words:
                transcript = transcript.replace(word, "")
            
            # Common replacements for technical terms
            replacements = {
                "റൗട്ടർ": "റൗട്ടർ",
                "ഫൈബർ": "ഫൈബർ",
                "ഇന്റർനെറ്റ്": "ഇന്റർനെറ്റ്",
                "വൈഫൈ": "വൈഫൈ",
                "കേബിൾ": "കേബിൾ",
                "സിഗ്നൽ": "സിഗ്നൽ",
                "സ്പീഡ്": "സ്പീഡ്",
                "ബാൻഡ്‌വിഡ്ത്ത്": "ബാൻഡ്‌വിഡ്ത്ത്",
                "ഡാറ്റ": "ഡാറ്റ",
                "ഡൗൺലോഡ്": "ഡൗൺലോഡ്",
                "അപ്‌ലോഡ്": "അപ്‌ലോഡ്",
                "പിംഗ്": "പിംഗ്",
                "ലാറ്റൻസി": "ലാറ്റൻസി",
                "ജിഗാബൈറ്റ്": "ജിഗാബൈറ്റ്",
                "മെഗാബൈറ്റ്": "മെഗാബൈറ്റ്",
                "ബിപിഎസ്": "ബിപിഎസ്",
                "എംബിപിഎസ്": "എംബിപിഎസ്",
                "ജിബിപിഎസ്": "ജിബിപിഎസ്"
            }
            
            # Apply replacements
            for wrong, correct in replacements.items():
                transcript = transcript.replace(wrong, correct)
                
            # Remove extra spaces
            transcript = re.sub(r'\s+', ' ', transcript).strip()
            
            return transcript
            
        except Exception as e:
            logger.error(f"Error in post-processing transcript: {e}")
            return transcript

    def _is_silence(self, text: str) -> bool:
        """Check if the transcript is likely from silence/background noise"""
        # Skip empty or very short texts
        if not text or len(text.strip()) <= 1:
            return True
            
        # Check if the text only contains the commonly misinterpreted word
        if text.strip() in ["സെക്സ്", "sex"]:
            logger.info("Detected standalone inappropriate word - likely silence misinterpretation")
            return True
            
        # Check if the text is very short (1-2 words) and contains the problematic word
        if len(text.split()) <= 2 and ("സെക്സ്" in text or "sex" in text):
            logger.info("Detected short phrase with inappropriate word - likely silence misinterpretation")
            return True
            
        return False

class RealTimeTranscriber:
    """Handles real-time speech transcription"""
    
    def __init__(self, on_transcript_callback=None, loop=None):
        self.audio_queue = queue.Queue()
        self.on_transcript_callback = on_transcript_callback
        self.loop = loop
        self.streaming_config = speech.StreamingRecognitionConfig(
            config=speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=SPEECH_SAMPLE_RATE,
                language_code=SPEECH_LANGUAGE_CODE,
                audio_channel_count=1,
                enable_automatic_punctuation=True,
                use_enhanced=True,
                model="default",
                profanity_filter=False,
                speech_contexts=[
                    speech.SpeechContext(
                        phrases=[
                            "കണക്ഷൻ പോയി",
                            "റീചാർജ് ചെയ്തു",
                            "ഇൻറർനെറ്റ് പ്രശ്നം",
                            "സിഗ്നൽ ഇല്ല",
                            "വേഗത കുറവാണ്",
                            "ചാനലുകൾ കാണില്ല"
                        ],
                        boost=15.0
                    )
                ]
            ),
            interim_results=True,
            single_utterance=False
        )
        self.stop_flag = False
        self.thread = None
        self.last_audio_level = 0
        self.silence_threshold = 100  # Threshold for determining silence
        self._start_thread()

    def _post_process_transcript(self, text: str) -> str:
        """Post-process transcript text"""
        # Skip processing if the text is likely from silence
        if self._is_silence(text):
            logger.info("Detected likely silence misinterpretation, ignoring transcript")
            return ""
        
        # Content filtering - remove inappropriate words
        inappropriate_words = ["സെക്സ്", "sex"]
        for word in inappropriate_words:
            text = text.replace(word, "")
        
        # Technical term corrections
        corrections = {
            "റീചാർജ്ജ്": "റീചാർജ്",
            "സിഗ്നല്": "സിഗ്നൽ",
        }
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
            
        # Clean up extra spaces that might result from word removal
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
        
    def _is_silence(self, text: str) -> bool:
        """Check if the transcript is likely from silence/background noise"""
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

    def add_audio(self, base64_audio: str):
        """Add audio data to queue"""
        try:
            audio_bytes = base64.b64decode(base64_audio)
            if not self.stop_flag:
                # Calculate audio level (simple RMS)
                if len(audio_bytes) > 0:
                    # Convert bytes to 16-bit integers
                    try:
                        audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
                        # Calculate RMS
                        self.last_audio_level = np.sqrt(np.mean(np.square(audio_data)))
                        logger.debug(f"Audio level: {self.last_audio_level}")
                    except ImportError:
                        # If numpy is not available, use a simpler method
                        self.last_audio_level = sum(abs(int.from_bytes(audio_bytes[i:i+2], byteorder='little', signed=True)) 
                                                for i in range(0, min(len(audio_bytes), 1000), 2)) / min(len(audio_bytes)//2, 500)
                        
                self.audio_queue.put(audio_bytes)
        except Exception as e:
            logger.error(f"Error adding audio: {e}")

    def _run_streaming(self):
        """Run streaming recognition with interim results processing"""
        try:
            requests = self._audio_generator()
            responses = speech_client.streaming_recognize(self.streaming_config, requests)
            
            last_interim = None
            interim_confidence_threshold = 0.7  # Only process high-confidence interim results
            
            for response in responses:
                if self.stop_flag:
                    break
                    
                if not response.results:
                    continue
                    
                result = response.results[0]
                if not result.alternatives:
                    continue
                    
                transcript = result.alternatives[0].transcript
                transcript = self._post_process_transcript(transcript)
                
                # Skip empty transcripts (from silence detection)
                if not transcript:
                    continue
                
                if result.is_final:
                    if self.on_transcript_callback and self.loop:
                        asyncio.run_coroutine_threadsafe(
                            self.on_transcript_callback(transcript),
                            self.loop
                        )
                        last_interim = None  # Reset interim tracking
                elif result.stability > interim_confidence_threshold:
                    # Process high-confidence interim results if they're different from last interim
                    # and at least 5 words long (to avoid processing fragments)
                    if (transcript != last_interim and 
                        len(transcript.split()) >= 5 and 
                        self.on_transcript_callback and 
                        self.loop):
                        # Log that we're using an interim result
                        logger.debug(f"Processing high-confidence interim result: {transcript}")
                        last_interim = transcript
                        # Process interim result in background without awaiting
                        asyncio.run_coroutine_threadsafe(
                            self.on_transcript_callback(transcript + " (interim)"),
                            self.loop
                        )
                        
        except Exception as e:
            logger.error(f"Error in streaming recognition: {e}")
    
    def stop(self):
        """Stop transcription"""
        self.stop_flag = True
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)

    def _start_thread(self):
        """Start transcription thread"""
        if self.thread is None or not self.thread.is_alive():
            self.stop_flag = False
            self.thread = threading.Thread(target=self._run_streaming, daemon=True)
            self.thread.start()

    def _audio_generator(self):
        """Generate audio chunks from queue"""
        while not self.stop_flag:
            try:
                chunk = self.audio_queue.get(timeout=1)
                yield speech.StreamingRecognizeRequest(audio_content=chunk)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in audio generator: {e}")
                break

@dataclass
class PhoneNumberCollector:
    """Helper class to manage phone number collection via DTMF"""
    digits: str = ""
    is_collecting: bool = False
    max_length: int = MAX_PHONE_LENGTH
    
    def reset(self):
        """Reset the collector state"""
        self.digits = ""
        self.is_collecting = False
    
    def start_collection(self):
        """Start collecting phone number"""
        self.reset()
        self.is_collecting = True
        
    def add_digit(self, digit: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Add a digit to the current collection.
        Returns: (is_complete, phone_number, error_message)
        """
        if not self.is_collecting:
            return False, None, None
            
        if digit == '*':  # Reset
            self.digits = ""
            return False, None, "ഫോൺ നമ്പർ റീസെറ്റ് ചെയ്തു. വീണ്ടും നൽകുക."
            
        if digit == '#':  # Confirm
            if len(self.digits) == self.max_length:
                phone = self.digits
                self.reset()
                return True, phone, None
            else:
                return False, None, f"ദയവായി {self.max_length} അക്കമുള്ള ഫോൺ നമ്പർ നൽകുക."
                
        if digit in "0123456789":
            self.digits += digit
            if len(self.digits) == self.max_length:
                phone = self.digits
                self.reset()
                return True, phone, None
            elif len(self.digits) > self.max_length:
                self.digits = ""
                return False, None, "നമ്പർ വളരെ വലുതാണ്. * അമർത്തി വീണ്ടും ശ്രമിക്കുക."
                
        return False, None, None

async def synthesize_speech_streaming(text: str) -> list:
    """Synthesize speech from text with streaming support"""
    # Generate a cache key for this text
    cache_key = hashlib.md5(text.encode()).hexdigest()
    
    # Check if we have cached audio chunks
    if cache_key in TTS_CACHE:
        cached_entry = TTS_CACHE[cache_key]
        if datetime.now() < cached_entry["expiry"]:
            logger.info(f"Using cached TTS audio for: {text[:30]}...")
            return cached_entry["chunks"]
    
    # Break text into sentences for progressive synthesis
    # Use a more efficient regex that handles multiple languages
    sentences = re.split(r'([.!?።፡]\s*)', text)
    audio_chunks = []
    
    # Group sentences into reasonable chunks (more efficient chunking)
    text_chunks = []
    current_chunk = ""
    
    for i in range(0, len(sentences), 2):
        if i < len(sentences):
            current_chunk += sentences[i]
        if i+1 < len(sentences):
            current_chunk += sentences[i+1]
            
        # More intelligent chunking - chunk at natural boundaries or maximum size
        if (len(current_chunk) > 50 or  # Increased from 30 for efficiency
            i+2 >= len(sentences) or
            (len(current_chunk) > 30 and current_chunk.endswith(('.', '!', '?', '።', '፡')))):
            text_chunks.append(current_chunk)
            current_chunk = ""
    
    # If there's any remaining text, add it as a chunk
    if current_chunk:
        text_chunks.append(current_chunk)
    
    # Skip empty chunks and combine very small chunks
    optimized_chunks = []
    temp_chunk = ""
    
    for chunk in text_chunks:
        if not chunk.strip():
            continue
            
        # Combine very small chunks
        if len(chunk) < 15 and temp_chunk:
            temp_chunk += chunk
        else:
            if temp_chunk:
                optimized_chunks.append(temp_chunk)
                temp_chunk = ""
            if len(chunk) < 15:
                temp_chunk = chunk
            else:
                optimized_chunks.append(chunk)
    
    if temp_chunk:
        optimized_chunks.append(temp_chunk)
        
    text_chunks = optimized_chunks
    
    # Process each chunk in parallel
    async def process_chunk(chunk):
        try:
            # Check if this chunk is already in cache (sub-chunk caching)
            chunk_key = hashlib.md5(chunk.encode()).hexdigest()
            if chunk_key in TTS_CACHE:
                cached_chunk = TTS_CACHE[chunk_key]
                if datetime.now() < cached_chunk["expiry"]:
                    logger.debug(f"Using cached TTS for chunk: {chunk[:20]}...")
                    return cached_chunk["chunks"][0]  # Return the first (only) chunk
            
            input_text = texttospeech.SynthesisInput(text=chunk)
            voice = texttospeech.VoiceSelectionParams(
                language_code=SPEECH_LANGUAGE_CODE,
                name=SPEECH_VOICE_NAME
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                sample_rate_hertz=SPEECH_SAMPLE_RATE
            )
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: tts_client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)
            )
            
            audio_content = response.audio_content
            
            # Cache this chunk
            TTS_CACHE[chunk_key] = {
                "chunks": [audio_content],
                "expiry": datetime.now() + TTS_CACHE_TTL
            }
            
            return audio_content
        except Exception as e:
            logger.error(f"Error synthesizing chunk: {e}")
            return None
    
    # Process first chunk immediately to reduce latency
    if text_chunks:
        first_chunk_audio = await process_chunk(text_chunks[0])
        if first_chunk_audio:
            audio_chunks.append(first_chunk_audio)
        
        # Process remaining chunks in parallel
        if len(text_chunks) > 1:
            tasks = [process_chunk(chunk) for chunk in text_chunks[1:]]
            remaining_chunks = await asyncio.gather(*tasks)
            audio_chunks.extend([chunk for chunk in remaining_chunks if chunk])
    
    # Cache the complete result
    if audio_chunks:
        TTS_CACHE[cache_key] = {
            "chunks": audio_chunks,
            "expiry": datetime.now() + TTS_CACHE_TTL
        }
    
    return audio_chunks

class ExotelBot:
    """Main bot class for handling calls"""
    
    def __init__(self):
        """Initialize the bot"""
        # Initialize basic components first
        self.websocket = None
        self.transcriber = None
        self.call_active = False
        self.chat_session = None
        self.call_id = None
        self.loop = None
        self.customer_info = None
        self.phone_collector = PhoneNumberCollector()
        self.last_message = None
        self.db = CustomerDatabaseManager()
        self.conversation_history = []
        self.last_context = None
        self.waiting_for_phone = False
        self.call_memory = None
        self.silence_counter = 0
        self.max_silence_responses = 2
        self.last_message_timestamp = datetime.now()
        self.last_user_speaking_time = None
        self.gemini_lock = asyncio.Lock()  # Add lock for Gemini API calls
        
        # Initialize escalation manager and Supabase manager
        self.escalation_manager = EscalationManager()
        self.supabase_manager = SupabaseManager()
        
        # Test Supabase permissions for escalations table
        if hasattr(self.supabase_manager, 'test_escalations_permissions'):
            permissions_ok = self.supabase_manager.test_escalations_permissions()
            if not permissions_ok:
                logger.warning("⚠️ Supabase escalations permissions test failed - escalations may not be recorded")
            else:
                logger.info("✅ Supabase escalations permissions verified")
        
        # Preload RAG knowledge for common troubleshooting scenarios
        self.preloaded_rag_data = self._preload_rag_knowledge()
        logger.info(f"Preloaded {len(self.preloaded_rag_data)} RAG knowledge entries")
        
        # Now reset state which uses the initialized components
        self._reset_state()
        
        # Initialize transcript enhancer
        common_phrases_path = os.path.join(os.path.dirname(__file__), "data", "common_phrases.txt")
        self.transcript_enhancer = TranscriptEnhancer(common_phrases_file=common_phrases_path)
        
        # Paths for temporary audio files
        self.data_dir = os.path.join(os.path.dirname(__file__), "data")
        self.temp_dir = os.path.join(self.data_dir, "temp")
        self.recordings_dir = os.path.join(self.data_dir, "recordings")
        self.tts_output_path = os.path.join(self.temp_dir, "tts_output.wav")
        self._ensure_directories_exist()
        
        # Recording related attributes
        self.recording_file = None
        self.recording_path = None

    def _preload_rag_knowledge(self) -> Dict[str, str]:
        """Preload all RAG knowledge to reduce latency during calls"""
        try:
            # Import knowledge base module
            from data.knowledge_base import get_troubleshooting_response
            
            # Define common troubleshooting queries to preload
            preload_queries = [
                # Red light issues
                "red light on modem", "ചുവപ്പ് ലൈറ്റ് മോഡത്തിൽ", "മോഡത്തിൽ റെഡ് ലൈറ്റ്",
                # No power issues
                "modem not turning on", "മോഡം ഓണാകുന്നില്ല", "power issue",
                # WiFi issues
                "wifi not connecting", "വൈഫൈ കണക്റ്റ് ചെയ്യുന്നില്ല", "wifi password",
                # Slow speed
                "slow internet", "വേഗത കുറവാണ്", "internet speed slow",
                # Disconnection
                "internet keeps disconnecting", "നെറ്റ് ഇടയ്ക്കിടെ പോകുന്നു", "connection drops",
                # Basic troubleshooting
                "router restart", "റൗട്ടർ റീസ്റ്റാർട്ട്", "reset modem", "check cables",
                # Fiber issues
                "fiber cable", "ഫൈബർ കേബിൾ", "optical signal", "LOS light",
                # Payment issues
                "payment", "പേയ്മെന്റ്", "recharge", "bill"
            ]
            
            # Create a dummy customer info for preloading
            dummy_customer_info = {
                "name": "Customer",
                "device_type": "fiber_modem"
            }
            
            # Preload knowledge for all queries
            preloaded_data = {}
            for query in preload_queries:
                # Use the function from knowledge_base
                result = get_troubleshooting_response(query, dummy_customer_info)
                if result and result.get("response"):
                    # Use a hash of the query as key
                    key = hashlib.md5(query.encode()).hexdigest()
                    preloaded_data[key] = result["response"]
                    
                    # Also store common variations of the query
                    for term in ["problem", "issue", "not working"]:
                        variation_key = hashlib.md5(f"{query} {term}".encode()).hexdigest()
                        preloaded_data[variation_key] = result["response"]
            
            return preloaded_data
        except Exception as e:
            logger.error(f"Error preloading RAG knowledge: {e}")
            return {}

    def _ensure_directories_exist(self):
        """Ensure all required directories exist"""
        for directory in [self.temp_dir, self.recordings_dir]:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory)
                    logger.info(f"Created directory: {directory}")
                except Exception as e:
                    logger.error(f"Error creating directory {directory}: {e}")

    def _start_recording(self):
        """Start recording the call"""
        try:
            # Create call-specific directory
            call_dir = os.path.join(self.recordings_dir, self.call_id)
            os.makedirs(call_dir, exist_ok=True)
            
            # Initialize recording file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.recording_path = os.path.join(call_dir, f"{timestamp}.wav")
            
            # Initialize WAV file with proper parameters for stereo
            self.recording_file = wave.open(self.recording_path, 'wb')
            self.recording_file.setnchannels(2)  # Stereo (2 channels)
            self.recording_file.setsampwidth(2)  # 2 bytes per sample (16-bit)
            self.recording_file.setframerate(8000)  # 8kHz sample rate
            
            logger.info(f"Started recording call {self.call_id} to {self.recording_path}")
        except Exception as e:
            logger.error(f"Error starting call recording: {e}")
            self.recording_file = None

    def _stop_recording(self):
        """Stop recording the call"""
        try:
            if self.recording_file:
                self.recording_file.close()
                logger.info(f"Finished recording call {self.call_id}")
                self.recording_file = None
                
                # Save call metadata
                metadata = {
                    "call_id": self.call_id,
                    "start_time": self.call_memory.start_time.isoformat() if self.call_memory else None,
                    "end_time": datetime.now().isoformat(),
                    "customer_phone": self.customer_info.get("phone") if self.customer_info else None,
                    "status": self.call_memory.status.value if self.call_memory else None,
                }
                
                metadata_path = os.path.join(os.path.dirname(self.recording_path), "metadata.json")
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                    
        except Exception as e:
            logger.error(f"Error stopping call recording: {e}")

    def _add_to_recording(self, audio_data: bytes, is_bot_audio: bool = False):
        """Add audio data to the recording
        
        Args:
            audio_data: The audio data to add
            is_bot_audio: True if this is bot audio, False if customer audio
        """
        try:
            if self.recording_file:
                # Convert mono to stereo by duplicating the channel
                # and zeroing out the unused channel
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                stereo = np.zeros((len(audio_array), 2), dtype=np.int16)
                
                if is_bot_audio:
                    # Bot audio goes to right channel
                    stereo[:, 1] = audio_array
                else:
                    # Customer audio goes to left channel
                    stereo[:, 0] = audio_array
                
                self.recording_file.writeframes(stereo.tobytes())
        except Exception as e:
            logger.error(f"Error adding audio to recording: {e}")

    def _reset_state(self):
        """Reset all state variables for a new call"""
        self.call_active = False
        self.call_id = None
        self.customer_info = None
        self.phone_collector.reset()
        self.last_message = None
        self.conversation_history = []
        self.last_context = None
        self.waiting_for_phone = False
        self.silence_counter = 0
        self.loop = asyncio.get_event_loop()
        if hasattr(self, 'transcriber') and self.transcriber:
            self.transcriber.stop()
            self.transcriber = None
            
        # Reset escalation manager for new call
        if hasattr(self, 'escalation_manager'):
            self.escalation_manager.reset()
            
        gemini_model = genai.GenerativeModel("gemini-2.0-flash-lite")
        self.chat_session = gemini_model.start_chat(history=[
            {
                "role": "user",
                "parts": [
                    "You are a Malayalam-speaking support bot for an internet service provider.You help customers with issues related to internet connection problems, slow speed, payment issues, and billing queries. Always reply only in Malayalam, using short, clear, and friendly sentences. Be warm, patient, and empathetic in every interaction."
                ]
            }
        ])
        logger.info("Bot state reset for new call")
        self.call_memory = CallMemory(call_id=self.call_id)
        self.waiting_for_phone = True

    async def play_message(self, text: str):
        """Play message to user with streaming support"""
        try:
            if not self.websocket or not self.call_active:
                return None
            
            # Track performance
            start_time = time.time()
            
            # Get audio chunks with streaming synthesis
            audio_chunks = await synthesize_speech_streaming(text)
            
            if not audio_chunks:
                logger.error("No audio chunks generated")
                return None
            
            synthesis_time = time.time() - start_time
            logger.debug(f"TTS synthesis completed in {synthesis_time:.3f}s for text: {text[:30]}...")
            
            # Play first chunk immediately for faster response
            first_chunk = audio_chunks[0]
            self._add_to_recording(first_chunk, is_bot_audio=True)
            
            first_response = {
                "event": "media",
                "media": {
                    "payload": base64.b64encode(first_chunk).decode('utf-8')
                }
            }
            await self.websocket.send(json.dumps(first_response))
            logger.info(f"Sent first TTS chunk in {time.time() - start_time:.3f}s: {text[:30]}...")
            
            # Process remaining chunks in batches to reduce overhead
            remaining_chunks = audio_chunks[1:]
            batch_size = 3  # Process chunks in batches of 3 for better throughput
            
            for i in range(0, len(remaining_chunks), batch_size):
                batch = remaining_chunks[i:i+batch_size]
                batch_tasks = []
                
                for chunk in batch:
                    # Create task for each chunk in the batch
                    batch_tasks.append(self._send_audio_chunk(chunk))
                
                # Process batch in parallel
                if batch_tasks:
                    await asyncio.gather(*batch_tasks)
                    
                # Small delay between batches to avoid network congestion
                if i + batch_size < len(remaining_chunks):
                    await asyncio.sleep(0.02)
            
            total_time = time.time() - start_time
            logger.info(f"Completed sending TTS message in {total_time:.3f}s: {text[:50]}...")
            return first_response
        except Exception as e:
            logger.error(f"Error playing message: {e}")
            return None

    async def _send_audio_chunk(self, chunk):
        """Send a single audio chunk with optimized processing"""
        try:
            # Add to recording
            self._add_to_recording(chunk, is_bot_audio=True)
            
            # Prepare and send response
            chunk_response = {
                "event": "media",
                "media": {
                    "payload": base64.b64encode(chunk).decode('utf-8')
                }
            }
            await self.websocket.send(json.dumps(chunk_response))
            return True
        except Exception as e:
            logger.error(f"Error sending audio chunk: {e}")
            return False

    async def handle_message(self, data):
        """Handle incoming websocket messages"""
        try:
            event = data.get("event")
            logger.debug(f"Received event: {event}")
            
            if event == "connected":
                logger.info("WebSocket connected")

            elif event == "start":
                self._reset_state()
                self.call_id = f"call_{int(time.time())}"
                self.call_active = True
                self.call_memory = CallMemory(call_id=self.call_id)
                logger.info(f"Call started: {self.call_id}")
                
                # Start recording the call
                self._start_recording()
                
                # Get time-appropriate greeting
                time_greeting = self._get_time_of_day_greeting()
                
                # More conversational initial greeting
                greeting = (
                    f"{time_greeting}! സ്കൈ വിഷനിലേക്ക് വിളിച്ചതിന് നന്ദി. "
                    f"എന്റെ പേര് അഞ്ജലി."
                    f"ദയവായി രജിസ്ട്രേഷനോടൊപ്പം ഉപയോഗിച്ച 10 അക്ക ഫോൺ നമ്പർ ടൈപ്പ് ചെയ്യാമോ?"
                )
                
                await self.play_message(greeting)
                
                # Start collecting phone number
                self.phone_collector.start_collection()
                    
            elif event == "dtmf":
                if not self.call_active:
                    return
                    
                # Extract DTMF digit from Exotel message format
                dtmf_data = data.get("dtmf", {})
                if isinstance(dtmf_data, dict):
                    digit = dtmf_data.get("digit")
                else:
                    digit = dtmf_data
                
                logger.info(f"Received DTMF data: {dtmf_data}, extracted digit: {digit}")
                
                if digit and isinstance(digit, str):
                    await self.handle_dtmf(digit)
                    
            elif event == "media":
                if not self.call_active:
                    return
                    
                payload = data.get("media", {}).get("payload")
                if payload:
                    # Decode base64 audio data
                    audio_data = base64.b64decode(payload)
                    
                    # Add customer audio to recording (left channel)
                    self._add_to_recording(audio_data, is_bot_audio=False)
                    
                    # Process for transcription
                    if self.transcriber is None:
                        self.transcriber = RealTimeTranscriber(
                            on_transcript_callback=self.on_transcription,
                            loop=self.loop
                        )
                    self.transcriber.add_audio(payload)

            elif event == "stop":
                logger.info(f"Call {self.call_id} ended")
                self.call_active = False
                if self.transcriber:
                    self.transcriber.stop()
                # Stop recording
                self._stop_recording()
                if self.call_memory and self.call_memory.status == CallStatus.ACTIVE:
                    self.call_memory.status = CallStatus.DISCONNECTED
                    await self._send_call_summary()

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            if self.call_memory:
                self.call_memory.status = CallStatus.DISCONNECTED
                await self._send_call_summary()

    def is_inappropriate_content(self, text: str) -> bool:
        """Check if text contains inappropriate content"""
        # List of inappropriate words or patterns to check for
        inappropriate_patterns = [
            r'സെക്സ്',  # No word boundary for non-Latin scripts
            r'\bsex\b',
            r'\bporn\b',
            r'\bxxx\b',
            # Add more patterns as needed
        ]
        
        # Convert to lowercase for case-insensitive matching
        text_lower = text.lower()
        
        # Check each pattern
        for pattern in inappropriate_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                # Log to warning
                logger.warning(f"Detected inappropriate content, filtered: {pattern}")
                
                # Log to separate file for monitoring
                try:
                    # Create logs directory if it doesn't exist
                    os.makedirs("logs", exist_ok=True)
                    
                    with open("logs/content_filter.log", "a", encoding="utf-8") as f:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        call_id = self.call_id if self.call_id else "unknown"
                        phone = self.call_memory.phone_number if self.call_memory and self.call_memory.phone_number else "unknown"
                        f.write(f"{timestamp} | Call: {call_id} | Phone: {phone} | Filtered: {text}\n")
                except Exception as e:
                    logger.error(f"Error logging to content filter log: {e}")
                
                return True
        
        return False

    def _is_silence(self, text: str) -> bool:
        """Check if the transcript is likely from silence/background noise"""
        # Skip empty or very short texts
        if not text or len(text.strip()) <= 1:
            return True
            
        # Check if the text only contains the commonly misinterpreted word
        if text.strip() in ["സെക്സ്", "sex"]:
            logger.info("Detected standalone inappropriate word - likely silence misinterpretation")
            return True
            
        # Check if the text is very short (1-2 words) and contains the problematic word
        if len(text.split()) <= 2 and ("സെക്സ്" in text or "sex" in text):
            logger.info("Detected short phrase with inappropriate word - likely silence misinterpretation")
            return True
            
        return False

    async def on_transcription(self, text: str):
        """Handle transcribed speech with streaming optimizations"""
        try:
            # Skip processing if call is not active
            if not self.call_active or (self.call_memory and self.call_memory.status != CallStatus.ACTIVE):
                logger.info(f"Ignoring transcription for inactive call: {text}")
                return
                
            # IMPORTANT: If we're waiting for phone number collection, ignore all transcriptions
            if self.waiting_for_phone:
                logger.info(f"Ignoring transcription while waiting for phone number: {text}")
                return
                
            # Skip if silence detected
            if self._is_silence(text):
                logger.info(f"Silence detected, ignoring: '{text}'")
                return
                
            # Skip if text has "(interim)" marker from streaming recognition
            if "(interim)" in text:
                logger.debug(f"Skipping interim result: {text}")
                return
                
            # Log the original transcript for debugging
            logger.debug(f"Original transcript: {text}")
            
            # Track processing time
            start_time = time.time()
            
            # Enhance transcript quality
            if hasattr(self, 'transcript_enhancer') and self.conversation_history:
                # Update context from conversation history
                self.transcript_enhancer.update_context(self.conversation_history)
                
                # Apply transcript enhancement
                enhanced_text = self.transcript_enhancer.enhance(text)
                
                # Log the enhanced transcript
                if enhanced_text != text:
                    logger.info(f"Enhanced transcript: '{text}' → '{enhanced_text}'")
                    text = enhanced_text
            
            # Track the current conversation state for better troubleshooting flow
            current_issue = None
            troubleshooting_stage = "identification"
            if self.call_memory and self.call_memory.troubleshooting_steps:
                # Check the last 3 exchanges to determine current state
                recent_steps = self.call_memory.troubleshooting_steps[-3:]
                
                # Look for specific issue identifiers in recent exchanges
                issue_indicators = {
                    "red_light": ["ചുവപ്പ് ലൈറ്റ്", "റെഡ് ലൈറ്റ്", "red light"],
                    "no_power": ["ലൈറ്റ് വരുന്നില്ല", "power", "പവർ", "ഓണാകുന്നില്ല"],
                    "wifi_issues": ["വൈഫൈ", "wifi", "കണക്ട്", "connect"],
                    "slow_speed": ["സ്ലോ", "slow", "വേഗത കുറവ്", "speed"],
                    "disconnection": ["ഡിസ്കണക്ട്", "disconnect", "കട്ടാകുന്നു"]
                }
                
                # Check for issue indicators in recent conversation
                for issue, terms in issue_indicators.items():
                    for step in recent_steps:
                        if any(term in step.step.lower() for term in terms):
                            current_issue = issue
                            troubleshooting_stage = "diagnosis"
                            break
                    if current_issue:
                        break
                
                # Check if we've moved to solution phase
                solution_indicators = ["try", "ശ്രമിക്കുക", "restart", "റീസ്റ്റാർട്ട്", "reset", "റീസെറ്റ്"]
                if any(any(term in step.result.lower() for term in solution_indicators) for step in recent_steps):
                    troubleshooting_stage = "solution"
            
            # Check if text is too short or likely misheard
            is_unclear = len(text.strip().split()) <= 2 or text.strip() in ["അത്", "എന്ത്", "എന്താ", "സ്വാസ്"]
            
            # Check if text is completely unrelated to ISP services
            isp_related_terms = ["ഇന്റർനെറ്റ്", "നെറ്റ്", "കണക്ഷൻ", "വൈഫൈ", "റൗട്ടർ", "മോഡം", "സ്പീഡ്", "ലൈറ്റ്", "റീചാർജ്", "ബിൽ", "പേയ്മെന്റ്"]
            is_completely_unrelated = all(term not in text for term in isp_related_terms) and len(text.strip().split()) > 3
            
            # Add to conversation history regardless of clarity
            self.conversation_history.append({
                "user": text,
                "bot": "",
                "timestamp": datetime.now().isoformat()
            })
            
            # Start RAG context fetching immediately and in parallel
            rag_task = asyncio.create_task(self._get_rag_context(text))
            
            # Get model context with customer info
            model_context = self.call_memory.get_model_context() if self.call_memory else ""
            customer_name = self.call_memory.customer_name if self.call_memory else "Customer"
            
            # Get previous exchanges for context
            previous_exchanges = ""
            if len(self.conversation_history) > 1:
                last_exchanges = self.conversation_history[-5:-1]  # Get 4 previous exchanges
                for exchange in last_exchanges:
                    previous_exchanges += f"User: {exchange.get('user', '')}\n"
                    previous_exchanges += f"Anjali: {exchange.get('bot', '')}\n"
            
            # Start creating the prompt in parallel with RAG retrieval
            base_prompt = f"""Context:
{model_context}

Previous exchanges:
{previous_exchanges}

Current user message: {text}

Current troubleshooting state:
- Issue: {current_issue if current_issue else "Not yet identified"}
- Stage: {troubleshooting_stage}
"""
            
            # Different instruction sets based on clarity
            if is_unclear or is_completely_unrelated:
                instructions = """
Instructions:
1. The user's message is UNCLEAR, VERY SHORT, or POSSIBLY UNRELATED to ISP services
2. This is likely due to transcription issues or background noise
3. DO NOT tell the user you couldn't understand them or ask what they meant
4. DO NOT repeat back what they said or ask "did you mean X?"
5. Instead, maintain the current troubleshooting flow based on previous exchanges
6. If you've already identified a problem (red light, no power, WiFi issues), continue diagnosing that specific issue
7. Ask precise, focused questions that follow a logical troubleshooting sequence
8. NEVER ask the user to send photos, screenshots, or any visual content
9. Respond as if you understood perfectly, in a natural and helpful way
10. Keep your response conversational and use simple, everyday Malayalam language
11. Focus only on ISP-related topics, even if the transcript seems unrelated"""
            else:
                instructions = """
Instructions:
1. Create a natural, flowing response in Malayalam that sounds like a real person talking
2. Follow a structured troubleshooting approach:
   - IDENTIFICATION: First clearly identify the exact problem (red light, no power, WiFi issue, etc.)
   - DIAGNOSIS: Ask targeted questions to pinpoint the specific issue
   - SOLUTION: Provide specific, step-by-step instructions once the issue is clear
3. Don't jump between different issues - focus on solving one problem at a time
4. Use the technical information ONLY as reference - adapt to what the user is actually telling you
5. Ask ONE specific question at a time, following a logical troubleshooting sequence
6. Wait for answers before moving to the next step
7. Vary your sentence structures and opening phrases
8. Avoid starting with the customer's name (use it sparingly)
9. Get straight to the point without unnecessary words
10. If you don't understand what the customer is saying, stay on the current troubleshooting path
11. NEVER ask the customer to send photos, screenshots, or any visual media
12. Remember you're on a voice-only phone call - only suggest actions possible over the phone"""
            
            # Try to get RAG context quickly (using preloaded data)
            try:
                # Use a shorter timeout since we have preloaded data
                rag_context = await asyncio.wait_for(rag_task, 0.3)
                logger.debug(f"RAG context retrieved in {time.time() - start_time:.3f}s")
                
                # Only add RAG context if available
                if rag_context:
                    technical_reference = f"""
Technical Reference (use ONLY as a guide, not a script to follow):
{rag_context}
"""
                    # Insert technical reference before instructions
                    prompt = base_prompt + technical_reference + instructions
                else:
                    prompt = base_prompt + instructions
            except asyncio.TimeoutError:
                # If RAG lookup takes too long, proceed without it
                logger.info(f"RAG context timed out after {time.time() - start_time:.3f}s, proceeding without it")
                prompt = base_prompt + instructions
            
            # Record time before making Gemini call
            pre_gemini_time = time.time()
            logger.debug(f"Prompt preparation completed in {pre_gemini_time - start_time:.3f}s")
            
            # Get AI response with streaming
            response_text = await query_gemini(prompt, self.chat_session, self.gemini_lock)
            
            # Log time for Gemini response
            post_gemini_time = time.time()
            logger.debug(f"Gemini response generated in {post_gemini_time - pre_gemini_time:.3f}s")
            
            # Play the response immediately
            await self.play_message(response_text)
            
            # Log total processing time
            logger.info(f"Total processing time: {time.time() - start_time:.3f}s")

            # Add response to conversation history
            self.conversation_history[-1]["bot"] = response_text

            # Update call memory
            if self.call_memory:
                self.call_memory.add_troubleshooting_step(text, response_text)
                
                # Check for escalation triggers
                await self._check_for_escalation(text, response_text)

        except Exception as e:
            logger.error(f"Error in transcription handling: {e}")
            error_response = "ക്ഷമിക്കണം, ഒരു ചെറിയ സാങ്കേതിക പ്രശ്നമുണ്ട്. ദയവായി ഒരു നിമിറ്റം കാത്തിരിക്കൂ, ഞാൻ വീണ്ടും ശ്രമിക്കാം."
            await self.play_message(error_response)
    
    async def _get_rag_context(self, text: str) -> str:
        """Get RAG context with preloaded data for faster response"""
        try:
            # Extract key technical terms for better RAG matching
            technical_terms = self.extract_technical_terms(text)
            enhanced_query = f"{text} {' '.join(technical_terms)}"
            
            # Generate a cache key for this query
            cache_key = hashlib.md5(enhanced_query.encode()).hexdigest()
            
            # Check if we have a cached result
            if cache_key in RAG_CACHE:
                cached_entry = RAG_CACHE[cache_key]
                if datetime.now() < cached_entry["expiry"]:
                    logger.info(f"Using cached RAG context for: {text[:50]}...")
                    return cached_entry["context"]
            
            # First check if we have preloaded data that matches
            start_time = time.time()
            best_match = None
            best_match_score = 0
            
            # Try to find the best match from preloaded data
            for query_key, rag_content in self.preloaded_rag_data.items():
                # Calculate a simple score based on term overlap
                score = 0
                for term in technical_terms:
                    if term.lower() in rag_content.lower():
                        score += 1
                
                if score > best_match_score:
                    best_match_score = score
                    best_match = rag_content
            
            # If we found a good match, use it directly
            if best_match and best_match_score >= 1:
                logger.info(f"Found preloaded RAG match in {time.time() - start_time:.3f}s with score {best_match_score}")
                
                # Cache the result
                RAG_CACHE[cache_key] = {
                    "context": best_match,
                    "expiry": datetime.now() + RAG_CACHE_TTL
                }
                
                return best_match
            
            # If no good match, fall back to normal query
            logger.info(f"No preloaded match, using regular RAG query: {enhanced_query}")
            
            # Use get_troubleshooting_response instead of direct query
            from data.knowledge_base import get_troubleshooting_response
            
            # Get customer info for context
            customer_info = {
                "name": self.call_memory.customer_name if self.call_memory and self.call_memory.customer_name else "",
                # Safely get device_type if it exists as an attribute
                "device_type": getattr(self.call_memory, "device_type", "fiber_modem") if self.call_memory else "fiber_modem"
            }
            
            # Get troubleshooting response as reference material, not script
            response_data = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: get_troubleshooting_response(enhanced_query, customer_info)
            )
            
            if response_data and response_data.get("response"):
                rag_context = response_data["response"]
                logger.info(f"RAG context found in {time.time() - start_time:.3f}s: {rag_context[:100]}...")
                
                # Cache the result
                RAG_CACHE[cache_key] = {
                    "context": rag_context,
                    "expiry": datetime.now() + RAG_CACHE_TTL
                }
                
                return rag_context
                
            # For empty responses, cache that too to avoid redundant lookups
            RAG_CACHE[cache_key] = {
                "context": "",
                "expiry": datetime.now() + RAG_CACHE_TTL
            }
            
        except Exception as e:
            logger.error(f"Error querying knowledge base: {e}")
        
        return ""
    
    def extract_technical_terms(self, text: str) -> list:
        """Extract technical terms from text to enhance RAG queries"""
        technical_terms = []
        
        # List of technical terms to look for
        term_mapping = {
            # Lights / Indicators
            "റെഡ് ലൈറ്റ്": "red light",
            "പച്ച ലൈറ്റ്": "green light",
            "മഞ്ഞ ലൈറ്റ്": "yellow light",
            "ലൈറ്റ്": "light",
            "ലാമ്പ്": "light",
            "കണക്ഷൻ ലൈറ്റ്": "connection light",
            "ഇൻറർനെറ്റ് ലൈറ്റ്": "internet light",
            "മോഡം": "modem",
            "റൗട്ടർ": "router",
            "റൂട്ടർ": "router",
            "വൈഫൈ": "wifi",
            "വൈ ഫൈ": "wifi",
            "ഹബ്ബ്": "hub",
            "ഡിവൈസ്": "device",
                "ഇന്റർനെറ്റ്": "internet",
            "ഇൻറർനെറ്റ്": "internet",
            "ഇന്റർനറ്റ്": "internet",
            "നെറ്റ്": "internet",
            "നെറ്റ് കണക്ഷൻ": "internet connection",
            "കണക്ഷൻ": "connection",
            "നെറ്റ് പോയം": "internet not working",
            "നെറ്റ് ഇല്ല": "no internet",
            "ഡാറ്റ": "data",
            "ഡാറ്റ പൊയി": "data not working",
            "ഡാറ്റ ഇല്ല": "no data",
            "സ്പീഡ്": "speed",
            "സ്ലോ": "slow",
            "നെറ്റ് സ്ലോ": "slow internet",
            "നെറ്റ് കട്ട്": "internet disconnected",
            "നിലവിൽ ഇല്ല": "not available",
            "വേറിയ സ്ലോ": "very slow",
            "ബ്രേക്ക്": "disconnect",
            "ഓഫായിരിക്കുന്നു": "turned off",
            "പോയി": "gone",
            "ഡൗൺ": "down",
            "ഇല്ല": "not working",
            "റീചാർജ്": "recharge",
            "റീചാർജ് ചെയ്തു": "recharged",
            "റീചാർജ് വേണ്ടേ": "need recharge",
            "അപ്ഡേറ്റ്": "update",
            "ഓൺ": "on",
            "ഓഫ്": "off",
            "ഓണാക്കൂ": "turn on",
            "ഓഫാക്കൂ": "turn off",
            "റീസെറ്റ്": "reset",
            "പ്ലഗ്": "plug",
            "അൺപ്ലഗ്": "unplug",
            "റീസ്റ്റാർട്ട്": "restart",
            "കണക്ട്": "connect",
            "ഡിസ്കണക്റ്റ്": "disconnect",
            "ടെക്‌നീഷ്യൻ": "technician",
            "ടെക്നീഷ്യൻ": "technician",
            "സപ്പോർട്ട്": "support",
            "കസ്റ്റമർ": "customer",
            "എക്‌സിക്യൂട്ടീവ്": "executive",
            "ഹെല്പ്": "help",
            "സഹായം": "help",
            "അഞ്‌ജലി": "Anjali",
            "ഇന്നലെ": "yesterday",
            "ഇന്ന്": "today",
            "രാവിലെ": "morning",
            "വൈകുന്നേരം": "evening",
            "രാത്രി": "night",
            "നെറ്റ് വരുന്നില്ല": "no internet",
            "നെറ്റ് ഇല്ല": "no internet",
            "നെറ്റ് കിട്ടുന്നില്ല": "no internet",
            "നെറ്റ് കിട്ടുന്നില്ല": "no internet",
            "കണക്ഷൻ കിട്ടുന്നില്ല": "no connection",
            "വേഗത കുറവാണ്": "low speed",
            "വേഗം കുറവാണ്": "low speed",
            "വേഗത കുറവുണ്ട്": "low speed",
            "വേഗം കുറവുണ്ട്": "low speed",
            "വേഗത കുറവുണ്ട്": "low speed",
            "വേഗം കുറവുണ്ട്": "low speed",
            "വേഗത കുറവുണ്ട്": "low speed",
            "വേഗം കുറവുണ്ട്": "low speed",
                    
        }
        
        # Check for each term
        for term, english in term_mapping.items():
            if term in text:
                technical_terms.append(term)
                technical_terms.append(english)
                
        return technical_terms

    async def _check_for_escalation(self, user_text: str, bot_response: str):
        """Check if escalation is needed and handle it"""
        try:
            if not self.call_memory or not hasattr(self, 'escalation_manager'):
                return
                
            # Update escalation manager with current conversation state
            customer_info = self.call_memory.customer_info or {}
            
            # Determine issue type and sub-issues based on conversation
            issue_type = self.call_memory.issue_type or "internet_down"
            sub_issues = self.call_memory.sub_issues or []
            
            # Calculate confidence based on conversation clarity
            confidence = 0.8  # Default confidence
            if len(user_text.strip().split()) <= 2:
                confidence = 0.4  # Low confidence for unclear messages
            elif len(user_text.strip().split()) >= 10:
                confidence = 0.9  # High confidence for detailed messages
            
            # Check if escalation is needed
            should_escalate = self.escalation_manager.should_escalate(
                failed_steps=len([step for step in self.call_memory.troubleshooting_steps if "ശരിയായില്ല" in step.result or "ഇല്ല" in step.result]),
                total_steps=len(self.call_memory.troubleshooting_steps),
                issue_type=issue_type,
                sub_issues=sub_issues,
                confidence=confidence,
                customer_info=customer_info,
                conversation_history=self.call_memory.conversation_history,
                previous_issues=[]  # Could be populated from database if needed
            )
            
            if should_escalate:
                # Get escalation reasons
                escalation_reasons = self.escalation_manager.get_escalation_reasons()
                
                # Update call memory
                self.call_memory.status = CallStatus.ESCALATED
                self.call_memory.escalation_reasons.extend(escalation_reasons)
                
                # Log escalation
                logger.info(f"Call {self.call_id} escalated due to: {', '.join(escalation_reasons)}")
                
                # Create escalation in database
                await self._create_escalation_in_database(escalation_reasons)
                
                # Play escalation message
                escalation_msg = (
                    "ക്ഷമിക്കണം, നിങ്ങളുടെ പ്രശ്നം പരിഹരിക്കാൻ എനിക്ക് കഴിയുന്നില്ല. "
                    "ഞാൻ നിങ്ങളെ ഒരു സാങ്കേതിക വിദഗ്ധനുമായി ബന്ധിപ്പിക്കാൻ പോകുന്നു. "
                    "ദയവായി കാത്തിരിക്കൂ."
                )
                await self.play_message(escalation_msg)
                
        except Exception as e:
            logger.error(f"Error checking for escalation: {e}")

    async def _create_escalation_in_database(self, escalation_reasons: List[str]):
        """Create escalation entry in Supabase database"""
        try:
            if not self.call_memory or not hasattr(self, 'supabase_manager'):
                logger.warning("Cannot create escalation: missing call memory or supabase manager")
                return
                
            # Prepare escalation data
            customer_info = self.call_memory.customer_info or {}
            issue_type = self.call_memory.issue_type or "internet_down"
            
            # Create conversation summary
            conversation_summary = ""
            if self.call_memory.conversation_history:
                recent_exchanges = self.call_memory.conversation_history[-10:]  # Last 10 exchanges
                for exchange in recent_exchanges:
                    if "user" in exchange and "bot" in exchange:
                        conversation_summary += f"User: {exchange['user']}\n"
                        conversation_summary += f"Bot: {exchange['bot']}\n\n"
            
            # Create troubleshooting steps summary
            troubleshooting_steps = []
            for step in self.call_memory.troubleshooting_steps:
                troubleshooting_steps.append(f"{step.step} → {step.result}")
            
            # Create escalation in database using escalation manager
            escalation_id = self.escalation_manager.create_escalation_in_database(
                issue_type=issue_type,
                customer_phone=self.call_memory.phone_number or "Unknown",
                customer_info=customer_info,
                conversation_summary=conversation_summary,
                troubleshooting_steps=troubleshooting_steps,
                escalation_reasons=escalation_reasons
            )
            
            if escalation_id:
                logger.info(f"✅ Escalation created in database: {escalation_id}")
            else:
                logger.error("❌ Failed to create escalation in database")
                # Fallback: Log escalation locally
                await self._log_escalation_locally(escalation_reasons, customer_info, issue_type, conversation_summary, troubleshooting_steps)
                
        except Exception as e:
            logger.error(f"Error creating escalation in database: {e}")
            # Fallback: Log escalation locally
            await self._log_escalation_locally(escalation_reasons, self.call_memory.customer_info or {}, self.call_memory.issue_type or "unknown", "", [])

    async def _log_escalation_locally(self, escalation_reasons: List[str], customer_info: Dict[str, Any], issue_type: str, conversation_summary: str, troubleshooting_steps: List[str]):
        """Log escalation information locally when Supabase fails"""
        try:
            # Create logs directory if it doesn't exist
            os.makedirs("logs", exist_ok=True)
            
            escalation_log = {
                "timestamp": datetime.now().isoformat(),
                "call_id": self.call_id,
                "customer_phone": self.call_memory.phone_number if self.call_memory else "Unknown",
                "issue_type": issue_type,
                "escalation_reasons": escalation_reasons,
                "customer_info": customer_info,
                "conversation_summary": conversation_summary,
                "troubleshooting_steps": troubleshooting_steps,
                "call_duration_seconds": self.call_memory.get_call_duration() if self.call_memory else 0
            }
            
            # Log to file
            with open("logs/escalations.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(escalation_log, ensure_ascii=False, indent=2) + "\n\n")
            
            logger.info(f"📝 Escalation logged locally to logs/escalations.log")
            
        except Exception as e:
            logger.error(f"Error logging escalation locally: {e}")

    async def check_if_phone_needed(self, text: str, rag_context: str) -> bool:
        """Check if phone number is needed"""
        try:
            response = await query_gemini(
                f"User said: {text}\nContext: {rag_context}\n\n"
                "Should I ask for phone number? Answer only yes or no.",
                self.chat_session,
                self.gemini_lock
            )
            return "yes" in response.lower()
        except Exception as e:
            logger.error(f"Error checking phone need: {e}")
            return True

    async def _send_call_summary(self):
        """Send call summary to database"""
        try:
            # Get customer info
            customer_info = self.call_memory.customer_info or {}
            
            # Get FULL conversation history
            conversation_history = self.call_memory.conversation_history or []
            
            # Extract recent transcripts - get more relevant ones
            recent_transcripts = []
            for entry in conversation_history[-15:]:  # Get last 15 exchanges
                if "user" in entry and entry["user"]:
                    recent_transcripts.append(entry["user"])
            
            # Extract actual troubleshooting steps from the conversation
            troubleshooting_steps = []
            if self.call_memory.troubleshooting_steps:
                for step in self.call_memory.troubleshooting_steps:
                    troubleshooting_steps.append(f"{step.step} → {step.result}")
            
            # Use more specific prompts for better results
            issue_prompt = (
                "Based on the FULL conversation history, provide a very concise (5-10 words) description of the main technical issue. "
                "Focus on the specific technical problem without explanation. "
                "Example: 'WiFi connectivity issue' or 'Router red light error' or 'Fiber cable damage'."
            )
            
            # Generate a more detailed call summary
            summary_prompt = (
                "Based on the FULL conversation history, provide a comprehensive summary (3-5 sentences) of what happened during the call. "
                "Include: 1) The customer's main issue, 2) Key troubleshooting steps taken, 3) What was discovered, and 4) The final outcome or resolution. "
                "Be specific about technical details mentioned."
            )
            
            # Generate steps tried prompt
            steps_prompt = (
                "Based on the conversation, list 3-5 specific troubleshooting steps that were attempted during the call. "
                "Format each step as a brief action statement. Only include steps that were actually tried, not suggestions. should be very consise with 1-2 sentences"
            )
            
            # Get the FULL context from the call memory
            context = self.call_memory.get_model_context()
            
            # Generate issue description, call summary, and steps tried using LLM
            issue_summary = await query_gemini(issue_prompt, self.chat_session, self.gemini_lock, context)
            call_summary = await query_gemini(summary_prompt, self.chat_session, self.gemini_lock, context)
            
            # Only generate steps if we don't have explicit troubleshooting steps recorded
            if not troubleshooting_steps:
                steps_tried = await query_gemini(steps_prompt, self.chat_session, self.gemini_lock, context)
                # Convert to list
                steps_list = [step.strip() for step in steps_tried.split('\n') if step.strip()]
                # Filter out any non-step lines (sometimes LLM adds explanatory text)
                steps_list = [step for step in steps_list if not step.startswith("Note:") and not step.startswith("*")]
                troubleshooting_steps = steps_list
            
            # Limit response length but allow for more detailed summaries
            issue_summary = _limit_response_length(issue_summary, 100)
            call_summary = _limit_response_length(call_summary, 500)  # Increased from 300 to 500
            
            # Determine resolution status
            if self.call_memory.status == CallStatus.RESOLVED:
                resolution_status = "Issue resolved successfully"
            elif self.call_memory.status == CallStatus.ESCALATED:
                resolution_status = "Issue escalated to human operator"
            else:
                resolution_status = "Call ended without resolution"
                
            # Add resolution notes if available
            if self.call_memory.resolution_notes:
                resolution_status += f": {self.call_memory.resolution_notes}"
            
            # Ensure customer info is properly set
            if not customer_info and self.call_memory.phone_number:
                # Try to get customer info again if missing
                _, customer_info = await self.validate_phone_number(self.call_memory.phone_number)
                customer_info = customer_info or {}
            
            # Log the final customer info being sent
            logger.info(f"Sending call report with customer info: {customer_info}")
            
            # Select the most relevant transcripts based on technical content
            if len(recent_transcripts) > 3:
                # Filter for technical terms to find the most relevant statements
                technical_statements = []
                for transcript in recent_transcripts:
                    terms = self.extract_technical_terms(transcript)
                    if terms:
                        technical_statements.append((transcript, len(terms)))
                
                # Sort by number of technical terms (most to least)
                technical_statements.sort(key=lambda x: x[1], reverse=True)
                
                # Take the top 3 most technical statements
                if technical_statements:
                    recent_transcripts = [s[0] for s in technical_statements[:3]]
                else:
                    # If no technical statements, take the 3 most recent
                    recent_transcripts = recent_transcripts[-3:]
            
            # Log the full summary for debugging
            logger.info(f"Call Summary for {self.call_memory.phone_number}:")
            logger.info(f"Issue: {issue_summary}")
            logger.info(f"Summary: {call_summary}")
            logger.info(f"Customer: {customer_info.get('Customer Name', customer_info.get('name', 'Unknown'))} ({customer_info.get('Provider', customer_info.get('isp', 'Unknown'))})")
            logger.info(f"Duration: {self.call_memory.get_call_duration()}s")
            logger.info(f"Status: {self.call_memory.status.value}")
            
            # Log escalation information if call was escalated
            if self.call_memory.status == CallStatus.ESCALATED and self.call_memory.escalation_reasons:
                logger.info(f"Escalation Reasons: {', '.join(self.call_memory.escalation_reasons)}")
                
                # Ensure escalation is created in database if not already done
                if hasattr(self, 'escalation_manager') and hasattr(self, 'supabase_manager'):
                    await self._create_escalation_in_database(self.call_memory.escalation_reasons)
            
        except Exception as e:
            logger.error(f"Error sending call summary: {e}")
            logger.error(f"Call memory state: {self.call_memory.generate_summary() if self.call_memory else 'No call memory'}")

    async def handle_dtmf(self, digit: str):
        """Handle DTMF input"""
        try:
            logger.info(f"Handling DTMF digit: {digit}, waiting_for_phone: {self.waiting_for_phone}")
            
            # Check for escalation request (0 key)
            if digit == "0" and not self.waiting_for_phone:
                # Customer requested escalation via DTMF
                if self.call_memory:
                    self.call_memory.status = CallStatus.ESCALATED
                    self.call_memory.escalation_reasons.append("Customer requested escalation via DTMF")
                    
                    # Create escalation in database
                    await self._create_escalation_in_database(["Customer requested escalation via DTMF"])
                    
                    # Play escalation message
                    escalation_msg = (
                        "ഞാൻ നിങ്ങളെ ഒരു സാങ്കേതിക വിദഗ്ധനുമായി ബന്ധിപ്പിക്കാൻ പോകുന്നു. "
                        "ദയവായി കാത്തിരിക്കൂ."
                    )
                    await self.play_message(escalation_msg)
                    
                    # Send call summary
                    await self._send_call_summary()
                    return
                    
            # If we're not collecting phone numbers and not escalating, start collection
            if not self.phone_collector.is_collecting:
                logger.info("Starting phone number collection")
                self.phone_collector.start_collection()
                
            is_complete, phone, error = self.phone_collector.add_digit(digit)
            logger.info(f"Phone collection result: complete={is_complete}, phone={phone}, error={error}")
            
            if error:
                # Make error messages more conversational
                friendly_errors = {
                    "ഫോൺ നമ്പർ റീസെറ്റ് ചെയ്തു. വീണ്ടും നൽകുക.": 
                        "ഫോൺ നമ്പർ റീസെറ്റ് ചെയ്തിരിക്കുന്നു. ദയവായി നിങ്ങളുടെ 10 അക്ക ഫോൺ നമ്പർ വീണ്ടും നൽകാമോ?",
                    
                    f"ദയവായി {self.phone_collector.max_length} അക്കമുള്ള ഫോൺ നമ്പർ നൽകുക.":
                        f"ക്ഷമിക്കണം, എന്നാൽ നമുക്ക് {self.phone_collector.max_length} അക്കമുള്ള ഫോൺ നമ്പർ ആണ് ആവശ്യം. ദയവായി പൂർണ്ണമായ നമ്പർ നൽകാമോ?",
                    
                    "നമ്പർ വളരെ വലുതാണ്. * അമർത്തി വീണ്ടും ശ്രമിക്കുക.":
                        "ക്ഷമിക്കണം, നമ്പർ വളരെ വലുതാണ്. * അമർത്തി റീസെറ്റ് ചെയ്ത് വീണ്ടും ശ്രമിക്കാമോ?"
                }
                
                friendly_message = friendly_errors.get(error, error)
                return await self.play_message(friendly_message)
                
            if is_complete and phone:
                logger.info(f"Validating phone number: {phone}")
                is_valid, customer_info = await self.validate_phone_number(phone)
                
                if not is_valid:
                    logger.warning(f"Invalid phone number: {phone}")
                    return await self.play_message(
                        "ക്ഷമിക്കണം, നിങ്ങളുടെ ഫോൺ നമ്പർ ഞങ്ങളുടെ സിസ്റ്റത്തിൽ കാണുന്നില്ല. "
                        "ദയവായി നമ്പർ പരിശോധിച്ച് വീണ്ടും ശ്രമിക്കുക, അല്ലെങ്കിൽ രജിസ്റ്റർ ചെയ്യാൻ ഞങ്ങളുടെ ഓഫീസുമായി ബന്ധപ്പെടാം."
                    )
                
                # Update call memory with phone and customer info
                self.call_memory.phone_number = phone
                self.call_memory.customer_info = customer_info
                self.call_memory.customer_name = customer_info.get("name")
                
                # Log the update
                logger.info(f"Updated call memory with customer info: {customer_info}")
                
                # No longer waiting for phone number
                self.waiting_for_phone = False
                logger.info(f"Set waiting_for_phone to False after successful phone validation")
                
                # Create a more personalized and warm greeting
                customer_name = customer_info.get('name', '')
                time_of_day = self._get_time_of_day_greeting()
                
                greeting_message = (
                    f"{time_of_day} {customer_name}! "
                    f"അഞ്ജലി സംസാരിക്കുന്നു. നിങ്ങളെ കണ്ടതിൽ സന്തോഷം. "
                    f"എന്താണ് പ്രശ്നം? എങ്ങനെ സഹായിക്കാം?"
                )
                
                return await self.play_message(greeting_message)
                
            return None
            
        except Exception as e:
            logger.error(f"Error handling DTMF: {e}")
            return await self.play_message("ക്ഷമിക്കണം, ഒരു ചെറിയ പ്രശ്നം ഉണ്ടായി. ഒരു നിമിഷം കാത്തിരിക്കാമോ?")
        
    def _get_time_of_day_greeting(self) -> str:
        """Return appropriate greeting based on time of day"""
        current_hour = datetime.now().hour
        
        if 4 <= current_hour < 12:
            return "സുപ്രഭാതം"  # Good morning
        elif 12 <= current_hour < 16:
            return "ഉച്ചയ്ക്ക് വന്ദനം"  # Good afternoon
        elif 16 <= current_hour < 20:
            return "സായാഹ്നം വന്ദനം"  # Good evening
        else:
            return "നമസ്കാരം"  # General greeting for night

    async def validate_phone_number(self, phone_number: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validate phone number and get customer info"""
        try:
            customer = self.db.get_customer_by_phone(phone_number)
            if not customer:
                logger.warning(f"No customer found for phone: {phone_number}")
                return False, None
            
            logger.info(f"Found customer: {customer.get('Customer Name')} for phone: {phone_number}")
            
            # Create customer info dictionary with both old and new field names for compatibility
            customer_info = {
                # New format fields
                "Customer Name": customer.get("Customer Name", "Unknown"),
                "User Name": customer.get("User Name", "Unknown"),
                "Address": customer.get("Address", "Unknown"),
                "Current Plan": customer.get("Current Plan", "Unknown"),
                "NickName": customer.get("NickName", "Unknown"),
                "Provider": customer.get("Provider", "Unknown"),
                "Subscriber Code": customer.get("Subscriber Code", "Unknown"),
                "Region": customer.get("Region", "Unknown"),
                "Operator": customer.get("Operator", "Unknown"),
                
                # Backward compatibility fields
                "name": customer.get("Customer Name", "Unknown"),
                "username": customer.get("User Name", "Unknown"),
                "plan": customer.get("Current Plan", "Unknown"),
                "operator": customer.get("Operator", "Unknown"),
                "isp": customer.get("Provider", "Unknown"),
                "services": customer.get("Current Plan", "Unknown")  # Use plan as service
            }
            
            # Update call memory with customer info
            if self.call_memory:
                self.call_memory.customer_info = customer_info
                self.call_memory.phone_number = phone_number
                logger.info(f"Updated call memory with customer info for {phone_number}")
            
            return True, customer_info
        except Exception as e:
            logger.error(f"Error validating phone: {e}")
            return False, None

    async def handle(self, websocket):
        """Main websocket handler"""
        try:
            self.websocket = websocket
            logger.info("WebSocket connection opened. Waiting for messages...")
            
            async for message in websocket:
                try:
                    if isinstance(message, str):
                        data = json.loads(message)
                        await self.handle_message(data)
                    else:
                        logger.warning(f"Received non-string message: {type(message)}")
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    
        except Exception as e:
            logger.error(f"WebSocket handler error: {e}")
        finally:
            logger.info(f"[{self.call_id}] WebSocket connection closed")
            self.call_active = False
            if self.transcriber:
                self.transcriber.stop()
            logger.info(f"[{self.call_id}] Connection cleanup completed")

    def _check_for_red_light(self, transcript: str) -> bool:
        """Check if the transcript mentions a red light, indicating fiber cut"""
        red_light_indicators = [
            "red light", "ചുവന്ന ലൈറ്റ്", "റെഡ് ലൈറ്റ്", "los", "loss", "los light", 
            "red", "ചുവന്ന", "ചുവപ്പ്", "fiber cut", "ഫൈബർ കട്ട്"
        ]
        return any(indicator in transcript.lower() for indicator in red_light_indicators)

    def _handle_red_light_fiber_cut(self) -> str:
        """Handle red light/fiber cut issue with direct instructions"""
        fiber_cut_msg = (
            "ചുവന്ന ലൈറ്റ് കാണുന്നത് ഫൈബർ കട്ട് പ്രശ്നം സൂചിപ്പിക്കുന്നു. "
            "ആദ്യം മോഡം പവർ ഓഫ് ചെയ്യുക (പ്ലഗ് സ്വിച്ച് വഴി ഓഫ് ചെയ്ത് ഓൺ ചെയ്യുക, മോഡത്തിലെ റീസ്റ്റാർട്ട് ബട്ടൺ അമർത്തരുത്). "
            "മോഡം പൂർണ്ണമായും ഓൺലൈൻ ആകാൻ 5 മിനിറ്റ് എടുക്കും. ദയവായി 5 മിനിറ്റ് കാത്തിരിക്കുക. "
            "5 മിനിറ്റിനു ശേഷവും പ്രശ്നം നിലനിൽക്കുന്നുവെങ്കിൽ മാത്രം ഞങ്ങളെ വീണ്ടും വിളിക്കുക. "
            "ഞങ്ങൾ നേരിട്ട് ടെക്നീഷ്യനെ അയക്കുന്നതാണ്, / "
            "Red light indicates a fiber cut issue. First turn off the modem (power off and on through the plug socket switch, DO NOT press the restart button on the modem). "
            "The modem takes about 5 minutes to be fully online. Please wait for 5 minutes. "
            "ONLY call us back if the issue persists after 5 minutes. We will directly send a technician to fix the fiber cut, "
            "the technician does not need to call you first."
        )
        
        # Update call memory to indicate fiber cut detected
        if hasattr(self, 'call_memory') and self.call_memory:
            self.call_memory.issue_type = "internet_down"
            self.call_memory.sub_issues = ["fiber_cut"]
            self.call_memory.escalation_reasons.append("Red light detected - potential fiber cut")
        
        return fiber_cut_msg

    def _check_for_no_power(self, transcript: str) -> bool:
        """Check if the transcript mentions no lights/power, indicating adapter issue"""
        no_power_indicators = [
            "no light", "no power", "ലൈറ്റ് ഇല്ല", "ലൈറ്റ് വരുന്നില്ല", "പവർ ഇല്ല", 
            "ഓൺ ആകുന്നില്ല", "not turning on", "won't turn on", "dead", "adapter", "അഡാപ്റ്റർ"
        ]
        return any(indicator in transcript.lower() for indicator in no_power_indicators)

    def _handle_adapter_power_issue(self) -> str:
        """Handle adapter/power supply issue with direct instructions"""
        adapter_issue_msg = (
            "മോഡത്തിൽ ലൈറ്റ് വരുന്നില്ലെങ്കിൽ അത് പവർ അഡാപ്റ്റർ പ്രശ്നമാകാൻ സാധ്യതയുണ്ട്. "
            "ദയവായി ഇനിപ്പറയുന്ന കാര്യങ്ങൾ പരിശോധിക്കുക:\n\n"
            "1. അഡാപ്റ്റർ പ്ലഗ് ശരിയായി കണക്റ്റ് ചെയ്തിട്ടുണ്ടോ എന്ന് പരിശോധിക്കുക\n"
            "2. വേറൊരു സോക്കറ്റിൽ അഡാപ്റ്റർ പ്ലഗ് ചെയ്ത് നോക്കുക\n"
            "3. അഡാപ്റ്റർ കേബിൾ വളഞ്ഞോ കേടായോ എന്ന് പരിശോധിക്കുക\n\n"
            "ഇവ പരിശോധിച്ച ശേഷം, മോഡം പ്ലഗ് സ്വിച്ച് വഴി ഓഫ് ചെയ്ത് ഓൺ ചെയ്യുക (മോഡത്തിലെ റീസ്റ്റാർട്ട് ബട്ടൺ അമർത്തരുത്). "
            "ഇവയൊന്നും പ്രശ്നം പരിഹരിക്കുന്നില്ലെങ്കിൽ, അഡാപ്റ്റർ കേടായതാകാം. "
            "ഞങ്ങൾ നേരിട്ട് ടെക്നീഷ്യനെ അയക്കുന്നതാണ്, പുതിയ അഡാപ്റ്റർ കൊണ്ടുവരാൻ ടെക്നീഷ്യനോട് പറയുന്നതാണ്. / "
            "If there are no lights on the modem, it's likely a power adapter issue. Please check the following:\n\n"
            "1. Verify the adapter is properly plugged in\n"
            "2. Try plugging the adapter into a different socket\n"
            "3. Check if the adapter cable is bent or damaged\n\n"
            "After checking these, turn off and on the modem through the plug socket switch (DO NOT press the restart button on the modem). "
            "If none of these resolve the issue, the adapter may be faulty. "
            "We will send a technician directly with a replacement adapter."
        )
        
        # Update call memory to indicate adapter issue detected
        if hasattr(self, 'call_memory') and self.call_memory:
            self.call_memory.issue_type = "hardware_issue"
            self.call_memory.sub_issues = ["adapter_issue"]
            self.call_memory.escalation_reasons.append("No power detected - potential adapter issue")
        
        return adapter_issue_msg

    def process_user_input(self, transcript: str, confidence: float = 1.0) -> str:
        """Process user input and generate appropriate response"""
        start_time = time.time()
        
        # Log the transcript
        logger.info(f"Processing transcript: {transcript}")
        
        # Check for no power/adapter issue first
        if self._check_for_no_power(transcript):
            logger.info("No power/adapter issue detected in transcript - immediate handling")
            response = self._handle_adapter_power_issue()
            processing_time = time.time() - start_time
            logger.info(f"Total processing time: {processing_time:.3f}s")
            return response
            
        # Check for red light/fiber cut next
        if self._check_for_red_light(transcript):
            logger.info("Red light/fiber cut detected in transcript - immediate handling")
            response = self._handle_red_light_fiber_cut()
            processing_time = time.time() - start_time
            logger.info(f"Total processing time: {processing_time:.3f}s")
            return response
        
        # Continue with normal processing if not red light or power issue
        # For now, return a default response
        return "ക്ഷമിക്കണം, എനിക്ക് നിങ്ങളുടെ പ്രശ്നം മനസ്സിലായില്ല. ദയവായി വീണ്ടും വിവരിക്കാമോ?"

async def handle_client(websocket):
    """Handle a single client connection"""
    bot = ExotelBot()
    try:
        await bot.handle(websocket)
    except websockets.exceptions.ConnectionClosed:
        logger.info("WebSocket connection closed normally")
    except Exception as e:
        logger.error(f"Error handling client: {e}")
    finally:
        if bot.transcriber:
            bot.transcriber.stop()

async def main():
    """Start the voicebot server"""
    max_retries = 5
    retry_count = 0
    retry_delay = 5  # seconds
    
    while retry_count < max_retries:
        try:
            server = await websockets.serve(
                handle_client, 
                "0.0.0.0", 
                8080,
                max_size=10 * 1024 * 1024,  # 10MB max message size
                ping_interval=30,           # Send ping every 30 seconds
                ping_timeout=10,            # Wait 10 seconds for pong response
                close_timeout=10            # Wait 10 seconds for close handshake
            )
            
            logger.info("🚀 Voicebot server started on ws://0.0.0.0:8080")
            await asyncio.Future()  # run forever
            
        except OSError as e:
            retry_count += 1
            logger.error(f"Failed to start server (attempt {retry_count}/{max_retries}): {e}")
            
            if retry_count < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                # Exponential backoff for retry delay
                retry_delay = min(retry_delay * 2, 60)  # Cap at 60 seconds
            else:
                logger.critical(f"Failed to start server after {max_retries} attempts")
                raise
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            raise

if __name__ == "__main__":
    # Test the extract_technical_terms function
    bot = ExotelBot()
    bot.call_id = "test-call-id"  # Set a test call ID
    
    # Test with Malayalam technical terms
    test_query = "എന്റെ മോഡത്തിൽ റെഡ് ലൈറ്റ് കാണുന്നു"
    print(f"Query: {test_query}")
    print(f"Technical terms: {bot.extract_technical_terms(test_query)}")
    
    # Test with another query
    test_query2 = "വൈഫൈ കണക്ഷൻ വളരെ സ്ലോ ആണ്"
    print(f"Query: {test_query2}")
    print(f"Technical terms: {bot.extract_technical_terms(test_query2)}")
    