package com.fightedu.health

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import androidx.activity.result.contract.ActivityResultContract
import androidx.health.connect.client.HealthConnectClient
import androidx.health.connect.client.PermissionController
import androidx.health.connect.client.permission.HealthPermission
import androidx.health.connect.client.records.ActiveCaloriesBurnedRecord
import androidx.health.connect.client.records.ExerciseSessionRecord
import androidx.health.connect.client.records.HeartRateRecord
import androidx.health.connect.client.records.Record
import androidx.health.connect.client.records.WeightRecord
import androidx.health.connect.client.records.metadata.Device
import androidx.health.connect.client.records.metadata.Metadata
import androidx.health.connect.client.request.AggregateRequest
import androidx.health.connect.client.request.ReadRecordsRequest
import androidx.health.connect.client.time.TimeRangeFilter
import androidx.health.connect.client.units.Energy
import com.fightedu.core.health.HealthAvailability
import com.fightedu.core.health.HealthGateway
import com.fightedu.core.health.HeartRateSummary
import com.fightedu.core.health.WorkoutKind
import com.fightedu.core.health.WorkoutRecord
import java.time.Duration
import java.time.Instant
import java.time.ZoneId

/**
 * Android'de sağlık deposu: Health Connect. Samsung Health (Ayarlar > Health Connect senkronu açıkken), Google Fit ve
 * diğer sağlık uygulamaları kayıtları buradan alır. Tüm izinler tek bir sistem ekranında birlikte istenir.
 * Hiçbir sağlık verisi cihaz dışına gönderilmez; uygulamanın internet izni yoktur.
 */
class HealthConnectGateway(context: Context) : HealthGateway {
    private val appContext = context.applicationContext
    private val client: HealthConnectClient? by lazy {
        if (availability() == HealthAvailability.AVAILABLE) HealthConnectClient.getOrCreate(appContext) else null
    }

    override fun availability(): HealthAvailability =
        when (HealthConnectClient.getSdkStatus(appContext, PROVIDER)) {
            HealthConnectClient.SDK_AVAILABLE -> HealthAvailability.AVAILABLE
            HealthConnectClient.SDK_UNAVAILABLE_PROVIDER_UPDATE_REQUIRED -> HealthAvailability.UPDATE_REQUIRED
            else -> HealthAvailability.NOT_INSTALLED
        }

    override suspend fun hasAllPermissions(): Boolean {
        val c = client ?: return false
        return runCatching { c.permissionController.getGrantedPermissions().containsAll(PERMISSIONS) }.getOrDefault(false)
    }

    override suspend fun writeWorkout(record: WorkoutRecord) {
        val c = client ?: throw IllegalStateException("Health Connect kullanılamıyor")
        c.insertRecords(toRecords(record))
    }

    override suspend fun latestWeightKg(): Double? {
        val c = client ?: return null
        return runCatching {
            val now = Instant.now()
            c.readRecords(
                ReadRecordsRequest(
                    recordType = WeightRecord::class,
                    timeRangeFilter = TimeRangeFilter.between(now.minus(Duration.ofDays(365)), now),
                    ascendingOrder = false,
                    pageSize = 1,
                ),
            ).records.firstOrNull()?.weight?.inKilograms
        }.getOrNull()
    }

    override suspend fun heartRate(startEpochMs: Long, endEpochMs: Long): HeartRateSummary? {
        val c = client ?: return null
        if (endEpochMs <= startEpochMs) return null
        return runCatching {
            val result = c.aggregate(
                AggregateRequest(
                    metrics = setOf(HeartRateRecord.BPM_AVG, HeartRateRecord.BPM_MAX),
                    timeRangeFilter = TimeRangeFilter.between(
                        Instant.ofEpochMilli(startEpochMs), Instant.ofEpochMilli(endEpochMs),
                    ),
                ),
            )
            val avg = result[HeartRateRecord.BPM_AVG] ?: return@runCatching null
            val max = result[HeartRateRecord.BPM_MAX] ?: avg
            HeartRateSummary(avg.toInt(), max.toInt())
        }.getOrNull()
    }

    companion object {
        const val PROVIDER = HealthConnectClient.DEFAULT_PROVIDER_PACKAGE_NAME

        /** Tek izin ekranında birlikte istenen izinler. */
        val PERMISSIONS: Set<String> = setOf(
            HealthPermission.getWritePermission(ExerciseSessionRecord::class),
            HealthPermission.getWritePermission(ActiveCaloriesBurnedRecord::class),
            HealthPermission.getReadPermission(WeightRecord::class),
            HealthPermission.getReadPermission(HeartRateRecord::class),
        )

        /** Health Connect'in tek ekranlık izin isteği (ActivityResult sözleşmesi). */
        fun permissionContract(): ActivityResultContract<Set<String>, Set<String>> =
            PermissionController.createRequestPermissionResultContract(PROVIDER)

        fun exerciseType(kind: WorkoutKind): Int = when (kind) {
            WorkoutKind.BOXING -> ExerciseSessionRecord.EXERCISE_TYPE_BOXING
            WorkoutKind.MARTIAL_ARTS -> ExerciseSessionRecord.EXERCISE_TYPE_MARTIAL_ARTS
            WorkoutKind.HIIT -> ExerciseSessionRecord.EXERCISE_TYPE_HIGH_INTENSITY_INTERVAL_TRAINING
            WorkoutKind.STRETCHING -> ExerciseSessionRecord.EXERCISE_TYPE_STRETCHING
        }

        /** Antrenman ve kalori kayıtları; aynı [WorkoutRecord.id] tekrar yazılırsa Health Connect günceller. */
        fun toRecords(r: WorkoutRecord, zone: ZoneId = ZoneId.systemDefault()): List<Record> {
            val start = Instant.ofEpochMilli(r.startEpochMs)
            val end = Instant.ofEpochMilli(maxOf(r.endEpochMs, r.startEpochMs + 1_000))
            val startOffset = zone.rules.getOffset(start)
            val endOffset = zone.rules.getOffset(end)
            val device = Device(type = Device.TYPE_PHONE)
            val session = ExerciseSessionRecord(
                startTime = start,
                startZoneOffset = startOffset,
                endTime = end,
                endZoneOffset = endOffset,
                metadata = Metadata.activelyRecorded(device = device, clientRecordId = r.id, clientRecordVersion = 1L),
                exerciseType = exerciseType(r.kind),
                title = r.title,
            )
            if (r.kcal <= 0.0) return listOf(session)
            val calories = ActiveCaloriesBurnedRecord(
                startTime = start,
                startZoneOffset = startOffset,
                endTime = end,
                endZoneOffset = endOffset,
                energy = Energy.kilocalories(r.kcal),
                metadata = Metadata.activelyRecorded(device = device, clientRecordId = "${r.id}:kcal",
                    clientRecordVersion = 1L),
            )
            return listOf(session, calories)
        }

        /** Health Connect kurulu değilse ya da eskiyse Play Store sayfası. */
        fun installIntent(): Intent = Intent(Intent.ACTION_VIEW).apply {
            setPackage("com.android.vending")
            data = Uri.parse("market://details?id=$PROVIDER&url=healthconnect%3A%2F%2Fonboarding")
            putExtra("overlay", true)
            putExtra("callerId", "com.fightedu")
        }

        /** Health Connect ayarları (Samsung Health senkronu ve uygulama izinleri buradan yönetilir). */
        fun settingsIntent(): Intent = Intent(
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
                "android.health.connect.action.HEALTH_HOME_SETTINGS"
            } else {
                "androidx.health.ACTION_HEALTH_CONNECT_SETTINGS"
            },
        )
    }
}
