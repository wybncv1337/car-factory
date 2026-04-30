import os
import json
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
import csv
from io import BytesIO, StringIO
from pathlib import Path

# ==================== КОНФИГУРАЦИЯ ====================

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / 'templates'
STATIC_DIR = BASE_DIR / 'static'

TEMPLATES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

app = Flask(__name__,
            template_folder=str(TEMPLATES_DIR),
            static_folder=str(STATIC_DIR))
CORS(app)

# Определяем тип базы данных
DATABASE_URL = os.environ.get('DATABASE_URL')
IS_RENDER = os.environ.get('RENDER') == 'true'


# ==================== РАБОТА С БАЗОЙ ДАННЫХ ====================

def get_db_connection():
    """Универсальное подключение к БД (SQLite или PostgreSQL)"""

    if DATABASE_URL and IS_RENDER:
        # PostgreSQL на Render
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    else:
        # SQLite локально
        conn = sqlite3.connect('car_factory.db')
        conn.row_factory = sqlite3.Row
        return conn


def execute_query(cursor, query, params=None):
    """Универсальное выполнение запроса (адаптирует ? под %s для PostgreSQL)"""
    if DATABASE_URL and IS_RENDER:
        # PostgreSQL
        if params:
            query = query.replace('?', '%s')
            cursor.execute(query, params)
        else:
            cursor.execute(query)
    else:
        # SQLite
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)


def init_db():
    """Создаёт таблицы, если их нет"""
    conn = get_db_connection()
    cur = conn.cursor()

    if DATABASE_URL and IS_RENDER:
        # PostgreSQL
        cur.execute('''
                    CREATE TABLE IF NOT EXISTS facts
                    (
                        id
                        SERIAL
                        PRIMARY
                        KEY,
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
        cur.execute('''
                    CREATE TABLE IF NOT EXISTS alerts
                    (
                        id
                        SERIAL
                        PRIMARY
                        KEY,
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
        cur.execute('''
                    CREATE TABLE IF NOT EXISTS alert_triggers
                    (
                        id
                        SERIAL
                        PRIMARY
                        KEY,
                        alert_id
                        INTEGER,
                        matched_doc_id
                        INTEGER,
                        matched_text
                        TEXT,
                        triggered_at
                        TIMESTAMP
                        DEFAULT
                        CURRENT_TIMESTAMP
                    )
                    ''')
    else:
        # SQLite
        cur.execute('''
                    CREATE TABLE IF NOT EXISTS facts
                    (
                        id
                        INTEGER
                        PRIMARY
                        KEY
                        AUTOINCREMENT,
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
        cur.execute('''
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
        cur.execute('''
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
                        triggered_at
                        TIMESTAMP
                        DEFAULT
                        CURRENT_TIMESTAMP
                    )
                    ''')

    conn.commit()
    conn.close()

    # Добавляем тестовые данные, если таблица пустая
    seed_test_data()
    print("✅ Database initialized")


def seed_test_data():
    """Добавляет тестовые данные, если таблица фактов пустая"""
    conn = get_db_connection()
    cur = conn.cursor()

    # Проверяем, есть ли данные
    execute_query(cur, "SELECT COUNT(*) as count FROM facts")
    count = cur.fetchone()['count']

    if count == 0:
        test_data = [
            ('release', '{"value":"Tesla выпустила новую модель Model 3", "company":"Tesla", "year":2024}', 0.95),
            ('vacancy',
             '{"value":"Открыта вакансия инженера в Tesla", "position":"Engineer", "salary":150000, "company":"Tesla"}',
             0.92),
            ('price',
             '{"value":"Цена Tesla Model 3 — 3.5 млн руб.", "amount":3500000, "currency":"RUB", "company":"Tesla"}',
             0.90),
            ('release', '{"value":"BMW представила новый электромобиль iX5", "company":"BMW", "year":2024}', 0.94),
            ('vacancy',
             '{"value":"BMW seeks Senior Java Developer", "position":"Java Dev", "salary":140000, "company":"BMW"}',
             0.91),
            ('price', '{"value":"BMW iX5 price starts at $45,000", "amount":45000, "currency":"USD", "company":"BMW"}',
             0.89),
            ('release', '{"value":"Toyota представила новую Camry 2024", "company":"Toyota", "year":2024}', 0.93),
            ('vacancy',
             '{"value":"Toyota открывает вакансию механика", "position":"Mechanic", "salary":90000, "company":"Toyota"}',
             0.88),
            ('price',
             '{"value":"Стоимость Toyota Camry от 2.8 млн руб.", "amount":2800000, "currency":"RUB", "company":"Toyota"}',
             0.91),
        ]

        for fact_type, fact_data, confidence in test_data:
            if DATABASE_URL and IS_RENDER:
                cur.execute("INSERT INTO facts (type, fact_data, confidence) VALUES (%s, %s, %s)",
                            (fact_type, fact_data, confidence))
            else:
                cur.execute("INSERT INTO facts (type, fact_data, confidence) VALUES (?, ?, ?)",
                            (fact_type, fact_data, confidence))

        conn.commit()
        print(f"✅ Added {len(test_data)} test records")

    conn.close()


# Инициализируем БД при запуске
init_db()


# ==================== СТРАНИЦЫ ====================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/facts-feed')
def facts_feed_page():
    return render_template('facts_feed.html')


@app.route('/companies')
def companies_page():
    return render_template('companies.html')


@app.route('/company/<company_name>')
def company_page(company_name):
    return render_template('company.html', company=company_name)


@app.route('/alerts')
def alerts_page():
    return render_template('alerts.html')


@app.route('/weekly-summary')
def weekly_summary_page():
    return render_template('weekly_summary.html')


@app.route('/qa-tests')
def qa_tests_page():
    return render_template('qa_tests.html')


# ==================== API: МЕТРИКИ ====================

@app.route('/api/metrics')
def get_metrics():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        execute_query(cur, "SELECT COUNT(*) as count FROM facts")
        total_facts = cur.fetchone()['count'] or 0
    except:
        total_facts = 0

    try:
        execute_query(cur, "SELECT COUNT(*) as count FROM alerts WHERE is_active = 1")
        total_alerts = cur.fetchone()['count'] or 0
    except:
        total_alerts = 0

    try:
        execute_query(cur, "SELECT COUNT(*) as count FROM alert_triggers")
        total_triggers = cur.fetchone()['count'] or 0
    except:
        total_triggers = 0

    # Подсчёт по типам (упрощённо)
    vacancies = total_facts // 3
    releases = total_facts // 3
    prices = total_facts // 3

    # Динамика по дням (последние 30 дней)
    daily_stats = []
    try:
        execute_query(cur, '''
                           SELECT DATE (created_at) as date, COUNT (*) as count
                           FROM facts
                           WHERE created_at IS NOT NULL
                           GROUP BY DATE (created_at)
                           ORDER BY date DESC
                               LIMIT 30
                           ''')
        for row in cur.fetchall():
            daily_stats.append({'date': row['date'], 'count': row['count']})
    except:
        pass

    conn.close()

    return jsonify({
        'total_docs': total_facts,
        'total_vacancies': vacancies,
        'total_releases': releases,
        'total_prices': prices,
        'total_alerts': total_alerts,
        'total_triggers': total_triggers,
        'daily_stats': daily_stats,
        'vacancies_timeline': [],
        'releases_timeline': []
    })


# ==================== API: ЛЕНТА ФАКТОВ ====================

@app.route('/api/facts')
def get_facts():
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    company = request.args.get('company')

    conn = get_db_connection()
    cur = conn.cursor()

    # Базовый запрос
    query = "SELECT * FROM facts"
    params = []

    if company:
        query += " WHERE fact_data LIKE ?"
        params.append(f'%{company}%')

    query += " ORDER BY id DESC"

    # Пагинация
    if DATABASE_URL and IS_RENDER:
        query += " LIMIT %s OFFSET %s"
    else:
        query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    execute_query(cur, query, params)

    facts = []
    for row in cur.fetchall():
        fact_data = {}
        if row['fact_data']:
            try:
                fact_data = json.loads(row['fact_data'])
            except:
                fact_data = {'value': row['fact_data'][:200]}

        facts.append({
            'id': row['id'],
            'type': row['type'],
            'data': fact_data,
            'confidence': row['confidence'] or 0.5,
            'created_at': row['created_at'],
            'source_url': ''
        })

    # Общее количество
    count_query = "SELECT COUNT(*) as count FROM facts"
    if company:
        count_query += " WHERE fact_data LIKE ?"
        execute_query(cur, count_query, [f'%{company}%'])
    else:
        execute_query(cur, count_query)
    total = cur.fetchone()['count'] or 0

    conn.close()

    return jsonify({
        'facts': facts,
        'total': total,
        'limit': limit,
        'offset': offset,
        'total_pages': (total + limit - 1) // limit if total > 0 else 1
    })


# ==================== API: КОМПАНИИ ====================

@app.route('/api/companies')
def get_companies():
    conn = get_db_connection()
    cur = conn.cursor()

    companies = set()

    execute_query(cur, "SELECT fact_data FROM facts LIMIT 100")
    for row in cur.fetchall():
        if row['fact_data']:
            try:
                data = json.loads(row['fact_data'])
                company = data.get('company', '')
                if company:
                    companies.add(company)
            except:
                pass

    conn.close()

    # Если нет компаний в БД, возвращаем стандартные
    if not companies:
        companies = ['Tesla', 'BMW', 'Toyota', 'Mercedes', 'Kia']

    return jsonify(sorted(list(companies)))


@app.route('/api/company/<company_name>')
def get_company_facts(company_name):
    conn = get_db_connection()
    cur = conn.cursor()

    execute_query(cur, "SELECT * FROM facts WHERE fact_data LIKE ? ORDER BY id DESC", [f'%{company_name}%'])

    facts = []
    for row in cur.fetchall():
        fact_data = {}
        if row['fact_data']:
            try:
                fact_data = json.loads(row['fact_data'])
            except:
                fact_data = {'value': row['fact_data'][:200]}

        facts.append({
            'id': row['id'],
            'type': row['type'],
            'data': fact_data,
            'confidence': row['confidence'] or 0.5,
            'created_at': row['created_at'],
            'source_url': ''
        })

    # Статистика по категориям
    stats = {
        'total': len(facts),
        'vacancies': len([f for f in facts if f['type'] == 'vacancy']),
        'releases': len([f for f in facts if f['type'] == 'release']),
        'prices': len([f for f in facts if f['type'] == 'price'])
    }

    conn.close()

    return jsonify({
        'company': company_name,
        'stats': stats,
        'facts': facts[:50]
    })


# ==================== API: АЛЕРТЫ ====================

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        execute_query(cur, "SELECT * FROM alerts ORDER BY created_at DESC")
        rows = cur.fetchall()

        alerts = []
        for row in rows:
            alerts.append({
                'id': row['id'],
                'name': row['name'],
                'company': row['company'],
                'type': row['alert_type'],
                'keywords': row['keywords'].split(',') if row['keywords'] else [],
                'language': row['language'] or 'any',
                'is_active': bool(row['is_active']),
                'created_at': row['created_at'],
                'last_triggered_at': row.get('last_triggered_at')
            })
    except:
        alerts = []

    conn.close()
    return jsonify(alerts)


@app.route('/api/alerts', methods=['POST'])
def create_alert():
    data = request.json

    conn = get_db_connection()
    cur = conn.cursor()

    keywords = ','.join(data.get('keywords', [])) if isinstance(data.get('keywords'), list) else data.get('keywords',
                                                                                                          '')

    if DATABASE_URL and IS_RENDER:
        cur.execute('''
                    INSERT INTO alerts (name, company, alert_type, keywords, language, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ''',
                    (data.get('name'), data.get('company'), data.get('type'), keywords, data.get('language', 'any'),
                     datetime.now()))
    else:
        cur.execute('''
                    INSERT INTO alerts (name, company, alert_type, keywords, language, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''',
                    (data.get('name'), data.get('company'), data.get('type'), keywords, data.get('language', 'any'),
                     datetime.now()))

    conn.commit()
    alert_id = cur.lastrowid
    conn.close()

    return jsonify({'id': alert_id, 'message': 'Alert created'})


@app.route('/api/alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    conn = get_db_connection()
    cur = conn.cursor()

    if DATABASE_URL and IS_RENDER:
        cur.execute("DELETE FROM alerts WHERE id = %s", (alert_id,))
    else:
        cur.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))

    conn.commit()
    conn.close()
    return jsonify({'message': 'Alert deleted'})


# ==================== API: СВОДКА ЗА НЕДЕЛЮ ====================

@app.route('/api/weekly-summary')
def get_weekly_summary():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    conn = get_db_connection()
    cur = conn.cursor()

    # Новости за неделю
    news_by_day = []
    try:
        if DATABASE_URL and IS_RENDER:
            cur.execute('''
                        SELECT DATE (created_at) as date, COUNT (*) as count
                        FROM facts
                        WHERE created_at >= %s
                        GROUP BY DATE (created_at)
                        ORDER BY date
                        ''', (start_date,))
        else:
            cur.execute('''
                        SELECT DATE (created_at) as date, COUNT (*) as count
                        FROM facts
                        WHERE created_at >= ?
                        GROUP BY DATE (created_at)
                        ORDER BY date
                        ''', (start_date,))

        for row in cur.fetchall():
            news_by_day.append({'date': row['date'], 'count': row['count']})
    except:
        pass

    # Новые факты за неделю
    if DATABASE_URL and IS_RENDER:
        cur.execute("SELECT COUNT(*) as count FROM facts WHERE created_at >= %s", (start_date,))
    else:
        cur.execute("SELECT COUNT(*) as count FROM facts WHERE created_at >= ?", (start_date,))
    total_new = cur.fetchone()['count'] or 0

    # Срабатывания алертов
    try:
        if DATABASE_URL and IS_RENDER:
            cur.execute("SELECT COUNT(*) as count FROM alert_triggers WHERE triggered_at >= %s", (start_date,))
        else:
            cur.execute("SELECT COUNT(*) as count FROM alert_triggers WHERE triggered_at >= ?", (start_date,))
        alert_triggers = cur.fetchone()['count'] or 0
    except:
        alert_triggers = 0

    conn.close()

    return jsonify({
        'period': {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d')
        },
        'news_by_day': news_by_day,
        'new_vacancies': total_new // 3,
        'new_releases': total_new // 3,
        'new_prices': total_new // 3,
        'alert_triggers': alert_triggers,
        'top_companies': []
    })


# ==================== API: ЭКСПОРТ CSV ====================

@app.route('/api/facts/export/csv')
def export_facts_csv():
    conn = get_db_connection()
    cur = conn.cursor()

    execute_query(cur, "SELECT * FROM facts LIMIT 1000")
    rows = cur.fetchall()

    output = StringIO()
    writer = csv.writer(output)

    if rows:
        headers = ['id', 'type', 'fact_data', 'confidence', 'created_at']
        writer.writerow(headers)

        for row in rows:
            writer.writerow([row['id'], row['type'], row['fact_data'], row['confidence'], row['created_at']])

    conn.close()

    output.seek(0)
    return send_file(
        BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'facts_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )


# ==================== API: QA ТЕСТЫ ====================

@app.route('/api/qa/test-bad-sources')
def test_bad_sources():
    conn = get_db_connection()
    cur = conn.cursor()

    # Ищем короткие записи
    if DATABASE_URL and IS_RENDER:
        cur.execute(
            "SELECT id, fact_data, LENGTH(fact_data) as len_content FROM facts WHERE fact_data IS NULL OR LENGTH(fact_data) < 50 LIMIT 15")
    else:
        cur.execute(
            "SELECT id, fact_data, LENGTH(fact_data) as len_content FROM facts WHERE fact_data IS NULL OR LENGTH(fact_data) < 50 LIMIT 15")

    bad_sources = []
    for row in cur.fetchall():
        bad_sources.append({
            'id': row['id'],
            'url': 'fact_' + str(row['id']),
            'content_length': row['len_content'] or 0
        })

    conn.close()

    return jsonify({
        'bad_sources_count': len(bad_sources),
        'bad_sources': bad_sources,
        'message': f'Found {len(bad_sources)} potentially bad sources'
    })


# ==================== ЗАПУСК ====================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)