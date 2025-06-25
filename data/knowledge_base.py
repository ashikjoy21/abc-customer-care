def get_troubleshooting_response(query: str, customer_info=None) -> dict:
    """Get troubleshooting response from knowledge base"""
    try:
        # Load knowledge base files
        kb_files = _get_knowledge_base_files()
        
        # Load documents from knowledge base files
        documents = []
        for file_path in kb_files:
            docs = _load_documents_from_file(file_path)
            if docs:
                documents.extend(docs)
                
        logger.info(f"Loaded {len(documents)} documents from knowledge base files")
        
        # Add technical terms to enhance search
        enhanced_terms = _extract_technical_terms(query)
        enhanced_query = query
        if enhanced_terms:
            enhanced_query = f"{query} {' '.join(enhanced_terms)}"
            logger.info(f"Enhanced query with technical terms: {enhanced_terms}")
        
        # Get relevant documents using semantic search
        relevant_docs = _get_relevant_documents(enhanced_query, documents)
        
        if not relevant_docs:
            return {"response": "No relevant information found."}
            
        # Format the response as reference information, not as a script
        response_parts = []
        
        # Add greeting with customer name if available
        if customer_info and customer_info.get("name"):
            response_parts.append(f"നമസ്കാരം {customer_info.get('name')},")
        
        # Add relevant information from knowledge base as reference
        for doc in relevant_docs[:2]:  # Limit to top 2 most relevant documents
            # Extract title and content
            title = doc.get("title", {}).get("malayalam", "")
            if title:
                response_parts.append(f"**{title}**\n")
                
            # Add symptoms as reference information
            symptoms = doc.get("symptoms", {}).get("malayalam", [])
            if symptoms:
                response_parts.append("ലക്ഷണങ്ങൾ:")
                for symptom in symptoms:
                    response_parts.append(f"- {symptom}")
                response_parts.append("")
                
            # Add diagnosis questions as reference information
            questions = doc.get("diagnosis", {}).get("questions", [])
            if questions:
                response_parts.append("സഹായകരമായ ചോദ്യങ്ങൾ:")
                for q in questions:
                    response_parts.append(f"- {q.get('malayalam', '')}")
                response_parts.append("")
                
            # Add solution steps as reference information
            steps = doc.get("solution", {}).get("steps", [])
            if steps:
                response_parts.append("പരിഹാര നിർദ്ദേശങ്ങൾ:")
                for step in steps:
                    response_parts.append(f"- {step.get('malayalam', '')}")
                    
        # Join all parts with newlines
        response_text = "\n".join(response_parts)
        
        return {"response": response_text, "relevant_docs": relevant_docs}
        
    except Exception as e:
        logger.error(f"Error getting troubleshooting response: {e}")
        return {"response": "Error retrieving information from knowledge base."} 