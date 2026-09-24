import hashlib
import re
import sqlite3


class HashDeduplicator:
    def __init__(self, db_path='car_factory.db'):
        """
        Args:
            db_path: путь к файлу базы данных
        """
        self.db_path = db_path

    def clean_text(self, text):
        """Очистка текста от HTML и лишних пробелов"""
        if not text:
            return ""

        text = re.sub(r'<[^>]+>', ' ', text)
        # Удаляем лишние пробелы
        text = re.sub(r'\s+', ' ', text)
        # Удаляем пробелы в начале и конце
        text = text.strip()

        return text

    def get_hash(self, text):
        """Вычисляет хеш текста"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def process_all_raw(self):
        """Обрабатывает все сырые документы"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("PRAGMA table_info(clean_docs)")
            columns = [col[1] for col in cursor.fetchall()]

            if 'hash' not in columns:
                cursor.execute('ALTER TABLE clean_docs ADD COLUMN hash TEXT')
                print("   ✅ Добавлена колонка hash в clean_docs")

            cursor.execute('SELECT id, raw_content FROM raw_docs WHERE raw_content IS NOT NULL')
            rows = cursor.fetchall()

            print(f"\n🔄 Найдено документов для обработки: {len(rows)}")

            cleaned_count = 0
            duplicate_count = 0

            for row in rows:
                doc_id = row[0]
                raw_content = row[1]

                if raw_content:
                    clean_content = self.clean_text(raw_content)
                    hash_val = self.get_hash(clean_content)

                    cursor.execute('SELECT id FROM clean_docs WHERE hash = ?', (hash_val,))
                    if not cursor.fetchone():
                        cursor.execute('''
                                       INSERT INTO clean_docs (raw_doc_id, clean_content, hash)
                                       VALUES (?, ?, ?)
                                       ''', (doc_id, clean_content[:10000], hash_val))
                        cleaned_count += 1
                    else:
                        duplicate_count += 1

            conn.commit()
            print(f"✅ Уникальных документов: {cleaned_count}")
            print(f"⏭️ Дубликатов пропущено: {duplicate_count}")
            return True

        except Exception as e:
            print(f"❌ Ошибка в дедупликации: {e}")
            return False
        finally:
            conn.close()