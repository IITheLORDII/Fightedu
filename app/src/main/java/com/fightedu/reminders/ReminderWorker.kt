package com.fightedu.reminders

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.fightedu.appContainer
import com.fightedu.core.domain.ChallengeDay
import com.fightedu.core.domain.ChallengeProgress
import com.fightedu.core.domain.PlanConfig
import java.time.LocalDate

/** Hatırlatıcı açıksa ve kullanıcı bugün henüz bir şey tamamlamadıysa meydan okumanın sıradaki gününü hatırlatır. */
class ReminderWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {
    override suspend fun doWork(): Result {
        val container = applicationContext.appContainer
        val repo = container.repository
        val userId = container.session.current ?: return Result.success()
        val plan = repo.planNow(userId) ?: return Result.success()
        if (!plan.reminderEnabled) return Result.success()
        if (LocalDate.now().dayOfWeek !in PlanConfig.maskToDays(plan.daysMask)) return Result.success()
        val program = container.content.program(plan.sportId) ?: return Result.success()
        val progress = ChallengeProgress(
            program,
            repo.completedKeysNow(userId, plan.sportId),
            repo.activityDaysNow(userId),
        )
        if (progress.trainedToday) return Result.success() // bugün zaten çalıştı
        val next = progress.current ?: return Result.success()
        val sport = container.content.sport(plan.sportId)?.name.orEmpty()
        val text = when (next) {
            is ChallengeDay.Workout -> "$sport · Gün ${next.number}/30: ${next.training.title}. Antrenmanın seni bekliyor!"
            is ChallengeDay.Rest -> "$sport · Gün ${next.number}/30 dinlenme günü. 8 dakikalık esneme ister misin?"
        }
        val streak = progress.currentStreak
        ReminderNotifications.show(applicationContext, if (streak > 1) "$text 🔥 $streak günlük serini bozma." else text)
        return Result.success()
    }
}
