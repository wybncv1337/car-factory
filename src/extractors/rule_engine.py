"""Классификация новостей для AI Radar без вызова языковой модели."""

import json
from pathlib import Path

from .ai_pricing_extractor import AIPricingExtractor
from .ai_tool_extractor import AIToolExtractor
from .ai_update_extractor import AIUpdateExtractor


class RuleEngine:
    def __init__(self, db_path=None):
        # Аргумент сохранён, чтобы старые scripts/run_*.py не падали при запуске.
        self.db_path = db_path
        self.extractors = {"tool": AIToolExtractor(), "update": AIUpdateExtractor(), "pricing": AIPricingExtractor()}

    def detect_fact_type(self, text):
        text = text.lower()
        if any(word in text for word in ("pricing", "price", "free tier", "credits", "тариф", "цена", "стоимость", "лимит", "подписк")):
            return "pricing"
        if any(word in text for word in ("update", "changelog", "new feature", "improved", "обновлен", "новая функция", "улучшен")):
            return "update"
        return "tool"

    def extract_from_text(self, text, source_url=""):
        fact_type = self.detect_fact_type(text)
        return self.extractors[fact_type].extract(text, source_url)

    def extract_from_folder(self, folder_path):
        """Обрабатывает .txt-файлы; удобно для проверки алгоритма без сайта."""
        results = []
        for file_path in Path(folder_path).glob("*.txt"):
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            results.extend(self.extract_from_text(text, str(file_path)))
        return results

    def get_statistics(self, facts):
        return {
            "total_facts": len(facts),
            "tools": sum(f.get("type") == "tool" for f in facts),
            "updates": sum(f.get("type") == "update" for f in facts),
            "pricing": sum(f.get("type") == "pricing" for f in facts),
        }

    def save_results(self, results, output_file):
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path
