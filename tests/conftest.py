import pytest
from unittest.mock import Mock, patch, MagicMock

@pytest.fixture(scope="session")
def mock_supabase():
    """Mock Supabase client"""
    with patch('supabase_client.supabase_manager') as mock:
        client = Mock()
        client.check_connection.return_value = True
        client.get_active_incidents.return_value = []
        client.resolve_incident.return_value = True
        client.create_incident.return_value = "test-incident-id"
        mock.return_value = client
        yield client

@pytest.fixture(scope="session")
def mock_speech_client():
    """Mock Google Cloud Speech client"""
    with patch('google.cloud.speech.SpeechClient') as mock:
        client = Mock()
        mock.return_value = client
        yield client

@pytest.fixture(scope="session")
def mock_tts_client():
    """Mock Google Cloud Text-to-Speech client"""
    with patch('google.cloud.texttospeech.TextToSpeechClient') as mock:
        client = Mock()
        mock.return_value = client
        yield client

@pytest.fixture(scope="session")
def mock_gemini():
    """Mock Gemini chat session"""
    with patch('google.generativeai.GenerativeModel') as mock:
        model = Mock()
        chat = Mock()
        model.start_chat.return_value = chat
        mock.return_value = model
        yield chat

@pytest.fixture
def mock_db():
    """Mock database"""
    with patch('db.CustomerDatabaseManager') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture(scope="session")
def mock_query_engine():
    """Mock RAG query engine"""
    with patch('llama_index.core.VectorStoreIndex.as_query_engine') as mock:
        engine = Mock()
        mock.return_value = engine
        yield engine 