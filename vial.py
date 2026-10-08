"""Cosmic Vial - modelled and textured from scratch to match the user's icon
(game2/assets/icons/cosmic_mutation_vial.png), proportions measured off it.
Nothing from the icon image is used as texture. The look is made here:
  * steel, gold, gem and glow materials are hand-built cel shaders in the icon's painted style
    (soft two-tone light from the upper left, bright bevelled edges, purple bounce light, a little
    brush noise, sparkles on the gems), baked into one texture atlas
  * the galaxy in the glass is painted in code (spiral arms, core, nebula, star dust, sparkles,
    glass streaks) and packed into the same atlas
The orbit ring, floating crystals and the moving glow are VFX in game.
    blender -b --factory-startup --python vial.py -- <out_dir>      (build, bake, export, preview)
    blender --factory-startup --python vial.py -- <out_dir> --live   (watch it get built)
Units: 1 = 100 icon pixels; Z up, the front faces -Y."""
import bpy, bmesh, sys, os, math
import numpy as np
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
LIVE = '--live' in args
args = [a for a in args if a != '--live']
OUT = args[0] if args else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'export', 'vial')
IH = 724
CX = 274
K = 0.11                   # the icon is seen slightly from above: 1 unit nearer sits 11 px lower
ATLAS = 1024
GLASS_ROWS = 388           # top strip of the atlas holds the painted glass (1024 x 388 = its unrolled shape)

# side silhouette (icon row, half-width px, material of the band below this ring)
TOP = [(12, 30, 'glow'), (16, 46, 'glow'), (34, 60, 'steel'), (70, 96, 'steel'), (74, 100, 'steel'),
       (100, 124, 'steel'), (102, 164, 'steel'), (186, 164, 'steel'), (188, 142, 'gold'), (194, 144, 'gold'),
       (226, 136, 'gold'), (234, 120, 'gold')]
BOTTOM = [(506, 120, 'gold'), (512, 136, 'gold'), (536, 158, 'gold'), (558, 158, 'steel'), (560, 165, 'steel'),
          (612, 165, 'steel'), (624, 143, 'steel'), (636, 129, 'steel'), (640, 94, 'steel'), (672, 68, 'glow'),
          (684, 56, 'glow'), (704, 24, 'glow')]
GLASS = (226, 514, 121)
SECTION = [(0.6, -0.95), (1.0, -0.4), (1.0, 0.4), (0.6, 0.95), (-0.6, 0.95), (-1.0, 0.4), (-1.0, -0.4), (-0.6, -0.95)]
GLASS_SIDES = 40
MATS = ['steel', 'gold', 'gem', 'glow', 'glass']


def z_of(row):
    return (IH - row) / 100.0


def place(sx, sy, y):
    return Vector(((sx - CX) / 100.0, y, z_of(sy - K * 100 * abs(y))))


def lin(hexs):
    h = hexs.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


# ---------------------------------------------------------------- painted glass (galaxy)

def fbm(h, w, seed, scale):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w))
    for octave in range(4):
        n = rng.standard_normal((h, w))
        fy = np.fft.fftfreq(h)[:, None]
        fx = np.fft.fftfreq(w)[None, :]
        s = scale / (2 ** octave)
        g = np.exp(-(fx ** 2 + fy ** 2) * (s ** 2) * 2)
        f = np.real(np.fft.ifft2(np.fft.fft2(n) * g))
        out += f / (f.std() + 1e-9) / (1.6 ** octave)
    return (out - out.min()) / (out.max() - out.min())


def paint_glass(W=ATLAS, H=GLASS_ROWS):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
    pxu = W / (2 * math.pi * GLASS[2] / 100)            # pixels per unit around the tube

    def u_of(icon_x):                                     # icon column -> atlas column on the front
        return W / 2 + math.asin(max(-0.99, min(0.99, (icon_x - CX) / GLASS[2]))) / (2 * math.pi) * W

    def v_of(icon_y):
        return (icon_y - GLASS[0]) / (GLASS[1] - GLASS[0]) * H

    def col(h):
        return np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)])

    n1 = fbm(H, W, 1, 40)
    n2 = fbm(H, W, 2, 22)
    n3 = fbm(H, W, 3, 6)
    img = np.zeros((H, W, 3))
    img += col('#0b0f3c')
    img += (col('#2a3fc8') - col('#0b0f3c')) * (np.clip(n1 - 0.35, 0, 1) * 1.3)[..., None]
    img += col('#5a2aa8') * (np.clip(n2 - 0.5, 0, 1) * 1.1)[..., None]

    def galaxy(cx, cy, R, rot, strength):
        dx = (xx - cx + W / 2) % W - W / 2
        dy = yy - cy
        r = np.sqrt(dx ** 2 + dy ** 2) + 1e-6
        th = np.arctan2(dy, dx) + rot + (n2 - 0.5) * 0.9
        q = r / R
        arms = (0.5 + 0.5 * np.cos(2 * th - 5.5 * np.log(q + 0.03))) ** 2.6
        fade = np.exp(-q ** 2 * 2.4)
        t = np.clip(q * 1.4, 0, 1)[..., None]
        armcol = col('#ff9ee6') * (1 - t) + col('#9a52ff') * t
        g = arms[..., None] * fade[..., None] * armcol * 1.25 * strength
        g += (col('#c070ff') * np.exp(-q ** 2 * 5) * 0.35 * strength)[..., None] if False else col('#c070ff') * (np.exp(-q ** 2 * 5) * 0.35 * strength)[..., None]
        core = np.exp(-(q / 0.1) ** 2) * 1.3 + np.exp(-(q / 0.28) ** 2) * 0.45
        g += col('#fff1dc') * (core * strength)[..., None]
        return g, arms * fade

    g1, a1 = galaxy(u_of(CX), v_of(400), 1.05 * pxu, 0.0, 1.0)
    g2, a2 = galaxy(0, v_of(330), 0.75 * pxu, 2.0, 0.65)
    img += g1 + g2

    rng = np.random.default_rng(7)

    def dot(x, y, rad, c, a):
        x0, x1 = int(max(0, x - rad * 3)), int(min(W, x + rad * 3 + 1))
        y0, y1 = int(max(0, y - rad * 3)), int(min(H, y + rad * 3 + 1))
        if x0 >= x1 or y0 >= y1:
            return
        d2 = (xx[y0:y1, x0:x1] - x) ** 2 + (yy[y0:y1, x0:x1] - y) ** 2
        img[y0:y1, x0:x1] += c * (a * np.exp(-d2 / (rad * rad)))[..., None]

    # star dust along the arms, and scattered stars
    arms = a1 + a2 * 0.6
    for _ in range(2600):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        if rng.uniform() < arms[int(y), int(x)] * 0.9:
            dot(x, y, rng.uniform(0.7, 1.4), col('#ffd2f4'), rng.uniform(0.5, 1.0))
    for _ in range(420):
        dot(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.6, 1.2), col('#cfe0ff'), rng.uniform(0.3, 0.9))

    def sparkle(x, y, size, c):
        x0, x1 = int(max(0, x - size)), int(min(W, x + size + 1))
        y0, y1 = int(max(0, y - size)), int(min(H, y + size + 1))
        dx = np.abs(xx[y0:y1, x0:x1] - x)
        dy = np.abs(yy[y0:y1, x0:x1] - y)
        w = size * 0.07
        ray = np.maximum(np.exp(-dx / w) * np.clip(1 - dy / size, 0, 1) ** 2,
                         np.exp(-dy / w) * np.clip(1 - dx / size, 0, 1) ** 2)
        glow = np.exp(-(dx ** 2 + dy ** 2) / (size * 0.28) ** 2)
        a = np.clip(ray * 1.3 + glow * 0.9, 0, 1.4)
        img[y0:y1, x0:x1] += (c * 0.8 + 0.4) * a[..., None]

    # the icon's big sparkles, front, and a few more round the back
    for ix, iy, s, c in ((222, 270, 40, '#8fd0ff'), (346, 244, 26, '#ffb8f0'), (340, 300, 20, '#bfe6ff'),
                         (332, 458, 30, '#8fd0ff'), (224, 520, 34, '#ffffff'), (352, 524, 24, '#ffd8f6')):
        sparkle(u_of(ix), v_of(iy), s, col(c))
    for u, iy, s in ((0.08, 280, 26), (0.9, 470, 30), (0.2, 480, 20), (0.78, 260, 22), (0.98, 400, 18)):
        sparkle(u * W, v_of(iy), s, col('#bfe0ff'))

    # glass: bright streaks down the tube (the icon's edge highlights) and a cool glow at both ends
    for ang in (-74, 74, 180 - 74, -(180 - 74)):
        u = (0.5 + ang / 360) % 1 * W
        d = np.abs((xx - u + W / 2) % W - W / 2)
        img += col('#9cc4ff') * (np.exp(-(d / 9) ** 2) * 0.55 + np.exp(-(d / 30) ** 2) * 0.18)[..., None]
        img += col('#ffffff') * (np.exp(-(d / 2.2) ** 2) * 0.75)[..., None]
    ends = np.exp(-(yy / 26) ** 2) + np.exp(-((H - yy) / 26) ** 2)
    img += col('#7d6cff') * (ends * 0.45)[..., None]
    img *= (0.92 + 0.16 * n3)[..., None]                 # brush texture
    return np.clip(img, 0, 1)


# ---------------------------------------------------------------- cel-shaded materials

LIGHT = Vector((-0.45, -0.65, 0.62)).normalized()
PALETTE = {
    'steel': dict(shadow='#141925', mid='#283043', lit='#465372', edge='#9cb2dc', bounce='#5b3fd0', brush=0.1),
    'gold': dict(shadow='#8f5320', mid='#d99a3c', lit='#ffd873', edge='#fff3c4', bounce='#a8642a', brush=0.08),
    'gem': dict(shadow='#2a0d8c', mid='#6236e6', lit='#a982ff', edge='#e2d2ff', bounce='#3a1ab0', brush=0.05),
}


class NB:
    def __init__(self, mat):
        mat.use_nodes = True
        self.nt = mat.node_tree
        self.nt.nodes.clear()
        self.L = self.nt.links

    def node(self, kind, **props):
        n = self.nt.nodes.new(kind)
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def put(self, sock, v):
        if isinstance(v, bpy.types.NodeSocket):
            self.L.new(v, sock)
        else:
            sock.default_value = v

    def vm(self, op, a, b=None, scale=None, out='Vector'):
        n = self.node('ShaderNodeVectorMath', operation=op)
        self.put(n.inputs[0], a)
        if b is not None:
            self.put(n.inputs[1], b)
        if scale is not None:
            self.put(n.inputs['Scale'], scale)
        return n.outputs[out]

    def m(self, op, a, b=None, clamp=False):
        n = self.node('ShaderNodeMath', operation=op, use_clamp=clamp)
        self.put(n.inputs[0], a)
        if b is not None:
            self.put(n.inputs[1], b)
        return n.outputs[0]

    def rng(self, v, a, b, c=0.0, d=1.0):
        n = self.node('ShaderNodeMapRange', clamp=True)
        self.put(n.inputs['Value'], v)
        n.inputs['From Min'].default_value = a
        n.inputs['From Max'].default_value = b
        n.inputs['To Min'].default_value = c
        n.inputs['To Max'].default_value = d
        return n.outputs['Result']

    def lerp(self, a, b, f):
        return self.vm('ADD', a, self.vm('SCALE', self.vm('SUBTRACT', b, a), scale=f))

    def finish(self, color):
        em = self.node('ShaderNodeEmission')
        self.put(em.inputs['Color'], color)
        out = self.node('ShaderNodeOutputMaterial')
        self.L.new(em.outputs[0], out.inputs['Surface'])


def toon(name):
    mat = bpy.data.materials.new(name)
    b = NB(mat)
    p = PALETTE[name]
    geo = b.node('ShaderNodeNewGeometry')
    bev = b.node('ShaderNodeBevel')
    bev.inputs['Radius'].default_value = 0.035
    N = bev.outputs['Normal']
    ndl = b.vm('DOT_PRODUCT', N, tuple(LIGHT), out='Value')
    c = b.lerp(lin(p['shadow']), lin(p['mid']), b.rng(ndl, -0.2, 0.15))
    c = b.lerp(c, lin(p['lit']), b.rng(ndl, 0.55, 0.68))
    edge = b.rng(b.m('SUBTRACT', 1.0, b.vm('DOT_PRODUCT', N, geo.outputs['Normal'], out='Value')), 0.004, 0.05)
    c = b.lerp(c, lin(p['edge']), b.m('MULTIPLY', edge, b.rng(ndl, -0.6, 0.3, 0.35, 0.95)))
    c = b.lerp(c, lin(p['bounce']), b.m('MULTIPLY', b.rng(ndl, -0.15, -0.65), 0.75))
    noise = b.node('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 7.0
    noise.inputs['Detail'].default_value = 4.0
    b.L.new(geo.outputs['Position'], noise.inputs['Vector'])
    c = b.vm('SCALE', c, scale=b.rng(noise.outputs['Fac'], 0.3, 0.7, 1 - p['brush'], 1 + p['brush']))
    if name == 'gem':
        # a four-point sparkle and glow at each gem's heart
        attr = b.node('ShaderNodeAttribute', attribute_name='gemc')
        d = b.vm('SUBTRACT', geo.outputs['Position'], attr.outputs['Vector'])
        sep = b.node('ShaderNodeSeparateXYZ')
        b.L.new(d, sep.inputs[0])
        ax = b.m('ABSOLUTE', sep.outputs['X'])
        az = b.m('ABSOLUTE', sep.outputs['Z'])
        star = b.m('SUBTRACT', 1.0, b.m('ADD', b.m('MULTIPLY', b.m('MULTIPLY', ax, az), 260.0),
                                        b.m('MULTIPLY', b.m('ADD', ax, az), 4.2)), clamp=True)
        glow = b.rng(b.vm('LENGTH', d, out='Value'), 0.0, 0.2, 0.75, 0.0)
        s = b.m('MAXIMUM', star, glow)
        c = b.lerp(c, lin('#fff6ff'), s)
        c = b.lerp(c, lin('#d9a6ff'), b.m('MULTIPLY', glow, 0.5))
    b.finish(c)
    return mat


def glow_mat():
    mat = bpy.data.materials.new('glow')
    b = NB(mat)
    geo = b.node('ShaderNodeNewGeometry')
    sep = b.node('ShaderNodeSeparateXYZ')
    b.L.new(geo.outputs['Normal'], sep.inputs[0])
    up = b.m('ABSOLUTE', sep.outputs['Z'])
    c = b.lerp(lin('#4a22c8'), lin('#9c6bff'), b.rng(up, 0.1, 0.6))
    c = b.lerp(c, lin('#efe0ff'), b.rng(up, 0.85, 1.0, 0.0, 0.85))
    b.finish(c)
    return mat


def glass_mat(img):
    mat = bpy.data.materials.new('glass')
    b = NB(mat)
    uvn = b.node('ShaderNodeUVMap', uv_map='GlassUV')
    tex = b.node('ShaderNodeTexImage', image=img)
    b.L.new(uvn.outputs['UV'], tex.inputs['Vector'])
    b.finish(tex.outputs['Color'])
    return mat


# ---------------------------------------------------------------- geometry

class Piece:
    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.gemc = self.bm.verts.layers.float_vector.new('gemc')

    def face(self, verts, mat):
        f = self.bm.faces.new(verts)
        f.material_index = MATS.index(mat)
        return f

    def lathe(self, profile):
        rings = []
        for row, hw, _ in profile:
            s = hw / 100.0
            rings.append([self.bm.verts.new((x * s, y * s, z_of(row))) for x, y in SECTION])
        n = len(SECTION)
        for i in range(len(rings) - 1):
            for k in range(n):
                k2 = (k + 1) % n
                self.face((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]), profile[i][2])
        self.face(list(reversed(rings[0])), profile[0][2])
        self.face(rings[-1], profile[-2][2])

    def solid(self, front, back, apex, mat, center=None):
        fv = [self.bm.verts.new(c) for c in front]
        bv = [self.bm.verts.new(c) for c in back]
        n = len(fv)
        for k in range(n):
            k2 = (k + 1) % n
            self.face((fv[k], bv[k], bv[k2], fv[k2]), mat)
        self.face(list(reversed(bv)), mat)
        av = self.bm.verts.new(apex)
        for k in range(n):
            self.face((fv[k], fv[(k + 1) % n], av), mat)
        if center is not None:
            for v in fv + bv + [av]:
                v[self.gemc] = center

    def star(self, cx, cy, up, down, side, y0):
        """the gold four-point star frame with its raised purple gem, front (y0 < 0) or back"""
        s = -1 if y0 < 0 else 1

        def outline(scale, inner, y):
            pts = [(0, -up), (inner * side, -inner * up), (side, 0), (inner * side, inner * down),
                   (0, down), (-inner * side, inner * down), (-side, 0), (-inner * side, -inner * up)]
            out = [place(cx + dx * scale, cy + dy * scale, y) for dx, dy in pts]
            return out if s < 0 else list(reversed(out))

        self.solid(outline(1.0, 0.34, y0 + s * 0.06), outline(0.94, 0.34, y0 - s * 0.08),
                   place(cx, cy, y0 + s * 0.2), 'gold')
        gy = y0 + s * 0.16
        gem_front = outline(0.56, 0.3, gy)
        apex = place(cx, cy, gy + s * 0.2)
        self.solid(gem_front, outline(0.5, 0.3, gy - s * 0.12), apex, 'gem', center=apex)

    def horn(self, base, tip, y, width, depth):
        s = -1 if y < 0 else 1
        b = place(base[0], base[1], y)
        t = place(tip[0], tip[1], y + s * 0.06)
        d = (t - b).normalized()
        side = Vector((-d.z, 0, d.x)) * width
        dep = Vector((0, depth, 0))
        vs = [self.bm.verts.new(c) for c in (b + side, b + dep, b - side, b - dep)]
        tv = self.bm.verts.new(t)
        for k in range(4):
            self.face((vs[k], vs[(k + 1) % 4], tv), 'gold')
        self.face(list(reversed(vs)), 'gold')

    def glass(self):
        z0, z1, hw = z_of(GLASS[1]), z_of(GLASS[0]), GLASS[2] / 100.0
        uvl = self.bm.loops.layers.uv.new('GlassUV')
        ring = lambda z: [self.bm.verts.new((hw * math.sin(-math.pi + 2 * math.pi * k / GLASS_SIDES),
                                             -hw * math.cos(-math.pi + 2 * math.pi * k / GLASS_SIDES), z))
                          for k in range(GLASS_SIDES)]
        lo, hi = ring(z0), ring(z1)
        for k in range(GLASS_SIDES):
            k2 = (k + 1) % GLASS_SIDES
            f = self.face((lo[k], lo[k2], hi[k2], hi[k]), 'glass')
            u0, u1 = k / GLASS_SIDES, (k + 1) / GLASS_SIDES
            for loop, uv in zip(f.loops, ((u0, 0), (u1, 0), (u1, 1), (u0, 1))):
                loop[uvl].uv = uv
            f.smooth = True

    def to_object(self, mats):
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in MATS:
            me.materials.append(mats[m])
        ob = bpy.data.objects.new(self.name, me)
        bpy.context.scene.collection.objects.link(ob)
        return ob


def build_steps(mats):
    """each step adds one piece of the vial (so the live window shows it being put together)"""
    band = 1.64 * 0.95 + 0.02

    def caps():
        p = Piece('Caps')
        p.lathe(TOP)
        p.lathe(BOTTOM)
        return p

    def glass():
        p = Piece('Glass')
        p.glass()
        return p

    def stars():
        p = Piece('Stars')
        for s in (-1, 1):
            p.star(CX, 172, 84, 81, 76, s * band)
            p.star(CX, 590, 68, 72, 67, s * band)
        return p

    def horns():
        p = Piece('Horns')
        for s in (-1, 1):
            for side in (-1, 1):
                p.horn((CX + side * 72, 106), (CX + side * 105, 50), s * 1.38, 0.17, 0.15)
                p.horn((CX + side * 96, 596), (CX + side * 117, 642), s * 1.6, 0.12, 0.1)
        return p

    return [caps, glass, stars, horns]


def finish_piece(ob):
    if ob.name.startswith('Glass'):
        return
    bev = ob.modifiers.new('Bevel', 'BEVEL')
    bev.width = 0.028
    bev.segments = 2
    bev.limit_method = 'ANGLE'
    bev.angle_limit = math.radians(25)
    bev.use_clamp_overlap = True
    bev.harden_normals = False


def make_materials(glass_img):
    return {'steel': toon('steel'), 'gold': toon('gold'), 'gem': toon('gem'), 'glow': glow_mat(), 'glass': glass_mat(glass_img)}


def glass_image():
    px = paint_glass()
    img = bpy.data.images.new('GlassPaint', ATLAS, GLASS_ROWS, alpha=False)
    rgba = np.concatenate([px, np.ones(px.shape[:2] + (1,))], -1)[::-1]
    img.pixels = rgba.astype(np.float32).ravel()
    return img, px


def clear():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def bake_and_export():
    os.makedirs(OUT, exist_ok=True)
    clear()
    glass_img, glass_px = glass_image()
    mats = make_materials(glass_img)
    obs = []
    for step in build_steps(mats):
        ob = step().to_object(mats)
        finish_piece(ob)
        obs.append(ob)
    scene = bpy.context.scene
    view = bpy.context.view_layer
    # body: apply bevels, join, unwrap into the lower part of the atlas
    body = [o for o in obs if o.name != 'Glass']
    glass = next(o for o in obs if o.name == 'Glass')
    for o in body:
        view.objects.active = o
        bpy.ops.object.modifier_apply(modifier='Bevel')
    bpy.ops.object.select_all(action='DESELECT')
    for o in body:
        o.select_set(True)
    view.objects.active = body[0]
    bpy.ops.object.join()
    B = view.objects.active
    B.name = 'CosmicVial'
    B.data.uv_layers.new(name='UVMap')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=0.006, area_weight=0.6)
    bpy.ops.object.mode_set(mode='OBJECT')
    region = (ATLAS - GLASS_ROWS - 6) / ATLAS
    for d in B.data.uv_layers['UVMap'].data:
        d.uv = (d.uv[0], d.uv[1] * region)
    for p in B.data.polygons:
        p.use_smooth = False

    # bake the cel shading into the atlas
    atlas = bpy.data.images.new('CosmicVial_atlas', ATLAS, ATLAS, alpha=False)
    for m in ('steel', 'gold', 'gem', 'glow'):
        nt = mats[m].node_tree
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = atlas
        nt.nodes.active = n
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 24
    scene.cycles.device = 'CPU'
    bpy.ops.object.select_all(action='DESELECT')
    B.select_set(True)
    view.objects.active = B
    bpy.ops.object.bake(type='EMIT', margin=6, use_clear=True)

    # the painted glass goes in the top strip
    A = np.array(atlas.pixels[:], np.float32).reshape(ATLAS, ATLAS, 4)
    A[ATLAS - GLASS_ROWS:, :, :3] = glass_px[::-1]
    A[..., 3] = 1
    atlas.pixels = A.ravel()
    atlas.filepath_raw = os.path.join(OUT, 'CosmicVial_tex.png')
    atlas.file_format = 'PNG'
    atlas.save()

    # glass UVs into that strip, then one mesh, one material
    g = glass.data
    guv = g.uv_layers['GlassUV']
    newuv = g.uv_layers.new(name='UVMap')
    lo = (ATLAS - GLASS_ROWS) / ATLAS
    for i, d in enumerate(guv.data):
        u, v = d.uv
        newuv.data[i].uv = (u, lo + v * GLASS_ROWS / ATLAS - 0.5 / ATLAS * (2 * v - 1))
    g.uv_layers.remove(g.uv_layers['GlassUV'])
    final = bpy.data.materials.new('CosmicVial')
    final.use_nodes = True
    nt = final.node_tree
    bsdf = nt.nodes['Principled BSDF']
    tn = nt.nodes.new('ShaderNodeTexImage')
    tn.image = atlas
    nt.links.new(tn.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(tn.outputs['Color'], bsdf.inputs['Emission Color'])
    bsdf.inputs['Emission Strength'].default_value = 1.0
    for o in (B, glass):
        o.data.materials.clear()
        o.data.materials.append(final)
    bpy.ops.object.select_all(action='DESELECT')
    B.select_set(True)
    glass.select_set(True)
    view.objects.active = B
    bpy.ops.object.join()
    B = view.objects.active
    B.data.uv_layers.active = B.data.uv_layers['UVMap']
    if 'GlassUV' in B.data.uv_layers:
        B.data.uv_layers.remove(B.data.uv_layers['GlassUV'])
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'CosmicVial.fbx'), use_selection=True, path_mode='COPY',
                             embed_textures=True, mesh_smooth_type='FACE')

    # previews: the texture as baked (that's what Roblox gets)
    bsdf.inputs['Base Color'].default_value = (0, 0, 0, 1)
    nt.links.remove(next(l for l in nt.links if l.to_socket == bsdf.inputs['Base Color']))
    scene.render.engine = 'BLENDER_EEVEE'
    scene.view_settings.view_transform = 'Standard'
    scene.render.film_transparent = True
    scene.render.resolution_x, scene.render.resolution_y = 600, 760
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 7.6
    scene.collection.objects.link(cam)
    scene.camera = cam
    mid = Vector((0, 0, z_of(360)))
    for name, d in {'front': (0, -1, K), 'quarter': (-0.8, -1, 0.25), 'side': (-1, 0, 0.15), 'back': (0.3, 1, 0.2)}.items():
        dv = Vector(d).normalized()
        cam.location = mid + dv * 20
        cam.rotation_euler = (mid - cam.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = os.path.join(OUT, f'CosmicVial_{name}.png')
        bpy.ops.render.render(write_still=True)
    print('BUILD OK CosmicVial')


def live():
    clear()
    glass_img, _ = glass_image()
    mats = make_materials(glass_img)
    steps = build_steps(mats)
    state = {'i': 0}

    def frame():
        for win in bpy.context.window_manager.windows:
            for area in win.screen.areas:
                if area.type == 'VIEW_3D':
                    for sp in area.spaces:
                        if sp.type == 'VIEW_3D':
                            sp.shading.type = 'MATERIAL'
                            sp.overlay.show_floor = False
                    region = next((r for r in area.regions if r.type == 'WINDOW'), None)
                    with bpy.context.temp_override(window=win, area=area, region=region):
                        try:
                            bpy.ops.view3d.view_all()
                        except Exception:
                            pass

    def tick():
        if state['i'] >= len(steps):
            return None
        ob = steps[state['i']]().to_object(mats)
        finish_piece(ob)
        state['i'] += 1
        frame()
        return 1.2

    bpy.app.timers.register(tick, first_interval=1.5)


if LIVE:
    bpy.app.timers.register(lambda: (live(), None)[1], first_interval=0.5)
else:
    bake_and_export()
