import asyncio
import functools
import cProfile
import pstats
import io
import time
import logging
from datetime import datetime
from typing import Callable, Dict, Any, Optional, List
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global storage for timing results
timing_results = {}
current_profiler = None

def async_profiler(func):
    """Decorator to profile async functions with cProfile"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        global current_profiler
        
        # Create a profiler for this function
        pr = cProfile.Profile()
        pr.enable()
        
        # Store the current profiler
        old_profiler = current_profiler
        current_profiler = pr
        
        # Track timing
        start_time = time.time()
        
        try:
            # Run the function
            result = await func(*args, **kwargs)
            return result
        finally:
            # Stop profiling
            end_time = time.time()
            pr.disable()
            current_profiler = old_profiler
            
            # Log timing
            elapsed = end_time - start_time
            func_name = func.__qualname__
            if func_name not in timing_results:
                timing_results[func_name] = []
            timing_results[func_name].append(elapsed)
            
            # Log profiling results
            s = io.StringIO()
            ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
            ps.print_stats(20)  # Show top 20 functions
            
            # Create profiling directory if it doesn't exist
            os.makedirs('profiling_results', exist_ok=True)
            
            # Save detailed profile
            with open(f'profiling_results/{func_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.prof', 'w') as f:
                f.write(s.getvalue())
            
            logger.info(f"Function {func_name} took {elapsed:.4f} seconds")
    
    return wrapper

def sync_profiler(func):
    """Decorator to profile synchronous functions with cProfile"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Create a profiler for this function
        pr = cProfile.Profile()
        pr.enable()
        
        # Track timing
        start_time = time.time()
        
        try:
            # Run the function
            result = func(*args, **kwargs)
            return result
        finally:
            # Stop profiling
            end_time = time.time()
            pr.disable()
            
            # Log timing
            elapsed = end_time - start_time
            func_name = func.__qualname__
            if func_name not in timing_results:
                timing_results[func_name] = []
            timing_results[func_name].append(elapsed)
            
            # Log profiling results
            s = io.StringIO()
            ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
            ps.print_stats(20)  # Show top 20 functions
            
            # Create profiling directory if it doesn't exist
            os.makedirs('profiling_results', exist_ok=True)
            
            # Save detailed profile
            with open(f'profiling_results/{func_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.prof', 'w') as f:
                f.write(s.getvalue())
            
            logger.info(f"Function {func_name} took {elapsed:.4f} seconds")
    
    return wrapper

class FunctionTimer:
    """Context manager to time function execution"""
    def __init__(self, name):
        self.name = name
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        elapsed = end_time - self.start_time
        
        if self.name not in timing_results:
            timing_results[self.name] = []
        timing_results[self.name].append(elapsed)
        
        logger.info(f"{self.name} took {elapsed:.4f} seconds")

async def async_timer(name: str, coro):
    """Async context manager to time coroutine execution"""
    start_time = time.time()
    try:
        return await coro
    finally:
        end_time = time.time()
        elapsed = end_time - start_time
        
        if name not in timing_results:
            timing_results[name] = []
        timing_results[name].append(elapsed)
        
        logger.info(f"{name} took {elapsed:.4f} seconds")

def generate_timing_report():
    """Generate a report of all timing results"""
    logger.info("===== Timing Report =====")
    
    for func_name, times in sorted(timing_results.items()):
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        total_time = sum(times)
        calls = len(times)
        
        logger.info(f"{func_name}:")
        logger.info(f"  Calls: {calls}")
        logger.info(f"  Total Time: {total_time:.4f}s")
        logger.info(f"  Avg Time: {avg_time:.4f}s")
        logger.info(f"  Min Time: {min_time:.4f}s")
        logger.info(f"  Max Time: {max_time:.4f}s")
    
    # Save report to file
    os.makedirs('profiling_results', exist_ok=True)
    with open(f'profiling_results/timing_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt', 'w') as f:
        f.write("===== Timing Report =====\n\n")
        
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

# Example usage
if __name__ == "__main__":
    logger.info("Run this module to apply profiling decorators to your code.")
    logger.info("Import the decorators in your main modules to profile specific functions.") 