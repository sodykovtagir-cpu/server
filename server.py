from flask import Flask, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

SECRET_TOKEN = "HAsdkrlaaaiwejkdh12AUs"

# Функция, которая выбирает иконку в зависимости от адреса сайта
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
    elif "mail" in url or "yandex" in url:
        return "📧 [Почта/Инфо]"
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
    
    # Поиск через Startpage
    if '.' not in query_input:
        try:
            search_url = "https://www.startpage.com/sp/search"
            data = {
                "query": query_input,
                "cat": "web",
                "cmd": "process_search",
                "language": "nederlands",
                "engine0": "v1u0sh"
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = requests.post(search_url, data=data, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            results.append(f" ۩  РЕЗУЛЬТАТЫ ПОИСКА: {query_input.upper()}  ۩ ")
            results.append("=" * 40)
            results.append("")
            
            for result in soup.find_all('li', class_='w-gl__result'):
                title_tag = result.find('a', class_='w-gl__result-title')
                snippet_tag = result.find('p', class_='w-gl__description')
                
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    link = title_tag.get('href', '')
                    snippet = snippet_tag.get_text(strip=True) if snippet_tag else "Нет описания."
                    
                    clean_link = link.replace("https://", "").replace("http://", "")
                    
                    # Получаем крутую текстовую иконку для сайта
                    icon = get_site_icon(clean_link)
                    
                    results.append(f"{icon} {title}")
                    results.append(f"Описание: {snippet}")
                    results.append(f"Адрес: {clean_link}")
                    results.append("-" * 35)
            
            if len(results) <= 3:
                for tag in soup(["script", "style", "noscript", "header", "footer"]):
                    tag.extract()
                return soup.get_text(separator='\n', strip=True), 200, {'Content-Type': 'text/plain; charset=utf-8'}
                
            return "\n".join(results), 200, {'Content-Type': 'text/plain; charset=utf-8'}
            
        except Exception as e:
            return f"Ошибка поиска Startpage: {str(e)}", 200
            
    else:
        # Просмотр обычного сайта
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
