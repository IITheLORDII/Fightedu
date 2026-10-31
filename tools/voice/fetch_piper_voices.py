#!/usr/bin/env python3
"""Piper'ın resmi ses listesinden (rhasspy/piper-voices/voices.json) tüm Türkçe sesleri indirir.
Model: tools/voice/build/piper/<ses>.onnx(.json); lisans kartları: tools/voice/samples/<ses>.MODEL_CARD.md"""
import json
import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
OUT = os.path.join(HERE, "build", "piper")
CARDS = os.path.join(HERE, "samples")


def get(url):
    with urllib.request.urlopen(url + "?download=true", timeout=120) as r:
        return r.read()


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(CARDS, exist_ok=True)
    voices = json.loads(get(BASE + "voices.json"))
    tr = {k: v for k, v in voices.items() if k.startswith("tr_")}
    print("Türkçe sesler:", ", ".join(f"{k} ({v.get('quality')}, {v.get('num_speakers', 1)} konuşmacı)" for k, v in tr.items()))
    for key, v in tr.items():
        for path in v["files"]:
            name = os.path.basename(path)
            if name.endswith(".onnx") or name.endswith(".onnx.json"):
                dest = os.path.join(OUT, name)
            elif name == "MODEL_CARD":
                dest = os.path.join(CARDS, f"{key}.MODEL_CARD.md")
            else:
                continue
            with open(dest, "wb") as fh:
                fh.write(get(BASE + path))
            print("  ", dest, os.path.getsize(dest))


if __name__ == "__main__":
    main()
