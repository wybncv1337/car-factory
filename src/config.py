# src/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env файл
load_dotenv()


class Config:
    # Ollama настройки (бесплатно, локально)
    OLLAMA_BASE_URL = "http://localhost:11434/v1"
    OLLAMA_MODEL = "qwen2.5:7b"  # или "gemma2:9b", "llama3.1:8b", "mistral:7b"

    # DeepSeek настройки (опционально, если есть ключ)
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')

    # Для совместимости (автоматически выбирает DeepSeek если есть ключ, иначе Ollama)
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

    # Настройки кэша
    CACHE_DIR = Path('cache/llm_responses')
    CACHE_ENABLED = True

    # Порог "важности" текста (минимальная длина для отправки в LLM)
    IMPORTANCE_THRESHOLD = 500  # символов

    # Настройки базы данных
    DB_PATH = 'car_factory.db'

    # Лимиты
    MAX_TEXT_LENGTH = 4000
    REQUEST_TIMEOUT = 30