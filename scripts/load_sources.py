import csv
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.database.db_manager import DatabaseManager

def load_sources(csv_file='sources.csv'):
    db = DatabaseManager('car_factory.db')
    
    companies = set()
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            companies.add(row['company'])
    
    print(f"🏢 Добавляем компании:")
    for company in companies:
        db.add_company(company)
        print(f"  - {company}")
    
    print(f"\n📡 Добавляем источники:")
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            db.add_source(row['company'], row['type'], row['url'], row.get('name', ''))
    
    stats = db.get_stats()
    print(f"\n📊 Статистика: всего источников {stats['sources']}")

if __name__ == '__main__':
    print("="*50)
    print("📥 ЗАГРУЗКА ИСТОЧНИКОВ")
    print("="*50)
    load_sources()