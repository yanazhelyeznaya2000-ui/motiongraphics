"""Shared engine: palette, easing (vectorised), text, additive point splatting, and the
post-processing stack (bloom, chromatic aberration, vignette, film grain, tone-map).

All scenes draw into a float32 RGB image (H, W, 3) with values around 0..1, and the
compositor runs `post()` on it to get the final uint8 frame.
"""
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 30
BEAT = 0.5  # 120 BPM

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FONTS = {
    "display": os.path.join(ROOT, "fonts", "InterDisplay-Black.otf"),
    "body": os.path.join(ROOT, "fonts", "Inter-Medium.otf"),
}

COL = {k: np.array(v, np.float32) for k, v in {
    "ink": (0.035, 0.040, 0.062),
    "panel": (0.10, 0.11, 0.15),
    "cream": (0.95, 0.93, 0.88),
    "coral": (1.00, 0.35, 0.30),
    "yellow": (1.00, 0.76, 0.29),
    "teal": (0.18, 0.80, 0.74),
    "violet": (0.55, 0.42, 1.00),
}.items()}
BG = COL["ink"]

_STOPS = [COL["coral"], COL["yellow"], COL["teal"], COL["violet"], COL["coral"]]
_XS = np.linspace(0, 1, 5)


def grad(t):
    """Looping colour gradient coral -> yellow -> teal -> violet -> coral. Any shape in, (...,3) out."""
    t = np.asarray(t, np.float32) % 1.0
    return np.stack([np.interp(t, _XS, [s[c] for s in _STOPS]) for c in range(3)], -1).astype(np.float32)


# --- easing (works on scalars and arrays) -------------------------------------------------
def clip01(x):
    return np.clip(x, 0.0, 1.0)


def ease_io(x):
    x = clip01(x)
    return np.where(x < 0.5, 4 * x ** 3, 1 - (-2 * x + 2) ** 3 / 2)


def ease_out(x):
    return 1 - (1 - clip01(x)) ** 3


def ease_in(x):
    return clip01(x) ** 3


def ease_out_expo(x):
    x = clip01(x)
    return 1 - 2.0 ** (-10 * x)


def ease_out_back(x, s=1.70158):
    x = clip01(x) - 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def pulse(t, k=7.0):
    """1.0 on every beat, decaying fast."""
    return float(np.exp(-(t % BEAT) * k))


# --- text ---------------------------------------------------------------------------------
_fc = {}


def font(kind, size):
    key = (kind, int(size))
    if key not in _fc:
        _fc[key] = ImageFont.truetype(FONTS[kind], int(size))
    return _fc[key]


def text_width(s, kind, size, track=0):
    return font(kind, size).getlength(s) + track * max(0, len(s) - 1)


def draw_text(img, s, x, y, size, color, alpha=1.0, kind="display", track=0, anchor="c"):
    """Blend text into img. y is the vertical centre of the capital letters.
    anchor 'c' centres on x, 'l' left-aligns at x, 'r' right-aligns at x."""
    if alpha <= 0 or not s:
        return
    f = font(kind, size)
    asc, desc = f.getmetrics()
    w = int(text_width(s, kind, size, track)) + 8
    h = asc + desc + 8
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    if track == 0:
        d.text((4, 4 + asc), s, font=f, fill=255, anchor="ls")
    else:
        cx = 4.0
        for ch in s:
            d.text((cx, 4 + asc), ch, font=f, fill=255, anchor="ls")
            cx += f.getlength(ch) + track
    a = np.asarray(m, np.float32) / 255.0 * float(alpha)
    x0 = int({"c": x - w / 2, "l": x - 4, "r": x - w + 4}[anchor])
    y0 = int(y + 0.364 * size - (4 + asc))
    ih, iw = img.shape[:2]
    cx0, cy0, cx1, cy1 = max(x0, 0), max(y0, 0), min(x0 + w, iw), min(y0 + h, ih)
    if cx1 <= cx0 or cy1 <= cy0:
        return
    a = a[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0, None]
    reg = img[cy0:cy1, cx0:cx1]
    reg[:] = reg * (1 - a) + np.asarray(color, np.float32) * a


def draw_word_stagger(img, s, cx, cy, size, color, t, t0, stagger=0.04, kind="display", dur=0.6, rise=70):
    """Letters rise and fade in one after another."""
    f = font(kind, size)
    x = cx - f.getlength(s) / 2
    for i, ch in enumerate(s):
        if ch == " ":
            continue
        xi = x + f.getlength(s[:i])
        wi = f.getlength(s[:i + 1]) - f.getlength(s[:i])
        p = float(ease_out_expo((t - t0 - i * stagger) / dur))
        if p > 0:
            draw_text(img, ch, xi + wi / 2, cy + (1 - p) * rise, size, color, alpha=p, kind=kind)


def hud(img, t, label, t0):
    """Editorial corner furniture: scene label top-left, timecode top-right."""
    a = float(ease_out(t / 0.5)) * 0.85
    draw_text(img, label, 80, 78, 24, COL["cream"], a, kind="body", track=6, anchor="l")
    img[104:106, 80:80 + int(280 * ease_out(t / 0.7))] = COL["cream"] * 0.5
    g = t0 + t
    tc = f"{int(g // 60):02d}:{int(g % 60):02d}:{int((g % 1) * FPS):02d}"
    draw_text(img, tc, W - 80, 78, 24, COL["cream"], a * 0.8, kind="body", track=4, anchor="r")


def paste(img, patch, x0, y0):
    ph, pw = patch.shape[:2]
    x0, y0 = int(x0), int(y0)
    cx0, cy0, cx1, cy1 = max(x0, 0), max(y0, 0), min(x0 + pw, img.shape[1]), min(y0 + ph, img.shape[0])
    if cx1 > cx0 and cy1 > cy0:
        img[cy0:cy1, cx0:cx1] = patch[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0]


# --- additive point splatting ----------------------------------------------------------------
def splat(img, x, y, col, w=1.0):
    """Add coloured points to img (nearest pixel, additive). col: (N,3) or (3,), w: scalar or (N,)."""
    ix = np.rint(x).astype(np.int64)
    iy = np.rint(y).astype(np.int64)
    m = (ix >= 0) & (ix < W) & (iy >= 0) & (iy < H)
    idx = iy[m] * W + ix[m]
    col = np.broadcast_to(col, (len(x), 3))[m]
    ww = w if np.isscalar(w) else np.asarray(w)[m]
    for c in range(3):
        img[..., c] += np.bincount(idx, weights=col[:, c] * ww, minlength=W * H).reshape(H, W).astype(np.float32)


# --- post-processing -------------------------------------------------------------------------
_VIG = None
_NOISE = None


def _prep():
    global _VIG, _NOISE
    if _VIG is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        _VIG = (1 - 0.34 * np.clip(d - 0.35, 0, 1) ** 1.6).astype(np.float32)
        rng = np.random.default_rng(3)
        _NOISE = [cv2.resize(rng.standard_normal((H // 2, W // 2)).astype(np.float32), (W, H),
                             interpolation=cv2.INTER_LINEAR) for _ in range(6)]


def post(img, t, kick=0.0, bloom=0.9, grain=0.03, chroma=1.5, vignette=True):
    """float32 image -> uint8 frame. `kick` (0..1) is the cut-impact: flash + colour split."""
    _prep()
    img = np.maximum(img, 0)
    if bloom > 0:
        small = cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        g = cv2.GaussianBlur(np.maximum(small - 0.5, 0), (0, 0), 7)
        g += 0.7 * cv2.GaussianBlur(np.maximum(small - 0.25, 0), (0, 0), 20)
        img = img + cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR) * bloom
    s = int(round(chroma + 10 * kick))
    if s > 0:
        img = np.stack([np.roll(img[..., 0], s, 1), img[..., 1], np.roll(img[..., 2], -s, 1)], -1)
    if vignette:
        img = img * _VIG[..., None]
    img = img + _NOISE[int(t * FPS) % 6][..., None] * grain
    img = img + kick * 0.22
    img = img / (1 + 0.18 * img) * 1.18
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)
