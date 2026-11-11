"""Scene 4 (18-24 s): a lit, rotating torus knot made of 200,000 points. Sphere morphs into knot."""
import cv2
import numpy as np

from .fx import *

DUR, T0 = 6.0, 18.0
POST = dict(bloom=1.1, grain=0.03, chroma=1.8)

M, K = 4800, 42
TH = np.linspace(0, 2 * np.pi, M, endpoint=False).astype(np.float32)
_r = np.cos(3 * TH) + 2
P = np.stack([_r * np.cos(2 * TH), _r * np.sin(2 * TH), -np.sin(3 * TH)], 1).astype(np.float32)
_T = np.roll(P, -1, 0) - np.roll(P, 1, 0)
_T /= np.linalg.norm(_T, axis=1, keepdims=True)
_N1 = np.cross(_T, np.array([0, 0, 1.0], np.float32))
_N1 /= np.linalg.norm(_N1, axis=1, keepdims=True)
_B1 = np.cross(_T, _N1)
PHI = np.linspace(0, 2 * np.pi, K, endpoint=False).astype(np.float32)
NRM = (np.cos(PHI)[None, :, None] * _N1[:, None, :] + np.sin(PHI)[None, :, None] * _B1[:, None, :]).astype(np.float32)

_lat = (np.arange(M) / M * np.pi - np.pi / 2)[:, None].astype(np.float32)
_lon = PHI[None, :] + np.arange(M)[:, None] * 0.03
SPH_N = np.stack([np.cos(_lat) * np.cos(_lon), np.sin(_lat) * np.ones_like(_lon), np.cos(_lat) * np.sin(_lon)], -1).astype(np.float32)
SPH_P = SPH_N * 3.1
BASECOL = None

rng = np.random.default_rng(4)
STARS = rng.uniform(-14, 14, (2600, 3)).astype(np.float32)
RING_A = rng.uniform(0, 2 * np.pi, 6000).astype(np.float32)
RING_R = (6.2 + rng.normal(0, 0.12, 6000)).astype(np.float32)
RING_Y = rng.normal(0, 0.08, 6000).astype(np.float32)

LIGHT = np.array([-0.4, 0.6, -0.7], np.float32)
LIGHT /= np.linalg.norm(LIGHT)
HALF = LIGHT + np.array([0, 0, -1], np.float32)
HALF /= np.linalg.norm(HALF)


def _rot(yaw, pitch):
    cy, sy, cp, sp = np.cos(yaw), np.sin(yaw), np.cos(pitch), np.sin(pitch)
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], np.float32)
    rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]], np.float32)
    return rx @ ry


def _project(pts, dist, F=1500.0):
    zc = pts[:, 2] + dist
    return W / 2 + pts[:, 0] * F / zc, H / 2 - pts[:, 1] * F / zc, zc


def _knot(t):
    rad = 0.40 * (1 + 0.22 * np.sin(12 * TH - 5 * t))
    kp = P[:, None, :] + rad[:, None, None] * NRM
    m = float(ease_out_expo(t / 1.5))
    pts = SPH_P + (kp - SPH_P) * m
    nr = SPH_N + (NRM - SPH_N) * m
    nr /= np.linalg.norm(nr, axis=2, keepdims=True)
    return pts.reshape(-1, 3), nr.reshape(-1, 3)


def draw(t):
    img = np.zeros((H, W, 3), np.float32) + BG
    dist = 9.8 - 0.35 * pulse(t, 8.0) - 0.9 * float(ease_out(t / 1.5))
    base = np.repeat(grad(TH / (2 * np.pi) + 0.12 * t)[:, None, :], K, 1).reshape(-1, 3)

    for dt in (-0.016, 0.0, 0.016):
        tt = t + dt
        R = _rot(0.55 * tt + 0.6, 0.35 + 0.15 * np.sin(0.7 * tt))
        pts, nr = _knot(tt)
        pts = pts @ R.T
        nr = nr @ R.T
        x, y, zc = _project(pts, dist)
        facing = -nr[:, 2]
        vis = (facing > -0.12).astype(np.float32)
        diff = np.clip(nr @ LIGHT, 0, 1)
        spec = np.clip(nr @ HALF, 0, 1) ** 30
        rim = (1 - np.clip(facing, 0, 1)) ** 2
        col = base * (0.10 + 0.95 * diff[:, None]) + spec[:, None] * 0.9 + rim[:, None] * COL["teal"] * 0.35
        fog = np.exp(-(zc - 6.0) * 0.16)
        splat(img, x, y, col, vis * fog * 2.4 / 3.0)

    # orbiting ring of particles
    ang = RING_A + t * 0.9
    ring = np.stack([RING_R * np.cos(ang), RING_Y + 0.9 * np.sin(ang * 2 + t), RING_R * np.sin(ang)], 1)
    R = _rot(0.55 * t + 0.6, 0.35 + 0.15 * np.sin(0.7 * t))
    ring = ring @ R.T
    x, y, zc = _project(ring, dist)
    splat(img, x, y, COL["violet"] * 0.9, np.exp(-(zc - 6.0) * 0.12) * 1.6)

    # starfield drifting toward camera
    st = STARS.copy()
    st[:, 2] = ((st[:, 2] - t * 2.0 + 14) % 28) - 14
    x, y, zc = _project(st, 11.0)
    ok = zc > 1.0
    splat(img, x[ok], y[ok], COL["cream"] * 0.5, np.clip(1.5 - zc[ok] / 20, 0.05, 1) * 1.2)

    img = cv2.GaussianBlur(img, (0, 0), 1.1) * 1.6
    hud(img, t, "03 / 3D  200,000 POINTS", T0)
    draw_text(img, "NO ENGINE  ·  NO MESH  ·  JUST MATH", 80, H - 80, 22, COL["cream"],
              float(ease_out((t - 1.0) / 0.6)) * 0.7, kind="body", track=6, anchor="l")
    return img
