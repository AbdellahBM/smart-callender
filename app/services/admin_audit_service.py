from app.extensions import db
from app.models import AdminActionLog


class AdminAuditService:
    @staticmethod
    def log_action(admin_user, action, entity_type=None, entity_id=None, details=None):
        try:
            admin_id = getattr(admin_user, "id", None)
            db.session.add(
                AdminActionLog(
                    admin_id=admin_id,
                    action=action,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    details=details,
                )
            )
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    @staticmethod
    def get_recent(limit=200):
        return (
            db.session.query(AdminActionLog)
            .order_by(AdminActionLog.created_at.desc())
            .limit(limit)
            .all()
        )
