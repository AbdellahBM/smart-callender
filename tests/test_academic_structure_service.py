import unittest
from datetime import date

from app import create_app
from app.extensions import db
from app.services.academic_structure_service import AcademicStructureService


class TestAcademicStructureService(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.drop_all()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.ctx.pop()

    def test_only_one_academic_year_is_active(self):
        first_year = AcademicStructureService.create_year(
            "2025-2026", date(2025, 9, 1), date(2026, 7, 31)
        )
        second_year = AcademicStructureService.create_year(
            "2026-2027", date(2026, 9, 1), date(2027, 7, 31)
        )

        self.assertFalse(first_year.actif)
        self.assertTrue(second_year.actif)

    def test_clone_year_copies_unarchived_academic_structure(self):
        source_year = AcademicStructureService.create_year("2025-2026", None, None)
        cycle = AcademicStructureService.create_cycle(source_year.id, "Lycée", "LYC", 1)
        level = AcademicStructureService.create_level(cycle.id, "2BAC", "2BAC", 1)
        filiere = AcademicStructureService.create_filiere(level.id, "Sciences", "SCI")
        AcademicStructureService.create_groupe(filiere.id, "2BAC A", 30, source_year.id)

        result = AcademicStructureService.clone_year_structure(source_year.id, "2026-2027")

        self.assertEqual(1, result["niveaux_doublonnes"])
        self.assertEqual(1, result["filieres_doublonnes"])
        self.assertEqual(1, result["groupes_dupliques"])
