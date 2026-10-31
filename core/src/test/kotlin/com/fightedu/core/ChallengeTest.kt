package com.fightedu.core

import com.fightedu.core.domain.ChallengeCalendar
import com.fightedu.core.domain.ChallengeDay
import com.fightedu.core.domain.ChallengeProgress
import com.fightedu.core.domain.ProgressTracker
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.LocalDate

class ChallengeTest {
    private val program = TestContent.library.program("boxing")!!
    private val today = LocalDate.of(2026, 10, 31)

    private fun keysUpTo(n: Int): Set<String> = (1..n).map { d ->
        ChallengeCalendar.workoutNumber(d)?.let { ProgressTracker.keyOf(it) } ?: ChallengeProgress.restKey(d)
    }.toSet()

    @Test
    fun `takvim 30 gün - 24 antrenman ve 6 dinlenme, son gün final antrenmanı`() {
        val days = ChallengeCalendar.days(program)
        assertEquals(30, days.size)
        assertEquals(24, days.count { it is ChallengeDay.Workout })
        assertEquals(ChallengeCalendar.REST_DAYS, days.filterIsInstance<ChallengeDay.Rest>().map { it.number }.toSet())
        assertEquals((1..24).toList(), days.filterIsInstance<ChallengeDay.Workout>().map { it.training.day })
        assertEquals(24, (days.last() as ChallengeDay.Workout).training.day)
        assertNull(ChallengeCalendar.workoutNumber(5))
        assertEquals(4, ChallengeCalendar.workoutNumber(4))
        assertEquals(5, ChallengeCalendar.workoutNumber(6))
        for (w in 1..24) assertEquals(w, ChallengeCalendar.workoutNumber(ChallengeCalendar.challengeDayOf(w)))
        assertEquals(5, ChallengeCalendar.weeks)
        assertEquals(29..30, ChallengeCalendar.daysOfWeek(5))
        assertEquals(2, ChallengeCalendar.weekOf(8))
    }

    @Test
    fun `günler sırayla açılır, dinlenme günü de tamamlanmalı`() {
        val none = ChallengeProgress(program, emptySet(), today = today)
        assertTrue(none.isUnlocked(1))
        assertFalse(none.isUnlocked(2))
        assertEquals(1, none.current?.number)

        val four = ChallengeProgress(program, keysUpTo(4), today = today)
        assertTrue(four.current is ChallengeDay.Rest)
        assertEquals(5, four.current?.number)
        assertTrue(four.isUnlocked(5))
        assertFalse(four.isUnlocked(6))

        val five = ChallengeProgress(program, keysUpTo(5), today = today)
        assertEquals(6, five.current?.number)
        assertEquals(5, (five.current as ChallengeDay.Workout).training.day)
        assertEquals(5, five.doneCount)
        assertEquals(4, five.workoutsDone)
        assertTrue(five.isUnlocked(6))

        val week = ChallengeProgress(program, keysUpTo(7), today = today)
        assertTrue(week.isWeekDone(1))
        assertFalse(week.isWeekDone(2))

        val all = ChallengeProgress(program, keysUpTo(30), today = today)
        assertTrue(all.isFinished)
        assertNull(all.current)
        assertEquals(1f, all.progress)
    }

    @Test
    fun `dinlenme günü önceki antrenmanın evresine sayılır`() {
        val p = ChallengeProgress(program, emptySet(), today = today)
        val phases = program.phases
        assertEquals(phases[0], p.phaseOf(5))
        assertEquals(phases[0], p.phaseOf(7)) // antrenman 6 = 1. evrenin değerlendirmesi
        assertEquals(phases[1], p.phaseOf(8))
        assertEquals(phases[3], p.phaseOf(30))
        assertEquals(30, phases.sumOf { p.daysOfPhase(it).size })
    }

    @Test
    fun `seri bugünden ya da dünden geriye sayılır`() {
        val t = today.toEpochDay()
        fun streak(vararg back: Long) =
            ChallengeProgress(program, emptySet(), back.map { t - it }.toSet(), today)
        assertEquals(0, streak().currentStreak)
        assertEquals(3, streak(0, 1, 2).currentStreak)
        assertEquals(2, streak(1, 2).currentStreak) // bugün henüz çalışmadı
        assertEquals(0, streak(2, 3).currentStreak)
        val gap = streak(0, 1, 5, 6, 7, 8)
        assertEquals(2, gap.currentStreak)
        assertEquals(4, gap.bestStreak)
        assertTrue(gap.trainedToday)
    }

    @Test
    fun `her dalın takvimi kurulabilir`() {
        for (sport in TestContent.library.sports) {
            val days = ChallengeCalendar.days(TestContent.library.program(sport.id)!!)
            assertEquals(sport.id, 30, days.size)
        }
    }
}
