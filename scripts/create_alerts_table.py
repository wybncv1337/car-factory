import sqlite3


def create_alerts_table():
    conn = sqlite3.connect('car_factory.db')
    cursor = conn.cursor()

    # Таблица для алертов
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS alerts
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       name
                       TEXT
                       NOT
                       NULL,
                       company
                       TEXT,
                       alert_type
                       TEXT,
                       keywords
                       TEXT,
                       language
                       TEXT,
                       frequency
                       TEXT
                       DEFAULT
                       'daily',
                       is_active
                       INTEGER
                       DEFAULT
                       1,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP,
                       last_triggered_at
                       TIMESTAMP,
                       user_id
                       TEXT
                       DEFAULT
                       'default'
                   )
                   ''')

    # Таблица для истории срабатываний
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

    # Таблица для пользователей (простая)
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS users
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       username
                       TEXT
                       UNIQUE,
                       telegram_id
                       TEXT,
                       email
                       TEXT,
                       notify_method
                       TEXT
                       DEFAULT
                       'console'
                   )
                   ''')

    conn.commit()
    conn.close()
    print("✅ Таблицы для алертов созданы")


if __name__ == "__main__":
    create_alerts_table()