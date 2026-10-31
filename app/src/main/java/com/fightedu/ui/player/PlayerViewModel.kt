package com.fightedu.ui.player

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.viewModelScope
import com.fightedu.coach.Coach
import com.fightedu.coach.CoachVoice
import com.fightedu.core.domain.Callout
import com.fightedu.core.domain.SessionRunner
import com.fightedu.core.domain.SessionRunner.Event
import com.fightedu.core.domain.Step
import com.fightedu.data.CoachSettings
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/** Oynatıcı ekranının anlık durumu. */
data class PlayerUi(
    val index: Int = 0,
    val remaining: Int = 0,
    val totalElapsed: Int = 0,
    val paused: Boolean = false,
    val finished: Boolean = false,
    val progress: Float = 0f,
    /** Son verilen koç komutu (ekranda birkaç saniye görünür). */
    val callout: Callout? = null,
)

/**
 * Antrenmanı yürütür: saniyede bir [SessionRunner.tick], olayları sesli koça iletir. Durum
 * [SavedStateHandle]'a yazılır; ekran döndürme / süreç ölümü sonrası kaldığı yerden devam eder.
 */
class PlayerViewModel(app: Application, private val saved: SavedStateHandle) : AndroidViewModel(app) {
    private val coach = Coach(app)
    private var runner: SessionRunner? = null
    private var ticker: Job? = null
    private var calloutUntil = 0

    private val _ui = MutableStateFlow(PlayerUi())
    val ui: StateFlow<PlayerUi> = _ui.asStateFlow()

    val steps: List<Step> get() = runner?.steps.orEmpty()

    /** İlk çağrıda antrenmanı kurar ve başlatır; sonraki çağrılar (yeniden oluşturma) etkisizdir. */
    fun setup(day: Int, steps: List<Step>, settings: CoachSettings, voice: CoachVoice?) {
        coach.voiceEnabled = settings.voice
        coach.vibrationEnabled = settings.vibration
        if (runner != null) return
        // ses planı oynatıcının adımlarıyla eşleşmiyorsa (içerik değişmiş) kısa anonslara dön
        coach.setVoice(voice?.takeIf { it.cues.steps.size == steps.size })
        val r = SessionRunner(steps)
        runner = r
        if (saved.get<Int>(KEY_DAY) == day) {
            r.restore(
                index = saved.get<Int>(KEY_INDEX) ?: 0,
                remaining = saved.get<Int>(KEY_REMAINING) ?: SessionRunner.durationOf(steps.firstOrNull()),
                elapsedInStep = saved.get<Int>(KEY_ELAPSED_STEP) ?: 0,
                totalElapsed = saved.get<Int>(KEY_TOTAL) ?: 0,
                paused = true,
                finished = saved.get<Boolean>(KEY_FINISHED) ?: false,
            )
        } else {
            saved[KEY_DAY] = day
            coach.onEvents(r.start(), r.index, r.elapsedInStep)
        }
        publish()
        ticker = viewModelScope.launch {
            while (true) {
                delay(1000)
                val events = r.tick()
                if (events.isNotEmpty() || !r.paused) handle(events)
            }
        }
    }

    fun togglePause() = act { r ->
        r.togglePause()
        if (r.paused) coach.stop()
        emptyList()
    }

    fun next() = act { it.next() }

    fun prev() = act { it.prev() }

    fun addRest(seconds: Int) = act { r ->
        r.addRest(seconds)
        emptyList()
    }

    private fun act(block: (SessionRunner) -> List<Event>) {
        val r = runner ?: return
        handle(block(r))
    }

    private fun handle(events: List<Event>) {
        val r = runner ?: return
        events.forEach { e ->
            when (e) {
                is Event.Call -> {
                    _ui.value = _ui.value.copy(callout = e.callout)
                    calloutUntil = r.totalElapsed + CALLOUT_VISIBLE
                }
                is Event.StepStarted -> calloutUntil = 0
                else -> Unit
            }
        }
        coach.onEvents(events, r.index, r.elapsedInStep)
        publish()
    }

    private fun publish() {
        val r = runner ?: return
        saved[KEY_INDEX] = r.index
        saved[KEY_REMAINING] = r.remaining
        saved[KEY_ELAPSED_STEP] = r.elapsedInStep
        saved[KEY_TOTAL] = r.totalElapsed
        saved[KEY_FINISHED] = r.finished
        _ui.value = PlayerUi(
            index = r.index,
            remaining = r.remaining,
            totalElapsed = r.totalElapsed,
            paused = r.paused,
            finished = r.finished,
            progress = r.progress,
            callout = _ui.value.callout?.takeIf { r.totalElapsed < calloutUntil },
        )
    }

    override fun onCleared() {
        ticker?.cancel()
        coach.release()
    }

    companion object {
        private const val CALLOUT_VISIBLE = 4
        private const val KEY_DAY = "day"
        private const val KEY_INDEX = "index"
        private const val KEY_REMAINING = "remaining"
        private const val KEY_ELAPSED_STEP = "elapsedStep"
        private const val KEY_TOTAL = "total"
        private const val KEY_FINISHED = "finished"
    }
}
