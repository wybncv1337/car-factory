#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import hashlib


def create_deduplicated_db():
    print("=" * 60)
    print("🔄 СОЗДАНИЕ ЧИСТОЙ БД С ЗАЩИТОЙ ОТ ДУБЛИКАТОВ")
    print("=" * 60)

    # Подключаемся к БД
    conn = sqlite3.connect('car_factory.db')
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
                       content_hash
                       TEXT
                       UNIQUE,
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
                       content_hash
                       TEXT
                       UNIQUE,
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
                       data_hash
                       TEXT
                       UNIQUE,
                       confidence
                       REAL,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   ''')

    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS sources
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       name
                       TEXT,
                       url
                       TEXT
                       UNIQUE,
                       source_type
                       TEXT,
                       is_active
                       INTEGER
                       DEFAULT
                       1,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   ''')

    conn.commit()

    sources = [
        ('АвтоВАЗ (Lada)', 'https://www.lada.ru/press', 'html'),
        ('Drive.ru', 'https://www.drive.ru/news/', 'html'),
        ('Auto.ru', 'https://www.auto.ru/news/', 'html'),
    ]

    for name, url, source_type in sources:
        try:
            cursor.execute('''
                           INSERT INTO sources (name, url, source_type)
                           VALUES (?, ?, ?)
                           ''', (name, url, source_type))
        except sqlite3.IntegrityError:
            print(f"   ⏭️ Источник {name} уже существует")

    conn.commit()
    conn.close()

    print("✅ Создана чистая БД с защитой от дубликатов")


if __name__ == "__main__":
    create_deduplicated_db()