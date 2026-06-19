from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)
app.json.ensure_ascii = False # Важно для корректного русского языка

SECRET_TOKEN = "HAsdkrlaaaiwejkdh12AUs"

def get_site_icon(url):
    url = url.lower()
    if "youtube.com" in url or "youtu.be" in url: return "🎬 [YouTube]"
    elif "vk.com" in url: return "💬 [ВКонтакте]"
    elif "wikipedia.org" in url: return "📚 [Википедия]"
    elif "github.com" in url: return "💻 [GitHub]"
    elif "steam" in url or "play" in url or "game" in url: return "🎮 [Игры]"
    elif "rss" in url or "xml" in url or "feed" in url: return "📰 [RSS Лента]"
    else: return "🌐 [Сайт]"

@app.route('/')
def home():
    return "WAP-сервер активен и защищен!", 200

@app.route('/search/<token>/<path:query_input>')
def search_route(token, query_input):
    if token != SECRET_TOKEN: return jsonify({"error": "Доступ запрещён"}), 403
    try:
        wiki_api = f"https://ru.wikipedia.org/w/api.php?action=query&list=search&srsearch={query_input}&format=json"
        req = requests.get(wiki_api, headers={'User-Agent': 'NavalBrowser/2.0'}, timeout=10).json()
        search_results = req.get('query', {}).get('search', [])
        if not search_results:
            return jsonify({"text": f"📚 По запросу '{query_input}' ничего не найдено."}), 200
        results = [f" 📚 НАВАЛ ПОИСК: {query_input.upper()} 📚", "="*40, ""]
        for item in search_results[:5]:
            title = item['title']
            snippet = BeautifulSoup(item['snippet'], 'html.parser').get_text()
            results.append(f"📖 {title}\nИнфо: {snippet}...\nСсылка: ru.wikipedia.org/wiki/{title.replace(' ', '_')}\n" + "-"*35)
        return jsonify({"text": "\n".join(results)}), 200
    except Exception as e:
        return jsonify({"text": f"❌ Ошибка поиска: {str(e)}"}), 200

@app.route('/browse/<token>/<path:clean_url>')
def browse_route(token, clean_url):
    if token != SECRET_TOKEN: return jsonify({"error": "Доступ запрещён"}), 403
    target_url = f"https://{clean_url}"
    try:
        response = requests.get(target_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        is_rss = (
            ".xml" in clean_url.lower()
            or ".rss" in clean_url.lower()
            or "rss" in clean_url.lower()
            or "feed" in clean_url.lower()
            or "xml" in response.headers.get('Content-Type', '').lower()
        )

        if is_rss:
            # Используем настоящий XML-парсер вместо html.parser,
            # чтобы корректно читать вложенность <item>/<title>/<description>
            try:
                soup = BeautifulSoup(response.content, "xml")
            except Exception:
                soup = BeautifulSoup(response.content, "lxml")

            feed_title_tag = soup.find('title')
            feed_title = feed_title_tag.get_text(strip=True) if feed_title_tag else "Без названия"
            rss_results = [f"📰 RSS ЛЕНТА: {feed_title.upper()}", "="*40, ""]

            items = soup.find_all('item') or soup.find_all('entry')
            if not items:
                return jsonify({"text": f"📰 RSS ЛЕНТА: {feed_title.upper()}\n\nНе удалось найти новости (нестандартный формат ленты)."}), 200

            for item in items[:5]:
                title_tag = item.find('title')
                title = title_tag.get_text(strip=True) if title_tag else "Новость без заголовка"

                desc_tag = item.find('description') or item.find('summary') or item.find('content')
                if desc_tag:
                    desc = BeautifulSoup(desc_tag.get_text(), 'html.parser').get_text(strip=True)
                else:
                    desc = "Описание отсутствует."
                if len(desc) > 180: desc = desc[:180] + "..."
                rss_results.append(f"🔥 {title}\nАнонс: {desc}\n" + "-"*35)
            return jsonify({"text": "\n".join(rss_results)}), 200

        soup = BeautifulSoup(response.text, 'html.parser')
        for tag in soup(["script", "style", "header", "footer", "nav", "aside", "noscript"]): tag.extract()
        icon = get_site_icon(clean_url)
        return jsonify({"text": f"{icon} Содержимое сайта {clean_url}:\n\n{soup.get_text(separator='\n', strip=True)}"}), 200
    except Exception as e:
        return jsonify({"text": f"❌ Ошибка шлюза: {str(e)}"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
