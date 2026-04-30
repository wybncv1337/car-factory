import sqlite3
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from io import BytesIO, StringIO
from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / 'templates'
STATIC_DIR = BASE_DIR / 'static'

TEMPLATES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

app = Flask(__name__,
            template_folder=str(TEMPLATES_DIR),
            static_folder=str(STATIC_DIR))
CORS(app)

DB_PATH = BASE_DIR / 'car_factory.db'


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
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
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM raw_docs")
        total_docs = cursor.fetchone()[0] or 0
    except:
        total_docs = 0

    try:
        cursor.execute("SELECT COUNT(*) FROM facts")
        total_facts = cursor.fetchone()[0] or 0
    except:
        total_facts = 0

    try:
        cursor.execute("SELECT COUNT(*) FROM alerts WHERE is_active = 1")
        total_alerts = cursor.fetchone()[0] or 0
    except:
        total_alerts = 0

    try:
        cursor.execute("SELECT COUNT(*) FROM alert_triggers")
        total_triggers = cursor.fetchone()[0] or 0
    except:
        total_triggers = 0

    daily_stats = []
    try:
        cursor.execute('''
                       SELECT DATE (created_at) as date, COUNT (*) as count
                       FROM raw_docs
                       WHERE created_at IS NOT NULL
                       GROUP BY DATE (created_at)
                       ORDER BY date DESC
                           LIMIT 30
                       ''')
        daily_stats = [{'date': row['date'], 'count': row['count']} for row in cursor.fetchall()]
    except:
        pass

    conn.close()

    return jsonify({
        'total_docs': total_docs,
        'total_vacancies': total_facts // 3,
        'total_releases': total_facts // 3,
        'total_prices': total_facts // 3,
        'total_alerts': total_alerts,
        'total_triggers': total_triggers,
        'daily_stats': daily_stats,
        'vacancies_timeline': [],
        'releases_timeline': []
    })


# ==================== API: ЛЕНТА ФАКТОВ ====================

@app.route('/api/facts')
def get_facts():
    try:
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM facts ORDER BY id DESC LIMIT ? OFFSET ?', (limit, offset))
        rows = cursor.fetchall()

        cursor.execute('SELECT COUNT(*) FROM facts')
        total = cursor.fetchone()[0] or 0

        facts = []
        for row in rows:
            row_dict = {key: row[key] for key in row.keys()}

            fact_data = {}
            if 'fact_data' in row_dict and row_dict['fact_data']:
                try:
                    fact_data = json.loads(row_dict['fact_data'])
                except:
                    fact_data = {'value': str(row_dict['fact_data'])[:200]}

            facts.append({
                'id': row_dict.get('id'),
                'type': 'fact',
                'data': fact_data,
                'confidence': row_dict.get('confidence', 0.5),
                'created_at': row_dict.get('created_at'),
                'source_url': row_dict.get('source_url', '')
            })

        conn.close()

        return jsonify({
            'facts': facts,
            'total': total,
            'limit': limit,
            'offset': offset,
            'total_pages': (total + limit - 1) // limit if total > 0 else 1
        })

    except Exception as e:
        print(f"Error in /api/facts: {e}")
        return jsonify({'facts': [], 'total': 0, 'limit': 20, 'offset': 0, 'total_pages': 1})


# ==================== API: КОМПАНИИ ====================

@app.route('/api/companies')
def get_companies():
    try:
        conn = get_db()
        cursor = conn.cursor()

        companies = set()

        cursor.execute('SELECT fact_data FROM facts LIMIT 100')
        for row in cursor.fetchall():
            if row['fact_data']:
                text = str(row['fact_data']).lower()
                for company in ['tesla', 'toyota', 'bmw', 'mercedes', 'kia', 'hyundai', 'nissan']:
                    if company in text:
                        companies.add(company.capitalize())

        conn.close()

        return jsonify(sorted(list(companies)))

    except Exception as e:
        print(f"Error in /api/companies: {e}")
        return jsonify([])


@app.route('/api/company/<company_name>')
def get_company_facts(company_name):
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM facts ORDER BY id DESC')
        rows = cursor.fetchall()

        facts = []
        for row in rows:
            row_dict = {key: row[key] for key in row.keys()}

            fact_data = {}
            if 'fact_data' in row_dict and row_dict['fact_data']:
                try:
                    fact_data = json.loads(row_dict['fact_data'])
                except:
                    fact_data = {'value': str(row_dict['fact_data'])[:200]}

            if company_name.lower() in str(fact_data).lower():
                facts.append({
                    'id': row_dict.get('id'),
                    'type': 'fact',
                    'data': fact_data,
                    'confidence': row_dict.get('confidence', 0.5),
                    'created_at': row_dict.get('created_at'),
                    'source_url': row_dict.get('source_url', '')
                })

        conn.close()

        stats = {
            'total': len(facts),
            'vacancies': 0,
            'releases': 0,
            'prices': 0
        }

        return jsonify({
            'company': company_name,
            'stats': stats,
            'facts': facts[:50]
        })

    except Exception as e:
        print(f"Error in /api/company: {e}")
        return jsonify(
            {'company': company_name, 'stats': {'total': 0, 'vacancies': 0, 'releases': 0, 'prices': 0}, 'facts': []})


# ==================== API: АЛЕРТЫ ====================

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM alerts ORDER BY created_at DESC')
        rows = cursor.fetchall()

        alerts = []
        for row in rows:
            row_dict = {key: row[key] for key in row.keys()}
            alerts.append({
                'id': row_dict.get('id'),
                'name': row_dict.get('name', ''),
                'company': row_dict.get('company'),
                'type': row_dict.get('alert_type'),
                'keywords': row_dict.get('keywords', '').split(',') if row_dict.get('keywords') else [],
                'language': row_dict.get('language', 'any'),
                'is_active': bool(row_dict.get('is_active', 1)),
                'created_at': row_dict.get('created_at'),
                'last_triggered_at': row_dict.get('last_triggered_at')
            })

        conn.close()
        return jsonify(alerts)

    except Exception as e:
        print(f"Error in /api/alerts: {e}")
        return jsonify([])


@app.route('/api/alerts', methods=['POST'])
def create_alert():
    try:
        data = request.json

        conn = get_db()
        cursor = conn.cursor()

        keywords = ','.join(data.get('keywords', [])) if isinstance(data.get('keywords'), list) else data.get(
            'keywords', '')

        cursor.execute('''
                       INSERT INTO alerts (name, company, alert_type, keywords, language, created_at)
                       VALUES (?, ?, ?, ?, ?, ?)
                       ''', (
                           data.get('name'),
                           data.get('company'),
                           data.get('type'),
                           keywords,
                           data.get('language', 'any'),
                           datetime.now()
                       ))

        conn.commit()
        alert_id = cursor.lastrowid
        conn.close()

        return jsonify({'id': alert_id, 'message': 'Alert created'})

    except Exception as e:
        print(f"Error in create_alert: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM alerts WHERE id = ?', (alert_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Alert deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== API: СВОДКА ЗА НЕДЕЛЮ ====================

@app.route('/api/weekly-summary')
def get_weekly_summary():
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        conn = get_db()
        cursor = conn.cursor()

        news_by_day = []
        try:
            cursor.execute('''
                           SELECT DATE (created_at) as date, COUNT (*) as count
                           FROM raw_docs
                           WHERE created_at IS NOT NULL AND created_at >= ?
                           GROUP BY DATE (created_at)
                           ORDER BY date
                           ''', (start_date,))
            news_by_day = [{'date': row['date'], 'count': row['count']} for row in cursor.fetchall()]
        except:
            pass

        try:
            cursor.execute('SELECT COUNT(*) FROM facts WHERE created_at >= ?', (start_date,))
            total_new = cursor.fetchone()[0] or 0
        except:
            total_new = 0

        try:
            cursor.execute('SELECT COUNT(*) FROM alert_triggers WHERE triggered_at >= ?', (start_date,))
            alert_triggers = cursor.fetchone()[0] or 0
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

    except Exception as e:
        print(f"Error in weekly-summary: {e}")
        return jsonify({
            'period': {'start': '2024-01-01', 'end': '2024-01-07'},
            'news_by_day': [],
            'new_vacancies': 0,
            'new_releases': 0,
            'new_prices': 0,
            'alert_triggers': 0,
            'top_companies': []
        })


# ==================== API: ЭКСПОРТ ====================

@app.route('/api/facts/export/csv')
def export_facts_csv():
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM facts LIMIT 1000')
        rows = cursor.fetchall()

        output = StringIO()
        writer = csv.writer(output)

        if rows:
            headers = [key for key in rows[0].keys()]
            writer.writerow(headers)

            for row in rows:
                writer.writerow([row[h] for h in headers])

        conn.close()

        output.seek(0)
        return send_file(
            BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'facts_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )

    except Exception as e:
        print(f"Error in export: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== QA ТЕСТЫ ====================

@app.route('/api/qa/test-bad-sources')
def test_bad_sources():
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
                       SELECT id, source_url, LENGTH(raw_content) as len_content
                       FROM raw_docs
                       WHERE raw_content IS NULL
                          OR LENGTH(raw_content) < 100 LIMIT 15
                       ''')

        bad_sources = []
        for row in cursor.fetchall():
            bad_sources.append({
                'id': row['id'],
                'url': row['source_url'] or 'unknown',
                'content_length': row['len_content'] or 0
            })

        conn.close()

        return jsonify({
            'bad_sources_count': len(bad_sources),
            'bad_sources': bad_sources,
            'message': f'Found {len(bad_sources)} potentially bad sources'
        })

    except Exception as e:
        return jsonify({'bad_sources_count': 0, 'bad_sources': [], 'message': str(e)})


if __name__ == '__main__':
    print("=" * 50)
    print("Car Factory Analytics")
    print("=" * 50)
    print(f"Templates: {TEMPLATES_DIR}")
    print(f"Database: {DB_PATH}")
    print(f"Open: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)