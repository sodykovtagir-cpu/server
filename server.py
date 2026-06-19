from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
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

@app.route('/search/<token>/<path:query_input>')
def search_route(token, query_input):
    if token != SECRET_TOKEN:
        return jsonify({"error": "Доступ запрещён"}), 403

    try:
        search_url = f"https://www.mojeek.com/search?q={query_input}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        res = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        results = []
        results.append(f" ۩  НАВАЛ ПОИСК: {query_input.upper()}  ۩ ")
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
            return jsonify({"text": f"Ничего не найдено по запросу '{query_input}'."}), 200
            
        # Отдаем JSON — Unity это обожает
        return jsonify({"text": "\n".join(results)}), 200
        
    except Exception as e:
        return jsonify({"text": f"Ошибка поискового узла: {str(e)}"}), 200

@app.route('/browse/<token>/<path:clean_url>')
def browse_route(token, clean_url):
    if token != SECRET_TOKEN:
        return jsonify({"error": "Доступ запрещён"}), 403

    target_url = f"https://{clean_url}"
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(target_url, headers=headers, timeout=10)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        for tag in soup(["script", "style", "header", "footer", "nav", "aside", "noscript"]):
            tag.extract()
            
        clean_text = soup.get_text(separator='\n', strip=True)
        return jsonify({"text": clean_text}), 200
        
    except Exception as e:
        return jsonify({"text": f"Ошибка шлюза: {str(e)}"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
