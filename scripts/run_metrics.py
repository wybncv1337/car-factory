#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from pathlib import Path
import json
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    print("=" * 60)
    print("РАСЧЕТ МЕТРИК")
    print("=" * 60)

    print("\n[1/3] Загрузка данных из базы данных...")

    import sqlite3
    db_path = 'car_factory.db'

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Считаем статистику
        cursor.execute("SELECT COUNT(*) FROM raw_docs")
        total_docs = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM facts WHERE type = 'vacancy'")
        total_vacancies = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM facts WHERE type = 'release'")
        total_releases = cursor.fetchone()[0]

        conn.close()

        print(f"\n[2/3] Результаты:")
        print(f"   Всего документов: {total_docs}")
        print(f"   Всего вакансий: {total_vacancies}")
        print(f"   Всего релизов: {total_releases}")

        # Сохраняем отчет
        report = {
            'generated_at': datetime.now().isoformat(),
            'news_tempo': {'total': total_docs},
            'hiring_activity': {'total_vacancies': total_vacancies},
            'product_changes': {'total_releases': total_releases}
        }

        results_dir = Path('results')
        results_dir.mkdir(exist_ok=True)

        output_file = results_dir / f"metrics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n[3/3] Отчет сохранен: {output_file}")
        print(f"\n[OK] Готово!")

    except Exception as e:
        print(f"[ERROR] {e}")
        return False

    return True


if __name__ == "__main__":
    main()