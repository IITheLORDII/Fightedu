package com.fightedu.coach

import android.content.Context
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import java.util.Locale

/**
 * Ses kayıtları yokken cihazın konuşma motoru. Motor hazır olana kadar gelen cümleler bekletilir (ilk anons
 * kaybolmaz); cümleler sıraya eklenir, yalnızca yeni adımda kuyruk temizlenir.
 */
class TtsSpeaker(context: Context, private val focus: AudioFocus) {
    private var ready = false
    private val pending = mutableListOf<String>()
    private var lastId = ""
    private val tts: TextToSpeech = TextToSpeech(context.applicationContext) { status ->
        if (status == TextToSpeech.SUCCESS) {
            val r = tts.setLanguage(Locale("tr", "TR"))
            ready = r != TextToSpeech.LANG_MISSING_DATA && r != TextToSpeech.LANG_NOT_SUPPORTED
            if (ready) {
                tts.setSpeechRate(1.05f)
                tts.setAudioAttributes(AudioFocus.SPEECH)
                tts.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                    override fun onStart(utteranceId: String?) = Unit
                    override fun onDone(utteranceId: String?) {
                        if (utteranceId == lastId) focus.release()
                    }

                    @Deprecated("Deprecated in Java")
                    override fun onError(utteranceId: String?) = Unit
                })
                val queued = pending.toList()
                pending.clear()
                speak(queued, flush = true)
            }
        }
    }

    val isSpeaking: Boolean get() = ready && tts.isSpeaking

    fun speak(texts: List<String>, flush: Boolean) {
        if (texts.isEmpty()) return
        if (!ready) {
            if (flush) pending.clear()
            pending += texts
            return
        }
        focus.acquire()
        texts.forEachIndexed { i, t ->
            lastId = "u${System.nanoTime()}"
            tts.speak(t, if (flush && i == 0) TextToSpeech.QUEUE_FLUSH else TextToSpeech.QUEUE_ADD, null, lastId)
        }
    }

    fun stop() {
        pending.clear()
        if (ready) tts.stop()
        focus.release()
    }

    fun release() {
        tts.stop()
        tts.shutdown()
        focus.release()
    }
}
