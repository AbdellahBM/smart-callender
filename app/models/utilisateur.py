from datetime import datetime, timezone
from flask_login import UserMixin
from app.extensions import db, bcrypt


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Utilisateur(UserMixin, db.Model):
    """
    Classe mère pour tous les utilisateurs du système.
    Rôles : admin, enseignant, etudiant
    """

    __tablename__ = "utilisateurs"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    nom = db.Column(db.String(80), nullable=False)
    prenom = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="etudiant")
    actif = db.Column(db.Boolean, default=True)
    date_creation = db.Column(db.DateTime, default=utc_now)

    # Relations selon le rôle
    groupe_id = db.Column(db.Integer, db.ForeignKey("groupes.id"), nullable=True)  # Étudiant
    groupe = db.relationship("Groupe", backref="etudiants", foreign_keys=[groupe_id])

    # Matières enseignées (pour Enseignant) - relation many-to-many
    matieres = db.relationship(
        "Matiere",
        secondary="enseignant_matiere",
        backref=db.backref("enseignants", lazy="dynamic"),
        lazy="dynamic",
    )

    # Séquences / séances dont il est responsable
    seances_enseignant = db.relationship(
        "Seance",
        backref="enseignant",
        lazy="dynamic",
        foreign_keys="Seance.enseignant_id",
    )
    indisponibilites = db.relationship(
        "Indisponibilite", backref="enseignant", lazy="dynamic", cascade="all, delete-orphan"
    )
    reservations = db.relationship(
        "Reservation", backref="demandeur", lazy="dynamic", cascade="all, delete-orphan"
    )

    ROLES = ("admin", "enseignant", "etudiant")

    def __repr__(self):
        return f"<Utilisateur {self.email} ({self.role})>"

    def set_password(self, password: str) -> None:
        """Hash et enregistre le mot de passe."""
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """Vérifie le mot de passe."""
        return bcrypt.check_password_hash(self.password_hash, password)

    @property
    def est_admin(self) -> bool:
        return self.role == "admin"

    @property
    def est_enseignant(self) -> bool:
        return self.role == "enseignant"

    @property
    def est_etudiant(self) -> bool:
        return self.role == "etudiant"

    def get_nom_complet(self) -> str:
        """Retourne le nom complet de l'utilisateur."""
        return f"{self.prenom} {self.nom}".strip()


# Table d'association Enseignant <-> Matière (many-to-many)
enseignant_matiere = db.Table(
    "enseignant_matiere",
    db.Column("enseignant_id", db.Integer, db.ForeignKey("utilisateurs.id"), primary_key=True),
    db.Column("matiere_id", db.Integer, db.ForeignKey("matieres.id"), primary_key=True),
)
