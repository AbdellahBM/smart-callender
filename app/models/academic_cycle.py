from app.extensions import db


class AcademicCycle(db.Model):
    __tablename__ = "academic_cycles"

    id = db.Column(db.Integer, primary_key=True)
    school_year_id = db.Column(
        db.Integer,
        db.ForeignKey("academic_years.id"),
        nullable=False,
    )
    nom = db.Column(db.String(80), nullable=False)
    code = db.Column(db.String(20))
    ordre = db.Column(db.Integer, nullable=False, default=0)
    actif = db.Column(db.Boolean, nullable=False, default=True)
    archive = db.Column(db.Boolean, nullable=False, default=False)

    school_year = db.relationship("AcademicYear", back_populates="cycles")
    levels = db.relationship(
        "AcademicLevel",
        back_populates="academic_cycle",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<AcademicCycle {self.nom}>"
