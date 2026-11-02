from .base_extractor import BaseExtractor


class AIPricingExtractor(BaseExtractor):
    """Создаёт карточку изменения тарифа или лимитов из текста новости."""
    def __init__(self):
        super().__init__("ai_pricing")

    def extract(self, text, source=""):
        return [{"type": "pricing", "value": text[:300].strip(), "description": text[:500].strip(), "source_url": source, "confidence": 0.75, "extracted_by": self.name}]
