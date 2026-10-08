"""Textures for the Cursed mutation VFX (MonsterVfxClient). Same conventions as mutation_flipbooks.py:
white / greyscale on alpha so Roblox tints them; sheets are 1024x1024 = 4x4 grid of 256px frames.
    <blender python> cursed_flipbooks.py [out_dir]
Writes:
  fb_skull     ghostly skull: bone dimmer, eye sockets blazing and flickering, a wispy tail (Loop)
  fb_flame     a licking flame tongue, noise scrolling up, seamless (Loop) - tinted black AND crimson
  tx_csigil    cursed circle for the ground: thorny rings, a pentagram, runes (single texture)
  tx_drop      a blood droplet (single)
"""
import sys, os, math, zlib, struct
import numpy as np

F = 256
G = 4
NF = G * G


def save_png(path, rgba):
    h, w = rgba.shape[:2]
    data = (np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8)
    raw = b''.join(b'\x00' + data[y].tobytes() for y in range(h))

    def chunk(tag, payload):
        c = struct.pack('>I', len(payload)) + tag + payload
        return c + struct.pack('>I', zlib.crc32(tag + payload) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)


def grid(n):
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float64)
    u = (xx + 0.5) / n * 2 - 1
    v = 1 - (yy + 0.5) / n * 2
    return u, v


u, v = grid(F)


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def edge_fade(a, uu=None, vv=None):
    uu = u if uu is None else uu
    vv = v if vv is None else vv
    return a * (1 - smooth(0.9, 0.99, np.maximum(np.abs(uu), np.abs(vv))))


def frame(gray, alpha):
    out = np.zeros((F, F, 4))
    out[..., 0] = out[..., 1] = out[..., 2] = np.clip(gray, 0, 1)
    out[..., 3] = np.clip(edge_fade(alpha), 0, 1)
    return out


def sheet(frames):
    out = np.zeros((F * G, F * G, 4))
    for i, fr in enumerate(frames):
        gy, gx = divmod(i, G)
        out[gy * F:(gy + 1) * F, gx * F:(gx + 1) * F] = fr
    return out


def make_noise(seed, res):
    g = np.random.default_rng(seed).random((res + 1, res + 1))
    g[-1, :] = g[0, :]
    g[:, -1] = g[:, 0]

    def sample(x, y):
        x = np.mod(x, res)
        y = np.mod(y, res)
        x0 = np.floor(x).astype(int)
        y0 = np.floor(y).astype(int)
        fx = x - x0
        fy = y - y0
        fx = fx * fx * (3 - 2 * fx)
        fy = fy * fy * (3 - 2 * fy)
        a = g[y0, x0] * (1 - fx) + g[y0, x0 + 1] * fx
        b = g[y0 + 1, x0] * (1 - fx) + g[y0 + 1, x0 + 1] * fx
        return a * (1 - fy) + b * fy
    return sample


def fbm(sample, x, y, octaves=4):
    tot, amp, norm = 0, 1.0, 0
    for o in range(octaves):
        tot = tot + sample(x * 2 ** o, y * 2 ** o) * amp
        norm += amp
        amp *= 0.5
    return tot / norm


N1 = make_noise(31, 64)
N2 = make_noise(47, 64)


def ellipse(cx, cy, rx, ry, soft=0.02, uu=None, vv=None):
    uu = u if uu is None else uu
    vv = v if vv is None else vv
    d = np.sqrt(((uu - cx) / rx) ** 2 + ((vv - cy) / ry) ** 2)
    return smooth(1 + soft / min(rx, ry), 1 - soft / min(rx, ry), d)


def seg_dist(px, py, ax, ay, bx, by):
    abx, aby = bx - ax, by - ay
    t = np.clip(((px - ax) * abx + (py - ay) * aby) / (abx * abx + aby * aby + 1e-9), 0, 1)
    dx, dy = px - (ax + abx * t), py - (ay + aby * t)
    return np.sqrt(dx * dx + dy * dy)


out_dir = sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].endswith('.py') else 'export/vfx_cursed'
os.makedirs(out_dir, exist_ok=True)

# ---------------------------------------------------------------- skull
frames = []
for i in range(NF):
    t = i / NF * 2 * math.pi
    bob = 0.03 * math.sin(t)
    sx, sy = u, v - bob
    # wispy tail under the jaw, waving
    wave = 0.12 * np.sin(sy * 5 + t * 2) * smooth(-0.1, -0.9, sy)
    tail_w = 0.30 * smooth(-0.95, -0.2, sy)
    tail = smooth(tail_w + 0.04, tail_w - 0.02, np.abs(sx - wave)) * smooth(-0.98, -0.6, sy) * smooth(-0.05, -0.3, sy)
    tail *= 0.55 + 0.45 * fbm(N1, sx * 6 + 3, sy * 6 - t * 1.2, 3)
    cran = ellipse(0, 0.18, 0.56, 0.52, uu=sx, vv=sy)
    cheek = ellipse(0, -0.12, 0.44, 0.34, uu=sx, vv=sy)
    jaw = ellipse(0, -0.34, 0.30, 0.18, uu=sx, vv=sy)
    bone = np.maximum(np.maximum(cran, cheek), jaw)
    # cracks across the cranium
    crack = smooth(0.018, 0.006, seg_dist(sx, sy, -0.18, 0.62, -0.06, 0.38)) + smooth(0.014, 0.004, seg_dist(sx, sy, -0.06, 0.38, -0.14, 0.24))
    # eye sockets (they blaze) and the nose
    flick = 0.8 + 0.2 * math.sin(t * 3) + 0.1 * math.sin(t * 7)
    eyeL = ellipse(-0.21, 0.04, 0.15, 0.13, uu=sx, vv=sy)
    eyeR = ellipse(0.21, 0.04, 0.15, 0.13, uu=sx, vv=sy)
    eyes = np.maximum(eyeL, eyeR)
    glow = (np.exp(-(((sx + 0.21) ** 2 + (sy - 0.04) ** 2) / 0.03)) + np.exp(-(((sx - 0.21) ** 2 + (sy - 0.04) ** 2) / 0.03))) * flick
    nose = smooth(0.03, 0.0, np.maximum(np.abs(sx) * 1.6 + (sy + 0.15) * 0.9 - 0.08, -(sy + 0.2)))
    # teeth: a dark line with gaps
    teeth = smooth(0.02, 0.005, np.abs(sy + 0.30)) * (np.abs(sx) < 0.24)
    teeth += smooth(0.012, 0.003, np.abs(np.mod(sx + 0.04, 0.08) - 0.04)) * ((sy < -0.27) & (sy > -0.42) & (np.abs(sx) < 0.24))
    gray = 0.55 * bone + 0.25 * tail
    gray = gray * (1 - 0.6 * crack) * (1 - 0.85 * np.clip(teeth, 0, 1)) * (1 - 0.8 * nose)
    gray = np.where(eyes > 0.5, 0.15, gray)            # sockets dark...
    gray = np.maximum(gray, np.clip(glow, 0, 1))        # ...with a blazing glow in them
    alpha = np.clip(np.maximum(bone, tail * 0.8) + glow * 0.8, 0, 1)
    alpha *= 1 - 0.0 * eyes
    frames.append(frame(gray, alpha))
save_png(os.path.join(out_dir, 'fb_skull.png'), sheet(frames))

# ---------------------------------------------------------------- flame tongue
frames = []
for i in range(NF):
    t = i / NF * 2 * math.pi
    # time on a circle so the loop is seamless
    ox, oy = math.cos(t) * 3.0, math.sin(t) * 3.0
    h01 = np.clip((v + 0.9) / 1.8, 0, 1)                # 0 at the base .. 1 at the tip
    # the flame sways more the higher it goes
    sway = (fbm(N2, u * 1.5 + ox, v * 1.5 - i / NF * 4 + oy, 3) - 0.5) * 0.7 * h01 ** 1.3
    x = u - sway
    width = 0.42 * (1 - h01) ** 0.55 + 0.02
    shape = smooth(width, width * 0.25, np.abs(x))
    # turbulence scrolling up: the top breaks apart into licking tongues
    dens = fbm(N1, x * 3.2 + ox, v * 2.6 - i / NF * 8 + oy, 4)
    a = np.clip(shape * (dens * 1.9 - h01 * 1.15 + 0.45), 0, 1)
    a *= smooth(-0.98, -0.8, v)                         # soft base
    core = smooth(width * 0.7, 0, np.abs(x)) * (1 - h01) ** 0.7
    gray = np.clip(0.5 + 0.5 * core, 0, 1)
    frames.append(frame(gray, a))
save_png(os.path.join(out_dir, 'fb_flame.png'), sheet(frames))

# ---------------------------------------------------------------- cursed ground circle
S = 1024
U, V = grid(S)
R = np.sqrt(U * U + V * V)
A = np.arctan2(V, U)


def ring(r0, w):
    return smooth(w, w * 0.4, np.abs(R - r0))


a = ring(0.92, 0.018) + ring(0.84, 0.012) + ring(0.60, 0.014) + ring(0.54, 0.008)
# thorns pointing out from the outer ring
nth = 28
ph = np.mod(A / (2 * math.pi) * nth, 1.0)
k = np.abs(ph - 0.5) / 0.1                              # thin spikes: only near each spike's centre line
thorn_len = 0.075 * np.clip(1 - k, 0, 1)
a += smooth(0.004, 0.0, (R - 0.92) - thorn_len) * (R > 0.925) * (k < 1)
# inward thorns on the inner ring
ph2 = np.mod(A / (2 * math.pi) * 18 + 0.5, 1.0)
k2 = np.abs(ph2 - 0.5) / 0.09
a += smooth(0.004, 0.0, (0.535 - R) - 0.05 * np.clip(1 - k2, 0, 1)) * (R < 0.535) * (k2 < 1)
# pentagram inside
pts = [(math.cos(math.pi / 2 + k * 2 * math.pi / 5) * 0.53, math.sin(math.pi / 2 + k * 2 * math.pi / 5) * 0.53) for k in range(5)]
star = np.zeros_like(U)
for k in range(5):
    ax, ay = pts[k]
    bx, by = pts[(k + 2) % 5]
    star = np.maximum(star, smooth(0.012, 0.004, seg_dist(U, V, ax, ay, bx, by)))
a += star
# runes between the rings: little random glyphs made of short strokes
rng = np.random.default_rng(5)
glyphs = np.zeros_like(U)
for k in range(24):
    ca = k / 24 * 2 * math.pi
    cx, cy = math.cos(ca) * 0.72, math.sin(ca) * 0.72
    for _ in range(3):
        p = rng.uniform(-0.035, 0.035, 4)
        glyphs = np.maximum(glyphs, smooth(0.009, 0.003, seg_dist(U, V, cx + p[0], cy + p[1], cx + p[2], cy + p[3])))
a += glyphs
# a faint smoky fill between the rings
smoke = fbm(N1, U * 8, V * 8, 4)
a += 0.18 * smooth(0.55, 0.65, R) * smooth(0.9, 0.8, R) * smoke
a = np.clip(a, 0, 1) * smooth(1.0, 0.97, R)
img = np.zeros((S, S, 4))
img[..., 0] = img[..., 1] = img[..., 2] = 1
img[..., 3] = a
save_png(os.path.join(out_dir, 'tx_csigil.png'), img)

# ---------------------------------------------------------------- blood drop
S = 128
U, V = grid(S)
# teardrop: a circle at the bottom pulled up into a point
dy = V + 0.3
w = np.where(dy < 0, np.sqrt(np.clip(0.36 - dy * dy, 0, None)), 0.6 * np.clip(1 - dy / 1.0, 0, 1) ** 1.6)
drop = smooth(w + 0.03, w - 0.03, np.abs(U)) * (V < 0.75) * (V > -0.92)
shine = np.exp(-(((U + 0.18) ** 2 + (V + 0.18) ** 2) / 0.012))
img = np.zeros((S, S, 4))
g = np.clip(0.75 + 0.25 * shine, 0, 1)
img[..., 0] = img[..., 1] = img[..., 2] = g
img[..., 3] = np.clip(drop, 0, 1)
save_png(os.path.join(out_dir, 'tx_drop.png'), img)
print('wrote', out_dir)
