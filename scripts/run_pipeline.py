"""Запуск всего пайплайна: сбор → очистка → дедупликация → извлечение"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.collectors.collector_manager import CollectorManager
from src.deduplicators.hash_deduplicator import HashDeduplicator
from src.extractors.rule_engine import RuleEngine
from src.database.db_manager import DatabaseManager
from src.utils.logger import setup_logger

def main():
    logger = setup_logger('pipeline')
    
    print("="*60)
    print("🏭 ЗАПУСК ПОЛНОГО ПАЙПЛАЙНА")
    print("="*60)
    
    print("\n📡 ШАГ 1: Сбор данных")
    collector = CollectorManager()
    collect_results = collector.collect_all()
    
    print("\n🔄 ШАГ 2: Дедупликация")
    dedup = HashDeduplicator('car_factory.db')
    clean_docs = dedup.process_all_raw()
    
    print("\n🔍 ШАГ 3: Извлечение фактов")
    engine = RuleEngine('car_factory.db')
    facts = engine.extract_from_clean_docs()
    
    db = DatabaseManager('car_factory.db')
    stats = db.get_stats()
    
    print("\n" + "="*60)
    print("📊 ИТОГИ РАБОТЫ")
    print("="*60)
    print(f"📡 Собрано сырых документов: {stats['raw_docs']}")
    print(f"🔄 Очищено уникальных: {stats['clean_docs']}")
    print(f"🔍 Извлечено фактов: {stats['facts']}")
    
    if stats['facts_by_type']:
        print(f"\n📋 По типам фактов:")
        for t, count in stats['facts_by_type'].items():
            print(f"  {t}: {count}")
    
    print(f"\n⚠️ Активных ошибок: {stats['active_alerts']}")
    print("\n✅ Пайплайн завершён!")

if __name__ == '__main__':
    main()