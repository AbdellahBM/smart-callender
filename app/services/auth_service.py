"""
app/services/auth_service.py - Service d'authentification

Gère la vérification des identifiants et la gestion des utilisateurs.
"""

from app.models.utilisateur import Utilisateur
from app.extensions import db, bcrypt

class AuthService:
    @staticmethod
    def login(email, password):
        """
        Vérifie les identifiants d'un utilisateur.
        
        Args:
            email (str): L'email de l'utilisateur.
            password (str): Le mot de passe en clair.
            
        Returns:
            Utilisateur ou None: L'objet utilisateur si authentification réussie, sinon None.
        """
        user = db.session.query(Utilisateur).filter_by(email=email.lower().strip()).first()
        if user and user.check_password(password):
            return user
        return None

    @staticmethod
    def create_user(email, password, nom, prenom, role="etudiant", **kwargs):
        """
        Crée un nouvel utilisateur.
        """
        existing_user = db.session.query(Utilisateur).filter_by(email=email.lower().strip()).first()
        if existing_user:
            raise ValueError("Un utilisateur avec cet email existe déjà.")

        user = Utilisateur(
            email=email.lower().strip(),
            nom=nom.strip(),
            prenom=prenom.strip(),
            role=role
        )
        user.set_password(password)
        
        # Gestion des attributs spécifiques
        if role == "etudiant" and "groupe_id" in kwargs:
            user.groupe_id = kwargs["groupe_id"]
        
        db.session.add(user)
        db.session.commit()
        return user
