from datetime import datetime, timezone

from app.extensions import db


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AdminActionLog(db.Model):
    """Journal des actions administrateur pour la traçabilité."""

    __tablename__ = "admin_action_logs"

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("utilisateurs.id"), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50), nullable=True)
    entity_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    admin = db.relationship("Utilisateur")

    def __repr__(self):
        return f"<AdminActionLog action={self.action} admin={self.admin_id} entity={self.entity_type}:{self.entity_id}>"
