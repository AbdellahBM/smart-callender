from app.extensions import db

class Filiere(db.Model):
    __tablename__ = "filieres"
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    code = db.Column(db.String(10))
    academic_level_id = db.Column(db.Integer, db.ForeignKey("academic_levels.id"))
    actif = db.Column(db.Boolean, nullable=False, default=True)
    archive = db.Column(db.Boolean, nullable=False, default=False)
    ordre = db.Column(db.Integer, nullable=False, default=0)

    academic_level = db.relationship("AcademicLevel", back_populates="filieres")

    def __repr__(self):
        return f"<Filiere {self.nom}>"
