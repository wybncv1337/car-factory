# src/extractors/base_extractor.py

import re
from abc import ABC, abstractmethod


class BaseExtractor(ABC):
    """Базовый класс для всех экстракторов"""

    def __init__(self, name="base"):
        """
        Конструктор базового экстрактора
        Args:
            name: имя экстрактора (по умолчанию "base")
        """
        self.name = name
        self.patterns = []  # Должен быть списком словарей

    @abstractmethod
    def extract(self, text, source=""):
        """Основной метод для извлечения фактов"""
        pass

    def _compile_patterns(self):
        """Компилирует регулярные выражения из паттернов"""
        compiled = []
        for pattern in self.patterns:
            if isinstance(pattern, dict):
                # Если словарь - компилируем regex из ключа 'pattern'
                if 'pattern' in pattern:
                    try:
                        compiled.append({
                            'regex': re.compile(pattern['pattern'], re.IGNORECASE | re.UNICODE),
                            'type': pattern.get('type', 'unknown'),
                            'subtype': pattern.get('subtype', ''),
                            'confidence': pattern.get('confidence', 0.8),
                            'field': pattern.get('field', 'value'),
                            'currency': pattern.get('currency', None)
                        })
                    except re.error as e:
                        print(f"Ошибка компиляции regex {pattern['pattern']}: {e}")
            elif isinstance(pattern, (tuple, list)) and len(pattern) >= 2:
                # Для обратной совместимости с кортежами
                try:
                    regex_str = pattern[0] if isinstance(pattern[0], str) else str(pattern[0])
                    compiled.append({
                        'regex': re.compile(regex_str, re.IGNORECASE | re.UNICODE),
                        'type': pattern[1] if len(pattern) > 1 else 'unknown',
                        'subtype': '',
                        'confidence': pattern[2] if len(pattern) > 2 else 0.8,
                        'field': 'value',
                        'currency': None
                    })
                except re.error as e:
                    print(f"Ошибка компиляции regex {regex_str}: {e}")
        return compiled

    def _extract_with_patterns(self, text, source=""):
        """Общий метод для извлечения с использованием паттернов"""
        facts = []
        compiled_patterns = self._compile_patterns()

        for pattern_info in compiled_patterns:
            try:
                regex = pattern_info['regex']
                fact_type = pattern_info['type']
                subtype = pattern_info['subtype']
                confidence = pattern_info['confidence']

                for match in regex.finditer(text):
                    # Берем первую группу или всю строку
                    if match.groups():
                        value = match.group(1).strip()
                    else:
                        value = match.group(0).strip()

                    if value:  # Проверяем, что значение не пустое
                        fact = {
                            'type': fact_type,
                            'subtype': subtype,
                            'value': value,
                            'original_text': match.group(0),
                            'confidence': confidence,
                            'source': source,
                            'position': match.start()
                        }

                        # Добавляем валюту если есть
                        if pattern_info.get('currency'):
                            fact['currency'] = pattern_info['currency']

                        facts.append(fact)
            except Exception as e:
                print(f"Ошибка при обработке паттерна {pattern_info.get('type')}: {e}")
                continue

        return facts