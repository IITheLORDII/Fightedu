package com.fightedu.core.voice

import com.fightedu.core.content.ContentLibrary
import com.fightedu.core.domain.ChallengeCalendar
import com.fightedu.core.domain.SessionRunner
import com.fightedu.core.domain.TrainingPlanner
import com.fightedu.core.model.TrainingDay
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

/** Bir ses klibi: [text] ekranda/incelemede görünen, [say] seslendirilen metin; [ms] süre. */
@Serializable
data class Clip(val text: String, val say: String, val ms: Int, val measured: Boolean = false)

@Serializable
data class VoiceManifest(val version: Int = 1, val clips: Map<String, Clip>) {
    fun clip(id: String): Clip? = clips[id]
}

/** Bir adımın sesleri: başında [start], adımın [at] saniyesinde (SessionRunner.elapsedInStep) diğerleri. */
@Serializable
data class StepCues(
    @SerialName("s") val start: List<String> = emptyList(),
    val at: Map<Int, List<String>> = emptyMap(),
)

/** Bir antrenman (ya da dinlenme) seansının ses planı; adımlar TrainingPlanner.steps ile aynı sıradadır. */
@Serializable
data class DayCues(val steps: List<StepCues>, val finish: List<String> = emptyList()) {
    val clipIds: Set<String> get() = (steps.flatMap { it.start + it.at.values.flatten() } + finish).toSet()
}

/** Bir dalın ses planları: antrenman günü -> plan, meydan okumanın dinlenme günü -> dinlenme seansı planı. */
@Serializable
data class SportCues(val sport: String, val days: Map<Int, DayCues>, val rest: Map<Int, DayCues> = emptyMap())

/**
 * Sesli koçun metinleri ve ses klipleri (assets/voice; tools/voice/make_voice.py üretir).
 * Klip dosyası yoksa uygulama aynı metni cihazın konuşma motoruyla okur.
 */
class VoiceScript(val manifest: VoiceManifest, private val sports: Map<String, SportCues>) {

    fun workout(sportId: String, day: Int): DayCues? = sports[sportId]?.days?.get(day)

    /** Meydan okumanın [challengeDay]. günü (dinlenme günü) için aktif dinlenme seansı. */
    fun restDay(sportId: String, challengeDay: Int): DayCues? = sports[sportId]?.rest?.get(challengeDay)

    /**
     * İçerikle tutarlılık: her plan, oynatıcının adım sayısıyla eşleşmeli; klipler manifestte (ve [assetExists]
     * verilirse diskte) bulunmalı; zamanlar adım süresinin içinde olmalı. Boş liste = sorun yok.
     */
    fun validate(library: ContentLibrary, assetExists: ((String) -> Boolean)? = null): List<String> {
        val errors = mutableListOf<String>()
        val planner = TrainingPlanner(library)
        fun check(tag: String, day: TrainingDay, cues: DayCues?) {
            if (cues == null) {
                errors += "$tag: ses planı yok"
                return
            }
            val steps = planner.steps(day)
            if (cues.steps.size != steps.size) {
                errors += "$tag: ${cues.steps.size} adım planı, oynatıcıda ${steps.size} adım"
                return
            }
            steps.forEachIndexed { i, step ->
                val len = SessionRunner.durationOf(step)
                for (sec in cues.steps[i].at.keys) {
                    if (len > 0 && sec !in 1 until len) errors += "$tag/adım ${i + 1}: $sec. sn adım dışında ($len sn)"
                }
            }
            for (id in cues.clipIds) {
                if (manifest.clip(id) == null) errors += "$tag: manifestte olmayan klip $id"
            }
        }
        for (sport in library.sports) {
            val program = library.program(sport.id) ?: continue
            for (day in program.days) check("${sport.id}/gün ${day.day}", day, workout(sport.id, day.day))
            val rest = library.restDay
            if (rest != null) {
                for (n in ChallengeCalendar.REST_DAYS) check("${sport.id}/dinlenme $n", rest, restDay(sport.id, n))
            }
        }
        if (assetExists != null) {
            val missing = manifest.clips.keys.count { !assetExists(clipAsset(it)) }
            if (missing > 0) errors += "$missing klibin ses dosyası yok"
        }
        return errors
    }

    companion object {
        const val DIR = "voice"

        fun clipAsset(id: String) = "$DIR/clips/$id.ogg"

        private val json = Json { ignoreUnknownKeys = true }

        /** Ses planlarını yükler; dosyalar yoksa null (uygulama eski konuşma metinlerine döner). */
        fun load(sportIds: List<String>, readAsset: (String) -> String?): VoiceScript? {
            val manifest = readAsset("$DIR/manifest.json")?.let { json.decodeFromString<VoiceManifest>(it) } ?: return null
            val sports = sportIds.mapNotNull { id ->
                readAsset("$DIR/cues_$id.json")?.let { id to json.decodeFromString<SportCues>(it) }
            }.toMap()
            return VoiceScript(manifest, sports)
        }
    }
}
