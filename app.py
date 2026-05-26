import os
import json
import sqlite3
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

# Просто используем SQLite, без PostgreSQL
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

        # Динамика по дням
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

    # Общее количество
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


# ==================== API: КОМПАНИИ ====================

@app.route('/api/companies')
def get_companies():
    conn = get_db()
    cur = conn.cursor()

    companies = set()

    cur.execute("SELECT fact_data FROM facts LIMIT 200")

    for row in cur.fetchall():
        try:
            data = json.loads(row['fact_data']) if row['fact_data'] else {}

            if 'company' in data and data['company']:
                companies.add(data['company'])

            text = str(data.get('value', ''))
            car_companies = ['Tesla', 'BMW', 'Toyota', 'Lada', 'Mercedes', 'Audi', 'Volkswagen', 'Kia', 'Hyundai',
                             'Nissan']
            for company in car_companies:
                if company.lower() in text.lower():
                    companies.add(company)
        except:
            pass

    conn.close()

    result = sorted(list(companies)) if companies else ['Tesla', 'BMW', 'Toyota']
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
        'facts': facts[:50]
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)