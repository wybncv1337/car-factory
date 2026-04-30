#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from pathlib import Path


def view_results():
    print("=" * 70)
    print("ПРОСМОТР РЕЗУЛЬТАТОВ МОК-РЕЖИМА")
    print("=" * 70)

    # Ищем последний файл с результатами
    results_dir = Path('results')
    if not results_dir.exists():
        print("❌ Папка results не найдена")
        return

    # Находим все JSON файлы
    json_files = list(results_dir.glob('llm_extraction_*.json'))

    if not json_files:
        print("❌ Файлы с результатами не найдены")
        print("   (Мок-режим не сохранил результаты, только показал, что обработал)")
        return

    # Берем самый свежий файл
    latest_file = max(json_files, key=lambda f: f.stat().st_mtime)

    print(f"\n📁 Файл результатов: {latest_file}")
    print(f"📏 Размер: {latest_file.stat().st_size} байт")

    with open(latest_file, 'r', encoding='utf-8') as f:
        results = json.load(f)

    print(f"\n📊 Количество результатов: {len(results)}")

    # Показываем первые 2 результата
    for i, result in enumerate(results[:2]):
        print(f"\n🔍 Результат {i + 1}:")
        print(json.dumps(result, ensure_ascii=False, indent=2)[:500])

    print("\n" + "=" * 70)


if __name__ == "__main__":
    view_results()