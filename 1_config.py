import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
PORT = int(os.getenv('PORT', 5000))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Model Configuration
MODEL_NAME = 'gemini-2.0-flash'
MAX_TOKENS = 2000
TEMPERATURE = 0.0

# Extraction Configuration
FUZZY_MATCH_THRESHOLD = 0.85
MIN_AMOUNT_DIFFERENCE = 0.01
REQUEST_TIMEOUT = 30

# Validation
SUPPORTED_FORMATS = ['image/png', 'image/jpeg', 'image/gif', 'image/webp']
MAX_DOCUMENT_SIZE = 50 * 1024 * 1024  # 50MB
