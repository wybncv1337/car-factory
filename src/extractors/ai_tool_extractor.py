from .base_extractor import BaseExtractor


class AIToolExtractor(BaseExtractor):
    """Создаёт карточку нового ИИ-инструмента из текста новости."""
    def __init__(self):
        super().__init__("ai_tool")

    def extract(self, text, source=""):
        return [{"type": "tool", "value": text[:300].strip(), "description": text[:500].strip(), "source_url": source, "confidence": 0.7, "extracted_by": self.name}]
