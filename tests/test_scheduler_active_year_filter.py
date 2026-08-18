import unittest
from datetime import time

from app import create_app
from app.extensions import db
from app.models import Matiere, Seance, Utilisateur
from app.services.academic_structure_service import AcademicStructureService
from app.services.scheduler import SchedulerService


class TestSchedulerActiveYearFilter(unittest.TestCase):
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

    def test_planifiable_lessons_only_include_the_active_school_year(self):
        first_year = AcademicStructureService.create_year("2025-2026", None, None)
        first_group = self._create_group(first_year.id, "1BAC A")
        second_year = AcademicStructureService.create_year("2026-2027", None, None)
        second_group = self._create_group(second_year.id, "1BAC B")

        teacher = Utilisateur(email="teacher@school.test", nom="Teacher", prenom="One", role="enseignant")
        teacher.set_password("password")
        subject = Matiere(nom="Mathématiques")
        db.session.add_all([teacher, subject])
        db.session.flush()
        first_lesson = Seance(
            matiere_id=subject.id,
            enseignant_id=teacher.id,
            groupe_id=first_group.id,
            jour_semaine=0,
            heure_debut=time(8, 30),
            heure_fin=time(10, 0),
        )
        second_lesson = Seance(
            matiere_id=subject.id,
            enseignant_id=teacher.id,
            groupe_id=second_group.id,
            jour_semaine=0,
            heure_debut=time(10, 15),
            heure_fin=time(11, 45),
        )
        db.session.add_all([first_lesson, second_lesson])
        db.session.commit()

        lesson_ids = {lesson.id for lesson in SchedulerService.query_planifiable_seances().all()}

        self.assertEqual({second_lesson.id}, lesson_ids)

    @staticmethod
    def _create_group(year_id, group_name):
        cycle = AcademicStructureService.create_cycle(year_id, "Lycée", "LYC", 1)
        level = AcademicStructureService.create_level(cycle.id, "1BAC", "1BAC", 1)
        filiere = AcademicStructureService.create_filiere(level.id, "Sciences", "SCI")
        return AcademicStructureService.create_groupe(filiere.id, group_name, 30, year_id)
