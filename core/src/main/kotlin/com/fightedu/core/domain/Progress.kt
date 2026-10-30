package com.fightedu.core.domain

import com.fightedu.core.model.TrainingDay
import com.fightedu.core.model.TrainingPhase
import com.fightedu.core.model.TrainingProgram

/** Sıralı günlere göre ilerleme: bir gün, önceki gün tamamlanınca açılır; tamamlananlar tekrar yapılabilir. */
class ProgressTracker(
    val program: TrainingProgram,
    val completedDays: Set<Int>,
) {
    val totalDays: Int get() = program.totalDays

    fun isCompleted(day: Int) = day in completedDays

    fun isUnlocked(day: Int) = day <= 1 || isCompleted(day) || isCompleted(day - 1)

    val completedCount: Int get() = program.days.count { isCompleted(it.day) }

    val overallProgress: Float
        get() = if (totalDays == 0) 0f else completedCount.toFloat() / totalDays

    /** Sıradaki gün: tamamlanmamış ilk gün (hepsi bittiyse null). */
    val nextDay: TrainingDay? get() = program.days.firstOrNull { !isCompleted(it.day) }

    /** Kullanıcının bulunduğu evre (bitince son evre). */
    val currentPhase: TrainingPhase?
        get() = program.phaseOf(nextDay?.day ?: totalDays)

    fun completedInPhase(phase: TrainingPhase) = (phase.from..phase.to).count { isCompleted(it) }

    val isFinished: Boolean get() = totalDays > 0 && completedCount == totalDays

    companion object {
        fun keyOf(day: Int) = "day_$day"

        /** Saklanan anahtarlardan gün numaraları (eski biçimdeki anahtarlar yok sayılır). */
        fun daysFromKeys(keys: Set<String>): Set<Int> =
            keys.mapNotNull { k -> k.removePrefix("day_").takeIf { k.startsWith("day_") }?.toIntOrNull() }.toSet()
    }
}
