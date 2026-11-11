"""Scene 1 (0-6 s): 70,000 particles swirl, then snap into the word MOTION, pulse on the beat, explode."""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .fx import *

DUR, T0 = 6.0, 0.0
POST = dict(bloom=1.0, grain=0.03, chroma=1.5)

N = 70000
rng = np.random.default_rng(11)


def _text_points(s, size, n):
    f = ImageFont.truetype(FONTS["display"], size)
    im = Image.new("L", (W, H), 0)
    ImageDraw.Draw(im).text((W / 2, H / 2 - 10), s, font=f, fill=255, anchor="mm")
    ys, xs = np.nonzero(np.asarray(im) > 128)
    i = rng.integers(0, len(xs), n)
    return xs[i] + rng.normal(0, 0.7, n), ys[i] + rng.normal(0, 0.7, n)


TX, TY = _text_points("MOTION", 340, N)
TH0 = rng.uniform(0, 2 * np.pi, N)
R0 = np.sqrt(rng.uniform(0.0, 1, N)) * 950
DELAY = rng.uniform(0, 1, N)
SEED = rng.uniform(0, 2 * np.pi, N)
EXPL = rng.normal(0, 1, (N, 2)).astype(np.float32)
SPD = rng.uniform(0.4, 1.6, N).astype(np.float32)
OM = 0.5 + 1.4 * (1 - R0 / 950)
COLU = (TX / W * 0.9).astype(np.float32)


def draw(t):
    img = np.zeros((H, W, 3), np.float32) + BG

    th = TH0 + OM * t
    sr = R0 * (1 + 0.06 * np.sin(t * 2 + SEED * 3))
    sx = W / 2 + np.cos(th) * sr
    sy = H / 2 + np.sin(th) * sr * 0.62

    e = ease_io((t - 0.9 - DELAY * 1.3) / 1.5).astype(np.float32)
    x = sx + (TX - sx) * e
    y = sy + (TY - sy) * e

    # shimmer + beat pulse once formed
    shim = np.sin(t * 9 + SEED * 5) * 1.6 * e
    x += shim
    y += np.cos(t * 7 + SEED * 3) * 1.6 * e
    p = pulse(t, 8.0) * 0.016 * (t > 2.4)
    x += (x - W / 2) * p * e
    y += (y - H / 2) * p * e

    # explosion
    ex = max(t - 4.6, 0.0)
    if ex > 0:
        x += EXPL[:, 0] * SPD * ex ** 2 * 520 + (x - W / 2) * ex * 0.8
        y += EXPL[:, 1] * SPD * ex ** 2 * 520 + (y - H / 2) * ex * 0.8

    appear = float(clip01(t / 0.5))
    fade = float(1 - clip01((t - 5.3) / 0.7))
    col = grad(COLU + t * 0.04 + 0.15 * np.sin(SEED))
    splat(img, x, y, col, 2.6 * appear * fade)
    img = cv2.GaussianBlur(img, (0, 0), 0.8)

    draw_text(img, "EVERY PIXEL, COMPUTED.", W / 2, H / 2 + 270, 30, COL["cream"],
              float(ease_out((t - 3.0) / 0.6)) * 0.8 * fade, kind="body", track=10)
    hud(img, t, "01 / PARTICLES  70,000", T0)
    return img
