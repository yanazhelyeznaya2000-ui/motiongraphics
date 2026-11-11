"""Scene 3: the title exits upward, the bar collapses to a dot, rings ripple out, sign-off."""
from motion import Frame, W, H, PALETTE, mix
from motion.easing import progress, in_cubic, in_out_cubic, out_cubic, out_expo, lerp
from scenes import layout as L

DURATION = 3.0
CX, CY = W / 2, H / 2
STAGGER = 0.02


def draw(t):
    f = Frame()
    bg = PALETTE["bg"]
    fade = in_out_cubic(progress(t, 2.45, 0.55))  # final fade to background

    def c(name):
        return mix(PALETTE[name], bg, fade)

    # Title letters keep rising and leave through the top of their window.
    n = 0
    for line, base in zip(L.LINES, L.BASELINES):
        for ch, x in L.letters(line):
            p = 1 + in_cubic(progress(t, 0.0 + n * STAGGER, 0.4))
            f.text_reveal(x, base, ch, L.TITLE_SIZE, PALETTE["cream"], p)
            n += 1

    # Caption fades out.
    cap = 1 - out_cubic(progress(t, 0.0, 0.3))
    if cap > 0:
        f.text(L.X0, L.CAPTION_Y, L.CAPTION, L.CAPTION_SIZE, mix(bg, PALETTE["teal"], cap))

    # Bar narrows to the centre and drops to a dot at screen centre.
    shrink = in_out_cubic(progress(t, 0.25, 0.5))
    drop = in_out_cubic(progress(t, 0.6, 0.35))
    half = lerp((L.X1 - L.X0) / 2, L.BAR_H / 2, shrink)
    by = lerp(L.BAR_Y + L.BAR_H / 2, CY, drop)
    if t < 0.95:
        f.rect(CX - half, by - L.BAR_H / 2, CX + half, by + L.BAR_H / 2, PALETTE["coral"])
    else:
        pulse = out_expo(progress(t, 0.95, 0.4))
        f.circle(CX, CY, lerp(L.BAR_H / 2, 22, pulse) * (1 - fade), c("coral"))

    # Rings ripple out from the dot.
    for k, name in enumerate(["coral", "yellow", "teal"]):
        p = out_cubic(progress(t, 0.95 + k * 0.14, 1.3))
        if 0 < p < 1:
            f.ring(CX, CY, 30 + p * 700, 10 * (1 - p) + 1, mix(PALETTE[name], bg, p))

    # Sign-off.
    s = out_expo(progress(t, 1.25, 0.7))
    if s > 0:
        msg = "your turn."
        from motion.frame import text_width
        x = CX - text_width(msg, "display", 72) / 2
        f.text_reveal(x, CY + 160, msg, 72, c("cream"), s)
    return f.finish()
