from app.extensions import db

class Groupe(db.Model):
    __tablename__ = "groupes"
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    effectif = db.Column(db.Integer, default=0)
    filiere_id = db.Column(db.Integer, db.ForeignKey("filieres.id"))
    school_year_id = db.Column(db.Integer, db.ForeignKey("academic_years.id"))
    actif = db.Column(db.Boolean, nullable=False, default=True)
    archive = db.Column(db.Boolean, nullable=False, default=False)
    ordre = db.Column(db.Integer, nullable=False, default=0)

    filiere = db.relationship("Filiere", backref="groupes")
    school_year = db.relationship("AcademicYear", back_populates="groupes")

    def __repr__(self):
        return f"<Groupe {self.nom}>"
