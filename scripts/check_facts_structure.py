import sqlite3


def check_facts():
    conn = sqlite3.connect('car_factory.db')
    cursor = conn.cursor()

    # Проверяем структуру таблицы
    cursor.execute("PRAGMA table_info(facts)")
    columns = cursor.fetchall()

    print("Структура таблицы 'facts':")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")

    # Проверяем есть ли данные
    cursor.execute("SELECT * FROM facts LIMIT 1")
    sample = cursor.fetchone()
    if sample:
        print(f"\nПример данных: {sample}")

    conn.close()


if __name__ == "__main__":
    check_facts()