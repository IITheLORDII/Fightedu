#!/bin/bash
# Koçun efekt sesleri (ffmpeg sinüs üreteciyle): gong (çalışma başı), zil (dinlenme), bip (3-2-1), bitiş.
set -e
OUT=$(cd "$(dirname "$0")/../../app/src/main/assets/voice" && pwd)
enc="-ac 1 -ar 48000 -c:a libopus -b:a 48k"
# gong: alçak temel + harmonikler, üstel sönüm
ffmpeg -v error -y -f lavfi -i "aevalsrc='0.55*exp(-2.6*t)*(sin(2*PI*196*t)+0.6*sin(2*PI*392.7*t)+0.35*sin(2*PI*588*t)+0.2*sin(2*PI*989*t))':s=48000:d=1.6" -af "afade=t=in:d=0.004,volume=0.9" $enc "$OUT/fx_gong.ogg"
# dinlenme zili: iki tonlu yumuşak "ding-dong"
ffmpeg -v error -y -f lavfi -i "aevalsrc='0.5*exp(-5*t)*sin(2*PI*988*t)*lt(t,0.45)+0.5*exp(-5*(t-0.42))*sin(2*PI*784*t)*gte(t,0.42)':s=48000:d=1.2" -af "afade=t=in:d=0.004" $enc "$OUT/fx_bell.ogg"
# geri sayım bipi
ffmpeg -v error -y -f lavfi -i "aevalsrc='0.6*sin(2*PI*1046*t)':s=48000:d=0.13" -af "afade=t=in:d=0.005,afade=t=out:st=0.10:d=0.03" $enc "$OUT/fx_beep.ogg"
# bitiş: yükselen üçlü
ffmpeg -v error -y -f lavfi -i "aevalsrc='0.45*(sin(2*PI*523*t)*between(t,0,0.18)+sin(2*PI*659*t)*between(t,0.18,0.36)+(sin(2*PI*784*t)+0.5*sin(2*PI*1046*t))*exp(-1.8*(t-0.36))*gte(t,0.36))':s=48000:d=1.6" -af "afade=t=in:d=0.004" $enc "$OUT/fx_finish.ogg"
ls -la "$OUT"/fx_*.ogg
