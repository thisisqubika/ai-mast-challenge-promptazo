"""In-memory check-in registry seeded with demo users."""

from app.data.seed import FANS

_checked_in: dict[str, str] = {f.user_id: f.name for f in FANS}


def is_checked_in(user_id: str) -> bool:
    return user_id in _checked_in


def register(user_id: str, name: str) -> None:
    _checked_in[user_id] = name
