package com.fightedu.core.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/** Uygulamadaki bir dövüş sporu (boks, kick boks, güreş, tekvando). */
@Serializable
data class Sport(
    val id: String,
    val name: String,
    val emoji: String,
    val colorHex: String,
    val tagline: String,
    val description: String,
)

@Serializable
enum class MoveCategory(val label: String) {
    @SerialName("stance") STANCE("Duruş"),
    @SerialName("footwork") FOOTWORK("Ayak Oyunu"),
    @SerialName("strike") STRIKE("Vuruş"),
    @SerialName("kick") KICK("Tekme"),
    @SerialName("defense") DEFENSE("Savunma"),
    @SerialName("takedown") TAKEDOWN("Dalış / İndirme"),
    @SerialName("ground") GROUND("Yer"),
    @SerialName("combination") COMBINATION("Kombinasyon"),
    @SerialName("form") FORM("Form"),
    @SerialName("conditioning") CONDITIONING("Kondisyon"),
    @SerialName("warmup") WARMUP("Isınma"),
    @SerialName("stretch") STRETCH("Esneme"),
}

/** Hareket kütüphanesindeki tek bir teknik/egzersiz. */
@Serializable
data class Move(
    val id: String,
    val sport: String,
    val name: String,
    val category: MoveCategory,
    val level: Int,
    val description: String,
    val steps: List<String>,
    val mistakes: List<String>,
    val tip: String = "",
    val reps: Int? = null,
    val sec: Int? = null,
) {
    /** Hareket videosunun (döngüsel MP4) assets içindeki yolu. */
    val videoAsset: String get() = "video/$id.mp4"

    /** Liste küçük resimleri ve video yüklenirken gösterilen kapak resmi. */
    val posterAsset: String get() = "poster/$id.webp"

    val levelLabel: String
        get() = when (level) {
            1 -> "Başlangıç"
            2 -> "Orta"
            else -> "İleri"
        }
}

/** Antrenman bloğunun türü (arayüzde ikon ve renk için). */
@Serializable
enum class BlockKind(val label: String) {
    @SerialName("warmup") WARMUP("Isınma"),
    @SerialName("technique") TECHNIQUE("Teknik"),
    @SerialName("shadow") SHADOW("Gölge"),
    @SerialName("bag") BAG("Torba"),
    @SerialName("drill") DRILL("Drill"),
    @SerialName("form") FORM("Form"),
    @SerialName("conditioning") CONDITIONING("Kondisyon"),
    @SerialName("cooldown") COOLDOWN("Esneme"),
}

/**
 * Blok oynatma biçimi:
 * - ROUND: her raunt [Block.work] saniye; video [Block.moves] arasında döner, koç [Block.calls] komutlarını verir.
 * - CIRCUIT: her hareket bir istasyon ([Block.work] sn), istasyonlar arası [Block.rest]; [Block.rounds] tur.
 * - REPS: her harekette [Block.reps] tekrar, kullanıcı "Bitti" der; [Block.rounds] set.
 */
@Serializable
enum class BlockMode {
    @SerialName("round") ROUND,
    @SerialName("circuit") CIRCUIT,
    @SerialName("reps") REPS,
}

@Serializable
data class Block(
    val kind: BlockKind,
    val title: String,
    val mode: BlockMode,
    val rounds: Int,
    val work: Int = 0,
    val rest: Int = 0,
    val reps: Int? = null,
    val moves: List<String>,
    val calls: List<String> = emptyList(),
    /** Koçun blok başında söylediği kısa talimat. */
    val cue: String = "",
)

/** Antrenmanın bir günü: koç notu ve sıralı bloklar. */
@Serializable
data class TrainingDay(
    val day: Int,
    val title: String,
    val focus: String,
    val blocks: List<Block>,
)

/** Programın bir evresi: [from]..[to] günleri. */
@Serializable
data class TrainingPhase(
    val title: String,
    val from: Int,
    val to: Int,
    val goal: String,
)

/** Bir sporun sıralı günlerden oluşan antrenman programı. */
@Serializable
data class TrainingProgram(
    val sport: String,
    val phases: List<TrainingPhase>,
    val days: List<TrainingDay>,
) {
    val totalDays: Int get() = days.size

    fun day(number: Int): TrainingDay? = days.firstOrNull { it.day == number }

    fun phaseOf(day: Int): TrainingPhase? = phases.firstOrNull { day in it.from..it.to }
}
