import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.deduplicators.hash_deduplicator import HashDeduplicator

def main():
    print("="*60)
    print("🔄 ЗАПУСК ДЕДУПЛИКАЦИИ")
    print("="*60)
    
    dedup = HashDeduplicator('car_factory.db')
    results = dedup.process_all_raw()
    
    print(f"\n✅ Дедупликация завершена. Новых уникальных документов: {len(results)}")

if __name__ == '__main__':
    main()