#!/usr/bin/env python3
"""Synthesize the 32-second, 120 BPM soundtrack from scratch (numpy + scipy). -> out/audio.wav

Structure follows the picture:  0-6 build · 6-12 kinetic beat · 12-18 melodic · 18-24 full ·
24-28 driving + snare roll · 28-32 outro. Every scene cut gets an impact.
"""
import os

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt

SR = 44100
BEAT = 0.5
DUR = 32.0
N = int(SR * DUR)
rng = np.random.default_rng(5)


def tt(d):
    return np.arange(int(SR * d)) / SR


def lp(x, f, o=2):
    return sosfilt(butter(o, f, "low", fs=SR, output="sos"), x)


def hp(x, f, o=2):
    return sosfilt(butter(o, f, "high", fs=SR, output="sos"), x)


def bp(x, lo, hi):
    return sosfilt(butter(2, [lo, hi], "band", fs=SR, output="sos"), x)


def stem():
    return np.zeros((2, N), np.float64)


def put(buf, t0, sig, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N or i < 0:
        return
    j = min(i + len(sig), N)
    seg = sig[:j - i] * gain
    buf[0, i:j] += seg * (1 - max(pan, 0))
    buf[1, i:j] += seg * (1 + min(pan, 0))


# --- instruments -----------------------------------------------------------------------------
def kick():
    t = tt(0.45)
    ph = 2 * np.pi * np.cumsum(48 + 150 * np.exp(-t * 30)) / SR
    return (np.sin(ph) * np.exp(-t * 7.5) + 0.35 * np.exp(-t * 300) * rng.standard_normal(len(t))) * 0.95


def clap():
    t = tt(0.28)
    n = bp(rng.standard_normal(len(t)), 900, 3800)
    env = np.exp(-t * 20)
    for off in (0.0, 0.011, 0.022):
        k = np.clip(t - off, 0, None)
        env += (t >= off) * np.exp(-k * 160) * 0.8
    return n * env * 0.5


def snare():
    t = tt(0.25)
    n = bp(rng.standard_normal(len(t)), 1500, 8000) * np.exp(-t * 22)
    return (n * 0.6 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 28) * 0.5) * 0.8


def hat(open_=False):
    t = tt(0.35 if open_ else 0.12)
    return hp(rng.standard_normal(len(t)), 7000) * np.exp(-t * (12 if open_ else 70)) * 0.25


def bass(f, d):
    t = tt(d)
    saw = 2 * ((f * t) % 1) - 1
    s = lp(saw, 380) * 0.65 + np.sin(2 * np.pi * f * t) * 0.75
    return s * np.minimum(1, t / 0.005) * np.clip(np.minimum(1, (d - t) / 0.03), 0, 1)


def pad(freqs, d):
    t = tt(d)
    s = np.zeros_like(t)
    for f in freqs:
        for det in (0.994, 1.0, 1.006):
            s += 2 * ((f * det * t) % 1) - 1
    env = np.minimum(1, t / 0.5) * np.clip(np.minimum(1, (d - t) / 0.6), 0, 1)
    return s * env / (len(freqs) * 3)


def pluck(f, d=0.5):
    t = tt(d)
    s = 0.6 * (2 * ((f * t) % 1) - 1) + 0.4 * np.sin(2 * np.pi * 2 * f * t)
    return s * np.exp(-t * 9) * np.minimum(1, t / 0.002)


def stab(f):
    t = tt(0.3)
    s = (2 * ((f * t) % 1) - 1) * 0.6 + np.sin(2 * np.pi * f * t) * 0.6
    return lp(s, 3500) * np.exp(-t * 16)


def riser(d):
    t = tt(d)
    n = hp(rng.standard_normal(len(t)), 1500) * (t / d) ** 2.2 * 0.35
    ph = 2 * np.pi * np.cumsum(200 * 10 ** (t / d)) / SR
    return n + np.sin(ph) * (t / d) ** 2 * 0.18


def impact():
    t = tt(2.6)
    ph = 2 * np.pi * np.cumsum(30 + 90 * np.exp(-t * 6)) / SR
    boom = np.sin(ph) * np.exp(-t * 2.0)
    air = lp(rng.standard_normal(len(t)), 3000) * np.exp(-t * 3) * 0.5
    return boom + air


def bell(f):
    t = tt(2.5)
    return sum(np.sin(2 * np.pi * f * r * t) * a * np.exp(-t * d)
               for r, a, d in ((1, 1, 1.6), (2.76, 0.4, 2.4), (5.4, 0.2, 3.5))) * 0.5


# --- arrangement --------------------------------------------------------------------------------
CHORDS = [[220.0, 261.63, 329.63], [174.61, 220.0, 261.63], [261.63, 329.63, 392.0], [196.0, 246.94, 293.66]]
ROOTS = [55.0, 43.65, 65.41, 49.0]
ARP_PAT = [0, 1, 2, 3, 4, 5, 4, 3, 2, 1, 0, 1, 2, 3, 4, 3]

drums, bassb, padb, arpb, fxb = stem(), stem(), stem(), stem(), stem()
kicks = []


def bar_t(b):
    return b * 2.0


KICK, CLAP, SNARE = kick(), clap(), snare()
HAT_C, HAT_O = hat(), hat(True)

# riser + impact on every cut
for cut in (6, 12, 18, 24, 28):
    put(fxb, cut, impact(), 0.9)
for start, length in ((2.5, 3.5), (8.5, 3.5), (14.5, 3.5), (20.5, 3.5)):
    put(fxb, start + 0.0, riser(length)[:int(length * SR)], 0.8)
put(fxb, 24.0 - 0.0, np.zeros(1))

for b in range(16):
    t0 = bar_t(b)
    ch, root = CHORDS[b % 4], ROOTS[b % 4]
    sec = 0 if b < 3 else 1 if b < 6 else 2 if b < 9 else 3 if b < 12 else 4 if b < 14 else 5

    # pad everywhere, swelling in section 0
    pg = {0: 0.35 + 0.15 * b, 1: 0.5, 2: 0.9, 3: 0.7, 4: 0.5, 5: 0.9}[sec]
    put(padb, t0, pad([f * m for f in ch for m in (1, 2)], 2.0), pg)

    for beat in range(4):
        tb = t0 + beat * BEAT * 1.0
        # --- kicks
        k_on = (sec == 0 and b >= 1) or sec in (1, 2, 3, 4) or (sec == 5 and b == 14 and beat == 0)
        if k_on:
            put(drums, tb, KICK, 0.9 if sec == 2 else 1.0)
            kicks.append(tb)
        # --- claps on 2 and 4
        if sec in (1, 2, 3, 4) and beat in (1, 3):
            put(drums, tb, CLAP, 0.5 if sec == 2 else 0.8, pan=0.1)
        # --- hats
        if sec >= 1 or b == 2:
            put(drums, tb + 0.25, HAT_O if sec in (3, 4) else HAT_C, 0.6, pan=0.25)
            put(drums, tb, HAT_C, 0.35, pan=-0.2)
            if sec in (2, 3, 4):
                put(drums, tb + 0.125, HAT_C, 0.3, pan=0.3)
                put(drums, tb + 0.375, HAT_C, 0.3, pan=-0.3)
        # --- bass
        if sec in (1, 3, 4):
            for h in (0, 1):
                f = root * (2 if (h == 1 and sec != 1) else 1)
                put(bassb, tb + h * 0.25, bass(f, 0.22), 0.9)
            if sec == 4:
                for h in (2, 3):
                    put(bassb, tb + h * 0.125 + 0.0, bass(root * (2 if h == 3 else 1), 0.11), 0.7)
        elif sec == 2:
            if beat in (0, 2):
                put(bassb, tb, bass(root, 0.95), 0.9)
        elif sec == 5 and b == 14 and beat == 0:
            put(bassb, tb, bass(root, 1.9), 0.9)
        # --- arp (16ths)
        if sec in (2, 3, 4) or (sec == 1 and b == 5) or (sec == 5):
            for s16 in range(4):
                idx = ARP_PAT[(beat * 4 + s16) % 16]
                tones = ch + [f * 2 for f in ch]
                f = tones[idx % 6] * 2
                if sec == 5 and s16 % 2:
                    continue
                put(arpb, tb + s16 * 0.125, pluck(f), 0.5 if sec != 5 else 0.35, pan=(-0.4 if s16 % 2 else 0.4))

# word slam stabs in the kinetic opening (6.0 .. 8.0)
for i, f in enumerate((440.0, 493.88, 523.25, 587.33, 659.25)):
    put(arpb, 6.0 + i * BEAT, stab(f), 0.9)

# snare roll into the tunnel's last bar + into the outro impact
t = 26.0
step = 0.25
while t < 28.0:
    put(drums, t, SNARE, 0.35 + 0.65 * (t - 26.0) / 2.0)
    step = max(0.03, step * 0.9)
    t += step
# 4-on-the-floor drive in tunnel with off-beat bass pump
for b in (12, 13):
    for beat in range(4):
        put(bassb, bar_t(b) + beat * BEAT + 0.25, bass(ROOTS[b % 4] * 2, 0.2), 0.6)

# outro bells
for i, f in enumerate((880.0, 659.25, 523.25, 440.0)):
    put(arpb, 28.6 + i * 0.5, bell(f), 0.5, pan=0.3 if i % 2 else -0.3)
put(fxb, 28.0, bell(220.0), 0.7)

# --- mix ---------------------------------------------------------------------------------------
tgrid = np.arange(N) / SR
duck = np.ones(N)
for k in kicks:
    i = int(k * SR)
    j = min(i + int(0.4 * SR), N)
    seg = np.arange(j - i) / SR
    duck[i:j] *= 1 - 0.65 * np.exp(-seg / 0.11)

padf = lp(padb, 2200) * duck
bassf = lp(bassb, 500) * duck
arpf = hp(arpb, 200) * (0.6 + 0.4 * duck)


def reverb(x, wet=0.14):
    t = tt(1.6)
    ir = np.stack([rng.standard_normal(len(t)), rng.standard_normal(len(t))]) * np.exp(-t * 3.2)
    ir = lp(ir, 6000)
    return np.stack([fftconvolve(x[c], ir[c])[:N] for c in range(2)]) * wet * 0.05


rev = reverb(padf + arpf + fxb * 0.4)

# ping-pong delay (dotted 8th) on the arp
dly = np.zeros_like(arpf)
d = int(0.375 * SR)
for rep in range(1, 4):
    g = 0.45 ** rep
    o = d * rep
    if o < N:
        dly[0, o:] += arpf[1, :N - o] * g
        dly[1, o:] += arpf[0, :N - o] * g

mix = drums * 1.0 + bassf * 0.95 + padf * 0.55 + arpf * 0.55 + dly * 0.5 + fxb * 0.55 + rev
mix = hp(mix, 25)
mix = np.tanh(mix * 1.15)
mix *= 0.92 / np.max(np.abs(mix))
fade = np.clip((DUR - tgrid) / 1.5, 0, 1) ** 1.5
fade *= np.clip(tgrid / 0.05, 0, 1)
mix *= fade

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out")
os.makedirs(out, exist_ok=True)
wavfile.write(os.path.join(out, "audio.wav"), SR, (mix.T * 32767).astype(np.int16))
print("wrote out/audio.wav", mix.shape, f"peak={np.max(np.abs(mix)):.2f}")
