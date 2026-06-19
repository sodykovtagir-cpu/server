"""
Мини-браузер — серверная часть.
Принимает GET /render?url=https://example.com
Возвращает JSON-массив команд для Lua-клиента:

[
  {"t":"label", "x":10, "y":0,  "s":"Заголовок", "fs":20, "c":[255,255,255]},
  {"t":"link",  "x":10, "y":30, "s":"Текст ссылки", "url":"https://..."},
  {"t":"img",   "x":10, "y":60, "w":200, "h":150, "url":"https://..."},
  ...
]

Каждая команда уже содержит готовую позицию (x,y) — клиенту остаётся
только создать соответствующий элемент и не нужно ничего парсить,
вычислять word-wrap, резолвить относительные ссылки и т.п. — всё
сделано здесь.

Зависимости: flask, requests, beautifulsoup4
    pip install flask requests beautifulsoup4
"""

from flask import Flask, request, jsonify
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup, NavigableString, Comment

app = Flask(__name__)

PAGE_W = 760          # ширина области рендера в окне клиента (px)
LINE_H = 22           # высота строки
CHAR_W = 7.5          # примерная ширина символа при font_size=14
MAX_CHARS_PER_LINE = int((PAGE_W - 20) / CHAR_W)

IGNORE_TAGS = {"script", "style", "head", "noscript", "svg", "iframe"}
BLOCK_TAGS = {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr", "section", "article", "header", "footer"}

HEADING_SIZE = {"h1": 24, "h2": 20, "h3": 18, "h4": 16, "h5": 15, "h6": 14}


def wrap_text(text, max_chars):
    """Простой word-wrap по количеству символов в строке."""
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        cand = (cur + " " + w).strip()
        if len(cand) > max_chars and cur:
            lines.append(cur)
            cur = w
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines or [""]


def fetch_html(url):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; MiniBrowser/1.0)"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.text


def parse_to_commands(html, base_url):
    soup = BeautifulSoup(html, "html.parser")

    # убираем игнорируемые теги целиком (script/style/...)
    for tag in soup(IGNORE_TAGS):
        tag.decompose()
    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        c.extract()

    body = soup.body or soup
    commands = []
    y = [0]  # мутабельный счётчик высоты, используем список как "ссылку"

    def add_text(text, font_size=14, color=(220, 220, 220), bold=False):
        text = " ".join(text.split())
        if not text:
            return
        max_chars = int((PAGE_W - 20) / (font_size * 0.55))
        prefix = "[Ж] " if bold else ""
        for line in wrap_text(text, max_chars):
            commands.append({
                "t": "label", "x": 10, "y": y[0],
                "s": prefix + line, "fs": font_size, "c": list(color)
            })
            y[0] += int(LINE_H * (font_size / 14))

    def add_link(text, href):
        text = " ".join(text.split()) or href or "(ссылка)"
        full = urljoin(base_url, href) if href else None
        if not full:
            add_text(text)
            return
        if len(text) > 90:
            text = text[:87] + "..."
        commands.append({"t": "link", "x": 10, "y": y[0], "s": "> " + text, "url": full})
        y[0] += LINE_H

    def add_image(src, w=None, h=None):
        if not src:
            return
        full = urljoin(base_url, src)
        w = w or 200
        h = h or 150
        if w > PAGE_W - 20:
            scale = (PAGE_W - 20) / w
            w = PAGE_W - 20
            h = h * scale
        commands.append({"t": "img", "x": 10, "y": y[0], "w": int(w), "h": int(h), "url": full})
        y[0] += int(h) + 6

    def add_spacer(h=10):
        y[0] += h

    def walk(node, bold=False):
        for child in node.children:
            if isinstance(child, NavigableString):
                text = str(child)
                if text.strip():
                    add_text(text, bold=bold)
                continue

            name = child.name
            if name is None:
                continue

            if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
                add_spacer(8)
                add_text(child.get_text(), font_size=HEADING_SIZE.get(name, 16), color=(255, 255, 255), bold=True)
                add_spacer(6)
            elif name == "br":
                add_spacer(LINE_H)
            elif name == "hr":
                add_spacer(4)
                commands.append({"t": "label", "x": 10, "y": y[0], "s": "-" * 60, "fs": 12, "c": [90, 90, 90]})
                add_spacer(LINE_H)
            elif name == "img":
                w = child.get("width")
                h = child.get("height")
                try:
                    w = int(float(w)) if w else None
                except ValueError:
                    w = None
                try:
                    h = int(float(h)) if h else None
                except ValueError:
                    h = None
                add_image(child.get("src"), w, h)
            elif name == "a":
                href = child.get("href")
                text = child.get_text()
                if child.find("img"):
                    # ссылка-картинка: рисуем картинку, текст (если есть) — отдельно
                    walk(child, bold)
                else:
                    add_link(text, href)
            elif name in ("b", "strong"):
                add_text(child.get_text(), bold=True)
            elif name == "li":
                add_text("• " + child.get_text())
            elif name in BLOCK_TAGS:
                walk(child, bold)
                add_spacer(4)
            else:
                walk(child, bold)

    walk(body)
    return commands


@app.route("/render")
def render():
    url = request.args.get("url", "")
    if not url:
        return jsonify({"error": "no url"}), 400
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    try:
        html = fetch_html(url)
        commands = parse_to_commands(html, url)
        return jsonify({"ok": True, "url": url, "commands": commands})
    except requests.RequestException as e:
        return jsonify({"ok": False, "error": str(e)}), 502
    except Exception as e:
        return jsonify({"ok": False, "error": "parse_error: " + str(e)}), 500


@app.route("/")
def index():
    return jsonify({"status": "ok", "usage": "/render?url=https://example.com"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
