package com.fightedu.data.db

import androidx.room.Entity
import androidx.room.PrimaryKey

/** Tek satırlık aktif program kaydı (id her zaman 1). */
@Entity(tableName = "user_plan")
data class UserPlanEntity(
    @PrimaryKey val id: Int = 1,
    val sportId: String,
    /** Pazartesi = bit 0 ... Pazar = bit 6 */
    val daysMask: Int,
    val startEpochDay: Long,
    val reminderEnabled: Boolean = false,
    val reminderHour: Int = 18,
)

/** Tamamlanan seans; anahtar PlannedSession.key ("w3_d1"). */
@Entity(tableName = "completed_sessions")
data class CompletedSessionEntity(
    @PrimaryKey val sessionKey: String,
    val completedAt: Long,
)
