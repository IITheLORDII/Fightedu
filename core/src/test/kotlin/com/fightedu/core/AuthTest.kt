package com.fightedu.core

import com.fightedu.core.auth.AccountRules
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
        assertTrue(AccountRules.validateRegister("Ali Veli", " Ali@Ornek.com ", "123456", "123456").isValid)
        val bad = AccountRules.validateRegister("  ", "ali@", "123", "124")
        assertNotNull(bad.name)
        assertNotNull(bad.email)
        assertNotNull(bad.password)
        assertNotNull(bad.confirm)
        assertNull(AccountRules.emailError("ad.soyad+fight@mail.co.uk"))
        assertNotNull(AccountRules.emailError("ad soyad@mail.com"))
        assertNotNull(AccountRules.passwordError("      "))
        assertEquals("ali@ornek.com", AccountRules.normalizeEmail(" Ali@Ornek.COM "))
        assertEquals("İA", AccountRules.initials("ilker  akın"))
        assertEquals("?", AccountRules.initials(" "))
    }
}
