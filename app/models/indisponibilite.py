from datetime import date, time
from app.extensions import db


class Indisponibilite(db.Model):
    """
    Représente une plage où un enseignant n'est pas disponible.
    Peut être ponctuelle (date) ou récurrente (jour_semaine + créneau).
    """

    __tablename__ = "indisponibilites"

    id = db.Column(db.Integer, primary_key=True)
    enseignant_id = db.Column(db.Integer, db.ForeignKey("utilisateurs.id"), nullable=False)

    # Option 1 : Plage ponctuelle (date unique)
    date_debut = db.Column(db.Date, nullable=True)
    date_fin = db.Column(db.Date, nullable=True)

    # Option 2 : Récurrente (chaque semaine)
    jour_semaine = db.Column(db.Integer, nullable=True)  # 0-4
    heure_debut = db.Column(db.Time, nullable=True)
    heure_fin = db.Column(db.Time, nullable=True)

    motif = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f"<Indisponibilite enseignant={self.enseignant_id}>"

    def est_ponctuelle(self) -> bool:
        return self.date_debut is not None
