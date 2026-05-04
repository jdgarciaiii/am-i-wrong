import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # API Configuration
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(32))
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Security Configuration
    CORS_ORIGINS = ['http://localhost:5000', 'http://127.0.0.1:5000', 
                    'https://localhost:5000', 'https://127.0.0.1:5000']
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS = 10  # requests per minute
    RATE_LIMIT_WINDOW = 60    # seconds
    
    # Input Validation
    MAX_INPUT_LENGTH = 800
    MIN_INPUT_LENGTH = 10
    
    # API Configuration
    API_TIMEOUT = 30
    API_MODEL = 'claude-3-haiku-20240307'
    API_MAX_TOKENS = 1000
