package com.fightedu.core.health

import kotlin.math.max
import kotlin.math.roundToInt

/** Sağlık uygulamalarındaki antrenman türleri (Health Connect / ileride HealthKit karşılıkları). */
enum class WorkoutKind { BOXING, MARTIAL_ARTS, HIIT, STRETCHING }

/** Sağlık uygulamasına yazılacak, biten bir antrenman. */
data class WorkoutRecord(
    /** Kalıcı kimlik: aynı antrenman ikinci kez yazılırsa yeni kayıt açılmaz, mevcut güncellenir. */
    val id: String,
    val sportId: String,
    val kind: WorkoutKind,
    val title: String,
    val startEpochMs: Long,
    val endEpochMs: Long,
    /** Duraklatmalar hariç aktif süre (sn). */
    val activeSeconds: Int,
    /** Tahmini aktif kalori (kcal; bazal metabolizma hariç). */
    val kcal: Double,
)

/** Oynatıcıda biten bir seans: duvar saati başlangıç/bitiş ve duraklatmalar hariç aktif süre. */
data class WorkoutSummary(val startEpochMs: Long, val endEpochMs: Long, val activeSeconds: Int)

/** Antrenman süresince saatten gelen nabız (bpm). */
data class HeartRateSummary(val average: Int, val max: Int)

enum class HealthAvailability {
    /** Bağlanılabilir. */
    AVAILABLE,

    /** Health Connect kurulu değil (Android 13 ve öncesi) ya da cihaz desteklemiyor. */
    NOT_INSTALLED,

    /** Health Connect güncellenmeli. */
    UPDATE_REQUIRED,
}

/**
 * Platform sağlık deposu. Android'de Health Connect (Samsung Health, Google Fit vb. buradan okur);
 * ileride iOS sürümünde Apple Health (HealthKit) aynı arayüzü uygular.
 */
interface HealthGateway {
    fun availability(): HealthAvailability

    /** Uygulamanın istediği tüm izinler verilmiş mi (tek izin ekranında istenir). */
    suspend fun hasAllPermissions(): Boolean

    suspend fun writeWorkout(record: WorkoutRecord)

    /** En son kilo kaydı (kg); izin yoksa ya da kayıt yoksa null. */
    suspend fun latestWeightKg(): Double?

    /** [startEpochMs]-[endEpochMs] arasındaki nabız özeti; saat yoksa ya da izin yoksa null. */
    suspend fun heartRate(startEpochMs: Long, endEpochMs: Long): HeartRateSummary?
}

object Workouts {
    /** Dalın sağlık uygulamasındaki antrenman türü; dinlenme günü esnemesi her dalda STRETCHING. */
    fun kindOf(sportId: String, restDay: Boolean = false): WorkoutKind = when {
        restDay -> WorkoutKind.STRETCHING
        sportId == "boxing" -> WorkoutKind.BOXING
        sportId == "kickboxing" || sportId == "taekwondo" || sportId == "wrestling" -> WorkoutKind.MARTIAL_ARTS
        else -> WorkoutKind.HIIT
    }

    /** Aynı kullanıcının aynı günü aynı anda başlattığı antrenman için hep aynı kimlik. */
    fun recordId(userId: Long, sportId: String, sessionKey: String, startEpochMs: Long): String =
        "fightedu:$userId:$sportId:$sessionKey:$startEpochMs"
}

/**
 * Aktif kalori tahmini: (MET - 1) x kilo x saat. MET değerleri Compendium of Physical Activities'ten, programların
 * ısınma ve dinlenme içerdiği düşünülerek orta-yüksek yoğunluk alınmıştır; 1 MET (dinlenme) çıkarılır ki
 * sağlık uygulamasındaki bazal kaloriyle çift sayılmasın.
 */
object CalorieEstimator {
    const val DEFAULT_WEIGHT_KG = 70.0
    private const val MIN_WEIGHT_KG = 30.0
    private const val MAX_WEIGHT_KG = 250.0

    fun met(sportId: String, restDay: Boolean = false): Double = when {
        restDay -> 2.3 // esneme, hafif
        sportId == "boxing" -> 7.0 // gölge, torba, kondisyon karışık
        sportId == "kickboxing" || sportId == "taekwondo" -> 7.5
        sportId == "wrestling" -> 6.0
        else -> 8.0 // devre / HIIT
    }

    /** [weightKg] null ya da makul aralık dışındaysa [DEFAULT_WEIGHT_KG]. Sonuç bir ondalığa yuvarlanır. */
    fun activeKcal(sportId: String, activeSeconds: Int, weightKg: Double?, restDay: Boolean = false): Double {
        val kg = weightKg?.takeIf { it in MIN_WEIGHT_KG..MAX_WEIGHT_KG } ?: DEFAULT_WEIGHT_KG
        val hours = max(0, activeSeconds) / 3600.0
        val kcal = (met(sportId, restDay) - 1.0) * kg * hours
        return (kcal * 10).roundToInt() / 10.0
    }
}
