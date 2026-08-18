"""
app/services/resource_service.py - Service de gestion des ressources

Gère les opérations CRUD pour les Salles, Enseignants, Groupes, Matières, Filières.
"""

from app.models import (
    AcademicCycle,
    AcademicLevel,
    Filiere,
    Groupe,
    Matiere,
    Salle,
    Utilisateur,
)
from app.extensions import db
from app.services.academic_structure_service import AcademicStructureService
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

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
            if "nom" in data and data["nom"] is not None:
                salle.nom = str(data["nom"]).strip()
            if "capacite" in data and data["capacite"] is not None:
                salle.capacite = int(data["capacite"])
            if "type_salle" in data and data["type_salle"] is not None:
                salle.type_salle = str(data["type_salle"]).strip()
            if "equipement_video" in data:
                salle.equipement_video = bool(data["equipement_video"])
            if "equipement_pc" in data:
                salle.equipement_pc = bool(data["equipement_pc"])
            if "equipement_tp" in data:
                salle.equipement_tp = bool(data["equipement_tp"])
            if "description" in data:
                description = data["description"]
                salle.description = description.strip() if description is not None else None

            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                return None
        return salle

    @staticmethod
    def delete_salle(salle_id):
        salle = db.session.get(Salle, salle_id)
        if salle:
            try:
                db.session.delete(salle)
                db.session.commit()
                return True
            except IntegrityError:
                db.session.rollback()
                return False
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
    def get_groupes_for_active_year():
        active_year = AcademicStructureService.get_active_year()
        query = (
            db.session.query(Groupe)
            .join(Filiere)
            .outerjoin(AcademicLevel, Filiere.academic_level_id == AcademicLevel.id)
            .outerjoin(AcademicCycle, AcademicLevel.academic_cycle_id == AcademicCycle.id)
            .filter(
                Groupe.archive.is_(False),
                Groupe.actif.is_(True),
                Filiere.archive.is_(False),
                Filiere.actif.is_(True),
                or_(
                    Filiere.academic_level_id.is_(None),
                    (
                        AcademicLevel.actif.is_(True)
                        & AcademicLevel.archive.is_(False)
                        & AcademicCycle.actif.is_(True)
                        & AcademicCycle.archive.is_(False)
                    ),
                ),
            )
        )
        if active_year:
            query = query.filter(
                or_(
                    Groupe.school_year_id == active_year.id,
                    Groupe.school_year_id.is_(None),
                )
            )
        return query.order_by(Filiere.nom, Groupe.ordre, Groupe.nom).all()

    @staticmethod
    def update_groupe(groupe_id, data):
        groupe = db.session.get(Groupe, groupe_id)
        if groupe:
            if "nom" in data and data["nom"] is not None:
                groupe.nom = str(data["nom"]).strip()
            if "effectif" in data and data["effectif"] is not None:
                groupe.effectif = int(data["effectif"])
            if "filiere_id" in data and data["filiere_id"] is not None:
                filiere = db.session.get(Filiere, int(data["filiere_id"]))
                if filiere is None:
                    raise ValueError("La filière sélectionnée n'existe pas.")
                groupe.filiere_id = filiere.id
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                return None
        return groupe

    @staticmethod
    def create_groupe(nom, effectif, filiere_id):
        groupe = Groupe(nom=nom, effectif=effectif, filiere_id=filiere_id)
        db.session.add(groupe)
        db.session.commit()
        return groupe

    @staticmethod
    def delete_groupe(groupe_id):
        groupe = db.session.get(Groupe, groupe_id)
        if groupe:
            try:
                db.session.delete(groupe)
                db.session.commit()
                return True
            except IntegrityError:
                db.session.rollback()
                return False
        return False

    # --- MATIERES ---
    @staticmethod
    def get_all_matieres():
        return db.session.query(Matiere).order_by(Matiere.nom).all()

    @staticmethod
    def update_matiere(matiere_id, data):
        matiere = db.session.get(Matiere, matiere_id)
        if matiere:
            if "nom" in data and data["nom"] is not None:
                matiere.nom = str(data["nom"]).strip()
            if "code" in data:
                code = data["code"]
                matiere.code = code.strip() if code is not None else None
            if "filiere_id" in data and data["filiere_id"] is not None:
                filiere = db.session.get(Filiere, int(data["filiere_id"]))
                if filiere is None:
                    raise ValueError("La filière sélectionnée n'existe pas.")
                matiere.filiere_id = filiere.id
            if "volume_horaire_cours" in data and data["volume_horaire_cours"] is not None:
                matiere.volume_horaire_cours = int(data["volume_horaire_cours"])
            if "volume_horaire_td" in data and data["volume_horaire_td"] is not None:
                matiere.volume_horaire_td = int(data["volume_horaire_td"])
            if "volume_horaire_tp" in data and data["volume_horaire_tp"] is not None:
                matiere.volume_horaire_tp = int(data["volume_horaire_tp"])
            if "duree_seance_default" in data and data["duree_seance_default"] is not None:
                matiere.duree_seance_default = int(data["duree_seance_default"])
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                return None
        return matiere

    @staticmethod
    def create_matiere(nom, code=None, filiere_id=None, volume_cours=0, volume_tp=0, volume_td=0, duree=90):
        if filiere_id is not None and db.session.get(Filiere, filiere_id) is None:
            raise ValueError("La filière sélectionnée n'existe pas.")
        matiere = Matiere(
            nom=nom,
            code=code,
            volume_horaire_cours=volume_cours,
            volume_horaire_td=volume_td,
            volume_horaire_tp=volume_tp,
            duree_seance_default=duree,
            filiere_id=filiere_id,
        )
        db.session.add(matiere)
        db.session.commit()
        return matiere

    @staticmethod
    def delete_matiere(matiere_id):
        matiere = db.session.get(Matiere, matiere_id)
        if matiere:
            try:
                matiere.enseignants.clear()
                db.session.delete(matiere)
                db.session.commit()
                return True
            except IntegrityError:
                db.session.rollback()
                return False
        return False

    # --- FILIERES ---
    @staticmethod
    def get_all_filieres():
        return db.session.query(Filiere).order_by(Filiere.nom).all()

    @staticmethod
    def get_filieres_for_active_year():
        active_year = AcademicStructureService.get_active_year()
        if active_year is None:
            return []
        return (
            db.session.query(Filiere)
            .join(AcademicLevel)
            .join(AcademicCycle)
            .filter(
                AcademicCycle.school_year_id == active_year.id,
                Filiere.actif.is_(True),
                Filiere.archive.is_(False),
                AcademicLevel.actif.is_(True),
                AcademicLevel.archive.is_(False),
                AcademicCycle.actif.is_(True),
                AcademicCycle.archive.is_(False),
            )
            .order_by(AcademicLevel.ordre, Filiere.ordre, Filiere.nom)
            .all()
        )

    @staticmethod
    def get_levels_for_active_year():
        active_year = AcademicStructureService.get_active_year()
        if active_year is None:
            return []
        return (
            db.session.query(AcademicLevel)
            .join(AcademicCycle)
            .filter(
                AcademicCycle.school_year_id == active_year.id,
                AcademicLevel.actif.is_(True),
                AcademicLevel.archive.is_(False),
                AcademicCycle.actif.is_(True),
                AcademicCycle.archive.is_(False),
            )
            .order_by(AcademicCycle.ordre, AcademicLevel.ordre, AcademicLevel.nom)
            .all()
        )

    @staticmethod
    def get_cycles_for_active_year():
        active_year = AcademicStructureService.get_active_year()
        if active_year is None:
            return []
        return (
            db.session.query(AcademicCycle)
            .filter_by(school_year_id=active_year.id, actif=True, archive=False)
            .order_by(AcademicCycle.ordre, AcademicCycle.nom)
            .all()
        )

    @staticmethod
    def update_filiere(filiere_id, data):
        filiere = db.session.get(Filiere, filiere_id)
        if filiere:
            if "nom" in data and data["nom"] is not None:
                filiere.nom = str(data["nom"]).strip()
            if "code" in data:
                code = data["code"]
                filiere.code = code.strip() if code is not None else None
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                return None
        return filiere

    @staticmethod
    def create_filiere(nom, code=None):
        filiere = Filiere(nom=nom, code=code)
        db.session.add(filiere)
        db.session.commit()
        return filiere

    @staticmethod
    def delete_filiere(filiere_id):
        filiere = db.session.get(Filiere, filiere_id)
        if filiere:
            try:
                db.session.delete(filiere)
                db.session.commit()
                return True
            except IntegrityError:
                db.session.rollback()
                return False
        return False
