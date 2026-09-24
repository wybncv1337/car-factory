import sqlite3

conn = sqlite3.connect('car_factory.db')
cur = conn.cursor()

print("=" * 60)
print("ИСПРАВЛЕНИЕ ТИПОВ ФАКТОВ")
print("=" * 60)

# Находим факты, которые ошибочно в релизах, но содержат признаки цены
cur.execute('''
    SELECT id, fact_data FROM facts 
    WHERE type = 'release' 
    AND (
        LOWER(fact_data) LIKE '%pricing%' 
        OR LOWER(fact_data) LIKE '%price%'
        OR LOWER(fact_data) LIKE '%цена%'
        OR LOWER(fact_data) LIKE '%стоимость%'
        OR LOWER(fact_data) LIKE '%msrp%'
        OR LOWER(fact_data) LIKE '%cost%'
    )
''')

wrong_facts = cur.fetchall()
print(f"\nНайдено фактов с признаками цены в релизах: {len(wrong_facts)}")

for fact_id, fact_data in wrong_facts:
    cur.execute('UPDATE facts SET type = ? WHERE id = ?', ('price', fact_id))
    print(f"  ✅ Факт {fact_id} перемещён в 'price'")

# Обратная проверка — факты-цены с признаками релиза
cur.execute('''
    SELECT id, fact_data FROM facts 
    WHERE type = 'price' 
    AND (
        LOWER(fact_data) LIKE '%release%'
        OR LOWER(fact_data) LIKE '%launch%'
        OR LOWER(fact_data) LIKE '%unveil%'
    )
''')

wrong_releases = cur.fetchall()
print(f"\nНайдено фактов с признаками релиза в ценах: {len(wrong_releases)}")

for fact_id, fact_data in wrong_releases:
    cur.execute('UPDATE facts SET type = ? WHERE id = ?', ('release', fact_id))
    print(f"  ✅ Факт {fact_id} перемещён в 'release'")

conn.commit()

# Итоговая статистика
cur.execute("SELECT type, COUNT(*) FROM facts GROUP BY type")
print("\n📊 Итоговая статистика по типам:")
for row in cur.fetchall():
    print(f"   {row[0]}: {row[1]}")

conn.close()
print("\n✅ Готово!")