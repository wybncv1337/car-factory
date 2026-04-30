import sqlite3
from datetime import datetime
from . import models

class DatabaseManager:
    def __init__(self, db_path='car_factory.db'):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        """Получить соединение с БД"""
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        """Создание всех таблиц"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(models.CREATE_COMPANIES_TABLE)
        cursor.execute(models.CREATE_SOURCES_TABLE)
        cursor.execute(models.CREATE_RAW_DOCS_TABLE)
        cursor.execute(models.CREATE_CLEAN_DOCS_TABLE)
        cursor.execute(models.CREATE_FACTS_TABLE)
        cursor.execute(models.CREATE_ALERTS_TABLE)
        
        for index in models.CREATE_INDEXES:
            cursor.execute(index)
        
        conn.commit()
        conn.close()
        print("✅ База данных инициализирована")
    
    def add_company(self, name, website_url=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO companies (name, website_url)
            VALUES (?, ?)
        ''', (name, website_url))
        company_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return company_id
    
    def add_source(self, company_name, source_type, url, name=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM companies WHERE name = ?', (company_name,))
        company = cursor.fetchone()
        
        if not company:
            print(f"❌ Компания {company_name} не найдена")
            conn.close()
            return None
        
        company_id = company[0]
        cursor.execute('''
            INSERT OR IGNORE INTO sources (company_id, source_type, url, name)
            VALUES (?, ?, ?, ?)
        ''', (company_id, source_type, url, name))
        
        source_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return source_id
    
    def get_active_sources(self, source_type=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT s.id, s.company_id, s.source_type, s.url, s.name, c.name as company_name
            FROM sources s
            JOIN companies c ON s.company_id = c.id
            WHERE s.is_active = 1
        '''
        params = []
        
        if source_type:
            query += ' AND s.source_type = ?'
            params.append(source_type)
        
        cursor.execute(query, params)
        sources = cursor.fetchall()
        conn.close()
        return sources
    
    def save_raw_doc(self, source_id, content, status=200, error=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO raw_docs (source_id, raw_content, http_status, error_message)
            VALUES (?, ?, ?, ?)
        ''', (source_id, content, status, error))
        
        doc_id = cursor.lastrowid
        
        cursor.execute('''
            UPDATE sources SET last_checked = ? WHERE id = ?
        ''', (datetime.now(), source_id))
        
        conn.commit()
        conn.close()
        return doc_id
    
    def save_clean_doc(self, raw_doc_id, clean_content, content_hash):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO clean_docs (raw_doc_id, clean_content, content_hash)
            VALUES (?, ?, ?)
        ''', (raw_doc_id, clean_content, content_hash))
        
        doc_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return doc_id
    
    def save_fact(self, clean_doc_id, fact_type, fact_json, confidence):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO facts (clean_doc_id, fact_type, fact_json, confidence)
            VALUES (?, ?, ?, ?)
        ''', (clean_doc_id, fact_type, fact_json, confidence))
        
        fact_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return fact_id
    
    def add_alert(self, source_id, alert_type, message):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts (source_id, alert_type, message)
            VALUES (?, ?, ?)
        ''', (source_id, alert_type, message))
        
        alert_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return alert_id
    
    def check_duplicate(self, content_hash):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id FROM clean_docs WHERE content_hash = ?
        ''', (content_hash,))
        
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def get_stats(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        cursor.execute('SELECT COUNT(*) FROM companies')
        stats['companies'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM sources')
        stats['sources'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT source_type, COUNT(*) FROM sources GROUP BY source_type')
        stats['sources_by_type'] = dict(cursor.fetchall())
        
        cursor.execute('SELECT COUNT(*) FROM raw_docs')
        stats['raw_docs'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM clean_docs')
        stats['clean_docs'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM facts')
        stats['facts'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT fact_type, COUNT(*) FROM facts GROUP BY fact_type')
        stats['facts_by_type'] = dict(cursor.fetchall())
        
        cursor.execute('SELECT COUNT(*) FROM alerts WHERE is_resolved = 0')
        stats['active_alerts'] = cursor.fetchone()[0]
        
        conn.close()
        return stats