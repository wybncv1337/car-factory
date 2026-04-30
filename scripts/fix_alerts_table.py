import sqlite3


def fix_alerts_table():
    conn = sqlite3.connect('car_factory.db')
    cursor = conn.cursor()

    # Проверяем текущую структуру
    cursor.execute("PRAGMA table_info(alerts)")
    columns = cursor.fetchall()

    print("📋 Текущая структура таблицы alerts:")
    for col in columns:
        print(f"   - {col[1]} ({col[2]})")

    # Пересоздаем таблицу с правильной структурой
    print("\n🔄 Пересоздаем таблицу alerts...")

    # Удаляем старую таблицу
    cursor.execute("DROP TABLE IF EXISTS alerts")

    # Создаем новую с правильными колонками
    cursor.execute('''
                   CREATE TABLE alerts
                   (
                       id                INTEGER PRIMARY KEY AUTOINCREMENT,
                       name              TEXT NOT NULL,
                       company           TEXT,
                       alert_type        TEXT,
                       keywords          TEXT,
                       language          TEXT      DEFAULT 'any',
                       frequency         TEXT      DEFAULT 'daily',
                       is_active         INTEGER   DEFAULT 1,
                       created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                       last_triggered_at TIMESTAMP,
                       user_id           TEXT      DEFAULT 'default'
                   )
                   ''')

    # Создаем таблицу для истории (если нет)
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS alert_triggers
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       alert_id
                       INTEGER,
                       matched_doc_id
                       INTEGER,
                       matched_text
                       TEXT,
                       matched_by
                       TEXT,
                       triggered_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP,
                       FOREIGN
                       KEY
                   (
                       alert_id
                   ) REFERENCES alerts
                   (
                       id
                   )
                       )
                   ''')

    conn.commit()
    conn.close()

    print("✅ Таблицы пересозданы с правильной структурой")


if __name__ == "__main__":
    fix_alerts_table()