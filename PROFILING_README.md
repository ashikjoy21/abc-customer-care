# Latency Profiling Tools

This directory contains tools to profile and analyze latency in the call flow system. These tools use Python's `cProfile` and custom timing utilities to measure performance across different components.

## Available Profiling Scripts

- **profile_latency.py**: Core profiling utilities with decorators and timing tools
- **profile_call_flow.py**: Profiles the main call flow processes and websocket handling
- **profile_rag.py**: Profiles the RAG (Retrieval-Augmented Generation) engines
- **profile_speech.py**: Profiles STT (Speech-to-Text) and TTS (Text-to-Speech) components
- **run_profiling.py**: Main script that runs all profiling tools in sequence

## How to Run

### Option 1: Run All Profiling Scripts

To run all profiling scripts in sequence and generate a comprehensive report:

```
python run_profiling.py
```

This will execute each profiling script and collect results into a summary file.

### Option 2: Run Individual Profiling Scripts

You can run specific profiling scripts to focus on particular components:

```
# Profile RAG engine
python profile_rag.py

# Profile speech components
python profile_speech.py

# Profile call flow
python profile_call_flow.py
```

### Option 3: Custom Profiling in Your Code

You can instrument your own code by importing and using the decorators from `profile_latency.py`:

```python
from profile_latency import async_profiler, sync_profiler, FunctionTimer

# For synchronous functions
@sync_profiler
def my_function():
    # Your code here
    pass

# For asynchronous functions
@async_profiler
async def my_async_function():
    # Your async code here
    pass

# For code blocks using context manager
with FunctionTimer("my_operation"):
    # Code to time
    pass
```

## Profiling Results

All profiling results are saved in the `profiling_results` directory:

- General timing reports: `profiling_results/timing_report_*.txt`
- cProfile detailed results: `profiling_results/[function_name]_*.prof`
- Component-specific results:
  - RAG: `profiling_results/rag/*`
  - Speech: `profiling_results/speech/*`
- Summary reports: `profiling_results/summary_*.txt`

## Analyzing cProfile Results

To analyze the detailed cProfile results, you can use tools like `snakeviz`:

1. Install snakeviz: `pip install snakeviz`
2. View a profile: `snakeviz profiling_results/[function_name].prof`

This will open an interactive visualization of the profiling data in your browser.

## Interpreting Results

When analyzing the profiling results, look for:

1. **Hot spots**: Functions that take the most total time
2. **Frequency**: Functions called most often
3. **Bottlenecks**: Functions with high average execution time
4. **Variance**: Functions with high variance in execution time

Common latency issues in this codebase may include:

- **RAG Operations**: Knowledge base loading, embedding computation, and vector searches
- **Speech Processing**: STT and TTS API calls, audio processing
- **Network I/O**: API calls to external services (Gemini, Google Speech)
- **Initialization**: Heavy loading during startup
- **Caching**: Cache misses leading to repeated expensive operations

## Adding New Profiling

To profile additional components:

1. Create a new profiling script based on the existing examples
2. Import the necessary functions from `profile_latency.py`
3. Instrument the relevant functions with the decorators
4. Add any specialized profiling logic for your component
5. Update `run_profiling.py` to include your new script 