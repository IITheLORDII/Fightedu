package com.fightedu.reminders

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.fightedu.appContainer
import com.fightedu.core.domain.ProgressTracker
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId

/** Seçilen antrenman günlerinde, sıradaki gün henüz bugün yapılmadıysa bildirim gösterir. */
class ReminderWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {
    override suspend fun doWork(): Result {
        val container = applicationContext.appContainer
        val repo = container.repository
        if (!repo.reminderNow().enabled) return Result.success()
        val plan = repo.currentPlan() ?: return Result.success()
        if (LocalDate.now().dayOfWeek !in plan.trainingDays) return Result.success()
        val last = repo.lastCompletedAt()?.let {
            Instant.ofEpochMilli(it).atZone(ZoneId.systemDefault()).toLocalDate()
        }
        if (last == LocalDate.now()) return Result.success() // bugünkü antrenman yapıldı
        val program = container.content.program(plan.sportId) ?: return Result.success()
        val tracker = ProgressTracker(program, ProgressTracker.daysFromKeys(repo.completedKeysNow()))
        val next = tracker.nextDay ?: return Result.success()
        val sport = container.content.sport(plan.sportId)?.name.orEmpty()
        ReminderNotifications.show(
            applicationContext,
            "$sport · Gün ${next.day}: ${next.title}. Antrenmanın seni bekliyor!",
        )
        return Result.success()
    }
}
