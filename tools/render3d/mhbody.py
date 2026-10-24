"""MakeHuman (MPFB2, CC0) temel gövdesi: şekil hedefleri, eklem noktaları, kemikler ve ağırlıklar.

Blender'dan bağımsızdır (yalnızca numpy). Koordinatlar Blender düzenindedir: metre, Z yukarı,
karakter -Y yönüne bakar (MPFB ile aynı).
"""
import gzip
import json
import os

import numpy as np

ASSET_DIR = os.environ.get(
    "MPFB_DATA", os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "mpfb2"))


def _mh_to_blender(a):
    """MakeHuman obj (desimetre, Y yukarı, +Z ileri) -> Blender (metre, Z yukarı, -Y ileri)."""
    a = np.asarray(a, dtype=np.float64).reshape(-1, 3)
    return np.stack([a[..., 0], -a[..., 2], a[..., 1]], axis=-1) * 0.1


class BaseMesh:
    def __init__(self, root=ASSET_DIR):
        self.root = root
        verts, uvs, faces, face_uvs, face_groups = [], [], [], [], []
        group = None
        with open(os.path.join(root, "3dobjs", "base.obj"), encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("v "):
                    verts.append([float(x) for x in line.split()[1:4]])
                elif line.startswith("vt "):
                    uvs.append([float(x) for x in line.split()[1:3]])
                elif line.startswith("f "):
                    vi, ti = [], []
                    for tok in line.split()[1:]:
                        p = tok.split("/")
                        vi.append(int(p[0]) - 1)
                        ti.append(int(p[1]) - 1 if len(p) > 1 and p[1] else -1)
                    faces.append(vi)
                    face_uvs.append(ti)
                    face_groups.append(group)
                elif line.startswith("g "):
                    group = line.split()[1]
        self.rest = _mh_to_blender(verts)
        self.uvs = np.array(uvs)
        self.faces = faces
        self.face_uvs = face_uvs
        self.face_groups = face_groups
        with open(os.path.join(root, "mesh_metadata", "basemesh_vertex_groups.json"), encoding="utf-8") as fh:
            raw = json.load(fh)
        self.groups = {}
        for name, ranges in raw.items():
            idx = []
            for a, b in ranges:
                idx.extend(range(a, b + 1))
            self.groups[name] = np.array(idx, dtype=np.int64)
        self._target_cache = {}

    # -- hedefler ------------------------------------------------------------------
    def target(self, rel):
        if rel not in self._target_cache:
            path = os.path.join(self.root, "targets", rel + ".target.gz")
            idx, delta = [], []
            with gzip.open(path, "rt", encoding="utf-8") as fh:
                for line in fh:
                    p = line.split()
                    if len(p) == 4 and not line.startswith("#"):
                        idx.append(int(p[0]))
                        delta.append([float(x) for x in p[1:]])
            self._target_cache[rel] = (np.array(idx, dtype=np.int64), _mh_to_blender(delta))
        return self._target_cache[rel]

    def faces_in(self, group):
        return [k for k, g in enumerate(self.face_groups) if g == group]


# --------------------------------------------------------------------------------
# Makro değişkenler (MakeHuman ile aynı ağırlıklandırma)
# --------------------------------------------------------------------------------
def _interp(value, points):
    """points: [(isim, konum)...] artan konum; değeri komşu iki isim arasında doğrusal paylaştırır."""
    out = {name: 0.0 for name, _ in points}
    if value <= points[0][1]:
        out[points[0][0]] = 1.0
        return out
    for (n0, p0), (n1, p1) in zip(points, points[1:]):
        if value <= p1:
            t = (value - p0) / (p1 - p0)
            out[n0] += 1.0 - t
            out[n1] += t
            return out
    out[points[-1][0]] = 1.0
    return out


def macro_weights(gender, age, muscle, weight):
    return (
        _interp(gender, [("female", 0.0), ("male", 1.0)]),
        _interp(age, [("baby", 0.0), ("child", 0.1875), ("young", 0.5), ("old", 1.0)]),
        _interp(muscle, [("minmuscle", 0.0), ("averagemuscle", 0.5), ("maxmuscle", 1.0)]),
        _interp(weight, [("minweight", 0.0), ("averageweight", 0.5), ("maxweight", 1.0)]),
    )


DEFAULT_SHAPE = dict(
    gender=1.0, age=0.5, muscle=0.5, weight=0.5, height=0.5, proportions=0.5,
    race=dict(african=1 / 3, asian=1 / 3, caucasian=1 / 3),
    details={},
)


def shaped_vertices(base, shape):
    s = dict(DEFAULT_SHAPE)
    s.update(shape)
    gw, aw, mw, ww = macro_weights(s["gender"], s["age"], s["muscle"], s["weight"])
    v = base.rest.copy()

    def add(rel, w):
        if w <= 1e-6:
            return
        idx, d = base.target(rel)
        v[idx] += w * d

    for g, wg in gw.items():
        for a, wa in aw.items():
            if wg * wa <= 0:
                continue
            for race, wr in s["race"].items():
                add(f"macrodetails/{race}-{g}-{a}", wg * wa * wr)
            for m, wm in mw.items():
                for wt, wwt in ww.items():
                    base_w = wg * wa * wm * wwt
                    if base_w <= 0:
                        continue
                    add(f"macrodetails/universal-{g}-{a}-{m}-{wt}", base_w)
                    h = s["height"]
                    if h > 0.5:
                        add(f"macrodetails/height/{g}-{a}-{m}-{wt}-maxheight", base_w * (h - 0.5) * 2)
                    elif h < 0.5:
                        add(f"macrodetails/height/{g}-{a}-{m}-{wt}-minheight", base_w * (0.5 - h) * 2)
                    p = s["proportions"]
                    if p > 0.5:
                        add(f"macrodetails/proportions/{g}-{a}-{m}-{wt}-idealproportions", base_w * (p - 0.5) * 2)
                    elif p < 0.5:
                        add(f"macrodetails/proportions/{g}-{a}-{m}-{wt}-uncommonproportions", base_w * (0.5 - p) * 2)
    for rel, w in s["details"].items():
        add(rel, w)
    return v


# --------------------------------------------------------------------------------
# İskelet
# --------------------------------------------------------------------------------
def _smoothstep(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


class Rig:
    def __init__(self, base, verts, name="game_engine", root=ASSET_DIR):
        with open(os.path.join(root, "rigs", "standard", f"rig.{name}.json"), encoding="utf-8") as fh:
            self.spec = json.load(fh)
        with open(os.path.join(root, "rigs", "standard", f"weights.{name}.json"), encoding="utf-8") as fh:
            self.weights = json.load(fh)["weights"]

        def point(p):
            if p["strategy"] == "CUBE":
                return verts[base.groups[p["cube_name"]]].mean(axis=0)
            if p["strategy"] == "MEAN":
                return verts[np.array(p["vertex_indices"])].mean(axis=0)
            if p["strategy"] == "VERTEX":
                return verts[p["vertex_index"]]
            raise ValueError(p["strategy"])

        self.bones = {}
        for bname, b in self.spec.items():
            self.bones[bname] = dict(head=point(b["head"]), tail=point(b["tail"]), roll=b["roll"],
                                     parent=b["parent"] or None)
        # ebeveyn sırası (kökten yapraklara)
        order, seen = [], set()

        def visit(n):
            if n in seen:
                return
            p = self.bones[n]["parent"]
            if p:
                visit(p)
            seen.add(n)
            order.append(n)

        for n in self.bones:
            visit(n)
        self.order = order
        # deri ağırlıkları: kol/bacak dönüşü (twist) uzuv boyunca yardımcı kemiklere dağıtılır;
        # self.weights özgün kalır (giysi bölgeleri baskın kemiğe göre seçilir)
        self.skin_weights = self._twist_weights(verts)

    # yardımcı twist kemikleri: (ad, ana kemik, kemik boyunca baş/uç, ağırlık(t))
    TWIST = (
        ("upperarm_twist", "upperarm", (0.0, 0.5), lambda t: 1.0 - _smoothstep(0.05, 0.6, t)),
        ("lowerarm_twist", "lowerarm", (0.5, 1.0), lambda t: _smoothstep(0.2, 0.95, t)),
        ("thigh_twist", "thigh", (0.0, 0.5), lambda t: 1.0 - _smoothstep(0.05, 0.55, t)),
    )

    def _twist_weights(self, verts):
        weights = {b: list(p) for b, p in self.weights.items()}
        for tw, main, (a, b), wfun in self.TWIST:
            for s in ("l", "r"):
                parent = self.bones[f"{main}_{s}"]
                h, tl = np.asarray(parent["head"]), np.asarray(parent["tail"])
                ax = tl - h
                name = f"{tw}_{s}"
                self.bones[name] = dict(head=h + ax * a, tail=h + ax * b, roll=parent["roll"],
                                        parent=f"{main}_{s}")
                self.order.append(name)
                keep, moved = [], []
                for vi, w in weights[f"{main}_{s}"]:
                    t = float((verts[vi] - h) @ ax / (ax @ ax))
                    f = wfun(t)
                    if f > 1e-3:
                        moved.append((vi, w * f))
                    if f < 1.0 - 1e-3:
                        keep.append((vi, w * (1.0 - f)))
                weights[f"{main}_{s}"] = keep
                weights[name] = moved
        return weights

    def joint(self, base, verts, cube):
        return verts[base.groups[cube]].mean(axis=0)
