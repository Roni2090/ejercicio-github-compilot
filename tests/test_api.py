"""
Integration tests for the Mergington High School FastAPI application.
Tests follow the Arrange-Act-Assert (AAA) pattern and isolate shared state.
"""

import copy
import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def restore_activities():
    """Restore the in-memory activities state before and after each test."""
    app_module = importlib.import_module("src.app")
    original_activities = copy.deepcopy(app_module.activities)

    yield

    app_module.activities.clear()
    app_module.activities.update(original_activities)


@pytest.fixture
def client():
    """Provide a TestClient instance for the FastAPI app."""
    app_module = importlib.import_module("src.app")
    return TestClient(app_module.app)


def test_get_activities(client):
    """GET /activities returns a dictionary of available activities."""
    # Arrange
    # (client fixture provides the test client)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    activity = data["Chess Club"]
    assert "description" in activity
    assert "schedule" in activity
    assert "max_participants" in activity
    assert "participants" in activity
    assert isinstance(activity["participants"], list)


def test_signup_adds_participant(client):
    """POST /activities/{activity_name}/signup adds a new participant."""
    # Arrange
    activity_name = "Chess Club"
    new_email = "newstudent@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": new_email},
    )

    # Assert
    assert response.status_code == 200
    assert "Signed up" in response.json()["message"]

    # Verify participant was added
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert new_email in activities_data[activity_name]["participants"]


def test_signup_duplicate_fails(client):
    """Signing up the same student twice returns 400 on the second attempt."""
    # Arrange
    activity_name = "Chess Club"
    duplicate_email = "duplicate@mergington.edu"

    # Act
    first_response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": duplicate_email},
    )
    second_response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": duplicate_email},
    )

    # Assert
    assert first_response.status_code == 200
    assert second_response.status_code == 400
    assert "already signed up" in second_response.json()["detail"]


def test_remove_participant(client):
    """DELETE /activities/{activity_name}/participants removes a participant."""
    # Arrange
    activity_name = "Chess Club"
    email_to_remove = "michael@mergington.edu"

    activities_before = client.get("/activities").json()
    assert email_to_remove in activities_before[activity_name]["participants"]

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email_to_remove},
    )

    # Assert
    assert response.status_code == 200
    assert "Removed" in response.json()["message"]

    activities_after = client.get("/activities").json()
    assert email_to_remove not in activities_after[activity_name]["participants"]


def test_signup_invalid_activity_returns_404(client):
    """Signing up for an invalid activity returns 404."""
    # Arrange
    invalid_activity = "Nonexistent Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{invalid_activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_remove_invalid_participant_returns_404(client):
    """Removing a participant who does not exist returns 404."""
    # Arrange
    activity_name = "Chess Club"
    invalid_email = "ghost@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": invalid_email},
    )

    # Assert
    assert response.status_code == 404
    assert "Participant not found" in response.json()["detail"]
