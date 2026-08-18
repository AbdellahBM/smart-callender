import unittest
import warnings

from app import create_app
from app.extensions import db
from app.models import AcademicYear, Groupe
from app.services.settings_service import SchoolSettingsService
from scripts.seed_db import seed


class TestSeedYearBootstrap(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.ctx.pop()

    def test_seed_creates_an_active_year_and_assigns_every_demo_class(self):
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always", DeprecationWarning)
            seed(self.app)

        active_year = db.session.query(AcademicYear).filter_by(actif=True).one()
        groups = db.session.query(Groupe).all()

        self.assertEqual(9, len(groups))
        self.assertTrue(all(group.school_year_id == active_year.id for group in groups))
        self.assertEqual(active_year.libelle, SchoolSettingsService.get_academic_year())
        self.assertFalse(
            any("utcnow" in str(warning.message) for warning in caught_warnings),
            "Le seed ne doit pas utiliser datetime.utcnow déprécié.",
        )
