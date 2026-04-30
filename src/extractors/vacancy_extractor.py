# src/extractors/vacancy_extractor.py

from .base_extractor import BaseExtractor
import re


class VacancyExtractor(BaseExtractor):
    """Экстрактор для поиска вакансий"""

    def __init__(self):
        super().__init__(name="vacancy")  # 👈 Передаем имя
        self.patterns = [
            # Русские вакансии
            {
                'pattern': r'(?:вакансия|требуется|ищем|открыта вакансия|в поиске)\s+([А-Яа-я\s]+)',
                'type': 'vacancy',
                'subtype': 'title',
                'confidence': 0.9
            },
            {
                'pattern': r'(?:зарплата|оклад|доход|з/п|заработная плата)\s*[:\s]*(\d[\d\s]*(?:\.?\d+)?)',
                'type': 'vacancy',
                'subtype': 'salary',
                'confidence': 0.85
            },
            {
                'pattern': r'(?:опыт работы|требования|квалификация)\s*[:\s]*([А-Яа-я\s\d]+)',
                'type': 'vacancy',
                'subtype': 'requirements',
                'confidence': 0.8
            },
            {
                'pattern': r'(?:график работы|режим работы)\s*[:\s]*([А-Яа-я\s]+)',
                'type': 'vacancy',
                'subtype': 'schedule',
                'confidence': 0.8
            },
            # Английские вакансии
            {
                'pattern': r'(?:vacancy|job|position|hiring|we are looking for)\s+([A-Za-z\s]+)',
                'type': 'vacancy',
                'subtype': 'title',
                'confidence': 0.9
            },
            {
                'pattern': r'(?:salary|wage|pay|compensation)\s*[:\s]*\$?(\d[\d,]*(?:\.?\d+)?)',
                'type': 'vacancy',
                'subtype': 'salary',
                'confidence': 0.85
            },
            {
                'pattern': r'(?:experience|requirements|qualifications)\s*[:\s]*([A-Za-z\s\d]+)',
                'type': 'vacancy',
                'subtype': 'requirements',
                'confidence': 0.8
            },
            {
                'pattern': r'(?:work schedule|work mode)\s*[:\s]*([A-Za-z\s]+)',
                'type': 'vacancy',
                'subtype': 'schedule',
                'confidence': 0.8
            }
        ]

    def extract(self, text, source=""):
        """Извлекает информацию о вакансиях"""
        return self._extract_with_patterns(text, source)