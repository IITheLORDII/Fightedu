package com.fightedu

import androidx.health.connect.client.records.ActiveCaloriesBurnedRecord
import androidx.health.connect.client.records.ExerciseSessionRecord
import androidx.health.connect.client.records.metadata.Metadata
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.fightedu.core.health.WorkoutKind
import com.fightedu.core.health.WorkoutRecord
import com.fightedu.health.HealthConnectGateway
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import java.time.ZoneId

@RunWith(AndroidJUnit4::class)
class HealthConnectRecordsTest {
    private val record = WorkoutRecord(
        id = "fightedu:7:boxing:day_3:1700000000000",
        sportId = "boxing",
        kind = WorkoutKind.BOXING,
        title = "Gün 3: Blok ve Savuşturma",
        startEpochMs = 1_700_000_000_000,
        endEpochMs = 1_700_002_400_000,
        activeSeconds = 2100,
        kcal = 245.0,
    )

    @Test
    fun `antrenman ve kalori kaydı doğru tür, saat ve kimlikle üretilir`() {
        val records = HealthConnectGateway.toRecords(record, ZoneId.of("Europe/Istanbul"))
        assertEquals(2, records.size)
        val session = records[0] as ExerciseSessionRecord
        assertEquals(ExerciseSessionRecord.EXERCISE_TYPE_BOXING, session.exerciseType)
        assertEquals(record.title, session.title)
        assertEquals(record.startEpochMs, session.startTime.toEpochMilli())
        assertEquals(record.endEpochMs, session.endTime.toEpochMilli())
        assertEquals("aynı antrenman tekrar yazılırsa güncellenir", record.id, session.metadata.clientRecordId)
        assertEquals(Metadata.RECORDING_METHOD_ACTIVELY_RECORDED, session.metadata.recordingMethod)
        assertEquals(3 * 3600, session.startZoneOffset?.totalSeconds)
        val kcal = records[1] as ActiveCaloriesBurnedRecord
        assertEquals(245.0, kcal.energy.inKilocalories, 0.001)
        assertEquals("${record.id}:kcal", kcal.metadata.clientRecordId)
    }

    @Test
    fun `türler eşlenir, kalorisi olmayan seansta yalnız antrenman yazılır`() {
        assertEquals(ExerciseSessionRecord.EXERCISE_TYPE_MARTIAL_ARTS, HealthConnectGateway.exerciseType(WorkoutKind.MARTIAL_ARTS))
        assertEquals(ExerciseSessionRecord.EXERCISE_TYPE_HIGH_INTENSITY_INTERVAL_TRAINING,
            HealthConnectGateway.exerciseType(WorkoutKind.HIIT))
        assertEquals(ExerciseSessionRecord.EXERCISE_TYPE_STRETCHING, HealthConnectGateway.exerciseType(WorkoutKind.STRETCHING))
        val records = HealthConnectGateway.toRecords(record.copy(kcal = 0.0))
        assertEquals(1, records.size)
        // bitiş başlangıçtan önce/eşitse en az 1 sn'lik geçerli aralık
        val same = HealthConnectGateway.toRecords(record.copy(endEpochMs = record.startEpochMs, kcal = 0.0))
        assertTrue((same[0] as ExerciseSessionRecord).endTime.isAfter((same[0] as ExerciseSessionRecord).startTime))
    }

    @Test
    fun `izinler tek ekranda istenecek dört izin`() {
        assertEquals(4, HealthConnectGateway.PERMISSIONS.size)
        assertTrue(HealthConnectGateway.PERMISSIONS.all { it.startsWith("android.permission.health.") })
    }
}
