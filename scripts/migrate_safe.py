import sqlite3
import psycopg2

DATABASE_URL = "postgresql://car_user:EkK5vPD2thBrZvCGCjTzioFfQa9nRwYZ@dpg-d8aivfeq1p3s73dlc7d0-a.frankfurt-postgres.render.com/car_factory"

print("1️⃣ Подключаюсь к PostgreSQL...")
try:
    pg_conn = psycopg2.connect(DATABASE_URL)
    pg_cur = pg_conn.cursor()
    print("   ✅ Подключено")
except Exception as e:
    print(f"   ❌ Ошибка подключения: {e}")
    exit(1)

pg_cur.execute("DROP TABLE IF EXISTS facts")
pg_cur.execute("""
    CREATE TABLE facts (
        id SERIAL PRIMARY KEY,
        type TEXT,
        fact_data TEXT,
        confidence REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
print("   ✅ Таблица создана")

print("2️⃣ Читаю локальную БД...")
local_conn = sqlite3.connect('car_factory.db')
local_cur = local_conn.cursor()
local_cur.execute("SELECT type, fact_data, confidence, created_at FROM facts")
rows = local_cur.fetchall()
print(f"   📊 Найдено фактов: {len(rows)}")

if len(rows) == 0:
    print("   ⚠️ ВНИМАНИЕ: локальная БД пустая!")
    print("   Сначала запусти: python main.py (пункт 4)")
    exit(1)

print("3️⃣ Переношу данные...")
for row in rows:
    pg_cur.execute("""
        INSERT INTO facts (type, fact_data, confidence, created_at)
        VALUES (%s, %s, %s, %s)
    """, row)

pg_conn.commit()

print("4️⃣ Проверяю...")
pg_cur.execute("SELECT COUNT(*) FROM facts")
count = pg_cur.fetchone()[0]
print(f"   ✅ В PostgreSQL теперь {count} фактов")

pg_cur.close()
pg_conn.close()
local_conn.close()
print("🎉 Готово!")