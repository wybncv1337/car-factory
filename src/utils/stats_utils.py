def print_statistics(stats, title="СТАТИСТИКА"):
    print(f"\n{'='*60}")
    print(f"📊 {title}")
    print('='*60)
    
    print(f"📄 Всего файлов: {stats['total_files']}")
    print(f"📄 Файлы с фактами: {stats['files_with_facts']}")
    print(f"🔍 Всего фактов: {stats['total_facts']}")
    
    if stats['total_files'] > 0:
        coverage = (stats['files_with_facts'] / stats['total_files']) * 100
        print(f"📈 Покрытие: {coverage:.1f}% файлов содержат факты")
    
    if stats['by_type']:
        print(f"\n📋 По типам фактов:")
        for fact_type, count in stats['by_type'].items():
            print(f"  {fact_type}: {count}")
    
    print(f"\n🎯 По уверенности:")
    print(f"  Высокая (≥0.9): {stats['by_confidence']['high']}")
    print(f"  Средняя (0.7-0.89): {stats['by_confidence']['medium']}")
    print(f"  Низкая (<0.7): {stats['by_confidence']['low']}")