#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from pathlib import Path
import sqlite3
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    print("=" * 60)
    print("УПРАВЛЕНИЕ АЛЕРТАМИ")
    print("=" * 60)

    db_path = 'car_factory.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    while True:
        print("\nВыберите действие:")
        print("1. Создать алерт")
        print("2. Показать все алерты")
        print("3. Проверить алерты")
        print("4. Удалить алерт")
        print("0. Назад")

        choice = input("\nВаш выбор: ").strip()

        if choice == '1':
            name = input("Название алерта: ").strip()
            company = input("Компания (Enter для пропуска): ").strip() or None
            alert_type = input("Тип (vacancy/release/price, Enter для пропуска): ").strip() or None
            keywords = input("Ключевые слова (через запятую, Enter для пропуска): ").strip() or None
            language = input("Язык (ru/en/any): ").strip() or 'any'

            cursor.execute('''
                           INSERT INTO alerts (name, company, alert_type, keywords, language, created_at)
                           VALUES (?, ?, ?, ?, ?, ?)
                           ''', (name, company, alert_type, keywords, language, datetime.now()))

            conn.commit()
            print(f"\n[OK] Алерт '{name}' создан!")

        elif choice == '2':
            cursor.execute('SELECT id, name, company, alert_type, keywords, language, is_active FROM alerts')
            rows = cursor.fetchall()

            if not rows:
                print("\n   Нет активных алертов")
            else:
                print("\nСписок алертов:")
                print("-" * 50)
                for row in rows:
                    status = "ACTIVE" if row[6] else "INACTIVE"
                    print(f"  [{row[0]}] {row[1]} ({status})")
                    if row[2]: print(f"      Компания: {row[2]}")
                    if row[3]: print(f"      Тип: {row[3]}")
                    if row[4]: print(f"      Ключевые слова: {row[4]}")

        elif choice == '3':
            print("\nПроверка алертов на новых документах...")

            cursor.execute('''
                           SELECT id, clean_content
                           FROM clean_docs
                           WHERE clean_content IS NOT NULL
                           ORDER BY id DESC LIMIT 10
                           ''')

            docs = cursor.fetchall()
            triggers_found = 0

            for doc_id, content in docs:
                if content:
                    cursor.execute(
                        'SELECT id, name, company, alert_type, keywords, language FROM alerts WHERE is_active = 1')
                    alerts = cursor.fetchall()

                    for alert in alerts:
                        alert_id, name, company, alert_type, keywords, language = alert
                        matched = False

                        if company and company.lower() not in content.lower():
                            continue

                        if keywords:
                            kw_list = [k.strip().lower() for k in keywords.split(',')]
                            if not any(kw in content.lower() for kw in kw_list):
                                continue

                        matched = True

                        if matched:
                            cursor.execute('''
                                           INSERT INTO alert_triggers (alert_id, matched_doc_id, matched_text, triggered_at)
                                           VALUES (?, ?, ?, ?)
                                           ''', (alert_id, doc_id, content[:200], datetime.now()))
                            triggers_found += 1
                            print(f"   [TRIGGER] Алерт '{name}' сработал на документе {doc_id}")

            conn.commit()
            print(f"\n[OK] Найдено срабатываний: {triggers_found}")

        elif choice == '4':
            alert_id = input("ID алерта для удаления: ").strip()
            cursor.execute('DELETE FROM alerts WHERE id = ?', (alert_id,))
            conn.commit()
            print(f"[OK] Алерт {alert_id} удален")

        elif choice == '0':
            break

        else:
            print("[ERROR] Неверный выбор")

    conn.close()


if __name__ == "__main__":
    main()