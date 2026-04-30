"""
Модуль для языковой поддержки и нормализации текста.
Задачи:
1. Определение языка (RU/EN).
2. Приведение дат к единому формату (ISO: YYYY-MM-DD).
3. Приведение валют к единому формату (RUB, USD, EUR и т.д.).
"""
import re
import logging
from typing import Optional, Tuple, Dict, Any

# Попытка импорта сторонних библиотек
try:
    from langdetect import detect, DetectorFactory, LangDetectException
    # Фиксируем зерно для воспроизводимости результатов
    DetectorFactory.seed = 42
    LANGLIB = True
except ImportError:
    LANGLIB = False
    logging.warning("langdetect не установлен. Языковая поддержка отключена.")

try:
    import dateparser
    DATELIB = True
except ImportError:
    DATELIB = False
    logging.warning("dateparser не установлен. Нормализация дат отключена.")

# Встроенная библиотека для работы с датами (запасной вариант)
from datetime import datetime


class TextNormalizer:
    """
    Класс для нормализации текстовых данных.
    Определяет язык, приводит даты и валюты к единому формату.
    """

    def __init__(self):
        # Словарь валют для ручного поиска (если нет currency-parser)
        self.currency_map = {
            'руб': 'RUB', 'р.': 'RUB', 'rub': 'RUB', 'rur': 'RUB',
            'usd': 'USD', 'доллар': 'USD', '$': 'USD',
            'eur': 'EUR', 'евро': 'EUR', '€': 'EUR',
            'gbp': 'GBP', 'фунт': 'GBP', '£': 'GBP',
            'cny': 'CNY', 'юань': 'CNY', '¥': 'CNY',
        }
        # Паттерны для поиска дат (ISO, RU, EN)
        self.date_patterns = [
            # ISO format
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', 'iso'),
            # RU format: 01.01.2024 or 01.01.24
            (r'(\d{1,2})\.(\d{1,2})\.(\d{2,4})', 'ru'),
            # RU format: 1 января 2024
            (r'(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+(\d{4})', 'ru_text'),
            # EN format: Jan 1, 2024 or January 1 2024
            (r'(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)[.,]?\s+(\d{1,2})[.,]?\s+(\d{4})', 'en_text'),
            # EN format: 1st January 2024
            (r'(\d{1,2})(?:st|nd|rd|th)?\s+(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)[.,]?\s+(\d{4})', 'en_text2'),
        ]

    def detect_language(self, text: str) -> str:
        """
        Определяет язык текста (RU или EN).

        Args:
            text: Входной текст.

        Returns:
            'ru', 'en' или 'unknown'.
        """
        if not text or not LANGLIB:
            return 'unknown'

        # Очищаем текст от лишних символов для более точного определения
        clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
        # Берем первые 1000 символов для скорости
        sample = clean_text[:1000].strip()

        if not sample:
            return 'unknown'

        try:
            lang = detect(sample)
            if lang.startswith('ru'):
                return 'ru'
            elif lang.startswith('en'):
                return 'en'
            else:
                return 'unknown'
        except LangDetectException:
            return 'unknown'

    def normalize_date(self, date_str: str, hint_lang: str = None) -> Optional[str]:
        """
        Приводит дату к формату YYYY-MM-DD.

        Args:
            date_str: Строка с датой.
            hint_lang: Подсказка языка ('ru', 'en'). Если None, определяется автоматически.

        Returns:
            Дата в формате ISO или None, если не удалось распарсить.
        """
        if not date_str or not DATELIB:
            return None

        # Настройка языков для dateparser
        lang_codes = ['ru', 'en']  # По умолчанию ищем и там, и там
        if hint_lang == 'ru':
            lang_codes = ['ru']
        elif hint_lang == 'en':
            lang_codes = ['en']

        # Пытаемся распарсить через dateparser (он лучше справляется с текстовыми датами)
        parsed_date = dateparser.parse(
            date_str,
            languages=lang_codes,
            settings={
                'PREFER_DATES_FROM': 'past',
                'DATE_ORDER': 'DMY' if hint_lang == 'ru' else 'MDY'
            }
        )

        if parsed_date:
            return parsed_date.strftime('%Y-%m-%d')

        # Если dateparser не сработал, пробуем свои регулярные выражения
        for pattern, pattern_type in self.date_patterns:
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                try:
                    return self._parse_date_with_pattern(match.groups(), pattern_type)
                except (ValueError, IndexError):
                    continue
        return None

    def _parse_date_with_pattern(self, groups: Tuple[str, ...], pattern_type: str) -> str:
        """Вспомогательный метод для парсинга дат по паттернам."""
        year, month, day = None, None, None

        if pattern_type == 'iso':
            year, month, day = groups[0], groups[1], groups[2]
        elif pattern_type == 'ru':
            day, month, year = groups[0], groups[1], groups[2]
            # Преобразуем год в 4-значный
            if len(year) == 2:
                year = '20' + year if int(year) < 50 else '19' + year
        elif pattern_type == 'ru_text':
            day, month_name, year = groups
            month = self._ru_month_to_number(month_name)
        elif pattern_type in ['en_text', 'en_text2']:
            if pattern_type == 'en_text':
                month_name, day, year = groups
            else:  # en_text2
                day, month_name, year = groups
            month = self._en_month_to_number(month_name)

        if year and month and day:
            return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
        return None

    def _ru_month_to_number(self, month_name: str) -> str:
        months = {
            'января': '1', 'февраля': '2', 'марта': '3', 'апреля': '4',
            'мая': '5', 'июня': '6', 'июля': '7', 'августа': '8',
            'сентября': '9', 'октября': '10', 'ноября': '11', 'декабря': '12'
        }
        return months.get(month_name.lower(), '1')

    def _en_month_to_number(self, month_name: str) -> str:
        months = {
            'jan': '1', 'january': '1',
            'feb': '2', 'february': '2',
            'mar': '3', 'march': '3',
            'apr': '4', 'april': '4',
            'may': '5',
            'jun': '6', 'june': '6',
            'jul': '7', 'july': '7',
            'aug': '8', 'august': '8',
            'sep': '9', 'september': '9',
            'oct': '10', 'october': '10',
            'nov': '11', 'november': '11',
            'dec': '12', 'december': '12'
        }
        return months.get(month_name.lower()[:3], '1')

    def normalize_currency(self, text: str) -> Dict[str, Any]:
        """
        Ищет в тексте валюты и приводит их к стандартному виду.

        Args:
            text: Входной текст.

        Returns:
            Словарь с найденными валютами: {
                "currency": "RUB",
                "amount": 1500000.00,
                "original": "1.5 млн руб"
            }
        """
        result = {
            "currency": None,
            "amount": None,
            "original": None
        }

        if not text:
            return result

        # Ищем числа, за которыми могут следовать валюты
        # Простой паттерн: число (с возможными разделителями и суффиксами млн/тыс) + валюта
        amount_patterns = [
            # 1 500 000 руб, 1.5 млн руб
            r'(\d+(?:[.,]\d+)?)\s*(?:млн|тыс|million|thousand)?\s*(' + '|'.join(re.escape(key) for key in self.currency_map.keys()) + r')',
            # $1.5 million, $1500
            r'(' + '|'.join(re.escape(key) for key in self.currency_map.keys()) + r')\s*(\d+(?:[.,]\d+)?)\s*(?:млн|тыс|million|thousand)?',
        ]

        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                if match.group(0)[0].isdigit():
                    # Число первое
                    amount_str, curr_key = groups
                else:
                    # Валюта первая
                    curr_key, amount_str = groups

                result['original'] = match.group(0)
                result['currency'] = self.currency_map.get(curr_key.lower(), curr_key.upper())

                # Обработка числа
                amount_str = amount_str.replace(',', '.').replace(' ', '')
                try:
                    amount = float(amount_str)
                    # Проверяем множители (млн, тыс)
                    if 'млн' in match.group(0).lower() or 'million' in match.group(0).lower():
                        amount *= 1_000_000
                    elif 'тыс' in match.group(0).lower() or 'thousand' in match.group(0).lower():
                        amount *= 1_000
                    result['amount'] = amount
                except ValueError:
                    result['amount'] = None
                break

        return result

    def process_text(self, text: str) -> Dict[str, Any]:
        """
        Главный метод обработки текста: определяет язык, находит и нормализует даты и валюты.

        Args:
            text: Входной текст.

        Returns:
            Словарь с результатами обработки.
        """
        if not text:
            return {'language': 'unknown', 'dates': [], 'currencies': []}

        # 1. Определяем язык
        language = self.detect_language(text)

        # 2. Ищем все даты (простой поиск)
        # В реальном проекте здесь может быть более сложная логика
        date_mentions = []
        # Для демонстрации просто берем первую найденную дату
        date = self.normalize_date(text, language)
        if date:
            date_mentions.append(date)

        # 3. Ищем валюты
        currency_mentions = []
        currency = self.normalize_currency(text)
        if currency['currency']:
            currency_mentions.append(currency)

        return {
            'language': language,
            'dates': date_mentions,
            'currencies': currency_mentions
        }

# Создаем глобальный экземпляр для удобства использования
normalizer = TextNormalizer()

# Пример использования
if __name__ == '__main__':
    # Тестовые примеры
    test_texts = [
        "Компания выпустит новую модель 15 мая 2024 года. Цена составит 2.5 млн руб.",
        "The new car will be released on January 15, 2024. Price: $45,000.",
        "Дата выхода: 01.02.24. Стоимость: 1500000 рублей.",
        "Launch date: 2024-03-01. Price: 35000 EUR."
    ]

    for text in test_texts:
        result = normalizer.process_text(text)
        print(f"\nТекст: {text}")
        print(f"Результат: {result}")