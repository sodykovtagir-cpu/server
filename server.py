from flask import Flask, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

SECRET_TOKEN = "HAsdkrlaaaiwejkdh12AUs "

@app.route('/')
def home():
    return "WAP-сервер активен!", 200

@app.route('/browse')
def browse():
    user_token = request.headers.get('X-Auth-Token')
    if user_token != SECRET_TOKEN:
        return "Ошибка: Доступ запрещён. Неверный токен!", 403

    target_url = request.args.get('url')
    if not target_url:
        return "Укажи URL через ?url=...", 200
        
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(target_url, headers=headers, timeout=10)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        for tag in soup(["script", "style", "header", "footer", "nav", "aside"]):
            tag.extract()
            
        clean_text = soup.get_text(separator='\n', strip=True)
        return clean_text, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        
    except Exception as e:
        return f"Ошибка шлюза: {str(e)}", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
