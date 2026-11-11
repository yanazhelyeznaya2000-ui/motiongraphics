"""Shared title layout so scenes 2 and 3 line up exactly."""
from motion import W
from motion.frame import text_width

TITLE_SIZE = 190
LINES = ["MOTION", "GRAPHICS"]
BASELINES = [455, 640]
BAR_Y, BAR_H = 690, 16
CAPTION = "a starter scene, drawn frame by frame in Python"
CAPTION_SIZE = 34
CAPTION_Y = 760

BLOCK_W = max(text_width(s, "display", TITLE_SIZE) for s in LINES)
X0 = (W - BLOCK_W) / 2
X1 = X0 + BLOCK_W


def letters(line):
    """(char, x) pairs for one title line, left-aligned at X0."""
    out = []
    for i, ch in enumerate(line):
        x = X0 + text_width(line[:i], "display", TITLE_SIZE)
        out.append((ch, x))
    return out
