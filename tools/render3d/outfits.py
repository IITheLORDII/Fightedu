"""Kıyafet ve ekipman: gövdeden türetilen giysi kabukları, metaball eldivenler.

Giysi bölgeleri her köşenin baskın kemiği ve o kemik boyunca konumuyla (t: 0 = baş, 1 = uç)
seçilir; örn. şort = pelvis + bel + uyluğun üst %55'i. Giysi, gövdenin dışına normaller boyunca
itilir, yumuşatılır ve gövdenin deri ağırlıklarını (yumuşatılmış) kullanır.
"""
import math

import bpy
import numpy as np
from mathutils import Matrix, Vector

from character import mesh_from
from shading import NB, set_texspace, srgb


def unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def side_free(name):
    return name[:-2] if name.endswith(("_l", "_r")) else name


class BodyMap:
    def __init__(self, ch):
        self.ch = ch
        bv = ch.bv
        n = len(bv)
        me = ch.body.data
        self.normals = np.array([v.normal[:] for v in me.vertices])
        bones = [b for b in ch.rig.weights if ch.rig.weights[b]]
        local = {int(o): i for i, o in enumerate(ch.body_used)}
        W = np.zeros((n, len(bones)))
        for j, b in enumerate(bones):
            for vi, w in ch.rig.weights[b]:
                if vi in local:
                    W[local[vi], j] = w
        self.bones = bones
        self.W = W
        dom = W.argmax(axis=1)
        self.dom = np.array([bones[k] for k in dom])
        self.dom_base = np.array([side_free(b) for b in self.dom])
        t = np.zeros(n)
        for b in bones:
            m = self.dom == b
            if not m.any():
                continue
            h = np.asarray(ch.rig.bones[b]["head"])
            tl = np.asarray(ch.rig.bones[b]["tail"])
            ax = tl - h
            t[m] = ((bv[m] - h) @ ax) / max(ax @ ax, 1e-9)
        self.t = t
        # komşuluk (kenarlar)
        nb = [set() for _ in range(n)]
        for f in ch.bf:
            for a, b in zip(f, f[1:] + f[:1]):
                nb[a].add(b)
                nb[b].add(a)
        self.nb = [np.array(sorted(x), dtype=np.int64) for x in nb]

    def face_info(self):
        if hasattr(self, "fdom"):
            return
        ch = self.ch
        fdom, ft = [], []
        for f in ch.bf:
            w = self.W[f].sum(axis=0)
            b = self.bones[int(w.argmax())]
            c = ch.bv[f].mean(axis=0)
            h = np.asarray(ch.rig.bones[b]["head"])
            ax = np.asarray(ch.rig.bones[b]["tail"]) - h
            fdom.append(side_free(b))
            ft.append(float(((c - h) @ ax) / max(ax @ ax, 1e-9)))
        self.fdom = np.array(fdom)
        self.ft = np.array(ft)

    def select_faces(self, rules):
        self.face_info()
        m = np.zeros(len(self.fdom), dtype=bool)
        for base, (t0, t1) in rules.items():
            m |= (self.fdom == base) & (self.ft >= t0) & (self.ft <= t1)
        return [int(k) for k in np.nonzero(m)[0]]

    def select(self, rules):
        """rules: {kemik_adı (taraf eki olmadan): (t0, t1)} -> köşe maskesi."""
        m = np.zeros(len(self.t), dtype=bool)
        for base, (t0, t1) in rules.items():
            m |= (self.dom_base == base) & (self.t >= t0) & (self.t <= t1)
        return m


def surface_bind(ob, target):
    """Surface Deform: nesneyi hedefin (iskeletle deforme olan vekil gövde) yüzeyine bağlar."""
    mod = ob.modifiers.new("SurfaceDeform", "SURFACE_DEFORM")
    mod.target = target
    mod.falloff = 14.0  # yalnızca en yakın yüzeyler etkilesin (kol yüzeyleri gövde giysisini çekmesin)
    bpy.context.view_layer.update()
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob]):
        bpy.ops.object.surfacedeform_bind(modifier=mod.name)
    if not mod.is_bound:
        raise RuntimeError(f"{ob.name}: Surface Deform bağlanamadı")
    return mod


def bm_parent_child(bn):
    """Sınırdaki köşe komşu kemiğe ait olabilir (örn. uyluk ağzında pelvis değil, diz)."""
    return {"thigh_l": "calf_l", "thigh_r": "calf_r", "calf_l": "thigh_l", "calf_r": "thigh_r",
            "upperarm_l": "lowerarm_l", "upperarm_r": "lowerarm_r", "lowerarm_l": "upperarm_l",
            "lowerarm_r": "upperarm_r"}.get(bn, bn)


def _smooth(values, idx_nb, iters, keep=None):
    v = values.copy()
    for _ in range(iters):
        avg = np.array([v[nb].mean(axis=0) if len(nb) else v[i] for i, nb in enumerate(idx_nb)])
        if keep is not None:
            avg[keep] = v[keep]
        v = 0.5 * v + 0.5 * avg
    return v


def garment(ch, bm, name, rules, offset, materials, thickness=0.003, smooth_iters=4,
            snap=None, subsurf=1, texspace=None, relax=None, keep_face=None, hem_z=None, edge_smooth=8):
    """offset(dom_base, t, rest_pos) -> metre; materials: [(malzeme, yüz_seçici(merkez, kemik, t))...]
    snap: {kemik: t} – bu kemikteki sınır köşeleri tam t düzlemine taşınır (düz paça/kol ağzı)."""
    fids = bm.select_faces(rules)
    if keep_face is not None:
        fids = [k for k in fids if keep_face(ch.bv[ch.bf[k]].mean(axis=0), bm.fdom[k], bm.ft[k])]
    used = sorted({v for k in fids for v in ch.bf[k]})
    remap = {o: i for i, o in enumerate(used)}
    faces = [[remap[v] for v in ch.bf[k]] for k in fids]
    used = np.array(used)
    rest = ch.bv[used].copy()
    nb = [np.array([remap[x] for x in bm.nb[o] if x in remap], dtype=np.int64) for o in used]
    # sınır köşeleri
    edge_count = {}
    for f in faces:
        for a, b in zip(f, f[1:] + f[:1]):
            key = (min(a, b), max(a, b))
            edge_count[key] = edge_count.get(key, 0) + 1
    boundary = np.zeros(len(used), dtype=bool)
    for (a, b), c in edge_count.items():
        if c == 1:
            boundary[a] = boundary[b] = True
    if snap:
        for bone_base, tt in snap.items():
            for side in ("_l", "_r"):
                bn = bone_base + side
                if bn not in ch.rig.bones:
                    continue
                h = np.asarray(ch.rig.bones[bn]["head"])
                ax = np.asarray(ch.rig.bones[bn]["tail"]) - h
                cur_all = ((rest - h) @ ax) / (ax @ ax)
                m = boundary & np.isin(bm.dom[used], [bn, bm_parent_child(bn)]) & (np.abs(cur_all - tt) < 0.15)
                if m.any():
                    rest[m] += np.outer(tt - cur_all[m], ax)
    # kenar çizgisini yumuşat: yüz basamaklarından oluşan testere dişi kenarlar düzgün bir eğriye dönsün
    bnb = {}
    for (a, b), cnt in edge_count.items():
        if cnt == 1:
            bnb.setdefault(a, []).append(b)
            bnb.setdefault(b, []).append(a)
    for _ in range(edge_smooth):
        new = rest.copy()
        for v, nbs in bnb.items():
            if len(nbs) == 2:
                new[v] = 0.5 * rest[v] + 0.25 * (rest[nbs[0]] + rest[nbs[1]])
        rest = new
    if hem_z is not None:
        # yatay etek: alttaki sınır köşelerini aynı yüksekliğe getir (testere dişi kenar olmasın)
        m = boundary & (rest[:, 2] < hem_z + 0.03)
        rest[m, 2] = hem_z
    off = np.array([offset(bm.dom_base[o], bm.t[o], ch.bv[o]) for o in used])
    disp = bm.normals[used] * off[:, None]
    disp = _smooth(disp, nb, smooth_iters)
    pos = rest + disp
    if relax:
        # ayak parmakları gibi ayrıntıları yumuşat (Taubin: büzülmeden)
        bones_r, iters = relax
        movable = np.isin(bm.dom_base[used], bones_r) & ~boundary
        for _ in range(iters):
            for lam in (0.5, -0.53):
                avg = np.array([pos[n_].mean(axis=0) if len(n_) else pos[i] for i, n_ in enumerate(nb)])
                pos[movable] += lam * (avg[movable] - pos[movable])
    uvf = [ch.buvf[k] for k in fids]
    ob = mesh_from(f"{ch.name}_{name}", pos, faces, uvf, ch.base.uvs)
    # gövdenin deforme olmuş yüzeyine bağla: kalça/omuz büküldüğünde giysi deriyle birlikte hareket eder
    ob.parent = ch.arm_ob
    surface_bind(ob, ch.proxy())
    if thickness:
        sol = ob.modifiers.new("Solid", "SOLIDIFY")
        sol.thickness = thickness
        sol.offset = -1.0
        # eşit kalınlık keskin köşelerde uzun sivri çıkıntılar üretiyor; kalınlığı kenar boyuyla sınırla
        sol.use_even_offset = False
        sol.thickness_clamp = 1.0
    sub = ob.modifiers.new("Subsurf", "SUBSURF")
    sub.levels = 0
    sub.render_levels = subsurf
    # malzemeler
    if texspace is None:
        lo, hi = pos.min(axis=0), pos.max(axis=0)
        texspace = ((lo + hi) / 2, (hi - lo) / 2 + 1e-3)
    set_texspace(ob, texspace[0], texspace[1])
    for mat, _sel in materials:
        ob.data.materials.append(mat)
    if len(materials) > 1:
        for poly, k in zip(ob.data.polygons, fids):
            vs = ch.bf[k]
            c = ch.bv[vs].mean(axis=0)
            dom = bm.dom_base[vs[0]]
            tt = float(np.mean(bm.t[vs]))
            for mi, (_m, chooser) in enumerate(materials):
                if chooser is None or chooser(c, dom, tt):
                    poly.material_index = mi
    ob.data.update()
    return ob


# --------------------------------------------------------------------------------
# Malzemeler
# --------------------------------------------------------------------------------
def fabric(name, color, roughness=0.75, sheen=0.5, weave=60.0, stripes=None, center=None, half=None):
    """Kumaş; stripes: [(renk, maske_kurucu(nb, pos))] – rest koordinatlı şerit/desen."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    b = NB(nt)
    base = srgb(color) if isinstance(color, str) else color
    col = base
    if stripes:
        pos = b.rest_position(center, half)
        for scol, builder in stripes:
            m = builder(b, pos)
            col = b.mix(m, col, srgb(scol))
    b.set(bsdf.inputs["Base Color"], col)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Sheen Weight"].default_value = sheen
    bsdf.inputs["Specular IOR Level"].default_value = 0.3
    tex = b.node("ShaderNodeTexNoise", Scale=weave, Detail=2.0)
    bump = b.node("ShaderNodeBump", Strength=0.08)
    b.l.new(tex.outputs["Fac"], bump.inputs["Height"])
    b.l.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def satin(name, color, stripes=None, center=None, half=None):
    """Parlak boks şortu kumaşı."""
    mat = fabric(name, color, roughness=0.42, sheen=0.3, weave=200.0, stripes=stripes, center=center, half=half)
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Specular IOR Level"].default_value = 0.4
    bsdf.inputs["Anisotropic"].default_value = 0.3
    return mat


def leather(name, color, roughness=0.3, coat=0.6):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    b = NB(nt)
    bsdf.inputs["Base Color"].default_value = srgb(color)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Coat Weight"].default_value = coat
    bsdf.inputs["Coat Roughness"].default_value = 0.18
    bsdf.inputs["Specular IOR Level"].default_value = 0.5
    tex = b.node("ShaderNodeTexNoise", Scale=180.0, Detail=3.0)
    bump = b.node("ShaderNodeBump", Strength=0.05)
    b.l.new(tex.outputs["Fac"], bump.inputs["Height"])
    b.l.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


# --------------------------------------------------------------------------------
# Maske kurucular (rest koordinatı)
# --------------------------------------------------------------------------------
def leg_side_stripe(ch, width=0.016):
    """Uyluğun dış yanında dikey şerit (iki bacak)."""
    def build(b, pos):
        out = None
        for s, sx in (("l", 1.0), ("r", -1.0)):
            h = np.asarray(ch.rig.bones[f"thigh_{s}"]["head"])
            ax = unit(np.asarray(ch.rig.bones[f"thigh_{s}"]["tail"]) - h)
            rel = b.vmath("SUBTRACT", pos, tuple(h))
            along = b.vmath("DOT_PRODUCT", rel, tuple(ax))
            radial = b.vmath("SUBTRACT", rel, b.vec_scale(tuple(ax), along))
            fwd = b.vmath("DOT_PRODUCT", radial, (0.0, -1.0, 0.0))
            lat = b.vmath("DOT_PRODUCT", radial, (sx, 0.0, 0.0))
            band = b.smooth(b.math("ABSOLUTE", fwd), width * 0.5 - 0.002, width * 0.5 + 0.002, invert=True)
            m = b.math("MULTIPLY", band, b.smooth(lat, 0.0, 0.02))
            out = m if out is None else b.math("MAXIMUM", out, m)
        return out
    return build


def z_band(z0, z1, soft=0.003):
    def build(b, pos):
        z = b.vmath("DOT_PRODUCT", pos, (0.0, 0.0, 1.0))
        return b.math("MULTIPLY", b.smooth(z, z0 - soft, z0 + soft), b.smooth(z, z1 - soft, z1 + soft, invert=True))
    return build


# --------------------------------------------------------------------------------
# Eldiven (metaball -> mesh), el kemiğine bağlı
# --------------------------------------------------------------------------------
def _metaball_mesh(name, build):
    mb = bpy.data.metaballs.new(name + "_mb")
    mb.resolution = 0.004
    mb.render_resolution = 0.004
    mb.threshold = 0.6

    def elem(kind, center, axes, rot, radius=None, stiff=2.0):
        """ELLIPSOID: axes = görünen yarı eksenler (m); CAPSULE: axes[0] yarı uzunluk, radius yarıçap.
        Blender alanı f = s(1 - d²/R²)³ olduğundan yüzey R·sqrt(1 - (eşik/s)^(1/3)) uzaklıktadır."""
        k = math.sqrt(1.0 - (mb.threshold / stiff) ** (1.0 / 3.0))
        e = mb.elements.new(type=kind)
        e.co = Vector([float(x) for x in center])
        e.rotation = rot
        e.stiffness = stiff
        if kind == "ELLIPSOID":
            r = max(axes)
            e.radius = r / k
            e.size_x, e.size_y, e.size_z = axes[0] / r, axes[1] / r, axes[2] / r
        else:
            e.radius = radius / k
            e.size_x = axes[0]
        return e

    build(elem)
    ob_mb = bpy.data.objects.new(name + "_mbo", mb)
    bpy.context.scene.collection.objects.link(ob_mb)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob_mb.evaluated_get(dg))
    bpy.data.objects.remove(ob_mb)
    me.name = name
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = True
    return ob


def rot_of(x, y):
    """Yerel X -> x, Y -> y (dik) olan dönüş (quaternion)."""
    x = unit(x)
    y = unit(y - x * (y @ x))
    return Matrix(np.stack([x, y, np.cross(x, y)], axis=1).tolist()).to_quaternion()


def glove(ch, side, color="#C8102E", cuff="#141414", trim="#EDEDED", size=1.0):
    bones = ch.rig.bones
    W = np.asarray(bones[f"hand_{side}"]["head"])
    d = unit(W - np.asarray(bones[f"lowerarm_{side}"]["head"]))
    idx = np.asarray(bones[f"index_01_{side}"]["head"])
    pk = np.asarray(bones[f"pinky_01_{side}"]["head"])
    th = np.asarray(bones[f"thumb_02_{side}"]["head"])
    lat = unit(idx - pk)
    lat = unit(lat - d * (lat @ d))
    pn = np.cross(d, lat)
    if pn @ (th - W) < 0:
        pn = -pn
    k = ch.size * size
    rot = rot_of(d, lat)

    def build(elem):
        elem("ELLIPSOID", W + d * 0.058 * k - pn * 0.006 * k, (0.068 * k, 0.052 * k, 0.046 * k), rot)
        elem("ELLIPSOID", W + d * 0.092 * k - pn * 0.004 * k, (0.046 * k, 0.054 * k, 0.047 * k), rot, stiff=2.0)
        tdir = unit(d * 0.9 + pn * 0.2)
        elem("ELLIPSOID", W + d * 0.052 * k + lat * 0.044 * k + pn * 0.026 * k, (0.040 * k, 0.018 * k, 0.020 * k),
             rot_of(tdir, lat), stiff=2.0)
        elem("CAPSULE", W - d * 0.045 * k, (0.032 * k, 0, 0), rot, radius=0.040 * k)

    ob = _metaball_mesh(f"{ch.name}_glove_{side}", build)
    me = ob.data
    me.materials.append(leather(f"{ch.name}_glove_{side}_mat", color))
    me.materials.append(leather(f"{ch.name}_cuff_{side}_mat", cuff, roughness=0.45, coat=0.3))
    me.materials.append(leather(f"{ch.name}_trim_{side}_mat", trim, roughness=0.5, coat=0.1))
    for p in me.polygons:
        a = (np.array(p.center[:]) - W) @ d
        if a < -0.004 * k:
            p.material_index = 1
        if -0.011 * k < a < -0.004 * k:
            p.material_index = 2
    _bone_parent(ob, ch.arm_ob, f"hand_{side}")
    return ob


def hide_hands(ch, bm):
    """Eldivenin içinde kalan el köşelerini gizle (iç içe geçme görünmesin)."""
    hand = np.isin(bm.dom_base, ["hand", "index_01", "index_02", "index_03", "middle_01", "middle_02",
                                 "middle_03", "ring_01", "ring_02", "ring_03", "pinky_01", "pinky_02",
                                 "pinky_03", "thumb_01", "thumb_02", "thumb_03"])
    hand |= (bm.dom_base == "lowerarm") & (bm.t > 0.8)
    g = ch.body.vertex_groups.new(name="hidden")
    g.add([int(i) for i in np.nonzero(hand)[0]], 1.0, "REPLACE")
    m = ch.body.modifiers.new("HideHands", "MASK")
    m.vertex_group = "hidden"
    m.invert_vertex_group = True
    ch.body.modifiers.move(ch.body.modifiers.find("HideHands"), 1)


def shoe(ch, bm, side, top_t, color, sole_color="#EDEDED", lace_color="#F0F0F0", pad=0.0065, sole_h=0.013,
         name="boot"):
    """Ayağın dilimlerine oturan metaball ayakkabı/bot; top_t: baldır boyunca konç yüksekliği."""
    bones = ch.rig.bones
    A = np.asarray(bones[f"foot_{side}"]["head"])
    Bl = np.asarray(bones[f"ball_{side}"]["head"])
    fwd = Bl - A
    fwd[2] = 0.0
    fwd = unit(fwd)
    up = np.array([0.0, 0.0, 1.0])
    lat = np.cross(fwd, up)
    sel = np.isin(bm.dom_base, ["foot", "ball"]) & (bm.dom == f"foot_{side}") | (bm.dom == f"ball_{side}")
    P = ch.bv[sel]
    u = (P - A) @ fwd
    w = (P - A) @ lat
    rot = rot_of(fwd, lat)
    ku = np.linspace(u.min(), u.max(), 9)

    def build(elem):
        for u0, u1 in zip(ku, ku[1:]):
            m = (u >= u0) & (u <= u1)
            if m.sum() < 4:
                continue
            Q = P[m]
            ww = w[m]
            zc = (Q[:, 2].max() + max(Q[:, 2].min(), 0.0)) / 2
            hz = (Q[:, 2].max() - max(Q[:, 2].min(), 0.0)) / 2 + pad
            wc = (ww.max() + ww.min()) / 2
            hw = (ww.max() - ww.min()) / 2 + pad
            c = A + fwd * ((u0 + u1) / 2) + lat * wc
            c[2] = zc
            elem("ELLIPSOID", c, ((u1 - u0) * 0.75 + pad, hw, hz), rot, stiff=1.5)
        # konç: baldır dilimleri
        cn = f"calf_{side}"
        h = np.asarray(bones[cn]["head"])
        ax = np.asarray(bones[cn]["tail"]) - h
        tt = ((ch.bv - h) @ ax) / (ax @ ax)
        calf = (bm.dom == cn) | (bm.dom == f"foot_{side}")
        for t0 in np.linspace(0.84, top_t, 4) if top_t < 0.84 else []:
            m = calf & (np.abs(tt - t0) < 0.03)
            if m.sum() < 4:
                continue
            Q = ch.bv[m]
            c = Q.mean(axis=0)
            rad = np.percentile(np.linalg.norm((Q - c) - np.outer((Q - c) @ unit(ax), unit(ax)), axis=1), 90)
            elem("ELLIPSOID", c, (rad + pad, rad + pad, 0.035), rot_of(lat, fwd), stiff=1.6)
        top = A + up * 0.04
        elem("ELLIPSOID", top + fwd * 0.005, (0.045, 0.040, 0.045), rot, stiff=1.6)

    ob = _metaball_mesh(f"{ch.name}_{name}_{side}", build)
    me = ob.data

    # tabanı düzle, konç ağzını düz kes
    cn = f"calf_{side}"
    h = np.asarray(bones[cn]["head"])
    axv = np.asarray(bones[cn]["tail"]) - h
    for v in me.vertices:
        co = np.array(v.co[:])
        if co[2] < 0.0015:
            co[2] = 0.0015
        t = ((co - h) @ axv) / (axv @ axv)
        if t < top_t:
            co = co + axv * (top_t - t)
        v.co = co

    me.materials.append(leather(f"{ch.name}_{name}_{side}_mat", color, roughness=0.38, coat=0.35))
    me.materials.append(leather(f"{ch.name}_{name}_sole_{side}", sole_color, roughness=0.7, coat=0.0))
    me.materials.append(fabric(f"{ch.name}_{name}_lace_{side}", lace_color, roughness=0.8))
    for p in me.polygons:
        c = np.array(p.center[:])
        if c[2] < sole_h * ch.size:
            p.material_index = 1
        else:
            rel = c - A
            if abs(rel @ lat - 0.0) < 0.011 and (rel @ fwd) > 0.0 and (rel @ fwd) < 0.10 and c[2] > 0.04:
                # bağcık şeridi: üstte ve önde
                p.material_index = 2 if int(c[2] * 260) % 2 == 0 else 0
    ob.parent = ch.arm_ob
    surface_bind(ob, ch.proxy())
    return ob


def _bone_parent(ob, arm_ob, bone):
    bpy.context.view_layer.update()
    mw = ob.matrix_world.copy()
    ob.parent = arm_ob
    ob.parent_type = "BONE"
    ob.parent_bone = bone
    ob.matrix_world = mw


# --------------------------------------------------------------------------------
# Hazır kıyafetler
# --------------------------------------------------------------------------------
def _bone_pt(ch, bone, end="head"):
    return np.asarray(ch.rig.bones[bone][end])


def shorts(ch, bm, name, color, trim, length=0.55, flare=0.030, waist=0.010, band=0.07, stripe=True,
           shiny=True):
    def off(base, t, p):
        if base in ("pelvis", "spine_01"):
            return waist
        if base == "thigh":
            return waist + 0.006 + flare * min(1.0, max(0.0, t / length))
        return waist

    rules = {"pelvis": (-9, 9), "spine_01": (-9, 0.55), "thigh": (-9, length)}
    sel = bm.select(rules)
    zt = ch.bv[sel, 2].max()
    lo, hi = ch.bv[sel].min(axis=0), ch.bv[sel].max(axis=0)
    center, half = (lo + hi) / 2, (hi - lo) / 2 + 0.05
    stripes = [(trim, leg_side_stripe(ch))] if stripe else None
    maker = satin if shiny else fabric
    body_mat = maker(f"{ch.name}_{name}", color, stripes=stripes, center=center, half=half)
    band_mat = fabric(f"{ch.name}_{name}_band", trim, roughness=0.6, sheen=0.3)
    return garment(ch, bm, name, rules, off,
                   [(body_mat, None), (band_mat, lambda c, dom, t: c[2] > zt - band * ch.size)],
                   thickness=0.004, smooth_iters=6, snap={"thigh": length}, texspace=(center, half))


def boxing_kit(ch, bm, shorts_color="#1F4FC8", trim="#F4F4F4", gloves="#C8102E", boots="#111111",
               socks="#F2F2F2", **_kw):
    items = [shorts(ch, bm, "shorts", shorts_color, trim)]
    sock = fabric(f"{ch.name}_sock", socks, roughness=0.9, sheen=0.6, weave=300.0)
    items.append(garment(ch, bm, "socks", {"calf": (0.66, 0.92)},
                         lambda b, t, p: 0.003, [(sock, None)], thickness=0.002, smooth_iters=2,
                         snap={"calf": 0.66}))
    for sd in ("l", "r"):
        items.append(shoe(ch, bm, sd, 0.76, boots, sole_color="#1C1C1C", lace_color="#E8E8E8"))
    hide_hands(ch, bm)
    for sd in ("l", "r"):
        items.append(glove(ch, sd, gloves))
    return items


def kickboxing_kit(ch, bm, shorts_color="#151515", trim="#D9A21B", gloves="#1F4FC8", ankle="#151515", **_kw):
    items = [shorts(ch, bm, "shorts", shorts_color, trim, length=0.40, flare=0.05, band=0.085, stripe=False)]
    sup = fabric(f"{ch.name}_ankle", ankle, roughness=0.85, sheen=0.4, weave=260.0)
    items.append(garment(ch, bm, "ankle", {"calf": (0.84, 9), "foot": (-9, 0.55)},
                         lambda b, t, p: 0.003, [(sup, None)], thickness=0.002, smooth_iters=2,
                         snap={"calf": 0.84}))
    hide_hands(ch, bm)
    for sd in ("l", "r"):
        items.append(glove(ch, sd, gloves))
    return items


def wrestling_kit(ch, bm, singlet="#1F3FA8", trim="#F2F2F2", shoes="#1A1A1A", **_kw):
    k = ch.size
    sh = _bone_pt(ch, "upperarm_l")
    neck = _bone_pt(ch, "neck_01")
    nip_z = ch.regions["nipples"][0][0][2]
    chest_y = _bone_pt(ch, "spine_03")[1]

    def keep(c, dom, t):
        front = c[1] < chest_y
        if c[2] > nip_z - 0.08 * k:
            # kol oyukları: koltuk altından omuz başına kadar açık
            if abs(c[0]) > sh[0] * 0.66:
                return False
            # ön yaka köprücük kemiklerinin altında, arkada kürek kemikleri arasında; askılar omuz üstünden
            if front and c[2] > nip_z + 0.12 * k and abs(c[0]) < 0.065 * k:
                return False
            if not front and c[2] > sh[2] - 0.03 * k and abs(c[0]) < 0.065 * k:
                return False
            if c[2] > neck[2] - 0.02 * k:
                return False
        return True

    # göğüs kası köşeleri kol kemiğine ağırlıklı olabildiği için kolun omuz tarafı da aday
    rules = {"pelvis": (-9, 9), "spine_01": (-9, 9), "spine_02": (-9, 9), "spine_03": (-9, 9),
             "clavicle": (-9, 9), "neck_01": (-9, 0.0), "upperarm": (-9, 0.05), "thigh": (-9, 0.32)}
    sel = bm.select(rules)
    lo, hi = ch.bv[sel].min(axis=0), ch.bv[sel].max(axis=0)
    center, half = (lo + hi) / 2, (hi - lo) / 2 + 0.05
    mat = fabric(f"{ch.name}_singlet", singlet, roughness=0.42, sheen=0.25, weave=320.0,
                 stripes=[(trim, leg_side_stripe(ch, 0.012))], center=center, half=half)
    items = [garment(ch, bm, "singlet", rules, lambda b, t, p: 0.004, [(mat, None)], thickness=0.0015,
                     smooth_iters=3, snap={"thigh": 0.32}, texspace=(center, half), keep_face=keep)]
    for sd in ("l", "r"):
        items.append(shoe(ch, bm, sd, 0.62, shoes, sole_color="#EDEDED", lace_color=shoes, pad=0.0035,
                          name="shoe"))
    return items


def taekwondo_kit(ch, bm, belt="#111111", hogu=None, **_kw):
    k = ch.size
    neck = _bone_pt(ch, "neck_01")
    chest_y = _bone_pt(ch, "spine_03")[1]
    hip_z = _bone_pt(ch, "thigh_l")[2]
    nip_z = ch.regions["nipples"][0][0][2]

    def keep_jacket(c, dom, t):
        # kapalı V yaka: göğüs kemiğinin ortasında birleşir, boyuna doğru açılır
        if c[1] < chest_y and dom in ("spine_03", "clavicle", "spine_02", "neck_01"):
            zr = (c[2] - (nip_z + 0.01 * k)) / max(neck[2] - nip_z, 1e-3)
            if zr > 0 and abs(c[0]) < 0.006 * k + 0.055 * k * min(1.0, zr):
                return False
        return c[2] < neck[2] - 0.01 * k

    def jacket_off(base, t, p):
        if base in ("upperarm",):
            return 0.012 + 0.008 * t
        if base == "lowerarm":
            return 0.020 + 0.014 * t
        if base in ("pelvis", "thigh"):
            return 0.030
        if base in ("clavicle", "spine_03"):
            return 0.011
        return 0.018

    white = fabric(f"{ch.name}_dobok", "#F3F3F1", roughness=0.85, sheen=0.7, weave=180.0)
    items = [garment(ch, bm, "jacket",
                     {"spine_01": (-9, 9), "spine_02": (-9, 9), "spine_03": (-9, 9), "clavicle": (-9, 9),
                      "neck_01": (-9, 0.1), "upperarm": (-9, 9), "lowerarm": (-9, 0.88), "pelvis": (-9, 9),
                      "thigh": (-9, 0.14)},
                     jacket_off, [(white, None)], thickness=0.004, smooth_iters=8,
                     snap={"lowerarm": 0.88, "thigh": 0.14}, keep_face=keep_jacket)]
    items.append(garment(ch, bm, "pants", {"pelvis": (-9, 9), "thigh": (-9, 9), "calf": (-9, 0.9)},
                         lambda b, t, p: 0.020 if b == "pelvis" else (0.022 + 0.012 * min(1, t) if b == "thigh"
                                                                      else 0.030 + 0.012 * t),
                         [(white, None)], thickness=0.004, smooth_iters=8,
                         snap={"calf": 0.9},
                         keep_face=lambda c, dom, t: dom != "pelvis" or c[2] < hip_z + 0.02 * k))
    # kuşak: bel hizasında bant
    zb = hip_z + 0.085 * k
    belt_mat = fabric(f"{ch.name}_belt", belt, roughness=0.7, sheen=0.3, weave=240.0)
    items.append(garment(ch, bm, "belt", {"spine_01": (-9, 9), "pelvis": (-9, 9)},
                         lambda b, t, p: 0.038, [(belt_mat, None)], thickness=0.006, smooth_iters=6, keep_face=lambda c, dom, t: abs(c[2] - zb) < 0.022 * k))
    # düğüm ve sarkan uçlar (pelvise bağlı)
    # yalnızca gövde (kollar A duruşunda bu yükseklikte öne uzanıyor)
    torso = (np.abs(ch.bv[:, 2] - zb) < 0.01) & (np.abs(ch.bv[:, 0]) < 0.08 * k)
    front = ch.bv[torso][:, 1].min()

    def knot(elem):
        c = np.array([0.0, front - 0.04 * k, zb])
        elem("ELLIPSOID", c, (0.028 * k, 0.018 * k, 0.022 * k), rot_of(np.array([1.0, 0, 0]),
                                                                     np.array([0, 1.0, 0])))

    kn = _metaball_mesh(f"{ch.name}_belt_knot", knot)
    kn.data.materials.append(belt_mat)
    _bone_parent(kn, ch.arm_ob, "pelvis")
    items.append(kn)
    if hogu:
        red = fabric(f"{ch.name}_hogu", hogu, roughness=0.45, sheen=0.1, weave=90.0)
        items.append(garment(ch, bm, "hogu", {"spine_02": (-9, 9), "spine_03": (-9, 9), "spine_01": (0.4, 9)},
                             lambda b, t, p: 0.055, [(red, None)], thickness=0.01, smooth_iters=10,
                             keep_face=lambda c, dom, t: c[2] < nip_z + 0.11 * k and c[2] > zb + 0.03 * k))
    return items


def general_kit(ch, bm, shirt="#7B8794", shorts_color="#1E1E1E", shoes="#F4F4F4", **_kw):
    k = ch.size
    neck = _bone_pt(ch, "neck_01")
    chest_y = _bone_pt(ch, "spine_03")[1]
    hip_z = _bone_pt(ch, "thigh_l")[2]

    hem = hip_z + 0.035 * k

    def keep(c, dom, t):
        # yuvarlak yaka: boyun dibini sarar, önde biraz aşağı iner
        if c[2] > neck[2] - 0.012 * k:
            return False
        if c[1] < chest_y and abs(c[0]) < 0.075 * k and c[2] > neck[2] - 0.055 * k:
            return False
        return dom != "pelvis" or c[2] > hem

    tee = fabric(f"{ch.name}_tee", shirt, roughness=0.9, sheen=0.5, weave=220.0)
    items = [garment(ch, bm, "tee",
                     {"spine_01": (-9, 9), "spine_02": (-9, 9), "spine_03": (-9, 9), "clavicle": (-9, 9),
                      "neck_01": (-9, 0.2), "upperarm": (-9, 0.42), "pelvis": (-9, 9)},
                     lambda b, t, p: (0.005 if b in ("clavicle", "spine_03", "neck_01") else
                                      (0.009 + 0.008 * t if b == "upperarm" else
                                       (0.017 if b == "pelvis" else 0.011))), [(tee, None)],
                     thickness=0.003, smooth_iters=6, snap={"upperarm": 0.42}, keep_face=keep, hem_z=hem)]
    items.append(shorts(ch, bm, "shorts", shorts_color, "#E6E6E6", length=0.45, flare=0.025, band=0.04,
                        stripe=True, shiny=False))
    sock = fabric(f"{ch.name}_sock", "#F2F2F2", roughness=0.9, sheen=0.6, weave=300.0)
    items.append(garment(ch, bm, "socks", {"calf": (0.84, 0.97)}, lambda b, t, p: 0.003, [(sock, None)],
                         thickness=0.002, smooth_iters=2, snap={"calf": 0.84}))
    for sd in ("l", "r"):
        items.append(shoe(ch, bm, sd, 0.93, shoes, sole_color="#FFFFFF", lace_color="#DADADA", pad=0.008,
                          sole_h=0.022, name="sneaker"))
    return items


KITS = {"boxing": boxing_kit, "kickboxing": kickboxing_kit, "wrestling": wrestling_kit,
        "taekwondo": taekwondo_kit, "general": general_kit}
