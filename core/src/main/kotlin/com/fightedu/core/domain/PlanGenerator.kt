package com.fightedu.core.domain

import com.fightedu.core.content.ContentLibrary
import com.fightedu.core.model.ExerciseRef
import java.time.LocalDate
import kotlin.math.roundToInt

/**
 * Spor şablonunu ve kullanıcının gün seçimini takvimli bir programa dönüştürür.
 *
 * - Her hafta, o haftanın evresindeki seans şablonlarının ilk N tanesi kullanılır
 *   (3 gün: A,B,C · 4 gün: +D · 5 gün: +E).
 * - Seanslar başlangıç tarihinden itibaren seçilen gün adlarına sırayla yerleştirilir;
 *   böylece her antrenman haftası tam N seans içerir.
 * - Bir evrenin ikinci haftasında ana bölümün tekrar/süreleri %15 artırılır (kademeli yüklenme).
 */
class PlanGenerator(private val library: ContentLibrary) {

    fun generate(config: PlanConfig): List<PlannedSession> {
        val n = config.daysPerWeek
        require(n in ContentLibrary.MIN_DAYS_PER_WEEK..ContentLibrary.MAX_DAYS_PER_WEEK) {
            "Haftada ${ContentLibrary.MIN_DAYS_PER_WEEK}-${ContentLibrary.MAX_DAYS_PER_WEEK} gün seçilmeli (seçilen: $n)"
        }
        val program = requireNotNull(library.program(config.sportId)) { "Program bulunamadı: ${config.sportId}" }
        val weeks = program.totalWeeks
        val dates = trainingDates(config, weeks * n)

        val sessions = mutableListOf<PlannedSession>()
        for (week in 1..weeks) {
            val phase = requireNotNull(program.phaseForWeek(week)) { "Hafta $week için evre yok" }
            val weekInPhase = phase.weeks.sorted().indexOf(week)
            val factor = 1.0 + PROGRESSION_PER_WEEK * weekInPhase
            phase.sessions.take(n).forEachIndexed { index, template ->
                sessions += PlannedSession(
                    week = week,
                    index = index,
                    date = dates[(week - 1) * n + index],
                    code = template.code,
                    title = template.title,
                    phaseTitle = phase.title,
                    phaseGoal = phase.goal,
                    warmup = program.warmup.map { resolve(it, Section.WARMUP, 1.0) },
                    main = template.main.map { resolve(it, Section.MAIN, factor) },
                    cooldown = program.cooldown.map { resolve(it, Section.COOLDOWN, 1.0) },
                )
            }
        }
        return sessions
    }

    private fun resolve(ref: ExerciseRef, section: Section, factor: Double): PlannedExercise {
        val move = requireNotNull(library.move(ref.move)) { "Hareket bulunamadı: ${ref.move}" }
        return PlannedExercise(
            move = move,
            section = section,
            sets = ref.sets,
            reps = ref.reps?.let { (it * factor).roundToInt() },
            sec = ref.sec?.let { roundTo5(it * factor) },
            rest = ref.rest,
        )
    }

    private fun roundTo5(v: Double): Int = ((v / 5.0).roundToInt() * 5).coerceAtLeast(5)

    companion object {
        const val PROGRESSION_PER_WEEK = 0.15

        /** Başlangıç tarihinden (dahil) itibaren seçilen günlere denk gelen ilk [count] tarih. */
        fun trainingDates(config: PlanConfig, count: Int): List<LocalDate> {
            require(config.trainingDays.isNotEmpty())
            val result = ArrayList<LocalDate>(count)
            var d = config.startDate
            while (result.size < count) {
                if (d.dayOfWeek in config.trainingDays) result += d
                d = d.plusDays(1)
            }
            return result
        }
    }
}
