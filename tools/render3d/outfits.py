"""Kıyafet ve ekipman: gövdeden türetilen giysi kabukları, metaball eldivenler.

Giysi bölgeleri her köşenin baskın kemiği ve o kemik boyunca konumuyla (t: 0 = baş, 1 = uç)
seçilir; örn. şort = pelvis + bel + uyluğun üst %55'i. Giysi, gövdenin dışına normaller boyunca
itilir, yumuşatılır ve gövdenin deri ağırlıklarını (yumuşatılmış) kullanır.
"""
import heapq
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


def _detail_peaks(ch, radius=6):
    """Köşe başına çevresindeki en yüksek ince kas ayrıntısı (m): UV haritasında yerel en büyük değer
    (köşeler arasındaki tepeler de hesaba katılsın)."""
    if getattr(ch, "_peaks", None) is None:
        h = ch.anat
        m = h.copy()
        for ax in (0, 1):
            src = m.copy()
            for s in range(1, radius + 1):
                m = np.maximum(m, np.roll(src, s, axis=ax))
                m = np.maximum(m, np.roll(src, -s, axis=ax))
        size = h.shape[0]
        vi = np.concatenate([np.asarray(f) for f in ch.bf])
        uv = ch.base.uvs[np.concatenate([np.asarray(f) for f in ch.buvf])]
        xy = np.clip(np.rint(uv * size - 0.5).astype(int), 0, size - 1)
        peaks = np.full(len(ch.bv), -np.inf)
        np.maximum.at(peaks, vi, m[xy[:, 1], xy[:, 0]])
        ch._peaks = np.where(np.isfinite(peaks), peaks, 0.0)
    return ch._peaks


def _inner_mask(ch, used, faces, rest, boundary, dist):
    """Giysinin altında kalıp ağzına (sınır köşelerine) yüzey boyunca `dist`ten uzak deri köşeleri."""
    nbr = [[] for _ in range(len(used))]
    for f in faces:
        for a, b in zip(f, f[1:] + f[:1]):
            ln = float(np.linalg.norm(rest[a] - rest[b]))
            nbr[a].append((b, ln))
            nbr[b].append((a, ln))
    d = np.full(len(used), np.inf)
    heap = [(0.0, int(i)) for i in np.nonzero(boundary)[0]]
    d[boundary] = 0.0
    heapq.heapify(heap)
    while heap:
        di, i = heapq.heappop(heap)
        if di > d[i]:
            continue
        for j, ln in nbr[i]:
            if di + ln < d[j]:
                d[j] = di + ln
                heapq.heappush(heap, (d[j], j))
    mask = np.zeros(len(ch.bv), dtype=bool)
    mask[used[d >= dist]] = True
    return mask


def garment(ch, bm, name, rules, offset, materials, thickness=0.003, smooth_iters=4,
            snap=None, subsurf=1, texspace=None, relax=None, keep_face=None, hem_z=None, edge_smooth=8,
            cloth=None, shape=None, anatomy=1.0, hide_inner=None, clear=None):
    """offset(dom_base, t, rest_pos) -> metre; materials: [(malzeme, yüz_seçici(merkez, kemik, t))...]
    snap: {kemik: t} – bu kemikteki sınır köşeleri tam t düzlemine taşınır (düz paça/kol ağzı).
    cloth: kumaş simülasyonu {"pin": pin(dom_base, t, rest_pos) -> 0..1, ...ayarlar}; pin 1 olan köşeler
    gövdeye bağlı kabukta kalır (bel lastiği), küçük değerler yalnızca hafifçe şekline çekilir (sarkan paça).
    shape(pos, body_rest, komşular) -> pos: kabuğun son biçimlendirmesi (örn. ayakkabı burnu ve tabanı).
    anatomy: gövdenin kas yontusunun giysiye geçen oranı (giysi gövde UV'sini taşır; deri kumaştan taşmasın).
    hide_inner: giysi ağzına (yaka, kol, etek) bu uzaklıktan (m) daha içerideki deri gizlenir.
    clear: kabuk, ince kas ayrıntısıyla birlikte derinin en az bu kadar (m) dışında kalır."""
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
    if shape is not None:
        pos = shape(pos, ch.bv[used], nb)
    if clear is not None:
        # giysiye geçmeyen kas ayrıntısı (tepeleri) deriyi kumaştan dışarı itmesin
        n = bm.normals[used]
        need = np.maximum(_detail_peaks(ch)[used], 0.0) * (1.0 - anatomy) + clear
        gap = np.einsum("ij,ij->i", pos - ch.bv[used], n)
        pos += n * np.maximum(need - gap, 0.0)[:, None]
    if hide_inner is not None:
        hide_body(ch, _inner_mask(ch, used, faces, rest, boundary, hide_inner))
    uvf = [ch.buvf[k] for k in fids]
    ob = mesh_from(f"{ch.name}_{name}", pos, faces, uvf, ch.base.uvs)
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
    if cloth:
        g = ob.vertex_groups.new(name="pin")
        for i, o in enumerate(used):
            g.add([i], float(cloth["pin"](bm.dom_base[o], bm.t[o], ch.bv[o])), "REPLACE")
        # kıvrımlar için daha sık ağ (ağırlıklar alt bölümlemede aradeğerlenir)
        sub0 = ob.modifiers.new("Densify", "SUBSURF")
        sub0.levels = cloth.get("densify", 1)
        with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob]):
            bpy.ops.object.modifier_apply(modifier=sub0.name)
    if cloth:
        # kumaş: sabitleme hedefi olarak deforme olan vekil gövdenin yüzeyine bağla
        ob.parent = ch.arm_ob
        surface_bind(ob, ch.proxy())
        add_cloth(ob, ch, cloth)
    else:
        # dar giysi gövde köşelerinden birebir türetildi: aynı deri ağırlıklarıyla iskelete bağla.
        # (yüzeye bağlama koltuk altında gövde yüzlerini de yakalıyor, kol kalkınca kol giysiden çıkıyordu)
        ch._weights(ob, ch.body_used[used])
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
    if anatomy:
        # kas ayrıntısı derideki yoğunlukta örneklensin (kumaşlı giysiler zaten bir kez sıklaştırıldı)
        if not cloth:
            sub.render_levels = subsurf + 1
        ch.displace(ob, anatomy)
    # malzemeler
    if texspace is None:
        lo, hi = pos.min(axis=0), pos.max(axis=0)
        texspace = ((lo + hi) / 2, (hi - lo) / 2 + 1e-3)
    set_texspace(ob, texspace[0], texspace[1])
    ob.data.update()
    return ob


def add_cloth(ob, ch, opts):
    """Kumaş simülasyonu (Surface Deform'dan sonra): sabitleme grubu 'pin', gövde vekili çarpışma nesnesi."""
    col = ch.collider()
    mod = ob.modifiers.new("Cloth", "CLOTH")
    cs = mod.settings
    cs.quality = opts.get("quality", 10)
    cs.mass = opts.get("mass", 0.15)
    cs.air_damping = 1.0
    cs.tension_stiffness = cs.compression_stiffness = opts.get("stretch", 12.0)
    cs.shear_stiffness = opts.get("shear", 6.0)
    cs.bending_stiffness = opts.get("bend", 0.3)
    cs.tension_damping = cs.compression_damping = cs.shear_damping = 5.0
    cs.bending_damping = 0.5
    cs.vertex_group_mass = "pin"
    cs.pin_stiffness = opts.get("pin_stiffness", 2.0)
    cc = mod.collision_settings
    cc.collision_quality = opts.get("collision_quality", 4)
    cc.distance_min = 0.004
    cc.use_self_collision = False
    pc = mod.point_cache
    pc.frame_start = 1
    pc.frame_end = 100000
    ch.cloth.append(ob)
    return mod


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


def hide_body(ch, mask):
    """Eldiven/ayakkabı içinde kalan deri köşelerini gizle (iç içe geçme görünmesin)."""
    g = ch.body.vertex_groups.get("hidden")
    if g is None:
        g = ch.body.vertex_groups.new(name="hidden")
        m = ch.body.modifiers.new("Hide", "MASK")
        m.vertex_group = "hidden"
        m.invert_vertex_group = True
        ch.body.modifiers.move(ch.body.modifiers.find("Hide"), ch.body.modifiers.find("Corrective") + 1)
    g.add([int(i) for i in np.nonzero(mask)[0]], 1.0, "REPLACE")


def hide_hands(ch, bm):
    hand = np.isin(bm.dom_base, ["hand", "index_01", "index_02", "index_03", "middle_01", "middle_02",
                                 "middle_03", "ring_01", "ring_02", "ring_03", "pinky_01", "pinky_02",
                                 "pinky_03", "thumb_01", "thumb_02", "thumb_03"])
    hand |= (bm.dom_base == "lowerarm") & (bm.t > 0.8)
    hide_body(ch, hand)


def lace_material(name, color, lace_color, sole_color, foot, center, half, top_z, sole_h, collar=None):
    """Deri üst + bağcık paneli (çapraz bağcıklar, rest koordinatında) + taban şeridi (+ konç yakası)."""
    mat = leather(name, color, roughness=0.36, coat=0.35)
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    b = NB(nt)
    pos = b.rest_position(center, half)
    col = srgb(color)
    for A, fwd, lat in foot:
        rel = b.vmath("SUBTRACT", pos, tuple(A))
        u = b.vmath("DOT_PRODUCT", rel, tuple(fwd))
        w = b.math("ABSOLUTE", b.vmath("DOT_PRODUCT", rel, tuple(lat)))
        z = b.vmath("DOT_PRODUCT", rel, (0.0, 0.0, 1.0))
        z = b.math("ADD", z, float(A[2]))
        # panel: ayak üstü ortası, bilekten parmak kutusuna; bot konçunun önünde yukarı devam eder
        panel = b.math("MULTIPLY", b.smooth(w, 0.015, 0.019, invert=True), b.smooth(u, 0.012, 0.03))
        panel = b.math("MULTIPLY", panel, b.smooth(u, 0.12, 0.135, invert=True))
        panel = b.math("MULTIPLY", panel, b.smooth(z, 0.028, 0.04))
        panel = b.math("MULTIPLY", panel, b.smooth(z, top_z - 0.012, top_z - 0.004, invert=True))
        # çapraz bağcıklar: yol boyunca s = z - 0.45 u; her sırada iki çapraz
        s_ = b.math("SUBTRACT", z, b.math("MULTIPLY", u, 0.45))
        ph1 = b.math("FRACT", b.math("ADD", b.math("DIVIDE", s_, 0.013), b.math("DIVIDE", w, 0.03)))
        ph2 = b.math("FRACT", b.math("SUBTRACT", b.math("DIVIDE", s_, 0.013), b.math("DIVIDE", w, 0.03)))
        cross = b.math("MAXIMUM", b.smooth(b.math("ABSOLUTE", b.math("SUBTRACT", ph1, 0.5)), 0.13, 0.2, invert=True),
                       b.smooth(b.math("ABSOLUTE", b.math("SUBTRACT", ph2, 0.5)), 0.13, 0.2, invert=True))
        tongue = b.math("MULTIPLY", panel, b.smooth(w, 0.013, 0.015, invert=True))
        col = b.mix(b.math("MULTIPLY", tongue, 0.6), col, (0.02, 0.02, 0.02, 1.0))
        col = b.mix(b.math("MULTIPLY", tongue, cross), col, srgb(lace_color))
        # taban şeridi
        col = b.mix(b.smooth(z, sole_h - 0.0015, sole_h + 0.0015, invert=True), col, srgb(sole_color))
        if collar:
            col = b.mix(b.smooth(z, top_z - 0.016, top_z - 0.013), col, srgb(collar))
    b.set(bsdf.inputs["Base Color"], col)
    return mat


def shoe(ch, bm, side, top_t, color, sole_color="#EDEDED", lace_color="#F0F0F0", pad=0.0055, sole_h=0.013,
         name="boot", welt=0.0035, flare=0.004, collar=None):
    """Ayağın kendi yüzeyinden türetilen ayakkabı/bot: parmaklar yumuşatılmış burun, düz taban ve dışa
    taşan taban kenarı (welt), konç ağzı top_t'de (baldır boyunca) düz kesilir; bağcıklar gölgelendiricide."""
    bones = ch.rig.bones
    A = np.asarray(bones[f"foot_{side}"]["head"])
    Bl = np.asarray(bones[f"ball_{side}"]["head"])
    fwd = Bl - A
    fwd[2] = 0.0
    fwd = unit(fwd)
    lat = np.cross(fwd, np.array([0.0, 0.0, 1.0]))
    rules = {"foot": (-9, 9), "ball": (-9, 9), "calf": (top_t, 9)}
    sel = bm.select(rules) & np.array([d.endswith("_" + side) for d in bm.dom])
    lo, hi = ch.bv[sel].min(axis=0), ch.bv[sel].max(axis=0)
    center, half = (lo + hi) / 2, (hi - lo) / 2 + 0.05

    def off(base, t, p):
        if base == "ball":
            return pad + 0.003           # burun: parmakların üstünde biraz boşluk
        if base == "calf":
            return pad + flare * max(0.0, (1.0 - t) / max(1.0 - top_t, 1e-3) - 0.4)
        return pad

    def shape(pos, rest, nb):
        pos = pos.copy()
        # burun: ayakkabı kalıbı gibi; her kesitte parmak zarfının genişliği/yüksekliğinden süperelips,
        # parmak aralıkları ve tümsekleri kaybolur
        ub = (Bl - A) @ fwd
        ru = (rest - A) @ fwd
        fm = np.isin(bm.dom, [f"foot_{side}", f"ball_{side}"])
        F = ch.bv[fm]
        fu, fw, fz = (F - A) @ fwd, (F - A) @ lat, F[:, 2]
        us = np.linspace(ub - 0.05, fu.max(), 18)
        prof = []
        for u_ in us:
            m = np.abs(fu - u_) < 0.012
            prof.append((fw[m].min(), fw[m].max(), fz[m].max()) if m.sum() > 2 else (np.nan,) * 3)
        prof = np.array(prof)
        for k in range(3):
            good = ~np.isnan(prof[:, k])
            prof[:, k] = np.interp(us, us[good], prof[good, k])
        for _ in range(3):
            prof[1:-1] = (prof[:-2] + 2 * prof[1:-1] + prof[2:]) / 4
        tp = pad + 0.003
        b_ = np.clip((ru - (ub - 0.035)) / 0.025, 0.0, 1.0)
        b_ = b_ * b_ * (3 - 2 * b_)
        sel_ = b_ > 0
        ne = 2.6
        # uç kapak: son cap_l metrede süperelipsoid (ön yüz yuvarlak kubbe)
        cap_l = 0.035
        uc0 = fu.max() + tp - cap_l
        i0 = int(min(len(us) - 1, round(float(np.interp(uc0, us, np.arange(len(us)))))))
        cwl, cwr, czt = prof[i0, 0] - tp, prof[i0, 1] + tp, prof[i0, 2] + tp

        def last(Q):
            rel = Q - A
            u_, w_, z_ = rel @ fwd, rel @ lat, Q[:, 2]
            wl = np.interp(u_, us, prof[:, 0]) - tp
            wr = np.interp(u_, us, prof[:, 1]) + tp
            zt = np.interp(u_, us, prof[:, 2]) + tp
            wc, hw, zc, hz = (wl + wr) / 2, (wr - wl) / 2, zt / 2, zt / 2
            cap = u_ > uc0
            wc[cap], hw[cap] = (cwl + cwr) / 2, (cwr - cwl) / 2
            zc[cap], hz[cap] = czt / 2, czt / 2
            du = np.where(cap, (u_ - uc0) / cap_l, 0.0)
            dw, dz = (w_ - wc) / hw, (z_ - zc) / hz
            sc_ = np.maximum((np.abs(du) ** ne + np.abs(dw) ** ne + np.abs(dz) ** ne) ** (1.0 / ne), 1e-6)
            out = A + np.outer(np.where(cap, uc0 + du / sc_ * cap_l, u_), fwd) + np.outer(wc + dw / sc_ * hw, lat)
            out[:, 2] = zc + dz / sc_ * hz
            return out

        bw = b_[sel_][:, None]
        pos[sel_] += (last(pos[sel_]) - pos[sel_]) * bw
        # izdüşümde katlanan parmak arası yüzleri aç: yüzey üzerinde gevşet, tekrar izdüşür
        idx = np.nonzero(sel_)[0]
        for _ in range(12):
            avg = np.array([pos[nb[i]].mean(axis=0) if len(nb[i]) else pos[i] for i in idx])
            q = 0.5 * pos[idx] + 0.5 * avg
            pos[idx] = q + (last(q) - q) * bw
        # taban: ayak tabanının altı düz, zemine oturur; tabana yakın köşeler yanlara taşar (welt)
        low = pos[:, 2] < sole_h
        pos[pos[:, 2] < 0.0015, 2] = 0.0015
        rel = pos[low] - A
        w = rel @ lat
        u = rel @ fwd
        # ayak ekseninden yanlara ve uca/topuğa doğru
        push = np.outer(np.sign(w) * welt, lat)
        push += np.outer(np.sign(u - u.mean()) * welt * 0.6, fwd)
        k = np.clip((sole_h - pos[low, 2]) / sole_h, 0.0, 1.0)[:, None]
        pos[low] += push * np.minimum(1.0, 3.0 * k)
        return pos

    mat = lace_material(f"{ch.name}_{name}_{side}", color, lace_color, sole_color, [(A, fwd, lat)], center, half,
                        float(_bone_pt(ch, f"calf_{side}")[2] + (_bone_pt(ch, f"calf_{side}", "tail")[2] -
                                                                _bone_pt(ch, f"calf_{side}")[2]) * top_t),
                        sole_h, collar)
    hide_body(ch, np.isin(bm.dom, [f"foot_{side}", f"ball_{side}"]))
    ob = garment(ch, bm, f"{name}_{side}", rules, off, [(mat, None)], thickness=0.0025, smooth_iters=3,
                 snap={"calf": top_t} if top_t < 0.97 else None, texspace=(center, half),
                 relax=(["ball", "foot"], 14), keep_face=lambda c, dom, t: (c[0] > 0) == (side == "l"),
                 shape=shape, edge_smooth=10)
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


def shorts(ch, bm, name, color, trim, length=0.86, flare=0.032, waist=0.010, band=0.07, stripe=True,
           shiny=True, cloth=True):
    hip_z = _bone_pt(ch, "thigh_l")[2]

    def pin(base, t, p):
        # bel lastiği gövdeye sabit; kalçadan aşağı sabitleme azalır, paçalar serbest sallanır
        if p[2] > zt - band * ch.size:
            return 1.0
        if base in ("pelvis", "spine_01"):
            u = min(1.0, max(0.0, (p[2] - (hip_z - 0.06 * ch.size)) / (zt - band * ch.size - hip_z + 0.06 * ch.size)))
            return 0.12 + 0.88 * u * u
        if base == "thigh":
            # dize kadar uzun paça: kalçaya yakın sıkı, paçaya doğru serbest (tekmede takılıp yırtılmasın)
            return 0.25 * (1.0 - min(1.0, max(0.0, t / length))) + 0.12
        return 0.5

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
                   thickness=0.003, smooth_iters=6, snap={"thigh": length}, texspace=(center, half),
                   cloth=dict(pin=pin) if cloth else None)


def boxing_kit(ch, bm, shorts_color="#1F4FC8", trim="#F4F4F4", gloves="#C8102E", boots="#111111",
               socks="#F2F2F2", **_kw):
    items = [shorts(ch, bm, "shorts", shorts_color, trim)]
    for sd in ("l", "r"):
        items.append(shoe(ch, bm, sd, 0.70, boots, sole_color="#1C1C1C", lace_color="#E8E8E8", collar=socks))
    hide_hands(ch, bm)
    for sd in ("l", "r"):
        items.append(glove(ch, sd, gloves))
    return items


def kickboxing_kit(ch, bm, shorts_color="#151515", trim="#D9A21B", gloves="#1F4FC8", ankle="#151515", **_kw):
    items = [shorts(ch, bm, "shorts", shorts_color, trim, length=0.84, flare=0.045, band=0.085, stripe=False)]
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
    items = [garment(ch, bm, "singlet", rules, lambda b, t, p: 0.0065, [(mat, None)], thickness=0.0015,
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
                     snap={"lowerarm": 0.88, "thigh": 0.14}, keep_face=keep_jacket,
                     # bol pamuk ceket: kas ayrıntısı kumaşta görünmez
                     anatomy=0.0, relax=(["spine_01", "spine_02", "spine_03", "pelvis", "clavicle", "upperarm",
                                          "lowerarm", "thigh"], 12),
                     clear=0.004, hide_inner=0.05)]
    def pants_pin(b, t, p):
        # bel (kuşağın altı) sabit; uyluktan paçaya doğru kumaş serbestleşir
        if b == "pelvis":
            return 1.0 if p[2] > hip_z - 0.02 * k else 0.7
        if b == "thigh":
            return 0.3 * (1.0 - min(1.0, max(0.0, t))) + 0.45
        return 0.42 - 0.1 * min(1.0, max(0.0, t))

    items.append(garment(ch, bm, "pants", {"pelvis": (-9, 9), "thigh": (-9, 9), "calf": (-9, 0.9)},
                         lambda b, t, p: 0.020 if b == "pelvis" else (0.022 + 0.012 * min(1, t) if b == "thigh"
                                                                      else 0.030 + 0.012 * t),
                         [(white, None)], thickness=0.003, smooth_iters=8,
                         snap={"calf": 0.9},
                         keep_face=lambda c, dom, t: dom != "pelvis" or c[2] < hip_z + 0.02 * k,
                         cloth=dict(pin=pants_pin, mass=0.25, stretch=15.0, bend=0.5, quality=12,
                                    pin_stiffness=5.0)))
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
                      "neck_01": (-9, 0.2), "upperarm": (-9, 0.56), "pelvis": (-9, 9)},
                     lambda b, t, p: (0.008 if b in ("clavicle", "spine_03", "neck_01") else
                                      (0.009 + 0.008 * t if b == "upperarm" else
                                       (0.017 if b == "pelvis" else 0.011))), [(tee, None)],
                     thickness=0.003, smooth_iters=6, snap={"upperarm": 0.56}, keep_face=keep, hem_z=hem,
                     # pamuklu tişört: göğüs ve sırt hacmi kalır, karın kası blokları kumaşa geçmez
                     anatomy=0.25, relax=(["spine_01", "spine_02", "spine_03", "pelvis", "clavicle"], 8),
                     clear=0.003, hide_inner=0.05)]
    items.append(shorts(ch, bm, "shorts", shorts_color, "#E6E6E6", length=0.84, flare=0.028, band=0.04,
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
