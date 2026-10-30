package com.fightedu.coach

import android.content.Context
import android.media.AudioManager
import android.media.ToneGenerator
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.speech.tts.TextToSpeech
import com.fightedu.core.domain.SessionRunner.Event
import com.fightedu.core.domain.Step
import com.fightedu.core.model.BlockMode
import com.fightedu.core.model.Move
import java.util.Locale

/**
 * Antrenman sırasında sesli koç: Türkçe konuşma (cihazda Türkçe ses yoksa yalnızca zil), gong/bip ve
 * titreşim. [SessionRunner] olaylarını konuşmaya çevirir.
 */
class Coach(context: Context) {
    var voiceEnabled = true
    var vibrationEnabled = true

    private var ready = false
    private val tts: TextToSpeech = TextToSpeech(context.applicationContext) { status ->
        if (status == TextToSpeech.SUCCESS) {
            val r = tts.setLanguage(Locale("tr", "TR"))
            ready = r != TextToSpeech.LANG_MISSING_DATA && r != TextToSpeech.LANG_NOT_SUPPORTED
            tts.setSpeechRate(1.05f)
        }
    }
    private val tone: ToneGenerator? = try {
        ToneGenerator(AudioManager.STREAM_MUSIC, 85)
    } catch (_: RuntimeException) {
        null
    }
    private val vibrator: Vibrator? =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            (context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager)?.defaultVibrator
        } else {
            @Suppress("DEPRECATION")
            context.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
        }

    fun onEvents(events: List<Event>) = events.forEach(::onEvent)

    fun onEvent(event: Event) {
        when (event) {
            is Event.StepStarted -> {
                val s = event.step
                if (s is Step.Work) {
                    tone?.startTone(ToneGenerator.TONE_PROP_BEEP2, 450) // gong
                    vibrate(longArrayOf(0, 120, 80, 120))
                    say(workAnnouncement(s), flush = true)
                } else if (s is Step.Rest) {
                    tone?.startTone(ToneGenerator.TONE_PROP_ACK, 350)
                    vibrate(longArrayOf(0, 300))
                    say(restAnnouncement(s), flush = true)
                }
            }
            is Event.Call -> say(callName(event.callout.move) + "!", flush = true)
            Event.TenSecondsLeft -> say("Son on saniye!", flush = true)
            is Event.Countdown -> tone?.startTone(ToneGenerator.TONE_PROP_BEEP, 120)
            Event.Finished -> {
                tone?.startTone(ToneGenerator.TONE_PROP_BEEP2, 900)
                vibrate(longArrayOf(0, 200, 100, 200, 100, 400))
                say("Antrenman bitti. Harika iş çıkardın!", flush = true)
            }
        }
    }

    fun say(text: String, flush: Boolean = false) {
        if (!voiceEnabled || !ready) return
        tts.speak(text, if (flush) TextToSpeech.QUEUE_FLUSH else TextToSpeech.QUEUE_ADD, null, text.hashCode().toString())
    }

    fun stop() {
        if (ready) tts.stop()
    }

    fun release() {
        tts.stop()
        tts.shutdown()
        tone?.release()
    }

    private fun vibrate(pattern: LongArray) {
        if (!vibrationEnabled) return
        try {
            vibrator?.vibrate(VibrationEffect.createWaveform(pattern, -1))
        } catch (_: SecurityException) {
        }
    }

    companion object {
        /** Komut olarak söylenecek kısa ad ("Jab (1)" -> "Jab", "Kombinasyon 1-2 (Jab–Cross)" -> "Bir iki"). */
        fun callName(move: Move): String = CALLS[move.id]
            ?: move.name.substringBefore(" (").substringAfter(": ").replace("–", " ").trim()

        private val CALLS = mapOf(
            "box_combo_12" to "Bir iki",
            "box_combo_123" to "Bir iki üç",
            "box_footwork" to "Ayak oyunu",
            "box_parry_block" to "Blok",
            "box_slip" to "Slip",
            "box_roll" to "Roll",
            "box_lead_hook" to "Sol kroşe",
            "box_rear_hook" to "Sağ kroşe",
            "box_lead_uppercut" to "Sol aparkat",
            "box_rear_uppercut" to "Sağ aparkat",
            "box_cross" to "Cross",
            "kb_combo_jcl" to "Jab cross low kick",
            "kb_combo_jcm" to "Jab cross kroşe middle",
            "kb_jab_cross" to "Jab cross",
            "kb_footwork" to "Açı değiştir",
            "kb_knee" to "Diz",
            "wr_level_change" to "Seviye",
            "wr_penetration" to "Penetrasyon",
            "wr_double_leg" to "Çift bacak",
            "wr_single_leg" to "Tek bacak",
            "wr_hand_fight" to "El mücadelesi",
            "wr_sit_out" to "Sit out",
            "wr_stand_up" to "Kalk",
            "tkd_footwork" to "Ayak oyunu",
            "tkd_taegeuk1" to "Taegeuk",
        )

        fun workAnnouncement(s: Step.Work): String {
            val b = s.block
            val first = s.round == 1 && s.station == 1
            val intro = if (first && b.cue.isNotBlank()) b.cue + " " else ""
            return intro + when (b.mode) {
                BlockMode.ROUND -> if (s.totalRounds > 1) "Raunt ${s.round}. Başla!" else "Başla!"
                BlockMode.CIRCUIT -> "${s.move.name.substringBefore(" (")}. ${s.seconds} saniye. Başla!"
                BlockMode.REPS -> "${s.move.name.substringBefore(" (")}. ${s.reps} tekrar."
            }
        }

        fun restAnnouncement(s: Step.Rest): String {
            val n = s.next
            val next = when {
                s.betweenBlocks -> "Sıradaki: ${n.block.title}"
                n.block.mode == BlockMode.ROUND -> "Sıradaki raunt ${n.round}"
                else -> "Sıradaki: ${n.move.name.substringBefore(" (")}"
            }
            return "Dinlen. ${s.seconds} saniye. $next."
        }
    }
}
