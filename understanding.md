# ABC Customer Care System - Technical Understanding

## System Architecture Overview

The ABC Customer Care system is a comprehensive voice-based customer support solution designed for ISP companies in Kerala. It provides automated troubleshooting, incident management, and escalation handling through natural language processing and AI-powered conversation management.

## Core Components

1. **Main Application (`main.py`)** - Entry point that initializes database and core services
2. **Call Flow Management (`call_flow.py`)** - Handles real-time voice conversations and call routing
3. **Enhanced Call Flow (`exotel_bot_enhanced.py`)** - Advanced call handling with troubleshooting engine
4. **Database Management (`db.py`)** - Customer data and call history management
5. **Supabase Integration (`supabase_client.py`)** - Database operations and incident management
6. **Escalation Management (`escalation_manager.py`)** - Handles incident escalation and operator notifications
7. **Real-time Monitoring**: Database notifications for operators
8. **Knowledge Base (`data/knowledge_base/`)** - RAG-powered troubleshooting guides
9. **Call Summary**: Database logging with call details

## Key Features

### Voice Processing
- **Real-time Transcription**: Google Cloud Speech-to-Text for Malayalam and English
- **Text-to-Speech**: Natural Malayalam voice responses
- **Audio Streaming**: WebSocket-based real-time audio communication

### AI-Powered Support
- **Conversation Management**: Gemini AI for natural language understanding
- **Issue Classification**: Automatic problem identification and categorization
- **Troubleshooting Engine**: Step-by-step guided problem resolution
- **Context Awareness**: Maintains conversation context throughout the call

### Customer Management
- **Phone Validation**: Automatic customer identification via phone number
- **Profile Management**: Customer history and technical level tracking
- **Area Issue Detection**: Automatic identification of widespread problems

### Incident Management
- **Automatic Escalation**: Routes complex issues to human operators
- **Database Logging**: Comprehensive call and incident tracking
- **Real-time Monitoring**: Live incident status updates

## Technical Stack

### Backend
- **Python 3.9+**: Core application logic
- **FastAPI**: Web framework for API endpoints
- **WebSockets**: Real-time communication
- **Supabase**: PostgreSQL database with real-time features

### AI & ML
- **Google Cloud Speech**: Voice transcription and synthesis
- **Google Gemini**: Natural language processing
- **RAG (Retrieval-Augmented Generation)**: Knowledge base queries
- **Sentence Transformers**: Text similarity and search

### Infrastructure
- **Docker**: Containerization
- **Supervisor**: Process management
- **Gunicorn**: WSGI server
- **Nginx**: Reverse proxy (optional)

## Data Flow

1. **Call Initiation**: Customer calls the support number
2. **Phone Validation**: System validates customer phone number
3. **Issue Identification**: AI analyzes customer's problem description
4. **Troubleshooting**: Guided step-by-step problem resolution
5. **Resolution/Escalation**: Either resolves issue or escalates to human
6. **Call Summary**: Logs complete call details to database

## Configuration

The system uses environment variables for configuration:
- Database credentials (Supabase)
- Google Cloud credentials
- API keys and endpoints
- Logging and monitoring settings

## Deployment

The system is designed for production deployment with:
- Process supervision
- Health monitoring
- Logging and metrics
- Scalable architecture
- Error handling and recovery