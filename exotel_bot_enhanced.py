import os
import re
import json
import time
import base64
import logging
import asyncio
import wave
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from call_memory_enhanced import CallMemoryEnhanced, CallStatus
from troubleshooting_engine import TroubleshootingEngine
from transcript_enhancer import TranscriptEnhancer
from utils import CustomerDatabaseManager, TelegramBotManager, RealTimeTranscriber, PhoneNumberCollector
from step_prioritizer import CustomerTechnicalProfile

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExotelBotEnhanced:
    """Enhanced ExotelBot with structured troubleshooting capabilities"""
    
    def __init__(self):
        """Initialize the enhanced bot"""
        # Initialize basic components
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
        self.telegram_bot = TelegramBotManager()
        self.conversation_history = []
        self.last_context = None
        self.waiting_for_phone = True
        self.call_memory = None
        self.silence_counter = 0
        self.max_silence_responses = 2
        self.last_message_timestamp = datetime.now()
        self.last_user_speaking_time = None
        
        # Initialize transcript enhancer
        common_phrases_path = os.path.join(os.path.dirname(__file__), "data", "common_phrases.txt")
        self.transcript_enhancer = TranscriptEnhancer(common_phrases_file=common_phrases_path)
        
        # Paths for files and directories
        self.data_dir = os.path.join(os.path.dirname(__file__), "data")
        self.temp_dir = os.path.join(self.data_dir, "temp")
        self.recordings_dir = os.path.join(self.data_dir, "recordings")
        self.tts_output_path = os.path.join(self.temp_dir, "tts_output.wav")
        self._ensure_directories_exist()
        
        # Recording related attributes
        self.recording_file = None
        self.recording_path = None
        
        # Reset state
        self._reset_state()
    
    def _reset_state(self):
        """Reset all state variables for a new call"""
        # Set call ID
        self.call_id = f"call_{int(time.time())}"
        
        # Initialize enhanced call memory with the ID
        self.call_memory = CallMemoryEnhanced(call_id=self.call_id)
        
        # Initialize troubleshooting engine
        knowledge_base_path = os.path.join(os.path.dirname(__file__), "data", "knowledge_base")
        self.call_memory.initialize_troubleshooting_engine(knowledge_base_path)
        
        # Reset other state variables
        self.call_active = True
        self.waiting_for_phone = True
        self.loop = asyncio.get_event_loop() if not self.loop else self.loop
        self.conversation_history = []
        self.last_context = None
        self.silence_counter = 0
        self.last_message_timestamp = datetime.now()
        self.last_user_speaking_time = None
        
        # Reset transcriber
        if self.transcriber:
            self.transcriber.stop()
            self.transcriber = None
            
        logger.info(f"Bot state reset for new call: {self.call_id}")
    
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
                    "issue_type": self.call_memory.current_issue_type if self.call_memory else None,
                    "sub_issues": self.call_memory.sub_issues if self.call_memory else None,
                    "escalated": self.call_memory.status == CallStatus.ESCALATED if self.call_memory else None
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
    
    def _is_silence(self, text: str) -> bool:
        """Check if transcribed text is likely from silence or background noise"""
        # If text is empty or very short, it's likely silence
        if not text or len(text.strip()) < 3:
            return True
            
        # Check for common noise patterns
        noise_patterns = [
            r'^\s*$',  # Empty or whitespace only
            r'^[.,!?]+$',  # Only punctuation
            r'^[hm]+$',  # Humming sounds
            r'^[ah]+$',  # Breathing sounds
        ]
        
        for pattern in noise_patterns:
            if re.match(pattern, text.strip(), re.IGNORECASE):
                return True
                
        # Check for inappropriate words that might be transcription errors from background noise
        inappropriate_words = ["fuck", "shit", "ass"]
        for word in inappropriate_words:
            if word in text.lower():
                logger.warning(f"Detected inappropriate word in transcript, treating as noise: {text}")
                return True
                
        return False
    
    def _get_time_of_day_greeting(self) -> str:
        """Get time-appropriate greeting in Malayalam"""
        hour = datetime.now().hour
        
        if 5 <= hour < 12:
            return "സുപ്രഭാതം"  # Good morning
        elif 12 <= hour < 17:
            return "ഉച്ചയ്ക്ക് വന്ദനം"  # Good afternoon
        else:
            return "സുഭ സന്ധ്യ"  # Good evening
    
    async def play_message(self, text: str) -> bool:
        """Play TTS message to user"""
        try:
            if not self.websocket or not self.call_active:
                logger.warning("Cannot play message: WebSocket not connected or call not active")
                return False
                
            # Update last message timestamp
            self.last_message_timestamp = datetime.now()
            self.last_message = text
            
            # Add to conversation history if call memory exists
            if self.call_memory and hasattr(self.call_memory, 'conversation_history'):
                self.call_memory.conversation_history.append({
                    "user": "",
                    "bot": text,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Add to local conversation history
            self.conversation_history.append({
                "user": "",
                "bot": text,
                "timestamp": datetime.now().isoformat()
            })
            
            # Use text-to-speech service to convert text to audio
            from utils import text_to_speech
            audio_data = await text_to_speech(text, output_path=self.tts_output_path)
            
            if not audio_data:
                logger.error("Failed to generate TTS audio")
                return False
                
            # Add bot's audio to recording
            self._add_to_recording(audio_data, is_bot_audio=True)
            
            # Convert audio data to base64
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Send audio to client
            response = {
                "event": "media",
                "media": {
                    "payload": audio_b64,
                    "encoding": "mulaw",
                    "sample_rate": 8000
                }
            }
            await self.websocket.send(json.dumps(response))
            
            logger.info(f"Sent TTS message: {text[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error playing message: {e}")
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
                self.call_memory = CallMemoryEnhanced(call_id=self.call_id)
                logger.info(f"Call started: {self.call_id}")
                
                # Start recording the call
                self._start_recording()
                
                # Initialize troubleshooting engine
                knowledge_base_path = os.path.join(os.path.dirname(__file__), "data", "knowledge_base")
                self.call_memory.initialize_troubleshooting_engine(knowledge_base_path)
                
                # Get time-appropriate greeting
                time_greeting = self._get_time_of_day_greeting()
                
                # More conversational initial greeting
                greeting = (
                    f"{time_greeting}! സാറ്റ് വിഷനിലേക്ക് വിളിച്ചതിന് നന്ദി. "
                    f"എന്റെ പേര് അഞ്ജലി, ഞാൻ എങ്ങനെ സഹായിക്കാം? "
                    f"ആദ്യം നിങ്ങളുടെ 10 അക്ക ഫോൺ നമ്പർ പറയാമോ?"
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
                    self.call_memory.status = CallStatus.DROPPED
                    await self._send_call_summary()

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            if self.call_memory:
                self.call_memory.status = CallStatus.DROPPED
                await self._send_call_summary()
    
    async def handle_dtmf(self, digit: str) -> None:
        """Handle DTMF input"""
        try:
            if not digit:
                return
                
            if self.waiting_for_phone:
                # Add digit to phone collector
                self.phone_collector.add_digit(digit)
                
                # Check if we have a complete phone number
                if self.phone_collector.is_complete():
                    phone = self.phone_collector.get_number()
                    is_valid, customer_info = await self.validate_phone_number(phone)
                    
                    if not is_valid:
                        await self.play_message("ക്ഷമിക്കണം, ആ നമ്പർ കണ്ടെത്താനായില്ല. ദയവായി നിങ്ങളുടെ 10 അക്ക ഫോൺ നമ്പർ വീണ്ടും നൽകുക.")
                        self.phone_collector.reset()
                        return
                        
                    # Update call memory with phone and customer info
                    self.call_memory.phone_number = phone
                    self.call_memory.customer_info = customer_info
                    self.call_memory.customer_name = customer_info["name"]
                    self.waiting_for_phone = False
                    
                    # Update customer technical profile
                    self.call_memory.update_customer_technical_profile()
                    
                    # Welcome message with customer name
                    welcome_msg = f"നമസ്കാരം {customer_info['name']}! എന്താണ് നിങ്ങളുടെ പ്രശ്നം? ദയവായി വിശദീകരിക്കുക."
                    await self.play_message(welcome_msg)
                    
                    # Start troubleshooting flow
                    self._start_troubleshooting_flow()
            else:
                # Handle DTMF during troubleshooting
                if digit == "0":
                    # Special case: 0 = escalate to human
                    self.call_memory.status = CallStatus.ESCALATED
                    self.call_memory.escalation_reasons.append("Customer requested escalation via DTMF")
                    await self.play_message("ഞാൻ നിങ്ങളെ ഒരു സാങ്കേതിക വിദഗ്ധനുമായി ബന്ധിപ്പിക്കാൻ പോകുന്നു. ദയവായി കാത്തിരിക്കൂ.")
                    await self._send_call_summary()
                
        except Exception as e:
            logger.error(f"Error handling DTMF: {e}")
            await self.play_message("ക്ഷമിക്കണം, എന്തോ പിശക് സംഭവിച്ചു. ദയവായി വീണ്ടും ശ്രമിക്കുക.")
    
    def _start_troubleshooting_flow(self):
        """Start the structured troubleshooting flow"""
        if not self.call_memory:
            logger.error("Cannot start troubleshooting: call memory not initialized")
            return
            
        logger.info(f"Starting structured troubleshooting flow for call {self.call_id}")
    
    async def on_transcription(self, text: str):
        """Handle transcribed speech"""
        try:
            # Skip processing if call is not active
            if not self.call_active or (self.call_memory and self.call_memory.status != CallStatus.ACTIVE):
                logger.info(f"Ignoring transcription for inactive call: {text}")
                return
                
            # Skip if waiting for phone number (phone should be entered via DTMF)
            if self.waiting_for_phone:
                logger.info(f"Waiting for phone number, ignoring transcription: {text}")
                return
                
            # Skip if silence detected
            if self._is_silence(text):
                logger.info(f"Silence detected, ignoring: '{text}'")
                return
                
            # Log the original transcript for debugging
            logger.debug(f"Original transcript: {text}")
            
            # Enhance transcript quality
            if hasattr(self, 'transcript_enhancer'):
                # Update context from conversation history
                self.transcript_enhancer.update_context(self.conversation_history)
                
                # Apply transcript enhancement
                enhanced_text = self.transcript_enhancer.enhance(text)
                
                # Log the enhanced transcript
                if enhanced_text != text:
                    logger.info(f"Enhanced transcript: '{text}' → '{enhanced_text}'")
                    text = enhanced_text
            
            # Process with troubleshooting engine if available
            if self.call_memory and hasattr(self.call_memory, 'troubleshooting_engine'):
                # First time: classify issue and start troubleshooting
                if not self.call_memory.current_issue_type:
                    issue_type = self.call_memory.classify_issue(text)
                    logger.info(f"Classified issue as: {issue_type} with confidence {self.call_memory.issue_confidence:.2f}")
                    if self.call_memory.sub_issues:
                        logger.info(f"Detected sub-issues: {self.call_memory.sub_issues}")
                    
                    # Start troubleshooting flow
                    step = self.call_memory.start_troubleshooting()
                    if step:
                        # Ask the first question in Malayalam
                        response = step.malayalam or step.english
                        await self.play_message(response)
                        
                        # Add to troubleshooting steps
                        self.call_memory.add_troubleshooting_step(
                            step=text,
                            result=response,
                            step_id=step.id,
                            success=None,  # Initial step, success not determined yet
                            priority_score=step.priority_score
                        )
                        return
                
                # Process user response and get next step
                next_step, should_escalate = self.call_memory.get_next_step(text)
                
                if should_escalate:
                    # Escalate to human
                    self.call_memory.status = CallStatus.ESCALATED
                    escalation_msg = (
                        "ക്ഷമിക്കണം, നിങ്ങളുടെ പ്രശ്നം പരിഹരിക്കാൻ എനിക്ക് കഴിയുന്നില്ല. "
                        "ഞാൻ നിങ്ങളെ ഒരു സാങ്കേതിക വിദഗ്ധനുമായി ബന്ധിപ്പിക്കാൻ പോകുന്നു. "
                        "ദയവായി കാത്തിരിക്കൂ."
                    )
                    await self.play_message(escalation_msg)
                    await self._send_call_summary()
                    return
                
                if next_step:
                    # Get response in Malayalam
                    response = next_step.malayalam or next_step.english
                    await self.play_message(response)
                    
                    # Add to troubleshooting steps
                    self.call_memory.add_troubleshooting_step(
                        step=text,
                        result=response,
                        step_id=next_step.id,
                        success=None,  # Will be determined from next user response
                        priority_score=next_step.priority_score
                    )
                    return
            
            # Fallback if troubleshooting engine not available or no next step
            # Add to conversation history
            self.conversation_history.append({
                "user": text,
                "bot": "",
                "timestamp": datetime.now().isoformat()
            })
            
            # Use generic response
            fallback_response = "ക്ഷമിക്കണം, നിങ്ങളുടെ പ്രശ്നം മനസ്സിലാക്കാൻ എനിക്ക് കഴിയുന്നില്ല. ദയവായി വീണ്ടും വിശദീകരിക്കാമോ?"
            await self.play_message(fallback_response)
            
        except Exception as e:
            logger.error(f"Error in transcription handling: {e}")
            error_response = "ക്ഷമിക്കണം, ഒരു ചെറിയ സാങ്കേതിക പ്രശ്നമുണ്ട്. ദയവായി ഒരു നിമിഷം കാത്തിരിക്കൂ, ഞാൻ വീണ്ടും ശ്രമിക്കാം."
            await self.play_message(error_response)
    
    async def validate_phone_number(self, phone_number: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validate phone number and get customer info"""
        try:
            if not phone_number or not phone_number.isdigit() or len(phone_number) != 10:
                logger.warning(f"Invalid phone number format: {phone_number}")
                return False, None
                
            # Check if customer exists in database
            customer_info = await self.db.get_customer_by_phone(phone_number)
            if not customer_info:
                logger.warning(f"Customer not found for phone: {phone_number}")
                return False, None
                
            # Get additional customer information
            customer_info = await self.db.get_customer_details(customer_info["customer_id"])
            
            # Check for area-wide issues
            if customer_info.get("area_id"):
                area_issue = await self.db.check_area_issue(customer_info["area_id"])
                if area_issue:
                    customer_info["has_area_issue"] = True
                    customer_info["area_issue_details"] = area_issue
                    
                    # Update call memory with area issue status
                    if self.call_memory:
                        self.call_memory.area_issue_status = area_issue.get("status")
            
            # Update call memory with customer info
            if self.call_memory:
                self.call_memory.customer_info = customer_info
                self.call_memory.phone_number = phone_number
                self.call_memory.customer_name = customer_info["name"]
                
                # Set default technical level if not present
                if "technical_level" not in customer_info:
                    # Determine technical level based on previous calls or default to 2
                    previous_calls = customer_info.get("previous_calls", 0)
                    if previous_calls > 5:
                        customer_info["technical_level"] = 3  # Experienced customer
                    else:
                        customer_info["technical_level"] = 2  # Average technical level
                
                # Update customer technical profile
                self.call_memory.update_customer_technical_profile()
                
                logger.info(f"Updated call memory with customer info for {phone_number}")
            
            return True, customer_info
        except Exception as e:
            logger.error(f"Error validating phone: {e}")
            return False, None
    
    async def _send_call_summary(self):
        """Send call summary to Telegram"""
        try:
            if not self.call_memory:
                logger.warning("Cannot send call summary: call memory not initialized")
                return
                
            # Generate summary
            summary = self.call_memory.generate_summary()
            
            # Add troubleshooting summary if available
            troubleshooting_summary = self.call_memory.get_troubleshooting_summary()
            if troubleshooting_summary:
                summary["troubleshooting_details"] = troubleshooting_summary
            
            # Format message
            message = f"📞 Call Summary: {self.call_id}\n"
            message += f"📱 Phone: {summary.get('phone_number', 'Unknown')}\n"
            message += f"👤 Customer: {summary.get('customer_name', 'Unknown')}\n"
            message += f"⏱️ Duration: {summary.get('duration_seconds', 0)} seconds\n"
            message += f"📊 Status: {summary.get('status', 'Unknown')}\n"
            
            if summary.get("issue_type"):
                message += f"🔍 Issue Type: {summary.get('issue_type')}\n"
                
                # Add sub-issues if available
                if summary.get("sub_issues"):
                    message += f"🔎 Sub-issues: {', '.join(summary.get('sub_issues'))}\n"
                
            if summary.get("troubleshooting_details"):
                ts_details = summary["troubleshooting_details"]
                message += f"🛠️ Steps Attempted: {ts_details.get('steps_attempted', 0)}\n"
                message += f"✅ Steps Succeeded: {ts_details.get('steps_succeeded', 0)}\n"
                message += f"❌ Steps Failed: {ts_details.get('steps_failed', 0)}\n"
            
            if summary.get("escalation_reasons"):
                message += f"⚠️ Escalation Reasons: {', '.join(summary.get('escalation_reasons', []))}\n"
                
            # Add customer technical level
            message += f"👨‍💻 Customer Technical Level: {summary.get('customer_technical_level', 2)}/5\n"
            
            # Send to Telegram
            await self.telegram_bot.send_message(message)
            logger.info(f"Sent call summary for {self.call_id} to Telegram")
            
        except Exception as e:
            logger.error(f"Error sending call summary: {e}")
    
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