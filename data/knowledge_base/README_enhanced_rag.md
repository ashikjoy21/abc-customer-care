# Enhanced RAG System for abc-angamaly

This directory contains the enhanced Retrieval-Augmented Generation (RAG) system for Malayalam network troubleshooting support.

## Overview

The enhanced RAG system improves upon the original implementation with:

1. **Semantic search** using multilingual embeddings
2. **Hybrid retrieval** combining vector search with keyword matching
3. **Context-aware responses** that consider conversation history
4. **Personalized troubleshooting** based on customer information
5. **Performance optimization** with caching and efficient indexing

## Components

### 1. Core Files

- `enhanced_rag_engine.py` - Main RAG implementation with semantic search
- `rag_architecture.md` - Detailed architecture documentation
- `rag_implementation_plan.md` - Implementation roadmap
- `requirements_enhanced_rag.txt` - Dependencies for the enhanced system

### 2. Directory Structure

```
knowledge_base/
├── __init__.py                # Exports public API
├── enhanced_rag_engine.py     # Enhanced RAG implementation
├── rag_engine.py              # Original RAG implementation
├── internet_down.md           # Knowledge base content
├── rag_architecture.md        # Architecture documentation
├── rag_implementation_plan.md # Implementation plan
├── README_enhanced_rag.md     # This file
└── storage/                   # Persisted vector indexes
    ├── enhanced_index.faiss   # FAISS vector index
    └── enhanced_index.json    # Document metadata
```

## Usage

### Basic Usage

```python
from data.knowledge_base.enhanced_rag_engine import get_enhanced_rag_engine

# Get RAG engine singleton
rag = get_enhanced_rag_engine()

# Query the knowledge base
response = rag.get_troubleshooting_response(
    query="നെറ്റ് കിട്ടുന്നില്ല",  # "No internet" in Malayalam
    customer_info=customer_info,
    conversation_history=conversation_history
)

# Access the response
print(response["response"])
```

### Adding Knowledge Sources

```python
rag = get_enhanced_rag_engine()

# Add a new knowledge source
rag.add_knowledge_source("path/to/new_knowledge.md")

# Save the updated index
rag.save()
```

## Implementation Details

### Embedding Model

The system uses the `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` model for generating embeddings, which supports Malayalam and English text.

### Vector Store

Document embeddings are stored in a FAISS index for efficient similarity search. The index is persisted to disk for reuse.

### Document Processing

Documents are processed from structured JSON/Markdown files and converted to a format suitable for retrieval, with:
- Content extraction in multiple languages
- Metadata enrichment
- Embedding generation

### Query Processing

Queries are processed with:
1. Conversation history integration
2. Embedding generation
3. Vector similarity search
4. Metadata filtering
5. Response formatting

## Performance Considerations

- In-memory caching for embeddings
- Optional Redis caching for query results
- Efficient FAISS indexing for fast similarity search

## Monitoring and Maintenance

- Log files track system performance and errors
- Index can be rebuilt as knowledge base expands
- Cached results expire after one hour to ensure freshness

## Future Enhancements

See `rag_implementation_plan.md` for the full roadmap of planned enhancements, including:
- Personalization improvements
- Feedback loop integration
- Automated knowledge base updates 