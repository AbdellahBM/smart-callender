from datetime import date

from sqlalchemy import inspect, text

from app.extensions import db
from app.models import AcademicYear


class AcademicStructureMigrationService:
    """Keeps legacy SQLite installations compatible with academic controls."""

    @classmethod
    def ensure_schema(cls):
        db.create_all()

        cls._ensure_column("groupes", "school_year_id", "INTEGER")
        cls._ensure_column("groupes", "actif", "BOOLEAN DEFAULT 1")
        cls._ensure_column("groupes", "archive", "BOOLEAN DEFAULT 0")
        cls._ensure_column("groupes", "ordre", "INTEGER DEFAULT 0")
        cls._ensure_column("filieres", "academic_level_id", "INTEGER")
        cls._ensure_column("filieres", "actif", "BOOLEAN DEFAULT 1")
        cls._ensure_column("filieres", "archive", "BOOLEAN DEFAULT 0")
        cls._ensure_column("filieres", "ordre", "INTEGER DEFAULT 0")

        cls.ensure_active_year()

    @staticmethod
    def _ensure_column(table, column, type_sql):
        columns = {item["name"] for item in inspect(db.engine).get_columns(table)}
        if column in columns:
            return

        db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {type_sql}"))
        db.session.commit()

    @classmethod
    def ensure_active_year(cls):
        if db.session.query(AcademicYear).count():
            return

        db.session.add(AcademicYear(libelle=cls._default_label(), actif=True))
        db.session.commit()

    @staticmethod
    def enforce_single_active_year():
        active_years = db.session.query(AcademicYear).filter_by(actif=True).all()
        for academic_year in active_years[:-1]:
            academic_year.actif = False
        if active_years:
            active_years[-1].actif = True
        db.session.commit()

    @staticmethod
    def _default_label():
        year = date.today().year
        return f"{year}-{year + 1}"
