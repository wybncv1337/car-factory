import json
from datetime import datetime
from pathlib import Path
from .vacancy_extractor import VacancyExtractor
from .price_extractor import PriceExtractor
from .release_extractor import ReleaseExtractor
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.database.db_manager import DatabaseManager

# Добавляем импорт нормализатора
from src.utils.text_normalizer import normalizer

from src.extractors.llm_extractor import llm_extractor


def extract_with_llm(self, text, source="", force_refresh=False):
    """
    Извлекает факты с помощью LLM (только для важных текстов)
    """
    # Проверяем важность текста
    if len(text) < 500:
        return {"skipped": "text_too_short"}

    # Используем LLM экстрактор
    result = llm_extractor.extract(text, source, force_refresh)

    # Сохраняем результаты в БД
    if 'error' not in result:
        self.db.save_fact(
            None,
            'llm_extraction',
            json.dumps(result, ensure_ascii=False),
            confidence=0.95
        )

    return result


def extract_mixed(self, text, source=""):
    """
    Комбинированное извлечение:
    - Для коротких текстов: rule-based экстракторы
    - Для длинных текстов: rule-based + LLM
    """
    # Сначала получаем факты через rule-based экстракторы
    rule_facts = self.extract_from_text(text, source)

    # Если текст важный, добавляем LLM-извлечение
    llm_facts = {}
    if len(text) >= 500:
        llm_result = self.extract_with_llm(text, source)
        if 'error' not in llm_result:
            llm_facts = llm_result

    return {
        'rule_based': rule_facts,
        'llm_based': llm_facts,
        'combined': rule_facts + [llm_facts] if llm_facts else rule_facts
    }

class RuleEngine:
    def __init__(self, db_path='car_factory.db'):
        self.db = DatabaseManager(db_path)
        self.extractors = {
            'vacancy': VacancyExtractor(),
            'price': PriceExtractor(),
            'release': ReleaseExtractor()
        }

    def extract_from_text(self, text, filename="unknown", clean_doc_id=None):
        all_facts = []

        # Получаем нормализованные данные из текста
        normalized_data = normalizer.process_text(text)

        for extractor_name, extractor in self.extractors.items():
            facts = extractor.extract(text, filename)
            for fact in facts:
                # Добавляем нормализованные поля к каждому факту
                fact['clean_doc_id'] = clean_doc_id
                fact['language'] = normalized_data['language']
                fact['normalized_dates'] = normalized_data['dates']
                fact['normalized_currencies'] = normalized_data['currencies']
                all_facts.append(fact)

                if clean_doc_id:
                    self.db.save_fact(
                        clean_doc_id,
                        fact['type'],
                        json.dumps(fact, ensure_ascii=False),
                        fact['confidence']
                    )

        return all_facts

    def extract_from_file(self, filepath, clean_doc_id=None):
        filepath = Path(filepath)
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()

        return self.extract_from_text(text, filepath.name, clean_doc_id)

    def extract_from_folder(self, folder_path):
        folder = Path(folder_path)
        if not folder.exists():
            print(f"❌ Папка {folder} не найдена")
            return {}

        results = {}
        txt_files = list(folder.glob('*.txt'))

        print(f"\n📂 Обрабатывается папка: {folder}")
        print(f"📄 Найдено файлов: {len(txt_files)}")

        # Статистика по языкам
        language_stats = {'ru': 0, 'en': 0, 'unknown': 0}

        for filepath in txt_files:
            print(f"  🔍 {filepath.name}...", end='')
            facts = self.extract_from_file(filepath)
            results[filepath.name] = facts

            # Собираем статистику по языкам
            if facts:
                # Берем язык из первого факта (они все одинаковые для одного файла)
                lang = facts[0].get('language', 'unknown')
                language_stats[lang] = language_stats.get(lang, 0) + 1

            print(f" найдено {len(facts)} фактов")

        # Выводим статистику по языкам
        print(f"\n📊 Статистика по языкам:")
        for lang, count in language_stats.items():
            if count > 0:
                print(f"   {lang.upper()}: {count} файлов")

        return results

    def extract_from_clean_docs(self):
        """Извлечь факты из всех clean_docs"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
                       SELECT c.id, c.clean_content, c.raw_doc_id
                       FROM clean_docs c
                                LEFT JOIN facts f ON c.id = f.clean_doc_id
                       WHERE f.id IS NULL
                       ''')

        docs = cursor.fetchall()
        conn.close()

        print(f"\n🔍 Найдено документов для извлечения фактов: {len(docs)}")

        results = []
        language_stats = {'ru': 0, 'en': 0, 'unknown': 0}

        for doc_id, content, raw_doc_id in docs:
            facts = self.extract_from_text(content, f"doc_{doc_id}", doc_id)
            results.extend(facts)

            # Собираем статистику по языкам
            if facts:
                lang = facts[0].get('language', 'unknown')
                language_stats[lang] = language_stats.get(lang, 0) + 1

            print(f"  📄 Документ {doc_id}: найдено {len(facts)} фактов")

        # Выводим статистику по языкам
        print(f"\n📊 Статистика по языкам в документах:")
        for lang, count in language_stats.items():
            if count > 0:
                print(f"   {lang.upper()}: {count} документов")

        return results

    def save_results(self, results, output_file=None):
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"results/extraction_{timestamp}.json"

        Path('results').mkdir(exist_ok=True)

        serializable = {}
        for filename, facts in results.items():
            serializable[filename] = facts

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable, f, ensure_ascii=False, indent=2)

        print(f"\n💾 Результаты сохранены в {output_file}")
        return output_file

    def get_statistics(self, results):
        stats = {
            'total_files': len(results),
            'total_facts': 0,
            'by_type': {},
            'by_confidence': {
                'high': 0, 'medium': 0, 'low': 0
            },
            'files_with_facts': 0,
            'language_stats': {'ru': 0, 'en': 0, 'unknown': 0}  # Добавляем статистику по языкам
        }

        for filename, facts in results.items():
            if facts:
                stats['files_with_facts'] += 1
                # Считаем языки
                lang = facts[0].get('language', 'unknown')
                stats['language_stats'][lang] = stats['language_stats'].get(lang, 0) + 1

            stats['total_facts'] += len(facts)

            for fact in facts:
                fact_type = fact['type']
                stats['by_type'][fact_type] = stats['by_type'].get(fact_type, 0) + 1

                conf = fact['confidence']
                if conf >= 0.9:
                    stats['by_confidence']['high'] += 1
                elif conf >= 0.7:
                    stats['by_confidence']['medium'] += 1
                else:
                    stats['by_confidence']['low'] += 1

        return stats

    def analyze_dates_and_currencies(self, results):
        """
        Дополнительный метод для анализа найденных дат и валют
        """
        date_stats = {
            'total_dates_found': 0,
            'files_with_dates': 0,
            'avg_dates_per_file': 0
        }

        currency_stats = {
            'total_currencies_found': 0,
            'files_with_currencies': 0,
            'currency_types': {}
        }

        files_with_dates = 0
        files_with_currencies = 0

        for filename, facts in results.items():
            has_date = False
            has_currency = False

            for fact in facts:
                # Считаем даты
                dates = fact.get('normalized_dates', [])
                if dates:
                    has_date = True
                    date_stats['total_dates_found'] += len(dates)

                # Считаем валюты
                currencies = fact.get('normalized_currencies', [])
                if currencies:
                    has_currency = True
                    for curr in currencies:
                        curr_code = curr.get('currency')
                        if curr_code:
                            currency_stats['currency_types'][curr_code] = \
                                currency_stats['currency_types'].get(curr_code, 0) + 1

            if has_date:
                files_with_dates += 1
            if has_currency:
                files_with_currencies += 1

        date_stats['files_with_dates'] = files_with_dates
        date_stats['avg_dates_per_file'] = date_stats['total_dates_found'] / len(results) if results else 0

        currency_stats['files_with_currencies'] = files_with_currencies
        currency_stats['total_currencies_found'] = sum(currency_stats['currency_types'].values())

        return {
            'date_statistics': date_stats,
            'currency_statistics': currency_stats
        }


# Пример использования
if __name__ == '__main__':
    # Быстрый тест
    engine = RuleEngine()

    # Тестовый текст
    test_text = """
    Компания выпустит новую модель 15 мая 2024 года. 
    Цена составит 2.5 млн руб. 
    Требуется инженер с зарплатой $5000 в месяц.
    """

    facts = engine.extract_from_text(test_text, "test.txt")
    print(json.dumps(facts, ensure_ascii=False, indent=2))