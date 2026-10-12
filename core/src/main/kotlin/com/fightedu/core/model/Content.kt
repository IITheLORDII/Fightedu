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
    /** Animasyon dosyasının assets içindeki yolu. */
    val lottieAsset: String get() = "lottie/$id.json"

    val levelLabel: String
        get() = when (level) {
            1 -> "Başlangıç"
            2 -> "Orta"
            else -> "İleri"
        }
}

/** Program şablonunda bir hareketin dozu (set x tekrar veya set x süre). */
@Serializable
data class ExerciseRef(
    val move: String,
    val sets: Int = 1,
    val reps: Int? = null,
    val sec: Int? = null,
    val rest: Int = 30,
)

@Serializable
data class SessionTemplate(
    val code: String,
    val title: String,
    val main: List<ExerciseRef>,
)

/** Programın 2 haftalık bir evresi; seanslar A..E sırasıyla öncelik taşır. */
@Serializable
data class Phase(
    val title: String,
    val weeks: List<Int>,
    val goal: String,
    val sessions: List<SessionTemplate>,
)

@Serializable
data class ProgramTemplate(
    val sport: String,
    val warmup: List<ExerciseRef>,
    val cooldown: List<ExerciseRef>,
    val phases: List<Phase>,
) {
    val totalWeeks: Int get() = phases.flatMap { it.weeks }.maxOrNull() ?: 0

    fun phaseForWeek(week: Int): Phase? = phases.firstOrNull { week in it.weeks }
}
