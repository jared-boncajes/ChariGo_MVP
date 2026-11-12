"""Rebuild the web-ready photos in static/images/opt/ from the originals.

Run from the project root after adding or replacing a photo:

    python -m pip install -r requirements-dev.txt   # once (needs numpy)
    python scripts/optimize_images.py

The originals in static/images/ are never modified. The app serves the WebP
copies written here (see image_url in app.py). To use a sharper photo, save it
under the same file name in static/images/ and run this script again.

What it does:
  * crops baked-in clutter (a partner's watermark, an ad panel);
  * enlarges small photos 2x with a high-quality filter and light sharpening,
    which browsers show more crisply than they stretch the small original;
  * builds the Angat Buhay banner as a wide brand-colour composite, so the
    photo is shown near its real size instead of being stretched across
    the whole screen;
  * re-encodes everything as WebP.
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "static" / "images"
OUT = SRC / "opt"

# Box = (left, top, right, bottom) in original pixels.
CROPS = {
    "hunger": (0, 0, 203, 172),  # drop the "Our mission is to end hunger" panel
    "animals": (0, 0, 360, 440),  # drop a stock-site logo in the corner
}
# Below this width a photo is enlarged 2x before encoding.
ENLARGE_BELOW = 700
BANNER_PHOTO = "community"
BANNER_SIZE = (1600, 640)


def enlarge(image):
    image = image.resize((image.width * 2, image.height * 2), Image.LANCZOS)
    return image.filter(ImageFilter.UnsharpMask(radius=1.6, percent=55, threshold=2))


def save(image, name, quality=84):
    OUT.mkdir(exist_ok=True)
    image.save(OUT / f"{name}.webp", "WEBP", quality=quality, method=6)


def banner():
    """Brand gradient on the left, the photo fading in from the right."""
    width, height = BANNER_SIZE
    photo = Image.open(SRC / f"{BANNER_PHOTO}.png").convert("RGB")
    photo = enlarge(photo)
    scale = height / photo.height
    photo = photo.resize((round(photo.width * scale), height), Image.LANCZOS)

    left, right = (176, 46, 86), (247, 116, 146)  # deep pink to ChariGo pink
    ramp = np.linspace(0, 1, width)[None, :, None]
    gradient = np.array(left) + (np.array(right) - np.array(left)) * ramp
    gradient = np.repeat(gradient, height, axis=0)
    # A little noise hides the visible stripes a smooth 8-bit gradient shows.
    noise = np.random.default_rng(7).normal(0, 1.6, gradient.shape)
    canvas = Image.fromarray(np.clip(gradient + noise, 0, 255).astype("uint8"))
    # Place the photo on the right and fade its left edge into the gradient.
    mask = Image.new("L", photo.size, 255)
    fade = min(photo.width // 2, 520)
    mask_draw = ImageDraw.Draw(mask)
    for x in range(fade):
        mask_draw.line([(x, 0), (x, photo.height)], fill=round(255 * (x / fade) ** 1.4))
    canvas.paste(photo, (width - photo.width, 0), mask)
    save(canvas, "angat-buhay", quality=90)


def main():
    for path in sorted(SRC.iterdir()):
        if path.suffix.lower() not in {".png", ".jpg"}:
            continue
        stem = path.stem
        if stem == "angat-buhay":
            continue  # built by banner()
        image = Image.open(path)
        if stem == "logo":
            image = image.convert("RGBA")
            image.thumbnail((192, 192), Image.LANCZOS)
            save(image, stem, quality=90)
            continue
        image = image.convert("RGB")
        if stem in CROPS:
            image = image.crop(CROPS[stem])
        if image.width < ENLARGE_BELOW:
            image = enlarge(image)
        image.thumbnail((1280, 1280), Image.LANCZOS)
        save(image, stem)
    banner()
    sizes = sum(p.stat().st_size for p in OUT.glob("*.webp"))
    print(f"Wrote {len(list(OUT.glob('*.webp')))} images, {sizes // 1024} KB in total.")


if __name__ == "__main__":
    main()
