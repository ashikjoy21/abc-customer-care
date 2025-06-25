#!/usr/bin/env python3
"""Test script for enhanced RAG system functionality"""

import os
import sys
import asyncio
import logging
from typing import Dict, Any, Optional, List
import json
import time

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.knowledge_base.enhanced_rag_engine import get_enhanced_rag_engine, EnhancedRAG, Document, DocumentType
from db import CustomerDatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Sample customer info for testing
SAMPLE_CUSTOMER = {
    "Customer Name": "Benny Sebastian",
    "User Name": "benny77181",
    "Current Plan": "FUP60M4000GPM200D",
    "Address": "Kolattukudy, Manjapra, Aluva, Manjapra, 683581.",
    "NickName": "kvsatbenny77181",
    "Provider": "KeralaVision",
    "Subscriber Code": null,
    "Region": "Kokkunnu",
    "Operator": "Joy Skyvision",
    
    # Enhanced fields for the new RAG system
    "name": "Benny Sebastian",
    "device_type": "fiber_modem",
    "technical_level": "medium",
    "language_preference": "malayalam"
}

# Sample queries in Malayalam
SAMPLE_QUERIES = [
    "നെറ്റ് കിട്ടുന്നില്ല",  # No internet
    "മോഡത്തിൽ ചുവന്ന ലൈറ്റ് കാണുന്നു",  # Red light on modem
    "നെറ്റ് സ്ലോ ആണ്",  # Slow internet
    "WiFi പേര് മാറി",  # WiFi name changed
    "മോഡത്തിൽ ലൈറ്റ് വരുന്നില്ല"  # No lights on modem
]

# Sample conversation history
SAMPLE_CONVERSATION = [
    {"user": "നെറ്റ് കിട്ടുന്നില്ല", "bot": "മോഡത്തിൽ ലൈറ്റ് വരുന്നുണ്ടോ?"},
    {"user": "ചുവന്ന ലൈറ്റ് കാണുന്നു", "bot": "ഫൈബർ കണക്ഷൻ പരിശോധിക്കാം"}
]

def test_embedding_model():
    """Test embedding model functionality"""
    try:
        # Get RAG engine
        rag_engine = get_enhanced_rag_engine()
        
        # Test embedding generation
        text = "നെറ്റ് കിട്ടുന്നില്ല"  # "No internet" in Malayalam
        embedding = rag_engine.embedding_model.get_embedding(text)
        
        # Check embedding shape
        dimension = rag_engine.embedding_model.dimension
        assert embedding.shape == (dimension,), f"Expected embedding dimension {dimension}, got {embedding.shape}"
        
        # Test embedding caching
        start_time = time.time()
        embedding1 = rag_engine.embedding_model.get_embedding(text)
        first_time = time.time() - start_time
        
        start_time = time.time()
        embedding2 = rag_engine.embedding_model.get_embedding(text)
        second_time = time.time() - start_time
        
        # Second call should be faster due to caching
        assert second_time < first_time, "Caching not working as expected"
        
        print(f"Embedding model test passed. Dimension: {dimension}")
        print(f"First call: {first_time:.4f}s, Second call: {second_time:.4f}s")
        
        return True
    except Exception as e:
        logger.error(f"Error testing embedding model: {e}")
        return False

def test_document_processing():
    """Test document processing functionality"""
    try:
        # Get RAG engine
        rag_engine = get_enhanced_rag_engine()
        
        # Get path to test knowledge base
        kb_path = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_base", "internet_down.md")
        
        # Process knowledge base
        documents = rag_engine.document_processor.process_json(kb_path)
        
        # Check documents
        assert len(documents) > 0, "No documents processed"
        
        # Check document structure
        doc = documents[0]
        assert isinstance(doc, Document), "Document not of correct type"
        assert doc.id is not None, "Document has no ID"
        assert doc.content is not None, "Document has no content"
        assert doc.metadata is not None, "Document has no metadata"
        assert doc.embedding is not None, "Document has no embedding"
        
        print(f"Document processing test passed. Processed {len(documents)} documents.")
        print(f"Sample document ID: {doc.id}")
        print(f"Sample document type: {doc.doc_type}")
        
        return True
    except Exception as e:
        logger.error(f"Error testing document processing: {e}")
        return False

def test_vector_search(query: str = "നെറ്റ് കിട്ടുന്നില്ല", top_k: int = 3):
    """Test vector search functionality"""
    try:
        # Get RAG engine
        rag_engine = get_enhanced_rag_engine()
        
        # Get query embedding
        query_embedding = rag_engine.embedding_model.get_embedding(query)
        
        # Search vector store
        start_time = time.time()
        results = rag_engine.vector_store.search(query_embedding, top_k=top_k)
        search_time = time.time() - start_time
        
        # Check results
        assert len(results) > 0, "No search results"
        
        print(f"Vector search test passed. Found {len(results)} results in {search_time:.4f}s.")
        print(f"Top result score: {results[0][1]:.4f}")
        
        return True
    except Exception as e:
        logger.error(f"Error testing vector search: {e}")
        return False

async def test_rag_query(query: str, customer_info: Optional[Dict[str, Any]] = None,
                        conversation_history: Optional[List[Dict[str, str]]] = None) -> None:
    """Test RAG system with a query"""
    try:
        # Get RAG engine
        rag_engine = get_enhanced_rag_engine()
        
        # Log the query
        logger.info(f"Query: {query}")
        
        # Get response
        start_time = time.time()
        response = rag_engine.get_troubleshooting_response(
            query=query,
            customer_info=customer_info,
            conversation_history=conversation_history
        )
        query_time = time.time() - start_time
        
        # Print response
        print("\nResponse:")
        print(response["response"])
        
        # Print sources
        print("\nSources:")
        for i, source in enumerate(response["source_nodes"][:3], 1):
            source_id = source.get("id", "unknown")
            print(f"{i}. {source_id} (Score: {response['scores'][i-1]:.4f})")
            
        print(f"\nQuery time: {query_time:.4f}s")
        print("\n" + "-"*50)
        
    except Exception as e:
        logger.error(f"Error testing RAG query: {e}")

async def test_with_real_customer(phone_number: str, query: str) -> None:
    """Test RAG with a real customer from the database"""
    try:
        # Get customer from database
        db = CustomerDatabaseManager()
        customer = db.get_customer_by_phone(phone_number)
        
        if not customer:
            logger.error(f"No customer found with phone number: {phone_number}")
            return
            
        logger.info(f"Found customer: {customer.get('Customer Name')}")
        
        # Test RAG query with customer info
        await test_rag_query(query, customer)
        
    except Exception as e:
        logger.error(f"Error testing with real customer: {e}")

async def test_context_aware_retrieval():
    """Test context-aware retrieval with conversation history"""
    try:
        # Get RAG engine
        rag_engine = get_enhanced_rag_engine()
        
        # Query without context
        print("\nTesting query WITHOUT conversation context:")
        response1 = rag_engine.get_troubleshooting_response(
            query="ചുവന്ന ലൈറ്റ് കാണുന്നു",  # "Red light showing"
            customer_info=SAMPLE_CUSTOMER
        )
        
        # Query with context
        print("\nTesting same query WITH conversation context:")
        response2 = rag_engine.get_troubleshooting_response(
            query="ചുവന്ന ലൈറ്റ് കാണുന്നു",  # "Red light showing"
            customer_info=SAMPLE_CUSTOMER,
            conversation_history=SAMPLE_CONVERSATION
        )
        
        # Print responses
        print("\nResponse WITHOUT context:")
        print(response1["response"][:200] + "..." if len(response1["response"]) > 200 else response1["response"])
        
        print("\nResponse WITH context:")
        print(response2["response"][:200] + "..." if len(response2["response"]) > 200 else response2["response"])
        
        print("\nContext-aware retrieval test completed.")
        
    except Exception as e:
        logger.error(f"Error testing context-aware retrieval: {e}")

async def main():
    """Main test function"""
    print("Testing Enhanced RAG system...\n")
    
    # Test embedding model
    print("\n1. Testing embedding model...")
    test_embedding_model()
    
    # Test document processing
    print("\n2. Testing document processing...")
    test_document_processing()
    
    # Test vector search
    print("\n3. Testing vector search...")
    test_vector_search()
    
    # Test with sample queries
    print("\n4. Testing with sample queries...")
    for query in SAMPLE_QUERIES:
        await test_rag_query(query, SAMPLE_CUSTOMER)
    
    # Test context-aware retrieval
    print("\n5. Testing context-aware retrieval...")
    await test_context_aware_retrieval()
    
    # Test with a real customer if phone number is provided
    print("\n6. Testing with real customer data...")
    phone = input("\nEnter a customer phone number to test (or press Enter to skip): ")
    if phone:
        query = input("Enter a query in Malayalam: ")
        await test_with_real_customer(phone, query)
    
    print("\nEnhanced RAG testing complete!")

if __name__ == "__main__":
    asyncio.run(main()) 