import requests
from abc import ABC, abstractmethod
import time
import hashlib
from datetime import datetime


class BaseCollector(ABC):
    def __init__(self, db_manager):
        self.db = db_manager
        self.timeout = 45
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

    def fetch(self, url):
        """Загружает данные с повторными попытками"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"      Попытка {attempt + 1}/{max_retries}...")
                response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
                response.raise_for_status()
                return response.text, response.status_code
            except requests.exceptions.ConnectionError as e:
                if attempt < max_retries - 1:
                    print(f"      ⏳ Соединение разорвано, повтор через 3 секунды...")
                    time.sleep(3)
                    continue
                raise
            except requests.exceptions.Timeout as e:
                if attempt < max_retries - 1:
                    print(f"      ⏳ Таймаут, повтор через 3 секунды...")
                    time.sleep(3)
                    continue
                raise
            except Exception as e:
                raise
        return None, 500

    def save_raw_doc(self, source_id, content, status, error=None):
        """Сохраняет сырой документ с проверкой на дубликаты"""
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest() if content else ''

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT id FROM raw_docs WHERE content_hash = ?', (content_hash,))
            existing = cursor.fetchone()

            if existing:
                print(f"   ⏭️ Документ уже существует (hash: {content_hash[:8]}...), пропускаем")
                return existing[0]

            source = self.db.get_source_by_id(source_id)
            source_url = source['url'] if source else f"unknown_{source_id}"

            error_text = str(error) if error else None

            cursor.execute('''
                           INSERT INTO raw_docs (source_url, raw_content, content_hash, created_at)
                           VALUES (?, ?, ?, ?)
                           ''', (source_url, content or error_text, content_hash, datetime.now()))
            conn.commit()
            return cursor.lastrowid