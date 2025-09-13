from flask import Flask

from habittracker import api, database


def create_app(db_url="sqlite:///habittracker.db"):
    """Application factory for creating Flask app instances."""
    app = Flask(__name__)

    # Configure the database engine with the provided URL
    database.engine.url = db_url

    # Register the teardown function to close DB sessions
    app.teardown_appcontext(database.close_db)

    # Register the API blueprint to add all API routes
    app.register_blueprint(api.bp)

    return app


# This block allows running the app directly for development
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
