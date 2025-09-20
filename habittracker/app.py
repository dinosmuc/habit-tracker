from flask import Flask, send_from_directory
from sqlalchemy import create_engine, event

from habittracker import api, database


def create_app(db_url="sqlite:///habittracker.db"):
    """Application factory for creating Flask app instances."""
    app = Flask(__name__, static_folder="../frontend", static_url_path="")

    # Dispose of old connections and create a fresh engine for the given URL.
    if database.engine:
        database.engine.dispose()
    database.engine = create_engine(db_url, connect_args={"check_same_thread": False})

    # Enable foreign key constraints for SQLite
    @event.listens_for(database.engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if "sqlite" in db_url:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    # Rebind the SessionLocal to the new, correct engine.
    database.SessionLocal.configure(bind=database.engine)

    app.teardown_appcontext(database.close_db)
    app.register_blueprint(api.bp)

    @app.route("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    return app
