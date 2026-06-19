from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import io
import os

app = Flask(__name__)

SECRET_TOKEN = "HAsdkrlaaaiwejkdh12AUs"

# Функция для добавления иконок к ссылкам при обычном просмотре сайтов
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
    return "WAP-сервер активен и защищен!", 200

# РОУТ ДЛЯ ПОИСКА ПО ВИКИПЕДИИ (без знаков ? и &, которые вешают игру)
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
            
            # Добавляем красивое оформление с иконкой книжки для каждой статьи
            results.append(f"📖 {title}")
            results.append(f"Инфо: {snippet}...")
            results.append(f"Ссылка: {wiki_link}")
            results.append("-" * 35)
            
        return jsonify({"text": "\n".join(results)}), 200
        
    except Exception as e:
        return jsonify({"text": f"❌ Ошибка поиска: {str(e)}"}), 200

# РОУТ ДЛЯ ПРЯМОГО ОТКРЫТИЯ САЙТОВ
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
        
        # Добавляем иконку сайта в начало страницы
        icon = get_site_icon(clean_url)
        final_text = f"{icon} Содержимое сайта {clean_url}:\n\n{clean_text}"
        
        return jsonify({"text": final_text}), 200
        
    except Exception as e:
        return jsonify({"text": f"❌ Ошибка шлюза: {str(e)}"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
