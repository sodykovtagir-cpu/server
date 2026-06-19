from flask import Flask, request
import requests
from bs4 import BeautifulSoup

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

@app.route('/browse')
def browse():
    user_token = request.headers.get('X-Auth-Token')
    if user_token != SECRET_TOKEN:
        return "Ошибка: Доступ запрещён. Неверный токен!", 403

    query_input = request.args.get('q')
    if not query_input:
        return "Введите поисковый запрос или URL...", 200
    
    # ЕСЛИ ПОИСК (нет точки в запросе) — ищем через DuckDuckGo HTML (без капчи)
    if '.' not in query_input:
        try:
            # Облегченная версия DDG для старых браузеров и скриптов
            search_url = f"https://html.duckduckgo.com/html/?q={query_input}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            results.append(f" ۩  РЕЗУЛЬТАТЫ ПОИСКА DDG: {query_input.upper()}  ۩ ")
            results.append("=" * 40)
            results.append("")
            
            # Парсим результаты поиска
            for result in soup.find_all('div', class_='result'):
                title_tag = result.find('a', class_='result__url')
                snippet_tag = result.find('a', class_='result__snippet')
                
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    link = title_tag.get('href', '')
                    snippet = snippet_tag.get_text(strip=True) if snippet_tag else "Нет описания."
                    
                    # Извлекаем чистую ссылку из редиректа DDG, если нужно, или просто чистим протокол
                    if "uddg=" in link:
                        clean_link = link.split("uddg=")[1].split("&")[0]
                        from urllib.parse import unquote
                        clean_link = unquote(clean_link)
                    else:
                        clean_link = link
                        
                    clean_link = clean_link.replace("https://", "").replace("http://", "")
                    icon = get_site_icon(clean_link)
                    
                    results.append(f"{icon} {title}")
                    results.append(f"Описание: {snippet}")
                    results.append(f"Ссылка: {clean_link}")
                    results.append("-" * 35)
            
            if len(results) <= 3:
                return f"По запросу '{query_input}' ничего не найдено или DDG временно недоступен.", 200
                
            return "\n".join(results), 200, {'Content-Type': 'text/plain; charset=utf-8'}
            
        except Exception as e:
            return f"Ошибка поиска DuckDuckGo: {str(e)}", 200
            
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
