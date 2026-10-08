"""Flipbook sprite sheets (and a couple of single textures) for the mutation VFX.
White / greyscale on alpha so Roblox tints them. Each sheet is 1024x1024 = a 4x4 grid of 256px
frames, read left-to-right, top-to-bottom (ParticleEmitter.FlipbookLayout = Grid4x4).
    <blender python> mutation_flipbooks.py [out_dir]
Writes:
  fb_coin      spinning gold coin, shaded rim + embossed star (Loop)
  fb_gem       spinning brilliant-cut gem with facet shading (Loop)
  fb_flare     sparkle that bursts open, spins and fades (OneShot)
  fb_shock     shockwave ring that expands and breaks up (OneShot)
  fb_vortex    3-arm spiral galaxy swirl, seamless rotation (Loop)
  fb_bolt      crackling electric arcs, a new bolt every frame (Random)
  fb_puff      nebula puff that billows out and dissolves (OneShot)
  fb_rays      god-ray burst slowly turning, seamless (Loop)
  tx_sigil     magic circle for the ground (single texture, spun with RotSpeed)
"""
import sys, os, math, zlib, struct
import numpy as np

F = 256          # frame size
G = 4            # grid
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


yy, xx = np.mgrid[0:F, 0:F].astype(np.float64)
u = (xx + 0.5) / F * 2 - 1          # -1..1 left->right
v = 1 - (yy + 0.5) / F * 2          # -1..1 bottom->top (flipped back on save)
r = np.sqrt(u * u + v * v)
ang = np.arctan2(v, u)


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def edge_fade(a):
    """keep everything off the frame border so neighbouring frames never bleed"""
    return a * (1 - smooth(0.9, 0.99, np.maximum(np.abs(u), np.abs(v))))


def frame(gray, alpha):
    out = np.zeros((F, F, 4))
    out[..., 0] = out[..., 1] = out[..., 2] = np.clip(gray, 0, 1)
    out[..., 3] = np.clip(edge_fade(alpha), 0, 1)
    return out                       # v=+1 is row 0, already top->bottom


def sheet(frames):
    out = np.zeros((F * G, F * G, 4))
    for i, fr in enumerate(frames):
        gy, gx = divmod(i, G)
        out[gy * F:(gy + 1) * F, gx * F:(gx + 1) * F] = fr
    return out


# --- value noise / fbm (tileable in angle when sampled on a circle) ---------------------------
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
        x1 = x0 + 1
        y1 = y0 + 1
        a = g[y0, x0] * (1 - fx) + g[y0, x1] * fx
        b = g[y1, x0] * (1 - fx) + g[y1, x1] * fx
        return a * (1 - fy) + b * fy
    return sample


def fbm(sample, x, y, octaves=4):
    tot, amp, norm = 0, 1.0, 0
    for o in range(octaves):
        tot = tot + sample(x * 2 ** o, y * 2 ** o) * amp
        norm += amp
        amp *= 0.5
    return tot / norm


N1 = make_noise(11, 64)
N2 = make_noise(23, 64)

out_sheets = {}

# ---------------------------------------------------------------- coin
frames = []
for i in range(NF):
    th = i / NF * 2 * math.pi
    c = math.cos(th)
    w = max(abs(c), 0.06)             # apparent width
    R = 0.78
    ex = u / w                        # unsquash into coin space
    rr = np.sqrt(ex * ex + v * v)
    disc = smooth(R, R - 0.02, rr)
    # edge band (the coin's thickness seen side-on)
    thick = 0.11 * abs(math.sin(th))
    side = (np.abs(u) < w * R + thick) & (np.abs(v) < np.sqrt(np.clip(1 - (np.clip(np.abs(u) - thick, 0, None) / (w * R + 1e-6)) ** 2, 0, 1)) * R)
    sgn = 1 if math.sin(th) >= 0 else -1
    side_mask = smooth(0, 0.02, (np.abs(u) - 0)) * side * (1 - disc)
    # face shading: raised rim, inner ring, embossed 5-point star
    rim = smooth(R - 0.16, R - 0.12, rr) * disc
    inner = np.exp(-((rr - (R - 0.22)) / 0.025) ** 2) * disc
    sa = np.arctan2(v, ex)
    kk = np.abs(np.mod(sa - math.pi / 2, 2 * math.pi / 5) / (2 * math.pi / 5) * 2 - 1)   # 1 at the points
    star_r = 0.14 + 0.2 * kk ** 1.6
    star = smooth(star_r + 0.02, star_r - 0.02, rr) * disc
    light = 0.5 + 0.5 * c                 # face brightness with turn
    gray = 0.62 + 0.18 * light
    gray = gray + 0.25 * rim - 0.25 * inner + 0.22 * star * (0.5 + 0.5 * np.clip(-ex - v, -1, 1))
    # moving specular glint across the face
    glint = np.exp(-(((ex + v) * 0.7 - math.sin(th) * 0.9) / 0.12) ** 2) * disc
    gray = gray + 0.45 * glint
    side_gray = 0.45 + 0.25 * np.cos(v * 3)
    gray = np.where(disc > 0.01, gray, side_gray)
    alpha = np.clip(disc + side_mask, 0, 1)
    frames.append(frame(gray, alpha))
out_sheets['fb_coin'] = sheet(frames)

# ---------------------------------------------------------------- gem (brilliant cut, spinning)
frames = []
facets = 8
for i in range(NF):
    th = i / NF * 2 * math.pi / facets * 2   # 2 facet steps per loop -> seamless (8-fold symmetry)
    # silhouette: crown (top trapezoid) + pavilion (point down)
    top, girdle, bottom = 0.55, 0.12, -0.85
    halfw_girdle = 0.82
    halfw_table = 0.42
    crown = (v >= girdle) & (v <= top)
    tw = halfw_table + (halfw_girdle - halfw_table) * (top - v) / (top - girdle)
    pav = (v < girdle) & (v >= bottom)
    pw = halfw_girdle * (v - bottom) / (girdle - bottom)
    hw = np.where(crown, tw, np.where(pav, pw, 0))
    inside = (np.abs(u) < hw) & (crown | pav)
    alpha = smooth(0, 0.03, hw - np.abs(u)) * inside
    # facets: the horizontal position maps to an angle round the gem; the gem spins by th
    phi = np.arcsin(np.clip(u / np.maximum(hw, 1e-3), -1, 1)) + th
    seg = np.floor(phi / (2 * math.pi / facets))
    facet_center = (seg + 0.5) * (2 * math.pi / facets)
    normal_x = np.sin(facet_center - th)
    shade = 0.55 + 0.4 * np.cos(facet_center * 1.0 + 0.6) * 0.5 + 0.25 * normal_x
    # facet edges as thin bright lines
    fpos = np.mod(phi, 2 * math.pi / facets) / (2 * math.pi / facets)
    edges = np.exp(-(np.minimum(fpos, 1 - fpos) / 0.04) ** 2) * (np.cos(phi - th) > 0)
    # crown gets lighter, pavilion has the star-fire diagonals
    shade = np.where(crown, shade + 0.15, shade - 0.05 + 0.2 * (np.mod(seg, 2) == 0) * (v < -0.2))
    table = crown & (v > top - 0.06)
    gray = np.clip(shade + 0.35 * edges, 0.25, 1)
    gray = np.where(table, 0.95, gray)
    girdle_line = np.exp(-((v - girdle) / 0.015) ** 2) * inside
    gray = np.clip(gray + 0.4 * girdle_line, 0, 1)
    # internal sparkle that drifts
    sx, sy = 0.3 * math.cos(th * 4), 0.15 + 0.2 * math.sin(th * 4)
    sp = np.exp(-(((u - sx) ** 2 + (v - sy) ** 2) / 0.006))
    spx = np.exp(-((u - sx) / 0.015) ** 2) * np.exp(-((v - sy) / 0.2) ** 2) + np.exp(-((v - sy) / 0.015) ** 2) * np.exp(-((u - sx) / 0.2) ** 2)
    gray = np.clip(gray + (sp + spx) * inside, 0, 1)
    alpha = np.clip(alpha + 0.8 * (sp + spx) * inside, 0, 1)
    frames.append(frame(gray, alpha))
out_sheets['fb_gem'] = sheet(frames)

# ---------------------------------------------------------------- flare (one shot)
frames = []
for i in range(NF):
    t = i / (NF - 1)
    grow = smooth(0, 0.3, t)
    fade = 1 - smooth(0.45, 1, t)
    rot = t * 0.6
    length = 0.25 + 0.7 * grow
    a1 = ang - rot

    def ray(a, width, ln):
        d = np.abs(np.sin(a1 - a)) * r
        along = np.abs(np.cos(a1 - a)) * r
        return np.exp(-(d / width) ** 2) * np.clip(1 - along / ln, 0, 1) ** 1.6
    star = ray(0, 0.04, length) + ray(math.pi / 2, 0.04, length)
    star += 0.5 * (ray(math.pi / 4, 0.025, length * 0.55) + ray(-math.pi / 4, 0.025, length * 0.55))
    core = np.exp(-(r / (0.06 + 0.1 * grow * fade)) ** 2)
    halo = 0.35 * np.exp(-(r / (0.2 + 0.25 * grow)) ** 2)
    ring = 0.5 * np.exp(-((r - 0.15 - 0.6 * t) / 0.025) ** 2) * (1 - t)
    a = (star + core + halo + ring) * fade
    frames.append(frame(np.ones_like(r), a))
out_sheets['fb_flare'] = sheet(frames)

# ---------------------------------------------------------------- shockwave (one shot)
frames = []
for i in range(NF):
    t = i / (NF - 1)
    rad = 0.12 + 0.78 * (1 - (1 - t) ** 2)
    width = 0.03 + 0.08 * t
    n = fbm(N1, np.cos(ang) * 3 + 10 + t * 2, np.sin(ang) * 3 + 10, 3)
    breakup = smooth(0.25 + 0.55 * t, 0.45 + 0.55 * t, n + 0.15)
    band = np.exp(-((r - rad) / width) ** 2)
    inner_glow = 0.35 * smooth(rad, rad * 0.4, r) * (r < rad) * (1 - t)
    streaks = 0.5 * np.exp(-((r - rad * 0.85) / (width * 2)) ** 2) * (0.5 + 0.5 * np.sin(ang * 24 + n * 6))
    a = (band * (0.4 + 0.6 * breakup) + streaks * breakup + inner_glow) * (1 - smooth(0.6, 1, t))
    gray = 0.85 + 0.15 * band
    frames.append(frame(gray, a))
out_sheets['fb_shock'] = sheet(frames)

# ---------------------------------------------------------------- vortex (loop)
frames = []
arms = 3
for i in range(NF):
    rot = i / NF * 2 * math.pi / arms        # seamless: one arm-step per loop
    spiral = np.mod(ang * arms - np.log(r + 1e-4) * 4.5 + rot * arms, 2 * math.pi)
    armv = 0.5 + 0.5 * np.cos(spiral)
    armv = armv ** 2
    n = fbm(N2, np.cos(ang) * (2 + r * 4) + 20, np.sin(ang) * (2 + r * 4) + 20, 4)
    dust = armv * (0.55 + 0.45 * n) * smooth(1.0, 0.25, r)
    core = np.exp(-(r / 0.13) ** 2) + 0.5 * np.exp(-(r / 0.3) ** 2)
    # tiny stars scattered in the arms
    sparkle = (N1(u * 40 + 3, v * 40 + 7) > 0.93) * armv * smooth(0.95, 0.4, r)
    a = np.clip(dust * 1.4 + core + sparkle, 0, 1) * smooth(0.98, 0.7, r)
    gray = np.clip(0.6 + 0.4 * core + 0.3 * armv, 0, 1)
    frames.append(frame(gray, a))
out_sheets['fb_vortex'] = sheet(frames)

# ---------------------------------------------------------------- bolt (random frames)
frames = []
rng = np.random.default_rng(5)


def bolt_path(x0, y0, x1, y1, depth, jag):
    if depth == 0:
        return [(x0, y0), (x1, y1)]
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = x1 - x0, y1 - y0
    ln = math.hypot(dx, dy)
    off = rng.normal(0, jag * ln)
    mx += -dy / (ln + 1e-6) * off
    my += dx / (ln + 1e-6) * off
    return bolt_path(x0, y0, mx, my, depth - 1, jag)[:-1] + bolt_path(mx, my, x1, y1, depth - 1, jag)


def seg_dist(px, py, ax, ay, bx, by):
    abx, aby = bx - ax, by - ay
    t = np.clip(((px - ax) * abx + (py - ay) * aby) / (abx * abx + aby * aby + 1e-9), 0, 1)
    return np.hypot(px - (ax + abx * t), py - (ay + aby * t))


for i in range(NF):
    a = np.zeros_like(r)
    gray = np.ones_like(r)
    nb = 2
    for b in range(nb):
        a0 = rng.uniform(0, 2 * math.pi)
        a1 = a0 + math.pi + rng.uniform(-0.9, 0.9)
        p = bolt_path(0.82 * math.cos(a0), 0.82 * math.sin(a0), 0.82 * math.cos(a1), 0.82 * math.sin(a1), 6, 0.22)
        d = np.full_like(r, 9.0)
        for (ax, ay), (bx, by) in zip(p[:-1], p[1:]):
            d = np.minimum(d, seg_dist(u, v, ax, ay, bx, by))
        # a branch
        k = rng.integers(len(p) // 4, 3 * len(p) // 4)
        bx0, by0 = p[k]
        ba = rng.uniform(0, 2 * math.pi)
        q = bolt_path(bx0, by0, bx0 + 0.4 * math.cos(ba), by0 + 0.4 * math.sin(ba), 4, 0.25)
        d2 = np.full_like(r, 9.0)
        for (ax, ay), (cx, cy) in zip(q[:-1], q[1:]):
            d2 = np.minimum(d2, seg_dist(u, v, ax, ay, cx, cy))
        a = a + np.exp(-(d / 0.012) ** 2) + 0.45 * np.exp(-(d / 0.06) ** 2)
        a = a + 0.7 * np.exp(-(d2 / 0.009) ** 2) + 0.25 * np.exp(-(d2 / 0.04) ** 2)
    frames.append(frame(gray, np.clip(a, 0, 1) * smooth(0.98, 0.8, r)))
out_sheets['fb_bolt'] = sheet(frames)

# ---------------------------------------------------------------- puff (one shot)
frames = []
for i in range(NF):
    t = i / (NF - 1)
    rad = 0.3 + 0.55 * (1 - (1 - t) ** 2)
    n = fbm(N2, u * 2.5 + 5 + t * 0.6, v * 2.5 + 5 - t * 0.8, 5)
    shape = smooth(rad, rad * 0.4, r * (0.8 + 0.5 * n))
    dissolve = smooth(t * 0.9 - 0.1, t * 0.9 + 0.15, n)
    a = shape * (0.35 + 0.65 * n) * dissolve * smooth(0, 0.12, t)
    gray = 0.55 + 0.45 * n
    frames.append(frame(gray, a))
out_sheets['fb_puff'] = sheet(frames)

# ---------------------------------------------------------------- god rays (loop)
frames = []
nr = 12
for i in range(NF):
    rot = i / NF * 2 * math.pi / nr
    rays = 0.5 + 0.5 * np.cos((ang - rot) * nr)
    rays2 = 0.5 + 0.5 * np.cos((ang + rot * 2) * 7 + 1.3)
    rr_ = rays ** 6 * 0.8 + rays2 ** 10 * 0.5
    a = rr_ * smooth(0.95, 0.1, r) + np.exp(-(r / 0.18) ** 2)
    frames.append(frame(np.ones_like(r), np.clip(a, 0, 1)))
out_sheets['fb_rays'] = sheet(frames)

# ---------------------------------------------------------------- sigil (single 512 texture)
S = 512
sy_, sx_ = np.mgrid[0:S, 0:S].astype(np.float64)
su = (sx_ + 0.5) / S * 2 - 1
sv = 1 - (sy_ + 0.5) / S * 2
sr = np.sqrt(su * su + sv * sv)
sa = np.arctan2(sv, su)


def ringl(rad, w):
    return np.exp(-((sr - rad) / w) ** 2)


sig = ringl(0.93, 0.012) + ringl(0.86, 0.008) + ringl(0.62, 0.01) + 0.6 * ringl(0.55, 0.006)
# runic ticks between the outer rings
tick = (np.abs(np.sin(sa * 36)) < 0.18) & (sr > 0.87) & (sr < 0.92)
dash = (np.mod(sa * 18 / math.pi, 2) < 1.2) & (sr > 0.7) & (sr < 0.78)
glyph_band = (sr > 0.66) & (sr < 0.82)
glyph = glyph_band * ((np.abs(np.sin(sa * 24 + sr * 30)) < 0.12) | (np.abs(sr - 0.74) < 0.008))
# 8-point star polygon inside
star_d = np.full_like(sr, 9.0)
pts = [(0.6 * math.cos(k * 2 * math.pi / 8 + math.pi / 8), 0.6 * math.sin(k * 2 * math.pi / 8 + math.pi / 8)) for k in range(8)]
for k in range(8):
    ax, ay = pts[k]
    bx, by = pts[(k + 3) % 8]
    star_d = np.minimum(star_d, seg_dist(su, sv, ax, ay, bx, by))
sig = sig + np.exp(-(star_d / 0.008) ** 2) + tick * 0.9 + glyph * 0.7 + dash * 0.25
sig = sig + 0.6 * ringl(0.18, 0.012) + 0.25 * np.exp(-(sr / 0.5) ** 2)
sig = np.clip(sig, 0, 1) * smooth(0.99, 0.95, sr)
out = np.zeros((S, S, 4))
out[..., :3] = 1
out[..., 3] = sig
sigil = out

dest = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'export', 'vfx')
os.makedirs(dest, exist_ok=True)
for name, img in out_sheets.items():
    save_png(os.path.join(dest, name + '.png'), img)
save_png(os.path.join(dest, 'tx_sigil.png'), sigil)
print('wrote', len(out_sheets) + 1, 'textures to', dest)
