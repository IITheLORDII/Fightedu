"""Düğüm (node) yardımcıları ve ten malzemesi.

Yüz ayrıntıları (kaş, dudak, sakal gölgesi, kısa saç, meme ucu) dokuyla değil, gövdenin
duruş öncesi (rest) koordinatlarında tanımlı yumuşak elipsoid maskelerle çizilir. Cycles'ın
'Generated' koordinatları deformasyondan önceki ağdan hesaplandığı için maskeler hareketle
birlikte deriye yapışık kalır.
"""
import bpy


def srgb(hexstr):
    h = hexstr.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def scaled(color, k):
    return tuple(min(1.0, c * k) for c in color[:3]) + (1.0,)


class NB:
    """Küçük düğüm kurucu."""

    def __init__(self, nt):
        self.nt = nt
        self.n = nt.nodes
        self.l = nt.links

    def node(self, kind, **inputs):
        nd = self.n.new(kind)
        for k, v in inputs.items():
            self.set(nd.inputs[k], v)
        return nd

    def set(self, sock, v):
        if hasattr(v, "is_output") or hasattr(v, "links"):
            self.l.new(v, sock)
        else:
            sock.default_value = v

    def math(self, op, a, b=0.0, c=None, clamp=False):
        nd = self.n.new("ShaderNodeMath")
        nd.operation = op
        nd.use_clamp = clamp
        self.set(nd.inputs[0], a)
        self.set(nd.inputs[1], b)
        if c is not None:
            self.set(nd.inputs[2], c)
        return nd.outputs[0]

    def vmath(self, op, a, b=(0.0, 0.0, 0.0), c=None):
        nd = self.n.new("ShaderNodeVectorMath")
        nd.operation = op
        self.set(nd.inputs[0], a)
        self.set(nd.inputs[1], b)
        if c is not None:
            self.set(nd.inputs[2], c)
        return nd.outputs["Value"] if op in ("LENGTH", "DOT_PRODUCT", "DISTANCE") else nd.outputs["Vector"]

    def vec_scale(self, v, scale):
        nd = self.n.new("ShaderNodeVectorMath")
        nd.operation = "SCALE"
        self.set(nd.inputs[0], v)
        self.set(nd.inputs["Scale"], scale)
        return nd.outputs["Vector"]

    def smooth(self, x, a, b, invert=False):
        """a..b arasında 0→1 (invert: 1→0) yumuşak geçiş."""
        nd = self.n.new("ShaderNodeMapRange")
        nd.interpolation_type = "SMOOTHSTEP"
        self.set(nd.inputs["Value"], x)
        nd.inputs["From Min"].default_value = a
        nd.inputs["From Max"].default_value = b
        nd.inputs["To Min"].default_value = 1.0 if invert else 0.0
        nd.inputs["To Max"].default_value = 0.0 if invert else 1.0
        return nd.outputs["Result"]

    def mix(self, fac, a, b):
        nd = self.n.new("ShaderNodeMix")
        nd.data_type = "RGBA"
        self.set(nd.inputs[0], fac)
        self.set(nd.inputs[6], a)
        self.set(nd.inputs[7], b)
        return nd.outputs[2]

    def rest_position(self, center, half):
        """Generated (0..1) -> dinlenme pozundaki dünya konumu (metre)."""
        tc = self.n.new("ShaderNodeTexCoord")
        size = tuple(2 * h for h in half)
        lo = tuple(c - h for c, h in zip(center, half))
        return self.vmath("MULTIPLY_ADD", tc.outputs["Generated"], size, lo)

    def ellipsoid(self, pos, center, radii, soft=0.25):
        q = self.vmath("DIVIDE", self.vmath("SUBTRACT", pos, tuple(center)), tuple(radii))
        d = self.vmath("LENGTH", q)
        return self.smooth(d, 1.0 - soft, 1.0 + soft, invert=True)

    def union(self, *masks):
        out = masks[0]
        for m in masks[1:]:
            out = self.math("MAXIMUM", out, m)
        return out


def set_texspace(ob, center, half):
    me = ob.data
    me.use_auto_texspace = False
    me.texspace_location = tuple(center)
    me.texspace_size = tuple(half)


def halfspace(b, pos, p0, normal, soft):
    d = b.vmath("DOT_PRODUCT", b.vmath("SUBTRACT", pos, tuple(p0)), tuple(normal))
    return b.smooth(d, -soft, soft)


def scalp_mask(b, pos, spec):
    """spec: dict(plane=(p0, n), soft, head=(c, r), cut=[(c, r)...]) ya da None."""
    if not spec:
        return 0.0
    # düzensiz saç çizgisi: düzlem uzaklığına gürültü ekle
    d = b.vmath("DOT_PRODUCT", b.vmath("SUBTRACT", pos, tuple(spec["plane"][0])), tuple(spec["plane"][1]))
    nz = b.node("ShaderNodeTexNoise", Scale=180.0, Detail=4.0)
    b.set(nz.inputs["Vector"], pos)
    d = b.math("MULTIPLY_ADD", b.math("SUBTRACT", nz.outputs["Fac"], 0.5), 0.012, d)
    soft = spec.get("soft", 0.006)
    m = b.smooth(d, -soft, soft)
    c, r = spec["head"]
    m = b.math("MULTIPLY", m, b.ellipsoid(pos, c, r, 0.08))
    for c, r in spec.get("cut", []):
        m = b.math("MULTIPLY", m, b.math("SUBTRACT", 1.0, b.ellipsoid(pos, c, r, 0.25), clamp=True))
    return m


def skin_material(name, tone, regions, hair_color="#20140E", stubble=0.22):
    """regions: dict(center, half, brows=[(c, r)...], lips=[...], stubble=[...], scalp=[...],
    nipples=[...], cut=[...]) – hepsi rest koordinatında elipsoidler."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    b = NB(nt)
    pos = b.rest_position(regions["center"], regions["half"])

    def masks(key, soft=0.3):
        items = regions.get(key, [])
        if not items:
            return 0.0
        return b.union(*[b.ellipsoid(pos, c, r, soft) for c, r in items])

    base = srgb(tone)
    # ten: düşük frekanslı renk değişimi (kızarıklık / gölgeler)
    noise = b.node("ShaderNodeTexNoise", Scale=9.0, Detail=3.0)
    b.set(noise.inputs["Vector"], pos)
    ramp = b.n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (base[0] * 0.93, base[1] * 0.82, base[2] * 0.80, 1.0)
    ramp.color_ramp.elements[1].color = scaled(base, 1.05)
    b.l.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    col = ramp.outputs["Color"]

    hair = srgb(hair_color)
    # sakal gölgesi
    fine = b.node("ShaderNodeTexNoise", Scale=900.0, Detail=1.0)
    b.set(fine.inputs["Vector"], pos)
    grain = b.smooth(fine.outputs["Fac"], 0.35, 0.65)
    st = masks("stubble", 0.35)
    if st != 0.0:
        col = b.mix(b.math("MULTIPLY", st, b.math("MULTIPLY_ADD", grain, 0.5 * stubble, 0.5 * stubble)), col,
                    scaled(hair, 1.6))
    # kısa saç (ensede/yanlarda kesik saç görünümü)
    sc = scalp_mask(b, pos, regions.get("scalp"))
    if sc != 0.0:
        col = b.mix(b.math("MULTIPLY", sc, b.math("MULTIPLY_ADD", grain, 0.08, 0.92)), col, hair)
    # kaşlar
    br = masks("brows", 0.35)
    if br != 0.0:
        col = b.mix(b.math("MULTIPLY", br, b.math("MULTIPLY_ADD", grain, 0.3, 0.65)), col, hair)
    # dudak ve meme ucu
    lp = masks("lips", 0.4)
    if lp != 0.0:
        col = b.mix(b.math("MULTIPLY", lp, 0.55), col, (base[0] * 0.80, base[1] * 0.42, base[2] * 0.40, 1.0))
    nip = masks("nipples", 0.45)
    if nip != 0.0:
        col = b.mix(b.math("MULTIPLY", nip, 0.75), col, (base[0] * 0.55, base[1] * 0.33, base[2] * 0.28, 1.0))

    # kas ayrımı: içbükey bölgeleri (pointiness) hafifçe koyulaştır
    ao = b.n.new("ShaderNodeAmbientOcclusion")
    ao.only_local = True
    ao.samples = 8
    ao.inputs["Distance"].default_value = 0.06
    cav = b.smooth(ao.outputs["AO"], 0.55, 1.0, invert=True)
    col = b.mix(b.math("MULTIPLY", cav, 0.55), col, (base[0] * 0.55, base[1] * 0.38, base[2] * 0.33, 1.0))
    b.l.new(col, bsdf.inputs["Base Color"])

    bsdf.inputs["Subsurface Weight"].default_value = 0.15
    bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.4, 0.25)
    bsdf.inputs["Subsurface Scale"].default_value = 0.01
    rough = b.math("MULTIPLY_ADD", sc, 0.2, 0.5) if sc != 0.0 else 0.5
    b.set(bsdf.inputs["Roughness"], rough)
    bsdf.inputs["Specular IOR Level"].default_value = 0.32
    # deri dokusu
    pores = b.node("ShaderNodeTexNoise", Scale=700.0, Detail=2.0)
    b.set(pores.inputs["Vector"], pos)
    bump = b.node("ShaderNodeBump", Strength=0.04)
    b.l.new(pores.outputs["Fac"], bump.inputs["Height"])
    normal = bump.outputs["Normal"]
    # anatomik kas ayrımları (kabartma haritası) ve oluklarda hafif koyulaşma
    relief = regions.get("relief", [])
    if relief:
        hgt = None
        groove = None
        for c, r, h in relief:
            m = b.ellipsoid(pos, c, r, 0.6)
            term = b.math("MULTIPLY", m, h)
            hgt = term if hgt is None else b.math("ADD", hgt, term)
            if h < 0:
                g = b.math("MULTIPLY", m, -h)
                groove = g if groove is None else b.math("MAXIMUM", groove, g)
        mb = b.node("ShaderNodeBump", Strength=1.0, Distance=0.006)
        b.set(mb.inputs["Height"], hgt)
        b.l.new(normal, mb.inputs["Normal"])
        normal = mb.outputs["Normal"]
        dark = b.mix(b.math("MULTIPLY", groove, 0.45), bsdf.inputs["Base Color"].links[0].from_socket,
                     (base[0] * 0.62, base[1] * 0.45, base[2] * 0.40, 1.0))
        b.l.new(dark, bsdf.inputs["Base Color"])
    b.l.new(normal, bsdf.inputs["Normal"])
    return mat
