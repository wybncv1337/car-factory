import re
from bs4 import BeautifulSoup


def clean_html(html_content):
    """Удаляет весь мусор из HTML и оставляет только текст новостей"""
    if not html_content:
        return ""

    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Удаляем скрипты, стили, навигацию, футеры
        for tag in soup(['script', 'style', 'nav', 'footer', 'header',
                         'aside', 'iframe', 'noscript', 'form']):
            tag.decompose()

        # Извлекаем текст
        text = soup.get_text(separator=' ')

        # Убираем лишние пробелы
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        # Удаляем очень короткие строки (мусор)
        lines = text.split('.')
        good_lines = [line.strip() for line in lines if len(line.strip()) > 30]

        return '. '.join(good_lines)
    except Exception as e:
        print(f"Ошибка очистки HTML: {e}")
        return ""


def extract_news_text(html_content):
    """Извлекает только текст новостей из HTML"""
    if not html_content:
        return []

    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Удаляем мусор
        for tag in soup(['script', 'style', 'nav', 'footer', 'header',
                         'aside', 'iframe', 'noscript', 'form', 'menu']):
            tag.decompose()

        # Ищем блоки с новостями
        news_blocks = []

        # Ищем article, .news, .post и т.д.
        for selector in ['article', '.news-item', '.post', '.article',
                         '.news', '[class*="news"]', '[class*="article"]']:
            for element in soup.select(selector):
                text = element.get_text(separator=' ').strip()
                text = re.sub(r'\s+', ' ', text)
                if len(text) > 50:
                    news_blocks.append(text)

        # Если ничего не нашли — берём весь текст
        if not news_blocks:
            text = soup.get_text(separator=' ')
            text = re.sub(r'\s+', ' ', text)
            news_blocks = [text]

        return news_blocks
    except Exception as e:
        print(f"Ошибка: {e}")
        return []