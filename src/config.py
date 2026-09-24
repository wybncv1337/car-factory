# src/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env файл
load_dotenv()


class Config:
    OLLAMA_BASE_URL = "http://localhost:11434/v1"
    OLLAMA_MODEL = "qwen2.5:7b"

    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')

    @classmethod
    def get_llm_config(cls):
        if cls.DEEPSEEK_API_KEY and cls.DEEPSEEK_API_KEY not in ['', 'your-api-key-here']:
            return {
                'api_key': cls.DEEPSEEK_API_KEY,
                'base_url': "https://api.deepseek.com/v1",
                'model': "deepseek-chat"
            }
        else:
            return {
                'api_key': "ollama",
                'base_url': cls.OLLAMA_BASE_URL,
                'model': cls.OLLAMA_MODEL
            }

    CACHE_DIR = Path('cache/llm_responses')
    CACHE_ENABLED = True

    IMPORTANCE_THRESHOLD = 500

    DB_PATH = 'car_factory.db'

    MAX_TEXT_LENGTH = 4000
    REQUEST_TIMEOUT = 30