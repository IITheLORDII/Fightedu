package com.fightedu.data

import androidx.room.withTransaction
import com.fightedu.core.domain.PlanConfig
import com.fightedu.data.db.AppDatabase
import com.fightedu.data.db.CompletedSessionEntity
import com.fightedu.data.db.UserPlanEntity
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import java.time.LocalDate

data class ReminderSettings(val enabled: Boolean, val hour: Int)

/** Kullanıcı planı ve ilerlemesinin cihazdaki (Room) kaydı. */
class TrainingRepository(private val db: AppDatabase) {
    private val planDao = db.planDao()
    private val progressDao = db.progressDao()

    val plan: Flow<PlanConfig?> = planDao.observe().map { it?.toConfig() }

    val reminder: Flow<ReminderSettings> = planDao.observe().map {
        ReminderSettings(it?.reminderEnabled ?: false, it?.reminderHour ?: DEFAULT_REMINDER_HOUR)
    }

    val completedKeys: Flow<Set<String>> = progressDao.observeAll().map { list -> list.map { it.sessionKey }.toSet() }

    suspend fun currentPlan(): PlanConfig? = planDao.get()?.toConfig()

    suspend fun completedKeysNow(): Set<String> = progressDao.keys().toSet()

    suspend fun reminderNow(): ReminderSettings {
        val p = planDao.get()
        return ReminderSettings(p?.reminderEnabled ?: false, p?.reminderHour ?: DEFAULT_REMINDER_HOUR)
    }

    /** Yeni program oluşturur; önceki ilerleme silinir, hatırlatıcı ayarı korunur. */
    suspend fun startPlan(config: PlanConfig) {
        db.withTransaction {
            val old = planDao.get()
            progressDao.clear()
            planDao.upsert(
                UserPlanEntity(
                    sportId = config.sportId,
                    daysMask = PlanConfig.daysToMask(config.trainingDays),
                    startEpochDay = config.startDate.toEpochDay(),
                    reminderEnabled = old?.reminderEnabled ?: false,
                    reminderHour = old?.reminderHour ?: DEFAULT_REMINDER_HOUR,
                ),
            )
        }
    }

    suspend fun setReminder(enabled: Boolean, hour: Int) {
        val current = planDao.get() ?: return
        planDao.upsert(current.copy(reminderEnabled = enabled, reminderHour = hour))
    }

    suspend fun markCompleted(sessionKey: String) {
        progressDao.insert(CompletedSessionEntity(sessionKey, System.currentTimeMillis()))
    }

    suspend fun unmarkCompleted(sessionKey: String) = progressDao.delete(sessionKey)

    suspend fun reset() {
        db.withTransaction {
            progressDao.clear()
            planDao.clear()
        }
    }

    private fun UserPlanEntity.toConfig() = PlanConfig(
        sportId = sportId,
        trainingDays = PlanConfig.maskToDays(daysMask),
        startDate = LocalDate.ofEpochDay(startEpochDay),
    )

    companion object {
        const val DEFAULT_REMINDER_HOUR = 18
    }
}
