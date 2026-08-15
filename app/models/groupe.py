from app.extensions import db

class Groupe(db.Model):
    __tablename__ = "groupes"
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    effectif = db.Column(db.Integer, default=0)
    filiere_id = db.Column(db.Integer, db.ForeignKey("filieres.id"))
    
    filiere = db.relationship("Filiere", backref="groupes")

    def __repr__(self):
        return f"<Groupe {self.nom}>"
