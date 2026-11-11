"""A drawing surface for one video frame.

Everything is drawn at SS x the output size and scaled down at the end, which gives
smooth (anti-aliased) edges with plain Pillow. Coordinates you pass in are always in
output pixels (1920x1080), so scenes never need to think about supersampling.
"""
import os
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 30
SS = 2  # supersampling factor

PALETTE = {
    "bg": (14, 15, 19),
    "cream": (242, 237, 228),
    "coral": (255, 90, 78),
    "teal": (46, 196, 182),
    "yellow": (255, 194, 75),
    "dim": (70, 72, 82),
}

_HERE = os.path.dirname(os.path.abspath(__file__))
_FONT_DIR = os.path.join(_HERE, "..", "fonts")
FONTS = {
    "display": "InterDisplay-Black.otf",
    "body": "Inter-Medium.otf",
}


def mix(a, b, p):
    """Blend colour a toward colour b by p (0..1)."""
    p = max(0.0, min(1.0, p))
    return tuple(int(round(x + (y - x) * p)) for x, y in zip(a, b))


@lru_cache(maxsize=64)
def font(kind, size):
    path = os.path.join(_FONT_DIR, FONTS[kind])
    return ImageFont.truetype(path, int(size * SS))


def text_width(s, kind, size):
    return font(kind, size).getlength(s) / SS


class Frame:
    def __init__(self, bg=PALETTE["bg"]):
        self.bg = bg
        self.img = Image.new("RGB", (W * SS, H * SS), bg)
        self.d = ImageDraw.Draw(self.img)

    # --- shapes -------------------------------------------------------------
    def circle(self, cx, cy, r, fill):
        if r <= 0:
            return
        s = SS
        self.d.ellipse([(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s], fill=fill)

    def ring(self, cx, cy, r, width, color):
        if r <= 0 or width <= 0:
            return
        s = SS
        self.d.ellipse(
            [(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s],
            outline=color, width=max(1, int(width * s)),
        )

    def rect(self, x0, y0, x1, y1, fill):
        if x1 <= x0 or y1 <= y0:
            return
        s = SS
        self.d.rectangle([x0 * s, y0 * s, x1 * s, y1 * s], fill=fill)

    def fill(self, color):
        self.rect(0, 0, W, H, color)

    # --- text ---------------------------------------------------------------
    def text(self, x, y, s, size, color, kind="body", anchor="ls"):
        self.d.text((x * SS, y * SS), s, font=font(kind, size), fill=color, anchor=anchor)

    def text_reveal(self, x, baseline, s, size, color, p, kind="display"):
        """Draw text rising into view from behind an invisible line.

        p=0 hidden, p=1 fully in place. Use p in 1..2 to keep rising and exit out the top.
        x is the left edge, baseline is the text baseline (output pixels).
        """
        if p <= 0 or p >= 2:
            return
        f = font(kind, size)
        asc, desc = f.getmetrics()
        w = int(f.getlength(s)) + 4
        h = asc + desc
        layer = Image.new("L", (w, h), 0)
        # 0..1: slide up from below the window; 1..2: slide up out of the top.
        offset = (1 - p) * h if p <= 1 else -(p - 1) * h
        ImageDraw.Draw(layer).text((0, offset), s, font=f, fill=255)
        top = int(baseline * SS) - asc
        self.img.paste(color, (int(x * SS), top, int(x * SS) + w, top + h), layer)

    # --- output -------------------------------------------------------------
    def finish(self):
        return self.img.resize((W, H), Image.LANCZOS)
