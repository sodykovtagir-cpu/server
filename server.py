from flask import Flask, request, send_file
import requests
from bs4 import BeautifulSoup
import io
import os

app = Flask(__name__)

SECRET_TOKEN = "HAsdkrlaaaiwejkdh12AUs"

def get_site_icon(url):
    url = url.lower()
    if "youtube.com" in url or "youtu.be" in url:
        return "🎬 [YouTube]"
    elif "vk.com" in url:
        return "💬 [ВКонтакте]"
    elif "wikipedia.org" in url:
        return "📚 [Википедия]"
    elif "github.com" in url:
        return "💻 [GitHub]"
    elif "steam" in url or "play" in url or "game" in url:
        return "🎮 [Игры]"
    else:
        return "🌐 [Сайт]"

@app.route('/')
def home():
    return "WAP-сервер активен!", 200

# НОВЫЙ БЕСПРОИГРЫШНЫЙ РОУТ ДЛЯ ПОИСКА БЕЗ ЗНАКОВ ? И &
@app.route('/search/<token>/<path:query_input>')
def search_route(token, query_input):
    if token != SECRET_TOKEN:
        return "Ошибка: Доступ запрещён. Неверный токен!", 403

    if not query_input:
        return "Введите поисковый запрос...", 200

    try:
        # Используем Mojeek, он стабилен и не банит
        search_url = f"https://www.mojeek.com/search?q={query_input}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        res = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        results = []
        results.append(f" ۩  НАВАЛ ПОИСК (БЕЗ БАНОВ): {query_input.upper()}  ۩ ")
        results.append("=" * 40)
        results.append("")
        
        for link_tag in soup.find_all('a', class_='ob'):
            title = link_tag.get_text(strip=True)
            link = link_tag.get('href', '')
            
            snippet_tag = link_tag.find_next('p', class_='s')
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else "Нет описания."
            
            if title and link and not link.startswith('/'):
                clean_link = link.replace("https://", "").replace("http://", "")
                icon = get_site_icon(clean_link)
                
                results.append(f"{icon} {title}")
                results.append(f"Инфо: {snippet}")
                results.append(f"Ссылка: {clean_link}")
                results.append("-" * 35)
        
        if len(results) <= 3:
            return f"Ничего не найдено по запросу '{query_input}'.", 200
            
        return "\n".join(results), 200, {'Content-Type': 'text/plain; charset=utf-8'}
        
    except Exception as e:
        return f"Ошибка поискового узла: {str(e)}", 200

# РОУТ ДЛЯ ПРЯМОГО ОТКРЫТИЯ САЙТОВ (когда есть точка)
@app.route('/browse/<token>/<path:clean_url>')
def browse_route(token, clean_url):
    if token != SECRET_TOKEN:
        return "Ошибка: Доступ запрещён. Неверный токен!", 403

    target_url = f"https://{clean_url}"
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(target_url, headers=headers, timeout=10)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        for tag in soup(["script", "style", "header", "footer", "nav", "aside", "noscript"]):
            tag.extract()
            
        clean_text = soup.get_text(separator='\n', strip=True)
        return clean_text, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        
    except Exception as e:
        return f"Ошибка шлюза: {str(e)}", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
