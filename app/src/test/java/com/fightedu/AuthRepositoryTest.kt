package com.fightedu

import android.content.Context
import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.fightedu.core.auth.LoginThrottle
import com.fightedu.core.auth.PasswordHasher
import com.fightedu.data.AuthRepository
import com.fightedu.data.AuthResult
import com.fightedu.data.SessionStore
import com.fightedu.data.TrainingRepository
import com.fightedu.data.db.AppDatabase
import com.fightedu.data.db.UserEntity
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class AuthRepositoryTest {
    private val context = ApplicationProvider.getApplicationContext<Context>()
    private lateinit var db: AppDatabase
    private lateinit var session: SessionStore
    private var now = 1_000_000L
    private lateinit var auth: AuthRepository

    @Before
    fun setUp() {
        db = Room.inMemoryDatabaseBuilder(context, AppDatabase::class.java).build()
        session = SessionStore(context).also { it.clear() }
        auth = AuthRepository(db, session, LoginThrottle { now })
    }

    @After
    fun tearDown() {
        db.close()
        session.clear()
    }

    @Test
    fun `kayıt, giriş ve yanlış şifre`() = runBlocking {
        val r = auth.register("Ali Veli", "Ali@Ornek.com", "gizlisifre1")
        assertTrue(r is AuthResult.Success)
        val stored = requireNotNull(db.userDao().findByEmail("ali@ornek.com"))
        assertEquals("yeni hesap güncel tekrar sayısıyla", PasswordHasher.ITERATIONS, stored.passwordIterations)
        assertNotEquals("şifre düz metin saklanmaz", "gizlisifre1", stored.passwordHash)
        auth.logout()
        assertTrue(auth.login(" ALI@ornek.com ", "gizlisifre1") is AuthResult.Success)
        auth.logout()
        val wrong = auth.login("ali@ornek.com", "yanlis-sifre")
        assertTrue(wrong is AuthResult.Failure && wrong.field == AuthResult.Field.GENERAL)
        val unknown = auth.login("yok@ornek.com", "gizlisifre1")
        assertEquals("kayıtlı olmayan e-postada aynı mesaj (hesap varlığı sızmaz)",
            (wrong as AuthResult.Failure).message, (unknown as AuthResult.Failure).message)
    }

    @Test
    fun `kısa şifreyle kayıt reddedilir`() = runBlocking {
        val r = auth.register("Ali", "ali@ornek.com", "1234567")
        assertTrue(r is AuthResult.Failure && r.field == AuthResult.Field.PASSWORD)
    }

    @Test
    fun `art arda yanlış şifre girişi kilitler, süre dolunca açılır`() = runBlocking {
        auth.register("Ali", "ali@ornek.com", "gizlisifre1")
        auth.logout()
        repeat(LoginThrottle.FREE_ATTEMPTS) { auth.login("ali@ornek.com", "yanlis-$it") }
        val locked = auth.login("ali@ornek.com", "gizlisifre1")
        assertTrue("kilitliyken doğru şifre de beklemeli",
            locked is AuthResult.Failure && locked.message.contains("Çok fazla"))
        now += LoginThrottle.BASE_LOCK_MS
        assertTrue(auth.login("ali@ornek.com", "gizlisifre1") is AuthResult.Success)
    }

    @Test
    fun `eski tekrar sayısıyla özetlenmiş şifre girişte yükseltilir`() = runBlocking {
        val legacy = PasswordHasher.create("eskisifre1", iterations = PasswordHasher.LEGACY_ITERATIONS)
        db.userDao().insert(UserEntity(name = "Eski", email = "eski@ornek.com", passwordHash = legacy.hash,
            passwordSalt = legacy.salt, isGuest = false, createdAt = 0, passwordIterations = PasswordHasher.LEGACY_ITERATIONS))
        assertTrue(auth.login("eski@ornek.com", "eskisifre1") is AuthResult.Success)
        val upgraded = requireNotNull(db.userDao().findByEmail("eski@ornek.com"))
        assertEquals(PasswordHasher.ITERATIONS, upgraded.passwordIterations)
        assertNotEquals(legacy.hash, upgraded.passwordHash)
        auth.logout()
        assertTrue("yükseltilmiş özetle giriş sürer", auth.login("eski@ornek.com", "eskisifre1") is AuthResult.Success)
    }

    @Test
    fun `misafir hesaba dönüşür, ilerlemesi korunur; hesap silinince her şey gider`() = runBlocking {
        val repo = TrainingRepository(db)
        val guest = auth.continueAsGuest()
        repo.selectSport(guest.id, "boxing")
        repo.markCompleted(guest.id, "boxing", "day_1", startedAt = 5_000, durationSec = 1800, kcal = 210.0)
        val r = auth.register("Ali", "ali@ornek.com", "gizlisifre1")
        assertEquals("misafir aynı kimlikle hesaba döner", guest.id, (r as AuthResult.Success).user.id)
        val done = requireNotNull(repo.completedSession(guest.id, "boxing", "day_1"))
        assertEquals(5_000L, done.startedAt)
        assertEquals(1800, done.durationSec)
        repo.setHealthSync(guest.id, true)
        assertTrue(requireNotNull(repo.planNow(guest.id)).healthSync)

        auth.deleteAccount()
        assertNull(session.current)
        assertNull(db.userDao().get(guest.id))
        assertNull(repo.planNow(guest.id))
        assertNull(repo.completedSession(guest.id, "boxing", "day_1"))
        assertTrue(repo.activityDaysNow(guest.id).isEmpty())
    }
}
