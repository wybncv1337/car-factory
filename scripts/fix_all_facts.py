import sqlite3
import json
import re

conn = sqlite3.connect('car_factory.db')
cur = conn.cursor()

print("=" * 60)
print("ПОЛНАЯ ОЧИСТКА И ИСПРАВЛЕНИЕ ФАКТОВ")
print("=" * 60)

# ==================== ШАГ 1: Удаляем дубликаты ====================
print("\n[1/4] Удаление дубликатов...")

cur.execute('''
            DELETE
            FROM facts
            WHERE id NOT IN (SELECT MIN(id)
                             FROM facts
                             GROUP BY fact_data)
            ''')
print(f"   ✅ Удалено дубликатов: {cur.rowcount}")

# ==================== ШАГ 2: Исправляем обрезанный текст ====================
print("\n[2/4] Исправление обрезанного текста...")

cur.execute("SELECT id, fact_data FROM facts")
rows = cur.fetchall()

fixed = 0
for fact_id, fact_data in rows:
    try:
        data = json.loads(fact_data)
        value = data.get('value', '')

        # Если текст начинается с цифры-обрывка (например "3 release")
        # ищем полный контекст
        if re.match(r'^\d+\s+(release|model|price|new)', value, re.IGNORECASE):
            # Пытаемся найти более полный текст
            if 'model' in value.lower() and not value.lower().startswith('model'):
                # "3 release on June 15" → "Model 3 release on June 15"
                value = 'Model ' + value
                data['value'] = value
                cur.execute('UPDATE facts SET fact_data = ? WHERE id = ?',
                            (json.dumps(data, ensure_ascii=False), fact_id))
                fixed += 1
    except:
        pass

print(f"   ✅ Исправлено: {fixed}")

# ==================== ШАГ 3: Удаляем мусор ====================
print("\n[3/4] Удаление мусорных фактов...")

# Получаем все факты
cur.execute("SELECT id, type, fact_data FROM facts")
rows = cur.fetchall()

removed = 0
for fact_id, fact_type, fact_data in rows:
    try:
        data = json.loads(fact_data)
        text = str(data.get('value', ''))
    except:
        text = str(fact_data)

    text_lower = text.lower()

    # Проверка на мусор
    is_garbage = (
            len(text) < 20
            or text.count('<') > 0
            or text.count('{') > 0
            or 'photo' in text_lower
            or 'sales sales' in text_lower
            or re.match(r'^[a-z\s]{5,30}$', text_lower)  # Только строчные буквы
            or 'data photos' in text_lower
            or 'stories behind' in text_lower
    )

    if is_garbage:
        cur.execute("DELETE FROM facts WHERE id = ?", (fact_id,))
        removed += 1

print(f"   ✅ Удалено мусора: {removed}")

# ==================== ШАГ 4: Статистика ====================
print("\n[4/4] Итоговая статистика...")

cur.execute("SELECT type, COUNT(*) FROM facts GROUP BY type")
for row in cur.fetchall():
    print(f"   {row[0]}: {row[1]}")

cur.execute("SELECT COUNT(*) FROM facts")
total = cur.fetchone()[0]
print(f"\n   Всего фактов: {total}")

conn.commit()
conn.close()
print("\n✅ Готово!")