package com.fightedu.coach

import android.content.Context
import android.media.AudioAttributes
import android.media.SoundPool

/** Kısa efektler (gong, dinlenme zili, 3-2-1 bipi, bitiş): SoundPool ile gecikmesiz ve hep aynı seviyede. */
class Fx(context: Context) {
    enum class Sound(val asset: String) { GONG("fx_gong"), BELL("fx_bell"), BEEP("fx_beep"), FINISH("fx_finish") }

    private val pool = SoundPool.Builder()
        .setMaxStreams(3)
        .setAudioAttributes(
            AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_ASSISTANCE_SONIFICATION)
                .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                .build(),
        )
        .build()

    private val ids: Map<Sound, Int> = Sound.entries.mapNotNull { s ->
        runCatching { context.assets.openFd("voice/${s.asset}.ogg").use { s to pool.load(it, 1) } }.getOrNull()
    }.toMap()

    fun play(sound: Sound, volume: Float = 0.9f) {
        ids[sound]?.let { pool.play(it, volume, volume, 1, 0, 1f) }
    }

    fun release() = pool.release()
}
