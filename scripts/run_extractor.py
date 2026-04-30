import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.extractors.rule_engine import RuleEngine
from src.utils.stats_utils import print_statistics

def main():
    print("="*60)
    print("🔍 ИЗВЛЕЧЕНИЕ ФАКТОВ")
    print("="*60)
    
    print("\nВыберите источник:")
    print("1. Из clean_docs (из базы данных)")
    print("2. Из папки с файлами")
    
    choice = input("\nВаш выбор (1-2): ").strip()
    
    engine = RuleEngine('car_factory.db')
    
    if choice == '1':
        facts = engine.extract_from_clean_docs()
        print(f"\n✅ Извлечено фактов: {len(facts)}")
        
    elif choice == '2':
        folder = input("Введите путь к папке (Enter = data/input): ").strip()
        if not folder:
            folder = 'data/input'
        
        results = engine.extract_from_folder(folder)
        stats = engine.get_statistics(results)
        print_statistics(stats)
        engine.save_results(results)
    
    else:
        print("❌ Неверный выбор")

if __name__ == '__main__':
    main()