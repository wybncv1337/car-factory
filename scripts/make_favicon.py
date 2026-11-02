"""Регенерация PNG-иконок сайта из той же геометрии, что и static/favicon.svg.

Запуск: python scripts/make_favicon.py
"""

from pathlib import Path

from PIL import Image, ImageDraw

TILE = 64
SUPERSAMPLE = 4
CORNER_RADIUS = 14
COLOR_TOP = (99, 102, 241)  # индиго
COLOR_BOTTOM = (162, 28, 175)  # пурпур
CENTER = (20, 44)
DOT_RADIUS = 6.5
RINGS = ((14, 6, 255), (27, 6, 128))  # радиус, толщина, непрозрачность дуги

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
SCALE = TILE * SUPERSAMPLE


def scale(value):
    return round(value * SCALE / TILE)


def gradient():
    """Диагональный градиент из двух цветов."""
    image = Image.new("RGBA", (SCALE, SCALE))
    pixels = image.load()
    for y in range(SCALE):
        for x in range(SCALE):
            ratio = (x + y) / (2 * (SCALE - 1))
            pixels[x, y] = tuple(round(a + (b - a) * ratio) for a, b in zip(COLOR_TOP, COLOR_BOTTOM)) + (255,)
    return image


def mark():
    """Белый «радар»: точка и две расходящиеся дуги."""
    layer = Image.new("RGBA", (SCALE, SCALE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    cx, cy = scale(CENTER[0]), scale(CENTER[1])
    dot = scale(DOT_RADIUS)
    draw.ellipse((cx - dot, cy - dot, cx + dot, cy + dot), fill=(255, 255, 255, 255))
    for radius, width, alpha in RINGS:
        # PIL рисует штрих внутрь ограничивающего круга, поэтому внешний край — r + width/2.
        outer = scale(radius + width / 2)
        bbox = (cx - outer, cy - outer, cx + outer, cy + outer)
        draw.arc(bbox, start=270, end=360, fill=(255, 255, 255, alpha), width=scale(width))
        cap, middle = scale(width / 2), scale(radius)
        for px, py in ((cx, cy - middle), (cx + middle, cy)):
            draw.ellipse((px - cap, py - cap, px + cap, py + cap), fill=(255, 255, 255, alpha))
    return layer


def rounded_mask():
    mask = Image.new("L", (SCALE, SCALE), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, SCALE - 1, SCALE - 1), radius=scale(CORNER_RADIUS), fill=255)
    return mask


def save(name, size, background, rounded):
    icon = Image.alpha_composite(background, mark())
    if rounded:
        icon.putalpha(rounded_mask())
    icon.resize((size, size), Image.LANCZOS).save(STATIC_DIR / name)
    print(f"✅ {STATIC_DIR / name}")


def main():
    canvas = gradient()
    solid = canvas.copy()
    solid.putalpha(255)  # apple-touch-icon не должен иметь прозрачных углов
    save("favicon.png", 48, canvas, rounded=True)
    save("apple-touch-icon.png", 180, solid, rounded=False)


if __name__ == "__main__":
    main()
