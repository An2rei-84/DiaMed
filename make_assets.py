"""Разовая генерация статических ассетов: favicon.ico и og-cover.png.

Запуск: python make_assets.py (нужна Pillow). SVG-фавиконка написана руками.
"""

import math

from PIL import Image, ImageDraw, ImageFont

BLUE = (13, 110, 253, 255)
WHITE = (255, 255, 255, 255)


def heart_points(cx, cy, scale, n=240):
    """Классическая параметрическая кривая сердца."""
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x * scale, cy - y * scale))
    return pts


def draw_pulse(draw, points, color, width):
    draw.line(points, fill=color, width=width, joint="curve")
    r = width / 2
    for x, y in (points[0], points[-1]):
        draw.ellipse([x - r, y - r, x + r, y + r], fill=color)


# ---- favicon.ico (фолбэк для старых браузеров) ----
img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.polygon(heart_points(32, 30, 1.55), fill=BLUE)
draw_pulse(d, [(10, 28), (24, 28), (29, 19), (35, 40), (40, 28), (54, 28)], WHITE, 4)
img.save("static/favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
print("static/favicon.ico готов")

# ---- og-cover.png 1200x630 (карточка ссылки в мессенджерах) ----
W, H = 1200, 630
top, bottom = (102, 126, 234), (118, 75, 162)
cover = Image.new("RGB", (W, H))
px = cover.load()
for y in range(H):
    k = y / (H - 1)
    row = tuple(int(top[i] + (bottom[i] - top[i]) * k) for i in range(3))
    for x in range(W):
        px[x, y] = row

overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
od = ImageDraw.Draw(overlay)
od.polygon(heart_points(600, 260, 7.2), fill=WHITE)
draw_pulse(od, [(380, 250), (510, 250), (560, 185), (640, 320), (690, 250), (820, 250)], (13, 110, 253, 255), 14)
cover = Image.alpha_composite(cover.convert("RGBA"), overlay)

draw = ImageDraw.Draw(cover)
try:
    font_big = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 96)
    font_small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 40)
except OSError:
    font_big = font_small = ImageFont.load_default()


def center_text(y, text, font):
    box = draw.textbbox((0, 0), text, font=font)
    draw.text(((W - (box[2] - box[0])) / 2, y), text, font=font, fill=WHITE)


center_text(430, "DiaMed", font_big)
center_text(545, "Современная медицинская диагностика", font_small)
cover.convert("RGB").save("static/img/og-cover.png", optimize=True)
print("static/img/og-cover.png готов")
