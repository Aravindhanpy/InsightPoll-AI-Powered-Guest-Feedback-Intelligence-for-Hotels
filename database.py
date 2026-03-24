"""
database.py
-----------
Single source of truth for the database connection.

- Uses SQLite (file: insightpoll.db in the project root)
- SQLModel wraps SQLAlchemy — same engine, cleaner syntax
- get_session() is a FastAPI dependency injected into every endpoint
  that needs DB access. It opens a session, yields it, then closes it
  automatically after the request — no manual cleanup needed.
"""

from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "sqlite:///./insightpoll.db"

engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables():
    """Called once at server startup. Creates all tables that don't exist yet."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency. Use as: session: Session = Depends(get_session)"""
    with Session(engine) as session:
        yield session
