import pytest

from habittracker import database
from habittracker.app import create_app
from habittracker.models import Base


@pytest.fixture(scope="session")
def app():
    """Fixture to create a Flask app instance for the test session."""
    app = create_app(db_url="sqlite:///:memory:")
    app.config.update({"TESTING": True})
    return app


@pytest.fixture(scope="function")
def client(app):
    """
    A test client for the app. This fixture also handles creating
    and dropping database tables for each test.
    """
    with app.app_context():
        # Create all tables using the app's configured engine
        Base.metadata.create_all(bind=database.engine)

        yield app.test_client()  # The tests run here

        # Drop all tables after the test is done
        Base.metadata.drop_all(bind=database.engine)
