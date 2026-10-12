package com.fightedu.core.domain

/** Antrenman oynatıcısının sırayla göstereceği adımlar. */
sealed interface WorkoutStep {
    /** Bir hareketin tek bir seti. [seconds] null ise tekrar bazlıdır, kullanıcı "Bitti" der. */
    data class Work(
        val exercise: PlannedExercise,
        val set: Int,
        val totalSets: Int,
    ) : WorkoutStep {
        val seconds: Int? get() = exercise.sec
    }

    data class Rest(
        val seconds: Int,
        val next: PlannedExercise,
    ) : WorkoutStep
}

object WorkoutPlanner {
    /** Tekrar bazlı setlerin süre tahmini için bir tekrarın ortalama süresi. */
    const val SECONDS_PER_REP = 3

    fun steps(session: PlannedSession): List<WorkoutStep> {
        val steps = mutableListOf<WorkoutStep>()
        val exercises = session.exercises
        exercises.forEachIndexed { i, ex ->
            for (set in 1..ex.sets) {
                steps += WorkoutStep.Work(ex, set, ex.sets)
                val isLastSet = set == ex.sets
                val next = if (isLastSet) exercises.getOrNull(i + 1) else ex
                if (next != null && ex.rest > 0) steps += WorkoutStep.Rest(ex.rest, next)
            }
        }
        return steps
    }

    fun estimatedSeconds(session: PlannedSession): Int = steps(session).sumOf {
        when (it) {
            is WorkoutStep.Work -> it.seconds ?: ((it.exercise.reps ?: 0) * SECONDS_PER_REP)
            is WorkoutStep.Rest -> it.seconds
        }
    }

    fun estimatedMinutes(session: PlannedSession): Int = (estimatedSeconds(session) + 59) / 60
}
