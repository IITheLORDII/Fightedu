package com.fightedu.core

import com.fightedu.core.domain.PlanConfig
import com.fightedu.core.domain.PlanGenerator
import com.fightedu.core.domain.Section
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.DayOfWeek
import java.time.DayOfWeek.FRIDAY
import java.time.DayOfWeek.MONDAY
import java.time.DayOfWeek.SATURDAY
import java.time.DayOfWeek.THURSDAY
import java.time.DayOfWeek.TUESDAY
import java.time.DayOfWeek.WEDNESDAY
import java.time.LocalDate

class PlanGeneratorTest {
    private val generator = PlanGenerator(TestContent.library)
    private val monday = LocalDate.of(2026, 10, 12)

    private fun config(sport: String, vararg days: DayOfWeek, start: LocalDate = monday) =
        PlanConfig(sport, days.toSet(), start)

    @Test
    fun `3, 4 ve 5 gün için 8 hafta x N seans üretilir`() {
        val dayOptions = listOf(
            setOf(MONDAY, WEDNESDAY, FRIDAY),
            setOf(MONDAY, TUESDAY, THURSDAY, FRIDAY),
            setOf(MONDAY, TUESDAY, WEDNESDAY, THURSDAY, SATURDAY),
        )
        for (sport in TestContent.library.sports) {
            for (days in dayOptions) {
                val sessions = generator.generate(PlanConfig(sport.id, days, monday))
                assertEquals(8 * days.size, sessions.size)
                for (week in 1..8) {
                    val codes = sessions.filter { it.week == week }.map { it.code }
                    assertEquals(listOf("A", "B", "C", "D", "E").take(days.size), codes)
                }
            }
        }
    }

    @Test
    fun `seanslar yalnızca seçilen günlere ve sırayla yerleşir`() {
        val sessions = generator.generate(config("boxing", MONDAY, WEDNESDAY, FRIDAY))
        assertTrue(sessions.all { it.date.dayOfWeek in setOf(MONDAY, WEDNESDAY, FRIDAY) })
        assertEquals(sessions.map { it.date }.sorted(), sessions.map { it.date })
        assertEquals(sessions.size, sessions.map { it.date }.toSet().size)
        assertEquals(monday, sessions.first().date)
        // 8 hafta, 3 gün: son seans 8. haftanın cuması
        assertEquals(monday.plusWeeks(7).plusDays(4), sessions.last().date)
    }

    @Test
    fun `başlangıç hafta ortasındaysa ilk uygun günden başlar`() {
        val thursday = monday.plusDays(3)
        val sessions = generator.generate(config("taekwondo", MONDAY, WEDNESDAY, FRIDAY, start = thursday))
        assertEquals(thursday.plusDays(1), sessions.first().date)
        assertEquals(24, sessions.size)
    }

    @Test
    fun `evrenin ikinci haftasında ana bölüm dozu artar, ısınma sabit kalır`() {
        val sessions = generator.generate(config("boxing", MONDAY, WEDNESDAY, FRIDAY))
        val w1 = sessions.first { it.week == 1 && it.code == "A" }
        val w2 = sessions.first { it.week == 2 && it.code == "A" }
        assertEquals(w1.main.map { it.move.id }, w2.main.map { it.move.id })
        val jab1 = w1.main.first { it.move.id == "box_jab" }
        val jab2 = w2.main.first { it.move.id == "box_jab" }
        assertTrue(jab2.reps!! > jab1.reps!!)
        assertEquals(w1.warmup, w2.warmup)
        assertTrue(w1.warmup.all { it.section == Section.WARMUP })
        assertTrue(w1.cooldown.all { it.section == Section.COOLDOWN })
    }

    @Test(expected = IllegalArgumentException::class)
    fun `2 gün reddedilir`() {
        generator.generate(config("boxing", MONDAY, THURSDAY))
    }

    @Test(expected = IllegalArgumentException::class)
    fun `6 gün reddedilir`() {
        generator.generate(config("boxing", MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY))
    }

    @Test
    fun `gün maskesi gidiş-dönüş`() {
        val days = setOf(MONDAY, WEDNESDAY, SATURDAY)
        assertEquals(days, PlanConfig.maskToDays(PlanConfig.daysToMask(days)))
        assertEquals(0b0100101, PlanConfig.daysToMask(days))
    }
}
