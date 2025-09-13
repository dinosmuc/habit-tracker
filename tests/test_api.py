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


def test_create_habit_invalid_data(client):
    """Test that creating a habit with invalid data returns a 400 error."""
    invalid_habit_data = {"name": "Test Habit"}  # Missing 'periodicity'
    response = client.post("/api/habits", json=invalid_habit_data)
    assert response.status_code == 400


def test_delete_habit(client):
    """Test that an existing habit can be deleted."""
    # Create a habit to delete
    response = client.post(
        "/api/habits", json={"name": "Habit to Delete", "periodicity": "daily"}
    )
    assert response.status_code == 201
    habit_id = response.json["id"]

    # Delete the habit
    delete_response = client.delete(f"/api/habits/{habit_id}")
    assert delete_response.status_code == 200

    # Verify it's gone
    get_response = client.get(f"/api/habits/{habit_id}")
    assert get_response.status_code == 404


def test_delete_habit_not_found(client):
    """Test that deleting a non-existent habit returns a 404 error."""
    response = client.delete("/api/habits/999")
    assert response.status_code == 404


def test_check_off_habit(client):
    """Test that an existing habit can be successfully checked off."""
    # Create a habit to check off
    response = client.post(
        "/api/habits", json={"name": "Habit to Check Off", "periodicity": "daily"}
    )
    assert response.status_code == 201
    habit_id = response.json["id"]

    # Check off the habit
    checkoff_response = client.post(f"/api/habits/{habit_id}/checkoff")
    assert checkoff_response.status_code == 201
    assert checkoff_response.json["habit_id"] == habit_id


def test_check_off_habit_not_found(client):
    """Test that checking off a non-existent habit returns a 404 error."""
    response = client.post("/api/habits/999/checkoff")
    assert response.status_code == 404
