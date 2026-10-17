#!/usr/bin/env python3
"""FightEdu Lottie animasyon üreticisi (3B iskelet + kamera projeksiyonu).

Hareketler (moves.py) 3B anahtar pozlarla tanımlanır: kalça/göğüs dönüşü, baş bakışı,
el ve ayak hedefleri. Dirsek ve dizler IK ile çözülür; figür her karede seçilen kamera
açısından 2B'ye çizilir (figure.py) ve Lottie JSON'a dönüştürülür (scene.py).

Kullanım:  python3 tools/lottie_gen/generate.py [--out DIR] [--only move_id ...] [--check-content]
Tasarımcı yapımı bir Lottie dosyası aynı isimle assets/lottie altına konarak kullanılabilir
(o hareketi moves.py'den kaldırın).
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
    default_out = os.path.normpath(os.path.join(here, "..", "..", "app", "src", "main", "assets", "lottie"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=default_out)
    parser.add_argument("--only", nargs="*")
    parser.add_argument("--check-content", action="store_true",
                        help="assets/content altındaki tüm hareketlerin animasyonu var mı kontrol et")
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
        content_dir = os.path.join(os.path.dirname(args.out), "content")

        def covered(move_id):
            # tasarımcı yapımı dosyalar moves.py'de yer almaz, assets/lottie altında durur
            return move_id in MOVES or os.path.exists(os.path.join(default_out, f"{move_id}.json"))

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
