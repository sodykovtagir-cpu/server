from flask import Flask, request, send_file
import requests
from bs4 import BeautifulSoup
import io
from urllib.parse import unquote

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
    
    # ЕСЛИ ПОИСК (нет точки в запросе)
    if '.' not in query_input:
        try:
            # Используем самый стабильный html-поисковик DDG
            search_url = f"https://html.duckduckgo.com/html/?q={query_input}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            results.append(f" ۩  РЕЗУЛЬТАТЫ ПОИСКА: {query_input.upper()}  ۩ ")
            results.append("=" * 40)
            results.append("")
            
            # Находим все блоки с результатами на странице
            search_elements = soup.find_all('a', class_='result__url')
            
            for tag in search_elements:
                title_elem = tag.find_next('a', class_='result__snippet')
                
                title = tag.get_text(strip=True)
                link = tag.get('href', '')
                snippet = title_elem.get_text(strip=True) if title_elem else "Нет описания."
                
                # Чистим ссылки DDG от редиректов
                if "uddg=" in link:
                    clean_link = link.split("uddg=")[1].split("&")[0]
                    clean_link = unquote(clean_link)
                else:
                    clean_link = link
                    
                clean_link = clean_link.replace("https://", "").replace("http://", "")
                icon = get_site_icon(clean_link)
                
                results.append(f"{icon} {title}")
                results.append(f"Описание: {snippet}")
                results.append(f"Ссылка: {clean_link}")
                results.append("-" * 35)
            
            # Если DDG выдал другую структуру, ищем по обычным ссылкам результатов
            if len(results) <= 3:
                for res_td in soup.find_all('td', class_='result-links--main'):
                    a_tag = res_td.find('a')
                    if a_tag:
                        title = a_tag.get_text(strip=True)
                        link = a_tag.get('href', '')
                        if "uddg=" in link:
                            link = unquote(link.split("uddg=")[1].split("&")[0])
                        link = link.replace("https://", "").replace("http://", "")
                        icon = get_site_icon(link)
                        
                        results.append(f"{icon} {title}")
                        results.append(f"Ссылка: {link}")
                        results.append("-" * 35)

            if len(results) <= 3:
                return f"По запросу '{query_input}' ничего не найдено через DDG.", 200
                
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
