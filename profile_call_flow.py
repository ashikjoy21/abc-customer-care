import asyncio
import logging
import os
import sys
import time
from datetime import datetime

# Import the original modules that we'll be profiling
import call_flow
from call_flow import ExotelBot, handle_client, main
import data.knowledge_base.rag_engine
import data.knowledge_base.enhanced_rag_engine
from troubleshooting_engine import TroubleshootingEngine

# Import our profiling utilities
from profile_latency import async_profiler, sync_profiler, FunctionTimer, async_timer, generate_timing_report, timing_results

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set up the directories for profiling results
os.makedirs('profiling_results', exist_ok=True)

# ==== Instrument key async functions ====

# Wrap key functions from call_flow.py with the async_profiler decorator
call_flow.ExotelBot.handle = async_profiler(call_flow.ExotelBot.handle)
call_flow.ExotelBot.handle_message = async_profiler(call_flow.ExotelBot.handle_message)
call_flow.ExotelBot.on_transcription = async_profiler(call_flow.ExotelBot.on_transcription)
call_flow.ExotelBot._get_rag_context = async_profiler(call_flow.ExotelBot._get_rag_context)
call_flow.ExotelBot.play_message = async_profiler(call_flow.ExotelBot.play_message)
call_flow.query_gemini = async_profiler(call_flow.query_gemini)
call_flow.synthesize_speech_streaming = async_profiler(call_flow.synthesize_speech_streaming)
call_flow.handle_client = async_profiler(call_flow.handle_client)
call_flow.main = async_profiler(call_flow.main)

# ==== Instrument key sync functions ====

# RAG engine functions
if hasattr(data.knowledge_base.rag_engine, 'RAGEngine'):
    data.knowledge_base.rag_engine.RAGEngine.query = sync_profiler(data.knowledge_base.rag_engine.RAGEngine.query)
    data.knowledge_base.rag_engine.RAGEngine.load_knowledge_base = sync_profiler(data.knowledge_base.rag_engine.RAGEngine.load_knowledge_base)

# Enhanced RAG engine functions
if hasattr(data.knowledge_base.enhanced_rag_engine, 'EnhancedRAGEngine'):
    data.knowledge_base.enhanced_rag_engine.EnhancedRAGEngine.query = sync_profiler(data.knowledge_base.enhanced_rag_engine.EnhancedRAGEngine.query)
    data.knowledge_base.enhanced_rag_engine.EnhancedRAGEngine.load_knowledge_base = sync_profiler(data.knowledge_base.enhanced_rag_engine.EnhancedRAGEngine.load_knowledge_base)

# Troubleshooting engine functions
TroubleshootingEngine.classify_issue = sync_profiler(TroubleshootingEngine.classify_issue)
TroubleshootingEngine.start_troubleshooting = sync_profiler(TroubleshootingEngine.start_troubleshooting)
TroubleshootingEngine.process_response = sync_profiler(TroubleshootingEngine.process_response)

# Transcription functions
if hasattr(call_flow, 'Transcriber'):
    call_flow.Transcriber.process_responses = sync_profiler(call_flow.Transcriber.process_responses)
    call_flow.Transcriber._post_process_transcript = sync_profiler(call_flow.Transcriber._post_process_transcript)

if hasattr(call_flow, 'RealTimeTranscriber'):
    call_flow.RealTimeTranscriber._run_streaming = sync_profiler(call_flow.RealTimeTranscriber._run_streaming)
    call_flow.RealTimeTranscriber._post_process_transcript = sync_profiler(call_flow.RealTimeTranscriber._post_process_transcript)

# ==== Override class initialization to insert timing ====

# Save original __init__ methods
original_exotel_bot_init = call_flow.ExotelBot.__init__

# Create instrumented versions
def instrumented_exotel_bot_init(self, *args, **kwargs):
    with FunctionTimer("ExotelBot.__init__"):
        original_exotel_bot_init(self, *args, **kwargs)

# Apply instrumented versions
call_flow.ExotelBot.__init__ = instrumented_exotel_bot_init

# ==== Run the main application with profiling ====

async def run_with_profiling():
    """Run the main application with profiling and generate a report at the end."""
    try:
        logger.info("Starting application with profiling...")
        start_time = time.time()
        
        # Run the original main function
        await main()
    finally:
        end_time = time.time()
        total_runtime = end_time - start_time
        
        logger.info(f"Total application runtime: {total_runtime:.2f} seconds")
        
        # Generate and save the timing report
        generate_timing_report()
        
        logger.info(f"Profiling complete. Results saved in the profiling_results directory.")

if __name__ == "__main__":
    # Set up asyncio event loop
    loop = asyncio.get_event_loop()
    
    try:
        # Run the application with profiling
        loop.run_until_complete(run_with_profiling())
    except KeyboardInterrupt:
        # Generate report even on interrupt
        generate_timing_report()
        logger.info("Application interrupted. Profiling results saved.")
    finally:
        loop.close() 