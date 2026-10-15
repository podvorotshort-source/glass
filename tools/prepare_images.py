"""Готовит фото каталога для сайта: кадр 3:4, WebP, два размера.

Источник — tools/catalog_photos.json (пути к оригиналам в source/).
Результат — site/assets/catalog/<направление>-<n>.webp
"""
import json, os
from PIL import Image, ImageOps

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "site", "assets", "catalog")
SIZES = {"": 960, "-s": 480}   # основной кадр и превью

def main():
    os.makedirs(OUT, exist_ok=True)
    photos = json.load(open(os.path.join(ROOT, "tools", "catalog_photos.json"), encoding="utf-8"))
    for cat, paths in photos.items():
        for n, rel in enumerate(paths, 1):
            im = ImageOps.exif_transpose(Image.open(os.path.join(ROOT, rel))).convert("RGB")
            for suffix, w in SIZES.items():
                fit = ImageOps.fit(im, (w, w * 4 // 3), Image.LANCZOS, centering=(0.5, 0.45))
                fit.save(os.path.join(OUT, f"{cat}-{n}{suffix}.webp"), quality=80, method=6)
            print(cat, n, im.size)

if __name__ == "__main__":
    main()
