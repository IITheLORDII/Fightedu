"""Blender'da gerçekçi sporcu: MakeHuman gövdesi, iskelet, ten/göz/saç malzemeleri.

Kıyafetler outfits.py'de üretilir. Bu modül yalnızca bpy içinde çalışır.
"""
import math

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

import anatomy
from mhbody import BaseMesh, Rig, shaped_vertices
from shading import set_texspace, skin_material, srgb

_BASE = None


def base_mesh():
    global _BASE
    if _BASE is None:
        _BASE = BaseMesh()
    return _BASE


# --------------------------------------------------------------------------------
# Malzemeler
# --------------------------------------------------------------------------------
def _principled(mat):
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    return nt, bsdf


def simple_material(name, color, roughness=0.5, metallic=0.0, coat=0.0, sheen=0.0, bump=0.0, bump_scale=120.0):
    mat = bpy.data.materials.new(name)
    nt, bsdf = _principled(mat)
    bsdf.inputs["Base Color"].default_value = srgb(color) if isinstance(color, str) else color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if coat:
        bsdf.inputs["Coat Weight"].default_value = coat
        bsdf.inputs["Coat Roughness"].default_value = 0.25
    if sheen:
        bsdf.inputs["Sheen Weight"].default_value = sheen
    if bump:
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = bump_scale
        b = nt.nodes.new("ShaderNodeBump")
        b.inputs["Strength"].default_value = bump
        nt.links.new(tex.outputs["Fac"], b.inputs["Height"])
        nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def hair_material(name, color):
    """Kısa saç: mat, koyu, ince tel dokusu (noise) ile."""
    mat = bpy.data.materials.new(name)
    nt, bsdf = _principled(mat)
    n, links = nt.nodes, nt.links
    tc = n.new("ShaderNodeTexCoord")
    noise = n.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 140.0
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.7
    links.new(tc.outputs["Object"], noise.inputs["Vector"])
    ramp = n.new("ShaderNodeValToRGB")
    base = srgb(color)
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = tuple(c * 0.6 for c in base[:3]) + (1.0,)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = tuple(min(1.0, c * 1.35) for c in base[:3]) + (1.0,)
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.9
    bsdf.inputs["Specular IOR Level"].default_value = 0.12
    bump = n.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.8
    bump.inputs["Distance"].default_value = 0.002
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def eye_material(name, iris="#3B2618"):
    mat = bpy.data.materials.new(name)
    nt, bsdf = _principled(mat)
    n, links = nt.nodes, nt.links
    tc = n.new("ShaderNodeTexCoord")
    sep = n.new("ShaderNodeSeparateXYZ")
    links.new(tc.outputs["Object"], sep.inputs["Vector"])
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "EASE"
    e = ramp.color_ramp.elements
    e[0].position = 0.0
    e[0].color = (0.78, 0.74, 0.70, 1.0)
    e[1].position = 0.80
    e[1].color = (0.80, 0.76, 0.72, 1.0)
    e2 = ramp.color_ramp.elements.new(0.84)
    e2.color = srgb(iris)
    e3 = ramp.color_ramp.elements.new(0.94)
    e3.color = (0.01, 0.01, 0.01, 1.0)
    math_n = n.new("ShaderNodeMath")
    math_n.operation = "MULTIPLY"
    math_n.inputs[1].default_value = 1.0
    links.new(sep.outputs["Z"], math_n.inputs[0])
    links.new(math_n.outputs[0], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.08
    bsdf.inputs["Coat Weight"].default_value = 1.0
    return mat


# --------------------------------------------------------------------------------
# Yardımcılar
# --------------------------------------------------------------------------------
def mesh_from(name, verts, faces, uv_faces=None, uvs=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    if uv_faces is not None and uvs is not None:
        uvl = me.uv_layers.new(name="UVMap")
        k = 0
        for poly, fuv in zip(me.polygons, uv_faces):
            for li, ti in zip(poly.loop_indices, fuv):
                uvl.data[li].uv = tuple(uvs[ti]) if ti >= 0 else (0.0, 0.0)
                k += 1
    for p in me.polygons:
        p.use_smooth = True
    me.validate()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def submesh(base, verts, group, extra_faces=None):
    """Bir obj grubundaki yüzlerden yeni (yeniden numaralanmış) alt ağ: (verts, faces, uvfaces, old_idx)."""
    fids = base.faces_in(group) if extra_faces is None else extra_faces
    used = sorted({v for k in fids for v in base.faces[k]})
    remap = {o: i for i, o in enumerate(used)}
    faces = [[remap[v] for v in base.faces[k]] for k in fids]
    uvf = [base.face_uvs[k] for k in fids]
    return verts[used], faces, uvf, np.array(used)


def _deform(ob, arm_ob):
    """İskelet deformasyonu: hacmi koruyan (dual quaternion) bükme + eklemlerdeki büzülmeleri gideren
    düzeltici yumuşatma (dinlenme şeklindeki ayrıntıyı geri ekler, yalnızca deformasyon bozukluklarını siler)."""
    mod = ob.modifiers.new("Armature", "ARMATURE")
    mod.object = arm_ob
    mod.use_deform_preserve_volume = True
    cs = ob.modifiers.new("Corrective", "CORRECTIVE_SMOOTH")
    cs.rest_source = "ORCO"
    cs.smooth_type = "LENGTH_WEIGHTED"
    cs.iterations = 8
    cs.factor = 0.5
    cs.use_pin_boundary = True
    return mod


# --------------------------------------------------------------------------------
# Karakter
# --------------------------------------------------------------------------------
ATHLETE = dict(
    gender=1.0, age=0.45, muscle=1.0, weight=0.42, height=0.5, proportions=0.9,
    race=dict(african=0.06, asian=0.06, caucasian=0.88),
    details={
        # gövde: geniş omuz ve sırt (V), kalın göğüs, ince bel, düz karın, kısa-kalın boyun
        "torso/torso-vshape-incr": 0.6,
        "torso/torso-muscle-pectoral-incr": 1.0,
        "torso/torso-muscle-dorsi-incr": 1.0,
        "torso/measure-waist-circ-decr": 0.85,
        "torso/measure-shoulder-dist-decr": 0.35,
        "torso/measure-bust-circ-incr": 0.5,
        "torso/torso-scale-depth-incr": 0.15,
        "torso/measure-hips-circ-decr": 0.3,
        "stomach/stomach-pregnant-decr": 1.0,
        "stomach/stomach-tone-incr": 1.0,
        "neck/measure-neck-circ-incr": 1.0,
        "neck/measure-neck-height-decr": 0.45,
        "neck/neck-scale-horiz-incr": 0.35, "neck/neck-scale-depth-incr": 0.25,
        # kollar: dolgun deltoid, biseps/triseps, önkol
        "arms/l-upperarm-muscle-incr": 1.0, "arms/r-upperarm-muscle-incr": 1.0,
        "arms/l-upperarm-shoulder-muscle-incr": 1.0, "arms/r-upperarm-shoulder-muscle-incr": 1.0,
        "arms/l-lowerarm-muscle-incr": 1.0, "arms/r-lowerarm-muscle-incr": 1.0,
        "arms/l-upperarm-scale-horiz-incr": 0.9, "arms/r-upperarm-scale-horiz-incr": 0.9,
        "arms/l-upperarm-scale-depth-incr": 0.7, "arms/r-upperarm-scale-depth-incr": 0.7,
        "arms/l-lowerarm-scale-horiz-incr": 0.25, "arms/r-lowerarm-scale-horiz-incr": 0.25,
        "arms/l-upperarm-fat-decr": 1.0, "arms/r-upperarm-fat-decr": 1.0,
        "arms/measure-upperarm-circ-incr": 0.8,
        "arms/l-lowerarm-fat-decr": 1.0, "arms/r-lowerarm-fat-decr": 1.0,
        # bacaklar: kuadriseps ve baldır (gastroknemius)
        "legs/l-upperleg-muscle-incr": 1.0, "legs/r-upperleg-muscle-incr": 1.0,
        "legs/l-lowerleg-muscle-incr": 1.0, "legs/r-lowerleg-muscle-incr": 1.0,
        "legs/l-upperleg-fat-decr": 0.8, "legs/r-upperleg-fat-decr": 0.8,
        "legs/l-upperleg-scale-horiz-incr": 0.3, "legs/r-upperleg-scale-horiz-incr": 0.3,
        "legs/l-upperleg-scale-depth-incr": 0.15, "legs/r-upperleg-scale-depth-incr": 0.15,
        "legs/measure-calf-circ-incr": 0.5, 
        "legs/l-lowerleg-fat-decr": 0.6, "legs/r-lowerleg-fat-decr": 0.6,
        "buttocks/buttocks-volume-incr": 0.25,
    },
)


class Character:
    """Bir sporcu: armature + gövde (+ saç, gözler); poz bone matrisleriyle verilir."""

    def __init__(self, name, shape=ATHLETE, skin="#B07A58", hair="#1E140E", iris="#4A2E1C",
                 target_height=1.76):
        self.name = name
        base = base_mesh()
        verts = shaped_vertices(base, shape)
        body_idx = base.groups["body"]
        # ayak tabanı z=0 ve hedef boy
        zmin = verts[body_idx, 2].min()
        h = verts[body_idx, 2].max() - zmin
        self.scale = target_height / h
        self.size = target_height / 1.76
        verts = verts.copy()
        verts[:, 2] -= zmin
        verts *= self.scale
        self.verts = verts
        self.rig = Rig(base, verts)
        self.base = base
        # anatomik yontu: kas kütleleri temel ağa işlenir (giysiler de bu hacmi taşır), ince ayrıntı
        # (oluklar, kas sınırları) haritada kalır ve Subsurf'ten sonra Displace ile uygulanır
        verts, self.anat = anatomy.sculpt(base, verts, self.rig, self.size, cache_key=repr(shape))
        self.verts = verts

        self.arm_ob = self._armature()
        bv, bf, buvf, used = submesh(base, verts, "body")
        self.body_used = used
        self.bv, self.bf, self.buvf = bv, bf, buvf
        self.body = mesh_from(f"{name}_body", bv, bf, buvf, base.uvs)
        self._weights(self.body, used)
        self.regions = self._face_regions(bv)
        set_texspace(self.body, self.regions["center"], self.regions["half"])
        self.body.data.materials.append(skin_material(f"{name}_skin", skin, self.regions, hair_color=hair))
        self._subsurf(self.body, 2)
        self.anat_tex = self._anatomy_texture()
        self.displace(self.body)

        self.cloth = []  # kumaş simülasyonlu giysiler (outfits.add_cloth)
        self.hair = self._short_hair(hair)
        self.eyes = self._eyes(iris)

    # -- yapı ---------------------------------------------------------------------
    def _armature(self):
        arm = bpy.data.armatures.new(f"{self.name}_arm")
        ob = bpy.data.objects.new(f"{self.name}_rig", arm)
        bpy.context.scene.collection.objects.link(ob)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.mode_set(mode="EDIT")
        for bname in self.rig.order:
            b = self.rig.bones[bname]
            eb = arm.edit_bones.new(bname)
            eb.head = Vector(b["head"])
            eb.tail = Vector(b["tail"])
            eb.roll = b["roll"]
            if b["parent"]:
                eb.parent = arm.edit_bones[b["parent"]]
        bpy.ops.object.mode_set(mode="OBJECT")
        for pb in ob.pose.bones:
            pb.rotation_mode = "QUATERNION"
        return ob

    def _weights(self, ob, used, nearest=False):
        rig = self.rig
        ob.parent = self.arm_ob
        _deform(ob, self.arm_ob)
        if nearest:
            # yardımcı geometri: en yakın gövde köşesinin ağırlıklarını kopyala
            from mathutils.kdtree import KDTree
            body = self.body_used
            kd = KDTree(len(body))
            for i, vi in enumerate(body):
                kd.insert(Vector(self.verts[vi]), i)
            kd.balance()
            src = {}
            for bone, pairs in rig.skin_weights.items():
                for vi, w in pairs:
                    src.setdefault(vi, []).append((bone, w))
            for i, vi in enumerate(used):
                _co, j, _d = kd.find(Vector(self.verts[vi]))
                for bone, w in src.get(int(body[j]), []):
                    g = ob.vertex_groups.get(bone) or ob.vertex_groups.new(name=bone)
                    g.add([i], w, "REPLACE")
            return
        local = {int(o): i for i, o in enumerate(used)}
        for bone, pairs in rig.skin_weights.items():
            idx = [(local[vi], w) for vi, w in pairs if vi in local]
            if not idx:
                continue
            g = ob.vertex_groups.new(name=bone)
            for i, w in idx:
                g.add([i], w, "REPLACE")

    def _subsurf(self, ob, level):
        m = ob.modifiers.new("Subsurf", "SUBSURF")
        m.levels = 0
        m.render_levels = level

    def _anatomy_texture(self):
        h = self.anat
        size = h.shape[0]
        self.anat_amp = float(np.abs(h).max()) + 1e-6
        img = bpy.data.images.new(f"{self.name}_anatomy", size, size, float_buffer=True, is_data=True)
        v = (0.5 + h / (2.0 * self.anat_amp)).astype(np.float32).ravel()
        px = np.ones(size * size * 4, dtype=np.float32)
        px[0::4] = v
        px[1::4] = v
        px[2::4] = v
        img.pixels.foreach_set(px)
        tex = bpy.data.textures.new(f"{self.name}_anatomy", "IMAGE")
        tex.image = img
        tex.extension = "EXTEND"
        return tex

    def displace(self, ob, scale=1.0):
        """Anatomik yontuyu (gövde UV'siyle) bir ağa uygula: gövde ve gövdeden türetilen dar giysiler."""
        m = ob.modifiers.new("Anatomy", "DISPLACE")
        m.texture = self.anat_tex
        m.texture_coords = "UV"
        m.uv_layer = ob.data.uv_layers[0].name
        m.direction = "NORMAL"
        m.mid_level = 0.5
        m.strength = 2.0 * self.anat_amp * scale
        return m

    def proxy(self):
        """Giysilerin bağlandığı, render edilmeyen alt çözünürlüklü gövde kopyası (yalnızca Armature)."""
        if getattr(self, "_proxy", None) is None:
            me = self.body.data.copy()
            me.name = f"{self.name}_proxy"
            # üçgenle: yontulmuş ağda dörtgenler düzlemsel/dışbükey olmayabilir, Surface Deform bağlanamaz
            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.triangulate(bm, faces=bm.faces[:])
            bm.to_mesh(me)
            bm.free()
            ob = bpy.data.objects.new(f"{self.name}_proxy", me)
            bpy.context.scene.collection.objects.link(ob)
            # köşe grupları (deri ağırlıkları) ağ verisiyle birlikte kopyalanır
            ob.parent = self.arm_ob
            _deform(ob, self.arm_ob)
            ob.hide_render = True
            ob.visible_camera = False
            ob.visible_shadow = False
            self._proxy = ob
        return self._proxy

    def collider(self):
        """Kumaşın çarptığı yüzey: vekil gövdeye çarpışma niteliği."""
        ob = self.proxy()
        if ob.modifiers.get("Collision") is None:
            ob.modifiers.new("Collision", "COLLISION")
            c = ob.collision
            c.thickness_outer = 0.004
            c.cloth_friction = 8.0
            c.damping = 0.3
        return ob

    def joint(self, cube):
        return self.verts[self.base.groups[cube]].mean(axis=0)

    def _face_regions(self, bv):
        """Yüz/gövde ayrıntı maskeleri (rest koordinatında elipsoidler)."""
        k = self.size
        lo, hi = bv.min(axis=0), bv.max(axis=0)
        center, half = (lo + hi) / 2, (hi - lo) / 2 + 1e-3
        le, re = self.joint("joint-l-eye"), self.joint("joint-r-eye")
        E = (le + re) / 2
        head = bv[bv[:, 2] > E[2] - 0.14 * k]

        def front_y(x, z, tol=0.006):
            m = (np.abs(head[:, 0] - x) < tol * k) & (np.abs(head[:, 2] - z) < tol * k)
            return head[m, 1].min() if m.any() else E[1] - 0.02 * k

        y_back = head[:, 1].max()
        y_front = front_y(0.0, E[2] + 0.05 * k)
        brows = []
        for e in (le, re):
            sx = np.sign(e[0])
            for dx, dz, rx, rz in ((-0.010, 0.0155, 0.011, 0.0042), (0.004, 0.0175, 0.012, 0.0040),
                                   (0.016, 0.0160, 0.009, 0.0033)):
                x, z = e[0] + sx * dx * k, e[2] + dz * k
                brows.append(((x, front_y(x, z) + 0.004 * k, z), (rx * k, 0.012 * k, rz * k)))
        mouth_z = E[2] - 0.071 * k
        lips = [((0.0, front_y(0.0, mouth_z) + 0.003 * k, mouth_z), (0.024 * k, 0.012 * k, 0.0085 * k))]
        stubble = [((0.0, front_y(0.0, E[2] - 0.09 * k) + 0.035 * k, E[2] - 0.085 * k), (0.068 * k, 0.07 * k, 0.04 * k)),
                   ((0.0, front_y(0.0, mouth_z + 0.014 * k) + 0.004 * k, mouth_z + 0.014 * k),
                    (0.026 * k, 0.012 * k, 0.006 * k))]
        # saç çizgisi: alında E+5 cm, ensede E-5.5 cm (eğik düzlem)
        p0 = np.array([0.0, y_front, E[2] + 0.052 * k])
        p1 = np.array([0.0, y_back, E[2] - 0.055 * k])
        t = p1 - p0
        n = np.array([0.0, -t[2], t[1]])
        n /= np.linalg.norm(n)
        if n[2] < 0:
            n = -n
        ear_y = E[1] + 0.085 * k
        hx = head[np.abs(head[:, 2] - E[2]) < 0.02 * k, 0].max()
        scalp = dict(plane=(p0, n), soft=0.006 * k,
                     head=((0.0, (y_front + y_back) / 2, E[2] + 0.02 * k),
                           (hx + 0.06 * k, (y_back - y_front) / 2 + 0.06 * k, 0.2 * k)),
                     cut=[((sx * hx, ear_y, E[2] - 0.008 * k), (0.02 * k, 0.03 * k, 0.034 * k)) for sx in (1, -1)]
                     + [((sx * 0.05 * k, y_front + 0.012 * k, E[2] + 0.05 * k), (0.02 * k, 0.03 * k, 0.02 * k))
                        for sx in (1, -1)])
        # meme uçları: göğüs ön yüzeyinde
        nipples = []
        sh = self.joint("joint-l-shoulder")
        for sx in (1, -1):
            x, z = sx * 0.095 * k, sh[2] - 0.165 * k
            m = (np.abs(bv[:, 0] - x) < 0.008 * k) & (np.abs(bv[:, 2] - z) < 0.008 * k) & (bv[:, 1] < sh[1])
            y = bv[m, 1].min() if m.any() else sh[1] - 0.1 * k
            nipples.append(((x, y, z), (0.011 * k, 0.012 * k, 0.010 * k)))
        self.hairline = (p0, n)
        return dict(center=center, half=half, brows=brows, lips=lips, stubble=stubble, scalp=scalp,
                    nipples=nipples)

    def _short_hair(self, color, top=0.0035, margin=0.02):
        """Üstte hacimli kısa saç kabuğu; kenarları boyalı saç çizgisinin içinde incelir (fade)."""
        base, verts = self.base, self.verts
        k = self.size
        p0, n = self.hairline
        le, re = self.joint("joint-l-eye"), self.joint("joint-r-eye")
        E = (le + re) / 2
        dist = (verts - p0) @ n
        ok = (dist > margin * k) & (verts[:, 2] > E[2] - 0.02 * k)
        head_faces = [i for i, f in enumerate(base.faces)
                      if base.face_groups[i] == "body" and all(ok[v] for v in f)]
        hv, hf, huvf, hused = submesh(base, verts, "body", extra_faces=head_faces)
        ob = mesh_from(f"{self.name}_hair", hv, hf, huvf, base.uvs)
        me = ob.data
        me.update()
        normals = np.array([v.normal[:] for v in me.vertices])
        d = (hv - p0) @ n
        t = np.clip((d - margin * k) / (0.05 * k), 0.0, 1.0)
        thick = 0.0008 * k + top * k * (t * t * (3 - 2 * t))
        new = hv + normals * thick[:, None]
        for v, co in zip(me.vertices, new):
            v.co = co
        self._weights(ob, hused)
        ob.data.materials.append(hair_material(f"{self.name}_hairmat", color))
        self._subsurf(ob, 1)
        return ob

    def _eyes(self, iris):
        out = []
        mat = eye_material(f"{self.name}_eyemat", iris)
        for side in ("l", "r"):
            c = self.joint(f"joint-{side}-eye")
            r = 0.0118 * self.size
            bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=24, ring_count=12, location=tuple(c))
            ob = bpy.context.active_object
            ob.name = f"{self.name}_eye_{side}"
            # yerel +Z bakış yönü (-Y); nesne koordinatları birim küre (malzeme Z'yi kullanır)
            ob.rotation_euler = (math.radians(90), 0, 0)
            ob.scale = (r, r, r)
            bpy.context.view_layer.update()
            for p in ob.data.polygons:
                p.use_smooth = True
            ob.data.materials.append(mat)
            # kafa kemiğine bağla
            mw = ob.matrix_world.copy()
            ob.parent = self.arm_ob
            ob.parent_type = "BONE"
            ob.parent_bone = "head"
            ob.matrix_world = mw
            out.append(ob)
        return out
