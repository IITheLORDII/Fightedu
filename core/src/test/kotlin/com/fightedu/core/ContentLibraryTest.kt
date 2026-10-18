package com.fightedu.core

import com.fightedu.core.content.ContentLibrary
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

class ContentLibraryTest {
    private val library = TestContent.library

    @Test
    fun `dört spor yüklenir`() {
        assertEquals(listOf("boxing", "kickboxing", "wrestling", "taekwondo"), library.sports.map { it.id })
    }

    @Test
    fun `içerik tutarlı ve her hareketin videosu ile kapak resmi var`() {
        val errors = library.validate { File(TestContent.assetsDir, it).isFile }
        assertTrue(errors.joinToString("\n"), errors.isEmpty())
    }

    @Test
    fun `her sporun en az 8 haftalık programı ve yeterli hareketi var`() {
        for (sport in library.sports) {
            val program = library.program(sport.id)!!
            assertTrue(program.totalWeeks >= ContentLibrary.MIN_WEEKS)
            assertTrue("${sport.id} hareket sayısı", library.movesForSport(sport.id).size >= 12)
        }
    }

    @Test
    fun `her sporun tüm hareketleri programda en az bir kez kullanılır`() {
        for (sport in library.sports) {
            val program = library.program(sport.id)!!
            val used = program.phases.flatMap { p -> p.sessions.flatMap { s -> s.main.map { it.move } } }.toSet()
            val unused = library.movesForSport(sport.id).map { it.id } - used
            assertTrue("${sport.id} kullanılmayan: $unused", unused.isEmpty())
        }
    }
}
