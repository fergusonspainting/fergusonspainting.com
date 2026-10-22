"""Make web-ready .webp copies of images/gallery/** into public/assets/img/gallery/**.

- Blurs house numbers, other businesses' names/phone numbers and bystanders (BLUR map below).
- Strips EXIF (location) by re-encoding.
- Writes <name>.webp (full, max 1600px) and <name>-sm.webp (600px thumbnail).

Run from the repo root:  python tools/optimize-images.py
"""
from pathlib import Path
from PIL import Image, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "images" / "gallery"
OUT = ROOT / "public" / "assets" / "img" / "gallery"

# (left, top, right, bottom) boxes in source-pixel coordinates
BLUR = {
    "painting-exterior/victorian-blue-repaint.jpg": [(678, 500, 722, 526)],
    "painting-exterior/ranch-repaint-dark-garage-door.jpg": [(605, 365, 660, 398)],
    "painting-exterior/gray-home-painting-in-progress.jpg": [(752, 555, 784, 620)],
    "painting-exterior/porch-home-painting-in-progress.jpg": [(585, 525, 645, 580), (300, 455, 360, 525)],
    "repairs/siding-repair-finished-gray.jpg": [(648, 612, 674, 690)],
    "repairs/gray-home-before-trim-repair.jpg": [(592, 555, 616, 618)],
    "commercial/retail-store-interior-finished.jpg": [
        (175, 220, 245, 255), (565, 300, 665, 345), (895, 335, 945, 365), (50, 520, 165, 645)],
    "commercial/retail-store-interior-prep.jpg": [(60, 358, 120, 388), (248, 362, 298, 392), (1232, 335, 1265, 365)],
    "commercial/pool-store-deck-build.jpg": [(945, 105, 1265, 255), (585, 390, 705, 490), (990, 465, 1050, 560)],
}

SIZES = ((1600, ""), (600, "-sm"))


def blur_regions(im, boxes):
    for box in boxes:
        region = im.crop(box)
        radius = max(6, min(region.size) // 3)
        im.paste(region.filter(ImageFilter.GaussianBlur(radius)), box)
    return im


def main():
    count = 0
    for src in sorted(SRC.rglob("*.jpg")):
        rel = src.relative_to(SRC).as_posix()
        im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
        im = blur_regions(im, BLUR.get(rel, []))
        dest = OUT / src.parent.relative_to(SRC)
        dest.mkdir(parents=True, exist_ok=True)
        for width, suffix in SIZES:
            copy = im.copy()
            copy.thumbnail((width, width), Image.LANCZOS)
            copy.save(dest / f"{src.stem}{suffix}.webp", "WEBP", quality=78, method=6)
        count += 1
    print(f"optimized {count} photos into {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
