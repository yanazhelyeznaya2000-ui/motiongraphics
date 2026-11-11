"""Scene 2 (6-12 s): beat-locked kinetic type, then a modular grid of six live mini-animations."""
import cv2
import numpy as np

from .fx import *

DUR, T0 = 6.0, 6.0
POST = dict(bloom=0.12, grain=0.035, chroma=1.5)

WORDS = ["THIS", "WHOLE", "VIDEO", "IS", "CODE."]
BGS = [COL["cream"], COL["coral"], COL["ink"], COL["yellow"], COL["teal"]]
FGS = [COL["ink"], COL["cream"], COL["cream"], COL["ink"], COL["ink"]]
GRID_START = 2.5

PW, PH, GAP, MARGIN = 592, 480, 24, 48
LABELS = ["NOISE", "RHYTHM", "TYPE", "WAVES", "GRIDS", "ROTATION"]


def _words(t):
    k = min(int(t / BEAT), 4)
    u = (t - k * BEAT) / BEAT
    img = np.empty((H, W, 3), np.float32)
    img[:] = BGS[k - 1] if k > 0 else BG
    edge = int(W * float(ease_out_expo(u / 0.3)))
    img[:, :edge] = BGS[k]
    word = WORDS[k]
    size = 600
    size = min(size, int(size * 1650 / text_width(word, "display", size)))
    size = int(size * (1 + 0.16 * (1 - float(ease_out_expo(u / 0.45)))))
    if u > 0.04:
        draw_text(img, word, W / 2, H / 2 + 10, size, FGS[k])
    draw_text(img, f"0{k + 1} / 05", 80, 78, 24, FGS[k], 0.8, kind="body", track=6, anchor="l")
    img[H - 60:H - 54, 0:int(W * (t / GRID_START))] = FGS[k]
    return img


# --- the six panels -----------------------------------------------------------------------------
def _u8(c):
    return tuple(int(v * 255) for v in c)


def _patch(color):
    p = np.empty((PH, PW, 3), np.uint8)
    p[:] = _u8(color)
    return p


def _p_orbits(t):
    p = _patch(COL["panel"])
    c = (PW // 2, PH // 2 - 24)
    for r, sp, col in ((70, 1.4, "coral"), (125, -0.9, "yellow"), (180, 0.6, "teal")):
        cv2.circle(p, c, r, _u8(COL["cream"] * 0.25), 2, cv2.LINE_AA)
        a = t * sp * 2 + r
        cv2.circle(p, (int(c[0] + r * np.cos(a)), int(c[1] + r * np.sin(a))), int(12 + 5 * pulse(t)), _u8(COL[col]), -1, cv2.LINE_AA)
    cv2.circle(p, c, int(14 + 6 * pulse(t)), _u8(COL["cream"]), -1, cv2.LINE_AA)
    return p.astype(np.float32) / 255


def _p_bars(t):
    p = _patch(COL["coral"])
    n, bw = 14, 30
    x0 = (PW - n * (bw + 10) + 10) // 2
    for i in range(n):
        h = (0.18 + 0.72 * abs(np.sin(t * 3 + i * 0.7)) * (0.75 + 0.25 * pulse(t))) * 320
        cv2.rectangle(p, (x0 + i * (bw + 10), int(PH - 100 - h)), (x0 + i * (bw + 10) + bw, PH - 100), _u8(COL["ink"]), -1)
    return p.astype(np.float32) / 255


def _p_type(t):
    img = np.empty((PH, PW, 3), np.float32)
    img[:] = COL["cream"]
    draw_text(img, "Aa", PW / 2, PH / 2 - 24, int(300 * (1 + 0.05 * pulse(t))), COL["ink"])
    return img


def _p_waves(t):
    p = _patch(COL["teal"])
    xs = np.arange(0, PW, 4)
    for k in range(4):
        ys = PH / 2 - 24 + np.sin(xs * 0.02 + t * (1.5 + k * 0.4) + k) * (50 + 22 * k) * (0.8 + 0.3 * pulse(t))
        pts = np.stack([xs, ys], 1).astype(np.int32)
        cv2.polylines(p, [pts], False, _u8(COL["ink"] if k % 2 == 0 else COL["cream"]), 5, cv2.LINE_AA)
    return p.astype(np.float32) / 255


def _p_dots(t):
    p = _patch(COL["yellow"])
    cols, rows = 13, 7
    for i in range(cols):
        for j in range(rows):
            x, y = 56 + i * 40, 56 + j * 44 + 8
            d = np.hypot(x - PW / 2, y - PH / 2)
            r = 3 + 14 * (0.5 + 0.5 * np.sin(d * 0.045 - t * 4))
            cv2.circle(p, (x, y), int(r), _u8(COL["ink"]), -1, cv2.LINE_AA)
    return p.astype(np.float32) / 255


def _p_squares(t):
    p = _patch(COL["violet"])
    c = np.array([PW / 2, PH / 2 - 24])
    for i in range(7):
        s = 40 + i * 28 + 12 * pulse(t)
        a = t * 0.5 * (i + 1) * 0.5 + i * 0.3
        v = np.array([[np.cos(a + k * np.pi / 2), np.sin(a + k * np.pi / 2)] for k in range(4)]) * s * 1.41 + c
        cv2.polylines(p, [v.astype(np.int32)], True, _u8(COL["cream"]), 3, cv2.LINE_AA)
    return p.astype(np.float32) / 255


PANELS = [_p_orbits, _p_bars, _p_type, _p_waves, _p_dots, _p_squares]
LABEL_COL = [COL["cream"], COL["ink"], COL["ink"], COL["ink"], COL["ink"], COL["cream"]]


def _grid(t):
    img = np.empty((H, W, 3), np.float32)
    img[:] = BG
    for i, fn in enumerate(PANELS):
        e = float(ease_out_back((t - GRID_START - i * 0.2) / 0.5))
        if e <= 0.02:
            continue
        patch = fn(t)
        draw_text(patch, f"0{i + 1}  {LABELS[i]}", 30, PH - 38, 24, LABEL_COL[i], 0.9, kind="body", track=5, anchor="l")
        col, row = i % 3, i // 3
        cx = MARGIN + col * (PW + GAP) + PW / 2
        cy = MARGIN + row * (PH + GAP) + PH / 2
        w, h = max(2, int(PW * e)), max(2, int(PH * e))
        patch = cv2.resize(patch, (w, h), interpolation=cv2.INTER_AREA if e < 1 else cv2.INTER_LINEAR)
        paste(img, patch, cx - w / 2, cy - h / 2)
    return img


def draw(t):
    img = _words(t) if t < GRID_START else _grid(t)
    return img
