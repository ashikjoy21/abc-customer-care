Based on my analysis of the entire workspace, I can now provide you with a comprehensive explanation of the logic and identify unused files.

## **System Architecture Overview**

This is a **Malayalam Customer Care Voicebot System** for an ISP (Internet Service Provider) in Kerala, India. The system provides automated customer support for internet-related issues through voice calls.

### **Core Components:**

1. **Main Application (`main.py`)** - Entry point that initializes Redis, database, and Telegram bot
2. **Call Flow (`call_flow.py`)** - Core voicebot logic handling WebSocket connections, speech processing, and conversation flow
3. **Enhanced Version (`main_enhanced.py` + `exotel_bot_enhanced.py`)** - Improved version with better error handling and structured troubleshooting
4. **Transcript Enhancement (`utils.py`)** - Malayalam text processing, code-switching detection, and technical term normalization
5. **Troubleshooting Engine (`troubleshooting_engine.py`)** - Structured problem-solving with decision trees
6. **Database Management (`db.py`)** - Customer data management
7. **Telegram Integration (`telegram_notifier.py`)** - Operator notifications and incident management
8. **RAG System (`data/knowledge_base/`)** - Knowledge retrieval for technical support

### **Key Features:**

- **Bilingual Support**: Malayalam + English code-switching
- **Speech Processing**: STT (Speech-to-Text) and TTS (Text-to-Speech) using Google Cloud
- **AI Integration**: Gemini AI for natural language understanding
- **Structured Troubleshooting**: Decision-tree based problem resolution
- **Real-time Monitoring**: Telegram notifications for operators
- **Call Recording**: Complete conversation logging
- **Performance Profiling**: Built-in latency monitoring tools

## **Current Active Architecture:**

The system currently runs on:
- **Entry Point**: `main_enhanced.py` (started via supervisor)
- **Core Bot**: `exotel_bot_enhanced.py`
- **Call Memory**: `call_memory_enhanced.py`
- **Troubleshooting**: `troubleshooting_engine.py`
- **Knowledge Base**: `data/knowledge_base/enhanced_rag_engine.py`
- **Utilities**: `utils.py` (contains TranscriptEnhancer)
- **Database**: `db.py`
- **Notifications**: `telegram_notifier.py`

## **System Flow:**

1. **Call Initiation**: WebSocket connection from Exotel
2. **Phone Collection**: DTMF-based phone number collection
3. **Customer Lookup**: Database query for customer information
4. **Issue Classification**: AI-powered issue identification
5. **Structured Troubleshooting**: Decision-tree based problem resolution
6. **RAG Context**: Knowledge base retrieval for technical guidance
7. **Conversation Management**: Natural language processing with Gemini AI
8. **Escalation**: Automatic escalation to human operators when needed
9. **Call Summary**: Telegram notification with call details
10. **Recording**: Complete conversation logging

The system is designed for **production use** in a Kerala-based ISP, handling Malayalam-English bilingual customer support calls with sophisticated AI-powered troubleshooting capabilities.