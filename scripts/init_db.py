#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3


def init_db():
    print("ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ")

    db_path = 'car_factory.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS raw_docs
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       source_url
                       TEXT,
                       raw_content
                       TEXT,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   ''')

    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS clean_docs
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       raw_doc_id
                       INTEGER,
                       clean_content
                       TEXT,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   ''')

    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS facts
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       clean_doc_id
                       INTEGER,
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
                   ''')

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
                       TEXT
                       DEFAULT
                       'any',
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
                       CURRENT_TIMESTAMP
                   )
                   ''')

    conn.commit()
    conn.close()

    print("[OK] База данных инициализирована")
    return True


if __name__ == "__main__":
    init_db()