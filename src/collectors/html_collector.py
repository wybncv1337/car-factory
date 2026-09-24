# src/collectors/html_collector.py
import requests
import time
from .base_collector import BaseCollector


class HTMLCollector(BaseCollector):
    def __init__(self, db_manager):
        super().__init__(db_manager)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

    def fetch(self, url):
        """Загружает HTML страницу"""
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text, response.status_code

    def collect(self, source):
        """Собирает данные с одного источника"""
        source_id = source.get('id')
        url = source.get('url')
        name = source.get('name', f'Источник {source_id}')

        if not url:
            return False, "No URL provided"

        try:
            print(f"   📡 Загрузка: {name}")
            content, status = self.fetch(url)

            self.db.save_raw_doc(source_id, content, status, None)

            return True, content
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            print(f"   ❌ Ошибка: {error_msg}")
            self.db.add_alert(source_id, 'parse_error', error_msg)
            self.db.save_raw_doc(source_id, '', 0, error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = str(e)
            print(f"   ❌ Исключение: {error_msg}")
            self.db.add_alert(source_id, 'parse_error', error_msg)
            return False, error_msg

    def collect_all(self):
        """Сбор данных со всех HTML источников"""
        results = []
        sources = self.db.get_active_sources('html')

        print(f"\n🔍 Найдено HTML-источников: {len(sources)}")

        for i, source in enumerate(sources):
            source_id = source['id']
            source_name = source.get('name', f'Источник {source_id}')
            source_url = source.get('url', '')

            print(f"\n📡 Обработка: {source_name}")
            print(f"   URL: {source_url}")

            try:
                success, content = self.collect(source)

                results.append({
                    'source_id': source_id,
                    'source_name': source_name,
                    'url': source_url,
                    'content': content if success else None,
                    'error': None if success else content,
                    'status': 'success' if success else 'failed'
                })

                if success:
                    print(f"   ✅ Успешно: {len(content)} символов")
                else:
                    print(f"   ❌ Ошибка: {content}")

            except Exception as e:
                print(f"   ❌ Критическая ошибка: {e}")
                results.append({
                    'source_id': source_id,
                    'source_name': source_name,
                    'url': source_url,
                    'content': None,
                    'error': str(e),
                    'status': 'failed'
                })


            if i < len(sources) - 1:
                print(f"   ⏳ Ждём 3 секунды перед следующим запросом...")
                time.sleep(3)

        return results