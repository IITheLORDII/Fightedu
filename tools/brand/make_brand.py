#!/usr/bin/env python3
"""FightEdu amblemi: kalkan + yüksek tekme atan dövüşçü silueti.

Siluet, 3B dövüşçünün (kb_high_kick, 20. kare, yandan) render'ından potrace ile çıkarıldı
(trace_silhouette.py -> silhouette.txt: "genişlik yükseklik\\nSVG yolu").
Bu betik aynı tasarımdan şunları üretir:
  tools/brand/emblem.svg                       (önizleme / web)
  app/src/main/res/drawable/ic_emblem.xml      (uygulama içi amblem)
  app/src/main/res/drawable/ic_splash_emblem.xml (Android 12+ açılış ekranı ikonu, 192 dp daire içinde)
  app/src/main/res/drawable/ic_launcher_foreground.xml / ic_launcher_monochrome.xml (uyarlanabilir ikon)
Kullanım: python3 tools/brand/make_brand.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.normpath(os.path.join(HERE, "..", "..", "app", "src", "main", "res", "drawable"))

with open(os.path.join(HERE, "silhouette.txt")) as fh:
    _w, _h, SIL = fh.read().split(None, 2)
SIL_W, SIL_H = float(_w), float(_h)

DARK = "#0E1116"
RED_TOP, RED_BOTTOM = "#FF5A3C", "#B0121C"
SHIELD = "M256,26C326,26 392,40 446,66L446,246C446,352 372,432 256,484C140,432 66,352 66,246L66,66C120,40 186,26 256,26Z"
INNER = "M256,52C318,52 376,64 422,85L422,246C422,338 358,408 256,456C154,408 90,338 90,246L90,85C136,64 194,52 256,52Z"
SHINE = "M90,85C136,64 194,52 256,52C318,52 376,64 422,85L422,170C330,120 190,130 90,215Z"
STREAKS = [("M150,330L395,105", 10, 0.18), ("M175,360L400,150", 7, 0.12)]
SIL_SCALE = 372.0 / SIL_H
SIL_X, SIL_Y = 256 - SIL_W * SIL_SCALE * 0.47, 62.0


def svg():
    streaks = "".join(f'<path d="{d}" stroke="#FFFFFF" stroke-opacity="{a}" stroke-width="{w}" stroke-linecap="round"/>'
                      for d, w, a in STREAKS)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
<defs>
 <linearGradient id="red" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{RED_TOP}"/><stop offset="1" stop-color="{RED_BOTTOM}"/></linearGradient>
 <linearGradient id="shine" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFFFFF" stop-opacity="0.22"/><stop offset="0.55" stop-color="#FFFFFF" stop-opacity="0"/></linearGradient>
</defs>
<path d="{SHIELD}" fill="{DARK}"/>
<path d="{INNER}" fill="url(#red)"/>
<path d="{SHINE}" fill="url(#shine)"/>
<path d="{INNER}" fill="none" stroke="#FFFFFF" stroke-opacity="0.85" stroke-width="4"/>
{streaks}
<g transform="translate({SIL_X:.1f},{SIL_Y:.1f}) scale({SIL_SCALE:.4f})"><path d="{SIL}" fill="#FFFFFF"/></g>
</svg>
'''


def gradient(x1, y1, x2, y2, stops):
    s = "".join(f'\n                    <item android:offset="{o}" android:color="{c}" />' for o, c in stops)
    return f'''
            <aapt:attr name="android:fillColor">
                <gradient android:type="linear" android:startX="{x1}" android:startY="{y1}" android:endX="{x2}"
                    android:endY="{y2}">{s}
                </gradient>
            </aapt:attr>'''


def emblem_paths(mono=False):
    """512'lik görüntü alanında amblem yolları (VectorDrawable)."""
    if mono:
        return f'''
        <path android:fillColor="#FFFFFFFF" android:fillType="evenOdd"
            android:pathData="{SHIELD}{INNER}" />
        <group android:translateX="{SIL_X:.1f}" android:translateY="{SIL_Y:.1f}" android:scaleX="{SIL_SCALE:.4f}"
            android:scaleY="{SIL_SCALE:.4f}">
            <path android:fillColor="#FFFFFFFF" android:pathData="{SIL}" />
        </group>'''
    streaks = "".join(f'''
        <path android:strokeColor="#FFFFFFFF" android:strokeAlpha="{a}" android:strokeWidth="{w}"
            android:strokeLineCap="round" android:pathData="{d}" />''' for d, w, a in STREAKS)
    return f'''
        <path android:fillColor="#FF0E1116" android:pathData="{SHIELD}" />
        <path android:pathData="{INNER}">{gradient(256, 52, 256, 456, [(0, "#FFFF5A3C"), (1, "#FFB0121C")])}
        </path>
        <path android:pathData="{SHINE}">{gradient(90, 52, 422, 384, [(0, "#38FFFFFF"), (0.55, "#00FFFFFF")])}
        </path>
        <path android:strokeColor="#FFFFFFFF" android:strokeAlpha="0.85" android:strokeWidth="4"
            android:pathData="{INNER}" />{streaks}
        <group android:translateX="{SIL_X:.1f}" android:translateY="{SIL_Y:.1f}" android:scaleX="{SIL_SCALE:.4f}"
            android:scaleY="{SIL_SCALE:.4f}">
            <path android:fillColor="#FFFFFFFF" android:pathData="{SIL}" />
        </group>'''


def vector(size_dp, viewport, scale, comment, mono=False):
    off = (viewport - 512 * scale) / 2
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!-- {comment} (tools/brand/make_brand.py ile üretildi; elle düzenleme) -->
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:aapt="http://schemas.android.com/aapt"
    android:width="{size_dp}dp"
    android:height="{size_dp}dp"
    android:viewportWidth="{viewport}"
    android:viewportHeight="{viewport}">
    <group android:translateX="{off:.2f}" android:translateY="{off:.2f}" android:scaleX="{scale:.5f}"
        android:scaleY="{scale:.5f}">{emblem_paths(mono)}
    </group>
</vector>
'''


def write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("->", os.path.relpath(path, os.path.join(HERE, "..", "..")))


def main():
    write(os.path.join(HERE, "emblem.svg"), svg())
    write(os.path.join(RES, "ic_emblem.xml"), vector(160, 512, 1.0, "FightEdu amblemi"))
    # Android 12+ açılış ikonu: 288 dp alan, içerik 192 dp çaplı daireye sığmalı (amblem ~0.6)
    write(os.path.join(RES, "ic_splash_emblem.xml"), vector(288, 512, 0.6, "Açılış ekranı ikonu"))
    # uyarlanabilir ikon: 108 dp, güvenli alan 66 dp çaplı daire
    write(os.path.join(RES, "ic_launcher_foreground.xml"), vector(108, 108, 0.128, "Uygulama ikonu ön katmanı"))
    write(os.path.join(RES, "ic_launcher_monochrome.xml"),
          vector(108, 108, 0.128, "Tek renk (temalı) uygulama ikonu", mono=True))


if __name__ == "__main__":
    main()
