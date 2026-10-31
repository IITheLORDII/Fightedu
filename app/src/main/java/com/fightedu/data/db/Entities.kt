package com.fightedu.data.db

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/** Cihazdaki yerel hesap. Misafirde e-posta ve şifre yok. Şifre yalnızca PBKDF2 özeti + tuz olarak saklanır. */
@Entity(tableName = "users", indices = [Index(value = ["email"], unique = true)])
data class UserEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val name: String,
    val email: String?,
    val passwordHash: String?,
    val passwordSalt: String?,
    val isGuest: Boolean,
    val createdAt: Long,
)

/** Kullanıcının seçtiği dal ve ayarları (kullanıcı başına bir satır; satır yoksa dal seçilmemiş). */
@Entity(tableName = "user_plan")
data class UserPlanEntity(
    @PrimaryKey val userId: Long,
    val sportId: String,
    /** Hatırlatıcı günleri: Pazartesi = bit 0 ... Pazar = bit 6 (varsayılan her gün). */
    val daysMask: Int = ALL_DAYS,
    val reminderEnabled: Boolean = false,
    val reminderHour: Int = 18,
    /** Antrenmanda Türkçe sesli koç. */
    val voiceCoach: Boolean = true,
    val vibration: Boolean = true,
) {
    companion object {
        const val ALL_DAYS = 0b1111111
    }
}

/**
 * Tamamlanan meydan okuma günü (dal başına): antrenman için "day_N", dinlenme için "rest_N"
 * (bkz. ProgressTracker.keyOf, ChallengeProgress.restKey). Dal değiştirmek ilerlemeyi silmez.
 */
@Entity(tableName = "completed_sessions", primaryKeys = ["userId", "sportId", "sessionKey"])
data class CompletedSessionEntity(
    val userId: Long,
    val sportId: String,
    val sessionKey: String,
    val completedAt: Long,
)

/** Kullanıcının bir şey tamamladığı günler (epoch günü) — seri (streak) hesabı için. */
@Entity(tableName = "activity_days", primaryKeys = ["userId", "epochDay"])
data class ActivityDayEntity(
    val userId: Long,
    val epochDay: Long,
)

/** Dal başına tamamlanan gün sayısı (dal seçim ekranındaki "8/30" için). */
data class SportCount(val sportId: String, val done: Int)
