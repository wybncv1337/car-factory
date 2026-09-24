import sqlite3
from datetime import datetime, timedelta
import random

conn = sqlite3.connect('car_factory.db')
cur = conn.cursor()

# Получаем все факты
cur.execute('SELECT id FROM facts')
ids = [row[0] for row in cur.fetchall()]

print(f'📊 Найдено фактов: {len(ids)}')

# Раскидываем по датам за последние 90 дней
for fact_id in ids:
    days_ago = random.randint(0, 90)
    new_date = (datetime.now() - timedelta(days=days_ago)).isoformat()
    cur.execute('UPDATE facts SET created_at = ? WHERE id = ?', (new_date, fact_id))

conn.commit()
conn.close()

print(f'✅ Обновлено {len(ids)} фактов')
print('Теперь даты распределены равномерно за последние 90 дней')