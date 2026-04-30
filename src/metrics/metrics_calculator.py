# src/metrics/metrics_calculator.py

import sqlite3
import json
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Any
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricsCalculator:
    """Класс для расчета метрик"""

    def __init__(self, db_path: str = 'car_factory.db'):
        self.db_path = db_path
        self.conn = None

    def get_connection(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def get_news_tempo(self) -> Dict:
        """Темп новостей"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Проверяем, есть ли таблица raw_docs
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='raw_docs'")
        if cursor.fetchone():
            cursor.execute('SELECT COUNT(*) as total FROM raw_docs')
            total = cursor.fetchone()[0]

            # Группируем по 10 документов
            cursor.execute('''
                           SELECT (id - 1) / 10 as group_num,
                                  COUNT(*) as count
                           FROM raw_docs
                           GROUP BY group_num
                           ORDER BY group_num
                           ''')
            rows = cursor.fetchall()
            data = [{'date': f"Batch_{row[0] + 1}", 'count': row[1]} for row in rows]
        else:
            total = 0
            data = []

        return {
            'total': total,
            'data': data,
            'avg': total / len(data) if data else 0
        }

    def get_hiring_activity(self) -> Dict:
        """Активность найма"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Проверяем структуру таблицы facts
        cursor.execute("PRAGMA table_info(facts)")
        columns = [col[1] for col in cursor.fetchall()]

        # Определяем, как называются колонки
        data_column = None
        if 'fact_data' in columns:
            data_column = 'fact_data'
        elif 'data' in columns:
            data_column = 'data'
        elif 'content' in columns:
            data_column = 'content'
        elif 'value' in columns:
            data_column = 'value'

        # Также ищем колонку для типа
        type_column = 'type' if 'type' in columns else None

        if data_column:
            query = f"SELECT {data_column}"
            if type_column:
                query += f", {type_column}"
            query += " FROM facts"

            if type_column:
                query += f" WHERE {type_column} = 'vacancy' OR {type_column} LIKE '%vacancy%'"

            cursor.execute(query)
        else:
            # Если нет подходящих колонок, пробуем получить все
            cursor.execute("SELECT * FROM facts")

        rows = cursor.fetchall()

        vacancies = []
        salaries = []

        for row in rows:
            try:
                # Пытаемся получить данные из разных возможных форматов
                text = ""
                if data_column:
                    data = row[0]
                else:
                    data = row[0] if len(row) > 0 else ""

                # Если данные в JSON
                if isinstance(data, str) and data.startswith('{'):
                    try:
                        data_dict = json.loads(data)
                        text = str(data_dict.get('value', data_dict.get('text', '')))
                    except:
                        text = data
                else:
                    text = str(data)

                vacancies.append(text)

                # Извлекаем зарплату
                salary_match = re.search(r'(\d{5,6})', text)
                if salary_match:
                    salaries.append(int(salary_match.group(1)))

            except Exception as e:
                continue

        # Группировка по блокам
        monthly = defaultdict(int)
        for i, v in enumerate(vacancies):
            group = i // 10
            monthly[f"Batch_{group + 1}"] += 1

        return {
            'total_vacancies': len(vacancies),
            'monthly_timeline': dict(monthly),
            'avg_salary': sum(salaries) / len(salaries) if salaries else 0,
            'min_salary': min(salaries) if salaries else 0,
            'max_salary': max(salaries) if salaries else 0,
            'salary_count': len(salaries)
        }

    def get_product_changes(self) -> Dict:
        """Продуктовые изменения (релизы)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Проверяем структуру таблицы facts
        cursor.execute("PRAGMA table_info(facts)")
        columns = [col[1] for col in cursor.fetchall()]

        data_column = None
        if 'fact_data' in columns:
            data_column = 'fact_data'
        elif 'data' in columns:
            data_column = 'data'
        elif 'content' in columns:
            data_column = 'content'

        type_column = 'type' if 'type' in columns else None

        if data_column:
            query = f"SELECT {data_column}"
            if type_column:
                query += f", {type_column}"
            query += " FROM facts"

            if type_column:
                query += f" WHERE {type_column} = 'release' OR {type_column} LIKE '%release%'"

            cursor.execute(query)
        else:
            cursor.execute("SELECT * FROM facts")

        rows = cursor.fetchall()

        releases = []
        models = Counter()

        model_keywords = ['vesta', 'model 3', 'camry', 'x5', 'e-class', 'sportage', 'sonata', 'qashqai', 'tesla', 'bmw',
                          'mercedes', 'toyota', 'kia', 'hyundai', 'nissan', 'lada']

        for row in rows:
            try:
                if data_column:
                    data = row[0]
                else:
                    data = row[0] if len(row) > 0 else ""

                # Парсим данные
                if isinstance(data, str) and data.startswith('{'):
                    try:
                        data_dict = json.loads(data)
                        text = str(data_dict.get('value', data_dict.get('text', '')))
                    except:
                        text = data
                else:
                    text = str(data)

                releases.append(text.lower())

                # Ищем модели
                text_lower = text.lower()
                for model in model_keywords:
                    if model in text_lower:
                        models[model] += 1

            except Exception as e:
                continue

        # Группировка по блокам
        monthly = defaultdict(int)
        for i, r in enumerate(releases):
            group = i // 10
            monthly[f"Batch_{group + 1}"] += 1

        return {
            'total_releases': len(releases),
            'monthly_timeline': dict(monthly),
            'top_models': [{'model': m, 'count': c} for m, c in models.most_common(5)]
        }

    def get_full_report(self) -> Dict:
        """Полный отчет по метрикам"""
        return {
            'generated_at': datetime.now().isoformat(),
            'news_tempo': self.get_news_tempo(),
            'hiring_activity': self.get_hiring_activity(),
            'product_changes': self.get_product_changes()
        }