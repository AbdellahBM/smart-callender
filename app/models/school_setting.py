from datetime import datetime, timezone

from app.extensions import db


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SchoolSetting(db.Model):
    """
    Paramètres de configuration école persistés en base.
    key: nom du paramètre (unique)
    value: valeur brute sous forme texte
    """

    __tablename__ = "school_settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(120), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    def __repr__(self):
        return f"<SchoolSetting {self.key}={self.value}>"
