import re


class PriceExtractor:
    """Извлекает информацию о ценах"""

    def extract(self, text):
        facts = []

        # Паттерны для поиска цен
        patterns = [
            r'pricing[:\s]+([^.]{10,100})',
            r'price[:\s]+([^.]{10,100})',
            r'цена[:\s]+([^.]{10,100})',
            r'стоимость[:\s]+([^.]{10,100})',
            r'(\d[\d\s]{3,10})\s*(?:руб|₽|rub)',
            r'\$(\d[\d,]{2,10})',
            r'€(\d[\d,]{2,10})',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                facts.append({
                    'value': match.strip() if isinstance(match, str) else match,
                    'confidence': 0.85,
                    'extracted_by': 'price_extractor'
                })

        # Если ничего не нашли, сохраняем весь текст
        if not facts:
            facts.append({
                'value': text[:300],
                'confidence': 0.6,
                'extracted_by': 'price_extractor_fallback'
            })

        return facts