# Simple RAG System for Network Troubleshooting

This is a simplified implementation of a Retrieval-Augmented Generation (RAG) system for network troubleshooting that doesn't rely on external embedding libraries.

## Features

- Token-based similarity search
- In-memory document storage
- Simple caching mechanism
- Bilingual support (English and Malayalam)
- Document metadata for enhanced retrieval

## Usage

```python
from data.knowledge_base import get_simple_rag_engine

# Get the RAG engine singleton
engine = get_simple_rag_engine()

# Query for documents
results = engine.query("my modem has no power")

# Get a formatted troubleshooting response
response = engine.get_troubleshooting_response("my modem has no power")
print(response["response"])
```

## Implementation Details

The SimpleRAG implementation includes:

1. **Document Storage**: Documents are stored in memory with metadata
2. **Simple Tokenization**: Text is tokenized by splitting on whitespace and punctuation
3. **Similarity Calculation**: Uses a simple cosine similarity between token counts
4. **Keyword Matching**: Enhances retrieval by matching against document keywords
5. **Caching**: Implements a time-based cache to improve response times for repeated queries
6. **Conversation Context**: Can incorporate conversation history for better responses

## Sample Documents

The system comes pre-loaded with sample network troubleshooting scenarios in both English and Malayalam, including:

- Modem power issues
- Fiber connection problems
- Slow internet troubleshooting

## Advantages

- No external dependencies required
- Lightweight implementation
- Bilingual support
- Easy to extend with additional documents 