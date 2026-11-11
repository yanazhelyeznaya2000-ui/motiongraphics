# motiongraphics

Motion graphics written as code. Each scene is a Python function that draws one frame for a given time `t`; `render.py` turns the scenes into a 1080p, 30 fps MP4.

No After Effects, no browser — just Python, Pillow and ffmpeg.

## Setup

```bash
pip install -r requirements.txt
# and ffmpeg: brew install ffmpeg  /  sudo apt install ffmpeg  /  winget install ffmpeg
```

## Render

```bash
python render.py                 # full video  -> out/motiongraphics.mp4
python render.py --scene 2       # re-render one scene and re-join (fast)
python render.py --still 2 1.2   # one frame of scene 2 at 1.2 s -> out/*.png
```

## How it's put together

```
motion/
  easing.py   easing curves (out_expo, out_back, in_out_cubic...) and progress(t, start, dur)
  frame.py    Frame: a 2x supersampled canvas with circle, ring, rect, text, text_reveal
scenes/
  s1_shapes.py  dot grid ripple, orbiting circles, coral flood transition
  s2_title.py   flood squeezes into a bar, title rises letter by letter
  s3_outro.py   title exits, bar collapses to a dot, rings ripple, sign-off
  layout.py     shared title positions
  __init__.py   SCENES = the order scenes play in
render.py
fonts/          Inter (SIL Open Font License 1.1)
```

## Make your own scene

1. Copy `scenes/s2_title.py` to `scenes/s4_whatever.py`.
2. Set `DURATION` (seconds) and edit `draw(t)`. The pattern for anything that moves:

   ```python
   p = out_expo(progress(t, start=0.5, duration=0.8))   # 0 -> 1 over that window
   f.circle(lerp(200, 1700, p), 540, 60, PALETTE["teal"])
   ```

3. Add it to `SCENES` in `scenes/__init__.py` and run `python render.py --scene 4`.

Colours live in `PALETTE` in `motion/frame.py`; swap them to restyle everything.
