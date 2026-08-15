from app.extensions import db

class Salle(db.Model):
    __tablename__ = "salles"
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    capacite = db.Column(db.Integer, default=30)
    type_salle = db.Column(db.String(20), default="cours") # cours, tp, amphi
    equipement_video = db.Column(db.Boolean, default=False)
    equipement_pc = db.Column(db.Boolean, default=False)
    equipement_tp = db.Column(db.Boolean, default=False)
    description = db.Column(db.String(200))

    def __repr__(self):
        return f"<Salle {self.nom}>"
