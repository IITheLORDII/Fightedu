package com.fightedu.core.auth

import java.security.MessageDigest
import java.security.SecureRandom
import java.util.Base64
import javax.crypto.SecretKeyFactory
import javax.crypto.spec.PBEKeySpec

/** Cihazda saklanan şifre: PBKDF2 özeti ve tuzu (Base64). Şifrenin kendisi hiçbir yerde tutulmaz. */
data class StoredPassword(val hash: String, val salt: String)

/** PBKDF2-HMAC-SHA256 ile şifre özeti; doğrulama sabit zamanlı karşılaştırmayla yapılır. */
object PasswordHasher {
    const val ITERATIONS = 60_000
    private const val KEY_BITS = 256
    private const val SALT_BYTES = 16
    private const val ALGORITHM = "PBKDF2WithHmacSHA256"

    private val random = SecureRandom()

    fun create(password: String, iterations: Int = ITERATIONS): StoredPassword {
        val salt = ByteArray(SALT_BYTES).also { random.nextBytes(it) }
        return StoredPassword(encode(derive(password, salt, iterations)), encode(salt))
    }

    fun verify(password: String, stored: StoredPassword, iterations: Int = ITERATIONS): Boolean {
        val salt = runCatching { decode(stored.salt) }.getOrNull() ?: return false
        val expected = runCatching { decode(stored.hash) }.getOrNull() ?: return false
        if (salt.isEmpty() || expected.isEmpty()) return false
        return MessageDigest.isEqual(derive(password, salt, iterations), expected)
    }

    private fun derive(password: String, salt: ByteArray, iterations: Int): ByteArray {
        val spec = PBEKeySpec(password.toCharArray(), salt, iterations, KEY_BITS)
        try {
            return SecretKeyFactory.getInstance(ALGORITHM).generateSecret(spec).encoded
        } finally {
            spec.clearPassword()
        }
    }

    private fun encode(bytes: ByteArray): String = Base64.getEncoder().encodeToString(bytes)

    private fun decode(text: String): ByteArray = Base64.getDecoder().decode(text)
}
