from flask import Flask, send_from_directory

from habittracker import api, database


def create_app(db_url="sqlite:///habittracker.db"):
    """Application factory for creating Flask app instances."""
    app = Flask(__name__, static_folder="../frontend", static_url_path="")

    # Dispose of old connections and create a fresh engine for the given URL.
    if database.engine:
        database.engine.dispose()

    # Create new engine using the centralized utility function
    database.engine = database.create_database_engine(db_url)

    # Rebind the SessionLocal to the new, correct engine.
    database.SessionLocal.configure(bind=database.engine)

    app.teardown_appcontext(database.close_db)
    app.register_blueprint(api.bp)

    @app.route("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    return app
