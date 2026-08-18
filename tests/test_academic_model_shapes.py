import unittest

from sqlalchemy import inspect

from app import create_app
from app.extensions import db


class TestAcademicModelShapes(unittest.TestCase):
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

    def test_new_tables_and_columns_exist(self):
        inspector = inspect(db.engine)

        self.assertIn("academic_years", inspector.get_table_names())
        self.assertIn("academic_cycles", inspector.get_table_names())
        self.assertIn("academic_levels", inspector.get_table_names())

        group_columns = {column["name"] for column in inspector.get_columns("groupes")}
        filiere_columns = {column["name"] for column in inspector.get_columns("filieres")}

        for column in ["school_year_id", "actif", "archive", "ordre"]:
            self.assertIn(column, group_columns)

        for column in ["academic_level_id", "actif", "archive", "ordre"]:
            self.assertIn(column, filiere_columns)
