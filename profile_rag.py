import asyncio
import time
import logging
import os
import sys
from datetime import datetime

# Import the original modules
import data.knowledge_base.rag_engine
import data.knowledge_base.enhanced_rag_engine
from data.knowledge_base.rag_engine import RAGEngine
from data.knowledge_base.enhanced_rag_engine import EnhancedRAGEngine
from call_flow import query_gemini

# Import our profiling utilities
from profile_latency import async_profiler, sync_profiler, FunctionTimer, async_timer, generate_timing_report, timing_results

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set up the directories for profiling results
os.makedirs('profiling_results', exist_ok=True)
os.makedirs('profiling_results/rag', exist_ok=True)

# ==== Instrument RAG engine functions ====

# Basic RAG engine
if hasattr(data.knowledge_base.rag_engine, 'RAGEngine'):
    original_rag_query = data.knowledge_base.rag_engine.RAGEngine.query
    original_rag_load = data.knowledge_base.rag_engine.RAGEngine.load_knowledge_base
    
    data.knowledge_base.rag_engine.RAGEngine.query = sync_profiler(original_rag_query)
    data.knowledge_base.rag_engine.RAGEngine.load_knowledge_base = sync_profiler(original_rag_load)

# Enhanced RAG engine
if hasattr(data.knowledge_base.enhanced_rag_engine, 'EnhancedRAGEngine'):
    original_enhanced_query = data.knowledge_base.enhanced_rag_engine.EnhancedRAGEngine.query
    original_enhanced_load = data.knowledge_base.enhanced_rag_engine.EnhancedRAGEngine.load_knowledge_base
    
    data.knowledge_base.enhanced_rag_engine.EnhancedRAGEngine.query = sync_profiler(original_enhanced_query)
    data.knowledge_base.enhanced_rag_engine.EnhancedRAGEngine.load_knowledge_base = sync_profiler(original_enhanced_load)

# Instrument query_gemini for RAG contexts
original_query_gemini = query_gemini
query_gemini = async_profiler(original_query_gemini)

# ==== Test queries for profiling ====

# Sample queries to test RAG performance
TEST_QUERIES = [
    "My internet is not working",
    "I can't access any websites",
    "My WiFi is connected but no internet",
    "Router lights are blinking",
    "How do I reset my modem?",
    "My connection is very slow",
    "I'm experiencing packet loss",
    "How do I change my WiFi password?",
    "My bill shows incorrect charges",
    "When will service be restored in my area?",
]

async def profile_rag_engine():
    """Profile the basic RAG engine"""
    logger.info("Profiling basic RAG engine...")
    
    try:
        # Initialize RAG engine
        with FunctionTimer("RAGEngine_initialization"):
            rag_engine = RAGEngine("data/knowledge_base")
        
        # Run test queries
        for i, query in enumerate(TEST_QUERIES):
            logger.info(f"Running basic RAG query {i+1}/{len(TEST_QUERIES)}: {query}")
            
            with FunctionTimer(f"RAGEngine_query_{i+1}"):
                result = rag_engine.query(query)
            
            logger.info(f"Result length: {len(result)}")
    except Exception as e:
        logger.error(f"Error profiling basic RAG engine: {e}")

async def profile_enhanced_rag_engine():
    """Profile the enhanced RAG engine"""
    logger.info("Profiling enhanced RAG engine...")
    
    try:
        # Initialize enhanced RAG engine
        with FunctionTimer("EnhancedRAGEngine_initialization"):
            enhanced_rag_engine = EnhancedRAGEngine("data/knowledge_base")
        
        # Run test queries
        for i, query in enumerate(TEST_QUERIES):
            logger.info(f"Running enhanced RAG query {i+1}/{len(TEST_QUERIES)}: {query}")
            
            with FunctionTimer(f"EnhancedRAGEngine_query_{i+1}"):
                result = enhanced_rag_engine.query(query)
            
            logger.info(f"Result length: {len(result)}")
    except Exception as e:
        logger.error(f"Error profiling enhanced RAG engine: {e}")

async def profile_gemini_with_rag():
    """Profile the combination of RAG and Gemini"""
    logger.info("Profiling Gemini with RAG context...")
    
    try:
        # Initialize RAG engine for context
        with FunctionTimer("RAGEngine_for_Gemini"):
            rag_engine = RAGEngine("data/knowledge_base")
        
        # Create a dummy chat session and lock
        dummy_chat_session = None
        lock = asyncio.Lock()
        
        # Run test queries
        for i, query in enumerate(TEST_QUERIES):
            logger.info(f"Running Gemini+RAG query {i+1}/{len(TEST_QUERIES)}: {query}")
            
            # Get RAG context
            with FunctionTimer(f"RAG_context_for_Gemini_{i+1}"):
                rag_context = rag_engine.query(query)
            
            # Query Gemini with RAG context
            try:
                with FunctionTimer(f"Gemini_with_RAG_{i+1}"):
                    result = await query_gemini(query, dummy_chat_session, lock, rag_context)
                
                logger.info(f"Result length: {len(result) if result else 0}")
            except Exception as e:
                logger.error(f"Error querying Gemini: {e}")
    except Exception as e:
        logger.error(f"Error profiling Gemini with RAG: {e}")

async def main():
    """Run all profiling tests"""
    start_time = time.time()
    
    try:
        # Profile basic RAG engine
        await profile_rag_engine()
        
        # Profile enhanced RAG engine
        await profile_enhanced_rag_engine()
        
        # Profile Gemini with RAG context
        await profile_gemini_with_rag()
        
    finally:
        end_time = time.time()
        total_runtime = end_time - start_time
        
        logger.info(f"Total profiling runtime: {total_runtime:.2f} seconds")
        
        # Generate and save the timing report
        generate_timing_report()
        
        # Save the report to the RAG-specific directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f'profiling_results/rag/rag_profiling_{timestamp}.txt', 'w') as f:
            f.write(f"RAG Profiling Report - {datetime.now().isoformat()}\n\n")
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
        
        logger.info(f"Profiling complete. Results saved in profiling_results/rag directory.")

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