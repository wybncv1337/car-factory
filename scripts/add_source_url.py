import sqlite3

conn = sqlite3.connect('car_factory.db')
cur = conn.cursor()

# Добавляем колонку source_url
try:
    cur.execute('ALTER TABLE facts ADD COLUMN source_url TEXT')
    print('✅ Колонка source_url добавлена')
except sqlite3.OperationalError:
    print('⚠️ Колонка уже существует')

conn.commit()
conn.close()
print('✅ Готово')