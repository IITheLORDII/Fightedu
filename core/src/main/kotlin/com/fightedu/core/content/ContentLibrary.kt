package com.fightedu.core.content

import com.fightedu.core.model.Move
import com.fightedu.core.model.ProgramTemplate
import com.fightedu.core.model.Sport
import kotlinx.serialization.json.Json

/** Uygulamanın tüm statik içeriği (sporlar, hareketler, program şablonları). */
class ContentLibrary(
    val sports: List<Sport>,
    moves: List<Move>,
    programs: List<ProgramTemplate>,
) {
    val moves: Map<String, Move> = moves.associateBy { it.id }
    val programs: Map<String, ProgramTemplate> = programs.associateBy { it.sport }

    fun sport(id: String): Sport? = sports.firstOrNull { it.id == id }
    fun move(id: String): Move? = moves[id]
    fun program(sportId: String): ProgramTemplate? = programs[sportId]
    fun movesForSport(sportId: String): List<Move> = moves.values.filter { it.sport == sportId }

    /**
     * İçerik tutarlılığını kontrol eder; boş liste = sorun yok.
     * [assetExists] verilirse her hareketin animasyon dosyası da aranır.
     */
    fun validate(assetExists: ((String) -> Boolean)? = null): List<String> {
        val errors = mutableListOf<String>()
        val sportIds = sports.map { it.id }.toSet()
        for (move in moves.values) {
            if (move.sport != GENERAL && move.sport !in sportIds) errors += "${move.id}: bilinmeyen spor ${move.sport}"
            if (move.steps.isEmpty()) errors += "${move.id}: adım yok"
            if (move.level !in 1..3) errors += "${move.id}: seviye 1-3 olmalı"
            if (assetExists != null && !assetExists(move.lottieAsset)) errors += "${move.id}: animasyon yok (${move.lottieAsset})"
        }
        for (sport in sports) {
            val program = programs[sport.id]
            if (program == null) {
                errors += "${sport.id}: program şablonu yok"
                continue
            }
            val weeks = program.phases.flatMap { it.weeks }.sorted()
            if (weeks != (1..weeks.size).toList()) errors += "${sport.id}: haftalar 1..N ardışık olmalı ($weeks)"
            if (weeks.size < MIN_WEEKS) errors += "${sport.id}: program en az $MIN_WEEKS hafta olmalı"
            val refs = program.warmup + program.cooldown + program.phases.flatMap { p -> p.sessions.flatMap { it.main } }
            for (ref in refs) {
                if (ref.move !in moves) errors += "${sport.id}: bilinmeyen hareket ${ref.move}"
                if ((ref.reps == null) == (ref.sec == null)) errors += "${sport.id}/${ref.move}: reps veya sec'ten tam olarak biri olmalı"
                if (ref.sets < 1) errors += "${sport.id}/${ref.move}: sets >= 1 olmalı"
            }
            for (phase in program.phases) {
                if (phase.sessions.size < MAX_DAYS_PER_WEEK) {
                    errors += "${sport.id}/${phase.title}: en az $MAX_DAYS_PER_WEEK seans şablonu olmalı"
                }
            }
        }
        return errors
    }

    companion object {
        const val GENERAL = "general"
        const val MIN_WEEKS = 8
        const val MIN_DAYS_PER_WEEK = 3
        const val MAX_DAYS_PER_WEEK = 5

        private val json = Json { ignoreUnknownKeys = true }

        /** [readAsset] assets köküne göre bir yol alır ve dosya içeriğini döndürür. */
        fun load(readAsset: (String) -> String): ContentLibrary {
            val sports = json.decodeFromString<List<Sport>>(readAsset("content/sports.json"))
            val moveFiles = listOf(GENERAL) + sports.map { it.id }
            val moves = moveFiles.flatMap { json.decodeFromString<List<Move>>(readAsset("content/moves_$it.json")) }
            val programs = sports.map { json.decodeFromString<ProgramTemplate>(readAsset("content/program_${it.id}.json")) }
            return ContentLibrary(sports, moves, programs)
        }
    }
}
