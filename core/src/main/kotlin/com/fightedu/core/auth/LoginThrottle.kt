package com.fightedu.core.auth

/**
 * Yanlış şifre denemelerini sınırlar (e-posta başına). [FREE_ATTEMPTS] hatadan sonra her yeni hata bekleme süresini
 * ikiye katlar: 30 sn, 1 dk, 2 dk ... en fazla [MAX_LOCK_MS]. Başarılı giriş sayacı sıfırlar.
 * Saat dışarıdan verilir (test edilebilirlik); durum bellekte tutulur, uygulama kapanınca sıfırlanır.
 */
class LoginThrottle(private val now: () -> Long = System::currentTimeMillis) {
    private data class Entry(val failures: Int, val lockedUntil: Long)

    private val entries = HashMap<String, Entry>()

    /** Bu e-posta için kalan bekleme süresi (ms); 0 ise denenebilir. */
    @Synchronized
    fun remainingLockMs(key: String): Long {
        val e = entries[key] ?: return 0
        return (e.lockedUntil - now()).coerceAtLeast(0)
    }

    @Synchronized
    fun onFailure(key: String) {
        val failures = (entries[key]?.failures ?: 0) + 1
        val lock = if (failures < FREE_ATTEMPTS) 0L else {
            val steps = (failures - FREE_ATTEMPTS).coerceAtMost(10)
            (BASE_LOCK_MS shl steps).coerceAtMost(MAX_LOCK_MS)
        }
        entries[key] = Entry(failures, if (lock > 0) now() + lock else 0L)
    }

    @Synchronized
    fun onSuccess(key: String) {
        entries.remove(key)
    }

    companion object {
        const val FREE_ATTEMPTS = 5
        const val BASE_LOCK_MS = 30_000L
        const val MAX_LOCK_MS = 15 * 60_000L

        /** "Çok fazla deneme" mesajı için okunur süre. */
        fun describe(ms: Long): String {
            val sec = ((ms + 999) / 1000).coerceAtLeast(1)
            return if (sec < 60) "$sec sn" else "${(sec + 59) / 60} dk"
        }
    }
}
