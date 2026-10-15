"""Собирает статьи из content/articles в страницы сайта.

- site/<slug>/index.html    — страница статьи по старому адресу (как на дизайнстекло.рф)
- site/stati/index.html     — все статьи по папкам
- site/assets/articles/     — превью статей для стеклянных папок
- site/index.html           — между <!-- articles:start/end --> вставляется блок папок и данные

Запуск: python tools/build_articles.py (или npm run build).
"""
import html
import json
import os
import re
import shutil
from datetime import date

import markdown
from PIL import Image, ImageOps

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "content", "articles")
SITE = os.path.join(ROOT, "site")
THUMBS = os.path.join(SITE, "assets", "articles")

# фон папки — фото его работы из каталога
FOLDER_ART = {
    "01-peregorodki": "assets/catalog/peregorodki-1-s.webp",
    "02-ograzhdeniya": "assets/catalog/ograzhdeniya-1-s.webp",
    "03-lestnicy": "assets/catalog/lestnicy-1-s.webp",
    "04-dushevye": "assets/catalog/dushevye-1-s.webp",
    "05-dveri": "assets/catalog/dveri-1-s.webp",
    "07-interer": "assets/catalog/interer-1-s.webp",
    "08-terrasy-kozyrki": "assets/catalog/ograzhdeniya-3-s.webp",
}
# пустые на старом сайте статьи: адрес сохраняем, ведём в каталог
REDIRECTS = {"lestnicy-iz-stekla-zakazat-v-tolyatti": "../#cat-lestnicy"}

MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля",
          "августа", "сентября", "октября", "ноября", "декабря"]


def ru_date(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def ru_plural(n, one, few, many):
    m10, m100 = n % 10, n % 100
    if m10 == 1 and m100 != 11:
        return one
    if 2 <= m10 <= 4 and not 12 <= m100 <= 14:
        return few
    return many


def read_article(path):
    text = open(path, encoding="utf-8").read()
    _, front, body = text.split("---", 2)
    meta = {}
    for line in front.strip().splitlines():
        key, _, value = line.partition(":")
        value = value.strip()
        meta[key.strip()] = json.loads(value) if value.startswith('"') else value
    return meta, body.strip()


def normalize_headings(body):
    """Самый крупный заголовок в тексте становится h2 (h1 — заголовок страницы)."""
    levels = [len(m) for m in re.findall(r"^(#{1,6}) ", body, re.M)]
    if not levels:
        return body
    shift = min(levels) - 2
    return re.sub(r"^(#{1,6}) ", lambda m: "#" * max(2, min(4, len(m.group(1)) - shift)) + " ", body, flags=re.M)


def to_webp(src, dst, max_w):
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    im.save(dst, quality=80, method=6)
    return im.size


def thumb(src, dst, size=(544, 368)):
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    ImageOps.fit(im, size, Image.LANCZOS).save(dst, quality=78, method=6)


def esc(s):
    return html.escape(s, quote=True)


def header(root):
    return f'''<header class="topbar topbar--page">
  <a class="brand" href="{root}" aria-label="ДизайнСтекло, на главную">
    <img class="brand__mark" src="{root}assets/logo-mark.png" width="60" height="30" alt="">
    <span class="brand__name">Дизайн<br>Стекло</span>
  </a>
  <nav class="topnav" aria-label="Основное меню">
    <a href="{root}#catalog">Каталог</a>
    <a href="{root}#works">Портфолио</a>
    <a href="{root}stati/">Статьи</a>
    <a href="{root}#about">О компании</a>
    <a href="{root}#contacts">Контакты</a>
  </nav>
  <div class="topbar__contact">
    <a class="topbar__phone" href="tel:+79278913800">+7 927 891-38-00</a>
    <a class="btn btn--ghost btn--sm" href="{root}#request">
      <span class="btn__glint" aria-hidden="true"></span>
      <span class="btn__frame" aria-hidden="true"></span>
      <span class="btn__label">Заказать замер</span>
    </a>
  </div>
</header>'''


def footer(root):
    return f'''<footer class="footer">
  <div class="footer__inner">
    <a class="brand" href="{root}" aria-label="ДизайнСтекло, на главную">
      <img class="brand__mark" src="{root}assets/logo-mark.png" width="60" height="30" alt="">
      <span class="brand__name">Дизайн<br>Стекло</span>
    </a>
    <p>Тольятти, Коммунальная&nbsp;32, ТЦ&nbsp;«Арбуз», офис&nbsp;305<br>
      <a href="tel:+79278913800">+7 927 891-38-00</a>, <a href="mailto:steklotlt@mail.ru">steklotlt@mail.ru</a></p>
    <p class="footer__small">Конструкции из стекла: проектирование, производство, монтаж. Тольятти, Самара и область. <a href="{root}politika-obrabotki-personalnyx-dannyx/">Обработка персональных данных</a>, <a href="{root}politika-konfidencialnosti/">конфиденциальность</a>.</p>
  </div>
</footer>'''


def page(title, description, root, body, canonical_path):
    return f'''<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <!-- превью для заказчика: убрать noindex при запуске на дизайнстекло.рф -->
  <meta name="robots" content="noindex, nofollow">
  <title>{esc(title)} — ДизайнСтекло</title>
  <meta name="description" content="{esc(description)}">
  <link rel="canonical" href="https://xn--80ahegeiiipn3am.xn--p1ai{canonical_path}">
  <link rel="icon" href="{root}assets/logo-mark.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600&family=Unbounded:wght@300;500;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{root}styles.css">
</head>
<body class="page">
{header(root)}
<main>
{body}
</main>
{footer(root)}
</body>
</html>
'''


def cta(root):
    return f'''<aside class="cta-strip">
  <div>
    <h2>Рассчитаем под ваш размер</h2>
    <p>Замерщик приедет бесплатно, посмотрит место и&nbsp;расскажет о&nbsp;нюансах монтажа.</p>
  </div>
  <div class="cta-strip__actions">
    <a class="btn btn--solid" href="{root}#request">
      <span class="btn__glint" aria-hidden="true"></span><span class="btn__frame" aria-hidden="true"></span>
      <span class="btn__label">Заказать замер</span>
    </a>
    <a class="btn btn--ghost" href="tel:+79278913800">
      <span class="btn__glint" aria-hidden="true"></span><span class="btn__frame" aria-hidden="true"></span>
      <span class="btn__label">+7 927 891-38-00</span>
    </a>
  </div>
</aside>'''


def redirect_page(target):
    return f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url={target}">
<link rel="canonical" href="{target}">
<title>ДизайнСтекло</title></head>
<body><p><a href="{target}">Перейти на сайт</a></p></body></html>
'''


def main():
    os.makedirs(THUMBS, exist_ok=True)
    folders = []
    for folder in sorted(os.listdir(SRC)):
        fdir = os.path.join(SRC, folder)
        if not os.path.isdir(fdir):
            continue
        items = []
        for name in os.listdir(fdir):
            if name.endswith(".md"):
                meta, body = read_article(os.path.join(fdir, name))
                meta["slug"] = name[:-3]
                meta["body"] = body
                items.append(meta)
        items.sort(key=lambda m: m["date"], reverse=True)
        folders.append({"key": folder, "label": items[0]["folder"], "items": items})

    for f in folders:
        for a in f["items"]:
            slug = a["slug"]
            out = os.path.join(SITE, slug)
            if os.path.isdir(out):
                shutil.rmtree(out)
            os.makedirs(out)
            if slug in REDIRECTS:
                open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(redirect_page(REDIRECTS[slug]))
                a["skip"] = True
                continue

            src_img = os.path.join(SRC, f["key"], "img")
            os.makedirs(os.path.join(out, "img"), exist_ok=True)

            def swap_img(m):
                alt, ref = m.group(1), m.group(2)
                stem = os.path.splitext(os.path.basename(ref))[0]
                w, h = to_webp(os.path.join(src_img, os.path.basename(ref)), os.path.join(out, "img", stem + ".webp"), 1400)
                return f'\n\n<figure><img src="img/{stem}.webp" width="{w}" height="{h}" alt="{esc(alt or a["title"])}" loading="lazy" decoding="async"></figure>\n\n'

            body = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", swap_img, normalize_headings(a["body"]))
            content = markdown.markdown(body, extensions=["extra", "sane_lists"])
            content = re.sub(r"<p>\s*(<figure>.*?</figure>)\s*</p>", r"\1", content, flags=re.S)
            words = len(re.sub(r"<[^>]+>", " ", content).split())
            minutes = max(1, round(words / 180))
            a["minutes"] = minutes

            cover_html = ""
            a["thumb"] = None
            if a.get("cover"):
                cover_src = os.path.join(src_img, os.path.basename(a["cover"]))
                if os.path.exists(cover_src):
                    thumb(cover_src, os.path.join(THUMBS, slug + ".webp"))
                    a["thumb"] = f"assets/articles/{slug}.webp"
                    # обложку показываем, если её нет в тексте статьи
                    cover_stem = os.path.splitext(os.path.basename(a["cover"]))[0]
                    if f"img/{cover_stem}.webp" not in content:
                        w, h = to_webp(cover_src, os.path.join(out, "img", "cover.webp"), 1600)
                        cover_html = f'<figure class="article__cover"><img src="img/cover.webp" width="{w}" height="{h}" alt="{esc(a["title"])}" decoding="async"></figure>'

            related = [r for r in f["items"] if r["slug"] != slug and r["slug"] not in REDIRECTS][:4]
            related_html = ""
            if related:
                links = "".join(f'<li><a href="../{r["slug"]}/">{esc(r["title"])}</a></li>' for r in related)
                related_html = f'<nav class="related" aria-label="Ещё статьи"><h2>Ещё в&nbsp;папке «{esc(f["label"])}»</h2><ul>{links}</ul></nav>'

            minutes_text = f"{minutes} {ru_plural(minutes, 'минута', 'минуты', 'минут')} чтения"
            body_html = f'''<article class="article">
  <nav class="crumbs" aria-label="Навигация"><a href="../">Главная</a><a href="../stati/">Статьи</a><a href="../stati/#{f["key"]}">{esc(f["label"])}</a></nav>
  <h1>{esc(a["title"])}</h1>
  <p class="article__meta"><time datetime="{a["date"]}">{ru_date(a["date"])}</time><span>{minutes_text}</span></p>
  {cover_html}
  <div class="prose">
{content}
  </div>
</article>
{cta("../")}
{related_html}'''
            desc = a.get("description") or re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", content)).strip()[:160]
            open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(
                page(a["title"], desc, "../", body_html, a.get("old_url") or f"/{slug}/"))

    # все статьи
    blocks = []
    for f in folders:
        items = [a for a in f["items"] if not a.get("skip")]
        links = "".join(
            f'<li><a href="../{a["slug"]}/"><span>{esc(a["title"])}</span><small>{a["minutes"]}&nbsp;мин</small></a></li>' for a in items)
        blocks.append(f'<section class="stati__folder" id="{f["key"]}"><h2>{esc(f["label"])}</h2><ul>{links}</ul></section>')
    total = sum(1 for f in folders for a in f["items"] if not a.get("skip"))
    stati_body = f'''<div class="stati">
  <nav class="crumbs" aria-label="Навигация"><a href="../">Главная</a></nav>
  <h1>Статьи</h1>
  <p class="stati__lead">{total} {ru_plural(total, 'статья', 'статьи', 'статей')} о&nbsp;стеклянных конструкциях: как выбрать стекло, что учесть при монтаже, сколько служит фурнитура.</p>
  {"".join(blocks)}
</div>
{cta("../")}'''
    os.makedirs(os.path.join(SITE, "stati"), exist_ok=True)
    open(os.path.join(SITE, "stati", "index.html"), "w", encoding="utf-8").write(
        page("Статьи", "Статьи о стеклянных перегородках, душевых, ограждениях и дверях.", "../", stati_body, "/stati/"))

    # данные для стеклянных папок на главной: 4 свежие статьи в каждой
    data = []
    for f in folders:
        items = [a for a in f["items"] if not a.get("skip")]
        files = []
        for a in reversed(items[:4]):  # компонент показывает последние файлы списка сверху
            file = {"name": a["title"], "meta": f'{a["minutes"]} мин', "href": f'{a["slug"]}/'}
            if a["thumb"]:
                file["image"] = a["thumb"]
            files.append(file)
        entry = {"label": f["label"], "meta": f"{len(items)} {ru_plural(len(items), 'статья', 'статьи', 'статей')}", "files": files}
        if f["key"] in FOLDER_ART:
            entry["image"] = FOLDER_ART[f["key"]]
        data.append(entry)

    fallback = "".join(
        f'<li><a href="stati/#{f["key"]}">{esc(f["label"])}</a></li>' for f in folders)
    block = f'''<!-- articles:start (собирается tools/build_articles.py) -->
  <section class="articles" id="articles" aria-labelledby="articles-title">
    <div class="articles__head">
      <h2 id="articles-title">Статьи</h2>
      <p>Разложили по&nbsp;папкам. Откройте папку, чтобы достать статьи.</p>
    </div>
    <div class="articles__grid" id="articles-folders">
      <ul class="articles__fallback">{fallback}</ul>
    </div>
    <a class="link-line articles__all" href="stati/">Все {total} {ru_plural(total, 'статья', 'статьи', 'статей')}</a>
    <script type="application/json" id="articles-data">{json.dumps(data, ensure_ascii=False)}</script>
    <script type="module" src="assets/articles.js"></script>
  </section>
  <!-- articles:end -->'''
    index_path = os.path.join(SITE, "index.html")
    s = open(index_path, encoding="utf-8").read()
    start, end = "<!-- articles:start", "<!-- articles:end -->"
    if start in s:
        a, b = s.index(start), s.index(end) + len(end)
        s = s[:a] + block + s[b:]
    else:
        marker = "  <!-- дальше по странице: о компании"
        s = s.replace(marker, "  " + block + "\n\n" + marker, 1)
    open(index_path, "w", encoding="utf-8").write(s)
    print(f"статей: {total}, папок: {len(folders)}")


if __name__ == "__main__":
    main()
