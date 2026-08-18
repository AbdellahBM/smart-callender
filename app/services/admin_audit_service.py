from datetime import datetime, timedelta, timezone
from typing import Optional

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
    def get_recent(limit: int = 200, since: Optional[datetime] = None):
        query = db.session.query(AdminActionLog).order_by(AdminActionLog.created_at.desc())
        if since is not None:
            query = query.filter(AdminActionLog.created_at >= since)
        return query.limit(limit).all()

    @staticmethod
    def purge_older_than(days: int):
        if days is None or days < 1:
            raise ValueError("La période de purge doit être supérieure ou égale à 1.")
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
        try:
            deleted = (
                db.session.query(AdminActionLog)
                .filter(AdminActionLog.created_at < cutoff)
                .delete(synchronize_session=False)
            )
            db.session.commit()
            return deleted
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def purge_all():
        try:
            deleted = db.session.query(AdminActionLog).delete(synchronize_session=False)
            db.session.commit()
            return deleted
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_for_export(limit: int = 5000, since: Optional[datetime] = None, entity_type: Optional[str] = None):
        query = db.session.query(AdminActionLog).order_by(AdminActionLog.created_at.desc())
        if since is not None:
            query = query.filter(AdminActionLog.created_at >= since)
        if entity_type is not None:
            query = query.filter(AdminActionLog.entity_type == entity_type)
        return query.limit(limit).all()

    @staticmethod
    def total_count():
        return (
            db.session.query(AdminActionLog)
            .count()
        )
