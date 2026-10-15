"""Скачивает всю медиатеку старого сайта (оригиналы) в source/photos/ + список с размерами."""
import json, os, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

BASE = "https://xn--80ahegeiiipn3am.xn--p1ai"
OUT = os.path.join(os.path.dirname(__file__), "..", "source", "photos")
UA = {"User-Agent": "Mozilla/5.0"}

def get(*a, **k):
    # Джино периодически рвёт соединение — повторяем с паузой
    import time
    for i in range(5):
        try:
            return _get_once(*a, **k)
        except Exception:
            if i == 4:
                raise
            time.sleep(2 * (i + 1))

def iri(url):
    # кириллица в путях WordPress-файлов
    return urllib.parse.quote(url, safe=":/?&=%#")

def _get_once(url):
    with urllib.request.urlopen(urllib.request.Request(iri(url), headers=UA), timeout=90) as r:
        return r.read()

items, page = [], 1
while True:
    try:
        batch = json.loads(get(f"{BASE}/wp-json/wp/v2/media?per_page=100&page={page}"))
    except Exception:
        break
    if not batch:
        break
    items += batch
    page += 1

os.makedirs(OUT, exist_ok=True)
rows = []
def fetch(m):
    url = m.get("source_url") or ""
    if not url or not (m.get("mime_type") or "").startswith("image/"):
        return None
    p = urllib.parse.urlparse(url).path.split("/wp-content/uploads/")[-1]
    name = urllib.parse.unquote(p).replace("/", "_")
    path = os.path.join(OUT, name)
    if not os.path.exists(path):
        try:
            data = get(url)
            open(path, "wb").write(data)
        except Exception as e:
            return {"file": name, "error": str(e)}
    d = m.get("media_details") or {}
    return {"file": name, "w": d.get("width"), "h": d.get("height"), "id": m["id"], "url": url}

with ThreadPoolExecutor(8) as ex:
    rows = [r for r in ex.map(fetch, items) if r]
json.dump(rows, open(os.path.join(OUT, "_list.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(items), "в медиатеке,", len(rows), "картинок,", sum(1 for r in rows if "error" in r), "ошибок")
