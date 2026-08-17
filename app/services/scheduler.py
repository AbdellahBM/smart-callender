"""
app/services/scheduler.py - Moteur de planification CSP (OR-Tools)

Ce service implémente la logique de génération d'emploi du temps en utilisant
la programmation par contraintes (Constraint Programming).
"""

from ortools.sat.python import cp_model
from app.models import Seance, Salle, Utilisateur, Groupe, Indisponibilite
from app.services.settings_service import SchoolSettingsService
from app.extensions import db
from datetime import time, timedelta, date

class SchedulerService:
    SLOTS = []
    
    @classmethod
    def _init_slots(cls):
        cls.SLOTS = []
        working_days = SchoolSettingsService.get_working_days()
        start_times = SchoolSettingsService.get_slot_times()
        duration_minutes = SchoolSettingsService.get_slot_duration_minutes()
        # Prépare des créneaux récurrents par jour configuré.
        for day in working_days:
            for start in start_times:
                t_min = start.hour * 60 + start.minute
                cls.SLOTS.append({
                    "day": day,
                    "start": start,
                    "duration": duration_minutes,
                    "start_min": t_min
                })
    
    @classmethod
    def get_slots(cls):
        """Retourne les créneaux actifs actuels sans muter l'état global."""
        working_days = SchoolSettingsService.get_working_days()
        start_times = SchoolSettingsService.get_slot_times()
        duration_minutes = SchoolSettingsService.get_slot_duration_minutes()
        slots = []
        for day in working_days:
            for start in start_times:
                t_min = start.hour * 60 + start.minute
                slots.append({
                    "day": day,
                    "start": start,
                    "duration": duration_minutes,
                    "start_min": t_min
                })
        return slots

    @staticmethod
    def generate_schedule():
        """
        Génère l'emploi du temps pour toutes les séances non planifiées (ou toutes).
        """
        SchedulerService._init_slots()
        model = cp_model.CpModel()
        
        # 1. Récupération des données
        seances = db.session.query(Seance).all() # On replanifie tout pour l'instant
        salles = db.session.query(Salle).all()
        # Filtrer les séances qui doivent être planifiées (ex: pas de date spécifique fixée manuellement ?)
        # Pour simplifier, on prend toutes les séances de type cours/td/tp sans date spécifique
        seances_to_plan = [s for s in seances if not s.date_specifique]
        
        if not seances_to_plan:
            return "Aucune séance à planifier."

        slots = SchedulerService.get_slots()
        num_slots = len(slots)
        if num_slots == 0:
            return "Aucun créneau actif (vérifiez les paramètres de planification)."
        
        # 2. Création des variables
        # x[seance_id, salle_id, slot_index]
        x = {}
        for s in seances_to_plan:
            for r in salles:
                for t in range(num_slots):
                    x[(s.id, r.id, t)] = model.NewBoolVar(f'x_s{s.id}_r{r.id}_t{t}')

        # 3. Contraintes

        # C1: Chaque séance doit être planifiée exactement une fois
        for s in seances_to_plan:
            model.Add(sum(x[(s.id, r.id, t)] for r in salles for t in range(num_slots)) == 1)

        # C2: Capacité des salles
        # Si une séance est assignée à une salle, la capacité de la salle doit être suffisante
        for s in seances_to_plan:
            groupe = db.session.get(Groupe, s.groupe_id)
            groupe_size = groupe.effectif if groupe else 0
            for r in salles:
                # Si la salle est trop petite, on force la variable à 0
                if r.capacite < groupe_size:
                     for t in range(num_slots):
                        model.Add(x[(s.id, r.id, t)] == 0)

        # C3: Conflits de salle (Une salle ne peut accueillir qu'une séance à la fois)
        for r in salles:
            for t in range(num_slots):
                model.Add(sum(x[(s.id, r.id, t)] for s in seances_to_plan) <= 1)

        # C4: Conflits d'enseignant (Un enseignant ne peut être qu'à un endroit à la fois)
        # Regrouper les séances par enseignant
        seances_by_prof = {}
        for s in seances_to_plan:
            if s.enseignant_id not in seances_by_prof:
                seances_by_prof[s.enseignant_id] = []
            seances_by_prof[s.enseignant_id].append(s)
            
        for prof_id, prof_seances in seances_by_prof.items():
            for t in range(num_slots):
                model.Add(sum(x[(s.id, r.id, t)] for s in prof_seances for r in salles) <= 1)

        # C5: Conflits de groupe (Un groupe ne peut avoir qu'un cours à la fois)
        seances_by_groupe = {}
        for s in seances_to_plan:
            if s.groupe_id not in seances_by_groupe:
                seances_by_groupe[s.groupe_id] = []
            seances_by_groupe[s.groupe_id].append(s)

        for grp_id, grp_seances in seances_by_groupe.items():
            for t in range(num_slots):
                model.Add(sum(x[(s.id, r.id, t)] for s in grp_seances for r in salles) <= 1)

        # C6: Indisponibilités des enseignants
        indisponibilites = db.session.query(Indisponibilite).all()
        for ind in indisponibilites:
            if ind.est_ponctuelle():
                continue # On ignore les ponctuelles pour le planning hebdomadaire récurrent
            
            # Récurrente (jour_semaine + heure)
            # Trouver les slots qui chevauchent l'indisponibilité
            # ind.heure_debut, ind.heure_fin, ind.jour_semaine
            if ind.jour_semaine is None: continue

            ind_start = ind.heure_debut.hour * 60 + ind.heure_debut.minute
            ind_end = ind.heure_fin.hour * 60 + ind.heure_fin.minute
            
            forbidden_slots = []
            for t_idx, slot in enumerate(slots):
                if slot["day"] == ind.jour_semaine:
                    slot_end = slot["start_min"] + slot["duration"]
                    # Chevauchement
                    if not (slot_end <= ind_start or slot["start_min"] >= ind_end):
                        forbidden_slots.append(t_idx)
            
            # Appliquer la contrainte : aucune séance de ce prof sur ces slots
            prof_seances = seances_by_prof.get(ind.enseignant_id, [])
            for s in prof_seances:
                for t in forbidden_slots:
                    for r in salles:
                        model.Add(x[(s.id, r.id, t)] == 0)

        # 4. Résolution
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 30.0
        status = solver.Solve(model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            # Sauvegarder les résultats
            count = 0
            for s in seances_to_plan:
                for r in salles:
                    for t in range(num_slots):
                        if solver.BooleanValue(x[(s.id, r.id, t)]):
                            slot = slots[t]
                            # Mise à jour de la séance
                            s.salle_id = r.id
                            s.jour_semaine = slot["day"]
                            s.heure_debut = slot["start"]
                            # Calcul heure fin
                            dt = datetime.combine(date.today(), slot["start"]) + timedelta(minutes=slot["duration"])
                            s.heure_fin = dt.time()
                            count += 1
            db.session.commit()
            return f"Succès : {count} séances planifiées."
        else:
            return "Échec : Impossible de trouver une solution avec les contraintes actuelles."

from datetime import datetime
