package com.fightedu.core.domain

import com.fightedu.core.model.Move
import java.time.DayOfWeek
import java.time.LocalDate

/** Kullanıcının onboarding'de seçtikleri. */
data class PlanConfig(
    val sportId: String,
    val trainingDays: Set<DayOfWeek>,
    val startDate: LocalDate,
) {
    val daysPerWeek: Int get() = trainingDays.size

    /** Haftanın günleri, Pazartesi'den başlayarak sıralı. */
    val sortedDays: List<DayOfWeek> get() = trainingDays.sortedBy { it.value }

    companion object {
        fun daysToMask(days: Set<DayOfWeek>): Int = days.fold(0) { acc, d -> acc or (1 shl (d.value - 1)) }
        fun maskToDays(mask: Int): Set<DayOfWeek> = DayOfWeek.entries.filter { mask and (1 shl (it.value - 1)) != 0 }.toSet()
    }
}

enum class Section(val label: String) {
    WARMUP("Isınma"),
    MAIN("Ana Bölüm"),
    COOLDOWN("Soğuma"),
}

/** Programda bir seansa yerleştirilmiş, dozu hesaplanmış hareket. */
data class PlannedExercise(
    val move: Move,
    val section: Section,
    val sets: Int,
    val reps: Int?,
    val sec: Int?,
    val rest: Int,
) {
    val doseLabel: String
        get() = buildString {
            if (sets > 1) append("$sets × ")
            if (reps != null) append("$reps tekrar") else append(formatDuration(sec ?: 0))
        }
}

/** Takvime yerleşmiş tek bir antrenman günü. */
data class PlannedSession(
    val week: Int,
    /** Hafta içindeki sıra (0 tabanlı). */
    val index: Int,
    val date: LocalDate,
    val code: String,
    val title: String,
    val phaseTitle: String,
    val phaseGoal: String,
    val warmup: List<PlannedExercise>,
    val main: List<PlannedExercise>,
    val cooldown: List<PlannedExercise>,
) {
    val key: String get() = keyOf(week, index)
    val exercises: List<PlannedExercise> get() = warmup + main + cooldown

    companion object {
        fun keyOf(week: Int, index: Int) = "w${week}_d$index"
    }
}

fun formatDuration(totalSec: Int): String {
    val m = totalSec / 60
    val s = totalSec % 60
    return when {
        m == 0 -> "$s sn"
        s == 0 -> "$m dk"
        else -> "$m dk $s sn"
    }
}
