import os
import json
import sqlite3
import re
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
import csv
from io import BytesIO, StringIO
from pathlib import Path

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / 'templates'
STATIC_DIR = BASE_DIR / 'static'

TEMPLATES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

app = Flask(__name__,
            template_folder=str(TEMPLATES_DIR),
            static_folder=str(STATIC_DIR))
CORS(app)

DB_PATH = 'car_factory.db'


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


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
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("SELECT COUNT(*) FROM facts")
        total_docs = cur.fetchone()[0] or 0

        cur.execute("SELECT COUNT(*) FROM facts WHERE type = 'vacancy'")
        total_vacancies = cur.fetchone()[0] or 0

        cur.execute("SELECT COUNT(*) FROM facts WHERE type = 'release'")
        total_releases = cur.fetchone()[0] or 0

        cur.execute("SELECT COUNT(*) FROM facts WHERE type = 'price'")
        total_prices = cur.fetchone()[0] or 0

        cur.execute("SELECT COUNT(*) FROM alerts WHERE is_active = 1")
        total_alerts = cur.fetchone()[0] or 0

        cur.execute('''
                    SELECT DATE (created_at) as date, COUNT (*) as count
                    FROM facts
                    WHERE created_at IS NOT NULL
                    GROUP BY DATE (created_at)
                    ORDER BY date DESC
                        LIMIT 30
                    ''')
        daily_stats = []
        for row in cur.fetchall():
            daily_stats.append({'date': row['date'], 'count': row['count']})

    except Exception as e:
        print(f"Error: {e}")
        total_docs = 0
        total_vacancies = 0
        total_releases = 0
        total_prices = 0
        total_alerts = 0
        daily_stats = []

    conn.close()
    return jsonify({
        'total_docs': total_docs,
        'total_vacancies': total_vacancies,
        'total_releases': total_releases,
        'total_prices': total_prices,
        'total_alerts': total_alerts,
        'daily_stats': daily_stats
    })


# ==================== API: ЛЕНТА ФАКТОВ ====================

@app.route('/api/facts')
def get_facts():
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    company = request.args.get('company')
    fact_type = request.args.get('type')

    conn = get_db()
    cur = conn.cursor()

    query = "SELECT * FROM facts"
    params = []
    conditions = []

    if company:
        conditions.append("fact_data LIKE ?")
        params.append(f'%{company}%')

    if fact_type:
        conditions.append("type = ?")
        params.append(fact_type)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cur.execute(query, params)

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
            'created_at': row['created_at']
        })

    count_query = "SELECT COUNT(*) FROM facts"
    if conditions:
        count_query += " WHERE " + " AND ".join(conditions)
        cur.execute(count_query, params[:len(params) - 2])
    else:
        cur.execute(count_query)
    total = cur.fetchone()[0] or 0

    conn.close()
    return jsonify({
        'facts': facts,
        'total': total,
        'limit': limit,
        'offset': offset,
        'total_pages': (total + limit - 1) // limit if total > 0 else 1
    })


# ==================== API: КОМПАНИИ (ИСПРАВЛЕНО) ====================

# Компании из двух слов (целиком)
MULTI_WORD_COMPANIES = [
    'Aston Martin', 'Alfa Romeo', 'Land Rover', 'Rolls Royce',
    'General Motors', 'Great Wall', 'Li Auto', 'Lynk Co',
    'Mercedes-Benz', 'Morgan Motor'
]

# Однословные компании (исключая те, что являются частями двухсловных)
SINGLE_WORD_COMPANIES = [
    'Tesla', 'BMW', 'Mercedes', 'Audi', 'Volkswagen', 'Porsche',
    'Toyota', 'Honda', 'Nissan', 'Hyundai', 'Kia', 'Ford',
    'Chevrolet', 'Cadillac', 'Volvo', 'Subaru', 'Mazda', 'Mitsubishi',
    'Lexus', 'Acura', 'Infiniti', 'Jaguar', 'Ferrari', 'Lamborghini',
    'Maserati', 'Bugatti', 'McLaren', 'Bentley', 'Fiat', 'Peugeot',
    'Citroen', 'Renault', 'Opel', 'Skoda', 'Seat', 'Lada',
    'АвтоВАЗ', 'ГАЗ', 'УАЗ', 'КАМАЗ', 'BYD', 'Geely', 'Nio', 'Xpeng'
]


@app.route('/api/companies')
def get_companies():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT fact_data FROM facts")
    rows = cur.fetchall()

    companies = set()

    for row in rows:
        try:
            data = json.loads(row['fact_data']) if row['fact_data'] else {}
            text = str(data.get('value', '')) + ' ' + str(data)

            # Проверяем поле company в JSON
            if 'company' in data and data['company']:
                companies.add(data['company'])

            # Сначала ищем компании из двух слов
            for mw in MULTI_WORD_COMPANIES:
                if mw.lower() in text.lower():
                    companies.add(mw)

            # Потом ищем однословные компании
            for sw in SINGLE_WORD_COMPANIES:
                if sw.lower() in text.lower():
                    # Проверяем, не является ли это частью двухсловной компании
                    is_part_of_multi = False
                    for mw in MULTI_WORD_COMPANIES:
                        if sw.lower() in mw.lower() and mw.lower() != sw.lower():
                            is_part_of_multi = True
                            break
                    if not is_part_of_multi:
                        companies.add(sw)

        except:
            pass

    conn.close()

    # Сортируем: сначала двухсловные, потом однословные
    multi = [c for c in companies if ' ' in c]
    single = [c for c in companies if ' ' not in c]
    result = sorted(multi) + sorted(single)

    return jsonify(result)


@app.route('/api/company/<company_name>')
def get_company_facts(company_name):
    conn = get_db()
    cur = conn.cursor()

    cur.execute('''
                SELECT *
                FROM facts
                WHERE fact_data LIKE ?
                ORDER BY created_at DESC
                ''', (f'%{company_name}%',))

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
            'created_at': row['created_at']
        })

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
        'facts': facts[:100]
    })


# ==================== API: АЛЕРТЫ ====================

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM alerts ORDER BY created_at DESC")
        alerts = []
        for row in cur.fetchall():
            alerts.append({
                'id': row['id'],
                'name': row['name'],
                'company': row['company'],
                'type': row['alert_type'],
                'keywords': row['keywords'].split(',') if row['keywords'] else [],
                'language': row['language'] or 'any',
                'is_active': bool(row['is_active']),
                'created_at': row['created_at']
            })
    except:
        alerts = []

    conn.close()
    return jsonify(alerts)


@app.route('/api/alerts', methods=['POST'])
def create_alert():
    data = request.json
    conn = get_db()
    cur = conn.cursor()

    keywords = ','.join(data.get('keywords', [])) if isinstance(data.get('keywords'), list) else data.get('keywords',
                                                                                                          '')

    cur.execute('''
                INSERT INTO alerts (name, company, alert_type, keywords, language, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (data.get('name'), data.get('company'), data.get('type'), keywords, data.get('language', 'any'),
                      datetime.now()))

    conn.commit()
    alert_id = cur.lastrowid
    conn.close()
    return jsonify({'id': alert_id, 'message': 'Alert created'})


@app.route('/api/alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Alert deleted'})


# ==================== API: СВОДКА ====================

@app.route('/api/weekly-summary')
def get_weekly_summary():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    conn = get_db()
    cur = conn.cursor()

    cur.execute('''
                SELECT DATE (created_at) as date, COUNT (*) as count
                FROM facts
                WHERE created_at >= ?
                GROUP BY DATE (created_at)
                ORDER BY date
                ''', (start_date,))

    news_by_day = [{'date': row['date'], 'count': row['count']} for row in cur.fetchall()]

    cur.execute("SELECT COUNT(*) FROM facts WHERE created_at >= ?", (start_date,))
    total_new = cur.fetchone()[0] or 0

    conn.close()

    return jsonify({
        'period': {'start': start_date.strftime('%Y-%m-%d'), 'end': end_date.strftime('%Y-%m-%d')},
        'news_by_day': news_by_day,
        'new_vacancies': total_new // 3,
        'new_releases': total_new // 3,
        'new_prices': total_new // 3,
        'alert_triggers': 0,
        'top_companies': []
    })


# ==================== API: ЭКСПОРТ ====================

@app.route('/api/facts/export/csv')
def export_facts_csv():
    company = request.args.get('company')

    conn = get_db()
    cur = conn.cursor()

    if company:
        cur.execute("SELECT * FROM facts WHERE fact_data LIKE ?", (f'%{company}%',))
    else:
        cur.execute("SELECT * FROM facts LIMIT 1000")

    rows = cur.fetchall()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['id', 'type', 'fact_data', 'confidence', 'created_at'])

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
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, fact_data FROM facts WHERE fact_data IS NULL OR LENGTH(fact_data) < 50 LIMIT 15")

    bad_sources = []
    for row in cur.fetchall():
        bad_sources.append({
            'id': row['id'],
            'url': 'fact_' + str(row['id']),
            'content_length': len(row['fact_data']) if row['fact_data'] else 0
        })

    conn.close()
    return jsonify({
        'bad_sources_count': len(bad_sources),
        'bad_sources': bad_sources,
        'message': f'Found {len(bad_sources)} potentially bad sources'
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)