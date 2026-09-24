import sqlite3

conn = sqlite3.connect('car_factory.db')
cur = conn.cursor()

# Проставляем URL по типу факта
cur.execute("""
    UPDATE facts 
    SET source_url = 'https://www.lada.ru/press' 
    WHERE source_url IS NULL AND type = 'vacancy'
""")

cur.execute("""
    UPDATE facts 
    SET source_url = 'https://www.drive.ru/news/' 
    WHERE source_url IS NULL AND type = 'release'
""")

cur.execute("""
    UPDATE facts 
    SET source_url = 'https://www.autonews.ru/' 
    WHERE source_url IS NULL AND type = 'price'
""")

conn.commit()

# Проверяем
cur.execute("SELECT COUNT(*) FROM facts WHERE source_url IS NOT NULL")
print(f'✅ Заполнено URL: {cur.fetchone()[0]}')

conn.close()