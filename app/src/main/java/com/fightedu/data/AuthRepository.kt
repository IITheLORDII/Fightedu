package com.fightedu.data

import android.database.sqlite.SQLiteConstraintException
import androidx.room.withTransaction
import com.fightedu.core.auth.AccountRules
import com.fightedu.core.auth.PasswordHasher
import com.fightedu.core.auth.StoredPassword
import com.fightedu.data.db.AppDatabase
import com.fightedu.data.db.UserEntity
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.withContext

/** Oturumdaki kullanıcı (arayüz için; şifre bilgisi taşımaz). */
data class User(val id: Long, val name: String, val email: String?, val isGuest: Boolean) {
    val initials: String get() = AccountRules.initials(name)
}

/** Kayıt/giriş sonucu; hata varsa hangi alana ait olduğu. */
sealed interface AuthResult {
    data class Success(val user: User) : AuthResult

    data class Failure(val field: Field, val message: String) : AuthResult

    enum class Field { NAME, EMAIL, PASSWORD, GENERAL }
}

/**
 * Cihazdaki yerel hesaplar: kayıt, giriş, misafir, misafiri hesaba çevirme ve çıkış.
 * Hesaplar yalnızca bu telefonda tutulur (sunucu yok); şifreler PBKDF2 ile özetlenir.
 */
class AuthRepository(private val db: AppDatabase, private val session: SessionStore) {
    private val users = db.userDao()

    @OptIn(ExperimentalCoroutinesApi::class)
    val currentUser: Flow<User?> = session.userId.flatMapLatest { id ->
        if (id == null) flowOf(null) else users.observe(id).map { it?.toUser() }
    }

    suspend fun register(name: String, email: String, password: String): AuthResult {
        val cleanName = AccountRules.normalizeName(name)
        val cleanEmail = AccountRules.normalizeEmail(email)
        AccountRules.nameError(cleanName)?.let { return AuthResult.Failure(AuthResult.Field.NAME, it) }
        AccountRules.emailError(cleanEmail)?.let { return AuthResult.Failure(AuthResult.Field.EMAIL, it) }
        AccountRules.passwordError(password)?.let { return AuthResult.Failure(AuthResult.Field.PASSWORD, it) }
        if (users.findByEmail(cleanEmail) != null) {
            return AuthResult.Failure(AuthResult.Field.EMAIL, "Bu e-posta ile zaten bir hesap var. Giriş yapmayı dene.")
        }
        val stored = withContext(Dispatchers.Default) { PasswordHasher.create(password) }
        val guest = session.current?.let { users.get(it) }?.takeIf { it.isGuest }
        return try {
            val user = if (guest != null) {
                // misafir hesaba dönüşür: ilerlemesi ve dal seçimi korunur
                guest.copy(name = cleanName, email = cleanEmail, passwordHash = stored.hash,
                    passwordSalt = stored.salt, isGuest = false).also { users.update(it) }
            } else {
                val entity = UserEntity(name = cleanName, email = cleanEmail, passwordHash = stored.hash,
                    passwordSalt = stored.salt, isGuest = false, createdAt = System.currentTimeMillis())
                entity.copy(id = users.insert(entity))
            }
            session.set(user.id)
            AuthResult.Success(user.toUser())
        } catch (_: SQLiteConstraintException) {
            AuthResult.Failure(AuthResult.Field.EMAIL, "Bu e-posta ile zaten bir hesap var. Giriş yapmayı dene.")
        }
    }

    suspend fun login(email: String, password: String): AuthResult {
        val cleanEmail = AccountRules.normalizeEmail(email)
        AccountRules.emailError(cleanEmail)?.let { return AuthResult.Failure(AuthResult.Field.EMAIL, it) }
        if (password.isEmpty()) return AuthResult.Failure(AuthResult.Field.PASSWORD, "Şifreni yaz.")
        val user = users.findByEmail(cleanEmail)
        val hash = user?.passwordHash
        val salt = user?.passwordSalt
        val ok = hash != null && salt != null && withContext(Dispatchers.Default) {
            PasswordHasher.verify(password, StoredPassword(hash, salt))
        }
        if (user == null || !ok) {
            return AuthResult.Failure(AuthResult.Field.GENERAL, "E-posta ya da şifre hatalı.")
        }
        dropGuest()
        session.set(user.id)
        return AuthResult.Success(user.toUser())
    }

    suspend fun continueAsGuest(): User {
        session.current?.let { id -> users.get(id)?.takeIf { it.isGuest }?.let { return it.toUser() } }
        val entity = UserEntity(name = "Sporcu", email = null, passwordHash = null, passwordSalt = null,
            isGuest = true, createdAt = System.currentTimeMillis())
        val id = users.insert(entity)
        session.set(id)
        return entity.copy(id = id).toUser()
    }

    suspend fun rename(name: String): String? {
        val id = session.current ?: return "Oturum yok."
        AccountRules.nameError(name)?.let { return it }
        val user = users.get(id) ?: return "Hesap bulunamadı."
        users.update(user.copy(name = AccountRules.normalizeName(name)))
        return null
    }

    /** Çıkış; misafirin cihazdaki verisi silinir (geri dönüş yolu olmadığı için). */
    suspend fun logout() {
        dropGuest()
        session.clear()
    }

    private suspend fun dropGuest() {
        val id = session.current ?: return
        val user = users.get(id) ?: return
        if (!user.isGuest) return
        db.withTransaction {
            db.progressDao().clearUser(id)
            db.activityDao().clearUser(id)
            db.planDao().delete(id)
            users.delete(id)
        }
    }

    private fun UserEntity.toUser() = User(id, name, email, isGuest)
}
