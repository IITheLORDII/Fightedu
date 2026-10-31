package com.fightedu.coach

import android.content.Context
import android.media.AudioAttributes
import android.media.AudioFocusRequest
import android.media.AudioManager

/** Koç konuşurken kullanıcının müziğini kısar (kapatmaz); konuşma bitince geri bırakır. */
class AudioFocus(context: Context) {
    private val am = context.getSystemService(AudioManager::class.java)
    private val request = AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK)
        .setAudioAttributes(SPEECH)
        .setOnAudioFocusChangeListener { }
        .build()
    private var held = false

    fun acquire() {
        if (held) return
        held = am?.requestAudioFocus(request) == AudioManager.AUDIOFOCUS_REQUEST_GRANTED
    }

    fun release() {
        if (!held) return
        am?.abandonAudioFocusRequest(request)
        held = false
    }

    companion object {
        val SPEECH: AudioAttributes = AudioAttributes.Builder()
            .setUsage(AudioAttributes.USAGE_ASSISTANCE_NAVIGATION_GUIDANCE)
            .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
            .build()
    }
}
