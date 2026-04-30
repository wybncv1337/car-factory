from abc import ABC, abstractmethod
import requests
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.database.db_manager import DatabaseManager

class BaseCollector(ABC):
    def __init__(self, db_path='car_factory.db'):
        self.db = DatabaseManager(db_path)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.timeout = 15
    
    @abstractmethod
    def fetch(self, url):
        pass
    
    def collect(self, source):
        source_id, company_id, source_type, url, name, company_name = source
        
        print(f"\n📡 [{company_name}] {name or url}")
        
        try:
            content, status = self.fetch(url)
            self.db.save_raw_doc(source_id, content, status)
            print(f"  ✅ Успешно ({len(content)} символов)")
            return True, content
            
        except requests.exceptions.Timeout:
            self.db.add_alert(source_id, 'timeout', f'Таймаут при загрузке {url}')
            self.db.save_raw_doc(source_id, '', 0, 'Timeout')
            return False, None
            
        except requests.exceptions.ConnectionError:
            self.db.add_alert(source_id, 'connection_error', f'Ошибка соединения {url}')
            self.db.save_raw_doc(source_id, '', 0, 'Connection Error')
            return False, None
            
        except Exception as e:
            self.db.add_alert(source_id, 'parse_error', str(e))
            self.db.save_raw_doc(source_id, '', 0, str(e))
            return False, None