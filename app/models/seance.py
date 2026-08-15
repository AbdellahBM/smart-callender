from datetime import time, date
from app.extensions import db


class Seance(db.Model):
    """
    Représente une séance planifiée dans l'emploi du temps.
    type_seance : cours, td, tp, examen
    """

    __tablename__ = "seances"

    id = db.Column(db.Integer, primary_key=True)
    matiere_id = db.Column(db.Integer, db.ForeignKey("matieres.id"), nullable=False)
    enseignant_id = db.Column(db.Integer, db.ForeignKey("utilisateurs.id"), nullable=False)
    groupe_id = db.Column(db.Integer, db.ForeignKey("groupes.id"), nullable=False)
    salle_id = db.Column(db.Integer, db.ForeignKey("salles.id"), nullable=True)

    type_seance = db.Column(db.String(20), nullable=False, default="cours")
    jour_semaine = db.Column(db.Integer, nullable=False)  # 0=Lundi, 4=Vendredi
    heure_debut = db.Column(db.Time, nullable=False)
    heure_fin = db.Column(db.Time, nullable=False)
    date_specifique = db.Column(db.Date, nullable=True)  # Pour examens ponctuels
    semestre = db.Column(db.String(20), nullable=True)  # S1, S2
    annee_scolaire = db.Column(db.String(20), nullable=True)  # 2024-2025

    TYPES = ("cours", "td", "tp", "examen")
    JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
    
    # Relations (nécessaires pour l'accès facile dans le code)
    matiere = db.relationship("Matiere")
    groupe = db.relationship("Groupe")
    salle = db.relationship("Salle")
    # enseignant relation définie dans Utilisateur (backref)

    def __repr__(self):
        return f"<Seance {self.matiere.nom if self.matiere else '?'} {self.get_jour_nom()} {self.heure_debut}>"

    def get_jour_nom(self) -> str:
        """Retourne le nom du jour (Lundi, Mardi, ...)."""
        if 0 <= self.jour_semaine < len(self.JOURS):
            return self.JOURS[self.jour_semaine]
        return "?"

    def chevauche(self, autre: "Seance") -> bool:
        """
        Vérifie si cette séance chevauche une autre (même jour, même créneau).
        """
        if self.jour_semaine != autre.jour_semaine:
            return False
        if self.date_specifique or autre.date_specifique:
            if self.date_specifique != autre.date_specifique:
                return False
        # Chevauchement horaire
        return not (self.heure_fin <= autre.heure_debut or autre.heure_fin <= self.heure_debut)
