import sqlite3
import json
import re

conn = sqlite3.connect('car_factory.db')
cur = conn.cursor()

print("=" * 60)
print("ОЧИСТКА МУСОРНЫХ ФАКТОВ")
print("=" * 60)

# Получаем все факты
cur.execute("SELECT id, type, fact_data FROM facts")
rows = cur.fetchall()

removed = 0
kept = 0

# Ключевые слова для валидных фактов
VALID_KEYWORDS = {
    'vacancy': ['вакансия', 'vacancy', 'hiring', 'job opening', 'position',
                'salary', 'зарплата', 'требуется', 'ищем', 'career', 'recruit'],
    'release': ['release', 'launch', 'new model', 'unveil', 'debut',
                'выпустила', 'представила', 'новая модель', 'announces',
                'introduces', 'presented'],
    'price': ['price', 'pricing', 'цена', 'стоимость', 'msrp', 'cost',
              'rub', 'usd', 'eur', '$', '€', '₽', 'руб', 'млн']
}

for fact_id, fact_type, fact_data in rows:
    try:
        data = json.loads(fact_data)
        text = str(data.get('value', ''))
    except:
        text = str(fact_data)

    text_lower = text.lower()

    # Проверяем:
    # 1. Есть ли ключевые слова для этого типа
    keywords = VALID_KEYWORDS.get(fact_type, [])
    has_keyword = any(kw in text_lower for kw in keywords)

    # 2. Есть ли признаки мусора
    is_garbage = (
            len(text) < 15  # Слишком короткий
            or text.count('<') > 0  # HTML-теги
            or text.count('{') > 0  # JSON-мусор
            or 'photo' in text_lower  # Фото-подписи
            or 'photo' in text_lower
            or re.match(r'^[a-z\s]+$', text_lower)  # Только строчные буквы (обрывок)
    )

    if has_keyword and not is_garbage:
        kept += 1
    else:
        cur.execute("DELETE FROM facts WHERE id = ?", (fact_id,))
        removed += 1

conn.commit()

# Итог
cur.execute("SELECT type, COUNT(*) FROM facts GROUP BY type")
print(f"\n✅ Удалено мусора: {removed}")
print(f"✅ Оставлено валидных: {kept}")
print(f"\n📊 Статистика по типам:")
for row in cur.fetchall():
    print(f"   {row[0]}: {row[1]}")

conn.close()