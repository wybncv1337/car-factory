# src/extractors/price_extractor.py

from .base_extractor import BaseExtractor
import re


class PriceExtractor(BaseExtractor):
    """Экстрактор для поиска цен и стоимости"""

    def __init__(self):
        super().__init__(name="price")
        self.patterns = [
            # Русские цены (рубли)
            {
                'pattern': r'(\d[\d\s]*)\s*(?:руб|₽|рублей|рубля|RUB)',
                'type': 'price',
                'subtype': 'ruble',
                'confidence': 0.9,
                'currency': 'RUB'
            },
            {
                'pattern': r'(\d+[.,]?\d*)\s*(?:млн|тыс|миллион|тысяч)\s*(?:руб|₽)',
                'type': 'price',
                'subtype': 'ruble',
                'confidence': 0.95,
                'currency': 'RUB'
            },
            {
                'pattern': r'цена\s*[:\s]*(\d[\d\s]*(?:[.,]\d+)?)',
                'type': 'price',
                'subtype': 'ruble',
                'confidence': 0.85,
                'currency': 'RUB'
            },
            # Доллары США
            {
                'pattern': r'\$(\d[\d,]*(?:\.\d+)?)',
                'type': 'price',
                'subtype': 'usd',
                'confidence': 0.95,
                'currency': 'USD'
            },
            {
                'pattern': r'(\d[\d,]*)\s*(?:dollars|USD|US dollars)',
                'type': 'price',
                'subtype': 'usd',
                'confidence': 0.9,
                'currency': 'USD'
            },
            {
                'pattern': r'price\s*[:\s]*\$?(\d[\d,]*(?:\.\d+)?)',
                'type': 'price',
                'subtype': 'usd',
                'confidence': 0.9,
                'currency': 'USD'
            },
            # Евро
            {
                'pattern': r'€(\d[\d,]*(?:\.\d+)?)',
                'type': 'price',
                'subtype': 'euro',
                'confidence': 0.95,
                'currency': 'EUR'
            },
            {
                'pattern': r'(\d[\d,]*)\s*(?:euros|EUR)',
                'type': 'price',
                'subtype': 'euro',
                'confidence': 0.9,
                'currency': 'EUR'
            }
        ]

    def extract(self, text, source=""):
        """Извлекает цены из текста"""
        facts = []

        for pattern_info in self.patterns:
            try:
                regex = re.compile(pattern_info['pattern'], re.IGNORECASE | re.UNICODE)
                for match in regex.finditer(text):
                    # Получаем значение
                    if match.groups():
                        value = match.group(1).strip()
                    else:
                        value = match.group(0).strip()

                    if value:
                        # Очищаем значение от пробелов и запятых
                        clean_value = re.sub(r'[,\s]', '', value)

                        # Пытаемся конвертировать в число
                        try:
                            if '.' in clean_value:
                                amount = float(clean_value)
                            else:
                                amount = int(clean_value)

                            # Проверяем множители в тексте
                            text_before = text[max(0, match.start() - 20):match.start()]
                            text_after = text[match.end():match.end() + 20]
                            context = (text_before + text_after).lower()

                            if 'тыс' in context or 'thousand' in context:
                                amount *= 1000
                            elif 'млн' in context or 'million' in context:
                                amount *= 1000000

                            fact = {
                                'type': pattern_info['type'],
                                'subtype': pattern_info.get('subtype', 'price'),
                                'value': value,
                                'amount': amount,
                                'currency': pattern_info.get('currency', 'RUB'),
                                'original_text': match.group(0),
                                'confidence': pattern_info['confidence'],
                                'source': source,
                                'position': match.start()
                            }
                            facts.append(fact)

                        except ValueError:
                            # Если не удалось конвертировать в число, сохраняем как строку
                            fact = {
                                'type': pattern_info['type'],
                                'subtype': pattern_info.get('subtype', 'price'),
                                'value': value,
                                'amount': None,
                                'currency': pattern_info.get('currency', 'RUB'),
                                'original_text': match.group(0),
                                'confidence': pattern_info['confidence'] * 0.8,  # Понижаем уверенность
                                'source': source,
                                'position': match.start()
                            }
                            facts.append(fact)

            except Exception as e:
                print(f"Ошибка в паттерне {pattern_info.get('pattern')}: {e}")
                continue

        return facts