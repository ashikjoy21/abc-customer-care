import pytest
import redis
from unittest.mock import Mock, patch

@pytest.fixture(scope="session")
def mock_redis():
    """Mock Redis client"""
    with patch('redis.Redis') as mock:
        client = Mock(spec=redis.Redis)
        client.ping.return_value = True
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

@pytest.fixture(scope="session")
def mock_telegram_bot():
    """Mock Telegram bot"""
    with patch('telegram_notifier.TelegramBotManager') as mock:
        bot = Mock()
        mock.return_value = bot
        yield bot

@pytest.fixture(scope="session")
def mock_db():
    """Mock customer database"""
    with patch('db.CustomerDatabaseManager') as mock:
        db = Mock()
        mock.return_value = db
        yield db

@pytest.fixture(scope="session")
def mock_query_engine():
    """Mock RAG query engine"""
    with patch('llama_index.core.VectorStoreIndex.as_query_engine') as mock:
        engine = Mock()
        mock.return_value = engine
        yield engine 