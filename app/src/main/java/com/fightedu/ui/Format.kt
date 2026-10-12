package com.fightedu.ui

import java.time.DayOfWeek
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.util.Locale

private val TR = Locale("tr", "TR")
private val SHORT_DATE = DateTimeFormatter.ofPattern("d MMM", TR)
private val LONG_DATE = DateTimeFormatter.ofPattern("d MMMM yyyy, EEEE", TR)

val DayOfWeek.shortTr: String
    get() = when (this) {
        DayOfWeek.MONDAY -> "Pzt"
        DayOfWeek.TUESDAY -> "Sal"
        DayOfWeek.WEDNESDAY -> "Çar"
        DayOfWeek.THURSDAY -> "Per"
        DayOfWeek.FRIDAY -> "Cum"
        DayOfWeek.SATURDAY -> "Cmt"
        DayOfWeek.SUNDAY -> "Paz"
    }

val DayOfWeek.longTr: String
    get() = when (this) {
        DayOfWeek.MONDAY -> "Pazartesi"
        DayOfWeek.TUESDAY -> "Salı"
        DayOfWeek.WEDNESDAY -> "Çarşamba"
        DayOfWeek.THURSDAY -> "Perşembe"
        DayOfWeek.FRIDAY -> "Cuma"
        DayOfWeek.SATURDAY -> "Cumartesi"
        DayOfWeek.SUNDAY -> "Pazar"
    }

/** "14 Eki Sal" gibi kısa tarih; bugün/yarın için göreli ifade. */
fun LocalDate.shortLabel(today: LocalDate = LocalDate.now()): String = when (this) {
    today -> "Bugün"
    today.plusDays(1) -> "Yarın"
    today.minusDays(1) -> "Dün"
    else -> "${format(SHORT_DATE)} ${dayOfWeek.shortTr}"
}

fun LocalDate.longLabel(): String = format(LONG_DATE)

fun formatClock(totalSec: Int): String = "%d:%02d".format(totalSec / 60, totalSec % 60)
