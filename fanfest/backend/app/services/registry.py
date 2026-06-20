"""Check-in registry backed by the registrations DB table."""

from app.db.database import get_session
from app.db.models import RegistrationModel


def is_checked_in(user_id: str) -> bool:
    with get_session() as db:
        return (
            db.query(RegistrationModel)
            .filter_by(user_id=user_id, checked_in=True)
            .count()
            > 0
        )


def register(user_id: str, name: str) -> None:
    # No-op: checkin_user in events_service persists directly to DB.
    pass
