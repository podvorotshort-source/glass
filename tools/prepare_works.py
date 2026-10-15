"""Фото для раздела «Работы»: превью 3:4 (600×800) и большое для просмотра.

Источник — tools/works_photos.json. Результат — site/assets/works/ и
site/assets/works/works.json (список для страницы).
"""
import json, os
from PIL import Image, ImageOps

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "site", "assets", "works")

def main():
    os.makedirs(OUT, exist_ok=True)
    photos = json.load(open(os.path.join(ROOT, "tools", "works_photos.json"), encoding="utf-8"))
    items = []
    for cat, paths in photos.items():
        for n, rel in enumerate(paths, 1):
            im = ImageOps.exif_transpose(Image.open(os.path.join(ROOT, rel))).convert("RGB")
            ImageOps.fit(im, (600, 800), Image.LANCZOS, centering=(0.5, 0.45)).save(
                os.path.join(OUT, f"{cat}-{n}.webp"), quality=78, method=6)
            big = im.copy()
            big.thumbnail((1400, 1400), Image.LANCZOS)
            big.save(os.path.join(OUT, f"{cat}-{n}-l.webp"), quality=82, method=6)
            items.append({"cat": cat, "src": f"assets/works/{cat}-{n}.webp",
                          "big": f"assets/works/{cat}-{n}-l.webp", "w": big.width, "h": big.height})
    json.dump(items, open(os.path.join(OUT, "works.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(len(items), "фото")

if __name__ == "__main__":
    main()


# ---- раздел «Работы» в site/index.html (между <!-- works:start/end -->) ----
CATS = [("peregorodki", "Перегородки", "Стеклянная перегородка"),
        ("dushevye", "Душевые", "Душевая из стекла"),
        ("ograzhdeniya", "Ограждения", "Стеклянное ограждение"),
        ("lestnicy", "Лестницы", "Лестница со стеклянным ограждением"),
        ("dveri", "Двери", "Стеклянная дверь"),
        ("loft", "Лофт", "Перегородка в стиле лофт"),
        ("interer", "Интерьер", "Стекло в интерьере")]
SHOW_FIRST = 12  # в «Все» сначала видно 12, остальные по кнопке


def inject():
    items = json.load(open(os.path.join(OUT, "works.json"), encoding="utf-8"))
    by_cat = {c: [i for i in items if i["cat"] == c] for c, *_ in CATS}
    # «Все»: по очереди из каждого направления, чтобы сетка была разнообразной
    mixed, k = [], 0
    while len(mixed) < len(items):
        for c, *_ in CATS:
            if k < len(by_cat[c]):
                mixed.append(by_cat[c][k])
        k += 1
    names = {c: (t, alt) for c, t, alt in CATS}
    tiles = []
    for n, it in enumerate(mixed):
        title, alt = names[it["cat"]]
        hidden = ' data-more' if n >= SHOW_FIRST else ''
        tiles.append(
            f'      <li class="work" data-cat="{it["cat"]}"{hidden}>'
            f'<a href="{it["big"]}" data-w="{it["w"]}" data-h="{it["h"]}">'
            f'<img src="{it["src"]}" width="600" height="800" alt="{alt}" loading="lazy" decoding="async">'
            f'<span class="work__cat">{title}</span></a></li>')
    chips = ['        <button type="button" class="chip" data-filter="all" aria-pressed="true">Все</button>'] + [
        f'        <button type="button" class="chip" data-filter="{c}" aria-pressed="false">{t}</button>' for c, t, _ in CATS]
    block = f'''<!-- works:start (собирается tools/prepare_works.py) -->
  <section class="works" id="works" aria-labelledby="works-title">
    <div class="works__head">
      <h2 id="works-title">Работы</h2>
      <p>Объекты в&nbsp;Тольятти, Самаре и&nbsp;области: квартиры, дома, офисы.</p>
    </div>
    <div class="works__filter" role="group" aria-label="Фильтр по направлениям">
{chr(10).join(chips)}
    </div>
    <ul class="works__grid">
{chr(10).join(tiles)}
    </ul>
    <button type="button" class="btn btn--ghost works__more">
      <span class="btn__glint" aria-hidden="true"></span><span class="btn__frame" aria-hidden="true"></span>
      <span class="btn__label">Показать ещё</span>
    </button>
  </section>
  <!-- works:end -->'''
    path = os.path.join(ROOT, "site", "index.html")
    s = open(path, encoding="utf-8").read()
    start, end = "<!-- works:start", "<!-- works:end -->"
    if start in s:
        a, b = s.index(start), s.index(end) + len(end)
        s = s[:a] + block + s[b:]
    else:
        marker = "<!-- articles:start"
        s = s.replace(marker, block + "\n\n  " + marker, 1)
    open(path, "w", encoding="utf-8").write(s)
    print("раздел «Работы» обновлён")


if __name__ == "__main__":
    inject()
