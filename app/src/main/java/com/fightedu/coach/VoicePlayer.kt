package com.fightedu.coach

import android.content.Context
import androidx.media3.common.AudioAttributes
import androidx.media3.common.C
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import com.fightedu.core.voice.VoiceScript

/** Kaydedilmiş koç cümlelerini (assets/voice/clips/<id>.ogg) sırayla, araya boşluk bırakmadan çalar. */
class VoicePlayer(context: Context, private val focus: AudioFocus) {
    private val player = ExoPlayer.Builder(context.applicationContext).build().apply {
        setAudioAttributes(
            AudioAttributes.Builder()
                .setUsage(C.USAGE_ASSISTANCE_NAVIGATION_GUIDANCE)
                .setContentType(C.AUDIO_CONTENT_TYPE_SPEECH)
                .build(),
            /* handleAudioFocus = */ false,
        )
        addListener(object : Player.Listener {
            override fun onPlaybackStateChanged(state: Int) {
                if (state == Player.STATE_ENDED) focus.release()
            }
        })
    }

    val isSpeaking: Boolean
        get() = player.playWhenReady && player.playbackState != Player.STATE_ENDED &&
            player.playbackState != Player.STATE_IDLE

    /** [flush]: çalan cümleyi kesip yenilerini başlat; değilse sıraya ekle. */
    fun play(ids: List<String>, flush: Boolean) {
        if (ids.isEmpty()) return
        val items = ids.map { MediaItem.fromUri("asset:///${VoiceScript.clipAsset(it)}") }
        if (flush || !isSpeaking) {
            player.setMediaItems(items)
            player.prepare()
        } else {
            player.addMediaItems(items)
        }
        focus.acquire()
        player.playWhenReady = true
    }

    fun stop() {
        player.stop()
        player.clearMediaItems()
        focus.release()
    }

    fun release() {
        player.release()
        focus.release()
    }
}
