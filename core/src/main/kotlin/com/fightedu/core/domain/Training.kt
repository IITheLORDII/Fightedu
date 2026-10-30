package com.fightedu.core.domain

import com.fightedu.core.content.ContentLibrary
import com.fightedu.core.model.Block
import com.fightedu.core.model.BlockMode
import com.fightedu.core.model.Move
import com.fightedu.core.model.TrainingDay

/** Raunt içinde koçun verdiği komut: çalışma başladıktan [atSec] saniye sonra [move]. */
data class Callout(val atSec: Int, val move: Move)

/** Oynatıcının sırayla göstereceği adımlar. */
sealed interface Step {
    val blockIndex: Int

    data class Work(
        override val blockIndex: Int,
        val block: Block,
        /** Raunt / tur / set numarası (1 tabanlı). */
        val round: Int,
        val totalRounds: Int,
        val move: Move,
        /** İstasyon sırası (CIRCUIT/REPS blokları; ROUND'da 1/1). */
        val station: Int,
        val stations: Int,
        /** Süreli adımda saniye; tekrarlı adımda null. */
        val seconds: Int?,
        val reps: Int?,
        val callouts: List<Callout>,
    ) : Step

    data class Rest(
        override val blockIndex: Int,
        val seconds: Int,
        val next: Work,
        /** Bir bloktan diğerine geçiş dinlenmesi mi? */
        val betweenBlocks: Boolean,
    ) : Step
}

/** Bir antrenman gününü raunt/istasyon adımlarına açar. */
class TrainingPlanner(private val library: ContentLibrary) {

    fun steps(day: TrainingDay): List<Step> {
        val out = mutableListOf<Step>()
        day.blocks.forEachIndexed { bi, block ->
            val works = works(bi, block)
            if (out.isNotEmpty() && works.isNotEmpty()) {
                out += Step.Rest(bi, maxOf(block.rest, BLOCK_TRANSITION), works.first(), betweenBlocks = true)
            }
            works.forEachIndexed { i, w ->
                out += w
                val next = works.getOrNull(i + 1)
                if (next != null && block.rest > 0) out += Step.Rest(bi, block.rest, next, betweenBlocks = false)
            }
        }
        return out
    }

    private fun works(bi: Int, block: Block): List<Step.Work> {
        val moves = block.moves.map { requireNotNull(library.move(it)) { "Hareket bulunamadı: $it" } }
        val calls = block.calls.map { requireNotNull(library.move(it)) { "Hareket bulunamadı: $it" } }
        val out = mutableListOf<Step.Work>()
        when (block.mode) {
            BlockMode.ROUND -> for (r in 1..block.rounds) {
                out += Step.Work(
                    bi, block, r, block.rounds, moves[(r - 1) % moves.size], 1, 1, block.work, null,
                    callouts(calls, block.work, r),
                )
            }
            BlockMode.CIRCUIT, BlockMode.REPS -> for (r in 1..block.rounds) {
                moves.forEachIndexed { i, m ->
                    val timed = block.mode == BlockMode.CIRCUIT
                    out += Step.Work(
                        bi, block, r, block.rounds, m, i + 1, moves.size,
                        if (timed) block.work else null, if (timed) null else block.reps, emptyList(),
                    )
                }
            }
        }
        return out
    }

    /** Komutlar ilk [CALL_START] sn'den sonra her [CALL_INTERVAL] sn'de bir; raunt değiştikçe sıra kayar. */
    private fun callouts(calls: List<Move>, work: Int, round: Int): List<Callout> {
        if (calls.isEmpty()) return emptyList()
        val out = mutableListOf<Callout>()
        var t = CALL_START
        var k = round - 1
        while (t <= work - CALL_END_GAP) {
            out += Callout(t, calls[k % calls.size])
            t += CALL_INTERVAL
            k++
        }
        return out
    }

    fun estimatedSeconds(day: TrainingDay): Int = steps(day).sumOf {
        when (it) {
            is Step.Work -> it.seconds ?: ((it.reps ?: 0) * SECONDS_PER_REP)
            is Step.Rest -> it.seconds
        }
    }

    fun estimatedMinutes(day: TrainingDay): Int = (estimatedSeconds(day) + 59) / 60

    companion object {
        const val SECONDS_PER_REP = 3
        const val BLOCK_TRANSITION = 30
        const val CALL_START = 8
        const val CALL_INTERVAL = 15
        const val CALL_END_GAP = 8

        /** Blok özeti, ör. "6 × 2 dk · 1 dk dinlenme" ya da "3 tur × 4 hareket". */
        fun summary(block: Block): String = when (block.mode) {
            BlockMode.ROUND -> "${block.rounds} raunt × ${formatDuration(block.work)}" +
                (if (block.rest > 0) " · ${formatDuration(block.rest)} dinlenme" else "")
            BlockMode.CIRCUIT -> "${block.rounds} tur × ${block.moves.size} hareket · ${formatDuration(block.work)}"
            BlockMode.REPS -> "${block.rounds} set × ${block.reps} tekrar"
        }
    }
}

/**
 * Antrenman oynatıcısının saf durum makinesi: zamanlayıcı her saniye [tick] çağırır; dönen olaylar
 * (raunt başı, komut, son 10 sn, geri sayım, bitiş) sesli koç ve gonga bağlanır.
 */
class SessionRunner(val steps: List<Step>) {

    sealed interface Event {
        data class StepStarted(val step: Step) : Event
        data class Call(val callout: Callout) : Event
        data object TenSecondsLeft : Event
        data class Countdown(val n: Int) : Event
        data object Finished : Event
    }

    var index = 0
        private set
    var remaining = durationOf(steps.firstOrNull())
        private set
    var elapsedInStep = 0
        private set
    var totalElapsed = 0
        private set
    var paused = false
        private set
    var finished = steps.isEmpty()
        private set

    val current: Step? get() = steps.getOrNull(index)
    val progress: Float get() = if (steps.isEmpty()) 1f else (if (finished) steps.size else index).toFloat() / steps.size

    /** Durum geri yüklenirken (ekran döndürme vb.) kullanılır. */
    fun restore(index: Int, remaining: Int, elapsedInStep: Int, totalElapsed: Int, paused: Boolean, finished: Boolean) {
        this.index = index.coerceIn(0, maxOf(0, steps.size - 1))
        this.remaining = remaining
        this.elapsedInStep = elapsedInStep
        this.totalElapsed = totalElapsed
        this.paused = paused
        this.finished = finished
    }

    fun start(): List<Event> = current?.let { listOf(Event.StepStarted(it)) } ?: listOf(Event.Finished)

    /** Bir saniye ilerlet. */
    fun tick(): List<Event> {
        if (paused || finished) return emptyList()
        totalElapsed++
        val step = current ?: return emptyList()
        if (durationOf(step) == 0) return emptyList() // tekrarlı adım: kullanıcı bitirir
        val events = mutableListOf<Event>()
        remaining--
        elapsedInStep++
        if (step is Step.Work) {
            step.callouts.filter { it.atSec == elapsedInStep }.forEach { events += Event.Call(it) }
            if (remaining == 10 && (step.seconds ?: 0) >= 30) events += Event.TenSecondsLeft
        }
        if (remaining in 1..3) events += Event.Countdown(remaining)
        if (remaining <= 0) events += goTo(index + 1)
        return events
    }

    fun next(): List<Event> = goTo(index + 1)

    fun prev(): List<Event> {
        // Adımın başındaysak bir önceki çalışma adımına, değilse bu adımın başına dön
        var target = if (elapsedInStep > 2) index else index - 1
        while (target > 0 && steps[target] is Step.Rest) target--
        return goTo(target.coerceAtLeast(0))
    }

    fun togglePause() {
        if (!finished) paused = !paused
    }

    fun addRest(seconds: Int) {
        if (current is Step.Rest) remaining += seconds
    }

    private fun goTo(target: Int): List<Event> {
        if (target >= steps.size) {
            finished = true
            index = steps.size - 1
            remaining = 0
            return listOf(Event.Finished)
        }
        index = target
        remaining = durationOf(steps[target])
        elapsedInStep = 0
        finished = false
        return listOf(Event.StepStarted(steps[target]))
    }

    companion object {
        fun durationOf(step: Step?): Int = when (step) {
            is Step.Work -> step.seconds ?: 0
            is Step.Rest -> step.seconds
            null -> 0
        }
    }
}
