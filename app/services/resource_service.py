"""
app/services/resource_service.py - Service de gestion des ressources

Gère les opérations CRUD pour les Salles, Enseignants, Groupes, Matières, Filières.
"""

from app.models import Salle, Groupe, Matiere, Filiere, Utilisateur
from app.extensions import db

class ResourceService:
    # --- SALLES ---
    @staticmethod
    def get_all_salles():
        return db.session.query(Salle).order_by(Salle.nom).all()

    @staticmethod
    def create_salle(data):
        salle = Salle(
            nom=data.get('nom'),
            capacite=data.get('capacite'),
            type_salle=data.get('type_salle'),
            equipement_video=data.get('equipement_video', False),
            equipement_pc=data.get('equipement_pc', False),
            equipement_tp=data.get('equipement_tp', False),
            description=data.get('description')
        )
        db.session.add(salle)
        db.session.commit()
        return salle

    @staticmethod
    def update_salle(salle_id, data):
        salle = db.session.get(Salle, salle_id)
        if salle:
            for key, value in data.items():
                if hasattr(salle, key):
                    setattr(salle, key, value)
            db.session.commit()
        return salle

    @staticmethod
    def delete_salle(salle_id):
        salle = db.session.get(Salle, salle_id)
        if salle:
            db.session.delete(salle)
            db.session.commit()
            return True
        return False

    # --- ENSEIGNANTS ---
    @staticmethod
    def get_all_enseignants():
        return db.session.query(Utilisateur).filter_by(role="enseignant").order_by(Utilisateur.nom).all()

    # --- GROUPES ---
    @staticmethod
    def get_all_groupes():
        return db.session.query(Groupe).join(Filiere).order_by(Filiere.nom, Groupe.nom).all()

    @staticmethod
    def create_groupe(nom, effectif, filiere_id):
        groupe = Groupe(nom=nom, effectif=effectif, filiere_id=filiere_id)
        db.session.add(groupe)
        db.session.commit()
        return groupe

    # --- MATIERES ---
    @staticmethod
    def get_all_matieres():
        return db.session.query(Matiere).order_by(Matiere.nom).all()

    # --- FILIERES ---
    @staticmethod
    def get_all_filieres():
        return db.session.query(Filiere).order_by(Filiere.nom).all()
