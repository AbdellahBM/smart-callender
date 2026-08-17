"""
app/services/auth_service.py - Service d'authentification

Gère la vérification des identifiants et la gestion des utilisateurs.
"""

from app.models.utilisateur import Utilisateur
from app.extensions import db, bcrypt
from sqlalchemy.exc import IntegrityError

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
            if not user.actif:
                raise ValueError("Ce compte est désactivé. Contactez l'administrateur.")
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

    @staticmethod
    def get_all():
        return Utilisateur.query.order_by(Utilisateur.nom, Utilisateur.prenom).all()

    @staticmethod
    def get_by_id(user_id):
        return db.session.get(Utilisateur, int(user_id))

    @staticmethod
    def delete_user(user_id):
        user = AuthService.get_by_id(user_id)
        if not user:
            return False
        admin_count = db.session.query(Utilisateur).filter_by(role="admin").count()
        if user.role == "admin" and admin_count <= 1:
            return False
        try:
            db.session.delete(user)
            db.session.commit()
            return True
        except IntegrityError:
            db.session.rollback()
            return False

    @staticmethod
    def set_status(user_id, actif):
        user = AuthService.get_by_id(user_id)
        if not user:
            return False
        if user.role == "admin" and not actif:
            admin_count = db.session.query(Utilisateur).filter_by(role="admin", actif=True).count()
            if admin_count <= 1:
                return False
        user.actif = bool(actif)
        try:
            db.session.commit()
            return True
        except IntegrityError:
            db.session.rollback()
            return False
