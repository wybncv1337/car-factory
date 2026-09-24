import sqlite3
import psycopg2
import os
import json

print("="*50)
print("ПЕРЕНОС РЕАЛЬНЫХ ДАННЫХ НА RENDER")
print("="*50)

print("\n[1/4] Чтение локальной БД...")
local_conn = sqlite3.connect('car_factory.db')
local_cur = local_conn.cursor()

local_cur.execute("SELECT COUNT(*) FROM facts")
count = local_cur.fetchone()[0]
print(f"  Найдено фактов: {count}")

if count == 0:
    print("❌ Нет данных в локальной БД! Сначала запустите python scripts/fill_db.py")
    exit(1)

print("\n[2/4] Подключение к PostgreSQL на Render...")
DATABASE_URL = input("Вставьте DATABASE_URL из Render: ").strip()

if not DATABASE_URL:
    print("❌ DATABASE_URL не введён!")
    exit(1)

pg_conn = psycopg2.connect(DATABASE_URL)
pg_cur = pg_conn.cursor()

print("\n[3/4] Перенос фактов...")

pg_cur.execute("DELETE FROM facts")
pg_cur.execute("DELETE FROM alerts")

local_cur.execute("SELECT type, fact_data, confidence, created_at FROM facts")
rows = local_cur.fetchall()

for row in rows:
    pg_cur.execute("""
        INSERT INTO facts (type, fact_data, confidence, created_at)
        VALUES (%s, %s, %s, %s)
    """, (row[0], row[1], row[2], row[3]))

try:
    local_cur.execute("SELECT name, company, alert_type, keywords, language, is_active, created_at FROM alerts")
    alerts = local_cur.fetchall()
    for alert in alerts:
        pg_cur.execute("""
            INSERT INTO alerts (name, company, alert_type, keywords, language, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, alert)
    print(f"  Перенесено алертов: {len(alerts)}")
except:
    print("  Алертов нет")

pg_conn.commit()

print("\n[4/4] Проверка...")
pg_cur.execute("SELECT COUNT(*) FROM facts")
new_count = pg_cur.fetchone()[0]
print(f"  Фактов в PostgreSQL: {new_count}")

pg_conn.close()
local_conn.close()

print("\n✅ ГОТОВО! Данные перенесены на Render")
print(f"   Перенесено фактов: {new_count}")