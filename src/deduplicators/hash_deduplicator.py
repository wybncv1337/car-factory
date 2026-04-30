import hashlib
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.database.db_manager import DatabaseManager
from src.cleaners.html_cleaner import HTMLCleaner

class HashDeduplicator:
    def __init__(self, db_path='car_factory.db'):
        self.db = DatabaseManager(db_path)
        self.cleaner = HTMLCleaner()
    
    def process_document(self, raw_doc_id, raw_content, source_id):
        """Обработать документ: очистить и проверить дубликат"""
        
        clean_text, text_hash = self.cleaner.clean_file(raw_content)
        
        is_duplicate = self.db.check_duplicate(text_hash)
        
        if is_duplicate:
            self.db.add_alert(source_id, 'duplicate', f'Найден дубликат с хэшем {text_hash[:16]}')
            print(f"  🔴 Дубликат (хэш: {text_hash[:16]}...)")
            return None
        else:
            clean_doc_id = self.db.save_clean_doc(raw_doc_id, clean_text, text_hash)
            print(f"  🟢 Уникальный документ (хэш: {text_hash[:16]}...)")
            return clean_doc_id
    
    def process_all_raw(self):
        """Обработать все необработанные raw_docs"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.id, r.raw_content, r.source_id
            FROM raw_docs r
            LEFT JOIN clean_docs c ON r.id = c.raw_doc_id
            WHERE c.id IS NULL
        ''')
        
        raw_docs = cursor.fetchall()
        conn.close()
        
        print(f"\n🔍 Найдено необработанных документов: {len(raw_docs)}")
        
        results = []
        for raw_id, raw_content, source_id in raw_docs:
            clean_id = self.process_document(raw_id, raw_content, source_id)
            if clean_id:
                results.append(clean_id)
        
        print(f"\n✅ Обработано: {len(results)} новых уникальных документов")
        return results