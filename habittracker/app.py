from flask import Flask
from sqlalchemy import create_engine

from habittracker import api, database


def create_app(db_url="sqlite:///habittracker.db"):
    """Application factory for creating Flask app instances."""
    app = Flask(__name__)

    # Dispose of old connections and create a fresh engine for the given URL.
    if database.engine:
        database.engine.dispose()
    database.engine = create_engine(db_url, connect_args={"check_same_thread": False})

    # Rebind the SessionLocal to the new, correct engine.
    database.SessionLocal.configure(bind=database.engine)

    app.teardown_appcontext(database.close_db)
    app.register_blueprint(api.bp)
    return app
