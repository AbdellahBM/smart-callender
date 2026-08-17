from datetime import time
from typing import List

from app.extensions import db
from app.models import SchoolSetting


class SchoolSettingsService:
    """
    Centralise la lecture/écriture des réglages de l'établissement.
    Valeurs stockées en base sous forme de texte pour éviter des migrations prématurées.
    """

    DEFAULT_WORKING_DAYS = "0,1,2,3,4"
    DEFAULT_SLOT_TIMES = "08:30,10:15,13:30,15:15,17:00"
    DEFAULT_SLOT_DURATION_MINUTES = "90"
    DAY_NAMES = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

    @classmethod
    def seed_default_settings(cls) -> None:
        defaults = {
            "school.work_days": cls.DEFAULT_WORKING_DAYS,
            "school.slot_times": cls.DEFAULT_SLOT_TIMES,
            "school.slot_duration_minutes": cls.DEFAULT_SLOT_DURATION_MINUTES,
        }
        for key, value in defaults.items():
            if not cls._exists(key):
                setting = SchoolSetting(key=key, value=value)
                db.session.add(setting)
        db.session.commit()

    @classmethod
    def get_value(cls, key: str, default: str | None = None) -> str | None:
        setting = db.session.query(SchoolSetting).filter_by(key=key).first()
        if setting is None:
            return default
        return setting.value

    @classmethod
    def set_value(cls, key: str, value: str) -> SchoolSetting:
        setting = db.session.query(SchoolSetting).filter_by(key=key).first()
        if setting is None:
            setting = SchoolSetting(key=key, value=value)
            db.session.add(setting)
        else:
            setting.value = value
        db.session.commit()
        return setting

    @classmethod
    def get_working_days(cls) -> List[int]:
        raw = cls.get_value("school.work_days", cls.DEFAULT_WORKING_DAYS) or ""
        days = []
        for item in raw.split(","):
            item = item.strip()
            if item:
                try:
                    value = int(item)
                except ValueError:
                    continue
                if 0 <= value <= 6:
                    days.append(value)
        return sorted(set(days)) if days else [0, 1, 2, 3, 4]

    @classmethod
    def get_slot_times(cls) -> List[time]:
        raw = cls.get_value("school.slot_times", cls.DEFAULT_SLOT_TIMES) or ""
        slots = []
        for item in raw.split(","):
            item = item.strip()
            if item:
                try:
                    hour, minute = item.split(":")
                    slots.append(time(int(hour), int(minute)))
                except Exception:
                    continue
        return slots or [time.fromisoformat("08:30"), time.fromisoformat("10:15"), time.fromisoformat("13:30"), time.fromisoformat("15:15"), time.fromisoformat("17:00")]

    @classmethod
    def get_slot_duration_minutes(cls) -> int:
        raw = cls.get_value("school.slot_duration_minutes", cls.DEFAULT_SLOT_DURATION_MINUTES)
        try:
            value = int(raw or cls.DEFAULT_SLOT_DURATION_MINUTES)
            if value <= 0:
                return int(cls.DEFAULT_SLOT_DURATION_MINUTES)
            return value
        except (TypeError, ValueError):
            return int(cls.DEFAULT_SLOT_DURATION_MINUTES)

    @classmethod
    def set_planning_settings(cls, working_days: str, slot_times: str, slot_duration: str) -> None:
        cls._validate_working_days(working_days)
        normalized_slot_times = cls._validate_slot_times(slot_times)
        try:
            duration = int(slot_duration)
        except ValueError as exc:
            raise ValueError("La durée d'un créneau doit être un entier.") from exc
        if duration <= 0:
            raise ValueError("La durée du créneau doit être supérieure à 0.")

        cls.set_value("school.work_days", ",".join(str(d) for d in cls._parse_working_days(working_days)))
        cls.set_value("school.slot_times", ",".join(normalized_slot_times))
        cls.set_value("school.slot_duration_minutes", str(duration))

    @classmethod
    def get_day_name(cls, day_index: int) -> str:
        if 0 <= day_index < len(cls.DAY_NAMES):
            return cls.DAY_NAMES[day_index]
        return "?"

    @classmethod
    def get_working_day_names(cls) -> List[str]:
        return [cls.DAY_NAMES[d] for d in cls.get_working_days() if 0 <= d < len(cls.DAY_NAMES)]

    @classmethod
    def _exists(cls, key: str) -> bool:
        return db.session.query(SchoolSetting).filter_by(key=key).first() is not None

    @classmethod
    def _parse_working_days(cls, raw: str) -> List[int]:
        days = []
        for item in raw.split(","):
            item = item.strip()
            if item:
                try:
                    value = int(item)
                except ValueError:
                    continue
                if 0 <= value <= 6:
                    days.append(value)
        if not days:
            raise ValueError("Aucun jour valide détecté.")
        return sorted(set(days))

    @classmethod
    def _validate_working_days(cls, raw: str) -> None:
        cls._parse_working_days(raw)

    @classmethod
    def _validate_slot_times(cls, raw: str) -> List[str]:
        slots = []
        for item in raw.split(","):
            item = item.strip()
            if not item:
                continue
            try:
                hour, minute = item.split(":")
                parsed = time(int(hour), int(minute))
            except Exception as exc:
                raise ValueError("Le format des créneaux doit être HH:MM séparés par des virgules.") from exc
            slots.append(parsed.strftime("%H:%M"))
        if not slots:
            raise ValueError("Aucun créneau valide détecté.")
        return slots
