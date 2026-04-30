#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Единый скрипт для управления всем проектом
Запуск: python main.py
"""

import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
import os

sys.path.insert(0, str(Path(__file__).parent))


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_banner():
    banner = f"""
{Colors.CYAN}{'=' * 60}{Colors.RESET}
{Colors.BOLD}     CAR FACTORY ANALYTICS - Универсальный инструмент{Colors.RESET}
{Colors.CYAN}{'=' * 60}{Colors.RESET}
    """
    print(banner)


def print_menu():
    menu = f"""
{Colors.YELLOW}ГЛАВНОЕ МЕНЮ:{Colors.RESET}

{Colors.GREEN}1.{Colors.RESET} LLM-извлечение фактов (с кэшированием)
{Colors.GREEN}2.{Colors.RESET} Расчет метрик и графики
{Colors.GREEN}3.{Colors.RESET} Управление алертами
{Colors.GREEN}4.{Colors.RESET} ЗАПУСТИТЬ ВСЁ (полный пайплайн)
{Colors.GREEN}5.{Colors.RESET} Показать дашборд метрик
{Colors.GREEN}6.{Colors.RESET} Заполнить БД тестовыми данными
{Colors.GREEN}7.{Colors.RESET} Очистить кэш
{Colors.GREEN}8.{Colors.RESET} Статистика системы
{Colors.GREEN}0.{Colors.RESET} Выход

{Colors.CYAN}{'-' * 40}{Colors.RESET}
"""
    print(menu)


def run_command(cmd, description):
    print(f"\n{Colors.BLUE}>> {description}...{Colors.RESET}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"{Colors.GREEN}[OK] {description} завершен{Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}[ERROR] {result.stderr}{Colors.RESET}")
            return False
    except Exception as e:
        print(f"{Colors.RED}[ERROR] {e}{Colors.RESET}")
        return False


def init_db():
    """Инициализация БД"""
    print(f"\n{Colors.CYAN}{'=' * 50}{Colors.RESET}")
    print(f"{Colors.BOLD}ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 50}{Colors.RESET}")

    import sqlite3
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

    print(f"{Colors.GREEN}[OK] База данных инициализирована{Colors.RESET}")
    return True


def llm_extraction():
    print(f"\n{Colors.CYAN}{'=' * 50}{Colors.RESET}")
    print(f"{Colors.BOLD}LLM-ИЗВЛЕЧЕНИЕ ФАКТОВ{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 50}{Colors.RESET}")

    print("\nВыберите источник:")
    print("1. Из папки data/input")
    print("2. Из базы данных")
    print("3. Тест на 100 текстах")

    choice = input("\nВаш выбор (1-3): ").strip()

    if choice == '1':
        folder = input("Путь к папке (Enter = data/input): ").strip() or 'data/input'
        cmd = f"python scripts/run_llm_extractor.py --source folder --path {folder}"
    elif choice == '2':
        cmd = "python scripts/run_llm_extractor.py --source db"
    else:
        cmd = "python scripts/run_llm_extractor.py --source test"

    run_command(cmd, "LLM-извлечение")


def run_metrics():
    print(f"\n{Colors.CYAN}{'=' * 50}{Colors.RESET}")
    print(f"{Colors.BOLD}РАСЧЕТ МЕТРИК{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 50}{Colors.RESET}")

    run_command("python scripts/run_metrics.py", "Расчет метрик")
    show_dashboard()


def manage_alerts():
    print(f"\n{Colors.CYAN}{'=' * 50}{Colors.RESET}")
    print(f"{Colors.BOLD}УПРАВЛЕНИЕ АЛЕРТАМИ{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 50}{Colors.RESET}")

    run_command("python scripts/run_alerts.py", "Управление алертами")


def full_pipeline():
    print(f"\n{Colors.CYAN}{'=' * 50}{Colors.RESET}")
    print(f"{Colors.BOLD}ЗАПУСК ПОЛНОГО ПАЙПЛАЙНА{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 50}{Colors.RESET}")

    steps = [
        ("Инициализация БД", init_db),
        ("Заполнение тестовыми данными", populate_test_data),
        ("LLM-извлечение фактов",
         lambda: run_command("python scripts/run_llm_extractor.py --source test", "LLM-извлечение")),
        ("Расчет метрик", lambda: run_command("python scripts/run_metrics.py", "Расчет метрик")),
    ]

    for desc, func in steps:
        print(f"\n{Colors.BLUE}>> {desc}...{Colors.RESET}")
        if callable(func):
            if not func():
                print(f"{Colors.RED}[ERROR] Пайплайн остановлен на шаге: {desc}{Colors.RESET}")
                return

    print(f"\n{Colors.GREEN}{Colors.BOLD}[OK] ВЕСЬ ПАЙПЛАЙН УСПЕШНО ЗАВЕРШЕН!{Colors.RESET}")
    show_dashboard()


def show_dashboard():
    print(f"\n{Colors.CYAN}{'=' * 50}{Colors.RESET}")
    print(f"{Colors.BOLD}ДАШБОРД МЕТРИК{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 50}{Colors.RESET}")

    results_dir = Path('results')
    if results_dir.exists():
        reports = list(results_dir.glob('metrics_report_*.json'))
        if reports:
            latest = max(reports, key=lambda p: p.stat().st_mtime)
            with open(latest, 'r', encoding='utf-8') as f:
                data = json.load(f)

            print(f"\n[1] ТЕМП НОВОСТЕЙ:")
            news = data.get('news_tempo', {})
            print(f"    Всего документов: {news.get('total', 0)}")

            print(f"\n[2] АКТИВНОСТЬ НАЙМА:")
            hiring = data.get('hiring_activity', {})
            print(f"    Всего вакансий: {hiring.get('total_vacancies', 0)}")
            if hiring.get('avg_salary', 0) > 0:
                print(f"    Средняя зарплата: {hiring['avg_salary']:,.0f} руб.")

            print(f"\n[3] ПРОДУКТОВЫЕ ИЗМЕНЕНИЯ:")
            products = data.get('product_changes', {})
            print(f"    Всего релизов: {products.get('total_releases', 0)}")

            print(f"\n{Colors.GREEN}[OK] Отчет сохранен: {latest}{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}[WARN] Нет сохраненных отчетов. Сначала запустите расчет метрик.{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}[WARN] Папка results не найдена{Colors.RESET}")


def populate_test_data():
    print(f"\n{Colors.CYAN}{'=' * 50}{Colors.RESET}")
    print(f"{Colors.BOLD}ЗАПОЛНЕНИЕ ТЕСТОВЫМИ ДАННЫМИ{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 50}{Colors.RESET}")

    return run_command("python scripts/populate_metrics_data.py", "Создание тестовых данных")


def clear_cache():
    print(f"\n{Colors.CYAN}{'=' * 50}{Colors.RESET}")
    print(f"{Colors.BOLD}ОЧИСТКА КЭША{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 50}{Colors.RESET}")

    import shutil
    cache_dir = Path('cache')
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
        print(f"{Colors.GREEN}[OK] Кэш очищен{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}[WARN] Папка кэша не найдена{Colors.RESET}")


def show_stats():
    print(f"\n{Colors.CYAN}{'=' * 50}{Colors.RESET}")
    print(f"{Colors.BOLD}СТАТИСТИКА СИСТЕМЫ{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 50}{Colors.RESET}")

    import sqlite3
    try:
        conn = sqlite3.connect('car_factory.db')
        cursor = conn.cursor()

        tables = ['raw_docs', 'clean_docs', 'facts', 'alerts', 'alert_triggers']
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   {table}: {count} записей")
            except:
                print(f"   {table}: таблица не существует")

        conn.close()
    except Exception as e:
        print(f"   Ошибка при чтении БД: {e}")

    cache_dir = Path('cache')
    if cache_dir.exists():
        cache_files = list(cache_dir.rglob('*.json'))
        print(f"   Кэш: {len(cache_files)} файлов")

    results_dir = Path('results')
    if results_dir.exists():
        results_files = list(results_dir.glob('*.json'))
        print(f"   Результаты: {len(results_files)} файлов")


def main():
    while True:
        print_banner()
        print_menu()

        choice = input(f"{Colors.YELLOW}Введите номер действия: {Colors.RESET}").strip()

        if choice == '1':
            llm_extraction()
        elif choice == '2':
            run_metrics()
        elif choice == '3':
            manage_alerts()
        elif choice == '4':
            full_pipeline()
        elif choice == '5':
            show_dashboard()
        elif choice == '6':
            populate_test_data()
        elif choice == '7':
            clear_cache()
        elif choice == '8':
            show_stats()
        elif choice == '0':
            print(f"\n{Colors.GREEN}До свидания!{Colors.RESET}")
            break
        else:
            print(f"{Colors.RED}[ERROR] Неверный выбор{Colors.RESET}")

        input(f"\n{Colors.CYAN}Нажмите Enter для продолжения...{Colors.RESET}")


if __name__ == "__main__":
    main()