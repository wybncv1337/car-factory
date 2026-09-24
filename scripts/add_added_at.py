import sqlite3

conn = sqlite3.connect('car_factory.db')
cur = conn.cursor()

# Добавляем колонку added_at
try:
    cur.execute('ALTER TABLE facts ADD COLUMN added_at TIMESTAMP')
    print('✅ Колонка added_at добавлена')
except sqlite3.OperationalError:
    print('⚠️ Колонка уже существует')

# Заполняем added_at текущим временем
cur.execute("UPDATE facts SET added_at = datetime('now') WHERE added_at IS NULL")
conn.commit()

cur.execute('SELECT COUNT(*) FROM facts')
print(f'✅ Обработано фактов: {cur.fetchone()[0]}')

conn.close()
