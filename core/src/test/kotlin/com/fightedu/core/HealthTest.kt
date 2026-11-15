package com.fightedu.core

import com.fightedu.core.health.CalorieEstimator
import com.fightedu.core.health.WorkoutKind
import com.fightedu.core.health.Workouts
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class HealthTest {
    @Test
    fun `dallar sağlık uygulamasındaki antrenman türlerine eşlenir`() {
        assertEquals(WorkoutKind.BOXING, Workouts.kindOf("boxing"))
        assertEquals(WorkoutKind.MARTIAL_ARTS, Workouts.kindOf("kickboxing"))
        assertEquals(WorkoutKind.MARTIAL_ARTS, Workouts.kindOf("taekwondo"))
        assertEquals(WorkoutKind.MARTIAL_ARTS, Workouts.kindOf("wrestling"))
        assertEquals(WorkoutKind.HIIT, Workouts.kindOf("general"))
        assertEquals(WorkoutKind.STRETCHING, Workouts.kindOf("boxing", restDay = true))
    }

    @Test
    fun `aktif kalori MET, kilo ve süreyle hesaplanır, bazal 1 MET düşülür`() {
        // boks 7 MET: (7-1) x 70 kg x 0,5 sa = 210 kcal
        assertEquals(210.0, CalorieEstimator.activeKcal("boxing", 1800, 70.0), 0.01)
        // kilo yoksa ya da saçma değerse 70 kg
        assertEquals(210.0, CalorieEstimator.activeKcal("boxing", 1800, null), 0.01)
        assertEquals(210.0, CalorieEstimator.activeKcal("boxing", 1800, 5.0), 0.01)
        // 90 kg -> oransal artar
        assertEquals(270.0, CalorieEstimator.activeKcal("boxing", 1800, 90.0), 0.01)
        // esneme günü düşük
        assertTrue(CalorieEstimator.activeKcal("boxing", 600, 70.0, restDay = true) < 20)
        assertEquals(0.0, CalorieEstimator.activeKcal("general", 0, 70.0), 0.0)
        assertEquals(0.0, CalorieEstimator.activeKcal("general", -10, 70.0), 0.0)
    }

    @Test
    fun `kayıt kimliği aynı antrenman için sabit, farklı başlangıçta farklı`() {
        val a = Workouts.recordId(7, "boxing", "day_3", 1_700_000_000_000)
        assertEquals(a, Workouts.recordId(7, "boxing", "day_3", 1_700_000_000_000))
        assertNotEquals(a, Workouts.recordId(7, "boxing", "day_3", 1_700_000_100_000))
        assertNotEquals(a, Workouts.recordId(8, "boxing", "day_3", 1_700_000_000_000))
    }
}
