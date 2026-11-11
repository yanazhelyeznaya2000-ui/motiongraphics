"""Scene 5 (24-28 s): a winding hex tunnel at speed with beat-locked type."""
import cv2
import numpy as np

from .fx import *

DUR, T0 = 4.0, 24.0
POST = dict(bloom=1.3, grain=0.03, chroma=2.5)

NR, NS = 34, 6
WORDS = ["NO TIMELINE", "NO PLUGINS", "NO PROBLEM", "JUST MATH."]


def _wob(z):
    return 0.9 * np.sin(0.21 * z) + 0.4 * np.sin(0.47 * z), 0.7 * np.sin(0.17 * z + 1.0)


def draw(t):
    canvas = np.zeros((H, W, 3), np.uint8)
    s = 6.0 * t + 0.6 * (1 - np.exp(-3 * t))
    d = ((np.arange(NR) - s) % NR) + 0.04
    d = np.sort(d)
    zw = d + s
    wx, wy = _wob(zw)
    cx0, cy0 = _wob(s)
    sc = 560.0
    R = sc / d
    cx = W / 2 + (wx - cx0) * sc / d
    cy = H / 2 + (wy - cy0) * sc / d
    ang = 0.30 * zw + 0.45 * t + 0.12 * pulse(t, 6.0)
    verts = ang[:, None] + np.arange(NS)[None, :] * 2 * np.pi / NS
    X = np.clip(cx[:, None] + R[:, None] * np.cos(verts), -30000, 30000)
    Y = np.clip(cy[:, None] + R[:, None] * np.sin(verts), -30000, 30000)

    base = grad(zw * 0.045 + t * 0.1)
    fade = np.clip(d / 0.6, 0, 1) * np.exp(-d * 0.075)
    cols = np.clip(base * fade[:, None] * 255, 0, 255).astype(np.uint8)

    for i in range(NR - 1, -1, -1):  # far to near
        c = tuple(int(v) for v in cols[i])
        th = int(np.clip(9 / d[i], 2, 16))
        pts = np.stack([X[i], Y[i]], 1).astype(np.int32)
        cv2.polylines(canvas, [pts], True, c, th, cv2.LINE_AA)
        if i + 1 < NR:
            c2 = tuple(int(v * 0.55) for v in cols[i])
            for j in range(0, NS, 2):
                cv2.line(canvas, (int(X[i, j]), int(Y[i, j])), (int(X[i + 1, j]), int(Y[i + 1, j])), c2, max(1, th // 2), cv2.LINE_AA)

    img = canvas.astype(np.float32) / 255.0 + BG
    k = min(int(t / 1.0), 3)
    u = t - k
    size = int(190 * (1 + 0.2 * (1 - float(ease_out_expo(u / 0.4)))))
    # a soft dark plate keeps the type readable over the tunnel
    plate = np.clip(1 - np.hypot((np.arange(W)[None, :] - W / 2) / 900, (np.arange(H)[:, None] - H / 2) / 190), 0, 1)
    img *= (1 - 0.55 * plate[..., None])
    draw_text(img, WORDS[k], W / 2, H / 2, size, COL["cream"], 0.97)
    hud(img, t, "04 / TUNNEL", T0)
    return img
