"""Забирает статьи (posts) со старого сайта дизайнстекло.рф и раскладывает по папкам.

content/articles/<NN-папка>/<slug>.md   — текст статьи + frontmatter
content/articles/<NN-папка>/img/         — картинки статьи
content/articles/index.json              — папки и файлы в формате GlassFolder
"""
import json, os, re, sys, urllib.request, urllib.parse
from bs4 import BeautifulSoup
from markdownify import markdownify as md

BASE = "https://xn--80ahegeiiipn3am.xn--p1ai"
ROOT = os.path.join(os.path.dirname(__file__), "..", "content", "articles")

# Папки на новом сайте: WP-категории сведены в 8 тем
FOLDERS = [
    ("01-peregorodki", "Перегородки", [91]),
    ("02-ograzhdeniya", "Ограждения", [90]),
    ("03-lestnicy", "Лестницы", [94], ["lestnicy-iz-stekla-zakazat-v-tolyatti"]),
    ("04-dushevye", "Душевые", [98], ["steklyannaya-dushevaya-zakazat-ili-kupit-gotovuyu-chto-luchshe", "plyusy-ispolzovaniya-dushevyx-kabin-iz-stekla"]),
    ("05-dveri", "Двери", [99]),
    ("06-steklo", "Стекло", [95]),
    ("07-interer", "Интерьер и фартуки", [97]),
    ("08-terrasy-kozyrki", "Террасы и козырьки", [93, 96]),
]
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

def _get_once(url, binary=False):
    req = urllib.request.Request(iri(url), headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    return data if binary else data.decode("utf-8")

def folder_for(post):
    slug = post["slug"]
    for f in FOLDERS:
        if len(f) > 3 and slug in f[3]:
            return f
    for f in FOLDERS:
        if set(post["categories"]) & set(f[2]):
            return f
    raise SystemExit(f"нет папки для {slug} {post['categories']}")

def meta_description(post):
    m = re.search(r'name="description" content="([^"]*)"', post.get("aioseo_head") or "")
    return BeautifulSoup(m.group(1), "html.parser").get_text() if m else ""

def content_html(post):
    html = post["content"]["rendered"]
    if len(BeautifulSoup(html, "html.parser").get_text(strip=True)) > 200:
        return html
    # Elementor-статьи: REST отдаёт пусто, берём со страницы
    page = BeautifulSoup(get(post["link"]), "html.parser")
    node = (page.select_one("[data-elementor-type='single-post'] .elementor-widget-theme-post-content")
            or page.select_one(".elementor-widget-theme-post-content")
            or page.select_one("article .entry-content")
            or page.select_one("[data-elementor-type='wp-post']"))
    return str(node) if node else html

def full_size(src):
    return re.sub(r"-\d+x\d+(\.\w+)$", r"\1", src)

def save_img(src, img_dir, used):
    src = urllib.parse.urljoin(BASE, src)
    name = urllib.parse.unquote(os.path.basename(urllib.parse.urlparse(full_size(src)).path))
    path = os.path.join(img_dir, name)
    if name not in used:
        os.makedirs(img_dir, exist_ok=True)
        for u in (full_size(src), src):
            try:
                data = get(u, binary=True)
                open(path, "wb").write(data); break
            except Exception:
                continue
        used.add(name)
    return "img/" + name

def yaml_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'

def main():
    posts = json.loads(get(f"{BASE}/wp-json/wp/v2/posts?per_page=100&_embed=wp:featuredmedia"))
    index = {key: {"folder": key, "label": label, "files": []} for key, label, *_ in FOLDERS}
    for post in posts:
        key, label, *_ = folder_for(post)
        fdir = os.path.join(ROOT, key)
        img_dir = os.path.join(fdir, "img")
        used = set(os.listdir(img_dir)) if os.path.isdir(img_dir) else set()
        soup = BeautifulSoup(content_html(post), "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        for img in soup.find_all("img"):
            src = img.get("data-src") or img.get("src")
            if src and "wp-content/uploads" in src:
                img["src"] = save_img(src, img_dir, used)
                for a in ("srcset", "sizes", "data-src", "data-srcset", "width", "height", "class", "loading", "decoding"):
                    img.attrs.pop(a, None)
        body = md(str(soup), heading_style="ATX", bullets="-", strip=["span", "div", "section"])
        body = re.sub(r"\n{3,}", "\n\n", body).strip()

        cover = ""
        media = (post.get("_embedded") or {}).get("wp:featuredmedia") or []
        if media and media[0].get("source_url"):
            cover = save_img(media[0]["source_url"], img_dir, used)

        title = BeautifulSoup(post["title"]["rendered"], "html.parser").get_text()
        old_path = urllib.parse.urlparse(post["link"]).path
        front = [
            "---",
            f"title: {yaml_str(title)}",
            f"description: {yaml_str(meta_description(post))}",
            f"date: {post['date'][:10]}",
            f"folder: {yaml_str(label)}",
            f"old_url: {yaml_str(old_path)}",
            f"cover: {yaml_str(cover)}" if cover else "cover: \"\"",
            "---", "",
        ]
        os.makedirs(fdir, exist_ok=True)
        open(os.path.join(fdir, post["slug"] + ".md"), "w", encoding="utf-8").write("\n".join(front) + body + "\n")
        words = len(re.sub(r"!\[[^\]]*\]\([^)]*\)", "", body).split())
        index[key]["files"].append({
            "name": title, "meta": f"{post['date'][:4]} · {words} слов",
            "href": f"{key}/{post['slug']}.md", "image": f"{key}/{cover}" if cover else None,
            "old_url": old_path,
        })
        print(f"{key:22} {words:5} слов  {post['slug']}")
    out = [v for v in index.values() if v["files"]]
    json.dump(out, open(os.path.join(ROOT, "index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
