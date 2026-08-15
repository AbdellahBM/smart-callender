from datetime import date, time
from app.extensions import db


class Reservation(db.Model):
    """
    Demande de réservation de salle par un enseignant.
    Statuts : en_attente, acceptee, refusee
    """

    __tablename__ = "reservations"

    id = db.Column(db.Integer, primary_key=True)
    enseignant_id = db.Column(db.Integer, db.ForeignKey("utilisateurs.id"), nullable=False)
    salle_id = db.Column(db.Integer, db.ForeignKey("salles.id"), nullable=False)

    date_reservation = db.Column(db.Date, nullable=False)
    heure_debut = db.Column(db.Time, nullable=False)
    heure_fin = db.Column(db.Time, nullable=False)
    motif = db.Column(db.String(300), nullable=True)
    statut = db.Column(db.String(20), default="en_attente")
    commentaire_admin = db.Column(db.String(300), nullable=True)

    STATUTS = ("en_attente", "acceptee", "refusee")
    
    salle = db.relationship("Salle")

    def __repr__(self):
        return f"<Reservation {self.date_reservation} salle={self.salle_id} ({self.statut})>"
