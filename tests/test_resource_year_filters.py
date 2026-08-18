import unittest

from app import create_app
from app.extensions import db
from app.services.academic_structure_service import AcademicStructureService
from app.services.resource_service import ResourceService


class TestResourceYearFilters(unittest.TestCase):
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

    def test_academic_resources_only_return_the_active_year(self):
        first_year = AcademicStructureService.create_year("2025-2026", None, None)
        first_cycle = AcademicStructureService.create_cycle(first_year.id, "Collège", "COL", 1)
        first_level = AcademicStructureService.create_level(first_cycle.id, "3AC", "3AC", 1)
        first_filiere = AcademicStructureService.create_filiere(first_level.id, "Général", "GEN")
        AcademicStructureService.create_groupe(first_filiere.id, "3AC A", 30, first_year.id)

        second_year = AcademicStructureService.create_year("2026-2027", None, None)
        second_cycle = AcademicStructureService.create_cycle(second_year.id, "Lycée", "LYC", 1)
        second_level = AcademicStructureService.create_level(second_cycle.id, "1BAC", "1BAC", 1)
        second_filiere = AcademicStructureService.create_filiere(second_level.id, "Sciences", "SCI")
        AcademicStructureService.create_groupe(second_filiere.id, "1BAC A", 32, second_year.id)

        self.assertEqual(["Lycée"], [cycle.nom for cycle in ResourceService.get_cycles_for_active_year()])
        self.assertEqual(["1BAC"], [level.nom for level in ResourceService.get_levels_for_active_year()])
        self.assertEqual(
            ["Sciences"],
            [filiere.nom for filiere in ResourceService.get_filieres_for_active_year()],
        )
        self.assertEqual(
            ["1BAC A"],
            [groupe.nom for groupe in ResourceService.get_groupes_for_active_year()],
        )
