from flask import Flask, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# Твой секретный токен защиты
SECRET_TOKEN = "HAsdkrlaaaiwejkdh12AUs"

@app.route('/')
def home():
    return "WAP-сервер активен!", 200

@app.route('/browse')
def browse():
    # Проверка безопасности (токен)
    user_token = request.headers.get('X-Auth-Token')
    if user_token != SECRET_TOKEN:
        return "Ошибка: Доступ запрещён. Неверный токен!", 403

    # Получаем запрос или ссылку из игры
    query_input = request.args.get('q')
    if not query_input:
        return "Введите поисковый запрос или URL...", 200
    
    # Если в запросе нет точки — это поиск в Гугле
    if '.' not in query_input:
        target_url = f"https://www.google.com/search?q={query_input.replace(' ', '+')}"
    else:
        # Если это ссылка, убираем протоколы и добавляем чистый https://
        clean_url = query_input.replace("https://", "").replace("http://", "")
        target_url = f"https://{clean_url}"
        
    try:
        # User-Agent, с которым Google сразу отдает текстовую страницу без редиректов
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}
        response = requests.get(target_url, headers=headers, timeout=10)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Вырезаем ненужные теги, чтобы не засорять экран в игре
        for tag in soup(["script", "style", "header", "footer", "nav", "aside", "noscript"]):
            tag.extract()
            
        # Получаем чистый текст
        clean_text = soup.get_text(separator='\n', strip=True)
        return clean_text, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        
    except Exception as e:
        return f"Ошибка шлюза: {str(e)}", 200

if __name__ == '__main__':
    # Запуск сервера на порту 8080 (Render сам перенаправит его на 10000)
    app.run(host='0.0.0.0', port=8080)
