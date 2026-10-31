package com.fightedu.core.voice

/** Sayıları Türkçe kelimeyle yazar (sesli koç rakam okumasın): 45 -> "kırk beş", 3 -> "üçüncü". */
object TurkishNumbers {
    private val ONES = listOf("", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz")
    private val TENS = listOf("", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan")
    private val ORD = mapOf(
        "bir" to "birinci", "iki" to "ikinci", "üç" to "üçüncü", "dört" to "dördüncü", "beş" to "beşinci",
        "altı" to "altıncı", "yedi" to "yedinci", "sekiz" to "sekizinci", "dokuz" to "dokuzuncu", "on" to "onuncu",
        "yirmi" to "yirminci", "otuz" to "otuzuncu", "kırk" to "kırkıncı", "elli" to "ellinci",
        "altmış" to "altmışıncı", "yetmiş" to "yetmişinci", "seksen" to "sekseninci", "doksan" to "doksanıncı",
        "yüz" to "yüzüncü",
    )

    fun cardinal(n: Int): String {
        if (n == 0) return "sıfır"
        require(n in 1..999) { "1..999: $n" }
        val parts = mutableListOf<String>()
        var x = n
        if (x >= 100) {
            val h = x / 100
            parts += if (h == 1) "yüz" else "${ONES[h]} yüz"
            x %= 100
        }
        if (x >= 10) {
            parts += TENS[x / 10]
            x %= 10
        }
        if (x > 0) parts += ONES[x]
        return parts.joinToString(" ")
    }

    fun ordinal(n: Int): String {
        val words = cardinal(n).split(" ").toMutableList()
        words[words.lastIndex] = ORD.getValue(words.last())
        return words.joinToString(" ")
    }

    /** 45 -> "kırk beş saniye", 60 -> "bir dakika", 90 -> "bir buçuk dakika". */
    fun duration(seconds: Int): String {
        if (seconds < 60) return "${cardinal(seconds)} saniye"
        val m = seconds / 60
        val s = seconds % 60
        return when (s) {
            0 -> "${cardinal(m)} dakika"
            30 -> "${cardinal(m)} buçuk dakika"
            else -> "${cardinal(m)} dakika ${cardinal(s)} saniye"
        }
    }
}
