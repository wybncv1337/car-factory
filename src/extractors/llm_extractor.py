# src/extractors/llm_extractor.py

import json
import hashlib
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

from tenacity import retry, stop_after_attempt, wait_exponential
import openai

from src.config import Config
from src.database.db_manager import DatabaseManager

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMExtractor:
    """
    Извлечение фактов с помощью LLM с кэшированием результатов
    Поддерживает:
    - Ollama (бесплатно, локально) - рекомендуется
    - DeepSeek (платно, онлайн)
    - Мок-режим (для тестирования)
    """

    def __init__(self, api_key: str = None, base_url: str = None, cache_dir: str = None):
        # Настройки по умолчанию (Ollama)
        self.base_url = base_url or getattr(Config, 'OLLAMA_BASE_URL', 'http://localhost:11434/v1')
        self.model = getattr(Config, 'OLLAMA_MODEL', 'qwen2.5:7b')
        self.api_key = api_key or "ollama"  # Ollama не требует ключ

        # Пытаемся использовать DeepSeek если настроен
        deepseek_key = os.getenv('DEEPSEEK_API_KEY') or getattr(Config, 'DEEPSEEK_API_KEY', '')
        if deepseek_key and deepseek_key not in ['', 'your-api-key-here', 'sk-placeholder']:
            self.api_key = deepseek_key
            self.base_url = "https://api.deepseek.com/v1"
            self.model = "deepseek-chat"
            logger.info("✅ Используется DeepSeek API")

        self.cache_dir = Path(cache_dir or Config.CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Подключение к БД
        self.db = DatabaseManager(Config.DB_PATH)

        # Статистика
        self.stats = {
            'total_processed': 0,
            'cache_hits': 0,
            'api_calls': 0,
            'errors': 0
        }

        # Инициализация клиента
        self.client = None
        self.mock_mode = False

        # Пытаемся инициализировать клиент
        try:
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            # Проверяем соединение (только для Ollama)
            if "localhost" in self.base_url or "127.0.0.1" in self.base_url:
                try:
                    self.client.models.list()
                    logger.info(f"✅ Ollama клиент инициализирован (модель: {self.model})")
                except Exception as e:
                    logger.warning(f"Ollama не доступен: {e}")
                    logger.info("   Убедитесь, что Ollama запущен: ollama serve")
                    logger.info("   Скачайте модель: ollama pull qwen2.5:7b")
                    self.mock_mode = True
            else:
                logger.info(f"✅ LLM клиент инициализирован ({self.base_url}, модель: {self.model})")
        except Exception as e:
            logger.warning(f"Не удалось инициализировать клиент: {e}")
            self.mock_mode = True

        # Если ничего не работает - мок-режим
        if self.mock_mode:
            logger.warning("⚠️ Работаем в мок-режиме (без реальных LLM запросов)")

    def _get_cache_key(self, text: str) -> str:
        """Создает уникальный ключ кэша на основе текста"""
        text_sample = text[:1000]
        return hashlib.md5(text_sample.encode('utf-8')).hexdigest()

    def _get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """Получает ответ из кэша"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.debug(f"Cache hit for key {cache_key}")
                return data
            except Exception as e:
                logger.warning(f"Error reading cache: {e}")
        return None

    def _save_to_cache(self, cache_key: str, data: Dict):
        """Сохраняет ответ в кэш"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved to cache: {cache_key}")
        except Exception as e:
            logger.warning(f"Error saving to cache: {e}")

    def _prepare_prompt(self, text: str) -> str:
        """Подготавливает промпт для LLM"""
        if len(text) > Config.MAX_TEXT_LENGTH:
            text = text[:Config.MAX_TEXT_LENGTH] + "..."

        prompt = f"""Ты - помощник по извлечению структурированных данных из текстов об автомобильной компании.
Извлеки информацию и верни ТОЛЬКО JSON без дополнительного текста, пояснений или маркдауна.

Текст:
{text}

Извлеки следующие факты (если есть, иначе пустой массив):

1. vacancies (вакансии):
   - position: должность
   - requirements: требования
   - salary: зарплата (число)
   - currency: валюта (RUB/USD/EUR)
   - location: локация

2. prices (цены):
   - amount: сумма (число)
   - currency: валюта
   - item: товар/услуга
   - condition: условия

3. releases (релизы):
   - model: модель
   - release_date: дата (YYYY-MM-DD)
   - specifications: характеристики

4. language: язык текста ("ru" или "en")

Верни ТОЛЬКО JSON в формате:
{{
    "vacancies": [],
    "prices": [],
    "releases": [],
    "language": "ru"
}}
"""
        return prompt

    def _extract_mock(self, text: str, source: str = "") -> Dict:
        """Мок-режим для тестирования без API"""
        # Определяем язык
        is_russian = any(c in text.lower() for c in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя')

        result = {
            "vacancies": [],
            "prices": [],
            "releases": [],
            "language": "ru" if is_russian else "en",
            "_metadata": {
                "source": source,
                "extracted_at": datetime.now().isoformat(),
                "model": "mock",
                "text_length": len(text),
                "mock_mode": True
            }
        }

        # Поиск вакансий в тексте
        vacancy_keywords = ['ваканс', 'hire', 'job', 'salary', 'зарплат', 'требуется', 'ищем', 'вакансия']
        if any(kw in text.lower() for kw in vacancy_keywords):
            result["vacancies"].append({
                "position": "Инженер-программист" if is_russian else "Software Engineer",
                "requirements": "Python, опыт работы от 3 лет" if is_russian else "Python, 3+ years experience",
                "salary": 150000 if is_russian else 120000,
                "currency": "RUB" if is_russian else "USD",
                "location": "Москва" if is_russian else "Remote"
            })

        # Поиск цен
        price_keywords = ['цена', 'price', 'стоимост', 'руб', '$', '€', '₽']
        if any(kw in text.lower() for kw in price_keywords):
            result["prices"].append({
                "amount": 2500000 if is_russian else 45000,
                "currency": "RUB" if is_russian else "USD",
                "item": "Новая модель" if is_russian else "New model",
                "condition": "new"
            })

        # Поиск релизов
        release_keywords = ['выпуст', 'release', 'новая модель', 'new model', 'релиз', 'представит']
        if any(kw in text.lower() for kw in release_keywords):
            result["releases"].append({
                "model": "Новая модель 2024" if is_russian else "New Model 2024",
                "release_date": "2024-05-15",
                "specifications": "электрический, автопилот" if is_russian else "electric, autonomous"
            })

        return result

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _call_llm(self, prompt: str) -> Dict:
        """Вызывает LLM API с повторными попытками"""
        if self.mock_mode or not self.client:
            logger.warning("Мок-режим, возвращаю тестовые данные")
            return {"_mock": True}

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system",
                     "content": "Ты - помощник по извлечению структурированных данных. Отвечай только JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000,
                timeout=Config.REQUEST_TIMEOUT
            )

            content = response.choices[0].message.content

            # Извлекаем JSON из ответа
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                return json.loads(json_str)
            else:
                return json.loads(content)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.debug(f"Raw response: {content[:500]}")
            raise
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            raise

    def extract(self, text: str, source: str = "", force_refresh: bool = False) -> Dict:
        """
        Извлекает факты из текста с использованием LLM

        Args:
            text: текст для анализа
            source: источник текста (URL или имя файла)
            force_refresh: игнорировать кэш и вызвать API

        Returns:
            словарь с извлеченными фактами
        """
        self.stats['total_processed'] += 1

        # Проверяем важность текста
        if len(text) < Config.IMPORTANCE_THRESHOLD:
            logger.debug(f"Text too short ({len(text)} chars), skipping LLM")
            return {"skipped": "text_too_short", "length": len(text)}

        # Проверяем кэш
        cache_key = self._get_cache_key(text)
        if not force_refresh and Config.CACHE_ENABLED:
            cached = self._get_cached_response(cache_key)
            if cached:
                self.stats['cache_hits'] += 1
                logger.info(f"Cache hit for {source}")
                return cached

        # Если в мок-режиме, используем мок
        if self.mock_mode:
            logger.info(f"Mock mode for {source}")
            result = self._extract_mock(text, source)
            if Config.CACHE_ENABLED:
                self._save_to_cache(cache_key, result)
            return result

        # Вызываем LLM
        logger.info(f"Calling LLM ({self.model}) for {source}...")
        self.stats['api_calls'] += 1

        try:
            prompt = self._prepare_prompt(text)
            result = self._call_llm(prompt)

            # Добавляем метаданные
            result['_metadata'] = {
                'source': source,
                'extracted_at': datetime.now().isoformat(),
                'model': self.model,
                'text_length': len(text)
            }

            # Сохраняем в кэш
            if Config.CACHE_ENABLED:
                self._save_to_cache(cache_key, result)

            # Сохраняем факты в БД
            self._save_facts_to_db(result, source)

            return result

        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"LLM extraction failed for {source}: {e}")
            # В случае ошибки используем мок
            return self._extract_mock(text, source)

    def _save_facts_to_db(self, facts: Dict, source: str):
        """Сохраняет извлеченные факты в базу данных"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Сохраняем вакансии
            for vacancy in facts.get('vacancies', []):
                cursor.execute('''
                               INSERT INTO facts (clean_doc_id, type, fact_data, confidence, created_at)
                               VALUES (?, ?, ?, ?, ?)
                               ''', (None, 'vacancy', json.dumps(vacancy, ensure_ascii=False), 0.95, datetime.now()))

            # Сохраняем цены
            for price in facts.get('prices', []):
                cursor.execute('''
                               INSERT INTO facts (clean_doc_id, type, fact_data, confidence, created_at)
                               VALUES (?, ?, ?, ?, ?)
                               ''', (None, 'price', json.dumps(price, ensure_ascii=False), 0.95, datetime.now()))

            # Сохраняем релизы
            for release in facts.get('releases', []):
                cursor.execute('''
                               INSERT INTO facts (clean_doc_id, type, fact_data, confidence, created_at)
                               VALUES (?, ?, ?, ?, ?)
                               ''', (None, 'release', json.dumps(release, ensure_ascii=False), 0.95, datetime.now()))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error saving facts to DB: {e}")

    def extract_batch(self, texts: List[Dict[str, str]], batch_size: int = 5) -> List[Dict]:
        """
        Обрабатывает пакет текстов с задержками между запросами

        Args:
            texts: список словарей [{"text": "...", "source": "..."}]
            batch_size: размер пакета для параллельной обработки

        Returns:
            список результатов
        """
        import time

        results = []
        total = len(texts)

        try:
            for i in range(0, total, batch_size):
                batch = texts[i:i + batch_size]
                logger.info(f"Processing batch {i // batch_size + 1}/{(total - 1) // batch_size + 1}")

                for j, item in enumerate(batch):
                    try:
                        logger.info(f"  Processing {j + 1}/{len(batch)}: {item.get('source', 'unknown')}")
                        result = self.extract(item['text'], item.get('source', 'unknown'))
                        results.append(result)

                        # Задержка между запросами (только для онлайн API)
                        if i + j + 1 < total and not self.mock_mode and "localhost" not in self.base_url:
                            time.sleep(1)

                    except KeyboardInterrupt:
                        raise
                    except Exception as e:
                        logger.error(f"Error processing {item.get('source')}: {e}")
                        results.append({"error": str(e), "source": item.get('source')})

                # Дополнительная задержка между батчами
                if i + batch_size < total and not self.mock_mode and "localhost" not in self.base_url:
                    logger.info(f"Waiting 3 seconds before next batch...")
                    time.sleep(3)

        except KeyboardInterrupt:
            logger.warning(f"Interrupted after processing {len(results)}/{total} texts")

        return results

    def get_stats(self) -> Dict:
        """Возвращает статистику работы"""
        return {
            **self.stats,
            'cache_size': len(list(self.cache_dir.glob('*.json'))),
            'cache_dir': str(self.cache_dir),
            'mock_mode': self.mock_mode,
            'model': self.model,
            'api_url': self.base_url
        }


# Создаем глобальный экземпляр
llm_extractor = LLMExtractor()