from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


_engine = None
_SessionLocal = None


def init_db(url: str) -> None:
    global _engine, _SessionLocal
    kwargs: dict = {}
    if "sqlite" in url:
        from sqlalchemy.pool import StaticPool

        kwargs["connect_args"] = {"check_same_thread": False}
        if ":memory:" in url:
            kwargs["poolclass"] = StaticPool
    _engine = create_engine(url, **kwargs)
    _SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False, expire_on_commit=False)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    session: Session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
