"""Scene 6 (28-32 s): end card. Ripple rings, title, counting stats, fade to black."""
import cv2
import numpy as np

from .fx import *

DUR, T0 = 4.0, 28.0
POST = dict(bloom=0.9, grain=0.03, chroma=1.5)

STATS = [(960, "FRAMES"), (6, "SCENES"), (0, "KEYFRAMES"), (1, "SYNTH SCORE")]


def draw(t):
    canvas = np.zeros((H, W, 3), np.uint8)
    c = (W // 2, H // 2 - 50)
    for k in range(7):
        p = (t * 0.35 + k / 7) % 1.0
        col = grad(k / 7 + t * 0.1) * 255 * (1 - p) ** 1.5 * 0.9
        cv2.circle(canvas, c, int(60 + p * 1150), tuple(int(v) for v in col), 2, cv2.LINE_AA)
    img = canvas.astype(np.float32) / 255.0 + BG

    cv2.circle(img, c, int(12 + 7 * pulse(t, 7.0)), tuple(float(v) for v in COL["coral"]), -1, cv2.LINE_AA)

    plate = np.clip(1 - np.hypot((np.arange(W)[None, :] - W / 2) / 1000, (np.arange(H)[:, None] - (H / 2 - 20)) / 330), 0, 1)
    img *= (1 - 0.6 * plate[..., None])

    draw_word_stagger(img, "MOTION GRAPHICS", W / 2, H / 2 - 70, 150, COL["cream"], t, 0.15, 0.035)
    draw_text(img, "WRITTEN AS CODE  ·  RENDERED IN PYTHON  ·  SCORED IN NUMPY", W / 2, H / 2 + 50, 26, COL["teal"],
              float(ease_out((t - 0.9) / 0.5)), kind="body", track=7)

    for i, (n, label) in enumerate(STATS):
        x = W / 2 + (i - 1.5) * 380
        a = float(ease_out((t - 1.2 - i * 0.12) / 0.5))
        v = int(round(n * float(ease_out_expo((t - 1.2 - i * 0.12) / 1.0))))
        draw_text(img, f"{v:,}", x, H / 2 + 190, 84, COL["cream"], a)
        draw_text(img, label, x, H / 2 + 262, 20, COL["yellow"], a * 0.9, kind="body", track=6)

    draw_text(img, "github.com/yanazhelyeznaya2000-ui/motiongraphics", W / 2, H - 70, 22, COL["cream"],
              float(ease_out((t - 1.8) / 0.6)) * 0.55, kind="body", track=3)
    img *= float(1 - ease_in((t - 3.2) / 0.8))
    return img
