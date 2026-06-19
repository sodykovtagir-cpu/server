from flask import Flask, request, send_file
import requests
from bs4 import BeautifulSoup
import io

app = Flask(__name__)

SECRET_TOKEN = "HAsdkrlaaaiwejkdh12AUs"

# Список стабильных публичных серверов SearXNG, которые не банят
SEARXNG_INSTANCES = [
    "https://search.onon.im",
    "https://searx.be",
    "https://searxng.site",
    "https://searx.work",
    "https://priv.au"
]

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

@app.route('/get_image')
def get_image():
    img_url = request.args.get('url')
    if not img_url:
        return "No URL provided", 400
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        img_res = requests.get(img_url, headers=headers, timeout=5)
        if img_res.status_code == 200:
            img_io = io.BytesIO(img_res.content)
            return send_file(img_io, mimetype=img_res.headers.get('Content-Type', 'image/png'))
    except Exception as e:
        return f"Error loading image: {str(e)}", 500
    return "Failed to load image", 404

@app.route('/browse')
def browse():
    user_token = request.headers.get('X-Auth-Token')
    if user_token != SECRET_TOKEN:
        return "Ошибка: Доступ запрещён. Неверный токен!", 403

    query_input = request.args.get('q')
    if not query_input:
        return "Введите поисковый запрос или URL...", 200
    
    # ЕСЛИ ПОИСК (нет точки в запросе) — ищем через SearXNG по всему инету
    if '.' not in query_input:
        response_json = None
        # Пробуем разные сервера, если какой-то лежит
        for instance in SEARXNG_INSTANCES:
            try:
                search_url = f"{instance}/search"
                params = {
                    "q": query_input,
                    "format": "json",
                    "pageno": 1,
                    "safesearch": 1
                }
                headers = {'User-Agent': 'Mozilla/5.0 NavalBrowser/2.0'}
                res = requests.get(search_url, params=params, headers=headers, timeout=5)
                
                if res.status_code == 200:
                    response_json = res.json()
                    break # Нашли рабочий сервер, выходим из цикла
            except:
                continue # Если сервер выдал ошибку, берем следующий
        
        if not response_json or not response_json.get('results'):
            return f"Ошибка: Все поисковые узлы SearXNG временно перегружены. Попробуй позже.", 200
            
        results = []
        results.append(f" ۩  РЕЗУЛЬТАТЫ ПОИСКА SEARXNG: {query_input.upper()}  ۩ ")
        results.append("=" * 40)
        results.append("")
        
        # Парсим чистый JSON без всякого HTML-мусора
        for item in response_json.get('results', [])[:6]: # Топ-6 сайтов
            title = item.get('title', 'Без названия')
            link = item.get('url', '')
            snippet = item.get('content', 'Нет описания.')
            
            clean_link = link.replace("https://", "").replace("http://", "")
            icon = get_site_icon(clean_link)
            
            results.append(f"{icon} {title}")
            results.append(f"Инфо: {snippet}")
            results.append(f"Ссылка: {clean_link}")
            results.append("-" * 35)
            
        return "\n".join(results), 200, {'Content-Type': 'text/plain; charset=utf-8'}
            
    # ЕСЛИ ССЫЛКА (есть точка) — открываем сайт напрямую
    else:
        clean_url = query_input.replace("https://", "").replace("http://", "")
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
    app.run(host='0.0.0.0', port=8080)
