import psycopg2


DATABASE_URL = "postgresql://car_user:Ekk5vPD2thBrZvCGCjTzioFfQa9nRwYZ@dpg-d8aivfeqlp3s73dlc7d0-a.frankfurt-postgres.render.com/car_factory?sslmode=require"

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute("""
                CREATE TABLE IF NOT EXISTS facts
                (
                    id
                    SERIAL
                    PRIMARY
                    KEY,
                    type
                    TEXT,
                    fact_data
                    TEXT,
                    confidence
                    REAL,
                    created_at
                    TIMESTAMP
                    DEFAULT
                    CURRENT_TIMESTAMP
                )
                """)
    conn.commit()
    print("✅ Таблица создана")

    cur.close()
    conn.close()

except Exception as e:
    print(f"❌ Ошибка: {e}")