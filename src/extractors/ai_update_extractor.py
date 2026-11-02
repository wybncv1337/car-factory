from .base_extractor import BaseExtractor


class AIUpdateExtractor(BaseExtractor):
    """Создаёт карточку обновления ИИ-инструмента из текста новости."""
    def __init__(self):
        super().__init__("ai_update")

    def extract(self, text, source=""):
        return [{"type": "update", "value": text[:300].strip(), "description": text[:500].strip(), "source_url": source, "confidence": 0.75, "extracted_by": self.name}]
