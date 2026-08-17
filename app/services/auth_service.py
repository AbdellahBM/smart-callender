"""
app/services/auth_service.py - Service d'authentification

Gère la vérification des identifiants et la gestion des utilisateurs.
"""

from app.models.utilisateur import Utilisateur
from app.models import Matiere
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
    def update_user(user_id, **kwargs):
        user = AuthService.get_by_id(user_id)
        if not user:
            return None

        new_email = kwargs.get("email")
        if new_email is not None and new_email.strip():
            normalized_email = new_email.strip().lower()
            existing = db.session.query(Utilisateur).filter(
                Utilisateur.email == normalized_email, Utilisateur.id != user.id
            ).first()
            if existing:
                raise ValueError("Un utilisateur avec cet email existe déjà.")
            user.email = normalized_email

        new_nom = kwargs.get("nom")
        if new_nom is not None:
            user.nom = str(new_nom).strip() or user.nom

        new_prenom = kwargs.get("prenom")
        if new_prenom is not None:
            user.prenom = str(new_prenom).strip() or user.prenom

        new_role = kwargs.get("role")
        if new_role is not None:
            if new_role not in Utilisateur.ROLES:
                raise ValueError("Rôle invalide.")
            if user.role == "admin" and new_role != "admin":
                admin_count = db.session.query(Utilisateur).filter_by(role="admin", actif=True).count()
                if admin_count <= 1:
                    raise ValueError("Impossible de retirer le dernier administrateur actif.")
            user.role = new_role

        groupe_id = kwargs.get("groupe_id")
        if user.role == "etudiant":
            if groupe_id is not None:
                if groupe_id == "":
                    user.groupe_id = None
                elif groupe_id == 0:
                    user.groupe_id = None
                else:
                    user.groupe_id = int(groupe_id)
        else:
            user.groupe_id = None

        new_password = kwargs.get("password")
        if new_password is not None:
            if not str(new_password).strip():
                raise ValueError("Le mot de passe ne peut pas être vide.")
            user.set_password(str(new_password))

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return None

        matiere_ids = kwargs.get("matiere_ids")
        if matiere_ids is not None and user.role == "enseignant":
            AuthService.set_teacher_matieres(user.id, matiere_ids)

        return user

    @staticmethod
    def reset_password(user_id, new_password):
        user = AuthService.get_by_id(user_id)
        if not user:
            return False
        if not str(new_password).strip():
            raise ValueError("Le mot de passe ne peut pas être vide.")
        user.set_password(str(new_password))
        try:
            db.session.commit()
            return True
        except IntegrityError:
            db.session.rollback()
            return False

    @staticmethod
    def get_teacher_matiere_ids(user_id):
        user = AuthService.get_by_id(user_id)
        if not user or user.role != "enseignant":
            return []
        return [m.id for m in user.matieres.all()]

    @staticmethod
    def set_teacher_matieres(user_id, matiere_ids):
        user = AuthService.get_by_id(user_id)
        if not user:
            return False
        if user.role != "enseignant":
            return False

        ids = []
        for raw in matiere_ids:
            try:
                ids.append(int(raw))
            except (TypeError, ValueError):
                raise ValueError("Liste de matières invalide.")

        if not ids:
            user.matieres = []
            db.session.commit()
            return True

        matieres = db.session.query(Matiere).filter(Matiere.id.in_(ids)).all()
        if len(matieres) != len(set(ids)):
            raise ValueError("Une ou plusieurs matières sont invalides.")

        user.matieres = matieres
        try:
            db.session.commit()
            return True
        except IntegrityError:
            db.session.rollback()
            return False

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
