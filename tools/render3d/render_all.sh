#!/usr/bin/env bash
# Tüm hareketleri render edip app/src/main/assets/{video,poster} altına yazar (saatler sürer; kaldığı yerden devam eder).
# Kullanım: tools/render3d/render_all.sh [hareket_id ...]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="${PYTHON:-$HERE/.venv/bin/python}"
export MPFB_DATA="${MPFB_DATA:-$HERE/assets/mpfb2}"
if [ "$#" -gt 0 ]; then
  exec "$PY" "$HERE/render_moves.py" --only "$@"
fi
exec "$PY" "$HERE/render_moves.py"
