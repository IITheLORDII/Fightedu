#!/usr/bin/env python3
"""FightEdu Lottie animasyon üreticisi.

Her hareket (moves.py) eklem açılarıyla tanımlanmış anahtar pozlardan oluşur. Bu script
pozları hacimli bir figüre (body.py) ve gerekirse hedefe – kum torbası ya da antrenman
partneri – (props.py) dönüştürüp app/src/main/assets/lottie/<move_id>.json olarak yazar.

Kullanım:  python3 tools/lottie_gen/generate.py [--out DIR] [--only move_id ...] [--check-content]
Tasarımcı yapımı bir Lottie dosyası aynı isimle assets/lottie altına konarak kullanılabilir.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from body import OUTFITS, PARTNER_OUTFITS, build_figure  # noqa: E402
from moves import BOX, KB, MOVES, TKD_GUARD, WR  # noqa: E402
from props import (bag_layers, explicit_hits, find_hits, floor_layers, impact_layers,  # noqa: E402
                   reach_profile, shadow_layer)
from rig import (FPS, H, POSE_KEYS, W, LayerBuilder, P, animated, dense_hip_track, static,  # noqa: E402
                 transform)

DEFAULT_OPP_BASE = {"boxing": BOX, "kickboxing": KB, "wrestling": WR, "taekwondo": TKD_GUARD}
FLOOR_COLORS = {"wrestling": "#F2D9A6", "taekwondo": "#C8E6C9"}  # minder renkleri

# Figürün kalça x konumu (hedefe göre); moves.M(x=...) kaydırması eklenir.
FIGURE_X = {None: 250, "bag": 165, "long_bag": 165, "opponent": 175, "opponent_left": 330}


def full_keys(move_id, base, raw_keys, dur):
    keys = [(f, P(base, **ov)) for f, ov in raw_keys]
    for f, pose in keys:
        missing = [k for k in POSE_KEYS if k not in pose]
        if missing:
            raise ValueError(f"{move_id}: frame {f} eksik anahtarlar {missing}")
    if keys[0][0] != 0:
        raise ValueError(f"{move_id}: ilk keyframe 0 olmalı")
    if keys[-1][0] != dur:
        keys.append((dur, keys[0][1]))
    return keys


def detect_hits(spec, keys, base_x, dur, direction):
    if spec.get("hits"):
        return explicit_hits(keys, base_x, spec["hits"], direction)
    return find_hits(reach_profile(keys, base_x, dur, direction))


def build_move(move_id, spec):
    sport = spec["sport"]
    dur = spec["dur"]
    target = spec.get("target")
    keys = full_keys(move_id, spec["base"], spec["keys"], dur)
    base_x = FIGURE_X[target] + spec.get("x_shift", 0)

    lb = LayerBuilder(dur)
    fig_hip = dense_hip_track(keys, base_x)
    fig = build_figure(lb, keys, base_x, OUTFITS[sport], fig_hip, name="fig")
    top, bottom = [], []          # figürün üstünde / altında çizilecek katmanlar
    shadows = [shadow_layer(lb, fig_hip)]

    if target in ("bag", "long_bag"):
        hits = detect_hits(spec, keys, base_x, dur, 1)
        x_left = min(r for _, r, _, _ in hits) - 4
        bottom += bag_layers(lb, x_left, hits, dur, long_bag=(target == "long_bag"))
        top += impact_layers(lb, hits, dur)
    elif target in ("opponent", "opponent_left"):
        direction = -1 if target == "opponent_left" else 1
        opp_base = spec.get("opp_base") or DEFAULT_OPP_BASE[sport]
        opp_keys = full_keys(move_id + "/opp", opp_base, spec.get("opp") or [(0, {})], dur)
        shift = [(0, [0, 0, 0]), (dur, [0, 0, 0])]
        attack = spec.get("opp_dist") is None
        if attack:
            # Rakip vuruşun ulaştığı yerde durur; darbede geri sarsılır.
            hits = detect_hits(spec, keys, base_x, dur, direction)
            contact = min(r for _, r, _, _ in hits)
            opp_x = direction * (contact + 16)
            shift = [(0, [0, 0, 0])]
            for i, (f, *_r) in enumerate(hits):
                nxt = hits[i + 1][0] if i + 1 < len(hits) else dur
                for kf in [(f, [0, 0, 0]), (f + 3, [9 * direction, 0, 0]), (f + 14, [0, 0, 0])]:
                    if kf[0] < nxt and kf[0] < dur:
                        shift.append(kf)
            shift.append((dur, [0, 0, 0]))
            shift = sorted({f: v for f, v in shift}.items())
            top += impact_layers(lb, hits, dur)
        else:
            opp_x = base_x + direction * spec["opp_dist"]

        mirrored = direction == 1
        local_x = W - opp_x if mirrored else opp_x
        opp_hip = dense_hip_track(opp_keys, local_x)
        shift_null = lb.add("opp_shift", 3, transform(animated(shift, 3), static(0)))
        mirror_null = lb.add("opp_mirror", 3, transform(static([W, 0, 0] if mirrored else [0, 0, 0]), static(0),
                                                        s=static([-100 if mirrored else 100, 100, 100])),
                             parent=shift_null)
        opp = build_figure(lb, opp_keys, local_x, PARTNER_OUTFITS[sport], opp_hip, parent=mirror_null, name="opp")
        world_hip = [(f, [W - v[0] if mirrored else v[0], v[1], 0]) for f, v in opp_hip]
        shadows.append(shadow_layer(lb, world_hip))
        # Savunma hareketlerinde saldıran rakibin kolu/bacağı görünsün diye rakip üstte.
        if attack:
            bottom += opp + [shift_null, mirror_null]
        else:
            top += opp + [shift_null, mirror_null]

    floor = floor_layers(lb, FLOOR_COLORS.get(sport, "#DCE2E6"))
    order = top + fig + bottom + shadows + [floor]
    layers = [lb.by_ind(i) for i in order]
    assert len(layers) == len(lb.layers), f"{move_id}: çizim sırasında eksik katman"

    return {
        "v": "5.7.4", "fr": FPS, "ip": 0, "op": dur, "w": W, "h": H, "nm": move_id, "ddd": 0,
        "assets": [], "layers": layers, "markers": [],
    }


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    default_out = os.path.normpath(os.path.join(here, "..", "..", "app", "src", "main", "assets", "lottie"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=default_out)
    parser.add_argument("--only", nargs="*")
    parser.add_argument("--check-content", action="store_true",
                        help="assets/content altındaki tüm hareketlerin animasyonu var mı kontrol et")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    ids = args.only or sorted(MOVES)
    for mid in ids:
        data = build_move(mid, MOVES[mid])
        with open(os.path.join(args.out, f"{mid}.json"), "w", encoding="utf-8") as fh:
            json.dump(data, fh, separators=(",", ":"))
    print(f"{len(ids)} animasyon yazıldı -> {args.out}")

    if args.check_content:
        content_dir = os.path.join(os.path.dirname(args.out), "content")
        missing = []
        for name in sorted(os.listdir(content_dir)):
            if name.startswith("moves_"):
                with open(os.path.join(content_dir, name), encoding="utf-8") as fh:
                    missing += [mv["id"] for mv in json.load(fh) if mv["id"] not in MOVES]
        if missing:
            print("Animasyonu olmayan hareketler:", ", ".join(missing))
            sys.exit(1)
        print("Tüm hareketlerin animasyonu mevcut.")


if __name__ == "__main__":
    main()
