#!/usr/bin/env python3
"""Render the showreel.

  python -m showreel.render              # all scenes (2 in parallel) + join (+ audio if out/audio.wav exists)
  python -m showreel.render --scene 4    # one scene, then re-join
  python -m showreel.render --still 4 2.5
  python -m showreel.render --sheet      # contact sheet of key frames -> out/sheet.png
"""
import argparse
import os
import subprocess
import sys
from multiprocessing import Pool

import cv2
import numpy as np

from .fx import FPS, H, W, post
from . import s1_particles, s2_kinetic, s3_liquid, s4_knot, s5_tunnel, s6_outro

SCENES = [s1_particles, s2_kinetic, s3_liquid, s4_knot, s5_tunnel, s6_outro]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out")
ENC = ["-c:v", "libx264", "-crf", "17", "-preset", "veryfast", "-pix_fmt", "yuv420p"]


def frame(i, t):
    mod = SCENES[i]
    kick = float(np.exp(-t * 14)) if i > 0 else 0.0  # impact on every cut
    return post(mod.draw(t), t, kick, **mod.POST)


def render_scene(i):
    mod = SCENES[i]
    n = round(mod.DUR * FPS)
    final = os.path.join(OUT, f"scene{i + 1}.mp4")
    tmp = os.path.join(OUT, f"scene{i + 1}.tmp.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", *ENC, tmp]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k in range(n):
        proc.stdin.write(frame(i, k / FPS).tobytes())
        if k % 60 == 59:
            print(f"scene {i + 1}: {k + 1}/{n}", flush=True)
    proc.stdin.close()
    if proc.wait() != 0:
        sys.exit(f"ffmpeg failed on scene {i + 1}")
    os.replace(tmp, final)
    return i


def join():
    lst = os.path.join(OUT, "scenes.txt")
    with open(lst, "w") as fh:
        for i in range(len(SCENES)):
            fh.write(f"file 'scene{i + 1}.mp4'\n")
    silent = os.path.join(OUT, "showreel_silent.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent], check=True)
    audio = os.path.join(OUT, "audio.wav")
    final = os.path.join(OUT, "showreel.mp4")
    if os.path.exists(audio):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", audio, "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", final], check=True)
    else:
        os.replace(silent, final)
    print("wrote", final)


def save(path, rgb):
    cv2.imwrite(path, cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", type=int)
    ap.add_argument("--still", nargs=2, metavar=("SCENE", "SECONDS"))
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--join", action="store_true", help="only re-join existing scene files (and audio)")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    if a.still:
        i, t = int(a.still[0]) - 1, float(a.still[1])
        p = os.path.join(OUT, f"still_{i + 1}_{t:.2f}.png")
        save(p, frame(i, t))
        print("wrote", p)
        return
    if a.sheet:
        picks = [(1, 1.2), (1, 3.4), (2, 1.2), (2, 4.4), (3, 2.0), (3, 4.2),
                 (4, 0.6), (4, 3.0), (5, 1.4), (5, 3.3), (6, 1.4), (6, 2.6)]
        tiles = [cv2.resize(frame(s - 1, t), (640, 360), interpolation=cv2.INTER_AREA) for s, t in picks]
        rows = [np.hstack(tiles[r * 3:r * 3 + 3]) for r in range(4)]
        save(os.path.join(OUT, "sheet.png"), np.vstack(rows))
        print("wrote out/sheet.png")
        return

    if not a.join:
        todo = [a.scene - 1] if a.scene else [3, 2, 0, 1, 4, 5]  # heaviest scenes first
        if len(todo) == 1:
            render_scene(todo[0])
        else:
            with Pool(2) as pool:
                for done in pool.imap_unordered(render_scene, todo):
                    print(f"scene {done + 1} done", flush=True)
    join()


if __name__ == "__main__":
    main()
