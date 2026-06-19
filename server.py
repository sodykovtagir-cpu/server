from flask import Flask, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

SECRET_TOKEN = "HAsdkrlaaaiwejkdh12AUs"

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
    
    # Если в запросе нет точки — ищем через безотказный DuckDuckGo HTML
    if '.' not in query_input:
        target_url = f"https://html.duckduckgo.com/html/?q={query_input.replace(' ', '+')}"
    else:
        clean_url = query_input.replace("https://", "").replace("http://", "")
        target_url = f"https://{clean_url}"
        
    try:
        # Стандартный чистый заголовок браузера
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(target_url, headers=headers, timeout=10)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Вырезаем весь лишний мусор и скрипты
        for tag in soup(["script", "style", "header", "footer", "nav", "aside", "noscript"]):
            tag.extract()
            
        # Если искали через DuckDuckGo, сделаем выдачу красивой и читаемой списком
        if "duckduckgo.com" in target_url:
            results = []
            results.append("=== РЕЗУЛЬТАТЫ ПОИСКА ===")
            results.append("")
            
            # Находим блоки с результатами поиска в HTML-версии DuckDuckGo
            for links in soup.find_all('a', class_='result__url'):
                title_block = links.find_previous('a', class_='result__snippet')
                title = links.get_text(strip=True)
                url_text = links.get('href', '')
                
                # Зачищаем внутренние ссылки DuckDuckGo, оставляя чистый сайт
                if "uddg=" in url_text:
                    url_text = url_text.split("uddg=")[1].split("&")[0]
                    from urllib.parse import unquote
                    url_text = unquote(url_text)
                
                if title and url_text:
                    results.append(f"• Ссылка: {url_text}")
                    results.append("")
            
            # Если вдруг ничего не нашлось стандартным парсером, отдаем просто текст
            if len(results) <= 3:
                clean_text = soup.get_text(separator='\n', strip=True)
                return clean_text, 200, {'Content-Type': 'text/plain; charset=utf-8'}
                
            return "\n".join(results), 200, {'Content-Type': 'text/plain; charset=utf-8'}
            
        # Для обычных сайтов возвращаем стандартный текст
        clean_text = soup.get_text(separator='\n', strip=True)
        return clean_text, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        
    except Exception as e:
        return f"Ошибка шлюза: {str(e)}", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
