# Koç sesi otomatik dinleme raporu

Her klip faster-whisper (small) ile yazıya döküldü ve okunması istenen metinle karşılaştırıldı. Puan: boşluksuz karakter hata oranı (ASR rakamları okunuşa çevrilir); metinde olmayan bir tekrar ya da aykırı süre +1. ASR da yanılabilir: listedekiler kulakla kontrol edilmeli.

1301 klip, ort. hata 0.049, yeniden kaydedilen 72, hâlâ eşiği (0.2) aşan 3 (tekrar: 1, süre: 0)

## Eşiği aşanlar

| puan | neden | metin | duyulan |
|---|---|---|---|
| 1.02 | tekrar | Sol, Sağ Direk: sağ direğin bitişinde ağırlık ön ayakta olur: bu, arka bacak tekmesi için yük oluşturur. | Sol, sağ direk, sağ direk'in bitişinde ağırlık ön ayakta olur. Bu, arka bacak tekmesi için yıkoluşturur. |
| 0.33 | - | Dal! | Dol. |
| 0.21 | - | Dinlen, kırk beş saniye. | Dinlen, kutbe saniye. |

## Yeniden kaydedilenler

| önce | sonra | metin | önce duyulan |
|---|---|---|---|
| yeni | 0.07 | Ellerinle rakibin başını ya da omuzlarını aşağı it. | - |
| yeni | 0.04 | Orta Tekme: tekme atan taraftaki kol dengeleme için aşağı ya da arkaya gidebilir, diğer el çenede. | - |
| yeni | 0.06 | Tekme atan taraftaki kol dengeleme için aşağı ya da arkaya gidebilir, diğer el çenede. | - |
| yeni | 0.07 | Dalış Savunması: ellerinle rakibin başını ya da omuzlarını aşağı it. | - |
| yeni | 0.00 | El Mücadelesi: rakibin bileğini kavra ve aşağı ya da yana çek. | - |
| yeni | 0.16 | Dalış, savunma ve yerden çıkış. | - |
| yeni | 0.03 | Yarın gün on altı: Saldırı ve Savunma. Dinç gel! | - |
| yeni | 0.04 | Elli on: dinlenme kısa, nefesini hareket sırasında düzenle. | - |
| yeni | 0.15 | Tekme, diz ve savunma, altı raunt. | - |
| yeni | 0.09 | Form ve sekiz raunt tekme: son raundu en iyi raundun yap. | - |
| yeni | 0.06 | Penetrasyon ve iki dizin arkası; baş yan tarafta, kalçayı sür. | - |
| yeni | 0.00 | Kırk beş on beş temposunda tüm istasyonlar; formu bozma. | - |
| yeni | 0.00 | Rakibin bileğini kavra ve aşağı ya da yana çek. | - |
| yeni | 0.07 | Dört yumruk ve savunma: komutlara anında cevap ver. | - |
| yeni | 0.05 | Yüksek Tekme: destek ayağında tam dön; gövde hafif geriye ya da yana açılır. | - |
| yeni | 0.06 | Destek ayağında tam dön; gövde hafif geriye ya da yana açılır. | - |
| yeni | 0.00 | Ön Duruş: ağırlığın yaklaşık üçte ikisi ön bacakta. | - |
| yeni | 0.14 | Bugünün konusu: saldırı ve savunma. | - |
| 2.00 | 0.00 | Sol sağ kroşe! | sol sağ kroşe, sol sağ kroşe. |
| 1.12 | 0.17 | Ön kolu dirsekten yaklaşık doksan derece bükerek yere paralel kaldır. | Ön kulu diğistekten yaklaşık 90 derece bir kere kere paralel kaldır. |
| 1.09 | 0.00 | Orta Blok: bloğu gövde dönüşüyle destekle. | Orta blok, blok, övde dönüşüyle destekle. |
| 1.04 | 1.02 | Sol, Sağ Direk: sağ direğin bitişinde ağırlık ön ayakta olur: bu, arka bacak tekmesi için yük oluşturur. | Sol, sağ direk, sağ direk'in bir dişinde ağırlık ön ayakta olur bu, arka bacak tekmesi için yük oluşturur. |
| 1.00 | 0.00 | Sağ kroşe! | Sağ kroşe. |
| 1.00 | 0.00 | Ön Tekme: ön tekme bir itme hareketidir; kalça ileri gitmezse güç olmaz. | Öntekme, öntekme bir itme hareketidir.  Kalça ileri gitmezse güç olmaz. |
| 0.71 | 0.00 | Ön tekme! | Antrenman. |
| 0.67 | 0.33 | Dal! | Dağıl. |
| 0.60 | 0.00 | Köprü! | Çöpür. |
| 0.57 | 0.00 | Gün on üç. Önce ısınıyoruz. | Gün 18.00 ınca ısınıyoruz. |
| 0.45 | 0.00 | Skuat, otuz saniye. Başla! | Kualat, oçasani, maşla. |
| 0.40 | 0.20 | Savun! | Sabon. |
| 0.40 | 0.10 | Börpi, başla! | Bir pi başlayın. |
| 0.39 | 0.00 | Gün yirmi yedi. Önce ısınıyoruz. | Gün yirmi yedi, öncelikle sners. |
| 0.37 | 0.04 | Duruşta, ellerini önde aktif tut. | Brüsta elinin önünde aktif tut. |
| 0.36 | 0.04 | Sıradaki raunt: Balta Tekmesi. | Süre dekir, hound, balt, tekme. |
| 0.36 | 0.00 | Tempoyu düşürme! | Tempo edişirmen. |
| 0.33 | 0.00 | Diz! | Dez. |
| 0.32 | 0.02 | Sağ direkten dönen gövdeyle ağırlığı ön ayağa al. | Saat direkten dönen gönleyle alı öner yaa av. |
| 0.32 | 0.10 | Sıradaki raunt: Düz Diz. | Direk irant, düz diz. |
| 0.31 | 0.19 | Hedef göğüs ortası. | Edef Kürsortası |
| 0.31 | 0.12 | Bugünün konusu: diz. | Bugün konusu bu. |
| 0.31 | 0.00 | Sıradaki: hit devresi. Dört tur, dört hareket. | Suna da ki hit every sit, dot tour, dot hareket. |
| 0.31 | 0.00 | Sık yapılan hata: ayağa kalkarken dik durmak. Buna dikkat et. | Sıkıya falan hata, ayak halkağa diktim bak, bunda dikkat et. |
| 0.30 | 0.17 | Gün on dört. Önce ısınıyoruz. | Gün 14 öncesini yorursun. |
| 0.30 | 0.03 | Sıradaki gün: Kardiyo Patlaması. Görüşmek üzere! | Sıradaki gün kardiopatlaması görüşmek üzere.  Güçmek üzere. |
| 0.29 | 0.00 | Dinlen, yirmi saniye. | Dinlen, Yemsenye. |
| 0.29 | 0.00 | Sıradaki: dördüncü tur, skuat. | Sıra da ki, doğru düğün dütör, skuat. |
| 0.29 | 0.14 | Şınavda dirsekler kırk beş derece, gövde tek parça. | Şanada disseklere kürt beştelecek o da tek parça. |
| 0.28 | 0.06 | Arka ayakla iterek kalçayı ileri taşı. | Arkayaklı, direk altı ileri taşı. |
| 0.28 | 0.14 | Sıradaki raunt: Savuşturma ve Blok. | Süredeki raunt, sol ştırmabe blok. |
| 0.27 | 0.14 | Her tekrarda yön değiştir. | Her tekrar da yönde istersin. |
| 0.27 | 0.15 | Blok bitti, iyi iş! Kırk beş saniye dinlen. | Blok bitti, iş, külpe saniyedinden. |
| 0.27 | 0.12 | Göğsünü dik, bakışını ileri tut. | Göğüsüne dik, okuşuna ileri tut. |
| 0.25 | 0.00 | Garda geri dön. | Garda get it on. |
| 0.25 | 0.04 | Gard al ve sürekli hareket et. | Gard, al, bez, direkte hareket et. |
| 0.25 | 0.00 | Sıradaki: dördüncü tur, Şınav. | Sredeki dördün jütlör şınav. |
| 0.25 | 0.05 | Güzel, vücudun ısınıyor. | Güzel, videodan ısınıyor. |
| 0.25 | 0.00 | Bugünün konusu: bir iki torba günü. | O günün konusu bir iki torbakıyla. |
| 0.24 | 0.10 | Sıradaki raunt: Seviye Değiştirme. | Sıradık yırağın seviyede iştirme. |
| 0.24 | 0.00 | Bitirici! Son bir gayret, tempoyu sonuna kadar koru. | bitirici, somge, gayret, tempoyu sonuna kadar korup.  Ondan... |
| 0.23 | 0.15 | Yürüyüş duruşu! | Yürüyüş Dörüşü. |
| 0.23 | 0.09 | Sıradaki: üçüncü tur, skuat. | Fıradaki uçuncu tor, skuat. |
| 0.22 | 0.00 | Bugünün konusu: final. | Bökenen konusu final. |
| 0.22 | 0.09 | Dizi hedefe doğrultup bacağı açarak ayak üstüyle vur. | Lizi hedefe doğrultup bacağı açarak ayak üşücüğüne boş. |
| 0.22 | 0.11 | Ön Duruş: kalça ve gövde öne dönük. | Öndürüş, kalça ve göğdüğüne dönük. |
| 0.22 | 0.17 | Dördüncü raunt, başla! | 4. raunt, hoşuna. |
| 0.22 | 0.13 | Skuat, kırk beş saniye. Başla! | Kuat kürtbeysanye. Başla. |
| 0.22 | 0.04 | Sıradaki: beşinci tur, börpi. | Sıradaki, peşinjitor berbi. |
| 0.21 | 0.14 | Seviye değiştir. | Tebiyye değiştir. |
| 0.21 | 0.05 | Sık yapılan hata: inişte dizi bükmek. Buna dikkat et. | Bu yuktaki yapılan hata inişte dizibikmek buna dikkat et. |
| 0.21 | 0.10 | Üçüncü tur. skuat, başla! | Bir çüncü tuş, skuat başla. |
| 0.21 | 0.21 | Dinlen, kırk beş saniye. | Dinlen, kürt, beysan, ye. |
| 0.21 | 0.00 | Gün beş: aktif dinlenme. | Gün beş aktiftin name. |
