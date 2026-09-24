import json
import sqlite3
from datetime import datetime
from pathlib import Path

from .vacancy_extractor import VacancyExtractor
from .price_extractor import PriceExtractor
from .release_extractor import ReleaseExtractor


class RuleEngine:
    def __init__(self, db_path='car_factory.db'):
        self.db_path = db_path
        self.extractors = {
            'vacancy': VacancyExtractor(),
            'price': PriceExtractor(),
            'release': ReleaseExtractor()
        }

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def detect_fact_type(self, text):
        """Определяет тип факта по тексту"""
        text_lower = text.lower()

        # Сначала проверяем ЦЕНУ (самый специфичный признак)
        price_keywords = ['pricing', 'price', 'цена', 'стоимость', 'cost',
                          'msrp', 'rub', 'usd', 'eur', '$', '€', '₽',
                          'руб', 'доллар', 'евро', 'million', 'млн']
        if any(kw in text_lower for kw in price_keywords):
            return 'price'

        # Потом ВАКАНСИЮ
        vacancy_keywords = ['вакансия', 'vacancy', 'hiring', 'job', 'salary',
                            'зарплата', 'требуется', 'ищем', 'position', 'career']
        if any(kw in text_lower for kw in vacancy_keywords):
            return 'vacancy'

        # Потом РЕЛИЗ
        release_keywords = ['release', 'launch', 'new model', 'выпустила',
                            'представила', 'новая модель', 'unveil', 'debut',
                            'announces', 'introduces']
        if any(kw in text_lower for kw in release_keywords):
            return 'release'

        # Если ничего не найдено — по умолчанию релиз
        return 'release'

    def extract_from_text(self, text, source_url=''):
        """Извлекает факты из текста"""
        all_facts = []

        # Определяем тип факта
        fact_type = self.detect_fact_type(text)

        # Извлекаем данные соответствующим экстрактором
        extractor = self.extractors.get(fact_type)
        if extractor:
            facts = extractor.extract(text)
            for fact in facts:
                fact['type'] = fact_type
                fact['source_url'] = source_url
                all_facts.append(fact)

        return all_facts

    def extract_from_clean_docs(self):
        """Извлекает факты из всех clean_docs"""
        conn = self.get_connection()
        cur = conn.cursor()

        # Проверяем структуру таблицы clean_docs
        cur.execute("PRAGMA table_info(clean_docs)")
        columns = [col[1] for col in cur.fetchall()]

        if 'source_url' in columns:
            cur.execute('''
                        SELECT c.id, c.clean_content, c.source_url
                        FROM clean_docs c
                                 LEFT JOIN facts f ON c.id = f.clean_doc_id
                        WHERE f.id IS NULL
                          AND c.clean_content IS NOT NULL
                        ''')
        else:
            cur.execute('''
                        SELECT c.id, c.clean_content, NULL as source_url
                        FROM clean_docs c
                                 LEFT JOIN facts f ON c.id = f.clean_doc_id
                        WHERE f.id IS NULL
                          AND c.clean_content IS NOT NULL
                        ''')

        docs = cur.fetchall()
        print(f"\n🔍 Найдено документов для извлечения: {len(docs)}")

        all_facts = []
        for doc_id, content, source_url in docs:
            facts = self.extract_from_text(content, source_url or '')
            for fact in facts:
                fact['clean_doc_id'] = doc_id
                all_facts.append(fact)

                # Сохраняем в БД
                try:
                    cur.execute('''
                                INSERT INTO facts (clean_doc_id, type, fact_data, confidence, source_url, created_at)
                                VALUES (?, ?, ?, ?, ?, ?)
                                ''', (
                                    doc_id,
                                    fact.get('type', 'unknown'),
                                    json.dumps(fact, ensure_ascii=False),
                                    fact.get('confidence', 0.8),
                                    fact.get('source_url', ''),
                                    datetime.now()
                                ))
                except sqlite3.OperationalError:
                    # Если колонки source_url нет
                    cur.execute('''
                                INSERT INTO facts (clean_doc_id, type, fact_data, confidence, created_at)
                                VALUES (?, ?, ?, ?, ?)
                                ''', (
                                    doc_id,
                                    fact.get('type', 'unknown'),
                                    json.dumps(fact, ensure_ascii=False),
                                    fact.get('confidence', 0.8),
                                    datetime.now()
                                ))

            print(f"  📄 Документ {doc_id}: найдено {len(facts)} фактов")

        conn.commit()
        conn.close()

        return all_facts

    def save_results(self, results, output_file=None):
        """Сохраняет результаты в JSON"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"results/extraction_{timestamp}.json"

        Path('results').mkdir(exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n💾 Результаты сохранены: {output_file}")
        return output_file