# Koç sesi otomatik dinleme raporu

Her klip faster-whisper (small) ile yazıya döküldü ve okunması istenen metinle karşılaştırıldı. Puan: boşluksuz karakter hata oranı (ASR rakamları okunuşa çevrilir); metinde olmayan bir tekrar ya da aykırı süre +1. ASR da yanılabilir: listedekiler kulakla kontrol edilmeli.

1301 klip, ort. hata 0.049, yeniden kaydedilen 23, hâlâ eşiği (0.2) aşan 3 (tekrar: 0, süre: 0)

## Eşiği aşanlar

| puan | neden | metin | duyulan |
|---|---|---|---|
| 0.25 | - | Eğil! | eğil / İYİL |
| 0.23 | - | Yürüyüş duruşu! | Yürüyüştür şu. |
| 0.21 | - | Tempoyu düşürme! | Tempo yedişirme. |

## Yeniden kaydedilenler

| önce | sonra | metin | önce duyulan |
|---|---|---|---|
| 0.60 | 0.00 | Köprü! | Kıbrı! |
| 0.52 | 0.05 | Gün on üç. Önce ısınıyoruz. | Gün 13.09. |
| 0.50 | 0.00 | Dal! | Dol. / Dağıl. |
| 0.40 | 0.00 | Savun! | Sabın. |
| 0.37 | 0.00 | Üçüncü tur. skuat, başla! | İçindir tuş, skuat, başna. |
| 0.37 | 0.05 | Sıradaki raunt: Düz Diz. | Sol da direk iraunt, düz dis. |
| 0.32 | 0.08 | Bugünün konusu: zirve devresi. | Bugün konusu, sol direk ve devresi. |
| 0.32 | 0.09 | Her tekrarda yön değiştir. | Her tek arada yondayıştır. |
| 0.31 | 0.04 | Göğsünü dik, bakışını ileri tut. | Ghost in a dick, akışına ileri tut. |
| 0.31 | 0.23 | Yürüyüş duruşu! | Yürüyüştür şo. |
| 0.30 | 0.09 | Sıradaki raunt: Tekme Bloğu. | Sürat-e kirjant, tekme blo. |
| 0.30 | 0.20 | Skuat, otuz saniye. Başla! | Skuat, otostanem, başla! |
| 0.29 | 0.13 | Form devresi: börpi ve skuat. Hız değil, kontrol. | Fondesli, burpi ve skuat, hızdayın kontrol. |
| 0.28 | 0.07 | Bugünün konusu: kardiyo fırtınası. | Bugün konusu kardioförtünasyon. |
| 0.26 | 0.00 | Tebrikler! Gün on bir tamamlandı. | Teplikler gün 11.00 tamamlandı. |
| 0.25 | 0.06 | Sol kroşe! | Sol kroşe. / soğuk röşen. |
| 0.22 | 0.13 | Skuat, kırk beş saniye. Başla! | Skuat kürpestaniye başla. |
| 0.22 | 0.19 | Bir bacağını diğerinin altından öne fırlat. | Bir bacaned yerin altından önü fırlat. |
| 0.21 | 0.16 | Dinlen, kırk beş saniye. | Dinlen, kutbe saniye. / Dinlen, Kütbe Saniye. |
| 0.21 | 0.13 | Form devresi: Mekik ve Plank. Hız değil, kontrol. | Pondiversit, mikik ve plank, hız değil, kontrol. |
| 0.21 | 0.12 | Ritmi koru, nefesini düzenle. | Ritmi kro, nefesine cüzende. |
| 0.21 | 0.00 | Bugünün konusu: yerden çıkış. | Bugün konusuyla yerden çıkış. |
| 0.10 | 0.00 | Skuat, başla! | Skuat başla. / Squad Bashla. |
