package com.fightedu.core

import com.fightedu.core.auth.AccountRules
import com.fightedu.core.auth.LoginThrottle
import com.fightedu.core.auth.PasswordHasher
import com.fightedu.core.auth.StoredPassword
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class AuthTest {
    @Test
    fun `şifre özeti doğrulanır, yanlış şifre ve bozuk kayıt reddedilir`() {
        val stored = PasswordHasher.create("gizli123", iterations = 1_000)
        assertTrue(PasswordHasher.verify("gizli123", stored, iterations = 1_000))
        assertFalse(PasswordHasher.verify("gizli124", stored, iterations = 1_000))
        assertFalse(PasswordHasher.verify("gizli123", stored.copy(salt = "!!"), iterations = 1_000))
        val other = PasswordHasher.create("gizli123", iterations = 1_000)
        assertNotEquals("tuz her seferinde farklı", stored.salt, other.salt)
        assertNotEquals(stored.hash, other.hash)
        assertFalse(PasswordHasher.verify("x", StoredPassword("", ""), iterations = 1_000))
    }

    @Test
    fun `kayıt formu kuralları`() {
        assertTrue(AccountRules.validateRegister("Ali Veli", " Ali@Ornek.com ", "12345678", "12345678").isValid)
        assertNotNull("7 karakter kısa", AccountRules.passwordError("1234567"))
        assertNotNull("129 karakter uzun", AccountRules.passwordError("a".repeat(129)))
        assertNull(AccountRules.passwordError("a".repeat(128)))
        val bad = AccountRules.validateRegister("  ", "ali@", "123", "124")
        assertNotNull(bad.name)
        assertNotNull(bad.email)
        assertNotNull(bad.password)
        assertNotNull(bad.confirm)
        assertNull(AccountRules.emailError("ad.soyad+fight@mail.co.uk"))
        assertNotNull(AccountRules.emailError("ad soyad@mail.com"))
        assertNotNull(AccountRules.passwordError("        "))
        assertEquals("ali@ornek.com", AccountRules.normalizeEmail(" Ali@Ornek.COM "))
        assertEquals("İA", AccountRules.initials("ilker  akın"))
        assertEquals("?", AccountRules.initials(" "))
    }

    @Test
    fun `eski tekrar sayısıyla özetlenmiş şifre doğrulanır ve yeniden özetlenmesi istenir`() {
        val legacy = PasswordHasher.create("eskisifre1", iterations = 2_000)
        assertTrue(PasswordHasher.verify("eskisifre1", legacy, iterations = 2_000))
        assertFalse("başka tekrar sayısıyla eşleşmez", PasswordHasher.verify("eskisifre1", legacy, iterations = 3_000))
        assertTrue(PasswordHasher.needsRehash(PasswordHasher.LEGACY_ITERATIONS))
        assertFalse(PasswordHasher.needsRehash(PasswordHasher.ITERATIONS))
        assertTrue("güncel sayı OWASP önerisine yakın", PasswordHasher.ITERATIONS >= 300_000)
    }

    @Test
    fun `yanlış şifre denemeleri sınırlanır, bekleme iki katına çıkar, başarı sıfırlar`() {
        var t = 1_000_000L
        val th = LoginThrottle { t }
        repeat(LoginThrottle.FREE_ATTEMPTS - 1) { th.onFailure("a@b.co") }
        assertEquals("ilk 4 hata serbest", 0L, th.remainingLockMs("a@b.co"))
        th.onFailure("a@b.co")
        assertEquals(LoginThrottle.BASE_LOCK_MS, th.remainingLockMs("a@b.co"))
        assertEquals("başka e-posta etkilenmez", 0L, th.remainingLockMs("c@d.co"))
        t += LoginThrottle.BASE_LOCK_MS
        assertEquals(0L, th.remainingLockMs("a@b.co"))
        th.onFailure("a@b.co")
        assertEquals(2 * LoginThrottle.BASE_LOCK_MS, th.remainingLockMs("a@b.co"))
        repeat(20) { th.onFailure("a@b.co") }
        assertEquals("üst sınır", LoginThrottle.MAX_LOCK_MS, th.remainingLockMs("a@b.co"))
        th.onSuccess("a@b.co")
        assertEquals(0L, th.remainingLockMs("a@b.co"))
        assertEquals("30 sn", LoginThrottle.describe(30_000))
        assertEquals("2 dk", LoginThrottle.describe(90_000))
    }
}
