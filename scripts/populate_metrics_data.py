#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import json
from datetime import datetime, timedelta
import random


def populate_metrics_data():
    print("=" * 60)
    print("ЗАПОЛНЕНИЕ ТЕСТОВЫМИ ДАННЫМИ ДЛЯ МЕТРИК")
    print("=" * 60)

    db_path = 'car_factory.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Проверяем, есть ли уже данные
    cursor.execute("SELECT COUNT(*) FROM raw_docs")
    count = cursor.fetchone()[0]

    if count > 50:
        print(f"[OK] В БД уже есть {count} записей")
        conn.close()
        return True

    print("[1/3] Создаю тестовые данные...")

    start_date = datetime.now() - timedelta(days=90)

    vacancies_list = [
        "Открыта вакансия инженера-конструктора. Зарплата от 150000 руб.",
        "Требуется Python разработчик. Зарплата 200000 руб.",
        "Ищем DevOps инженера. Опыт от 3 лет. Зарплата 180000 руб.",
        "Вакансия: Project Manager. Зарплата 180000 руб.",
        "Hiring Software Engineer. Salary $120,000 per year.",
        "Job opening: Data Scientist. Salary $130,000 per year.",
        "Вакансия: Тестировщик. Зарплата 120000 руб.",
        "Senior Java Developer needed. Salary $140,000."
    ]

    releases_list = [
        "Компания выпустит новую модель в мае 2024 года.",
        "Tesla announces new Model 3 release on June 15, 2024.",
        "Toyota представила обновленную Camry 2024.",
        "BMW launches new electric SUV model iX5.",
        "Mercedes-Benz reveals new E-Class Estate.",
        "Kia представляет обновленный Sportage 2024."
    ]

    prices_list = [
        "Цена новой модели составит 2.5 млн рублей.",
        "Price starts at $45,000.",
        "Стоимость базовой комплектации - 1.8 млн руб.",
        "Top trim level costs EUR 50,000.",
        "Цена от 3 500 000 рублей.",
        "Starting at $35,000."
    ]

    all_texts = []

    for i in range(100):
        days_ago = random.randint(0, 90)
        created_at = (start_date + timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')

        doc_type = random.choice(['vacancy', 'release', 'price'])

        if doc_type == 'vacancy':
            text = random.choice(vacancies_list)
            fact_type = 'vacancy'
        elif doc_type == 'release':
            text = random.choice(releases_list)
            fact_type = 'release'
        else:
            text = random.choice(prices_list)
            fact_type = 'price'

        all_texts.append({
            'text': text,
            'created_at': created_at,
            'type': fact_type,
            'source': f"test_{i}.txt"
        })

    print("[2/3] Сохраняю в базу данных...")

    for item in all_texts:
        cursor.execute('''
                       INSERT INTO raw_docs (source_url, raw_content, created_at)
                       VALUES (?, ?, ?)
                       ''', (item['source'], item['text'], item['created_at']))

        raw_doc_id = cursor.lastrowid

        cursor.execute('''
                       INSERT INTO clean_docs (raw_doc_id, clean_content, created_at)
                       VALUES (?, ?, ?)
                       ''', (raw_doc_id, item['text'], item['created_at']))

        clean_doc_id = cursor.lastrowid

        fact_data = json.dumps({"value": item['text'], "type": item['type']}, ensure_ascii=False)
        cursor.execute('''
                       INSERT INTO facts (clean_doc_id, type, fact_data, confidence, created_at)
                       VALUES (?, ?, ?, ?, ?)
                       ''', (clean_doc_id, item['type'], fact_data, 0.9, item['created_at']))

    conn.commit()
    conn.close()

    print(f"[3/3] ГОТОВО! Создано {len(all_texts)} тестовых документов")
    return True


if __name__ == "__main__":
    populate_metrics_data()