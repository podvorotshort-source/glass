"""Простые страницы и перенаправления со старых адресов дизайнстекло.рф.

- content/pages/*.md  → site/<старый адрес>/index.html (политики)
- REDIRECTS          → страницы-перенаправления, чтобы старые ссылки
                        и закладки не вели на 404 после переезда

Запуск: python tools/build_pages.py (входит в npm run build).
"""
import os
import re

import markdown

from build_articles import SITE, esc, page, read_article, redirect_page

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
PAGES = os.path.join(ROOT, "content", "pages")

# старый адрес → куда ведём на новом сайте (относительно корня)
REDIRECTS = {
    "/proizvodstvo-konstrukcij-iz-zakalennogo-stekla-2/": "",
    "/vse-o-steklyannyx-konstrukciyax/": "stati/",
    "/portfolio/": "#works",
    "/kompaniya/": "#about",
    "/kak-sdelat-zakaz/": "#about",
    "/garantiya/": "#about",
    "/dostavka/": "#about",
    "/oplata/": "#contacts",
    "/contacts/": "#contacts",
    "/peregorodki-iz-stekla/": "#cat-peregorodki",
    "/peregorodki-iz-stekla-2/": "#cat-peregorodki",
    "/peregorodki-iz-stekla-dlya-ban-i-saun/": "#cat-peregorodki",
    "/peregorodki-iz-stekla/alyuminievye-peregorodki/": "#cat-peregorodki",
    "/peregorodki-iz-stekla/bani-sauny-hamam/": "#cat-peregorodki",
    "/peregorodki-iz-stekla/celnosteklyannye-peregorodki/": "#cat-peregorodki",
    "/dushevye-iz-stekla/": "#cat-dushevye",
    "/dushevye-iz-stekla/razdvizhnaya-dushevaya/": "#cat-dushevye",
    "/dushevye-iz-stekla/raspashnaya-dushevaya/": "#cat-dushevye",
    "/dushevye-iz-stekla/dushevoe-ograzhdenie/": "#cat-dushevye",
    "/dushevye-iz-stekla/uglovaya-dushevaya/": "#cat-dushevye",
    "/dushevye-iz-stekla/dushevaya-trapeciya/": "#cat-dushevye",
    "/orgrazhdeniya-iz-stekla/": "#cat-ograzhdeniya",
    "/orgrazhdeniya-iz-stekla/balkonnoe-ograzhdenie/": "#cat-ograzhdeniya",
    "/orgrazhdeniya-iz-stekla/ograzhdenie-lestnic-na-stojkax/": "#cat-ograzhdeniya",
    "/orgrazhdeniya-iz-stekla/ograzhdenie-lestnic-na-tochkax/": "#cat-ograzhdeniya",
    "/lestnicy-iz-stekla/": "#cat-lestnicy",
    "/lestnicy-i-ograzhdeniya-iz-stekla/": "#cat-lestnicy",
    "/dveri-iz-stekla/": "#cat-dveri",
    "/dveri-iz-stekla-copy/": "#cat-dveri",
    "/dveri-iz-stekla/mayatnikovaya-dver/": "#cat-dveri",
    "/dveri-iz-stekla/razdvizhnaya-dver/": "#cat-dveri",
    "/dveri-iz-stekla/raspashnaya-dver/": "#cat-dveri",
    "/loft-stil/": "#cat-loft",
    "/loft-stil/peregorodki-loft/": "#cat-loft",
    "/loft-stil/raspashnye-dveri-loft/": "#cat-loft",
    "/loft-stil/dver-garmoshka-loft/": "#cat-loft",
    "/otkatnye-dveri-loft/": "#cat-loft",
    "/interer/": "#cat-interer",
    "/interer/polki/": "#cat-interer",
    "/interer/zerkala/": "#cat-interer",
    "/interer/kuxonnye-fartuki/": "#cat-interer",
    "/interer/osteklenie-terras-i-besedok/": "#cat-interer",
}


def write(path, text):
    out = os.path.join(SITE, path.strip("/"))
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(text)


def main():
    for name in sorted(os.listdir(PAGES)):
        if not name.endswith(".md"):
            continue
        meta, body = read_article(os.path.join(PAGES, name))
        path = meta["old_url"]
        root = "../" * path.strip("/").count("/") + "../"
        content = markdown.markdown(body, extensions=["extra", "sane_lists"])
        html = f'''<article class="article">
  <nav class="crumbs" aria-label="Навигация"><a href="{root}">Главная</a></nav>
  <h1>{esc(meta["title"])}</h1>
  <div class="prose">
{content}
  </div>
</article>'''
        desc = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", content)).strip()[:160]
        write(path, page(meta["title"], desc, root, html, path))

    for old, target in REDIRECTS.items():
        root = "../" * (old.strip("/").count("/") + 1)
        write(old, redirect_page(root + target))
    print(f"страниц: {len(os.listdir(PAGES))}, перенаправлений: {len(REDIRECTS)}")


if __name__ == "__main__":
    main()
