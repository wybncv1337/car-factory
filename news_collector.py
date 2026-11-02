"""Сбор новостей с официальных страниц компаний и запись их в базу AI News.

Каждая собранная карточка получает news_url — ссылку на конкретную статью,
поэтому в интерфейсе кнопка «Читать новость» ведёт на анонс, а не на раздел.

Запуск:
    python news_collector.py                 # собрать по 5 последних статей с каждого источника
    python news_collector.py --limit 3       # меньше статей
    python news_collector.py --dry-run       # показать, что нашлось, ничего не записывая
    python news_collector.py --source OpenAI # только один источник
"""

import argparse
import csv
import json
import re
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from src.extractors.rule_engine import RuleEngine

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "ai_radar.db"
SOURCES_PATH = BASE_DIR / "sources.csv"

REQUEST_TIMEOUT = 30
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}
DELAY_BETWEEN_REQUESTS = 1.0

# Ссылки на служебные разделы новостями не считаются.
JUNK_PATH_PARTS = ("about", "careers", "jobs", "contact", "legal", "privacy", "terms", "support", "login", "signin", "subscribe", "newsletter", "authors", "tag/", "category/", "/feed")
JUNK_TITLES = {"read more", "подробнее", "learn more", "смотреть все", "view all", "subscribe", "подписаться", "share", "поделиться"}
CATEGORY_KEYWORDS = {
    "Видео": ("video", "film", "clip", "видео", "клип"),
    "Аудио": ("audio", "voice", "speech", "music", "звук", "голос", "речь"),
    "Изображения": ("image", "photo", "illustr", "изображен", "фото"),
    "Дизайн": ("design", "canvas", "дизайн", "макет"),
    "Разработка": ("code", "developer", "api", "sdk", "studio", "код", "разработк"),
    "Агенты": ("agent", "агент", "assistant", "помощник"),
    "Поиск": ("search", "поиск"),
    "Тарифы и лимиты": ("pricing", "price", "plan", "tier", "credits", "тариф", "цена", "лимит", "подписк"),
}
DEFAULT_CATEGORY = "ИИ-инструменты"
MIN_TITLE_LENGTH = 15
ISO_DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

rule_engine = RuleEngine()


def load_sources(path=SOURCES_PATH):
    """Читает sources.csv: developer, type, url, name."""
    with open(path, encoding="utf-8-sig", newline="") as csv_file:
        return [row for row in csv.DictReader(csv_file) if row.get("url")]


def is_article_link(href, base_url):
    """True, если ссылка ведёт на статью того же сайта, а не в служебный раздел."""
    if not href or href.startswith(("#", "mailto:", "javascript:", "tel:")):
        return False
    url = urljoin(base_url, href.split("#")[0])
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or parsed.netloc != urlparse(base_url).netloc:
        return False
    if parsed.path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".pdf", ".mp4", ".xml", ".json", ".rss", ".zip")):
        return False
    if len([part for part in parsed.path.lower().split("/") if part]) < 2:
        return False
    return not any(junk in parsed.path.lower() for junk in JUNK_PATH_PARTS)


def detect_category(text):
    lowered = (text or "").lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return category
    return DEFAULT_CATEGORY


def parse_date(text):
    match = ISO_DATE.search(text or "")
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%Y-%m-%d")
    except ValueError:
        return None


def article_title(anchor):
    alt = anchor.img.get("alt", "") if anchor.img else ""
    return " ".join((anchor.get_text(" ", strip=True) or anchor.get("aria-label", "") or alt).split())


def extract_articles(html, base_url, limit=5):
    """Достаёт из страницы-раздела заголовки и ссылки последних статей."""
    soup = BeautifulSoup(html, "html.parser")
    articles, seen = [], set()
    for anchor in soup.find_all("a", href=True):
        if not is_article_link(anchor["href"], base_url):
            continue
        title = article_title(anchor)
        if len(title) < MIN_TITLE_LENGTH or title.lower().strip() in JUNK_TITLES:
            continue
        url = urljoin(base_url, anchor["href"].split("#")[0])
        if url in seen:
            continue
        seen.add(url)
        container = anchor.find_parent(["article", "li"]) or anchor
        published = container.find("time") or (anchor.find_parent("article") or anchor).find("time")
        articles.append({"title": title, "url": url, "published_at": parse_date(str(published)) if published else None})
        if len(articles) >= limit:
            break
    return articles


def extract_summary(html):
    """Первые содержательные абзацы статьи — они идут в описание карточки."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form", "noscript"]):
        tag.decompose()
    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p") if len(p.get_text(" ", strip=True)) > 60]
    return " ".join(paragraphs[:3])[:500]


def fetch(url, session):
    response = session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


def build_fact(developer, article, summary):
    """Собирает поля строки facts из найденной статьи.

    source_url остаётся пустым: страница-раздел в нём только запутала бы кнопку
    «Сайт продукта», а адрес статьи уже лежит в news_url.
    """
    text = f"{article['title']} {summary}"
    data = {
        "name": article["title"][:120],
        "developer": developer,
        "category": detect_category(text),
        "description": (summary or article["title"])[:300],
        "value": f"{developer}: {article['title']}"[:300],
    }
    created_at = article["published_at"] or datetime.now()
    return {
        "type": rule_engine.detect_fact_type(text),
        "fact_data": json.dumps(data, ensure_ascii=False),
        "confidence": 0.7,
        "news_url": article["url"],
        "created_at": created_at.strftime(DATE_FORMAT),
    }


def save_fact(connection, fact):
    """INSERT OR IGNORE: повторный запуск не создаёт дублей одной и той же статьи."""
    cursor = connection.execute(
        "INSERT OR IGNORE INTO facts (type, fact_data, confidence, news_url, created_at, is_demo) VALUES (?, ?, ?, ?, ?, 0)",
        (fact["type"], fact["fact_data"], fact["confidence"], fact["news_url"], fact["created_at"]),
    )
    return cursor.rowcount


def connect(db_path=DB_PATH):
    """База должна быть создана приложением: колонки сборщика появляются в init_db."""
    from app import init_db

    if not Path(db_path).exists():
        init_db()
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS facts_news_url ON facts(news_url) WHERE news_url IS NOT NULL")
    return connection


def collect(source, session, connection, limit, dry_run=False):
    """Собирает статьи одного источника; возвращает (найдено, записано)."""
    developer, listing_url = source["developer"], source["url"]
    try:
        articles = extract_articles(fetch(listing_url, session), listing_url, limit)
    except requests.RequestException as error:
        print(f"   ⚠️ {developer}: раздел недоступен ({error.__class__.__name__})")
        return 0, 0

    saved = 0
    for article in articles:
        try:
            summary = extract_summary(fetch(article["url"], session))
        except requests.RequestException as error:
            summary = ""
            print(f"   ⚠️ {developer}: текст статьи не загружен ({error.__class__.__name__})")
        fact = build_fact(developer, article, summary)
        if dry_run:
            print(f"   • [{fact['type']}] {article['title'][:60]} → {article['url']}")
            continue
        saved += save_fact(connection, fact)
        time.sleep(DELAY_BETWEEN_REQUESTS)
    return len(articles), saved


def main():
    parser = argparse.ArgumentParser(description="Сбор новостей об ИИ с официальных страниц компаний")
    parser.add_argument("--limit", type=int, default=5, help="сколько статей брать с одного источника")
    parser.add_argument("--source", help="собрать только указанный источник (например, OpenAI)")
    parser.add_argument("--dry-run", action="store_true", help="показать найденные статьи, не записывая их в базу")
    args = parser.parse_args()

    sources = load_sources()
    if args.source:
        sources = [row for row in sources if row["developer"].lower() == args.source.lower()]
    if not sources:
        print("Подходящий источник не найден в sources.csv.")
        return 1

    connection = None if args.dry_run else connect()
    session = requests.Session()
    found = written = 0
    for source in sources:
        print(f"\n📡 {source['developer']}: {source['url']}")
        source_found, source_saved = collect(source, session, connection, args.limit, args.dry_run)
        found += source_found
        written += source_saved
        time.sleep(DELAY_BETWEEN_REQUESTS)

    if connection:
        connection.commit()
        connection.close()
    print(f"\n✅ Найдено статей: {found}, новых карточек: {written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
