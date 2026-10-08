"""Generate particle textures for Monster Heist VFX (white/greyscale so Roblox can tint them).
    python vfx_textures.py <out_dir>
Writes glow, mote, star, ring, leaf, spore, wisp and shard PNGs (256x256 RGBA)."""
import sys, os, zlib, struct, math
import numpy as np

N = 256


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


yy, xx = np.mgrid[0:N, 0:N].astype(np.float64)
u = (xx + 0.5) / N * 2 - 1      # -1..1, left to right
v = 1 - (yy + 0.5) / N * 2      # -1..1, bottom to top
r = np.sqrt(u * u + v * v)
ang = np.arctan2(v, u)
rng = np.random.default_rng(7)


def rgba(gray, alpha, tint=(1, 1, 1)):
    out = np.zeros((N, N, 4))
    for i in range(3):
        out[..., i] = gray * tint[i]
    out[..., 3] = alpha
    return out


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


textures = {}

# soft round glow
textures['glow'] = rgba(np.ones_like(r), np.exp(-(r / 0.42) ** 2) * (1 - smooth(0.85, 1.0, r)))

# bright mote: hard core + soft halo
core = 1 - smooth(0.08, 0.16, r)
halo = np.exp(-(r / 0.35) ** 2) * 0.6
textures['mote'] = rgba(np.ones_like(r), np.clip(core + halo, 0, 1) * (1 - smooth(0.8, 1.0, r)))

# four-point star sparkle with a faint diagonal cross
def ray(a, width, length):
    d = np.abs(np.sin(ang - a)) * r
    along = np.abs(np.cos(ang - a)) * r
    return np.exp(-(d / width) ** 2) * np.clip(1 - along / length, 0, 1) ** 1.5
star = ray(0, 0.05, 1.0) + ray(math.pi / 2, 0.05, 1.0) + 0.45 * (ray(math.pi / 4, 0.035, 0.55) + ray(-math.pi / 4, 0.035, 0.55))
star += np.exp(-(r / 0.12) ** 2)
textures['star'] = rgba(np.ones_like(r), np.clip(star, 0, 1))

# ring (for ground auras / shockwaves)
textures['ring'] = rgba(np.ones_like(r), np.exp(-((r - 0.72) / 0.09) ** 2) + 0.35 * np.exp(-((r - 0.72) / 0.22) ** 2))

# leaf: pointed oval with a midrib and side veins, light-to-dark shading
lu, lv = u * 1.0, v * 1.15
half_w = 0.48 * np.clip(1 - lv * lv, 0, 1) ** 0.7 * (1 - 0.15 * lv)
inside = smooth(0.0, 0.03, half_w - np.abs(lu))
rib = np.exp(-(lu / 0.025) ** 2) * (np.abs(lv) < 0.92)
veins = np.zeros_like(r)
for k in np.linspace(-0.6, 0.6, 6):
    d = np.abs(lv - (k + np.abs(lu) * 0.8))
    veins += np.exp(-(d / 0.02) ** 2) * (np.abs(lu) < half_w * 0.9)
shade = 0.78 + 0.22 * (lu + 0.5)
gray = np.clip(shade - 0.25 * rib - 0.12 * np.clip(veins, 0, 1), 0.3, 1)
stem = (np.abs(lu) < 0.025) & (lv < -0.85) & (lv > -1.0)
textures['leaf'] = rgba(gray, np.clip(inside + stem, 0, 1))

# fuzzy spore: soft ball with wispy filaments
fil = 0.5 + 0.5 * np.sin(ang * 13 + 2 * np.sin(ang * 5))
edge = 0.35 + 0.12 * fil
spore = np.exp(-(r / 0.18) ** 2) + 0.55 * smooth(edge + 0.1, edge - 0.05, r) * (0.5 + 0.5 * fil)
textures['spore'] = rgba(np.ones_like(r), np.clip(spore, 0, 1) * (1 - smooth(0.85, 1.0, r)))

# wisp: soft vertical-gradient streak for trails (bright centre line, fades to edges)
textures['wisp'] = rgba(np.ones_like(r), np.exp(-(v / 0.35) ** 2) * (0.6 + 0.4 * np.cos(u * 3) ** 2))

# shard glint: elongated diamond with a hot centre
dia = 1 - smooth(0.85, 1.0, np.abs(u) / 0.35 + np.abs(v) / 0.95)
textures['shard'] = rgba(np.ones_like(r), np.clip(dia * 0.75 + np.exp(-(r / 0.12) ** 2), 0, 1))

out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), 'export', 'vfx')
os.makedirs(out, exist_ok=True)
for name, img in textures.items():
    save_png(os.path.join(out, f'mh_{name}.png'), img[::-1])   # PNG rows go top to bottom
print('wrote', len(textures), 'textures to', out)


# ---- UI textures -------------------------------------------------------------------------
def ui_textures(out):
    """Tileable Roblox-style stud overlay and a diagonal shine for title bars (greyscale + alpha,
    meant to sit on top of coloured frames)."""
    S = 128                     # one stud per tile; tile it in Roblox
    y, x = np.mgrid[0:S, 0:S].astype(np.float64)
    cu = (x + 0.5) / S - 0.5
    cv = (y + 0.5) / S - 0.5
    rr = np.sqrt(cu * cu + cv * cv)
    stud = smooth(0.30, 0.28, rr)                                 # stud disc
    rim = np.exp(-((rr - 0.29) / 0.025) ** 2)                     # dark outline ring
    light = np.clip(-(cu + cv) * 2.2, 0, 1) * stud                # lit from the top-left
    shade = np.clip((cu + cv) * 2.2, 0, 1) * stud
    gray = np.clip(0.5 + 0.5 * light - 0.35 * shade - 0.3 * rim, 0, 1)
    alpha = np.clip(0.55 * stud + 0.5 * rim + 0.18 * (light + shade), 0, 1)
    save_png(os.path.join(out, 'ui_stud.png'), rgba_any(gray, alpha))

    W, Hh = 512, 64
    y, x = np.mgrid[0:Hh, 0:W].astype(np.float64)
    d = (x + y * 1.0) % 160
    stripes = ((d > 20) & (d < 60)) * 1.0 + ((d > 75) & (d < 88)) * 0.7
    save_png(os.path.join(out, 'ui_shine.png'), rgba_any(np.ones_like(stripes), stripes * 0.35))


def rgba_any(gray, alpha):
    out = np.zeros(gray.shape + (4,))
    out[..., 0] = out[..., 1] = out[..., 2] = gray
    out[..., 3] = alpha
    return out


ui_textures(out)
print('wrote UI textures')


# ---- map textures ------------------------------------------------------------------------
def map_textures(out):
    """Neutral grey checker with stud bumps; tint it per surface with Texture.Color3
    (bright green grass, darker forest floor, brown cliffs). 2x2 squares, 4x4 studs per square."""
    S = 512
    y, x = np.mgrid[0:S, 0:S].astype(np.float64)
    sq = ((x // (S / 2)) + (y // (S / 2))) % 2           # checker squares
    base = np.where(sq == 0, 0.93, 0.82)
    cell = S / 8                                         # 4 studs per square side
    cu = (x % cell) / cell - 0.5
    cv = (y % cell) / cell - 0.5
    rr = np.sqrt(cu * cu + cv * cv)
    stud = smooth(0.33, 0.30, rr)
    light = np.clip(-(cu + cv) * 2.0, 0, 1) * stud
    shade = np.clip((cu + cv) * 2.0, 0, 1) * stud
    rim = np.exp(-((rr - 0.32) / 0.03) ** 2)
    gray = np.clip(base + 0.07 * light - 0.06 * shade - 0.05 * rim, 0, 1)
    save_png(os.path.join(out, 'map_checker.png'), rgba_any(gray, np.ones_like(gray)))


map_textures(out)
print('wrote map textures')
