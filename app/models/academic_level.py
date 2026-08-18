from app.extensions import db


class AcademicLevel(db.Model):
    __tablename__ = "academic_levels"

    id = db.Column(db.Integer, primary_key=True)
    academic_cycle_id = db.Column(
        db.Integer,
        db.ForeignKey("academic_cycles.id"),
        nullable=False,
    )
    nom = db.Column(db.String(80), nullable=False)
    code = db.Column(db.String(20))
    ordre = db.Column(db.Integer, nullable=False, default=0)
    actif = db.Column(db.Boolean, nullable=False, default=True)
    archive = db.Column(db.Boolean, nullable=False, default=False)

    academic_cycle = db.relationship("AcademicCycle", back_populates="levels")
    filieres = db.relationship("Filiere", back_populates="academic_level")

    def __repr__(self):
        return f"<AcademicLevel {self.nom}>"
