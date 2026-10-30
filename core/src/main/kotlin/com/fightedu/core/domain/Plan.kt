package com.fightedu.core.domain

import java.time.DayOfWeek

/**
 * Kullanıcının onboarding'de seçtikleri. Günler sırayla ilerler (takvim yok); seçilen hafta günleri
 * yalnızca hatırlatıcı içindir.
 */
data class PlanConfig(
    val sportId: String,
    val trainingDays: Set<DayOfWeek>,
) {
    val daysPerWeek: Int get() = trainingDays.size

    /** Haftanın günleri, Pazartesi'den başlayarak sıralı. */
    val sortedDays: List<DayOfWeek> get() = trainingDays.sortedBy { it.value }

    companion object {
        fun daysToMask(days: Set<DayOfWeek>): Int = days.fold(0) { acc, d -> acc or (1 shl (d.value - 1)) }
        fun maskToDays(mask: Int): Set<DayOfWeek> = DayOfWeek.entries.filter { mask and (1 shl (it.value - 1)) != 0 }.toSet()
    }
}

fun formatDuration(totalSec: Int): String {
    val m = totalSec / 60
    val s = totalSec % 60
    return when {
        m == 0 -> "$s sn"
        s == 0 -> "$m dk"
        else -> "$m dk $s sn"
    }
}
