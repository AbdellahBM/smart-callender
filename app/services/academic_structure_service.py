from app.extensions import db
from app.models import AcademicCycle, AcademicLevel, AcademicYear, Filiere, Groupe


class AcademicStructureService:
    @staticmethod
    def get_active_year():
        return db.session.query(AcademicYear).filter_by(actif=True, archive=False).first()

    @staticmethod
    def create_year(libelle, date_debut, date_fin):
        normalized_label = str(libelle or "").strip()
        if not normalized_label:
            raise ValueError("Le libellé de l'année est obligatoire.")
        if db.session.query(AcademicYear).filter_by(libelle=normalized_label).first():
            raise ValueError("Année déjà existante.")

        academic_year = AcademicYear(
            libelle=normalized_label,
            date_debut=date_debut,
            date_fin=date_fin,
            actif=False,
        )
        db.session.add(academic_year)
        db.session.flush()
        return AcademicStructureService.set_active_year(academic_year.id)

    @staticmethod
    def set_active_year(year_id):
        academic_year = db.session.get(AcademicYear, int(year_id))
        if academic_year is None:
            raise ValueError("Année invalide.")

        for active_year in db.session.query(AcademicYear).filter_by(actif=True).all():
            active_year.actif = False
        academic_year.archive = False
        academic_year.actif = True
        db.session.commit()
        return academic_year

    @staticmethod
    def archive_year(year_id, archive=True):
        academic_year = db.session.get(AcademicYear, int(year_id))
        if academic_year is None:
            raise ValueError("Année invalide.")

        academic_year.archive = bool(archive)
        if academic_year.archive:
            academic_year.actif = False
        db.session.commit()
        return academic_year

    @staticmethod
    def create_cycle(year_id, nom, code=None, ordre=0):
        AcademicStructureService._get_required(AcademicYear, year_id, "Année invalide.")
        cycle = AcademicCycle(
            school_year_id=int(year_id),
            nom=AcademicStructureService._required_name(nom, "Le nom du cycle est obligatoire."),
            code=AcademicStructureService._optional_code(code),
            ordre=int(ordre or 0),
        )
        db.session.add(cycle)
        db.session.commit()
        return cycle

    @staticmethod
    def create_level(cycle_id, nom, code=None, ordre=0):
        AcademicStructureService._get_required(AcademicCycle, cycle_id, "Cycle invalide.")
        level = AcademicLevel(
            academic_cycle_id=int(cycle_id),
            nom=AcademicStructureService._required_name(nom, "Le nom du niveau est obligatoire."),
            code=AcademicStructureService._optional_code(code),
            ordre=int(ordre or 0),
        )
        db.session.add(level)
        db.session.commit()
        return level

    @staticmethod
    def create_filiere(level_id, nom, code=None, ordre=0):
        AcademicStructureService._get_required(AcademicLevel, level_id, "Niveau invalide.")
        filiere = Filiere(
            academic_level_id=int(level_id),
            nom=AcademicStructureService._required_name(nom, "Le nom de la filière est obligatoire."),
            code=AcademicStructureService._optional_code(code),
            ordre=int(ordre or 0),
        )
        db.session.add(filiere)
        db.session.commit()
        return filiere

    @staticmethod
    def create_groupe(filiere_id, nom, effectif, school_year_id, ordre=0):
        AcademicStructureService._get_required(Filiere, filiere_id, "Filière invalide.")
        AcademicStructureService._get_required(AcademicYear, school_year_id, "Année invalide.")
        groupe = Groupe(
            filiere_id=int(filiere_id),
            nom=AcademicStructureService._required_name(nom, "Le nom de la classe est obligatoire."),
            effectif=int(effectif or 0),
            school_year_id=int(school_year_id),
            ordre=int(ordre or 0),
        )
        db.session.add(groupe)
        db.session.commit()
        return groupe

    @staticmethod
    def update_cycle(cycle_id, nom, code=None, ordre=0):
        return AcademicStructureService._update_named_entity(
            AcademicCycle,
            cycle_id,
            nom,
            code,
            ordre,
            "Cycle invalide.",
            "Le nom du cycle est obligatoire.",
        )

    @staticmethod
    def update_level(level_id, nom, code=None, ordre=0):
        return AcademicStructureService._update_named_entity(
            AcademicLevel,
            level_id,
            nom,
            code,
            ordre,
            "Niveau invalide.",
            "Le nom du niveau est obligatoire.",
        )

    @staticmethod
    def update_filiere(filiere_id, nom, code=None, ordre=0):
        return AcademicStructureService._update_named_entity(
            Filiere,
            filiere_id,
            nom,
            code,
            ordre,
            "Filière invalide.",
            "Le nom de la filière est obligatoire.",
        )

    @staticmethod
    def update_groupe(groupe_id, nom, effectif, ordre=0):
        groupe = AcademicStructureService._get_required(
            Groupe, groupe_id, "Classe invalide."
        )
        groupe.nom = AcademicStructureService._required_name(
            nom, "Le nom de la classe est obligatoire."
        )
        groupe.effectif = int(effectif or 0)
        groupe.ordre = int(ordre or 0)
        db.session.commit()
        return groupe

    @staticmethod
    def archive_cycle(cycle_id, archive=True):
        return AcademicStructureService._set_archive(
            AcademicCycle, cycle_id, archive, "Cycle invalide."
        )

    @staticmethod
    def archive_level(level_id, archive=True):
        return AcademicStructureService._set_archive(
            AcademicLevel, level_id, archive, "Niveau invalide."
        )

    @staticmethod
    def archive_filiere(filiere_id, archive=True):
        return AcademicStructureService._set_archive(
            Filiere, filiere_id, archive, "Filière invalide."
        )

    @staticmethod
    def archive_groupe(groupe_id, archive=True):
        return AcademicStructureService._set_archive(
            Groupe, groupe_id, archive, "Classe invalide."
        )

    @staticmethod
    def clone_year_structure(source_year_id, target_libelle, keep_effectif=False):
        source = AcademicStructureService._get_required(
            AcademicYear, source_year_id, "Année source invalide."
        )
        normalized_label = AcademicStructureService._required_name(
            target_libelle, "Le libellé de l'année est obligatoire."
        )
        if db.session.query(AcademicYear).filter_by(libelle=normalized_label).first():
            raise ValueError("Année déjà existante.")

        target = AcademicYear(libelle=normalized_label, actif=False)
        db.session.add(target)
        db.session.flush()

        counts = {
            "niveaux_doublonnes": 0,
            "filieres_doublonnes": 0,
            "groupes_dupliques": 0,
        }
        for cycle in source.cycles:
            if cycle.archive:
                continue
            cloned_cycle = AcademicCycle(
                school_year_id=target.id,
                nom=cycle.nom,
                code=cycle.code,
                ordre=cycle.ordre,
            )
            db.session.add(cloned_cycle)
            db.session.flush()

            for level in cycle.levels:
                if level.archive:
                    continue
                cloned_level = AcademicLevel(
                    academic_cycle_id=cloned_cycle.id,
                    nom=level.nom,
                    code=level.code,
                    ordre=level.ordre,
                )
                db.session.add(cloned_level)
                db.session.flush()
                counts["niveaux_doublonnes"] += 1

                for filiere in level.filieres:
                    if filiere.archive:
                        continue
                    cloned_filiere = Filiere(
                        academic_level_id=cloned_level.id,
                        nom=filiere.nom,
                        code=filiere.code,
                        ordre=filiere.ordre,
                    )
                    db.session.add(cloned_filiere)
                    db.session.flush()
                    counts["filieres_doublonnes"] += 1

                    for groupe in filiere.groupes:
                        if groupe.archive:
                            continue
                        db.session.add(
                            Groupe(
                                filiere_id=cloned_filiere.id,
                                nom=groupe.nom,
                                effectif=groupe.effectif if keep_effectif else 0,
                                school_year_id=target.id,
                                ordre=groupe.ordre,
                            )
                        )
                        counts["groupes_dupliques"] += 1

        db.session.commit()
        return counts

    @staticmethod
    def _get_required(model, identifier, message):
        row = db.session.get(model, int(identifier))
        if row is None:
            raise ValueError(message)
        return row

    @staticmethod
    def _update_named_entity(model, identifier, nom, code, ordre, invalid_message, name_message):
        entity = AcademicStructureService._get_required(model, identifier, invalid_message)
        entity.nom = AcademicStructureService._required_name(nom, name_message)
        entity.code = AcademicStructureService._optional_code(code)
        entity.ordre = int(ordre or 0)
        db.session.commit()
        return entity

    @staticmethod
    def _set_archive(model, identifier, archive, invalid_message):
        entity = AcademicStructureService._get_required(model, identifier, invalid_message)
        entity.archive = bool(archive)
        db.session.commit()
        return entity

    @staticmethod
    def _required_name(value, message):
        normalized_value = str(value or "").strip()
        if not normalized_value:
            raise ValueError(message)
        return normalized_value

    @staticmethod
    def _optional_code(value):
        return str(value).strip() if value else None
