package com.fightedu.data

import androidx.room.withTransaction
import com.fightedu.data.db.ActivityDayEntity
import com.fightedu.data.db.AppDatabase
import com.fightedu.data.db.CompletedSessionEntity
import com.fightedu.data.db.UserPlanEntity
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import java.time.LocalDate

data class ReminderSettings(val enabled: Boolean, val hour: Int)

data class CoachSettings(val voice: Boolean = true, val vibration: Boolean = true)

/** Kullanıcının seçili dalı, ayarları ve dal başına meydan okuma ilerlemesi (Room). */
class TrainingRepository(private val db: AppDatabase) {
    private val planDao = db.planDao()
    private val progressDao = db.progressDao()
    private val activityDao = db.activityDao()

    fun plan(userId: Long): Flow<UserPlanEntity?> = planDao.observe(userId)

    suspend fun planNow(userId: Long): UserPlanEntity? = planDao.get(userId)

    fun completedKeys(userId: Long, sportId: String): Flow<Set<String>> =
        progressDao.observeKeys(userId, sportId).map { it.toSet() }

    suspend fun completedKeysNow(userId: Long, sportId: String): Set<String> = progressDao.keys(userId, sportId).toSet()

    /** Dal -> tamamlanan meydan okuma günü sayısı. */
    fun sportProgress(userId: Long): Flow<Map<String, Int>> =
        progressDao.observeCounts(userId).map { list -> list.associate { it.sportId to it.done } }

    fun activityDays(userId: Long): Flow<Set<Long>> = activityDao.observe(userId).map { it.toSet() }

    suspend fun activityDaysNow(userId: Long): Set<Long> = activityDao.days(userId).toSet()

    /** Dalı seçer (ilerleme dal başına saklandığından önceki dalların ilerlemesi korunur). */
    suspend fun selectSport(userId: Long, sportId: String, reminder: ReminderSettings? = null) {
        val old = planDao.get(userId)
        val base = old?.copy(sportId = sportId) ?: UserPlanEntity(userId = userId, sportId = sportId)
        planDao.upsert(
            if (reminder == null) base else base.copy(reminderEnabled = reminder.enabled, reminderHour = reminder.hour),
        )
    }

    suspend fun setReminder(userId: Long, enabled: Boolean, hour: Int) {
        val current = planDao.get(userId) ?: return
        planDao.upsert(current.copy(reminderEnabled = enabled, reminderHour = hour))
    }

    suspend fun setCoach(userId: Long, settings: CoachSettings) {
        val current = planDao.get(userId) ?: return
        planDao.upsert(current.copy(voiceCoach = settings.voice, vibration = settings.vibration))
    }

    suspend fun markCompleted(userId: Long, sportId: String, key: String) {
        db.withTransaction {
            progressDao.insert(CompletedSessionEntity(userId, sportId, key, System.currentTimeMillis()))
            activityDao.insert(ActivityDayEntity(userId, LocalDate.now().toEpochDay()))
        }
    }

    suspend fun unmarkCompleted(userId: Long, sportId: String, key: String) = progressDao.delete(userId, sportId, key)

    /** Dalın meydan okumasını baştan başlatır. */
    suspend fun restartSport(userId: Long, sportId: String) = progressDao.clearSport(userId, sportId)

    companion object {
        const val DEFAULT_REMINDER_HOUR = 18
    }
}
