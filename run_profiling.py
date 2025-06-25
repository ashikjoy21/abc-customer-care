import os
import sys
import subprocess
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set up the directories for profiling results
os.makedirs('profiling_results', exist_ok=True)

def run_script(script_name, description):
    """Run a profiling script and log results"""
    logger.info(f"Running {description}...")
    start_time = time.time()
    
    # Run the script as a subprocess
    try:
        process = subprocess.Popen([sys.executable, script_name], 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE,
                                  text=True)
        
        # Stream output in real-time
        for line in iter(process.stdout.readline, ''):
            if line.strip():
                logger.info(f"{script_name}: {line.strip()}")
        
        # Get return code
        process.wait()
        
        if process.returncode != 0:
            # Print error output if there was an error
            for line in iter(process.stderr.readline, ''):
                if line.strip():
                    logger.error(f"{script_name} error: {line.strip()}")
            logger.error(f"{description} failed with return code {process.returncode}")
        else:
            end_time = time.time()
            logger.info(f"{description} completed in {end_time - start_time:.2f} seconds")
            
    except Exception as e:
        logger.error(f"Error running {script_name}: {e}")
        return False
    
    return process.returncode == 0

def main():
    """Run all profiling scripts in sequence"""
    start_time = time.time()
    logger.info("Starting comprehensive latency profiling...")
    
    # Timestamp for this profiling run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create a summary file
    summary_path = f'profiling_results/summary_{timestamp}.txt'
    with open(summary_path, 'w') as f:
        f.write(f"Latency Profiling Summary - {datetime.now().isoformat()}\n\n")
    
    # List of scripts to run
    profiling_scripts = [
        ('profile_rag.py', 'RAG Engine Profiling'),
        ('profile_speech.py', 'Speech Processing Profiling'),
        ('profile_call_flow.py', 'Call Flow Profiling'),
    ]
    
    results = []
    
    # Run each script
    for script, description in profiling_scripts:
        script_start = time.time()
        success = run_script(script, description)
        script_end = time.time()
        
        results.append({
            'script': script,
            'description': description,
            'success': success,
            'runtime': script_end - script_start
        })
        
        # Add to summary
        with open(summary_path, 'a') as f:
            f.write(f"{description}:\n")
            f.write(f"  Script: {script}\n")
            f.write(f"  Success: {success}\n")
            f.write(f"  Runtime: {script_end - script_start:.2f} seconds\n\n")
    
    # Calculate total runtime
    end_time = time.time()
    total_runtime = end_time - start_time
    
    # Add final summary
    with open(summary_path, 'a') as f:
        f.write(f"Total Profiling Runtime: {total_runtime:.2f} seconds\n\n")
        f.write("Summary of Results:\n")
        
        for result in results:
            status = "✓" if result['success'] else "✗"
            f.write(f"  {status} {result['description']}: {result['runtime']:.2f}s\n")
    
    logger.info(f"All profiling complete! Total runtime: {total_runtime:.2f} seconds")
    logger.info(f"Summary saved to {summary_path}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Profiling interrupted by user.")
    except Exception as e:
        logger.error(f"Unexpected error in profiling: {e}") 