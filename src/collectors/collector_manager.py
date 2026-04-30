from .html_collector import HTMLCollector
from .rss_collector import RSSCollector

class CollectorManager:
    def __init__(self):
        self.html = HTMLCollector()
        self.rss = RSSCollector()
    
    def collect_all(self):
        print("\n" + "="*60)
        print("📊 НАЧАЛО СБОРА ДАННЫХ")
        print("="*60)
        
        html_results = self.html.collect_all()
        rss_results = self.rss.collect_all()
        
        total = len(html_results) + len(rss_results)
        success = sum(1 for r in html_results + rss_results if r['success'])
        
        print("\n" + "="*60)
        print("📈 ИТОГИ СБОРА")
        print("="*60)
        print(f"Всего источников: {total}")
        print(f"Успешно: {success}")
        print(f"Ошибок: {total - success}")
        if total > 0:
            print(f"✅ Успешность: {success/total*100:.1f}%")
        
        return {
            'total': total,
            'success': success,
            'errors': total - success,
            'html_results': html_results,
            'rss_results': rss_results
        }
    
    def collect_by_type(self, source_type):
        if source_type == 'html':
            return self.html.collect_all()
        elif source_type == 'rss':
            return self.rss.collect_all()
        else:
            print(f"❌ Неизвестный тип: {source_type}")
            return []