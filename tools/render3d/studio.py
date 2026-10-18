"""Stüdyo: render ayarları, ışıklar, fon/zemin ve kamera."""
import math

import bpy
from mathutils import Vector

from character import simple_material, srgb


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    return scene


def setup_render(width=640, height=512, samples=48, fps=30):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.02
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    scene.cycles.max_bounces = 6
    scene.cycles.diffuse_bounces = 3
    scene.cycles.glossy_bounces = 2
    scene.cycles.transmission_bounces = 2
    scene.cycles.transparent_max_bounces = 4
    scene.cycles.caustics_reflective = False
    scene.cycles.caustics_refractive = False
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.fps = fps
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Punchy"
    scene.render.threads_mode = "AUTO"
    # karelerde yalnızca poz değişiyor: BVH/gölgelendirici verisi kareler arasında korunur
    scene.render.use_persistent_data = True


def world(color="#E9ECEF", strength=0.55):
    w = bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = srgb(color)
    bg.inputs["Strength"].default_value = strength


def area_light(name, loc, target, power, size, color=(1.0, 1.0, 1.0)):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = power
    data.size = size
    data.color = color
    ob = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return ob


def lights(center=(0.0, 0.0, 1.0), key_dir=(-1.0, -1.3, 0.9)):
    """Üç nokta: önden-yandan yumuşak ana ışık, karşı taraftan dolgu, arkadan kenar ışığı."""
    c = Vector(center)
    kd = Vector(key_dir).normalized()
    key = area_light("key", c + kd * 4.0, c, 1100.0, 1.6, (1.0, 0.96, 0.92))
    fd = Vector((-key_dir[0] * 0.2 + 1.0, key_dir[1], 0.3)).normalized()
    fill = area_light("fill", c + fd * 4.5, c, 160.0, 3.0, (0.92, 0.96, 1.0))
    rim = area_light("rim", c + Vector((0.6, 3.2, 1.4)), c + Vector((0, 0, 0.2)), 650.0, 1.4)
    return key, fill, rim


def backdrop(floor_color="#D9D6D0", wall_color="#EEF0F2", radius=8.0):
    """Sonsuz fon: zemin + kıvrımlı arka duvar (tek parça)."""
    import bmesh
    me = bpy.data.meshes.new("backdrop")
    bm = bmesh.new()
    # profil: zemin (y: -radius..2), kıvrım (r=1.5), duvar (z: 1.5..6)
    prof = []
    for i in range(0, 9):
        prof.append((-radius + i * (radius + 3.0) / 8.0, 0.0))
    for i in range(1, 9):
        a = math.radians(90.0 * i / 8.0)
        prof.append((3.0 + 1.5 * math.sin(a), 1.5 - 1.5 * math.cos(a)))
    for i in range(1, 5):
        prof.append((4.5, 1.5 + i * 1.5))
    xs = [-radius * 1.5, radius * 1.5]
    rows = []
    for y, z in prof:
        rows.append([bm.verts.new((x, y, z)) for x in xs])
    for a, b in zip(rows, rows[1:]):
        bm.faces.new((a[0], a[1], b[1], b[0]))
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new("backdrop", me)
    bpy.context.scene.collection.objects.link(ob)
    mat = bpy.data.materials.new("backdrop_mat")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    # zeminden duvara renk geçişi (yüksekliğe göre)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = srgb(floor_color)
    ramp.color_ramp.elements[1].position = 0.35
    ramp.color_ramp.elements[1].color = srgb(wall_color)
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.85
    ob.data.materials.append(mat)
    return ob


def camera(location, target, lens=70.0, name="cam"):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.sensor_width = 36.0
    ob = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = location
    d = Vector(target) - Vector(location)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = ob
    return ob


__all__ = ["reset_scene", "setup_render", "world", "lights", "backdrop", "camera", "simple_material"]
