"""Офлайн-проверка сборщика новостей: разбор страницы, классификация и запись в базу.

Запуск: python -m unittest tests.test_news_collector
"""

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import app
import demo_data
import news_collector

LISTING_HTML = """
<html><body>
  <nav><a href="/about-us">About the company</a><a href="/tags/ai">AI tag page</a></nav>
  <ul>
    <li><article><a href="/news/2026-11-01/video-model-4"><h3>Video Model 4 generates longer clips</h3></a><time datetime="2026-11-01T09:00:00Z">1 Nov</time></article></li>
    <li><article><a href="/news/2026-10-20/new-pricing-plans"><h3>New pricing plans and free tier limits</h3></a></article></li>
    <li><article><a href="/news/2026-10-18/short"><h3>Short</h3></a></article></li>
    <li><article><a href="/news/2026-10-17/hero.png"><img alt="Illustration of the release banner"></a></article></li>
    <li><article><a href="https://other.example.com/news/partner">Partner announcement on another domain</a></article></li>
    <li><article><a href="#top">Read more</a></article></li>
  </ul>
</body></html>
"""

ARTICLE_HTML = """
<html><body><header><p>Menu text</p></header>
<article>
  <p>The release adds a video model that renders longer clips and keeps character consistency across scenes.</p>
  <p>Teams can now preview results inside the editor and export them without leaving the workspace.</p>
</article>
<footer><p>Cookie notice text that is long enough to be filtered out of the summary by position.</p></footer>
</body></html>
"""

BASE_URL = "https://example.com/news/"


class ExtractTests(unittest.TestCase):
    def test_picks_only_real_articles(self):
        articles = news_collector.extract_articles(LISTING_HTML, BASE_URL, limit=5)
        self.assertEqual([a["url"] for a in articles], [
            "https://example.com/news/2026-11-01/video-model-4",
            "https://example.com/news/2026-10-20/new-pricing-plans",
        ])

    def test_reads_publication_date_from_time_tag(self):
        articles = news_collector.extract_articles(LISTING_HTML, BASE_URL, limit=1)
        self.assertEqual(articles[0]["published_at"], datetime(2026, 11, 1))

    def test_falls_back_to_image_alt_when_anchor_empty(self):
        html = '<a href="/news/2026-10-17/hero-post"><img alt="Illustration of the release banner"></a>'
        articles = news_collector.extract_articles(html, BASE_URL, limit=1)
        self.assertEqual(articles[0]["title"], "Illustration of the release banner")

    def test_limit_caps_number_of_articles(self):
        articles = news_collector.extract_articles(LISTING_HTML, BASE_URL, limit=1)
        self.assertEqual(len(articles), 1)

    def test_summary_skips_chrome_and_keeps_paragraphs(self):
        summary = news_collector.extract_summary(ARTICLE_HTML)
        self.assertIn("video model", summary)
        self.assertNotIn("Cookie notice", summary)


class FactTests(unittest.TestCase):
    def test_pricing_news_becomes_pricing_fact(self):
        article = {"title": "New pricing plans and free tier limits", "url": "https://example.com/news/p", "published_at": None}
        fact = news_collector.build_fact("Example", article, "Plans now include a free tier.")
        self.assertEqual(fact["type"], "pricing")
        self.assertEqual(fact["news_url"], article["url"])
        self.assertNotIn("source_url", fact, "у собранной новости нет ссылки на продукт, только на статью")

    def test_category_from_keywords(self):
        self.assertEqual(news_collector.detect_category("Video model for creators"), "Видео")
        self.assertEqual(news_collector.detect_category("Nothing related here"), "ИИ-инструменты")


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = Path(self.tmp.name) / "ai_radar.db"
        self.original_db_path = app.DB_PATH
        app.DB_PATH = self.db_path
        app.init_db()

    def tearDown(self):
        app.DB_PATH = self.original_db_path
        self.tmp.cleanup()

    def test_seed_marks_rows_as_demo(self):
        connection = news_collector.connect(self.db_path)
        demo = connection.execute("SELECT COUNT(*) FROM facts WHERE is_demo = 1").fetchone()[0]
        collected = connection.execute("SELECT COUNT(*) FROM facts WHERE is_demo = 0").fetchone()[0]
        connection.close()
        self.assertEqual(demo, len(demo_data.DEMO_FACTS))
        self.assertEqual(collected, 0)

    def test_collected_fact_survives_reseed_and_dedupes(self):
        connection = news_collector.connect(self.db_path)
        article = {"title": "Video Model 4 generates longer clips", "url": "https://example.com/news/v4", "published_at": datetime(2026, 11, 1)}
        fact = news_collector.build_fact("Example", article, "Longer clips with consistent characters.")
        self.assertEqual(news_collector.save_fact(connection, fact), 1)
        self.assertEqual(news_collector.save_fact(connection, fact), 0, "повтор не должен создавать дубль")
        connection.commit()

        app.init_db()  # пересид демо-витрины не трогает собранные карточки
        rows = connection.execute("SELECT news_url FROM facts WHERE is_demo = 0").fetchall()
        self.assertEqual([row["news_url"] for row in rows], ["https://example.com/news/v4"])

        demo_row = connection.execute("SELECT * FROM facts WHERE is_demo = 1 LIMIT 1").fetchone()
        # У демо-карточек своей ссылки на статью нет, поэтому берётся страница новостей компании.
        self.assertTrue(app.row_to_fact(demo_row)["news_url"])
        collected_row = connection.execute("SELECT * FROM facts WHERE is_demo = 0 LIMIT 1").fetchone()
        self.assertEqual(app.row_to_fact(collected_row)["news_url"], "https://example.com/news/v4")
        connection.close()


class CollectTests(unittest.TestCase):
    """Прогон collect() с подменой сети: проверка записи и защиты от дублей."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = Path(self.tmp.name) / "ai_radar.db"
        self.original_db_path = app.DB_PATH
        app.DB_PATH = self.db_path
        app.init_db()
        self.original_fetch = news_collector.fetch
        pages = {BASE_URL: LISTING_HTML}
        for article in news_collector.extract_articles(LISTING_HTML, BASE_URL, limit=5):
            pages[article["url"]] = ARTICLE_HTML
        news_collector.fetch = lambda url, session: pages[url]
        news_collector.DELAY_BETWEEN_REQUESTS = 0
        self.connection = news_collector.connect(self.db_path)
        self.source = {"developer": "Example", "url": BASE_URL, "name": "Новости Example"}

    def tearDown(self):
        news_collector.fetch = self.original_fetch
        news_collector.DELAY_BETWEEN_REQUESTS = 1.0
        self.connection.close()
        app.DB_PATH = self.original_db_path
        self.tmp.cleanup()

    def test_writes_collected_articles_as_non_demo(self):
        found, saved = news_collector.collect(self.source, None, self.connection, limit=5)
        self.connection.commit()
        rows = self.connection.execute("SELECT news_url, type FROM facts WHERE is_demo = 0").fetchall()
        self.assertEqual((found, saved), (2, 2))
        self.assertEqual(len(rows), 2)

    def test_second_run_adds_nothing(self):
        news_collector.collect(self.source, None, self.connection, limit=5)
        self.connection.commit()
        _, saved = news_collector.collect(self.source, None, self.connection, limit=5)
        self.connection.commit()
        self.assertEqual(saved, 0)

    def test_unreachable_listing_is_skipped(self):
        def fail(url, session):
            raise news_collector.requests.RequestException("offline")

        news_collector.fetch = fail
        found, saved = news_collector.collect(self.source, None, self.connection, limit=5)
        self.assertEqual((found, saved), (0, 0))


class MetricsTests(unittest.TestCase):
    """Разбивка по дням для графика: полное окно, нули в затишье и counts по типам."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = Path(self.tmp.name) / "ai_radar.db"
        self.original_db_path = app.DB_PATH
        app.DB_PATH = self.db_path
        app.init_db()

    def tearDown(self):
        app.DB_PATH = self.original_db_path
        self.tmp.cleanup()

    def test_window_covers_every_day_of_schedule(self):
        with app.get_db() as conn:
            stats = app.daily_breakdown(conn)
        self.assertEqual([item["date"] for item in stats][-1], datetime.now().strftime("%Y-%m-%d"))
        self.assertEqual([item["total"] for item in stats], list(reversed(demo_data.DAILY_COUNTS)))

    def test_events_match_the_day_schedule(self):
        self.assertEqual(len(demo_data.DAILY_COUNTS), app.DAYS_WINDOW)
        self.assertEqual(len(demo_data.DEMO_FACTS), sum(demo_data.DAILY_COUNTS))
        self.assertEqual([fact[3] for fact in demo_data.DEMO_FACTS], list(demo_data.day_schedule(len(demo_data.DEMO_FACTS))))

    def test_each_day_splits_into_types(self):
        with app.get_db() as conn:
            stats = app.daily_breakdown(conn)
        for item in stats:
            self.assertEqual(item["tool"] + item["update"] + item["pricing"], item["total"])
        self.assertEqual(sum(item["total"] for item in stats), len(demo_data.DEMO_FACTS))


if __name__ == "__main__":
    unittest.main()
