package com.fightedu.coach

import android.content.Context
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import com.fightedu.core.domain.SessionRunner.Event
import com.fightedu.core.domain.Step
import com.fightedu.core.model.BlockMode
import com.fightedu.core.model.Move
import com.fightedu.core.voice.DayCues
import com.fightedu.core.voice.TurkishNumbers
import com.fightedu.core.voice.VoiceManifest

/** Bir seansın ses planı: cümleler [manifest]te, adım adım zamanlama [cues]ta; [recorded] = ses dosyaları var. */
data class CoachVoice(val manifest: VoiceManifest, val cues: DayCues, val recorded: Boolean)

/**
 * Antrenman sırasında sesli koç. Seansın ses planı varsa her adımın başında ve belirli saniyelerinde rauntlara
 * özel cümleleri çalar (kayıtlı Türkçe ses; kayıt yoksa aynı cümleleri cihazın konuşma motoru okur). Efektler
 * (gong, zil, 3-2-1, bitiş) ve titreşim her zaman çalışır. Plan yoksa eski kısa anonslar kullanılır.
 */
class Coach(context: Context) {
    var voiceEnabled = true
    var vibrationEnabled = true

    private val focus = AudioFocus(context)
    private val fx = Fx(context)
    private val appContext = context.applicationContext
    private var voice: CoachVoice? = null
    private var clipPlayer: VoicePlayer? = null
    private var ttsSpeaker: TtsSpeaker? = null

    private val vibrator: Vibrator? =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            (context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager)?.defaultVibrator
        } else {
            @Suppress("DEPRECATION")
            context.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
        }

    fun setVoice(v: CoachVoice?) {
        voice = v
        if (v?.recorded == true && clipPlayer == null) clipPlayer = VoicePlayer(appContext, focus)
    }

    private fun tts(): TtsSpeaker = ttsSpeaker ?: TtsSpeaker(appContext, focus).also { ttsSpeaker = it }

    /** Runner olayları; [index] ve [elapsed] olaylardan sonraki adım ve adım içi saniyedir. */
    fun onEvents(events: List<Event>, index: Int, elapsed: Int) {
        var stepStarted = false
        for (event in events) {
            when (event) {
                is Event.StepStarted -> {
                    stepStarted = true
                    val work = event.step is Step.Work
                    fx.play(if (work) Fx.Sound.GONG else Fx.Sound.BELL)
                    vibrate(if (work) longArrayOf(0, 120, 80, 120) else longArrayOf(0, 300))
                    val cues = voice?.cues?.steps?.getOrNull(index)
                    if (cues != null) {
                        speakClips(cues.start, flush = true)
                    } else {
                        speakText(listOf(legacyAnnouncement(event.step)), flush = true)
                    }
                }
                is Event.Call -> if (voice == null && !speaking()) speakText(listOf(callName(event.callout.move) + "!"), flush = false)
                Event.TenSecondsLeft -> if (voice == null && !speaking()) speakText(listOf("Son on saniye!"), flush = false)
                is Event.Countdown -> fx.play(Fx.Sound.BEEP, 0.75f)
                Event.Finished -> {
                    fx.play(Fx.Sound.FINISH)
                    vibrate(longArrayOf(0, 200, 100, 200, 100, 400))
                    val fin = voice?.cues?.finish
                    if (fin != null) speakClips(fin, flush = true) else speakText(listOf("Antrenman bitti. Harika iş çıkardın!"), flush = true)
                }
            }
        }
        if (!stepStarted && elapsed > 0) {
            voice?.cues?.steps?.getOrNull(index)?.at?.get(elapsed)?.let { speakClips(it, flush = false) }
        }
    }

    private fun speaking() = clipPlayer?.isSpeaking == true || ttsSpeaker?.isSpeaking == true

    private fun speakClips(ids: List<String>, flush: Boolean) {
        if (!voiceEnabled || ids.isEmpty()) return
        val v = voice ?: return
        if (v.recorded) {
            clipPlayer?.play(ids, flush)
        } else {
            speakText(ids.mapNotNull { v.manifest.clip(it)?.say }, flush)
        }
    }

    private fun speakText(texts: List<String>, flush: Boolean) {
        if (!voiceEnabled || texts.isEmpty()) return
        tts().speak(texts, flush)
    }

    fun stop() {
        clipPlayer?.stop()
        ttsSpeaker?.stop()
    }

    fun release() {
        clipPlayer?.release()
        ttsSpeaker?.release()
        fx.release()
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

        /** Ses planı olmayan seanslar için kısa anons (sayılar kelimeyle). */
        fun legacyAnnouncement(step: Step): String = when (step) {
            is Step.Work -> workAnnouncement(step)
            is Step.Rest -> restAnnouncement(step)
        }

        fun workAnnouncement(s: Step.Work): String {
            val b = s.block
            val first = s.round == 1 && s.station == 1
            val intro = if (first && b.cue.isNotBlank()) b.cue.replace(Regex("\\d+")) { TurkishNumbers.cardinal(it.value.toInt()) } + " " else ""
            val name = s.move.name.substringBefore(" (")
            return intro + when (b.mode) {
                BlockMode.ROUND -> when {
                    s.totalRounds == 1 -> "Başla!"
                    s.round == s.totalRounds -> "Son raunt, başla!"
                    else -> "${TurkishNumbers.ordinal(s.round).replaceFirstChar { it.titlecase() }} raunt, başla!"
                }
                BlockMode.CIRCUIT -> "$name, ${TurkishNumbers.duration(s.seconds ?: 0)}. Başla!"
                BlockMode.REPS -> "$name. ${TurkishNumbers.cardinal(s.reps ?: 0)} tekrar."
            }
        }

        fun restAnnouncement(s: Step.Rest): String {
            val n = s.next
            val next = when {
                s.betweenBlocks -> "Sıradaki: ${n.block.title}"
                n.block.mode == BlockMode.ROUND && n.round == n.totalRounds -> "Sıradaki: son raunt"
                n.block.mode == BlockMode.ROUND -> "Sıradaki: ${TurkishNumbers.ordinal(n.round)} raunt"
                else -> "Sıradaki: ${n.move.name.substringBefore(" (")}"
            }
            return "Dinlen, ${TurkishNumbers.duration(s.seconds)}. $next."
        }
    }
}
