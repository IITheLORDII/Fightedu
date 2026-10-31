#!/usr/bin/env python3
"""Uygulamanın yeni akışının web önizlemesi ("FightEdu Antrenman Koçu" sayfası).

İçerik (dallar, hareketler, programlar, dinlenme günü) app/src/main/assets/content'ten okunur ve
app_preview.html şablonuna gömülür. Çıktı: tools/render3d/build/preview/program/index.html
Sayfa; video/<id>.mp4, poster/<id>.webp, hero/<dal>.webp ve emblem.svg dosyalarını göreli yoldan yükler.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
CONTENT = os.path.join(ROOT, "app", "src", "main", "assets", "content")
OUT = os.path.join(ROOT, "tools", "render3d", "build", "preview", "program", "index.html")


def load(name):
    with open(os.path.join(CONTENT, name), encoding="utf-8") as fh:
        return json.load(fh)


SPRITE_RATE = 24000
SPRITE_PARTS = 3


def make_sprites(clips_dir):
    """Web önizlemesi için klipleri birkaç MP3 dosyasında birleştirir (sayfa dosya sayısı sınırlı; Safari Ogg
    çalmayabilir). Dönüş: {"files": [...], "map": {id: [dosya, başlangıç_sn, süre_sn]}}"""
    import subprocess
    ids = sorted(f[:-4] for f in os.listdir(clips_dir) if f.endswith(".ogg"))
    pcm = {}
    for cid in ids:
        pcm[cid] = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(clips_dir, cid + ".ogg"), "-f", "s16le",
                                   "-ac", "1", "-ar", str(SPRITE_RATE), "-"], capture_output=True, check=True).stdout
    total = sum(len(b) for b in pcm.values())
    gap = b"\0\0" * int(SPRITE_RATE * 0.12)
    out_dir = os.path.join(os.path.dirname(OUT), "websprites")  # assets/voice bağlantısına yazma
    os.makedirs(out_dir, exist_ok=True)
    files, mapping, part, buf = [], {}, 0, bytearray()

    def flush():
        name = f"websprites/sprite_{len(files)}.mp3"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ac", "1", "-ar", str(SPRITE_RATE), "-i", "-",
                        "-c:a", "libmp3lame", "-b:a", "40k", os.path.join(os.path.dirname(OUT), name)],
                       input=bytes(buf), check=True)
        files.append(name)

    for cid in ids:
        if len(buf) > total / SPRITE_PARTS and len(files) < SPRITE_PARTS - 1:
            flush()
            buf = bytearray()
        start = len(buf) / 2 / SPRITE_RATE
        buf += pcm[cid]
        mapping[cid] = [len(files), round(start, 3), round(len(pcm[cid]) / 2 / SPRITE_RATE, 3)]
        buf += gap
    flush()
    return dict(files=files, map=mapping)


def main():
    sports = load("sports.json")
    files = ["general"] + [s["id"] for s in sports]
    moves = {}
    for f in dict.fromkeys(files):
        for m in load(f"moves_{f}.json"):
            moves[m["id"]] = {k: m[k] for k in ("name", "sport", "category", "description", "steps", "tip", "call") if k in m}
    programs = {s["id"]: load(f"training_{s['id']}.json") for s in sports}
    clips_dir = os.path.join(ROOT, "app", "src", "main", "assets", "voice", "clips")
    recorded = os.path.isdir(clips_dir) and any(f.endswith(".ogg") for f in os.listdir(clips_dir))
    sprite = make_sprites(clips_dir) if recorded else None
    data = dict(sports=sports, moves=moves, programs=programs, rest=load("rest_day.json"), voiceRecorded=recorded,
                voiceExt="ogg", voiceSprite=sprite)
    with open(os.path.join(HERE, "app_preview.html"), encoding="utf-8") as fh:
        html = fh.read()
    html = html.replace("/*__DATA__*/{}", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(OUT, round(len(html.encode()) / 1024), "KB")


if __name__ == "__main__":
    main()
