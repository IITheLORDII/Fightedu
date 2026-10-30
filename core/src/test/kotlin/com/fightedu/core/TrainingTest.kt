package com.fightedu.core

import com.fightedu.core.domain.ProgressTracker
import com.fightedu.core.domain.SessionRunner
import com.fightedu.core.domain.SessionRunner.Event
import com.fightedu.core.domain.Step
import com.fightedu.core.domain.TrainingPlanner
import com.fightedu.core.model.Block
import com.fightedu.core.model.BlockKind
import com.fightedu.core.model.BlockMode
import com.fightedu.core.model.TrainingDay
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class TrainingTest {
    private val library = TestContent.library
    private val planner = TrainingPlanner(library)

    private val sample = TrainingDay(
        day = 1, title = "Deneme", focus = "",
        blocks = listOf(
            Block(BlockKind.WARMUP, "İp", BlockMode.ROUND, rounds = 2, work = 60, rest = 20, moves = listOf("gen_jump_rope")),
            Block(
                BlockKind.BAG, "Torba", BlockMode.ROUND, rounds = 3, work = 60, rest = 30,
                moves = listOf("box_jab", "box_combo_12"), calls = listOf("box_jab", "box_cross"),
            ),
            Block(BlockKind.CONDITIONING, "Kondisyon", BlockMode.CIRCUIT, rounds = 2, work = 30, rest = 10,
                moves = listOf("gen_pushup", "gen_squat")),
            Block(BlockKind.CONDITIONING, "Şınav", BlockMode.REPS, rounds = 2, rest = 30, reps = 10,
                moves = listOf("gen_pushup")),
        ),
    )

    @Test
    fun `raunt, devre ve tekrar blokları doğru adımlara açılır`() {
        val steps = planner.steps(sample)
        val works = steps.filterIsInstance<Step.Work>()
        assertEquals(2 + 3 + 4 + 2, works.size)
        // torba raundunda video hareketler arasında döner
        assertEquals(listOf("box_jab", "box_combo_12", "box_jab"), works.filter { it.blockIndex == 1 }.map { it.move.id })
        // dinlenmeler arka arkaya gelmez, ilk ve son adım çalışma
        assertTrue(steps.zipWithNext().none { (a, b) -> a is Step.Rest && b is Step.Rest })
        assertTrue(steps.first() is Step.Work && steps.last() is Step.Work)
        // bloklar arası geçişte en az 30 sn
        val transitions = steps.filterIsInstance<Step.Rest>().filter { it.betweenBlocks }
        assertEquals(3, transitions.size)
        assertTrue(transitions.all { it.seconds >= TrainingPlanner.BLOCK_TRANSITION })
        // tekrarlı adım süresiz
        assertTrue(works.last().seconds == null && works.last().reps == 10)
    }

    @Test
    fun `koç komutları raunt içinde düzenli aralıkla ve raunt sonuna yakın değil`() {
        val bag = planner.steps(sample).filterIsInstance<Step.Work>().filter { it.blockIndex == 1 }
        for (w in bag) {
            assertTrue(w.callouts.isNotEmpty())
            assertEquals(TrainingPlanner.CALL_START, w.callouts.first().atSec)
            assertTrue(w.callouts.all { it.atSec <= 60 - TrainingPlanner.CALL_END_GAP })
            assertTrue(w.callouts.zipWithNext().all { (a, b) -> b.atSec - a.atSec == TrainingPlanner.CALL_INTERVAL })
        }
        // sonraki raunt komut sırası kayar
        assertEquals("box_cross", bag[1].callouts.first().move.id)
    }

    @Test
    fun `oynatıcı saniye saniye ilerler, olay üretir ve biter`() {
        val runner = SessionRunner(planner.steps(sample))
        assertTrue(runner.start().first() is Event.StepStarted)
        val events = mutableListOf<Event>()
        var guard = 0
        while (!runner.finished && guard++ < 10_000) {
            val step = runner.current
            if (step is Step.Work && step.seconds == null) events += runner.next() else events += runner.tick()
        }
        assertTrue(runner.finished)
        assertEquals(Event.Finished, events.last())
        assertTrue(events.any { it is Event.Call })
        assertTrue(events.any { it is Event.TenSecondsLeft })
        assertEquals(runner.steps.size - 1, events.count { it is Event.StepStarted })
        assertEquals(1f, runner.progress)
    }

    @Test
    fun `duraklat, ileri, geri ve dinlenme ekleme`() {
        val runner = SessionRunner(planner.steps(sample))
        runner.start()
        runner.togglePause()
        assertTrue(runner.tick().isEmpty())
        assertEquals(60, runner.remaining)
        runner.togglePause()
        repeat(5) { runner.tick() }
        assertEquals(55, runner.remaining)
        runner.next() // dinlenme
        assertTrue(runner.current is Step.Rest)
        runner.addRest(15)
        assertEquals(35, runner.remaining)
        runner.next() // 2. raunt
        runner.prev() // başındayken: önceki çalışma adımına (dinlenmeyi atlayarak)
        assertEquals(0, runner.index)
        assertFalse(runner.finished)
    }

    @Test
    fun `gerçek programın tüm günleri planlanabilir ve süreleri makul`() {
        for (sport in library.sports) {
            for (d in library.program(sport.id)!!.days) {
                val m = planner.estimatedMinutes(d)
                assertTrue("${sport.id} gün ${d.day}: $m dk", m in 20..60)
                assertTrue(planner.steps(d).isNotEmpty())
            }
        }
    }

    @Test
    fun `günler sırayla açılır, tamamlananlar tekrar yapılabilir`() {
        val program = library.program("boxing")!!
        val none = ProgressTracker(program, emptySet())
        assertTrue(none.isUnlocked(1))
        assertFalse(none.isUnlocked(2))
        assertEquals(1, none.nextDay?.day)
        val some = ProgressTracker(program, setOf(1, 2, 3))
        assertTrue(some.isUnlocked(4))
        assertFalse(some.isUnlocked(5))
        assertTrue(some.isUnlocked(2))
        assertEquals(4, some.nextDay?.day)
        assertEquals(3, some.completedInPhase(program.phases.first()))
        val all = ProgressTracker(program, (1..24).toSet())
        assertTrue(all.isFinished)
        assertNull(all.nextDay)
        assertEquals(1f, all.overallProgress)
        assertEquals(setOf(3, 12), ProgressTracker.daysFromKeys(setOf("day_3", "day_12", "w1_d0")))
    }
}
