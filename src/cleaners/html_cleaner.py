import re
from bs4 import BeautifulSoup

class HTMLCleaner:
    def clean_html(self, html_content):
        """Очистка HTML от тегов"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for script in soup(["script", "style", "meta", "link", "noscript"]):
            script.decompose()
        
        for h1 in soup.find_all('h1'):
            h1.decompose()
        
        for header in soup.find_all('header'):
            header.decompose()
        for footer in soup.find_all('footer'):
            footer.decompose()
        
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text.strip()
    
    def normalize_for_hash(self, text):
        """Нормализация для хэша (удаляем цифры)"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\d+', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def get_text_hash(self, text):
        import hashlib
        normalized = self.normalize_for_hash(text)
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    
    def clean_file(self, raw_content):
        clean_text = self.clean_html(raw_content)
        text_hash = self.get_text_hash(clean_text)
        return clean_text, text_hash