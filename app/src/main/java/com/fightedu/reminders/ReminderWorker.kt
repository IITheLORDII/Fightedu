package com.fightedu.reminders

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.fightedu.appContainer
import com.fightedu.core.domain.ProgressTracker
import java.time.LocalDate

/** Bugün programda tamamlanmamış bir seans varsa bildirim gösterir. */
class ReminderWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {
    override suspend fun doWork(): Result {
        val container = applicationContext.appContainer
        val repo = container.repository
        if (!repo.reminderNow().enabled) return Result.success()
        val plan = repo.currentPlan() ?: return Result.success()

        val sessions = container.planGenerator.generate(plan)
        val tracker = ProgressTracker(sessions, repo.completedKeysNow())
        val today = tracker.sessionOn(LocalDate.now())
        if (today != null && !tracker.isCompleted(today)) {
            val sport = container.content.sport(plan.sportId)?.name.orEmpty()
            ReminderNotifications.show(
                applicationContext,
                "$sport · Hafta ${today.week}: ${today.title}. Hadi başlayalım!",
            )
        }
        return Result.success()
    }
}
