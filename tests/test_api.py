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


def test_get_habits_analytics(client):
    """Test that the analytics API returns habits data."""
    # Create test habits
    client.post("/api/habits", json={"name": "Daily Habit", "periodicity": "daily"})
    client.post("/api/habits", json={"name": "Weekly Habit", "periodicity": "weekly"})

    response = client.get("/api/analytics/habits")
    assert response.status_code == 200
    assert isinstance(response.json, list)
    assert len(response.json) == 2


def test_get_habits_analytics_with_filter(client):
    """Test that the analytics API filters habits by periodicity."""
    # Create test habits
    client.post("/api/habits", json={"name": "Daily Habit", "periodicity": "daily"})
    client.post("/api/habits", json={"name": "Weekly Habit", "periodicity": "weekly"})

    response = client.get("/api/analytics/habits?periodicity=daily")
    assert response.status_code == 200
    assert isinstance(response.json, list)
    assert len(response.json) == 1
    assert response.json[0]["periodicity"] == "DAILY"


def test_get_habit_streaks(client):
    """Test that the analytics API returns streak data for a habit."""
    # Create a test habit
    response = client.post(
        "/api/habits", json={"name": "Test Habit", "periodicity": "daily"}
    )
    habit_id = response.json["id"]

    # Check off the habit to create completion data
    client.post(f"/api/habits/{habit_id}/checkoff")

    response = client.get(f"/api/analytics/habits/{habit_id}/streaks")
    assert response.status_code == 200
    assert "longest_streak" in response.json
    assert "current_streak" in response.json
    assert response.json["longest_streak"] >= 0
    assert response.json["current_streak"] >= 0


def test_get_habit_streaks_not_found(client):
    """Test that streak analytics for non-existent habit returns empty streaks."""
    response = client.get("/api/analytics/habits/999/streaks")
    assert response.status_code == 200
    assert response.json["longest_streak"] == 0
    assert response.json["current_streak"] == 0


def test_get_struggled_habits(client):
    """Test that the analytics API returns struggled habits data."""
    # Create test habits
    client.post("/api/habits", json={"name": "Good Habit", "periodicity": "daily"})
    client.post(
        "/api/habits", json={"name": "Struggling Habit", "periodicity": "daily"}
    )

    response = client.get("/api/analytics/habits/struggled")
    assert response.status_code == 200
    assert isinstance(response.json, list)


def test_get_completion_rates(client):
    """Test that the analytics API returns completion rates for all habits."""
    # Create test habits
    response1 = client.post(
        "/api/habits", json={"name": "Test Habit 1", "periodicity": "daily"}
    )
    client.post("/api/habits", json={"name": "Test Habit 2", "periodicity": "weekly"})

    # Check off one habit
    habit_id_1 = response1.json["id"]
    client.post(f"/api/habits/{habit_id_1}/checkoff")

    response = client.get("/api/analytics/habits/completion-rates")
    assert response.status_code == 200
    assert isinstance(response.json, list)
    assert len(response.json) == 2

    # Verify structure of response
    for habit_data in response.json:
        assert "id" in habit_data
        assert "name" in habit_data
        assert "completion_rate" in habit_data


def test_get_best_worst_day(client):
    """Test that the analytics API returns best and worst day data for weekly habit."""
    # Create a weekly habit
    response = client.post(
        "/api/habits", json={"name": "Weekly Habit", "periodicity": "weekly"}
    )
    habit_id = response.json["id"]

    response = client.get(f"/api/analytics/habits/{habit_id}/best-worst-day")
    assert response.status_code == 200
    assert "best_day" in response.json
    assert "worst_day" in response.json


def test_get_best_worst_day_daily_habit(client):
    """Test that best/worst day analytics for daily habit returns None values."""
    # Create a daily habit
    response = client.post(
        "/api/habits", json={"name": "Daily Habit", "periodicity": "daily"}
    )
    habit_id = response.json["id"]

    response = client.get(f"/api/analytics/habits/{habit_id}/best-worst-day")
    assert response.status_code == 200
    assert response.json["best_day"] is None
    assert response.json["worst_day"] is None


def test_get_best_worst_day_not_found(client):
    """Test that best/worst day analytics for non-existent habit returns None values."""
    response = client.get("/api/analytics/habits/999/best-worst-day")
    assert response.status_code == 200
    assert response.json["best_day"] is None
    assert response.json["worst_day"] is None
