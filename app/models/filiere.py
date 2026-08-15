from app.extensions import db

class Filiere(db.Model):
    __tablename__ = "filieres"
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    code = db.Column(db.String(10))

    def __repr__(self):
        return f"<Filiere {self.nom}>"
