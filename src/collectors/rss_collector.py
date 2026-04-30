from .base_collector import BaseCollector

class RSSCollector(BaseCollector):
    def fetch(self, url):
        response = self.session.get(url, timeout=self.timeout)
        response.encoding = 'utf-8'
        return response.text, response.status_code
    
    def collect_all(self):
        sources = self.db.get_active_sources('rss')
        print(f"\n🔍 Найдено RSS-источников: {len(sources)}")
        
        results = []
        for source in sources:
            success, content = self.collect(source)
            results.append({
                'source': source[3],
                'success': success,
                'content': content
            })
        
        return results