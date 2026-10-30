package com.fightedu.core.content

import com.fightedu.core.domain.TrainingPlanner
import com.fightedu.core.model.BlockMode
import com.fightedu.core.model.Move
import com.fightedu.core.model.Sport
import com.fightedu.core.model.TrainingProgram
import kotlinx.serialization.json.Json

/** Uygulamanın tüm statik içeriği (sporlar, hareketler, günlük antrenman programları). */
class ContentLibrary(
    val sports: List<Sport>,
    moves: List<Move>,
    programs: List<TrainingProgram>,
) {
    val moves: Map<String, Move> = moves.associateBy { it.id }
    val programs: Map<String, TrainingProgram> = programs.associateBy { it.sport }

    fun sport(id: String): Sport? = sports.firstOrNull { it.id == id }
    fun move(id: String): Move? = moves[id]
    fun program(sportId: String): TrainingProgram? = programs[sportId]
    fun movesForSport(sportId: String): List<Move> = moves.values.filter { it.sport == sportId }

    /**
     * İçerik tutarlılığını kontrol eder; boş liste = sorun yok.
     * [assetExists] verilirse her hareketin videosu ve kapak resmi de aranır.
     */
    fun validate(assetExists: ((String) -> Boolean)? = null): List<String> {
        val errors = mutableListOf<String>()
        val sportIds = sports.map { it.id }.toSet()
        for (move in moves.values) {
            if (move.sport != GENERAL && move.sport !in sportIds) errors += "${move.id}: bilinmeyen spor ${move.sport}"
            if (move.steps.isEmpty()) errors += "${move.id}: adım yok"
            if (move.level !in 1..3) errors += "${move.id}: seviye 1-3 olmalı"
            if (assetExists != null) {
                for (asset in listOf(move.videoAsset, move.posterAsset)) {
                    if (!assetExists(asset)) errors += "${move.id}: dosya yok ($asset)"
                }
            }
        }
        val planner = TrainingPlanner(this)
        for (sport in sports) {
            val program = programs[sport.id]
            if (program == null) {
                errors += "${sport.id}: antrenman programı yok"
                continue
            }
            val days = program.days.map { it.day }
            if (days != (1..TOTAL_DAYS).toList()) errors += "${sport.id}: günler 1..$TOTAL_DAYS ardışık olmalı ($days)"
            val covered = program.phases.sortedBy { it.from }.flatMap { (it.from..it.to).toList() }
            if (covered != days) errors += "${sport.id}: evreler tüm günleri bir kez kapsamalı"
            for (day in program.days) {
                val tag = "${sport.id}/gün ${day.day}"
                if (day.blocks.isEmpty()) errors += "$tag: blok yok"
                for (b in day.blocks) {
                    if (b.moves.isEmpty()) errors += "$tag/${b.title}: hareket yok"
                    for (m in b.moves + b.calls) if (m !in moves) errors += "$tag/${b.title}: bilinmeyen hareket $m"
                    if (b.rounds < 1) errors += "$tag/${b.title}: rounds >= 1 olmalı"
                    when (b.mode) {
                        BlockMode.ROUND, BlockMode.CIRCUIT ->
                            if (b.work <= 0 || b.reps != null) errors += "$tag/${b.title}: süreli blokta work > 0, reps yok"
                        BlockMode.REPS ->
                            if ((b.reps ?: 0) <= 0 || b.work != 0) errors += "$tag/${b.title}: tekrarlı blokta reps > 0, work yok"
                    }
                    if (b.mode != BlockMode.ROUND && b.calls.isNotEmpty()) errors += "$tag/${b.title}: komutlar yalnız raunt bloklarında"
                }
                if (errors.none { it.startsWith(tag) }) {
                    val min = planner.estimatedMinutes(day)
                    if (min !in MIN_MINUTES..MAX_MINUTES) errors += "$tag: süre $min dk ($MIN_MINUTES-$MAX_MINUTES olmalı)"
                }
            }
            val used = program.days.flatMap { d -> d.blocks.flatMap { it.moves + it.calls } }.toSet()
            val unused = movesForSport(sport.id).map { it.id }.filter { it !in used }
            if (unused.isNotEmpty()) errors += "${sport.id}: programda kullanılmayan hareketler $unused"
        }
        return errors
    }

    companion object {
        const val GENERAL = "general"
        const val TOTAL_DAYS = 24
        const val MIN_MINUTES = 20
        const val MAX_MINUTES = 60
        const val MIN_DAYS_PER_WEEK = 3
        const val MAX_DAYS_PER_WEEK = 5

        private val json = Json { ignoreUnknownKeys = true }

        /** [readAsset] assets köküne göre bir yol alır ve dosya içeriğini döndürür. */
        fun load(readAsset: (String) -> String): ContentLibrary {
            val sports = json.decodeFromString<List<Sport>>(readAsset("content/sports.json"))
            val moveFiles = listOf(GENERAL) + sports.map { it.id }
            val moves = moveFiles.flatMap { json.decodeFromString<List<Move>>(readAsset("content/moves_$it.json")) }
            val programs = sports.map { json.decodeFromString<TrainingProgram>(readAsset("content/training_${it.id}.json")) }
            return ContentLibrary(sports, moves, programs)
        }
    }
}
