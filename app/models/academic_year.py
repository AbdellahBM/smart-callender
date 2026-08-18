from app.extensions import db


class AcademicYear(db.Model):
    __tablename__ = "academic_years"

    id = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(30), nullable=False, unique=True)
    date_debut = db.Column(db.Date)
    date_fin = db.Column(db.Date)
    actif = db.Column(db.Boolean, nullable=False, default=False)
    archive = db.Column(db.Boolean, nullable=False, default=False)

    cycles = db.relationship(
        "AcademicCycle",
        back_populates="school_year",
        cascade="all, delete-orphan",
    )
    groupes = db.relationship("Groupe", back_populates="school_year")

    def __repr__(self):
        return f"<AcademicYear {self.libelle}>"
