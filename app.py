"""НейроРадар — веб-приложение для мониторинга ИИ-инструментов."""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "ai_radar.db"
app = Flask(__name__, template_folder=str(BASE_DIR / "templates"), static_folder=str(BASE_DIR / "static"))
CORS(app)


def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    """Создаёт базу НейроРадара и добавляет недостающие демонстрационные карточки."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL CHECK(type IN ('tool', 'update', 'pricing')),
                fact_data TEXT NOT NULL,
                confidence REAL NOT NULL DEFAULT 0.8,
                source_url TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
        now = datetime.now()
        demo_facts = [
            ("tool", {"name": "ChatGPT", "developer": "OpenAI", "category": "Текст и анализ", "description": "Помогает составлять тексты, анализировать документы и искать идеи.", "price": "Есть бесплатный тариф", "value": "ChatGPT — ИИ-помощник для текста, анализа и рабочих задач."}, "https://chatgpt.com", 0),
            ("tool", {"name": "Canva AI", "developer": "Canva", "category": "Дизайн", "description": "Создаёт макеты, изображения и презентации по описанию.", "price": "Есть бесплатный тариф", "value": "Canva AI — инструмент для дизайна, постов и презентаций."}, "https://www.canva.com", 1),
            ("tool", {"name": "GitHub Copilot", "developer": "GitHub", "category": "Разработка", "description": "Подсказывает код и объясняет ошибки прямо в редакторе.", "price": "Платный, есть пробный период", "value": "GitHub Copilot — ИИ-помощник для написания кода."}, "https://github.com/features/copilot", 2),
            ("update", {"name": "Обновление генерации изображений", "developer": "Adobe", "category": "Дизайн", "description": "Добавлены более точные настройки стиля и редактирование отдельных областей изображения.", "value": "Adobe обновила функции ИИ-генерации изображений."}, "https://www.adobe.com", 3),
            ("pricing", {"name": "Изменение лимитов", "developer": "Notion", "category": "Продуктивность", "description": "Обновлены лимиты использования ИИ-функций в рабочих пространствах.", "price": "Проверьте условия своего тарифа", "value": "Notion изменила лимиты ИИ-функций в тарифах."}, "https://www.notion.so", 4),
            ("update", {"name": "Новая функция транскрибации", "developer": "Zoom", "category": "Встречи", "description": "ИИ автоматически делает краткое содержание разговора и список задач.", "value": "Zoom добавил ИИ-резюме встреч и задачи."}, "https://www.zoom.com", 5),
            ("tool", {"name": "Claude", "developer": "Anthropic", "category": "Текст и анализ", "description": "Помогает работать с большими текстами, документами и структурированием информации.", "price": "Есть бесплатный тариф", "value": "Claude — ИИ-ассистент для анализа документов и работы с текстом."}, "https://claude.ai", 6),
            ("tool", {"name": "Gemini", "developer": "Google", "category": "Текст и мультимедиа", "description": "ИИ-помощник Google для работы с текстом, изображениями и задачами.", "price": "Есть бесплатный тариф", "value": "Gemini — мультимодальный ИИ-помощник от Google."}, "https://gemini.google.com", 7),
            ("tool", {"name": "Microsoft Copilot", "developer": "Microsoft", "category": "Продуктивность", "description": "Помощник для рабочих задач и приложений Microsoft.", "price": "Зависит от тарифа Microsoft 365", "value": "Microsoft Copilot — ИИ-помощник для рабочих задач."}, "https://copilot.microsoft.com", 8),
            ("tool", {"name": "Perplexity", "developer": "Perplexity", "category": "Поиск и анализ", "description": "Поисковый ИИ-сервис с ответами и ссылками на источники.", "price": "Есть бесплатный тариф", "value": "Perplexity — ИИ-поиск с источниками."}, "https://www.perplexity.ai", 9),
            ("tool", {"name": "Midjourney", "developer": "Midjourney", "category": "Изображения", "description": "Генерирует иллюстрации и визуальные концепты по текстовому описанию.", "price": "Платная подписка", "value": "Midjourney — генератор изображений по тексту."}, "https://www.midjourney.com", 10),
            ("tool", {"name": "Runway", "developer": "Runway", "category": "Видео", "description": "Помогает создавать и редактировать видео с помощью ИИ.", "price": "Есть бесплатный тариф", "value": "Runway — ИИ-инструмент для создания видео."}, "https://runwayml.com", 11),
            ("tool", {"name": "ElevenLabs", "developer": "ElevenLabs", "category": "Аудио", "description": "Создаёт реалистичную озвучку и синтез речи.", "price": "Есть бесплатный тариф", "value": "ElevenLabs — ИИ-сервис для генерации голоса."}, "https://elevenlabs.io", 12),
            ("tool", {"name": "Hugging Face", "developer": "Hugging Face", "category": "Разработка", "description": "Платформа с открытыми моделями, датасетами и инструментами для разработчиков.", "price": "Есть бесплатные возможности", "value": "Hugging Face — платформа для работы с ИИ-моделями."}, "https://huggingface.co", 13),
            ("tool", {"name": "Le Chat", "developer": "Mistral AI", "category": "Текст и анализ", "description": "Чат-ассистент для работы с текстом и повседневными задачами.", "price": "Есть бесплатный тариф", "value": "Le Chat — ИИ-ассистент от Mistral AI."}, "https://chat.mistral.ai", 14),
            ("tool", {"name": "Grok", "developer": "xAI", "category": "Текст и анализ", "description": "ИИ-ассистент для ответов на вопросы и работы с информацией.", "price": "Зависит от тарифа сервиса", "value": "Grok — ИИ-ассистент от xAI."}, "https://grok.com", 15),
            ("tool", {"name": "Figma AI", "developer": "Figma", "category": "Дизайн", "description": "Помогает создавать интерфейсы, тексты и визуальные элементы в Figma.", "price": "Зависит от тарифа Figma", "value": "Figma AI — ИИ-функции для проектирования интерфейсов."}, "https://www.figma.com", 16),
            ("tool", {"name": "Grammarly", "developer": "Grammarly", "category": "Текст", "description": "Проверяет и улучшает англоязычные тексты, письма и документы.", "price": "Есть бесплатный тариф", "value": "Grammarly — ИИ-помощник для редактирования текста."}, "https://www.grammarly.com", 17),
            ("tool", {"name": "YandexGPT", "developer": "Яндекс", "category": "Текст и анализ", "description": "Русскоязычная языковая модель для генерации и обработки текста.", "price": "Доступность зависит от сервиса", "value": "YandexGPT — русскоязычная ИИ-модель от Яндекса."}, "https://yandex.ru/project/yandexgpt", 18),
            ("tool", {"name": "GigaChat", "developer": "Сбер", "category": "Текст и анализ", "description": "Российский ИИ-ассистент для общения, генерации текста и рабочих задач.", "price": "Условия зависят от сервиса", "value": "GigaChat — ИИ-ассистент от Сбера."}, "https://developers.sber.ru/portal/products/gigachat", 19),
        ]
        for fact_type, data, url, days_ago in demo_facts:
            exists = conn.execute("SELECT 1 FROM facts WHERE fact_data LIKE ?", (f'%"name": "{data["name"]}"%',)).fetchone()
            if exists:
                continue
            created_at = (now - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
            conn.execute("INSERT INTO facts (type, fact_data, confidence, source_url, created_at) VALUES (?, ?, ?, ?, ?)", (fact_type, json.dumps(data, ensure_ascii=False), 0.9, url, created_at))


def row_to_fact(row):
    try:
        data = json.loads(row["fact_data"])
    except (TypeError, json.JSONDecodeError):
        data = {"value": row["fact_data"]}
    return {"id": row["id"], "type": row["type"], "data": data, "confidence": row["confidence"], "source_url": row["source_url"], "created_at": row["created_at"]}


@app.route("/")
def index(): return render_template("index.html")

@app.route("/facts-feed")
def facts_feed_page(): return render_template("facts_feed.html")

@app.route("/developers")
def developers_page(): return render_template("companies.html")

@app.route("/developer/<developer_name>")
def developer_page(developer_name): return render_template("company.html", developer=developer_name)

@app.route("/weekly-summary")
def weekly_summary_page(): return render_template("weekly_summary.html")


@app.route("/api/metrics")
def get_metrics():
    with get_db() as conn:
        counts = {row["type"]: row["count"] for row in conn.execute("SELECT type, COUNT(*) AS count FROM facts GROUP BY type")}
        daily_rows = conn.execute("SELECT DATE(created_at) AS date, COUNT(*) AS count FROM facts GROUP BY DATE(created_at) ORDER BY date").fetchall()
    return jsonify({"total_facts": sum(counts.values()), "total_tools": counts.get("tool", 0), "total_updates": counts.get("update", 0), "total_pricing": counts.get("pricing", 0), "daily_stats": [dict(row) for row in daily_rows]})


@app.route("/api/facts")
def get_facts():
    limit, offset = min(request.args.get("limit", 20, type=int), 100), max(request.args.get("offset", 0, type=int), 0)
    fact_type, developer = request.args.get("type", "").strip(), request.args.get("developer", "").strip()
    clauses, params = [], []
    if fact_type in {"tool", "update", "pricing"}: clauses.append("type = ?"); params.append(fact_type)
    if developer: clauses.append("fact_data LIKE ?"); params.append(f"%{developer}%")
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    with get_db() as conn:
        rows = conn.execute(f"SELECT * FROM facts{where} ORDER BY datetime(created_at) DESC, id DESC LIMIT ? OFFSET ?", params + [limit, offset]).fetchall()
        total = conn.execute(f"SELECT COUNT(*) FROM facts{where}", params).fetchone()[0]
    return jsonify({"facts": [row_to_fact(row) for row in rows], "total": total, "limit": limit, "offset": offset, "total_pages": max(1, (total + limit - 1) // limit)})


@app.route("/api/developers")
def get_developers():
    with get_db() as conn: rows = conn.execute("SELECT fact_data FROM facts").fetchall()
    developers = set()
    for row in rows:
        try:
            developer = json.loads(row["fact_data"]).get("developer")
            if developer: developers.add(developer)
        except (TypeError, json.JSONDecodeError): pass
    return jsonify(sorted(developers))


@app.route("/api/developer/<developer_name>")
def get_developer_facts(developer_name):
    with get_db() as conn: rows = conn.execute("SELECT * FROM facts WHERE fact_data LIKE ? ORDER BY datetime(created_at) DESC", (f"%{developer_name}%",)).fetchall()
    facts = [row_to_fact(row) for row in rows]
    return jsonify({"developer": developer_name, "facts": facts, "stats": {"total": len(facts), "tools": sum(f["type"] == "tool" for f in facts), "updates": sum(f["type"] == "update" for f in facts), "pricing": sum(f["type"] == "pricing" for f in facts)}})


@app.route("/api/weekly-summary")
def get_weekly_summary():
    start_date = datetime.now() - timedelta(days=7)
    with get_db() as conn: rows = conn.execute("SELECT * FROM facts WHERE datetime(created_at) >= ? ORDER BY datetime(created_at)", (start_date.strftime("%Y-%m-%d %H:%M:%S"),)).fetchall()
    facts, by_day, developer_counts = [row_to_fact(row) for row in rows], {}, {}
    for fact in facts:
        by_day[fact["created_at"][:10]] = by_day.get(fact["created_at"][:10], 0) + 1
        developer = fact["data"].get("developer")
        if developer: developer_counts[developer] = developer_counts.get(developer, 0) + 1
    return jsonify({"news_by_day": [{"date": date, "count": count} for date, count in sorted(by_day.items())], "new_tools": sum(f["type"] == "tool" for f in facts), "new_updates": sum(f["type"] == "update" for f in facts), "new_pricing": sum(f["type"] == "pricing" for f in facts), "top_developers": [{"name": name, "count": count} for name, count in sorted(developer_counts.items(), key=lambda item: item[1], reverse=True)[:10]]})


init_db()

if __name__ == "__main__": app.run(host="0.0.0.0", port=5000, debug=True)
