#!/usr/bin/env python3
"""Render the scenes to out/motiongraphics.mp4.

  python render.py                  # full render
  python render.py --scene 2        # re-render one scene, then re-join
  python render.py --still 2 1.2    # save one frame (scene 2 at 1.2 s) as a PNG
"""
import argparse
import os
import subprocess
import sys

from motion import W, H, FPS
from scenes import SCENES

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
ENC = ["-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p"]


def render_scene(i):
    mod = SCENES[i]
    final = os.path.join(OUT, f"scene{i + 1}.mp4")
    tmp = os.path.join(OUT, f"scene{i + 1}.tmp.mp4")
    n = round(mod.DURATION * FPS)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", *ENC, tmp]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k in range(n):
        proc.stdin.write(mod.draw(k / FPS).tobytes())
        print(f"\rscene {i + 1}: frame {k + 1}/{n}", end="", flush=True)
    proc.stdin.close()
    if proc.wait() != 0:
        sys.exit(f"\nffmpeg failed on scene {i + 1}")
    os.replace(tmp, final)
    print()


def join():
    listfile = os.path.join(OUT, "scenes.txt")
    with open(listfile, "w") as fh:
        for i in range(len(SCENES)):
            fh.write(f"file 'scene{i + 1}.mp4'\n")
    out = os.path.join(OUT, "motiongraphics.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", listfile, "-c", "copy", out], check=True)
    print("wrote", out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", type=int, help="render only this scene (1-based)")
    ap.add_argument("--still", nargs=2, metavar=("SCENE", "SECONDS"))
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    if a.still:
        s, sec = int(a.still[0]), float(a.still[1])
        path = os.path.join(OUT, f"still_s{s}_{sec:.2f}.png")
        SCENES[s - 1].draw(sec).save(path)
        print("wrote", path)
        return

    for i in ([a.scene - 1] if a.scene else range(len(SCENES))):
        render_scene(i)
    join()


if __name__ == "__main__":
    main()
