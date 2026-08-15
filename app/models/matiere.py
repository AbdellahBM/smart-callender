from app.extensions import db

class Matiere(db.Model):
    __tablename__ = "matieres"
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20))
    volume_horaire_cours = db.Column(db.Integer, default=0)
    volume_horaire_td = db.Column(db.Integer, default=0)
    volume_horaire_tp = db.Column(db.Integer, default=0)
    duree_seance_default = db.Column(db.Integer, default=90)
    filiere_id = db.Column(db.Integer, db.ForeignKey("filieres.id"), nullable=True)

    filiere = db.relationship("Filiere", backref="matieres")

    def __repr__(self):
        return f"<Matiere {self.nom}>"
