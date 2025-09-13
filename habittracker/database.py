from flask import g
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///habittracker.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
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
