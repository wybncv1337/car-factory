"""AI News — веб-приложение для мониторинга ИИ-инструментов."""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

from demo_data import DEMO_FACTS, DEMO_SEED_VERSION, DEVELOPER_SITES, DEVELOPER_NEWS_PAGES

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "ai_radar.db"
DAYS_WINDOW = 60
COMPANY_SITES = {name.casefold(): url for name, url in DEVELOPER_SITES.items()}
NEWS_PAGES = {name.casefold(): url for name, url in DEVELOPER_NEWS_PAGES.items()}
app = Flask(__name__, template_folder=str(BASE_DIR / "templates"), static_folder=str(BASE_DIR / "static"))
CORS(app)


def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def ensure_schema(conn):
    """Подтягивает колонки новых версий схемы в уже существующей базе."""
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(facts)")}
    if "news_url" not in columns:
        conn.execute("ALTER TABLE facts ADD COLUMN news_url TEXT")
    if "is_demo" not in columns:
        # Всё, что попало в базу до появления сборщика, — демонстрационные карточки.
        conn.execute("ALTER TABLE facts ADD COLUMN is_demo INTEGER NOT NULL DEFAULT 1")


def init_db():
    """Создаёт базу и один раз загружает сбалансированную витрину за 60 дней."""
    conn = get_db()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL CHECK(type IN ('tool', 'update', 'pricing')),
                fact_data TEXT NOT NULL,
                confidence REAL NOT NULL DEFAULT 0.8,
                source_url TEXT,
                news_url TEXT,
                is_demo INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)
        ensure_schema(conn)
        conn.commit()  # ALTER TABLE должен сохраниться даже если пересид не требуется
        row = conn.execute("SELECT value FROM app_settings WHERE key = 'demo_seed_version'").fetchone()
        if row and row["value"] == DEMO_SEED_VERSION:
            return

        # Пересид затрагивает только демо-записи: собранные новости остаются в базе.
        conn.execute("DELETE FROM facts WHERE is_demo = 1")
        now = datetime.now()
        for fact_type, data, url, days_ago in DEMO_FACTS:
            created_at = (now - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(
                "INSERT INTO facts (type, fact_data, confidence, source_url, created_at, is_demo) VALUES (?, ?, ?, ?, ?, 1)",
                (fact_type, json.dumps(data, ensure_ascii=False), 0.9, url, created_at),
            )
        conn.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES ('demo_seed_version', ?)", (DEMO_SEED_VERSION,))
        conn.commit()
    finally:
        conn.close()


def developer_site(developer, sites):
    return sites.get((developer or "").strip().casefold())


def row_to_fact(row):
    try:
        data = json.loads(row["fact_data"])
    except (TypeError, json.JSONDecodeError):
        data = {"value": row["fact_data"]}
    developer = data.get("developer")
    # У собранных новостей ссылка на статью лежит в базе, у демо-карточек — в карте разделов.
    news_url = row["news_url"] or developer_site(developer, NEWS_PAGES)
    return {"id": row["id"], "type": row["type"], "data": data, "confidence": row["confidence"], "source_url": row["source_url"], "company_url": developer_site(developer, COMPANY_SITES), "news_url": news_url, "created_at": row["created_at"]}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/facts-feed")
def facts_feed_page():
    return render_template("facts_feed.html")


@app.route("/developers")
def developers_page():
    return render_template("companies.html")


@app.route("/developer/<developer_name>")
def developer_page(developer_name):
    return render_template("company.html", developer=developer_name)


@app.route("/weekly-summary")
def weekly_summary_page():
    return render_template("weekly_summary.html")


def daily_breakdown(conn, days=DAYS_WINDOW):
    """Counts per day split by type, zero-filled so quiet days stay visible on the chart."""
    rows = conn.execute("SELECT DATE(created_at) AS date, type, COUNT(*) AS count FROM facts GROUP BY DATE(created_at), type").fetchall()
    today = datetime.now().date()
    stats = [
        {"date": (today - timedelta(days=offset)).strftime("%Y-%m-%d"), "tool": 0, "update": 0, "pricing": 0, "total": 0}
        for offset in range(days - 1, -1, -1)
    ]
    by_date = {item["date"]: item for item in stats}
    for row in rows:
        item = by_date.get(row["date"])
        if item and row["type"] in item:
            item[row["type"]] = row["count"]
            item["total"] += row["count"]
    return stats


@app.route("/api/metrics")
def get_metrics():
    with get_db() as conn:
        counts = {row["type"]: row["count"] for row in conn.execute("SELECT type, COUNT(*) AS count FROM facts GROUP BY type")}
        daily_stats = daily_breakdown(conn)
    return jsonify({"total_facts": sum(counts.values()), "total_tools": counts.get("tool", 0), "total_updates": counts.get("update", 0), "total_pricing": counts.get("pricing", 0), "daily_stats": daily_stats})


@app.route("/api/facts")
def get_facts():
    limit = min(request.args.get("limit", 20, type=int), 100)
    offset = max(request.args.get("offset", 0, type=int), 0)
    fact_type, developer = request.args.get("type", "").strip(), request.args.get("developer", "").strip()
    clauses, params = [], []
    if fact_type in {"tool", "update", "pricing"}:
        clauses.append("type = ?")
        params.append(fact_type)
    if developer:
        clauses.append("fact_data LIKE ?")
        params.append(f"%{developer}%")
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    with get_db() as conn:
        rows = conn.execute(f"SELECT * FROM facts{where} ORDER BY datetime(created_at) DESC, id DESC LIMIT ? OFFSET ?", params + [limit, offset]).fetchall()
        total = conn.execute(f"SELECT COUNT(*) FROM facts{where}", params).fetchone()[0]
    return jsonify({"facts": [row_to_fact(row) for row in rows], "total": total, "limit": limit, "offset": offset, "total_pages": max(1, (total + limit - 1) // limit)})


@app.route("/api/developers")
def get_developers():
    with get_db() as conn:
        rows = conn.execute("SELECT fact_data FROM facts").fetchall()
    developers = {json.loads(row["fact_data"]).get("developer") for row in rows}
    return jsonify(sorted(developer for developer in developers if developer))


@app.route("/api/developer/<developer_name>")
def get_developer_facts(developer_name):
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM facts WHERE fact_data LIKE ? ORDER BY datetime(created_at) DESC", (f"%{developer_name}%",)).fetchall()
    facts = [row_to_fact(row) for row in rows]
    return jsonify({"developer": developer_name, "facts": facts, "stats": {"total": len(facts), "tools": sum(f["type"] == "tool" for f in facts), "updates": sum(f["type"] == "update" for f in facts), "pricing": sum(f["type"] == "pricing" for f in facts)}})


@app.route("/api/weekly-summary")
def get_weekly_summary():
    start_date = datetime.now() - timedelta(days=7)
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM facts WHERE datetime(created_at) >= ? ORDER BY datetime(created_at)", (start_date.strftime("%Y-%m-%d %H:%M:%S"),)).fetchall()
    facts, by_day, developer_counts = [row_to_fact(row) for row in rows], {}, {}
    for fact in facts:
        by_day[fact["created_at"][:10]] = by_day.get(fact["created_at"][:10], 0) + 1
        developer = fact["data"].get("developer")
        if developer:
            developer_counts[developer] = developer_counts.get(developer, 0) + 1
    return jsonify({"news_by_day": [{"date": date, "count": count} for date, count in sorted(by_day.items())], "new_tools": sum(f["type"] == "tool" for f in facts), "new_updates": sum(f["type"] == "update" for f in facts), "new_pricing": sum(f["type"] == "pricing" for f in facts), "top_developers": [{"name": name, "count": count} for name, count in sorted(developer_counts.items(), key=lambda item: item[1], reverse=True)[:10]]})


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
