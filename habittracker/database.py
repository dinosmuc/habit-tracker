import os

from flask import g
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker


def create_database_engine(db_url):
    """Create and configure a SQLAlchemy engine with proper settings."""
    if db_url.startswith("sqlite"):
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(db_url)

    # Enable foreign key constraints for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if "sqlite" in db_url:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///habittracker.db")
engine = create_database_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Gets the database session for the current request.
    Creates a new session if one doesn't exist.
    """
    if "db" not in g:
        g.db = SessionLocal()
    return g.db


def close_db(e=None):
    """
    Closes the database session at the end of the request.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()
