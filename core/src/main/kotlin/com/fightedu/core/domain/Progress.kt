package com.fightedu.core.domain

import java.time.LocalDate
import kotlin.math.ceil

/** Tamamlanan seanslara göre ilerleme hesapları. */
class ProgressTracker(
    val sessions: List<PlannedSession>,
    val completedKeys: Set<String>,
) {
    val totalWeeks: Int = sessions.maxOfOrNull { it.week } ?: 0
    val daysPerWeek: Int = sessions.count { it.week == 1 }

    fun isCompleted(session: PlannedSession) = session.key in completedKeys

    fun sessionsOfWeek(week: Int) = sessions.filter { it.week == week }

    fun completedInWeek(week: Int) = sessionsOfWeek(week).count { isCompleted(it) }

    val completedCount: Int get() = sessions.count { isCompleted(it) }

    val overallProgress: Float
        get() = if (sessions.isEmpty()) 0f else completedCount.toFloat() / sessions.size

    /** Haftanın açılması için önceki haftada tamamlanması önerilen seans sayısı. */
    val unlockThreshold: Int get() = ceil(daysPerWeek * UNLOCK_RATIO).toInt()

    /**
     * 1. hafta her zaman açıktır; sonraki haftalar, bir önceki haftanın en az %70'i
     * tamamlanınca açılır. Bu yumuşak bir kilittir: arayüz uyarı gösterip yine de izin verebilir.
     */
    fun isWeekUnlocked(week: Int): Boolean =
        week <= 1 || completedInWeek(week - 1) >= unlockThreshold

    /** Kullanıcının bulunduğu hafta: açık olan en son hafta. */
    val currentWeek: Int
        get() = (1..totalWeeks).lastOrNull { isWeekUnlocked(it) } ?: 1

    /** Sıradaki tamamlanmamış seans (takvim sırasıyla). */
    val nextSession: PlannedSession?
        get() = sessions.firstOrNull { !isCompleted(it) }

    fun sessionOn(date: LocalDate): PlannedSession? = sessions.firstOrNull { it.date == date }

    /** Tarihi geçmiş ama tamamlanmamış seans sayısı. */
    fun missedCount(today: LocalDate): Int = sessions.count { it.date.isBefore(today) && !isCompleted(it) }

    val isFinished: Boolean get() = sessions.isNotEmpty() && sessions.all { isCompleted(it) }

    companion object {
        const val UNLOCK_RATIO = 0.7
    }
}
