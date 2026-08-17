from datetime import date, datetime, time, timedelta
from typing import List

from app.extensions import db
from app.models import Reservation, SchoolSetting


class SchoolSettingsService:
    """
    Centralise la lecture/écriture des réglages de l'établissement.
    Valeurs stockées en base sous forme de texte pour éviter des migrations prématurées.
    """

    DEFAULT_WORKING_DAYS = "0,1,2,3,4"
    DEFAULT_SLOT_TIMES = "08:30,10:15,13:30,15:15,17:00"
    DEFAULT_SLOT_DURATION_MINUTES = "90"
    DEFAULT_SCHOOL_NAME = "École Smart Callender"
    DEFAULT_ACADEMIC_YEAR = ""
    DEFAULT_TERM_START = ""
    DEFAULT_TERM_END = ""
    DEFAULT_HOLIDAYS = ""
    DEFAULT_MAX_DAILY_RESERVATIONS_PER_TEACHER = "3"
    DEFAULT_MIN_BOOKING_NOTICE_DAYS = "1"
    DEFAULT_ALLOW_BOOKING_IN_HOLIDAYS = "false"
    DAY_NAMES = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

    @classmethod
    def seed_default_settings(cls) -> None:
        defaults = {
            "school.work_days": cls.DEFAULT_WORKING_DAYS,
            "school.slot_times": cls.DEFAULT_SLOT_TIMES,
            "school.slot_duration_minutes": cls.DEFAULT_SLOT_DURATION_MINUTES,
            "school.name": cls.DEFAULT_SCHOOL_NAME,
            "school.academic_year": cls.DEFAULT_ACADEMIC_YEAR or cls._default_academic_year(),
            "school.term_start": cls.DEFAULT_TERM_START,
            "school.term_end": cls.DEFAULT_TERM_END,
            "school.holidays": cls.DEFAULT_HOLIDAYS,
            "school.max_daily_reservations_per_teacher": cls.DEFAULT_MAX_DAILY_RESERVATIONS_PER_TEACHER,
            "school.min_booking_notice_days": cls.DEFAULT_MIN_BOOKING_NOTICE_DAYS,
            "school.allow_booking_in_holidays": cls.DEFAULT_ALLOW_BOOKING_IN_HOLIDAYS,
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
    def get_school_name(cls) -> str:
        return cls.get_value("school.name", cls.DEFAULT_SCHOOL_NAME) or cls.DEFAULT_SCHOOL_NAME

    @classmethod
    def get_academic_year(cls) -> str:
        raw = cls.get_value("school.academic_year", "")
        if raw:
            return raw
        return cls._default_academic_year()

    @classmethod
    def get_term_start(cls) -> date | None:
        return cls._parse_iso_date(cls.get_value("school.term_start", cls.DEFAULT_TERM_START))

    @classmethod
    def get_term_end(cls) -> date | None:
        return cls._parse_iso_date(cls.get_value("school.term_end", cls.DEFAULT_TERM_END))

    @classmethod
    def get_holidays(cls) -> List[date]:
        raw = cls.get_value("school.holidays", cls.DEFAULT_HOLIDAYS) or ""
        holidays = []
        for token in raw.split(","):
            token = token.strip()
            if not token:
                continue
            parsed = cls._parse_iso_date(token)
            if parsed is None:
                continue
            holidays.append(parsed)
        return sorted(set(holidays))

    @classmethod
    def get_holidays_text(cls) -> str:
        return ", ".join(h.isoformat() for h in cls.get_holidays())

    @classmethod
    def get_max_daily_reservations_per_teacher(cls) -> int:
        raw = cls.get_value("school.max_daily_reservations_per_teacher", cls.DEFAULT_MAX_DAILY_RESERVATIONS_PER_TEACHER)
        try:
            value = int(raw or cls.DEFAULT_MAX_DAILY_RESERVATIONS_PER_TEACHER)
            if value < 0:
                return int(cls.DEFAULT_MAX_DAILY_RESERVATIONS_PER_TEACHER)
            return value
        except (TypeError, ValueError):
            return int(cls.DEFAULT_MAX_DAILY_RESERVATIONS_PER_TEACHER)

    @classmethod
    def get_min_booking_notice_days(cls) -> int:
        raw = cls.get_value("school.min_booking_notice_days", cls.DEFAULT_MIN_BOOKING_NOTICE_DAYS)
        try:
            value = int(raw or cls.DEFAULT_MIN_BOOKING_NOTICE_DAYS)
            if value < 0:
                return int(cls.DEFAULT_MIN_BOOKING_NOTICE_DAYS)
            return value
        except (TypeError, ValueError):
            return int(cls.DEFAULT_MIN_BOOKING_NOTICE_DAYS)

    @classmethod
    def get_allow_booking_in_holidays(cls) -> bool:
        return cls._parse_bool(cls.get_value("school.allow_booking_in_holidays", cls.DEFAULT_ALLOW_BOOKING_IN_HOLIDAYS))

    @classmethod
    def set_school_settings(
        cls,
        school_name: str,
        academic_year: str,
        term_start: str,
        term_end: str,
        holidays: str,
        max_daily_reservations: str,
        min_booking_notice_days: str,
        allow_booking_in_holidays: bool | str,
    ) -> None:
        school_name = (school_name or "").strip()
        if not school_name:
            raise ValueError("Le nom de l'école est obligatoire.")

        term_start_value = (term_start or "").strip()
        term_end_value = (term_end or "").strip()
        if term_start_value and term_end_value:
            term_start_date = cls._parse_iso_date(term_start_value)
            term_end_date = cls._parse_iso_date(term_end_value)
            if term_start_date is None or term_end_date is None:
                raise ValueError("Les dates de période doivent être au format AAAA-MM-DD.")
            if term_end_date < term_start_date:
                raise ValueError("La date de fin doit être supérieure ou égale à la date de début.")
        elif term_start_value or term_end_value:
            raise ValueError("Pour la période scolaire, veuillez renseigner la date de début et la date de fin.")

        parsed_holidays = cls._parse_holidays(holidays)
        try:
            max_daily = int(max_daily_reservations)
        except ValueError as exc:
            raise ValueError("Le maximum de réservations par enseignant doit être un entier.") from exc
        if max_daily < 0:
            raise ValueError("Le maximum de réservations par enseignant doit être un nombre positif (ou 0).")

        try:
            notice_days = int(min_booking_notice_days)
        except ValueError as exc:
            raise ValueError("Le préavis minimum doit être un entier.") from exc
        if notice_days < 0:
            raise ValueError("Le préavis minimum ne peut pas être négatif.")

        cls.set_value("school.name", school_name)
        cls.set_value("school.academic_year", academic_year.strip())
        cls.set_value("school.term_start", term_start_value)
        cls.set_value("school.term_end", term_end_value)
        cls.set_value("school.holidays", ", ".join(h.isoformat() for h in parsed_holidays))
        cls.set_value("school.max_daily_reservations_per_teacher", str(max_daily))
        cls.set_value("school.min_booking_notice_days", str(notice_days))
        cls.set_value("school.allow_booking_in_holidays", "true" if cls._parse_bool(allow_booking_in_holidays) else "false")

    @classmethod
    def validate_teacher_reservation_request(cls, teacher_id: int, day_date: date, heure_debut: time, heure_fin: time) -> None:
        if heure_debut >= heure_fin:
            raise ValueError("L'heure de fin doit être postérieure à l'heure de début.")

        workdays = set(cls.get_working_days())
        if day_date.weekday() not in workdays:
            raise ValueError("La date demandée n'est pas un jour de classe configuré.")

        term_start = cls.get_term_start()
        term_end = cls.get_term_end()
        if term_start and day_date < term_start:
            raise ValueError("La date demandée est antérieure au début de l'année scolaire.")
        if term_end and day_date > term_end:
            raise ValueError("La date demandée est postérieure à la fin de l'année scolaire.")

        if cls.is_holiday(day_date) and not cls.get_allow_booking_in_holidays():
            raise ValueError("La réservation n'est pas autorisée pendant les vacances.")

        min_notice_days = cls.get_min_booking_notice_days()
        if min_notice_days:
            earliest = date.today() + timedelta(days=min_notice_days)
            if day_date < earliest:
                raise ValueError(f"Préavis insuffisant ({min_notice_days} jour(s) minimum).")

        max_daily = cls.get_max_daily_reservations_per_teacher()
        if max_daily:
            daily_count = (
                db.session.query(Reservation)
                .filter(
                    Reservation.enseignant_id == teacher_id,
                    Reservation.date_reservation == day_date,
                    Reservation.statut != "refusee",
                )
                .count()
            )
            if daily_count >= max_daily:
                raise ValueError(
                    f"Limite quotidienne atteinte ({max_daily} demande(s) max par enseignant)."
                )

    @classmethod
    def is_holiday(cls, day_date: date) -> bool:
        return day_date in set(cls.get_holidays())

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
    def get_working_days_display(cls) -> str:
        return ", ".join(str(d) for d in cls.get_working_days())

    @classmethod
    def get_day_name(cls, day_index: int) -> str:
        if 0 <= day_index < len(cls.DAY_NAMES):
            return cls.DAY_NAMES[day_index]
        return "?"

    @classmethod
    def get_working_day_names(cls) -> List[str]:
        return [cls.DAY_NAMES[d] for d in cls.get_working_days() if 0 <= d < len(cls.DAY_NAMES)]

    @classmethod
    def _default_academic_year(cls) -> str:
        current_year = datetime.now().year
        return f"{current_year}-{current_year + 1}"

    @classmethod
    def _parse_bool(cls, value: bool | str) -> bool:
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in {"1", "true", "vrai", "oui", "yes", "y"}:
            return True
        if text in {"0", "false", "faux", "non", "no", "n"}:
            return False
        raise ValueError("La valeur booléenne doit être true/false (ou 1/0).")

    @classmethod
    def _parse_iso_date(cls, raw: str | None) -> date | None:
        if not raw:
            return None
        raw = raw.strip()
        if not raw:
            return None
        try:
            return date.fromisoformat(raw)
        except ValueError:
            return None

    @classmethod
    def _parse_holidays(cls, raw: str | None) -> List[date]:
        raw = raw or ""
        holidays = []
        for token in raw.split(","):
            token = token.strip()
            if not token:
                continue
            parsed = cls._parse_iso_date(token)
            if parsed is None:
                raise ValueError(f"Date de vacances invalide: {token}. Format attendu AAAA-MM-DD.")
            holidays.append(parsed)
        return sorted(set(holidays))

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
