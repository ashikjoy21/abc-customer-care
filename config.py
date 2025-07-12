import os
from dotenv import load_dotenv
from pathlib import Path

# Get project root directory
PROJECT_ROOT = Path(__file__).parent

# Load environment variables
load_dotenv()

# Redis Configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_OPERATOR_CHAT_ID = os.getenv("TELEGRAM_OPERATOR_CHAT_ID", "-1001234567890")

# GCP Configuration
GCP_CREDENTIALS_PATH = str(PROJECT_ROOT / "gcp_key.json")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# File Paths
DATA_DIR = PROJECT_ROOT / "data"
CUSTOMERS_JSON_PATH = str(DATA_DIR / "customers" / "customers.json")
KNOWLEDGE_BASE_PATH = str(DATA_DIR / "knowledge_base")
CALL_SESSIONS_PATH = str(DATA_DIR / "call_sessions")

# Ensure required directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
(DATA_DIR / "customers").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "knowledge_base").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "call_sessions").mkdir(parents=True, exist_ok=True)

# API Server Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("PORT", 8080))
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL", f"ws://{API_HOST}:{API_PORT}/ws")

# Speech Configuration
SPEECH_LANGUAGE_CODE = "ml-IN"
SPEECH_VOICE_NAME = "ml-IN-Standard-A"
SPEECH_SAMPLE_RATE = 8000

# Call Configuration
MAX_PHONE_LENGTH = 10
CALL_TIMEOUT_SECONDS = 600  # 5 minutes

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s" 