import asyncio
import time
import logging
import os
import sys
import base64
import wave
from datetime import datetime

# Import the original modules
from call_flow import synthesize_speech_streaming, RealTimeTranscriber
import call_flow

# Import our profiling utilities
from profile_latency import async_profiler, sync_profiler, FunctionTimer, async_timer, generate_timing_report, timing_results

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set up the directories for profiling results
os.makedirs('profiling_results', exist_ok=True)
os.makedirs('profiling_results/speech', exist_ok=True)

# ==== Instrument speech functions ====

# Text-to-Speech
original_synthesize_speech = call_flow.synthesize_speech_streaming
call_flow.synthesize_speech_streaming = async_profiler(original_synthesize_speech)

# Speech-to-Text (if available)
if hasattr(call_flow, 'RealTimeTranscriber'):
    # Method for adding audio
    original_add_audio = call_flow.RealTimeTranscriber.add_audio
    call_flow.RealTimeTranscriber.add_audio = sync_profiler(original_add_audio)
    
    # Method for running streaming
    original_run_streaming = call_flow.RealTimeTranscriber._run_streaming
    call_flow.RealTimeTranscriber._run_streaming = sync_profiler(original_run_streaming)
    
    # Method for post-processing transcript
    original_post_process = call_flow.RealTimeTranscriber._post_process_transcript
    call_flow.RealTimeTranscriber._post_process_transcript = sync_profiler(original_post_process)

# ==== Test data for profiling ====

# Sample text to synthesize
TEST_PHRASES = [
    "Hello, how can I help you today?",
    "I understand you're having issues with your internet connection.",
    "Have you tried restarting your router by unplugging it for about 30 seconds and then plugging it back in?",
    "Let me check if there are any reported outages in your area.",
    "I recommend resetting your network settings and reconnecting to your WiFi.",
    "ഇന്റർനെറ്റ് പ്രശ്നങ്ങൾ പരിഹരിക്കാൻ ദയവായി റൗട്ടർ റീസ്റ്റാർട്ട് ചെയ്യുക.",  # Malayalam: Please restart your router to fix internet issues
    "നിങ്ങളുടെ പരാതി രേഖപ്പെടുത്തിയിരിക്കുന്നു, ഉടൻ തന്നെ പരിഹരിക്കും.",      # Malayalam: Your complaint has been registered, it will be resolved soon
]

# Get a test audio file for STT if available
def get_test_audio_path():
    """Find a test audio file to use for STT profiling"""
    # Check test_audio directory
    if os.path.exists('test_audio'):
        audio_files = [f for f in os.listdir('test_audio') if f.endswith('.wav')]
        if audio_files:
            return os.path.join('test_audio', audio_files[0])
    
    # Check recordings directory
    recording_dirs = os.listdir('data/recordings')
    for recording_dir in recording_dirs:
        dir_path = os.path.join('data/recordings', recording_dir)
        if os.path.isdir(dir_path):
            audio_files = [f for f in os.listdir(dir_path) if f.endswith('.wav')]
            if audio_files:
                return os.path.join(dir_path, audio_files[0])
    
    return None

# ==== Profile TTS ====

async def profile_tts():
    """Profile Text-to-Speech performance"""
    logger.info("Profiling Text-to-Speech...")
    
    try:
        for i, text in enumerate(TEST_PHRASES):
            logger.info(f"Synthesizing speech {i+1}/{len(TEST_PHRASES)}: {text[:30]}...")
            
            start_time = time.time()
            audio_chunks = await call_flow.synthesize_speech_streaming(text)
            end_time = time.time()
            
            total_audio_size = sum(len(chunk) for chunk in audio_chunks)
            logger.info(f"TTS took {end_time - start_time:.4f}s, total audio size: {total_audio_size} bytes")
            
            # Add to timing results
            if f"TTS_synthesis_{i+1}" not in timing_results:
                timing_results[f"TTS_synthesis_{i+1}"] = []
            timing_results[f"TTS_synthesis_{i+1}"].append(end_time - start_time)
    
    except Exception as e:
        logger.error(f"Error profiling TTS: {e}")

# ==== Profile STT ====

async def profile_stt():
    """Profile Speech-to-Text performance"""
    logger.info("Profiling Speech-to-Text...")
    
    # Find a test audio file
    audio_path = get_test_audio_path()
    if not audio_path:
        logger.error("No test audio file found for STT profiling")
        return
    
    logger.info(f"Using test audio file: {audio_path}")
    
    try:
        # Load the audio file
        with wave.open(audio_path, 'rb') as wav_file:
            sample_rate = wav_file.getframerate()
            audio_data = wav_file.readframes(wav_file.getnframes())
        
        # Convert to base64 for processing
        base64_audio = base64.b64encode(audio_data).decode('utf-8')
        
        # Set up transcription results
        transcription_results = []
        
        # Callback function to collect transcription results
        def on_transcript(text):
            transcription_results.append(text)
            logger.info(f"Transcript received: {text}")
        
        # Initialize transcriber
        with FunctionTimer("RealTimeTranscriber_init"):
            transcriber = RealTimeTranscriber(on_transcript_callback=on_transcript)
        
        # Start transcription
        with FunctionTimer("RealTimeTranscriber_start"):
            transcriber._start_thread()
        
        # Send audio in chunks to simulate streaming
        chunk_size = len(audio_data) // 10  # Split into 10 chunks
        chunks = [audio_data[i:i+chunk_size] for i in range(0, len(audio_data), chunk_size)]
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Sending audio chunk {i+1}/{len(chunks)}")
            
            # Convert chunk to base64
            base64_chunk = base64.b64encode(chunk).decode('utf-8')
            
            # Add audio to transcriber
            with FunctionTimer(f"RealTimeTranscriber_add_audio_{i+1}"):
                transcriber.add_audio(base64_chunk)
            
            # Wait a bit between chunks to simulate real-time
            await asyncio.sleep(0.1)
        
        # Wait for transcription to complete
        logger.info("Waiting for transcription to complete...")
        await asyncio.sleep(2.0)
        
        # Stop transcriber
        with FunctionTimer("RealTimeTranscriber_stop"):
            transcriber.stop()
        
        logger.info(f"Final transcription results: {transcription_results}")
    
    except Exception as e:
        logger.error(f"Error profiling STT: {e}")

# ==== Main profiling function ====

async def main():
    """Run all profiling tests"""
    start_time = time.time()
    
    try:
        # Profile TTS
        await profile_tts()
        
        # Profile STT
        await profile_stt()
        
    finally:
        end_time = time.time()
        total_runtime = end_time - start_time
        
        logger.info(f"Total profiling runtime: {total_runtime:.2f} seconds")
        
        # Generate and save the timing report
        generate_timing_report()
        
        # Save the report to the speech-specific directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f'profiling_results/speech/speech_profiling_{timestamp}.txt', 'w') as f:
            f.write(f"Speech Processing Profiling Report - {datetime.now().isoformat()}\n\n")
            f.write(f"Total runtime: {total_runtime:.2f} seconds\n\n")
            
            for func_name, times in sorted(timing_results.items()):
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)
                total_time = sum(times)
                calls = len(times)
                
                f.write(f"{func_name}:\n")
                f.write(f"  Calls: {calls}\n")
                f.write(f"  Total Time: {total_time:.4f}s\n")
                f.write(f"  Avg Time: {avg_time:.4f}s\n")
                f.write(f"  Min Time: {min_time:.4f}s\n")
                f.write(f"  Max Time: {max_time:.4f}s\n\n")
        
        logger.info(f"Profiling complete. Results saved in profiling_results/speech directory.")

if __name__ == "__main__":
    # Set up asyncio event loop
    loop = asyncio.get_event_loop()
    
    try:
        # Run the profiling
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        # Generate report even on interrupt
        generate_timing_report()
        logger.info("Profiling interrupted. Results saved.")
    finally:
        loop.close() 