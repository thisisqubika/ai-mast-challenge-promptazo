"""In-memory check-in registry seeded with demo users."""

_checked_in: dict[str, str] = {
    "user_001": "Alice",
    "user_002": "Bob",
    "user_003": "Carlos",
}


def is_checked_in(user_id: str) -> bool:
    return user_id in _checked_in


def register(user_id: str, name: str) -> None:
    _checked_in[user_id] = name
