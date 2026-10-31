package com.fightedu.core.domain

import com.fightedu.core.model.TrainingDay
import com.fightedu.core.model.TrainingPhase
import com.fightedu.core.model.TrainingProgram
import java.time.LocalDate

/** 30 günlük meydan okumanın bir günü: dalın antrenman günlerinden biri ya da dinlenme günü. */
sealed interface ChallengeDay {
    /** Meydan okumadaki gün (1..30). */
    val number: Int

    data class Workout(override val number: Int, val training: TrainingDay) : ChallengeDay

    data class Rest(override val number: Int) : ChallengeDay
}

/**
 * 30 günlük takvim: 24 antrenman günü + 6 dinlenme günü. Her 5. gün dinlenme; finalden önce (28. gün) bir dinlenme
 * daha, böylece 30. gün programın son (değerlendirme) antrenmanıdır.
 */
object ChallengeCalendar {
    const val LENGTH = 30
    const val WORKOUTS = 24
    const val WEEK = 7
    val REST_DAYS: Set<Int> = setOf(5, 10, 15, 20, 25, 28)

    /** Hafta satırı sayısı (7'li haftalar; son hafta 2 gün). */
    val weeks: Int get() = (LENGTH + WEEK - 1) / WEEK

    fun isRest(number: Int): Boolean = number in REST_DAYS

    /** [number]. güne düşen antrenman günü (1..24); dinlenme günü ya da aralık dışı için null. */
    fun workoutNumber(number: Int): Int? =
        if (number !in 1..LENGTH || isRest(number)) null else number - REST_DAYS.count { it < number }

    /** [workout]. antrenman gününün meydan okumadaki günü. */
    fun challengeDayOf(workout: Int): Int {
        require(workout in 1..WORKOUTS) { "antrenman günü 1..$WORKOUTS olmalı: $workout" }
        return (1..LENGTH).first { workoutNumber(it) == workout }
    }

    /** 1'den başlayan hafta numarası. */
    fun weekOf(number: Int): Int = (number - 1) / WEEK + 1

    /** Haftanın günleri (son hafta kısa). */
    fun daysOfWeek(week: Int): IntRange = ((week - 1) * WEEK + 1)..minOf(week * WEEK, LENGTH)

    fun days(program: TrainingProgram): List<ChallengeDay> = (1..LENGTH).map { n ->
        val w = workoutNumber(n)
        if (w == null) {
            ChallengeDay.Rest(n)
        } else {
            ChallengeDay.Workout(n, requireNotNull(program.day(w)) { "${program.sport}: $w. gün yok" })
        }
    }
}

/**
 * Bir dalın 30 günlük meydan okumasındaki ilerleme.
 * Tamamlananlar anahtarlarla saklanır: antrenman günleri `day_N` (antrenman günü numarası, [ProgressTracker.keyOf]),
 * dinlenme günleri `rest_N` (meydan okuma günü). Bir gün, önceki gün bitince açılır; tamamlananlar tekrar yapılabilir.
 * [activityDays]: kullanıcının antrenman ya da dinlenme tamamladığı günler (epoch günü) — seri hesabı için.
 */
class ChallengeProgress(
    val program: TrainingProgram,
    completedKeys: Set<String>,
    activityDays: Set<Long> = emptySet(),
    val today: LocalDate = LocalDate.now(),
) {
    val days: List<ChallengeDay> = ChallengeCalendar.days(program)
    val tracker = ProgressTracker(program, ProgressTracker.daysFromKeys(completedKeys))
    private val restDone: Set<Int> = completedKeys.mapNotNull { k ->
        k.removePrefix(REST_PREFIX).takeIf { k.startsWith(REST_PREFIX) }?.toIntOrNull()
    }.filter { ChallengeCalendar.isRest(it) }.toSet()
    private val activity: List<Long> = activityDays.sorted()

    fun day(number: Int): ChallengeDay? = days.getOrNull(number - 1)

    fun isDone(number: Int): Boolean = when (val d = day(number)) {
        is ChallengeDay.Workout -> tracker.isCompleted(d.training.day)
        is ChallengeDay.Rest -> number in restDone
        null -> false
    }

    fun isUnlocked(number: Int): Boolean = number <= 1 || isDone(number) || isDone(number - 1)

    val doneCount: Int get() = days.count { isDone(it.number) }

    val progress: Float get() = doneCount.toFloat() / ChallengeCalendar.LENGTH

    /** Sıradaki gün: tamamlanmamış ilk gün (hepsi bittiyse null). */
    val current: ChallengeDay? get() = days.firstOrNull { !isDone(it.number) }

    val isFinished: Boolean get() = doneCount == ChallengeCalendar.LENGTH

    val workoutsDone: Int get() = tracker.completedCount

    fun isWeekDone(week: Int): Boolean = ChallengeCalendar.daysOfWeek(week).all { isDone(it) }

    /** Günün evresi; dinlenme günü, kendisinden önceki antrenmanın evresine sayılır. */
    fun phaseOf(number: Int): TrainingPhase? {
        val workout = (number downTo 1).firstNotNullOfOrNull { ChallengeCalendar.workoutNumber(it) } ?: 1
        return program.phaseOf(workout)
    }

    /** Evrenin meydan okuma günleri (dinlenme günleri dahil). */
    fun daysOfPhase(phase: TrainingPhase): List<Int> = (1..ChallengeCalendar.LENGTH).filter { phaseOf(it) == phase }

    /** Bugün ya da dün biten ardışık aktif gün sayısı (bugün henüz çalışılmadıysa seri dünden sayılır). */
    val currentStreak: Int
        get() {
            val set = activity.toHashSet()
            val t = today.toEpochDay()
            var d = when {
                t in set -> t
                (t - 1) in set -> t - 1
                else -> return 0
            }
            var n = 0
            while (d in set) {
                n++
                d--
            }
            return n
        }

    val bestStreak: Int
        get() {
            var best = 0
            var run = 0
            var prev: Long? = null
            for (d in activity) {
                run = if (prev != null && d == prev + 1) run + 1 else 1
                best = maxOf(best, run)
                prev = d
            }
            return best
        }

    val trainedToday: Boolean get() = today.toEpochDay() in activity

    companion object {
        private const val REST_PREFIX = "rest_"

        fun restKey(number: Int) = "$REST_PREFIX$number"
    }
}
