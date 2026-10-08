"""Procedural watercolour of an aerial coastline: sea.jpg (tall) + sand.png (shoreline band with alpha)."""
import numpy as np
from PIL import Image, ImageFilter
import sys, os, math
out = sys.argv[1]
rng = np.random.default_rng(5)

def value_noise(h, w, cell, aniso=1.0, rot=0.0):
    if rot:
        s = abs(math.sin(math.radians(rot))); c = abs(math.cos(math.radians(rot)))
        bw = int(w * c + h * s) + 4; bh = int(h * c + w * s) + 4
    else:
        bw, bh = w, h
    gh = max(2, int(bh / cell)) + 2; gw = max(2, int(bw / (cell * aniso))) + 2
    g = (rng.random((gh, gw)) * 255).astype(np.uint8)
    im = Image.fromarray(g).resize((bw, bh), Image.BICUBIC)
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC)
        im = im.crop(((bw - w) // 2, (bh - h) // 2, (bw - w) // 2 + w, (bh - h) // 2 + h))
    return (np.asarray(im).astype(np.float32) / 255.0) * 2 - 1

def fbm(h, w, cell, octaves=4, aniso=1.0, rot=0.0, gain=0.5):
    acc = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for i in range(octaves):
        acc += amp * value_noise(h, w, cell / (2 ** i), aniso, rot); tot += amp; amp *= gain
    return acc / tot

def hexc(s): return np.array([int(s[i:i+2], 16) for i in (1, 3, 5)], np.float32) / 255
def ramp(t, stops):
    pos = np.array([p for p, _ in stops]); cols = np.stack([hexc(c) for _, c in stops])
    o = np.zeros(t.shape + (3,), np.float32)
    for k in range(3): o[..., k] = np.interp(t, pos, cols[:, k])
    return o
def smoothstep(e0, e1, x): x = np.clip((x - e0) / (e1 - e0), 0, 1); return x * x * (3 - 2 * x)
def edges(f):
    gy = np.abs(np.diff(f, axis=0, prepend=f[:1])); gx = np.abs(np.diff(f, axis=1, prepend=f[:, :1]))
    return gx + gy
def washes(h, w, cell, levels, aniso, rot, octaves=4):
    """Watercolour wash: a noise field quantised into a few flat patches with softened edges,
    plus the pigment line that gathers where washes meet."""
    f = fbm(h, w, cell, octaves, aniso, rot) * 0.5 + 0.5
    q = np.floor(f * levels) / levels
    q = np.asarray(Image.fromarray((q * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(cell * 0.03))).astype(np.float32) / 255
    e = edges(q); e = e / (e.max() + 1e-6)
    e = np.asarray(Image.fromarray((np.clip(e * 6, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3.0))).astype(np.float32) / 255
    return (q - 0.5) * 2, e

# ------------------------------------------------------------------ SEA
W, H = 1600, 5200
y = np.linspace(0, 1, H, dtype=np.float32)[:, None].repeat(W, 1)
warp = fbm(H, W, 900, 3, aniso=2.2) * 0.06 + fbm(H, W, 320, 3, aniso=3.0) * 0.025
t = np.clip(y + warp, 0, 1)
# stays mid-light for most of its height; the page darkens it with a navy overlay
sea = ramp(t, [
    (0.00, '#2f93b4'), (0.06, '#2a86a8'), (0.14, '#25769c'), (0.24, '#216690'),
    (0.36, '#1d5784'), (0.50, '#194977'), (0.64, '#153b67'), (0.78, '#112e57'),
    (0.90, '#0e2449'), (1.00, '#0b1a3a')])
# three scales of washes
w1, e1 = washes(H, W, 640, 5, 2.4, -6)
w2, e2 = washes(H, W, 300, 6, 3.0, 8)
w3, e3 = washes(H, W, 130, 7, 3.6, -3)
sea *= (1 + 0.11 * w1 + 0.08 * w2 + 0.05 * w3)[..., None]
sea *= (1 - 0.06 * e1 - 0.05 * e2 - 0.03 * e3)[..., None]
# hue drift: teal vs indigo, plus a faint violet in the deep
hue = fbm(H, W, 520, 3, aniso=1.6, rot=14)
sea += (0.09 * hue * (0.4 + 0.6 * (1 - t)))[..., None] * (hexc('#4fd0c8') - hexc('#2b3f96'))
viol = np.clip(fbm(H, W, 420, 3, aniso=2.0, rot=-12), 0, 1) * np.clip((t - 0.55) * 2.5, 0, 1)
sea = sea * (1 - 0.18 * viol[..., None]) + hexc('#3b2d6e') * (0.18 * viol)[..., None]
# shoals (pale) in the shallows, reefs (dark) deeper
sh = fbm(H, W, 240, 4, aniso=3.4, rot=-4)
shoal = smoothstep(0.18, 0.42, sh) * np.clip(1 - t * 3.6, 0, 1)
sea = sea * (1 - 0.5 * shoal[..., None]) + hexc('#5fc0cf') * (0.5 * shoal)[..., None]
rf = fbm(H, W, 170, 4, aniso=2.4, rot=9)
reef = smoothstep(0.22, 0.5, rf) * np.clip((t - 0.4) * 2.5, 0, 1)
sea *= (1 - 0.20 * reef)[..., None]
# brush strokes: long directional streaks, two angles, plus dry-brush speckle
sea *= (1 + 0.09 * fbm(H, W, 80, 3, aniso=9.0, rot=-8) + 0.06 * fbm(H, W, 34, 2, aniso=12.0, rot=5))[..., None]
spk = fbm(H, W, 14, 2, aniso=4.0, rot=-8)
sea *= (1 - 0.07 * smoothstep(0.62, 0.85, spk) * (0.5 + 0.5 * t))[..., None]
# paper grain
sea += rng.normal(0, 0.016, (H, W, 1)).astype(np.float32)
sea = np.clip(sea, 0, 1)
im = Image.fromarray((sea * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))
im = Image.fromarray(np.clip(np.asarray(im).astype(np.float32) + rng.normal(0, 2.5, (H, W, 1)), 0, 255).astype(np.uint8))
im.save(os.path.join(out, 'sea.jpg'), quality=80, optimize=True, progressive=True)
print('sea', im.size, os.path.getsize(os.path.join(out, 'sea.jpg')) // 1024, 'KB')

# ------------------------------------------------------------------ SAND
W2, H2 = 1800, 640
e_a = fbm(8, W2, 420, 3)[4]; e_b = fbm(8, W2, 110, 3)[4]
edge = 518 + 36 * e_a + 9 * e_b
yy = np.arange(H2, dtype=np.float32)[:, None].repeat(W2, 1)
d = yy - edge[None, :]
base = fbm(H2, W2, 320, 4, aniso=2.5, rot=-3) * 0.5 + 0.5
sand = ramp(np.clip(base, 0, 1), [(0.0, '#d9c196'), (0.35, '#e9d9b3'), (0.65, '#f2e6c9'), (1.0, '#f8efd9')])
ws, es = washes(H2, W2, 260, 5, 3.0, -2, 3)
sand *= (1 + 0.07 * ws - 0.06 * es)[..., None]
sand *= (1 + 0.07 * fbm(H2, W2, 48, 3, aniso=9.0, rot=-2) + 0.045 * fbm(H2, W2, 14, 2, aniso=3.0))[..., None]
rip = np.sin((yy + 26 * fbm(H2, W2, 160, 3, aniso=3.0)) * (2 * np.pi / 23) + 1.8 * fbm(H2, W2, 400, 2)) * smoothstep(-400, -120, d) * smoothstep(-30, -70, d)
sand *= (1 + 0.035 * rip)[..., None]
blot = smoothstep(0.3, 0.6, fbm(H2, W2, 150, 3, aniso=2.0, rot=6))
sand = sand * (1 - 0.12 * blot[..., None]) + hexc('#c9a86f') * (0.12 * blot)[..., None]
wet = smoothstep(-44, -4, d) * smoothstep(3, -1, d) * (0.7 + 0.3 * (fbm(H2, W2, 90, 2, aniso=4) * 0.5 + 0.5))
sand = sand * (1 - 0.34 * wet)[..., None] + hexc('#a98b5c') * (0.34 * wet)[..., None]
sand += rng.normal(0, 0.022, (H2, W2, 1)).astype(np.float32)
alpha = np.clip(-d / 2.0 + 0.5, 0, 1)
# froth: lacy, patchy white past the edge
fn = fbm(H2, W2, 30, 3, aniso=4.0) * 0.5 + 0.5
fw = 16 + 26 * fn
foam = np.clip(1 - d / fw, 0, 1) * np.clip(d / 1.5, 0, 1) * smoothstep(0.1, 0.5, fn + 0.3)
lace = smoothstep(0.46, 0.66, fbm(H2, W2, 26, 3, aniso=6.0)) * smoothstep(0, 8, d) * smoothstep(70 + 16 * e_b[None, :], 26, d)
foam = np.clip(foam + 0.8 * lace, 0, 1)
rgb = sand * alpha[..., None] + np.ones(3, np.float32) * (1 - alpha)[..., None]
a = np.clip(alpha + (1 - alpha) * foam * 0.95, 0, 1)
im2 = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), a]) * 255).astype(np.uint8), 'RGBA')
im2.save(os.path.join(out, 'sand.png'), optimize=True)
print('sand', im2.size, os.path.getsize(os.path.join(out, 'sand.png')) // 1024, 'KB', 'edge', edge.min(), edge.max())
