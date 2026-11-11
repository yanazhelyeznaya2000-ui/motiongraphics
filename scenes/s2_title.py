"""Scene 2: the coral flood squeezes into a bar, and the title rises letter by letter."""
from motion import Frame, W, H, PALETTE, mix
from motion.easing import progress, out_expo, in_out_cubic, out_cubic, lerp
from scenes import layout as L

DURATION = 3.5
STAGGER = 0.035


def draw(t):
    f = Frame()

    # Coral fills the frame, then squeezes vertically into a thin bar, then narrows.
    squeeze = in_out_cubic(progress(t, 0.0, 0.7))
    narrow = out_expo(progress(t, 0.6, 0.8))
    y0 = lerp(0, L.BAR_Y, squeeze)
    y1 = lerp(H, L.BAR_Y + L.BAR_H, squeeze)
    x0 = lerp(0, L.X0, narrow)
    x1 = lerp(W, L.X1, narrow)
    f.rect(x0, y0, x1, y1, PALETTE["coral"])

    # Title letters rise in with a stagger.
    n = 0
    for line, base in zip(L.LINES, L.BASELINES):
        for ch, x in L.letters(line):
            p = out_expo(progress(t, 0.55 + n * STAGGER, 0.7))
            f.text_reveal(x, base, ch, L.TITLE_SIZE, PALETTE["cream"], p)
            n += 1

    # Caption fades in under the bar.
    cap = out_cubic(progress(t, 1.7, 0.6))
    if cap > 0:
        f.text(L.X0, L.CAPTION_Y + 14 * (1 - cap), L.CAPTION, L.CAPTION_SIZE,
               mix(PALETTE["bg"], PALETTE["teal"], cap))
    return f.finish()
