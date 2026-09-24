import sqlite3
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_path='car_factory.db'):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS sources
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               name
                               TEXT
                               NOT
                               NULL,
                               url
                               TEXT
                               NOT
                               NULL,
                               source_type
                               TEXT
                               DEFAULT
                               'html',
                               is_active
                               INTEGER
                               DEFAULT
                               1,
                               created_at
                               TIMESTAMP
                               DEFAULT
                               CURRENT_TIMESTAMP
                           )
                           ''')

            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS raw_docs
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               source_url
                               TEXT,
                               raw_content
                               TEXT,
                               created_at
                               TIMESTAMP
                               DEFAULT
                               CURRENT_TIMESTAMP
                           )
                           ''')

            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS clean_docs
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               raw_doc_id
                               INTEGER,
                               clean_content
                               TEXT,
                               created_at
                               TIMESTAMP
                               DEFAULT
                               CURRENT_TIMESTAMP
                           )
                           ''')

            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS facts
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               clean_doc_id
                               INTEGER,
                               type
                               TEXT,
                               fact_data
                               TEXT,
                               confidence
                               REAL,
                               created_at
                               TIMESTAMP
                               DEFAULT
                               CURRENT_TIMESTAMP
                           )
                           ''')

            conn.commit()

            # Добавляем тестовые источники
            cursor.execute("SELECT COUNT(*) FROM sources")
            if cursor.fetchone()[0] == 0:
                sources = [
                    ('АвтоВАЗ новости', 'https://www.lada.ru/press', 'html'),
                    ('Tesla news', 'https://www.tesla.com/blog', 'html'),
                ]
                cursor.executemany('INSERT INTO sources (name, url, source_type) VALUES (?, ?, ?)', sources)
                conn.commit()

    def get_active_sources(self, source_type=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if source_type:
                cursor.execute("SELECT * FROM sources WHERE is_active = 1 AND source_type = ?", (source_type,))
            else:
                cursor.execute("SELECT * FROM sources WHERE is_active = 1")
            return [dict(row) for row in cursor.fetchall()]

    def get_source_by_id(self, source_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sources WHERE id = ?", (source_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def save_raw_doc(self, source_id, content, status, error=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            source = self.get_source_by_id(source_id)
            source_url = source['url'] if source else f"unknown_{source_id}"

            error_text = str(error) if error else None
            cursor.execute('''
                           INSERT INTO raw_docs (source_url, raw_content, created_at)
                           VALUES (?, ?, ?)
                           ''', (source_url, content or error_text, datetime.now()))
            conn.commit()
            return cursor.lastrowid

    def save_clean_doc(self, raw_doc_id, clean_content):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO clean_docs (raw_doc_id, clean_content) VALUES (?, ?)',
                           (raw_doc_id, clean_content))
            conn.commit()
            return cursor.lastrowid

    def save_fact(self, clean_doc_id, fact_type, fact_data, confidence):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                           INSERT INTO facts (clean_doc_id, type, fact_data, confidence, created_at)
                           VALUES (?, ?, ?, ?, ?)
                           ''', (clean_doc_id, fact_type, fact_data, confidence, datetime.now()))
            conn.commit()
            return cursor.lastrowid

    def add_alert(self, source_id, alert_type, message):
        print(f"⚠️ ALERT: source={source_id}, type={alert_type}, message={message}")
        return True

    def get_stats(self):
        """Получает статистику по базе данных"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            stats = {}

            # Количество источников
            cursor.execute("SELECT COUNT(*) FROM sources")
            stats['sources'] = cursor.fetchone()[0]

            # Количество raw документов
            cursor.execute("SELECT COUNT(*) FROM raw_docs")
            stats['raw_docs'] = cursor.fetchone()[0]

            # Количество clean документов
            cursor.execute("SELECT COUNT(*) FROM clean_docs")
            stats['clean_docs'] = cursor.fetchone()[0]

            # Количество фактов по типам
            for fact_type in ['vacancy', 'release', 'price']:
                cursor.execute("SELECT COUNT(*) FROM facts WHERE type = ?", (fact_type,))
                stats[f'facts_{fact_type}'] = cursor.fetchone()[0]

            # Всего фактов
            cursor.execute("SELECT COUNT(*) FROM facts")
            stats['facts_total'] = cursor.fetchone()[0]

            return stats