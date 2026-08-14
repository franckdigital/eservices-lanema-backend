"""One-off script to generate distinct illustration images for the seeded
news articles (gradient background + emoji icon), so each article gets a
visually distinct thumbnail instead of reusing the lab photo. Run manually:
    python generate_illustrations.py
"""
from PIL import Image, ImageDraw, ImageFont
import os

SIZE = (1200, 800)
FONT_PATH = "C:/Windows/Fonts/seguiemj.ttf"

SLIDES = [
    {
        "filename": "securite-alimentaire.png",
        "colors": ((6, 95, 70), (16, 185, 129)),  # emerald
        "emoji": "\U0001F9EA",  # 🧪
    },
    {
        "filename": "metrologie-carburant.png",
        "colors": ((0, 35, 48), (0, 132, 224)),  # lanema blue
        "emoji": "⛽",  # ⛽
    },
    {
        "filename": "accreditation-iso.png",
        "colors": ((49, 46, 129), (99, 102, 241)),  # indigo
        "emoji": "\U0001F3C5",  # 🏅
    },
    {
        "filename": "portes-ouvertes.png",
        "colors": ((120, 53, 15), (245, 158, 11)),  # amber
        "emoji": "\U0001F3DB",  # 🏛
    },
]


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def make_gradient(size, c1, c2):
    w, h = size
    img = Image.new("RGB", size, c1)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        # diagonal-ish gradient by mixing x influence
        draw.line([(0, y), (w, y)], fill=lerp(c1, c2, t))
    return img


def add_decorations(img):
    draw = ImageDraw.Draw(img, "RGBA")
    w, h = img.size
    draw.ellipse([w - 260, -120, w + 140, 260], fill=(255, 255, 255, 18))
    draw.ellipse([-150, h - 220, 220, h + 150], fill=(255, 255, 255, 14))
    draw.ellipse([w * 0.55, h * 0.45, w * 0.55 + 320, h * 0.45 + 320], fill=(255, 255, 255, 10))
    return img


def add_icon(img, emoji):
    w, h = img.size
    font = ImageFont.truetype(FONT_PATH, 220)
    draw = ImageDraw.Draw(img, "RGBA")
    bbox = draw.textbbox((0, 0), emoji, font=font, embedded_color=True)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pos = ((w - tw) / 2 - bbox[0], (h - th) / 2 - bbox[1])
    draw.text(pos, emoji, font=font, embedded_color=True)
    return img


def main():
    out_dir = os.path.dirname(__file__)
    for s in SLIDES:
        img = make_gradient(SIZE, s["colors"][0], s["colors"][1])
        img = add_decorations(img)
        img = add_icon(img, s["emoji"])
        path = os.path.join(out_dir, s["filename"])
        img.save(path, "JPEG" if path.endswith(".jpg") else "PNG", quality=88)
        print("generated", path)


if __name__ == "__main__":
    main()
