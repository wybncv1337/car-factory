#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для запуска LLM-извлечения фактов
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


def extract_mock(text: str, source: str = "") -> dict:
    """Мок-режим для тестирования без API"""
    is_russian = any(c in text.lower() for c in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя')

    result = {
        "vacancies": [],
        "prices": [],
        "releases": [],
        "language": "ru" if is_russian else "en",
        "_metadata": {
            "source": source,
            "extracted_at": datetime.now().isoformat(),
            "model": "mock",
            "text_length": len(text)
        }
    }

    # Поиск вакансий
    if any(kw in text.lower() for kw in ['ваканс', 'hire', 'job', 'salary', 'зарплат', 'требуется']):
        result["vacancies"].append({
            "position": "Инженер-программист" if is_russian else "Software Engineer",
            "requirements": "Python, опыт работы от 3 лет" if is_russian else "Python, 3+ years experience",
            "salary": 150000 if is_russian else 120000,
            "currency": "RUB" if is_russian else "USD",
            "location": "Москва" if is_russian else "Remote"
        })

    # Поиск цен
    if any(kw in text.lower() for kw in ['цена', 'price', 'стоимост', 'руб', '$', '€']):
        result["prices"].append({
            "amount": 2500000 if is_russian else 45000,
            "currency": "RUB" if is_russian else "USD",
            "item": "Новая модель" if is_russian else "New model",
            "condition": "new"
        })

    # Поиск релизов
    if any(kw in text.lower() for kw in ['выпуст', 'release', 'новая модель', 'new model']):
        result["releases"].append({
            "model": "Новая модель 2024" if is_russian else "New Model 2024",
            "release_date": "2024-05-15",
            "specifications": "электрический, автопилот" if is_russian else "electric, autonomous"
        })

    return result


def load_texts_from_db(limit: int = None):
    """Загружает тексты из базы данных"""
    try:
        import sqlite3
        conn = sqlite3.connect('car_factory.db')
        cursor = conn.cursor()

        cursor.execute('''
                       SELECT id, clean_content, raw_doc_id
                       FROM clean_docs
                       WHERE clean_content IS NOT NULL
                         AND LENGTH(clean_content) > 100
                       ORDER BY id LIMIT ?
                       ''', (limit or 50,))

        docs = cursor.fetchall()
        conn.close()

        texts = []
        for doc_id, content, source in docs:
            if content:
                texts.append({
                    'text': content,
                    'source': f"doc_{doc_id}",
                    'doc_id': doc_id
                })

        print(f"  Загружено {len(texts)} документов из БД")
        return texts

    except Exception as e:
        print(f"  Ошибка при загрузке из БД: {e}")
        return []


def load_test_texts():
    """Загружает тестовые тексты"""
    test_texts = [
        "Компания выпустит новую модель 15 мая 2024 года. Цена: 2.5 млн руб.",
        "Tesla announces new Model 3 release on January 15, 2024. Price: $45,000.",
        "Открыта вакансия инженера с зарплатой от 150000 рублей в месяц.",
        "We are hiring a software engineer with salary $120,000 per year.",
    ]

    # Дублируем до 100
    while len(test_texts) < 100:
        test_texts.extend(test_texts[:100 - len(test_texts)])

    texts = [{'text': t, 'source': f'test_{i}.txt'} for i, t in enumerate(test_texts[:100])]
    print(f"  Создано {len(texts)} тестовых текстов")
    return texts


def main():
    print("=" * 60)
    print("LLM-ИЗВЛЕЧЕНИЕ ФАКТОВ")
    print("=" * 60)

    # Парсим аргументы командной строки
    source = 'test'  # по умолчанию
    limit = None

    if len(sys.argv) > 2:
        if sys.argv[1] == '--source':
            source = sys.argv[2]
        if len(sys.argv) > 3 and sys.argv[3] == '--limit':
            limit = int(sys.argv[4])

    print(f"\n[1/3] Загрузка текстов (источник: {source})...")

    if source == 'db':
        texts = load_texts_from_db(limit)
    elif source == 'folder':
        print("  Режим папки пока не реализован, использую тестовые данные")
        texts = load_test_texts()
    else:
        texts = load_test_texts()

    if not texts:
        print("  Нет текстов для обработки")
        return

    print(f"\n[2/3] Обработка {len(texts)} текстов...")

    results = []
    for i, item in enumerate(texts):
        text = item['text']
        source_name = item['source']

        print(f"  [{i + 1}/{len(texts)}] {source_name[:30]}...", end=' ')

        result = extract_mock(text, source_name)
        results.append(result)

        lang = result.get('language', 'unknown')
        vacancies = len(result.get('vacancies', []))
        prices = len(result.get('prices', []))
        releases = len(result.get('releases', []))
        print(f"OK (lang={lang}, v={vacancies}, p={prices}, r={releases})")

    print(f"\n[3/3] Сохранение результатов...")

    results_dir = Path('results')
    results_dir.mkdir(exist_ok=True)

    output_file = results_dir / f"llm_extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Результаты сохранены: {output_file}")
    print(f"[OK] Готово!")


if __name__ == "__main__":
    main()