from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import os

app = Flask(__name__)
# Принудительно отключаем ASCII-кодирование для красивого русского языка
app.json.ensure_ascii = False 

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
    elif "rss" in url or "xml" in url or "feed" in url:
        return "📰 [RSS Лента]"
    else:
        return "🌐 [Сайт]"

@app.route('/')
def home():
    return "WAP-сервер активен и защищен!", 200

# РОУТ ДЛЯ ПОИСКА ПО ВИКИПЕДИИ
@app.route('/search/<token>/<path:query_input>')
def search_route(token, query_input):
    if token != SECRET_TOKEN:
        return jsonify({"error": "Доступ запрещён"}), 403

    if not query_input:
        return jsonify({"text": "Введите поисковый запрос..."}), 200

    try:
        wiki_api = f"https://ru.wikipedia.org/w/api.php?action=query&list=search&srsearch={query_input}&format=json"
        headers = {'User-Agent': 'NavalBrowser/2.0'}
        req = requests.get(wiki_api, headers=headers, timeout=10).json()
        
        search_results = req.get('query', {}).get('search', [])
        
        if not search_results:
            return jsonify({"text": f"📚 По запросу '{query_input}' в Википедии ничего не найдено."}), 200
            
        results = []
        results.append(f" 📚  НАВАЛ ПОИСК (ВИКИПЕДИЯ): {query_input.upper()}  📚 ")
        results.append("=" * 40)
        results.append("")
        
        for item in search_results[:5]:  # Топ-5 статей
            title = item['title']
            snippet = BeautifulSoup(item['snippet'], 'html.parser').get_text()
            wiki_link = f"ru.wikipedia.org/wiki/{title.replace(' ', '_')}"
            
            results.append(f"📖 {title}")
            results.append(f"Инфо: {snippet}...")
            results.append(f"Ссылка: {wiki_link}")
            results.append("-" * 35)
            
        return jsonify({"text": "\n".join(results)}), 200
        
    except Exception as e:
        return jsonify({"text": f"❌ Ошибка поиска: {str(e)}"}), 200

# РОУТ ДЛЯ ПРЯМОГО ОТКРЫТИЯ САЙТОВ И RSS-ЛЕНТ
@app.route('/browse/<token>/<path:clean_url>')
def browse_route(token, clean_url):
    if token != SECRET_TOKEN:
        return jsonify({"error": "Доступ запрещён"}), 403

    target_url = f"https://{clean_url}"
    url_lower = clean_url.lower()
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(target_url, headers=headers, timeout=10)
        
        # Проверяем, является ли страница RSS-лентой
        is_rss = ".xml" in url_lower or ".rss" in url_lower or "feed" in url_lower or "xml" in response.headers.get('Content-Type', '').lower()
        
        if is_rss:
            try:
                # Парсим XML стандартным надёжным модулем Python
                root = ET.fromstring(response.content)
                rss_results = []
                
                # Ищем заголовок канала ленты
                channel_title = "Без названия"
                channel = root.find('channel')
                if channel is not None and channel.find('title') is not None:
                    channel_title = channel.find('title').text
                
                rss_results.append(f"📰 RSS ЛЕНТА НОВОСТЕЙ: {channel_title.upper()}")
                rss_results.append("=" * 40)
                rss_results.append("")
                
                # Ищем новости (работает для стандартных RSS 2.0)
                items = root.findall('.//item')
                if not items:
                    # Если это Atom-лента, ищем теги entry
                    items = root.findall('.//{http://www.w3.org/2005/Atom}entry') or root.findall('.//entry')
                
                for item in items[:5]: # Берем топ-5 новостей
                    title_tag = item.find('title') or item.find('{http://www.w3.org/2005/Atom}title')
                    title = title_tag.text if title_tag is not None else "Новость без заголовка"
                    
                    desc_tag = item.find('description') or item.find('summary') or item.find('{http://www.w3.org/2005/Atom}summary')
                    if desc_tag is not None and desc_tag.text:
                        # Чистим текст новости от случайных HTML-тегов картинок и ссылок
                        desc = BeautifulSoup(desc_tag.text, 'html.parser').get_text(strip=True)
                    else:
                        desc = "Описание отсутствует."
                        
                    if len(desc) > 180:
                        desc = desc[:180] + "..."
                        
                    rss_results.append(f"🔥 {title}")
                    rss_results.append(f"Анонс: {desc}")
                    rss_results.append("-" * 35)
                    
                return jsonify({"text": "\n".join(rss_results)}), 200
                
            except Exception as xml_err:
                # Если XML сломался, отдаем как обычный сайт, чтобы не вылетать
                pass

        # ОБЫЧНЫЙ ПРОСМОТР САЙТА (если это не RSS)
        soup = BeautifulSoup(response.text, 'html.parser')
        for tag in soup(["script", "style", "header", "footer", "nav", "aside", "noscript"]):
            tag.extract()
            
        clean_text = soup.get_text(separator='\n', strip=True)
        icon = get_site_icon(clean_url)
        final_text = f"{icon} Содержимое сайта {clean_url}:\n\n{clean_text}"
        
        return jsonify({"text": final_text}), 200
        
    except Exception as e:
        return jsonify({"text": f"❌ Ошибка шлюза: {str(e)}"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
