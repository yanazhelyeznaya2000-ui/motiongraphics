"""Scene 1: a dot grid ripples in, three circles pop and orbit, then coral floods the screen."""
import math

from motion import Frame, W, H, PALETTE, mix
from motion.easing import progress, out_back, out_cubic, in_out_cubic, in_cubic, lerp

DURATION = 3.0
CX, CY = W / 2, H / 2
COLS, ROWS = 17, 10
GAP = 110


def draw(t):
    f = Frame()
    bg, dim = PALETTE["bg"], PALETTE["dim"]
    exit_p = in_cubic(progress(t, 2.2, 0.55))  # everything collapses toward the centre

    # Dot grid: a radial wave switches each dot on, then it breathes.
    gx0 = CX - (COLS - 1) * GAP / 2
    gy0 = CY - (ROWS - 1) * GAP / 2
    for i in range(COLS):
        for j in range(ROWS):
            x, y = gx0 + i * GAP, gy0 + j * GAP
            dist = math.hypot(x - CX, y - CY)
            on = out_back(progress(t, dist / 1400, 0.45))
            breathe = 1 + 0.35 * math.sin(t * 5 - dist / 120)
            r = 5 * on * breathe * (1 - exit_p)
            x, y = lerp(x, CX, exit_p), lerp(y, CY, exit_p)
            f.circle(x, y, r, mix(bg, dim, min(1, on)))

    # Three circles pop in, orbit, then fall into the centre.
    colors = [PALETTE["coral"], PALETTE["teal"], PALETTE["yellow"]]
    spin = in_out_cubic(progress(t, 1.3, 1.1)) * math.tau * 0.75
    for k, c in enumerate(colors):
        pop = out_back(progress(t, 0.35 + k * 0.15, 0.6), s=2.2)
        ang = -math.pi / 2 + k * math.tau / 3 + spin
        orbit = 190 * (1 - exit_p)
        r = 85 * pop * (1 - 0.6 * exit_p)
        f.circle(CX + math.cos(ang) * orbit, CY + math.sin(ang) * orbit, r, c)

    # Transition: coral grows from the centre until it covers the frame.
    flood = in_out_cubic(progress(t, 2.45, 0.55))
    if flood > 0:
        f.circle(CX, CY, flood * math.hypot(CX, CY) * 1.02, PALETTE["coral"])
    return f.finish()
