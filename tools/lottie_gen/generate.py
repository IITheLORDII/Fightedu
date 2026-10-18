#!/usr/bin/env python3
"""FightEdu hareket tanımları: hızlı 2B Lottie önizleme ve içerik kapsam kontrolü.

Hareketler (moves.py) 3B anahtar pozlarla tanımlanır: kalça/göğüs dönüşü, baş bakışı, el ve ayak
hedefleri. Dirsek ve dizler IK ile çözülür. Uygulamadaki gerçekçi videolar aynı tanımlardan
tools/render3d/render_moves.py ile üretilir; bu betik ise saniyeler içinde 2B Lottie önizlemesi
(varsayılan: tools/lottie_gen/build/lottie) üretir ve her içerik hareketinin tanımlı olduğunu denetler.

Kullanım:  python3 tools/lottie_gen/generate.py [--out DIR] [--only move_id ...] [--check-content]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from moves import BOXING, GENERAL, KICKBOXING, TAEKWONDO, WRESTLING  # noqa: E402
from scene import build_move  # noqa: E402

MOVES = {**GENERAL, **BOXING, **KICKBOXING, **WRESTLING, **TAEKWONDO}


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    assets = os.path.normpath(os.path.join(here, "..", "..", "app", "src", "main", "assets"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=os.path.join(here, "build", "lottie"))
    parser.add_argument("--content", default=os.path.join(assets, "content"))
    parser.add_argument("--only", nargs="*")
    parser.add_argument("--check-content", action="store_true",
                        help="assets/content altındaki tüm hareketler tanımlı mı kontrol et")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    ids = args.only or sorted(MOVES)
    total = 0
    for mid in ids:
        data = build_move(mid, MOVES[mid])
        text = json.dumps(data, separators=(",", ":"), allow_nan=False)
        total += len(text)
        with open(os.path.join(args.out, f"{mid}.json"), "w", encoding="utf-8") as fh:
            fh.write(text)
    print(f"{len(ids)} animasyon yazıldı -> {args.out} ({total // 1024} KB)")

    if args.check_content:
        content_dir = args.content

        def covered(move_id):
            # gerçek çekim bir video konmuşsa hareketin moves.py'de tanımlı olması gerekmez
            return move_id in MOVES or os.path.exists(os.path.join(assets, "video", f"{move_id}.mp4"))

        missing = []
        for name in sorted(os.listdir(content_dir)):
            if name.startswith("moves_"):
                with open(os.path.join(content_dir, name), encoding="utf-8") as fh:
                    missing += [mv["id"] for mv in json.load(fh) if not covered(mv["id"])]
        if missing:
            print("Animasyonu olmayan hareketler:", ", ".join(missing))
            sys.exit(1)
        print("Tüm hareketlerin animasyonu mevcut.")


if __name__ == "__main__":
    main()
