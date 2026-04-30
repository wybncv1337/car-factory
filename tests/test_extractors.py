"""Тест: на 100 текстах найти ≥ 60% фактов"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extractors.rule_engine import RuleEngine
from src.utils.stats_utils import print_statistics
from tests.test_generator import TestDataGenerator

def run_test():
    print("="*60)
    print("🧪 ТЕСТ ИЗВЛЕЧЕНИЯ ФАКТОВ")
    print("="*60)
    
    generator = TestDataGenerator()
    expected_facts = generator.generate_dataset(100, fact_ratio=0.33)
    
    engine = RuleEngine()
    results = engine.extract_from_folder('data/test')
    engine.save_results(results, 'results/test_results.json')
    
    stats = engine.get_statistics(results)
    print_statistics(stats, "РЕЗУЛЬТАТЫ ТЕСТА")
    
    found_facts = stats['total_facts']
    if expected_facts > 0:
        percent = (found_facts / expected_facts) * 100
        print(f"\n🎯 Ожидалось фактов: {expected_facts}")
        print(f"🔍 Найдено фактов: {found_facts}")
        print(f"📊 Процент обнаружения: {percent:.1f}%")
        
        if percent >= 60:
            print("\n✅ ТЕСТ ПРОЙДЕН: >= 60% фактов найдено")
            return True
        else:
            print("\n❌ ТЕСТ НЕ ПРОЙДЕН: меньше 60%")
            return False
    return False

if __name__ == '__main__':
    run_test()