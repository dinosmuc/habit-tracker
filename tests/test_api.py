import pytest

from habittracker.app import create_app


@pytest.fixture
def client():
    """Configures the app to use a temporary in-memory database for testing."""
    app = create_app(db_url="sqlite:///:memory:")
    app.config["TESTING"] = True

    with app.test_client() as client:
        with app.app_context():
            pass
        yield client


def test_get_all_habits(client):
    """Test that the API returns all habits successfully."""
    response = client.get("/api/habits")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert isinstance(response.json, list)


def test_get_single_habit(client):
    """Test that the API returns a single, existing habit correctly."""
    # First, create a habit to ensure one exists in the empty test DB
    response = client.post(
        "/api/habits", json={"name": "Test Habit", "periodicity": "daily"}
    )
    assert response.status_code == 201
    habit_id = response.json["id"]

    # Now, test getting that specific habit
    response = client.get(f"/api/habits/{habit_id}")
    assert response.status_code == 200
    assert response.json["name"] == "Test Habit"


def test_get_single_habit_not_found(client):
    """Test that the API returns a 404 error for a non-existent habit."""
    response = client.get("/api/habits/999")
    assert response.status_code == 404
