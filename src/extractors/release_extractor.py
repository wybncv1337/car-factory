# src/extractors/release_extractor.py

from .base_extractor import BaseExtractor
import re


class ReleaseExtractor(BaseExtractor):
    """Экстрактор для поиска информации о релизах и новых моделях"""

    def __init__(self):
        super().__init__(name="release")
        self.patterns = [
            # Русские релизы
            {
                'pattern': r'(?:выпустит|представит|запустит|релиз|анонсирует|презентует)\s+([А-Яа-я0-9\s]+)',
                'type': 'release',
                'subtype': 'model',
                'confidence': 0.9
            },
            {
                'pattern': r'(?:новая модель|новинка|модель)\s+([А-Яа-я0-9\s]+)',
                'type': 'release',
                'subtype': 'model',
                'confidence': 0.85
            },
            {
                'pattern': r'(?:дата выхода|релиз|выпуск|поступление в продажу)\s*[:\s]*(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
                'type': 'release',
                'subtype': 'date',
                'confidence': 0.95
            },
            {
                'pattern': r'(\d{1,2}\s+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+\d{4})',
                'type': 'release',
                'subtype': 'date',
                'confidence': 0.95
            },
            # Английские релизы
            {
                'pattern': r'(?:releases|launches|introduces|announces|presents)\s+([A-Za-z0-9\s]+)',
                'type': 'release',
                'subtype': 'model',
                'confidence': 0.9
            },
            {
                'pattern': r'(?:new model|new car|new vehicle)\s+([A-Za-z0-9\s]+)',
                'type': 'release',
                'subtype': 'model',
                'confidence': 0.85
            },
            {
                'pattern': r'(?:release date|launch date|available from)\s*[:\s]*([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
                'type': 'release',
                'subtype': 'date',
                'confidence': 0.95
            },
            {
                'pattern': r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
                'type': 'release',
                'subtype': 'date',
                'confidence': 0.95
            }
        ]

    def extract(self, text, source=""):
        """Извлекает информацию о релизах"""
        facts = []

        for pattern_info in self.patterns:
            try:
                regex = re.compile(pattern_info['pattern'], re.IGNORECASE | re.UNICODE)
                for match in regex.finditer(text):
                    if match.groups():
                        value = match.group(1).strip()
                    else:
                        value = match.group(0).strip()

                    if value:
                        fact = {
                            'type': pattern_info['type'],
                            'subtype': pattern_info.get('subtype', 'info'),
                            'value': value,
                            'original_text': match.group(0),
                            'confidence': pattern_info['confidence'],
                            'source': source,
                            'position': match.start()
                        }
                        facts.append(fact)

            except Exception as e:
                print(f"Ошибка в паттерне {pattern_info.get('pattern')}: {e}")
                continue

        return facts