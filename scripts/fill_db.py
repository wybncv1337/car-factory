import sqlite3
import json
from datetime import datetime, timedelta
import random


def fill_database():
    print("Заполняю базу данных тестовыми данными...")

    conn = sqlite3.connect('car_factory.db')
    cursor = conn.cursor()

    # Тестовые данные
    test_data = [
        # Вакансии
        ('vacancy',
         '{"value": "Открыта вакансия инженера в Tesla", "position": "Engineer", "salary": 150000, "company": "Tesla"}'),
        ('vacancy',
         '{"value": "Требуется Python разработчик в Яндекс", "position": "Python Dev", "salary": 200000, "company": "Yandex"}'),
        ('vacancy',
         '{"value": "Hiring Software Engineer at Google", "position": "SWE", "salary": 150000, "company": "Google"}'),
        ('vacancy',
         '{"value": "Вакансия: Data Scientist в Сбере", "position": "Data Scientist", "salary": 180000, "company": "Sber"}'),
        ('vacancy',
         '{"value": "BMW seeks Senior Java Developer", "position": "Java Dev", "salary": 140000, "company": "BMW"}'),
        ('vacancy',
         '{"value": "Tesla hiring Autopilot Engineer", "position": "Autopilot Engineer", "salary": 180000, "company": "Tesla"}'),
        ('vacancy',
         '{"value": "Toyota открывает вакансию механика", "position": "Mechanic", "salary": 90000, "company": "Toyota"}'),

        # Релизы
        ('release',
         '{"value": "Tesla выпустила новую модель Model 3", "model": "Model 3", "year": 2024, "company": "Tesla"}'),
        ('release',
         '{"value": "Toyota представила новую Camry 2024", "model": "Camry", "year": 2024, "company": "Toyota"}'),
        ('release', '{"value": "BMW launches new iX5 electric SUV", "model": "iX5", "year": 2024, "company": "BMW"}'),
        ('release',
         '{"value": "Mercedes-Benz reveals new E-Class", "model": "E-Class", "year": 2024, "company": "Mercedes"}'),
        ('release',
         '{"value": "Kia представляет обновленный Sportage", "model": "Sportage", "year": 2024, "company": "Kia"}'),
        ('release',
         '{"value": "Tesla announces Cybertruck release date", "model": "Cybertruck", "year": 2024, "company": "Tesla"}'),
        ('release', '{"value": "BMW i5 electric sedan unveiled", "model": "i5", "year": 2024, "company": "BMW"}'),

        # Цены
        ('price',
         '{"value": "Цена Tesla Model 3 - 3.5 млн руб.", "amount": 3500000, "currency": "RUB", "company": "Tesla"}'),
        ('price', '{"value": "Price: $45,000 for new BMW iX5", "amount": 45000, "currency": "USD", "company": "BMW"}'),
        ('price',
         '{"value": "Стоимость Toyota Camry от 2.8 млн руб.", "amount": 2800000, "currency": "RUB", "company": "Toyota"}'),
        ('price',
         '{"value": "Mercedes E-Class starts at €50,000", "amount": 50000, "currency": "EUR", "company": "Mercedes"}'),
        ('price',
         '{"value": "Kia Sportage цена от 2.5 млн руб.", "amount": 2500000, "currency": "RUB", "company": "Kia"}'),
        ('price',
         '{"value": "Tesla Model Y price reduced to $44,000", "amount": 44000, "currency": "USD", "company": "Tesla"}'),
        ('price', '{"value": "BMW X5 price starts at $62,000", "amount": 62000, "currency": "USD", "company": "BMW"}'),
    ]

    now = datetime.now()

    for i, (fact_type, fact_data) in enumerate(test_data):
        # Случайная дата за последние 30 дней
        days_ago = random.randint(0, 30)
        created_at = (now - timedelta(days=days_ago)).isoformat()

        # raw_docs
        cursor.execute('''
                       INSERT INTO raw_docs (source_url, raw_content, created_at)
                       VALUES (?, ?, ?)
                       ''', (f"https://example.com/news_{i}.html", fact_data, created_at))
        raw_id = cursor.lastrowid

        # clean_docs
        cursor.execute('''
                       INSERT INTO clean_docs (raw_doc_id, clean_content, created_at)
                       VALUES (?, ?, ?)
                       ''', (raw_id, fact_data, created_at))
        clean_id = cursor.lastrowid

        # facts
        cursor.execute('''
                       INSERT INTO facts (clean_doc_id, type, fact_data, confidence, created_at)
                       VALUES (?, ?, ?, ?, ?)
                       ''', (clean_id, fact_type, fact_data, 0.95, created_at))

    # Добавляем алерты
    alerts = [
        ('Tesla вакансии', 'Tesla', 'vacancy', 'engineer,hiring', 'en', 1),
        ('BMW новинки', 'BMW', 'release', 'new,launch,unveils', 'en', 1),
        ('Новые цены', None, 'price', 'цена,стоимость,руб', 'ru', 1),
        ('Toyota обновления', 'Toyota', 'release', 'new,camry,hybrid', 'en', 1),
        ('Все вакансии', None, 'vacancy', 'developer,engineer,scientist', 'en', 1),
    ]

    for name, company, alert_type, keywords, language, is_active in alerts:
        cursor.execute('''
                       INSERT INTO alerts (name, company, alert_type, keywords, language, is_active, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)
                       ''', (name, company, alert_type, keywords, language, is_active, now.isoformat()))

    # Добавляем несколько срабатываний алертов
    cursor.execute("SELECT id FROM alerts")
    alert_ids = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT id, clean_content FROM clean_docs LIMIT 10")
    docs = cursor.fetchall()

    for alert_id in alert_ids[:3]:
        for doc_id, content in docs[:5]:
            cursor.execute('''
                           INSERT INTO alert_triggers (alert_id, matched_doc_id, matched_text, triggered_at)
                           VALUES (?, ?, ?, ?)
                           ''',
                           (alert_id, doc_id, content[:200], (now - timedelta(days=random.randint(0, 7))).isoformat()))

    conn.commit()
    conn.close()

    print(f"✅ Добавлено {len(test_data)} фактов")
    print(f"✅ Добавлено {len(alerts)} алертов")
    print("База данных успешно заполнена!")


if __name__ == "__main__":
    fill_database()