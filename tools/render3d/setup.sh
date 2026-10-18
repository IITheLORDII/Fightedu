#!/usr/bin/env bash
# Gerçekçi render ortamı: Blender'ın Python modülü (bpy) ve MakeHuman (MPFB2, CC0) gövde verisi.
# bpy 5.2 yalnızca Python 3.13 ile çalışır. Kullanım: tools/render3d/setup.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="${PYTHON:-python3.13}"
"$PY" -m venv "$HERE/.venv"
"$HERE/.venv/bin/pip" install -q "bpy==5.2.2" numpy
# MPFB2 gövde, şekil hedefleri, iskelet ve ağırlıklar (CC0) anny paketinin içinde dağıtılıyor
TMP="$(mktemp -d)"
"$HERE/.venv/bin/pip" download -q --no-deps "anny==0.6.1" -d "$TMP"
rm -rf "$HERE/assets/mpfb2"
mkdir -p "$HERE/assets"
"$HERE/.venv/bin/python" - "$TMP"/anny-0.6.1-py3-none-any.whl "$HERE/assets" <<'PY'
import os, sys, zipfile
whl, out = sys.argv[1], sys.argv[2]
prefix = "anny/data/mpfb2/"
with zipfile.ZipFile(whl) as z:
    for name in z.namelist():
        if name.startswith(prefix) and not name.endswith("/"):
            target = name[len(prefix):]
            if target.split("/")[0] in ("3dobjs", "mesh_metadata", "rigs", "targets", "LICENSE.md"):
                dest = f"{out}/mpfb2/{target}"
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with z.open(name) as src, open(dest, "wb") as dst:
                    dst.write(src.read())
PY
rm -rf "$TMP"
echo "Hazır. Örnek: $HERE/.venv/bin/python $HERE/render_moves.py --only box_jab"
