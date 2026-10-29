"""The Brute: an original hulking barbarian, built on the user's own muscle body (source/muscle_body.obj with its
normal maps), for the Roblox R6 rig.

Steps (each writes a viewport snapshot to export/steps/):
    body      the body, its normal maps, and a dark grey-brown skin colour map painted from them (creases darker,
              ridges catching the light)

    python build_brute.py -- --stage body
"""
import bpy, bmesh, math, os, sys
import numpy as np
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'armor'))
import build_armor as A                 # noqa: E402
from build_armor import lin, TAU        # noqa: E402

STAGE = A.STAGE
A.OUT = OUT = os.path.abspath(A.opt('--out', os.path.join(HERE, 'export')))
SRC = os.path.join(HERE, 'source')
STEPS = os.path.join(OUT, 'steps')
MATS = A.MATS

# the body's parts as exported from Studio, and the normal map each uses (matched by UV layout)
PARTS = {'Torso1': ('Torso', 'normal_torso'), 'ArmL1': ('LeftArm', 'normal_a'), 'ArmR1': ('RightArm', 'normal_a'),
         'LegL1': ('LeftLeg', 'normal_b'), 'LegR1': ('RightLeg', 'normal_b')}
SKIN = dict(base='#5d514c', crease='#231c1a', ridge='#86776f', warm='#6a4e44')


# ------------------------------------------------------------------ the body

def import_body():
    """the user's body, centred on the origin (feet at z 0) and turned to face -Y like everything else here"""
    before = set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=os.path.join(SRC, 'muscle_body.obj'), use_split_groups=True)
    obs = [o for o in bpy.data.objects if o not in before]
    pts = [o.matrix_world @ v.co for o in obs for v in o.data.vertices]
    cx = (min(p.x for p in pts) + max(p.x for p in pts)) / 2
    cy = (min(p.y for p in pts) + max(p.y for p in pts)) / 2
    z0 = min(p.z for p in pts)
    m = Matrix.Rotation(math.pi, 4, 'Z') @ Matrix.Translation((-cx, -cy, -z0))
    body = {}
    for o in obs:
        o.data.transform(m @ o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
        part, nmap = PARTS[o.name.split('.')[0]]
        o.name = o.data.name = 'Brute_' + part
        for p in o.data.polygons:
            p.use_smooth = True
        body[part] = (o, nmap)
    return body


def skin_maps(nmap):
    """from a part's normal map: a colour map (dark grey-brown skin, its creases deepened and its ridges lit, mottled)
    and a roughness map (a slight sheen on the ridges). Returns the two as Blender images"""
    from scipy import ndimage as ndi
    from PIL import Image
    a = np.asarray(Image.open(os.path.join(SRC, nmap + '.png')).convert('RGB'), dtype=np.float64) / 255.0
    nx, ny = a[..., 0] * 2 - 1, -(a[..., 1] * 2 - 1)       # image rows run down; OpenGL green runs up
    curv = ndi.gaussian_filter(np.gradient(nx, axis=1) + np.gradient(ny, axis=0), 1.5)
    curv /= np.percentile(np.abs(curv), 99) + 1e-6
    broad = ndi.gaussian_filter(curv, 6)
    H, W = curv.shape
    rng = np.random.default_rng(11)
    mott = ndi.gaussian_filter(rng.standard_normal((H, W)), 9)
    mott /= np.abs(mott).max()
    fine = ndi.gaussian_filter(rng.standard_normal((H, W)), 1.2)
    fine /= np.abs(fine).max()
    c = lambda h: np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)])
    col = np.ones((H, W, 3)) * c(SKIN['base'])
    crease = np.clip(-curv * 1.4 - broad * 0.6, 0, 1)[..., None]
    ridge = np.clip(curv * 1.1, 0, 1)[..., None]
    col = col * (1 - 0.55 * crease) + c(SKIN['crease']) * 0.55 * crease
    col = col * (1 - 0.35 * ridge) + c(SKIN['ridge']) * 0.35 * ridge
    m = np.clip(mott, 0, 1)[..., None]
    col = col * (1 - 0.18 * m) + c(SKIN['warm']) * 0.18 * m
    col *= (1 + 0.04 * fine)[..., None]
    # skin texture: pores and grain, a few old scars (lighter, raised), all kept inside the UV islands
    island = ndi.binary_erosion(np.abs(a - np.array([0.5, 0.5, 1.0])).sum(2) > 0.02, iterations=6)
    pores = ndi.gaussian_filter(rng.standard_normal((H, W)), 0.7)
    pores = np.clip(-pores / (np.abs(pores).max() + 1e-6) * 3, 0, 1) ** 1.5
    grain = ndi.gaussian_filter(rng.standard_normal((H, W)), 2.5)
    grain /= np.abs(grain).max()
    scar = np.zeros((H, W))
    ys, xs = np.nonzero(island)
    for k in range(5 if nmap == 'normal_torso' else 3):
        i = rng.integers(len(xs))
        x0, y0 = xs[i], ys[i]
        ang, length = rng.uniform(0, math.pi), rng.uniform(40, 110)
        bend = rng.uniform(-0.4, 0.4)
        for t in np.linspace(-0.5, 0.5, 200):
            a_ = ang + bend * t
            x, y = int(x0 + math.cos(a_) * length * t), int(y0 + math.sin(a_) * length * t)
            if 0 <= x < W and 0 <= y < H and island[y, x]:
                scar[y, x] = 1.0
        # a few stitch marks across the longest ones
    scar = np.clip(ndi.gaussian_filter(scar, 1.6) * 5, 0, 1)
    col = col * (1 - 0.06 * pores[..., None])
    col = col * (1 - 0.35 * scar[..., None]) + c('#8c776f') * 0.35 * scar[..., None]
    rough = np.clip(0.58 + 0.12 * crease[..., 0] - 0.1 * ridge[..., 0] + 0.03 * fine + 0.06 * pores - 0.12 * scar, 0, 1)
    # the detail's normals (pores and grain dimple in, scars stand proud), laid over the body's own normal map
    height = -0.6 * pores + 0.25 * grain + 1.8 * scar
    gy, gx = np.gradient(ndi.gaussian_filter(height, 0.8))
    d = np.dstack([-gx * 0.9, gy * 0.9, np.ones_like(gx)])
    d /= np.linalg.norm(d, axis=2, keepdims=True)
    base = a * 2 - 1
    t_ = base + np.array([0, 0, 1.0])            # reoriented normal blending: the detail follows the muscles' slopes
    u_ = d * np.array([-1, -1, 1.0])
    nrm = t_ * (t_ * u_).sum(2, keepdims=True) / t_[..., 2:3] - u_
    nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
    nrm = np.where(island[..., None], nrm, base)
    out = []
    for name, arr, srgb in ((nmap + '_skin', np.clip(col, 0, 1), True), (nmap + '_rough', np.dstack([rough] * 3), False),
                            (nmap + '_detail', nrm * 0.5 + 0.5, False)):
        im = bpy.data.images.new(name, W, H, alpha=False)
        im.colorspace_settings.name = 'sRGB' if srgb else 'Non-Color'
        px = np.ones((H, W, 4))
        px[..., :3] = np.where(arr > 0.04045, ((arr + 0.055) / 1.055) ** 2.4, arr / 12.92) if srgb else arr
        im.pixels = px[::-1].astype(np.float32).ravel()
        os.makedirs(os.path.join(OUT, 'textures'), exist_ok=True)
        im.filepath_raw = os.path.join(OUT, 'textures', name + '.png')
        im.file_format = 'PNG'
        im.save()
        out.append(im)
    return out


def skin_material(nmap):
    if 'Skin_' + nmap in MATS:
        return MATS['Skin_' + nmap]
    col, rough, nrm = skin_maps(nmap)
    m = bpy.data.materials.new('Skin_' + nmap)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexImage')
    tc.image = col
    tr = nt.nodes.new('ShaderNodeTexImage')
    tr.image = rough
    tn = nt.nodes.new('ShaderNodeTexImage')
    tn.image = nrm
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(tc.outputs[0], b.inputs['Base Color'])
    nt.links.new(tr.outputs[0], b.inputs['Roughness'])
    nt.links.new(tn.outputs[0], nm.inputs['Color'])
    nt.links.new(nm.outputs[0], b.inputs['Normal'])
    MATS['Skin_' + nmap] = m
    return m


# ------------------------------------------------------------------ step snapshots

def snapshot(name, objs, wire=True, target=(0, 0, 4.2), dist=27):
    """a viewport-style shot of the build so far from the front three-quarter and the back: the model with its
    materials, and (wire=True) its wireframe drawn over it"""
    sc, cam, cam_d = A.studio()
    sc.cycles.samples = 20
    extra = []
    if wire:
        black = bpy.data.materials.get('WireLine') or bpy.data.materials.new('WireLine')
        black.use_nodes = True
        nt = black.node_tree
        nt.nodes.clear()
        o = nt.nodes.new('ShaderNodeOutputMaterial')
        e = nt.nodes.new('ShaderNodeEmission')
        e.inputs[0].default_value = (0.02, 0.02, 0.02, 1)
        nt.links.new(e.outputs[0], o.inputs[0])
        for ob in objs:
            w = ob.copy()
            w.data = ob.data.copy()
            bpy.context.scene.collection.objects.link(w)
            md = w.modifiers.new('w', 'WIREFRAME')
            md.thickness = 0.008
            md.use_replace = True
            w.data.materials.clear()
            w.data.materials.append(black)
            extra.append(w)
    os.makedirs(STEPS, exist_ok=True)
    shots = []
    for i, az in enumerate((-25, 155)):
        a = math.radians(az - 90)
        cam_d.lens = 60
        cam.location = (dist * math.cos(a), dist * math.sin(a), target[2] + 2.0)
        cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.resolution_x, sc.render.resolution_y = 700, 860
        f = os.path.join(STEPS, f'_{i}.png')
        sc.render.filepath = f
        bpy.ops.render.render(write_still=True)
        shots.append(f)
    ims = [bpy.data.images.load(f) for f in shots]
    W, H = ims[0].size
    strip = np.zeros((H, W * 2, 4), dtype=np.float32)
    for k, im in enumerate(ims):
        strip[:, k * W:(k + 1) * W] = np.array(im.pixels[:], dtype=np.float32).reshape(H, W, 4)
    out = bpy.data.images.new(name, W * 2, H, alpha=False)
    out.pixels = strip.ravel()
    out.filepath_raw = os.path.join(STEPS, name + '.png')
    out.file_format = 'PNG'
    out.save()
    for f in shots:
        os.remove(f)
    for w in extra:
        bpy.data.objects.remove(w)
    print('STEP', out.filepath_raw, flush=True)


def main():
    A.reset()
    body = import_body()
    for part, (o, nmap) in body.items():
        o.data.materials.clear()
        o.data.materials.append(skin_material(nmap))
        print(part, 'tris', sum(len(p.vertices) - 2 for p in o.data.polygons), [round(x, 2) for x in o.dimensions])
    if STAGE == 'body':
        snapshot('step_01_body', [o for o, _ in body.values()], wire=False)
        return


if __name__ == '__main__':
    main()
