#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.collectors.collector_manager import CollectorManager
from src.deduplicators.hash_deduplicator import HashDeduplicator
from src.extractors.rule_engine import RuleEngine


def main():
    print("=" * 60)
    print("🏭 ЗАПУСК ПОЛНОГО ПАЙПЛАЙНА")
    print("=" * 60)


    print("\n📡 ШАГ 1: Сбор данных")
    collector = CollectorManager()
    collect_results = collector.collect_all()


    print("\n🔄 ШАГ 2: Дедупликация")
    dedup = HashDeduplicator('car_factory.db')
    dedup.process_all_raw()


    print("\n🔍 ШАГ 3: Извлечение фактов")
    engine = RuleEngine('car_factory.db')
    facts = engine.extract_from_clean_docs()

    print("\n" + "=" * 60)
    print("✅ ПАЙПЛАЙН ЗАВЕРШЁН")
    print(f"📊 Всего фактов: {len(facts)}")
    print("=" * 60)


if __name__ == "__main__":
    main()