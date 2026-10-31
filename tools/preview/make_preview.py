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


def main():
    sports = load("sports.json")
    files = ["general"] + [s["id"] for s in sports]
    moves = {}
    for f in dict.fromkeys(files):
        for m in load(f"moves_{f}.json"):
            moves[m["id"]] = {k: m[k] for k in ("name", "sport", "category", "description", "steps", "tip") if k in m}
    programs = {s["id"]: load(f"training_{s['id']}.json") for s in sports}
    clips_dir = os.path.join(ROOT, "app", "src", "main", "assets", "voice", "clips")
    web_dir = os.path.join(ROOT, "tools", "render3d", "build", "preview", "program", "voice", "clips_web")
    recorded = os.path.isdir(clips_dir) and any(f.endswith(".ogg") for f in os.listdir(clips_dir))
    data = dict(sports=sports, moves=moves, programs=programs, rest=load("rest_day.json"), voiceRecorded=recorded,
                voiceExt="ogg")
    with open(os.path.join(HERE, "app_preview.html"), encoding="utf-8") as fh:
        html = fh.read()
    html = html.replace("/*__DATA__*/{}", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(OUT, round(len(html.encode()) / 1024), "KB")


if __name__ == "__main__":
    main()
