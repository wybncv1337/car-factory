import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.collectors.collector_manager import CollectorManager

def main():
    print("="*60)
    print("📡 ЗАПУСК СБОРА ДАННЫХ")
    print("="*60)
    
    collector = CollectorManager()
    results = collector.collect_all()
    
    print(f"\n✅ Сбор завершён. Успешно: {results['success']}/{results['total']}")

if __name__ == '__main__':
    main()