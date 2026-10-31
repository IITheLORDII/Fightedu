# Koç sesi otomatik dinleme raporu

Her klip faster-whisper (small) ile yazıya döküldü ve okunması istenen metinle karşılaştırıldı. Puan: boşluksuz karakter hata oranı (ASR rakamları okunuşa çevrilir); metinde olmayan bir tekrar ya da aykırı süre +1. ASR da yanılabilir: listedekiler kulakla kontrol edilmeli.

1301 klip, ort. hata 0.068, yeniden kaydedilen 171, hâlâ eşiği (0.2) aşan 22 (tekrar: 0, süre: 0)

## Eşiği aşanlar

| puan | neden | metin | duyulan |
|---|---|---|---|
| 0.50 | - | Eğil! | İYİL |
| 0.50 | - | Sol kroşe! | soğuk röşen. |
| 0.41 | - | Dinlen, yirmi saniye. | Dinan Yemsenye. |
| 0.40 | - | Skuat, başla! | Quad Basla |
| 0.40 | - | Köprü! | Çöpre |
| 0.33 | - | Tekme + diz + savunma, altı raunt. | Tekme, diz da ka ba savunma altı round. |
| 0.33 | - | Dördüncü raunt, başla! | dördüncü rönt, hoşuna. |
| 0.31 | - | Yürüyüş duruşu! | Yürüyüş dönüşü. |
| 0.29 | - | Sıradaki: dördüncü tur, skuat. | Sıra da ki, derdini tutuş squat. |
| 0.25 | - | Sağ direk! | Sadirekk. |
| 0.25 | - | Garda geri dön. | Garda get it on. |
| 0.25 | - | Dördüncü tur. İp Atlama, başla! | 4. tuş ip atlama başla. |
| 0.25 | - | Blok! | Block. |
| 0.25 | - | Garda dön. | Garda done. |
| 0.24 | - | Dördüncü tur. Plank, başla! | 4. tur, plank başla. |
| 0.24 | - | Dördüncü tur. Şınav, başla! | 4. tur. Şınav başla. |
| 0.22 | - | Sağ direkten dönen gövdeyle ağırlığı ön ayağa al. | Saat direktan dönem görvdeyle ağırlığı unayar av. |
| 0.22 | - | Dalış + savunma + yerden çıkış. | Dalış Sabun Mablos yerden çıkış. |
| 0.21 | - | Tempoyu düşürme! | Tempo idişürme. |
| 0.21 | - | Sıradaki raunt: Düz Diz. | Sıra da ki don'tu, düz diz. |
| 0.21 | - | Form devresi: skuat ve Şınav. Hız değil, kontrol. | Pomdevesi, squad vs nav hız değil, kontrol. |
| 0.21 | - | Üçüncü tur. Şınav, başla! | 3. tur. Şınav başla. |

## Yeniden kaydedilenler

| önce | sonra | metin | önce duyulan |
|---|---|---|---|
| 3.43 | 0.14 | Üst blok! | Bir sonraki videoda görüşürüz. |
| 2.00 | 0.21 | Tempoyu düşürme! | ve Sermet'e izlediğiniz için teşekkürler. |
| 1.75 | 0.00 | Dinlen, otuz saniye. | Dinlen Otostanye.  Otostanye. |
| 1.54 | 0.09 | Sol sağ kroşe! | Sol star crochet. |
| 1.40 | 0.15 | Skuat, otuz saniye. Başla! | Skuat otusan ya başla.  Başla. |
| 1.33 | 0.17 | Duruşunu koru. | Duruşin okura. |
| 1.28 | 0.02 | Sık yapılan hata: dizlerin içe kapanması. Buna dikkat et. | sık yapılan hata dillerin içe kapanması. Buna dikkat et.  Buna dikkat et. |
| 1.28 | 0.03 | Yarın gün on bir: Dalış Karışık. Dinç gel! | Yarın gün 11 Dalış Karışık. Dinçi Gel.  Dinçi Gel. |
| 1.28 | 0.05 | Sık yapılan hata: ayak üstüyle vurmak. Buna dikkat et. | Sık yapılan hata ayak üstüyle vurmak buna dikkat et.  Buna dikkat et. |
| 1.28 | 0.00 | On saniye kaldı, dayan! | On saniye kaldı dayan.  Dayan. |
| 1.27 | 0.04 | Sık yapılan hata: kalçayı döndürmemek. Buna dikkat et. | Sık yapılan hata kalçayı döndürmemek, ona dikkat et.  Ona dikkat et. |
| 1.26 | 0.09 | Yarın gün altı: Sol, Sağ, Alçak Tekme. Dinç gel! | Yarın gün altı sol sağı alçak tekme, dinç ger.  Dinç ger. |
| 1.25 | 0.16 | Sık yapılan hata: sağ direk sırasında ön eli düşürmek. Buna dikkat et. | Sık yapılan hata, sağ direkt sırasında öneri düşürmek buna dikkat et.  Buna dikkat et. |
| 1.25 | 0.25 | Garda dön. | Garda done. |
| 1.24 | 0.00 | Sıradaki: Kondisyon. Üç tur, dört hareket. | Sıra da keyfini kondisyon 3-4 dört hareket. |
| 1.23 | 0.03 | Yarın gün on altı: Geri Tekme. Dinç gel! | Yarın gün 16 geri tekme.  Dinç gel.  Dinç gel. |
| 1.23 | 0.12 | Alt Blok: blok bittiğinde kol hafif bükülü kalır. | Alt block, block bittiğinde kol hafif bir türlü kalır.  Ama... |
| 1.14 | 0.05 | Bugünün konusu: sol kroşe. | Bu kanalıma abone olmayı unutmayın. |
| 1.11 | 0.00 | Kafa Kaçırma: küçük hareket = hızlı karşı atak. | Kafa kaçırma, küçük hareket, hızlı karşı atak.  Atak... |
| 1.02 | 0.00 | Ön Tekme: ön tekme bir itme hareketidir; kalça ileri gitmezse güç olmaz. | Öntekme, öntekme bir itme hareketidir.  Kalça ileri gitmez de güç olmaz. |
| 1.00 | 0.17 | Bugünün konusu: köprü. | Ogan and corn of soap chapter. |
| 1.00 | 0.00 | Son on saniye. | Son on saniye. |
| 1.00 | 0.00 | Diz! | DÜTH |
| 0.92 | 0.00 | Bugünün konusu: alt pozisyon. | Bu kanalıma abone olmayı unutmayın. |
| 0.77 | 0.31 | Yürüyüş duruşu! | Yerleştirişi'ye. |
| 0.75 | 0.15 | Sıradaki: beşinci raunt. | Söyle de keep pesting around. |
| 0.74 | 0.10 | İleri tekmeler ve form. | ileri tekmeler ve form.  Ağzı ileri tekme. |
| 0.60 | 0.40 | Skuat, başla! | Kuat Başla.  Boşta. |
| 0.59 | 0.15 | Bugünün konusu: saldırı + savunma. | Bu gün konusu, saadere producer var mı? |
| 0.55 | 0.05 | Şınav, elli saniye. Başla! | Şunaf Edithaniye başlayalım. |
| 0.52 | 0.14 | Sıradaki raunt: Sağ Kroşe. | Söyle deki rönt, sağa krosya. |
| 0.50 | 0.12 | Sağ kroşe! | Sağ kursu. |
| 0.50 | 0.00 | Sıradaki: üçüncü tur, Mekik. | Fıradakî, ütüncül tuzluğur mekîc. |
| 0.50 | 0.17 | Sıradaki: hit devresi. Dört tur, dört hareket. | sıradaki hit devresi. |
| 0.48 | 0.24 | Dördüncü tur. Plank, başla! | 3. tuş.  Pilan'k başlar. |
| 0.46 | 0.05 | Kroşe ile gövde arka bacak tekmesi için yüklenir. | Krosyede gördüğü de arka bir taktaki mesajı için yüklenmiş. |
| 0.46 | 0.04 | Her tekrarda yön değiştir. | haritekarda yondaymıştış. |
| 0.44 | 0.11 | Sıradaki raunt: Dalış Savunması. | Sıradaki round. Dediği sabah massa. |
| 0.44 | 0.12 | Sol ve sağ direği at. | FOLVE SAADIRI ATA |
| 0.42 | 0.25 | Garda geri dön. | KARDA GELITON |
| 0.41 | 0.10 | Diğer elinle ensesine veya dirseğine kontrol al. | DR-18'in en sesine beyaz defzeyini kontrol et. |
| 0.40 | 0.20 | Savun! | Subun. |
| 0.40 | 0.13 | Sıradaki: Bitirici, bir buçuk dakika. | Süredeki BTGP buçuk dakika. |
| 0.40 | 0.13 | Form devresi: börpi ve Şınav. Hız değil, kontrol. | Ponderistin Burpi Vesunov, Kuzdeir Kontrol |
| 0.40 | 0.16 | Hızla dönüp tekrar dört ayağa veya ayağa kalk. | Huzla benim tekerahı Dort Ayyavya Ayyavkalk. |
| 0.38 | 0.19 | Bugünün konusu: diz. | Bu genel konusu, bu dizi. |
| 0.38 | 0.00 | Düz Diz: geri basıp duruşa dön. | Bu diz geri bastıkları duruşa dön. |
| 0.38 | 0.29 | Sıradaki: dördüncü tur, skuat. | Seratakî, Dordun Jutuj, squat. |
| 0.37 | 0.18 | Ön Duruş: kalça ve gövde öne dönük. | Öndürüş, kalte ve göl dönerdilik. |
| 0.37 | 0.16 | Üçüncü tur. börpi, başla! | Bu çüncü tuz. Ver piy maşla. |
| 0.36 | 0.14 | Sıradaki: üçüncü tur, skuat. | Zira da ki ucun tutur squat. |
| 0.35 | 0.12 | Beşinci raunt, başla! | Beşin Gerand Paşıla. |
| 0.35 | 0.20 | Sıradaki raunt: Ön Duruş. | Seradaki round, Andrush. |
| 0.35 | 0.15 | Plank, kırk saniye. Başla! | Glank kütfani başla. |
| 0.35 | 0.15 | Gün yirmi dört. Önce ısınıyoruz. | Gün yeme dört öncesi ne oluruz? |
| 0.35 | 0.12 | Sıradaki raunt: Yuvarlak Tekme. | Sıra da ki round, you are luck, take me. |
| 0.34 | 0.17 | Bugünün konusu: tegık bir, bölüm bir. | Bugün konusu Tagic Bölün 5. |
| 0.34 | 0.02 | Sol, Sağ Direk, Sol Kroşe: ön ayak ucunda dönerek sol kroşeyi at. | ...sağ direkt saw crochet ön ayak ucunda dönerek saw crochet at. |
| 0.33 | 0.00 | Dal! | Daa |
| 0.33 | 0.24 | Dördüncü tur. Şınav, başla! | 4. tur şınağı başla. |
| 0.33 | 0.17 | Sol sağ! | Sosa. |
| 0.33 | 0.10 | Sıradaki raunt: Sol Kroşe. | Sıradaki round, Soul Crochet. |
| 0.32 | 0.16 | Sıradaki: Torba. Beş raunt, üçer dakika. | 3 dakiki torba 5 şant 3-4 dakika. |
| 0.32 | 0.21 | Sıradaki raunt: Düz Diz. | Sıradaki round, 2's diz. |
| 0.32 | 0.10 | Form devresi: börpi ve skuat. Hız değil, kontrol. | ...ornda address'e ver P ve squat hız değil, kontrol. |
| 0.32 | 0.16 | Üçüncü tur. skuat, başla! | İçinci tur, squad başlam. |
| 0.31 | 0.12 | Hedef göğüs ortası. | Edif Gürs Ortası. |
| 0.31 | 0.06 | Arka bacak esnetmelerini düzenli yap. | ...arkabaca kesin etmeden ucuzan yap. |
| 0.31 | 0.08 | Göğsünü dik, bakışını ileri tut. | Gözünü dik bakışına girer etsot. |
| 0.30 | 0.04 | Şınav, kırk beş saniye. Başla! | Şnaf kürpmeyi saniye başla. |
| 0.30 | 0.13 | Gün on dört. Önce ısınıyoruz. | Gün 14 oyuncağı sunuyoruz. |
| 0.30 | 0.04 | Börpi, kırk beş saniye. Başla! | Örpiyi kütbe saniye. Başla. |
| 0.30 | 0.20 | Sıradaki: altıncı raunt. | Sıradaki Alt & G Round. |
| 0.30 | 0.04 | Sol, Sağ Direk, Sol Kroşe: garda dön. | Sağ direkt, soğuk roşeği, garda dön. |
| 0.30 | 0.18 | Sıradaki: dördüncü tur, İp Atlama. | Sıradaki 4. tuş ip'e atlamak. |
| 0.29 | 0.00 | Sıradaki: Kondisyon. İki tur, dört hareket. | Stradikikondisyon2.haraket |
| 0.29 | 0.06 | Yumruk, ön tekme ve alçak tekme, altı raunt. | Yumruk, 1 tekme ve 1 tekme altı round. |
| 0.29 | 0.09 | Bir elinle enseyi, diğeriyle dirseği tut. | Bi elini enseye, diri ile dirseyturt. |
| 0.29 | 0.15 | Sık yapılan hata: dirsekleri açmak. Buna dikkat et. | Sık yapılan hata, diskekleri açmak buna dikkat et.  Buna dikkat... |
| 0.29 | 0.17 | Sıradaki: dördüncü tur, börpi. | Sıradaki Jordan Jutour burpi. |
| 0.29 | 0.08 | Sıradaki raunt: Güreş Duruşu. | Sıra da ki de hântı, güreş turşu. |
| 0.29 | 0.13 | Form devresi: skuat ve börpi. Hız değil, kontrol. | Form Devesi Squad Weber P.  Hızlıyı kontrol. |
| 0.29 | 0.00 | Gün on üç. Önce ısınıyoruz. | Gın 13 öğünce siniyoruz. |
| 0.29 | 0.00 | Tebrikler! Gün on altı tamamlandı. | Tepikler grunan avs tamamlandı. |
| 0.29 | 0.12 | Bitirici! Son bir gayret, tempoyu sonuna kadar koru. | Bir teriçi, zombie guided, tempo isonuna kadar koru. |
| 0.29 | 0.19 | Sıradaki: dördüncü raunt. | Sıra da ki, Doordun Dioraunt. |
| 0.29 | 0.14 | Alt blok! | Alt Biyok. |
| 0.29 | 0.14 | Dördüncü tur. börpi, başla! | Derdince tuş, Burpi Basla. |
| 0.28 | 0.17 | Kol alnın üstünde, bilek dışa dönük. | kol alınan üstünde gilekleşedin hük. |
| 0.28 | 0.10 | Omuz Esnetme, kırk beş saniye. Başla! | Omuz esnetme, kütme istane başla. |
| 0.27 | 0.00 | Kondisyon devresi: temiz form, düzenli nefes. | Kondisyon Debris'i, Tenghis Form, Duzanin Nefes. |
| 0.27 | 0.01 | Teknik çalışma: Sol Kroşe ve Sol, Sağ Direk, Sol Kroşe. Yavaş ve doğru; hız sonra gelir. | Teknik çalışma, saw crochet vessel, sağ direkt saw crochet, yavaş ve doğru, sonra gelir. |
| 0.27 | 0.20 | Ön el ve arka el sürekli çeneyi korur. | Ön el ve arka esirrekli çeneği kurursun. |
| 0.27 | 0.07 | Dinlen, bir dakika. | Dinlan, bitekika. |
| 0.26 | 0.16 | Dinlen, kırk beş saniye. | Dinlen külpessaniye. |
| 0.26 | 0.21 | Üçüncü tur. Şınav, başla! | 3. tur.  Şınav, Basla. |
| 0.26 | 0.17 | Sıradaki raunt: Tekme Bloğu. | Sıra da kirayon tekne blo |
| 0.26 | 0.09 | Ön diz bükülü, arka bacak düz. | Öndeyiz bir türlü arka bacak düz. |
| 0.26 | 0.13 | Raunt boyunca gardını koru. | Brown poyunca garden'ı koru. |
| 0.26 | 0.12 | Teknik çalışma: Boks Duruşu ve Sol Direk. Yavaş ve doğru; hız sonra gelir. | Teknik çalışma, box duruşu mesel olarak yavaş ve doğru hız sona gelir.  Sen bak... |
| 0.26 | 0.00 | Balta Tekmesi: tepe noktada bacak düz. | Ağlda tekmesi tepen ota da bacaklıyız. |
| 0.26 | 0.02 | Sık yapılan hata: ağırlığı öne vermek. Buna dikkat et. | Sık yapılan hata ağırlığı öne karmak. Buna dikkat et.  Font orda... |
| 0.25 | 0.00 | Güzel gidiyorsun, devam! | Güzel gidiyor orsunda. |
| 0.25 | 0.00 | Sıradaki gün: Sağ Kroşe. Görüşmek üzere! | Sıradaki gün sağ kroşe. Görüşmek üzere.  Hâre'yi de... |
| 0.25 | 0.02 | Sık yapılan hata: savunmadan sonra donup kalmak. Buna dikkat et. | Sıkı plan hatası, tıkılmadan sonra dolu kalmak, ona dikkat et. |
| 0.25 | 0.06 | Sıradaki: Teknik. Üç raunt, birer dakika. | Sıradaki teknik birçok rounds birer dakika. |
| 0.25 | 0.04 | Sıradaki: Arka Bacak Esnetme. | Sıradıkçı arka bacak istin etme. |
| 0.25 | 0.18 | Yarın gün altı: İp ve Ritim. Dinç gel! | Yarın gün altı ipeber içim, Dincigar. |
| 0.25 | 0.10 | Sol, Sağ Direk: arka ayağı döndürerek sağ direk at. | So, sadirek, arkaya dündirek, sadirek at. |
| 0.25 | 0.08 | Arka dizi yukarı ve ileri sür, kalçayı öne it. | arka diziyi yukarı ve ineriz görüş kalçayı önü it. |
| 0.25 | 0.05 | Bugünün konusu: üst blok. | Bugün konusu üst dock. |
| 0.25 | 0.17 | Gard yukarıda! | Gar tu kadıda |
| 0.25 | 0.15 | Sıradaki raunt: Üst Blok. | Stiradaki round üst block. |
| 0.25 | 0.00 | Tek bacak! | Tek maçak. |
| 0.24 | 0.22 | Sağ direkten dönen gövdeyle ağırlığı ön ayağa al. | Sağ direktten dönen gövdeyle ölü öne yağ al. |
| 0.24 | 0.15 | Form devresi: İp Atlama ve börpi. Hız değil, kontrol. | Form Devresi İpetamalibörp, hızlayı kontrol. |
| 0.24 | 0.15 | Sıradaki: Torba. Beş raunt, ikişer dakika. | sıradaki torba, peşrönt, içe harakika. |
| 0.24 | 0.17 | Sıradaki raunt: Savuşturma ve Blok. | Sıra da ki rönt savuştuğuma bir blok. |
| 0.24 | 0.08 | Sıradaki: ikinci tur, İp Atlama. | Sıradaki 2. tur EP Aklıma. |
| 0.24 | 0.02 | Sık yapılan hata: destek ayağını döndürmemek. Buna dikkat et. | Sık yapılan hata destek ayağını döndürmemek buna bir kadet.  Ben çok kes... |
| 0.24 | 0.14 | Sıradaki raunt: Orta Blok. | Siradeki round orta block. |
| 0.24 | 0.17 | Şınavda dirsekler kırk beş derece, gövde tek parça. | Şunanda dizi tekrar 45 dereceye gövdü tek parça. |
| 0.24 | 0.02 | Sık yapılan hata: dengeyi kaybetmek. Buna dikkat et. | Sık yapılan hata dengeyi kaybetmek buna dikkat et.  Buna dikkat... |
| 0.24 | 0.13 | Sıradaki: Tekme raundu. Yedi raunt, üçer dakika. | Sıradaki tekme roundu 7-4 dakika. |
| 0.24 | 0.16 | Skuat, şınav, börpi zinciri: kas dayanıklılığı. | Kuvat, şınav, berpizin jüde, kastayınıklılığı. |
| 0.23 | 0.00 | Sık yapılan hata: sert iniş. Buna dikkat et. | su keplen hata sert iniş, bunu bir kat et. |
| 0.23 | 0.17 | Sıradaki: Gölge. Üç raunt, üçer dakika. | Sıradaki, Gölge, Bütrand, Bütardakika |
| 0.23 | 0.16 | Form + sekiz raunt tekme: son raundu en iyi raundun yap. | Phone, psikiz round tekme, son roundu en iyi roundun yap. |
| 0.23 | 0.00 | Sıradaki: Şınav. | Sırada ki şuna of. |
| 0.23 | 0.10 | Sıradaki: Tekme raundu. Beş raunt, ikişer dakika. | Sıradaki tekme rando. Vesraant, 1 şardakika. |
| 0.23 | 0.09 | Sıradaki: üçüncü tur, börpi. | Sıra da ki, uçuncu tur, perp'i. |
| 0.23 | 0.09 | Sıradaki raunt: Düz Yumruk. | Sıra da ki round, doyuz yumruk. |
| 0.23 | 0.18 | Sıradaki: üçüncü tur, Şınav. | Sıradaki 3. tor şınav. |
| 0.23 | 0.00 | Bugünün konusu: bacak günü. | Bugünün konusu bacak günü.  Bacak. |
| 0.23 | 0.03 | Sık yapılan hata: kombinasyon sonunda çeneyi açık bırakmak. Buna dikkat et. | Tıkya plan hata kombinasyon sonunda çeneği açıp pratmak münehdik et. |
| 0.23 | 0.07 | Formun ilk bölümü: yavaş, net duruşlar. | Bu konumlu ilk bölümü yavaş net duruşlar. |
| 0.23 | 0.19 | Ön ayak ucunda dönerek sol kroşeyi at. | Ön ayak ucunda dönerek saw crochet at. |
| 0.22 | 0.19 | Her harekette temiz form; hız değil kontrol. | Her hareketi temiz formu, hızlıyı kontrol. |
| 0.22 | 0.00 | Alçak Tekme: aynı yoldan geri dön, gardı koru. | Altı alçak tekme, aynı yoldan getirden, gardı kuru. |
| 0.22 | 0.11 | Gün on: aktif dinlenme. | Gönlüm, aktif dinlenme. |
| 0.22 | 0.00 | Bugünün konusu: duruş. | Mogi'nin konusu, Duruş. |
| 0.22 | 0.00 | Her istasyonda kırk beş saniye çalış, on beş saniye dinlen. Tempo yüksek, form temiz! | Her istasyonuna kürtme saniye çalış, onbe saniye dinlen, tempo ıpsak, fontiniz. |
| 0.22 | 0.12 | Destek ayağı hedefe, kalça döner, ayak üstüyle vur. | Distik Ayağı Hedefe, Karta Donaç, Ayaküstüyle Vuruş. |
| 0.22 | 0.20 | Kik boks Duruşu: dizler hafif bükülü, vücut gevşek. | Keybox duruşu diziden hafif büküldü, lücut gevşek. |
| 0.22 | 0.07 | Yarın gün on altı: Sol, Sağ, Kroşe, Orta Tekme. Dinç gel! | Yarın gün 16 Sol Sa Crochet Orta Tekme.  Dinci Geldi. |
| 0.22 | 0.12 | Sıradaki raunt: Sol, Sağ Direk, Sol Kroşe. | Sıradaki round sol sağ direkt sol crochet. |
| 0.22 | 0.16 | Sağ direkle kalça ve arka ayağı döndür. | Saat direktle kalçer ve arka ayyalı döndür. |
| 0.22 | 0.07 | Ayak oyunu ve gölge. Ritmi koru, komut gelince tekmeni at. | Ayaklu oyunu ve görgü eritini koru, komik gelince tekmine at. |
| 0.22 | 0.00 | Plank, kırk beş saniye. Başla! | Plank külpey saniye. Başla! |
| 0.22 | 0.13 | Bugünün konusu: hız torbası. | Bugünün konuştuğu, az torbası. |
| 0.21 | 0.07 | Sıradaki raunt: Çift Bacak Dalışı. | Sıradaki round çişt bacak delişe. |
| 0.21 | 0.19 | Sık yapılan hata: dirseği yana açmak. Buna dikkat et. | Sık yapılan hata dc'ye açmak buna dikkat et. |
| 0.21 | 0.14 | Yan dön, diz göğse, topuk önde düz it. | Yandığın diz görse topuk önünde düz it. |
| 0.21 | 0.00 | Seviye değiştir. | Febiyede iştir. |
| 0.21 | 0.02 | Hızı ilk yirmi saniyede yavaş tut, sonra kademeli arttır. | Hızlı ilk yemizaniyeye baş tut.  Sonra kademeler arttır. |
| 0.21 | 0.05 | Üçüncü tur. Plank, başla! | 3. tur. Plank başla. |
| 0.21 | 0.05 | İkinci tur. Şınav, başla! | İkinci tur. Şınav başlıyor. |
| 0.21 | 0.10 | Sol, Sağ Direk: garda dön. | Sağ direkt Garda dön. |
| 0.21 | 0.12 | Sıradaki: Dalış alıştırması. Altı raunt, üçer dakika. | Süradaki dalış alıştırması 6-3-4 dakika. |
| 0.21 | 0.19 | Dolyo, dvi, ap, dolyo: ikinci tekme ilkinin dönüşünden. | Doluyor, tübi aptoluyor. İkinci tekme ikinin dönüşünden. |
| 0.21 | 0.00 | Kol Çevirme, bir dakika. Başla! | coach evilme bir dakika başla... |
| 0.21 | 0.00 | Gard al ve sürekli hareket et. | Gard all, bestrikli hareket ets. |
| 0.21 | 0.12 | Sıradaki raunt: Sol, Sağ Direk. | Sıradaki round sol sağ direktçı. |
| 0.21 | 0.00 | Sıradaki: dördüncü tur, Plank. | Sıradaki 4. tur, Plank. |
| 0.21 | 0.12 | Sıradaki: dördüncü tur, Şınav. | Sıradaki 4. tur Şınav. |
| 0.21 | 0.00 | Gün yirmi beş: aktif dinlenme. | Gün Yemekbeş, Aktif Dinleme. |
| 0.21 | 0.10 | Arka ayağı döndürerek sağ direk at. | arka ayağı dön direkt sağa direkt at. |
| 0.21 | 0.10 | Ön Bacak Esnetme, kırk saniye. Başla! | Önbese kesin etme, kıksan ye başla. |
| 0.21 | 0.14 | Sıradaki raunt: Seviye Değiştirme. | Saradaki round seria değiştirme. |
| 0.21 | 0.06 | İp ve börpi: dövüşçülerin klasik ikilisi. | İple Burpee, Düğüşülerin klasik ikilisi. |
| 0.20 | 0.00 | Sık yapılan hata: bacağı düz kaldırmak. Buna dikkat et. | Tekyapılan hata, Baja Düzkaldırmak.  Ben hadi kated. |
