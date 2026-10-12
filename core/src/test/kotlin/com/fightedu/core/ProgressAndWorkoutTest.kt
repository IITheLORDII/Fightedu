package com.fightedu.core

import com.fightedu.core.domain.PlanConfig
import com.fightedu.core.domain.PlanGenerator
import com.fightedu.core.domain.ProgressTracker
import com.fightedu.core.domain.WorkoutPlanner
import com.fightedu.core.domain.WorkoutStep
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.DayOfWeek
import java.time.LocalDate

class ProgressAndWorkoutTest {
    private val sessions = PlanGenerator(TestContent.library).generate(
        PlanConfig("kickboxing", setOf(DayOfWeek.TUESDAY, DayOfWeek.THURSDAY, DayOfWeek.SATURDAY), LocalDate.of(2026, 10, 13)),
    )

    @Test
    fun `hafta kilidi yüzde 70 kuralına uyar`() {
        val none = ProgressTracker(sessions, emptySet())
        assertTrue(none.isWeekUnlocked(1))
        assertFalse(none.isWeekUnlocked(2))
        assertEquals(1, none.currentWeek)
        assertEquals(3, none.unlockThreshold) // ceil(3 * 0.7)

        val twoDone = ProgressTracker(sessions, sessions.filter { it.week == 1 }.take(2).map { it.key }.toSet())
        assertFalse(twoDone.isWeekUnlocked(2))

        val weekDone = ProgressTracker(sessions, sessions.filter { it.week == 1 }.map { it.key }.toSet())
        assertTrue(weekDone.isWeekUnlocked(2))
        assertEquals(2, weekDone.currentWeek)
        assertEquals(sessions.first { it.week == 2 }, weekDone.nextSession)
    }

    @Test
    fun `genel ilerleme ve bitiş`() {
        val all = ProgressTracker(sessions, sessions.map { it.key }.toSet())
        assertEquals(1f, all.overallProgress)
        assertTrue(all.isFinished)
        assertEquals(null, all.nextSession)
        assertEquals(0, all.missedCount(LocalDate.of(2027, 1, 1)))
        assertEquals(sessions.size, ProgressTracker(sessions, emptySet()).missedCount(LocalDate.of(2027, 1, 1)))
    }

    @Test
    fun `oynatıcı adımları tüm setleri içerir ve sonda dinlenme yoktur`() {
        val session = sessions.first()
        val steps = WorkoutPlanner.steps(session)
        val workSteps = steps.filterIsInstance<WorkoutStep.Work>()
        assertEquals(session.exercises.sumOf { it.sets }, workSteps.size)
        assertTrue(steps.last() is WorkoutStep.Work)
        // Hiçbir dinlenme arka arkaya gelmez
        assertTrue(steps.zipWithNext().none { (a, b) -> a is WorkoutStep.Rest && b is WorkoutStep.Rest })
        val minutes = WorkoutPlanner.estimatedMinutes(session)
        assertTrue("tahmini süre $minutes dk", minutes in 15..90)
    }

    @Test
    fun `tüm seansların süresi makul aralıkta`() {
        for (sport in TestContent.library.sports) {
            val all = PlanGenerator(TestContent.library).generate(
                PlanConfig(sport.id, DayOfWeek.entries.take(5).toSet(), LocalDate.of(2026, 10, 12)),
            )
            for (s in all) {
                val m = WorkoutPlanner.estimatedMinutes(s)
                assertTrue("${sport.id} ${s.key} $m dk", m in 15..90)
            }
        }
    }
}
