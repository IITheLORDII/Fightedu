package com.fightedu.core.auth

import java.util.Locale

/** Kayıt/giriş formu kuralları; hata yoksa ilgili alan null. */
data class RegisterErrors(
    val name: String? = null,
    val email: String? = null,
    val password: String? = null,
    val confirm: String? = null,
) {
    val isValid: Boolean get() = name == null && email == null && password == null && confirm == null
}

object AccountRules {
    const val MIN_PASSWORD = 6
    const val MAX_NAME = 40
    private val EMAIL = Regex("^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\\.[A-Za-z0-9-]+)*\\.[A-Za-z]{2,}$")

    fun normalizeEmail(email: String): String = email.trim().lowercase(Locale.ROOT)

    fun normalizeName(name: String): String = name.trim().replace(Regex("\\s+"), " ")

    fun nameError(name: String): String? {
        val n = normalizeName(name)
        return when {
            n.isEmpty() -> "Adını yaz."
            n.length > MAX_NAME -> "Ad en fazla $MAX_NAME karakter olabilir."
            else -> null
        }
    }

    fun emailError(email: String): String? {
        val e = normalizeEmail(email)
        return when {
            e.isEmpty() -> "E-posta adresini yaz."
            !EMAIL.matches(e) -> "Geçerli bir e-posta adresi yaz (ör. ad@ornek.com)."
            else -> null
        }
    }

    fun passwordError(password: String): String? = when {
        password.isEmpty() -> "Şifre belirle."
        password.length < MIN_PASSWORD -> "Şifre en az $MIN_PASSWORD karakter olmalı."
        password.isBlank() -> "Şifre yalnızca boşluktan oluşamaz."
        else -> null
    }

    fun confirmError(password: String, confirm: String): String? =
        if (confirm != password) "Şifreler aynı değil." else null

    fun validateRegister(name: String, email: String, password: String, confirm: String) = RegisterErrors(
        name = nameError(name),
        email = emailError(email),
        password = passwordError(password),
        confirm = confirmError(password, confirm),
    )

    /** Ad soyadın baş harfleri (avatar için), ör. "Ali Veli" -> "AV". */
    fun initials(name: String): String {
        val parts = normalizeName(name).split(" ").filter { it.isNotEmpty() }
        return parts.take(2).joinToString("") { it.first().uppercase(Locale("tr", "TR")) }.ifEmpty { "?" }
    }
}
