import sqlite3


def create_tables():
    print("Создаю таблицы в базе данных...")

    conn = sqlite3.connect('car_factory.db')
    cursor = conn.cursor()

    # Удаляем старые таблицы (если есть)
    cursor.execute("DROP TABLE IF EXISTS raw_docs")
    cursor.execute("DROP TABLE IF EXISTS clean_docs")
    cursor.execute("DROP TABLE IF EXISTS facts")
    cursor.execute("DROP TABLE IF EXISTS alerts")
    cursor.execute("DROP TABLE IF EXISTS alert_triggers")

    # Создаем таблицу raw_docs
    cursor.execute('''
                   CREATE TABLE raw_docs
                   (
                       id          INTEGER PRIMARY KEY AUTOINCREMENT,
                       source_url  TEXT,
                       raw_content TEXT,
                       created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )
                   ''')

    # Создаем таблицу clean_docs
    cursor.execute('''
                   CREATE TABLE clean_docs
                   (
                       id            INTEGER PRIMARY KEY AUTOINCREMENT,
                       raw_doc_id    INTEGER,
                       clean_content TEXT,
                       created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )
                   ''')

    # Создаем таблицу facts
    cursor.execute('''
                   CREATE TABLE facts
                   (
                       id           INTEGER PRIMARY KEY AUTOINCREMENT,
                       clean_doc_id INTEGER,
                       type         TEXT,
                       fact_data    TEXT,
                       confidence   REAL,
                       created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )
                   ''')

    # Создаем таблицу alerts
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

    # Создаем таблицу alert_triggers
    cursor.execute('''
                   CREATE TABLE alert_triggers
                   (
                       id             INTEGER PRIMARY KEY AUTOINCREMENT,
                       alert_id       INTEGER,
                       matched_doc_id INTEGER,
                       matched_text   TEXT,
                       matched_by     TEXT,
                       triggered_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )
                   ''')

    conn.commit()
    conn.close()

    print("✅ Таблицы успешно созданы!")


if __name__ == "__main__":
    create_tables()