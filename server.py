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
    
    # Если в запросе нет точки — ищем по базе знаний Википедии через официальный API
    if '.' not in query_input:
        try:
            # Запрос к API Википедии для поиска статей
            wiki_api = f"https://ru.wikipedia.org/w/api.php?action=query&list=search&srsearch={query_input}&format=json"
            headers = {'User-Agent': 'NavalBrowser/1.0'}
            req = requests.get(wiki_api, headers=headers, timeout=10).json()
            
            search_results = req.get('query', {}).get('search', [])
            
            if not search_results:
                return f"По запросу '{query_input}' ничего не найдено.", 200
                
            results = []
            results.append(f"=== Результаты поиска для: {query_input} ===")
            results.append("")
            
            for item in search_results[:5]: # Берем первые 5 совпадений
                title = item['title']
                # Очищаем текст от HTML-тегов вроде <span>
                snippet = BeautifulSoup(item['snippet'], 'html.parser').get_text()
                
                results.append(f"📌 {title}")
                results.append(f"{snippet}...")
                results.append(f"Ссылка: ru.wikipedia.org/wiki/{title.replace(' ', '_')}")
                results.append("-" * 30)
                
            return "\n".join(results), 200, {'Content-Type': 'text/plain; charset=utf-8'}
            
        except Exception as e:
            return f"Ошибка поиска: {str(e)}", 200
            
    else:
        # Если это обычная ссылка, открываем как сайт
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
