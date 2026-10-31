"""Her dal için koyu fonlu, dikey "kahraman" görseli (açılış, hoş geldin ve dal seçimi ekranları).

Hareket videolarıyla aynı sahne kurulumu (MoveRenderer) kullanılır; yalnızca kadraj dikey, fon koyu ve kenar ışığı
dalın rengine boyanır. Çıktı: app/src/main/assets/hero/<dal>.webp
Kullanım: python render_heroes.py [--only boxing ...] [--samples 96] [--preview]
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import render_moves as rm  # noqa: E402
import retarget  # noqa: E402
import studio  # noqa: E402
from character import Character  # noqa: E402
from shading import srgb  # noqa: E402

# dal -> (hareket, kare (None: video kapak karesi), kenar ışığı rengi)
HEROES = {
    "boxing": ("box_cross", None, "#FF3B30"),
    "kickboxing": ("kb_high_kick", None, "#2F7BFF"),
    "wrestling": ("wr_double_leg", None, "#34C759"),
    "taekwondo": ("tkd_dollyo_chagi", None, "#AF52DE"),
    "general": ("gen_burpee", None, "#FF9500"),
}
DARK = dict(floor="#23262C", wall="#0F1115")
OUT = os.path.normpath(os.path.join(HERE, "..", "..", "app", "src", "main", "assets", "hero"))


def render_hero(sport, samples, out_dir, width, height):
    from generate import MOVES
    mid, frame, rim_color = HEROES[sport]
    mv = MOVES[mid]
    # dikey kadraj ve koyu fon: MoveRenderer modül sabitlerini kurulum sırasında okur
    rm.WIDTH, rm.HEIGHT = width, height
    rm.STYLE[mv.sport] = dict(rm.STYLE[mv.sport], **DARK)
    r = rm.MoveRenderer(mid, mv, samples=samples)
    r.build()
    import bpy
    bpy.context.scene.camera.data.lens *= 0.9  # biraz daha geniş kadraj: ayaklar ve tekme payı
    for ob in bpy.data.objects:
        if ob.type == "LIGHT" and ob.name.startswith("rim"):
            ob.data.color = srgb(rim_color)[:3]
            ob.data.energy *= 2.2
        elif ob.type == "LIGHT" and ob.name.startswith("fill"):
            ob.data.energy *= 0.55
    t = r.poster_frame() if frame is None else frame
    fdir = os.path.join(HERE, "build", "hero_frames", sport)  # PNG'ler asset klasörüne girmesin
    r.render(fdir, [t])
    png = os.path.join(fdir, f"{t:04d}.png")
    webp = os.path.join(out_dir, f"{sport}.webp")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", png, "-c:v", "libwebp", "-quality", "82", webp],
                   check=True)
    return webp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--samples", type=int, default=96)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--width", type=int, default=900)
    ap.add_argument("--height", type=int, default=1200)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    studio.reset_scene()
    retarget.configure_skeleton(retarget.body_dims(Character("probe", shape=rm.FIGHTER_SHAPE)))
    for sport in args.only or list(HEROES):
        print(sport, "->", render_hero(sport, args.samples, args.out, args.width, args.height), flush=True)


if __name__ == "__main__":
    main()
