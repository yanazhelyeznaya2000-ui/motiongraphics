"""Scene 3 (12-18 s): liquid glass. Nine metaballs with refraction, chromatic dispersion and fresnel."""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .fx import *

DUR, T0 = 6.0, 12.0
POST = dict(bloom=0.55, grain=0.03, chroma=1.5)

WH, HH = 960, 540
XH, YH = np.meshgrid(np.arange(WH, dtype=np.float32), np.arange(HH, dtype=np.float32))
NB = 9
rng = np.random.default_rng(21)
PH_ = rng.uniform(0, 2 * np.pi, (NB, 2))
FR = rng.uniform(0.25, 0.7, (NB, 2))
RAD = rng.uniform(40, 68, NB)


def _phrase_bg():
    f = ImageFont.truetype(FONTS["display"], 380)
    phrase = "GLASS   LIQUID   LIGHT   "
    u = int(f.getlength(phrase))
    im = Image.new("L", (u * 3, H), 0)
    d = ImageDraw.Draw(im)
    for k in range(3):
        d.text((k * u, H / 2 + 20), phrase, font=f, fill=255, anchor="lm")
    return np.asarray(im, np.float32) / 255, u


BGTXT, U = _phrase_bg()
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
GLOW = np.clip(1 - np.hypot((_xx - W / 2) / W, (_yy - H / 2) / H) * 1.6, 0, 1) ** 2
_LIGHT = np.array([-0.45, -0.6, 0.66], np.float32)
_LIGHT /= np.linalg.norm(_LIGHT)
_HALF = _LIGHT + np.array([0, 0, 1], np.float32)
_HALF /= np.linalg.norm(_HALF)


def _sm(a, b, v):
    s = np.clip((v - a) / (b - a), 0, 1)
    return s * s * (3 - 2 * s)


def draw(t):
    off = int((t * 70) % U)
    bg = np.empty((H, W, 3), np.float32)
    bg[:] = BG
    bg += GLOW[..., None] * np.array([0.05, 0.04, 0.10], np.float32)
    bg += BGTXT[:, off:off + W, None] * COL["cream"] * 0.13
    bgh = cv2.resize(bg, (WH, HH), interpolation=cv2.INTER_AREA)

    p = pulse(t, 6.0)
    f = np.zeros((HH, WH), np.float32)
    for i in range(NB):
        cx = WH / 2 + WH * 0.36 * np.sin(FR[i, 0] * t * 1.7 + PH_[i, 0])
        cy = HH / 2 + HH * 0.34 * np.sin(FR[i, 1] * t * 1.9 + PH_[i, 1])
        r = RAD[i] * (1 + 0.16 * p * (1 if i % 2 == 0 else -0.5))
        f += r * r / ((XH - cx) ** 2 + (YH - cy) ** 2 + 500)
    # grow in
    f *= float(ease_out_expo(t / 0.8))

    fc = np.minimum(f, 6.0)
    gy, gx = np.gradient(fc)
    inside = _sm(0.6, 1.2, f)
    amp = 260.0
    mapx = (XH - gx * amp * inside).astype(np.float32)
    mapy = (YH - gy * amp * inside).astype(np.float32)
    refr = cv2.remap(bgh, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

    k = 18.0
    nz = 1.0 / np.sqrt(1.0 + (gx * gx + gy * gy) * k * k)
    nx, ny = -gx * k * nz, -gy * k * nz
    diff = np.clip(nx * _LIGHT[0] + ny * _LIGHT[1] + nz * _LIGHT[2], 0, 1)
    spec = np.clip(nx * _HALF[0] + ny * _HALF[1] + nz * _HALF[2], 0, 1) ** 40
    fres = (1 - nz) ** 1.4
    env = grad(0.55 * nx + 0.35 * ny + 0.08 * t + fc * 0.02)
    shade = env * (0.20 + 0.85 * diff[..., None]) + spec[..., None] * 1.1 + fres[..., None] * COL["teal"] * 0.9
    col = refr * 0.55 + shade * 0.8

    # dispersion: each channel has its own iso-threshold, which fringes the edge with colour
    a = np.stack([_sm(0.86, 0.98, f), _sm(0.95, 1.07, f), _sm(1.04, 1.16, f)], -1)
    out = bgh * (1 - a) + col * a
    img = cv2.resize(out, (W, H), interpolation=cv2.INTER_CUBIC)

    hud(img, t, "02 / LIQUID GLASS", T0)
    draw_text(img, "REFRACTION  ·  DISPERSION  ·  FRESNEL", 80, H - 80, 22, COL["cream"],
              float(ease_out((t - 0.8) / 0.6)) * 0.7, kind="body", track=6, anchor="l")
    return img
