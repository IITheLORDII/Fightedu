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
    fun `her sporun 24 günlük programı ve yeterli hareketi var`() {
        for (sport in library.sports) {
            val program = library.program(sport.id)!!
            assertEquals(ContentLibrary.TOTAL_DAYS, program.totalDays)
            assertEquals(4, program.phases.size)
            assertTrue("${sport.id} hareket sayısı", library.movesForSport(sport.id).size >= 12)
        }
    }
}
