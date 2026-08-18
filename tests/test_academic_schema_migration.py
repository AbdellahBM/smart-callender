import unittest

from app import create_app
from app.extensions import db
from app.services.academic_structure_migration_service import (
    AcademicStructureMigrationService,
)


class TestAcademicSchemaMigration(unittest.TestCase):
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

    def test_schema_guard_is_idempotent(self):
        AcademicStructureMigrationService.ensure_schema()
        AcademicStructureMigrationService.ensure_schema()
