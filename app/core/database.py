"""SQLAlchemy engine and session management."""

from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Base class for application database models."""


def _engine_kwargs(database_url: str) -> dict[str, object]:
    if database_url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {"pool_pre_ping": True}


engine = create_engine(
    get_settings().database_url,
    **_engine_kwargs(get_settings().database_url),
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session and close it after the request."""

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def initialize_database() -> None:
    """Create tables and apply small additive local-schema upgrades."""

    from app.models import Evidence, Page, Project

    Base.metadata.create_all(bind=engine)
    page_columns = {column["name"] for column in inspect(engine).get_columns("pages")}
    if "raw_html" not in page_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE pages ADD COLUMN raw_html TEXT"))