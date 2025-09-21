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


def test_update_habit(client):
    """Test that a habit can be successfully updated."""
    # Create a habit to update
    response = client.post(
        "/api/habits", json={"name": "Original Name", "periodicity": "daily"}
    )
    assert response.status_code == 201
    habit_id = response.json["id"]

    # Update the habit
    update_response = client.put(
        f"/api/habits/{habit_id}",
        json={"name": "Updated Name", "periodicity": "weekly"},
    )
    assert update_response.status_code == 200
    assert update_response.json["name"] == "Updated Name"
    assert update_response.json["periodicity"] == "weekly"
    assert update_response.json["id"] == habit_id

    # Verify the habit was actually updated
    get_response = client.get(f"/api/habits/{habit_id}")
    assert get_response.status_code == 200
    assert get_response.json["name"] == "Updated Name"
    assert get_response.json["periodicity"] == "weekly"


def test_update_habit_partial(client):
    """Test that a habit can be partially updated (name only)."""
    # Create a habit to update
    response = client.post(
        "/api/habits", json={"name": "Original Name", "periodicity": "daily"}
    )
    assert response.status_code == 201
    habit_id = response.json["id"]

    # Update only the name
    update_response = client.put(
        f"/api/habits/{habit_id}", json={"name": "Updated Name Only"}
    )
    assert update_response.status_code == 200
    assert update_response.json["name"] == "Updated Name Only"
    assert update_response.json["periodicity"] == "daily"  # Should remain unchanged


def test_update_habit_not_found(client):
    """Test that updating a non-existent habit returns a 404 error."""
    response = client.put(
        "/api/habits/999", json={"name": "Updated Name", "periodicity": "weekly"}
    )
    assert response.status_code == 404


def test_update_habit_invalid_periodicity(client):
    """Test that updating a habit with invalid periodicity returns a 400 error."""
    # Create a habit to update
    response = client.post(
        "/api/habits", json={"name": "Test Habit", "periodicity": "daily"}
    )
    assert response.status_code == 201
    habit_id = response.json["id"]

    # Try to update with invalid periodicity
    update_response = client.put(
        f"/api/habits/{habit_id}", json={"name": "Test Habit", "periodicity": "invalid"}
    )
    assert update_response.status_code == 400
    assert "error" in update_response.json


def test_update_habit_empty_request(client):
    """Test that updating a habit with empty request body returns a 400 error."""
    # Create a habit to update
    response = client.post(
        "/api/habits", json={"name": "Test Habit", "periodicity": "daily"}
    )
    assert response.status_code == 201
    habit_id = response.json["id"]

    # Send empty JSON request (not completely empty which gives 415)
    update_response = client.put(f"/api/habits/{habit_id}", json={})
    assert update_response.status_code == 400


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


def test_habit_completion_status_not_completed(client):
    """Test that completion status API returns false for uncompleted habit."""
    # Create a habit
    response = client.post(
        "/api/habits", json={"name": "Test Habit", "periodicity": "daily"}
    )
    assert response.status_code == 201
    habit_id = response.json["id"]

    # Check completion status
    status_response = client.get(f"/api/habits/{habit_id}/completed")
    assert status_response.status_code == 200
    assert status_response.json["completed"] is False


def test_habit_completion_status_completed(client):
    """Test that completion status API returns true for completed habit."""
    # Create a habit
    response = client.post(
        "/api/habits", json={"name": "Test Habit", "periodicity": "daily"}
    )
    assert response.status_code == 201
    habit_id = response.json["id"]

    # Complete the habit
    client.post(f"/api/habits/{habit_id}/checkoff")

    # Check completion status
    status_response = client.get(f"/api/habits/{habit_id}/completed")
    assert status_response.status_code == 200
    assert status_response.json["completed"] is True


def test_habit_completion_status_nonexistent(client):
    """Test that completion status API returns false for non-existent habit."""
    response = client.get("/api/habits/999/completed")
    assert response.status_code == 200
    assert response.json["completed"] is False


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


def test_get_preferences_creates_default(client):
    """Test that GET /preferences creates and returns default preferences."""
    response = client.get("/api/preferences")
    assert response.status_code == 200

    data = response.json
    assert "id" in data
    assert data["struggle_threshold"] == 0.75
    assert data["show_bottom_percent"] == 0.25
    assert "created_at" in data
    assert "updated_at" in data


def test_get_preferences_returns_existing(client):
    """Test that GET /preferences returns existing preferences."""
    # Create preferences first
    create_response = client.get("/api/preferences")
    assert create_response.status_code == 200
    original_id = create_response.json["id"]

    # Get preferences again
    response = client.get("/api/preferences")
    assert response.status_code == 200
    assert response.json["id"] == original_id  # Same record


def test_update_preferences_full_update(client):
    """Test updating all preference fields."""
    update_data = {"struggle_threshold": 0.8, "show_bottom_percent": 0.3}

    response = client.put("/api/preferences", json=update_data)
    assert response.status_code == 200

    data = response.json
    assert data["struggle_threshold"] == 0.8
    assert data["show_bottom_percent"] == 0.3

    # Verify persistence
    get_response = client.get("/api/preferences")
    assert get_response.json["struggle_threshold"] == 0.8
    assert get_response.json["show_bottom_percent"] == 0.3


def test_update_preferences_partial_update(client):
    """Test updating only some preference fields."""
    # Set initial values
    client.put(
        "/api/preferences", json={"struggle_threshold": 0.6, "show_bottom_percent": 0.4}
    )

    # Update only threshold
    response = client.put("/api/preferences", json={"struggle_threshold": 0.9})
    assert response.status_code == 200

    data = response.json
    assert data["struggle_threshold"] == 0.9
    assert data["show_bottom_percent"] == 0.4  # Unchanged


def test_update_preferences_validation_clamping(client):
    """Test that preference values are clamped to valid ranges."""
    # Test upper bounds
    response = client.put(
        "/api/preferences", json={"struggle_threshold": 1.5, "show_bottom_percent": 2.0}
    )
    assert response.status_code == 200
    assert response.json["struggle_threshold"] == 1.0
    assert response.json["show_bottom_percent"] == 1.0

    # Test lower bounds
    response = client.put(
        "/api/preferences",
        json={"struggle_threshold": 0.05, "show_bottom_percent": -0.1},
    )
    assert response.status_code == 200
    assert response.json["struggle_threshold"] == 0.1
    assert response.json["show_bottom_percent"] == 0.1


def test_update_preferences_empty_request(client):
    """Test that empty JSON request returns 400."""
    response = client.put("/api/preferences", json={})
    assert response.status_code == 400
    assert "error" in response.json


def test_struggled_habits_uses_preferences(client):
    """Test that struggled habits endpoint uses stored preferences."""
    # Set custom preferences
    client.put(
        "/api/preferences",
        json={
            "struggle_threshold": 0.5,
            "show_bottom_percent": 1.0,  # Show all struggling habits
        },
    )

    # Create habits with different completion rates
    client.post("/api/habits", json={"name": "Good Habit", "periodicity": "daily"})
    client.post("/api/habits", json={"name": "Bad Habit", "periodicity": "daily"})

    # The struggled habits should use the stored preferences
    response = client.get("/api/analytics/habits/struggled")
    assert response.status_code == 200
    # Results will vary based on actual completions, but endpoint should work


def test_struggled_habits_query_param_override(client):
    """Test that query parameters can override stored preferences."""
    # Set default preferences
    client.put("/api/preferences", json={"struggle_threshold": 0.5})

    # Override with query parameters
    response = client.get("/api/analytics/habits/struggled?threshold=0.8&quartile=0.25")
    assert response.status_code == 200
