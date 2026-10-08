"""Compose PNGs into one contact sheet on a light background.
    python sheet.py <out.png> <cols> <tile_px> <in1.png> [<in2.png> ...]"""
import sys, zlib, struct
import numpy as np


def load(path):
    b = open(path, 'rb').read()
    i, idat, w, h, ct = 8, b'', 0, 0, 6
    while i < len(b):
        n = struct.unpack('>I', b[i:i + 4])[0]
        t, c = b[i + 4:i + 8], b[i + 8:i + 8 + n]
        if t == b'IHDR':
            w, h = struct.unpack('>II', c[:8])
            ct = c[9]
        elif t == b'IDAT':
            idat += c
        i += 12 + n
    ch = 4 if ct == 6 else 3
    raw = zlib.decompress(idat)
    stride = w * ch
    out = np.zeros((h, stride), np.uint8)
    prev = np.zeros(stride, np.int32)
    pos = 0
    for y in range(h):      # undo PNG row filters
        f = raw[pos]
        row = np.frombuffer(raw[pos + 1:pos + 1 + stride], np.uint8).astype(np.int32)
        pos += 1 + stride
        if f == 0:
            cur = row
        elif f == 2:
            cur = (row + prev) & 255
        else:
            cur = np.zeros(stride, np.int32)
            for x in range(stride):
                a = cur[x - ch] if x >= ch else 0
                c = prev[x - ch] if x >= ch else 0
                if f == 1:
                    cur[x] = (row[x] + a) & 255
                elif f == 3:
                    cur[x] = (row[x] + ((a + prev[x]) >> 1)) & 255
                else:
                    p = a + prev[x] - c
                    pa, pb, pc = abs(p - a), abs(p - prev[x]), abs(p - c)
                    pr = a if pa <= pb and pa <= pc else prev[x] if pb <= pc else c
                    cur[x] = (row[x] + pr) & 255
        out[y] = cur
        prev = cur
    img = out.reshape(h, w, ch) / 255.0
    if ch == 3:
        img = np.concatenate([img, np.ones((h, w, 1))], 2)
    return img


def resize(img, size):
    h, w = img.shape[:2]
    ys = (np.arange(size) * h / size).astype(int)
    xs = (np.arange(size) * w / size).astype(int)
    return img[ys][:, xs]


def save(path, rgb):
    data = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    h, w = data.shape[:2]
    raw = b''.join(b'\x00' + data[y].tobytes() for y in range(h))
    def chunk(t, p):
        c = struct.pack('>I', len(p)) + t + p
        return c + struct.pack('>I', zlib.crc32(t + p) & 0xffffffff)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                           + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


out, cols, tile = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
files = sys.argv[4:]
rows = (len(files) + cols - 1) // cols
sheet = np.ones((rows * tile, cols * tile, 3)) * np.array([0.82, 0.9, 0.97])
for k, f in enumerate(files):
    img = resize(load(f), tile)
    r, c = divmod(k, cols)
    a = img[..., 3:]
    sheet[r * tile:(r + 1) * tile, c * tile:(c + 1) * tile] = sheet[r * tile:(r + 1) * tile, c * tile:(c + 1) * tile] * (1 - a) + img[..., :3] * a
save(out, sheet)
print('sheet', out)
