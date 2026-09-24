# src/collectors/collector_manager.py
from src.database.db_manager import DatabaseManager
from .html_collector import HTMLCollector


class CollectorManager:
    def __init__(self, db_path='car_factory.db'):
        self.db = DatabaseManager(db_path)
        self.db.init_db()
        self.html = HTMLCollector(self.db)

    def collect_all(self):
        print("\n" + "=" * 60)
        print("📊 НАЧАЛО СБОРА ДАННЫХ")
        print("=" * 60)

        html_results = self.html.collect_all()

        return {'html': html_results, 'rss': []}