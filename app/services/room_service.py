"""
app/services/room_service.py - Service de disponibilité des salles

Calcule quelles salles sont occupées ou libres à une date/heure donnée
en tenant compte des Séances (emploi du temps) et des Réservations acceptées.
"""

from datetime import date, time
from app.models import Salle, Seance, Reservation
from app.extensions import db


def _time_ranges_overlap(start1: time, end1: time, start2: time, end2: time) -> bool:
    """True si les créneaux [start1,end1] et [start2,end2] se chevauchent."""
    return start1 < end2 and start2 < end1


def get_occupied_salle_ids(day_date: date, heure_debut: time, heure_fin: time):
    """
    Retourne les IDs des salles occupées au créneau (day_date, heure_debut -> heure_fin).

    Une salle est occupée si :
    - une Séance (emploi du temps) l'utilise ce jour de la semaine à ce créneau, ou
    - une Réservation acceptée l'utilise à cette date et ce créneau.
    """
    occupied_ids = set()
    weekday = day_date.weekday()  # 0=Lundi, 6=Dimanche. On utilise 0-4 (Lundi-Vendredi)

    # Séances récurrentes (même jour de semaine)
    if weekday < 5:  # Lundi=0 .. Vendredi=4
        seances = db.session.query(Seance).filter(
            Seance.jour_semaine == weekday,
            Seance.salle_id.isnot(None),
        ).all()
        for s in seances:
            if _time_ranges_overlap(s.heure_debut, s.heure_fin, heure_debut, heure_fin):
                occupied_ids.add(s.salle_id)

    # Réservations acceptées à cette date
    resas = db.session.query(Reservation).filter(
        Reservation.date_reservation == day_date,
        Reservation.statut == "acceptee",
    ).all()
    for r in resas:
        if _time_ranges_overlap(r.heure_debut, r.heure_fin, heure_debut, heure_fin):
            occupied_ids.add(r.salle_id)

    return occupied_ids


def get_free_salles(day_date: date, heure_debut: time, heure_fin: time, capacite_min=None, type_salle=None):
    """
    Retourne la liste des salles libres au créneau donné.

    Optionnel : capacite_min (filtrer par capacité >= X), type_salle (cours, tp, amphi).
    """
    occupied_ids = get_occupied_salle_ids(day_date, heure_debut, heure_fin)
    if occupied_ids:
        query = db.session.query(Salle).filter(~Salle.id.in_(occupied_ids))
    else:
        query = db.session.query(Salle)
    if capacite_min is not None:
        query = query.filter(Salle.capacite >= capacite_min)
    if type_salle:
        query = query.filter(Salle.type_salle == type_salle)
    return query.order_by(Salle.nom).all()
