import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

# Capture initial state once at import time, before any test mutates it
INITIAL_STATE = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the shared in-memory activities dict before each test."""
    activities.clear()
    activities.update(copy.deepcopy(INITIAL_STATE))


@pytest.fixture
def client():
    return TestClient(app, follow_redirects=False)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_200(client):
    # Arrange — no special setup needed

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_get_activities_contains_all_nine(client):
    # Arrange
    expected_names = {
        "Chess Club",
        "Programming Class",
        "Gym Class",
        "Basketball Team",
        "Tennis Club",
        "Art Studio",
        "Drama Club",
        "Debate Team",
        "Science Club",
    }

    # Act
    response = client.get("/activities")

    # Assert
    assert response.json().keys() == expected_names


def test_get_activities_structure(client):
    # Arrange
    required_keys = {"description", "schedule", "max_participants", "participants"}

    # Act
    response = client.get("/activities")

    # Assert
    for activity in response.json().values():
        assert required_keys.issubset(activity.keys())
        assert isinstance(activity["participants"], list)


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_success(client):
    # Arrange
    activity_name = "Chess Club"
    new_email = "newstudent@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={new_email}")

    # Assert
    assert response.status_code == 200
    assert "message" in response.json()
    assert new_email in activities[activity_name]["participants"]


def test_signup_unknown_activity(client):
    # Arrange
    activity_name = "Nonexistent Activity"
    email = "student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 404


def test_signup_duplicate_email(client):
    # Arrange — michael is already seeded in Chess Club
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={existing_email}")

    # Assert
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_unregister_success(client):
    # Arrange — michael is seeded in Chess Club
    activity_name = "Chess Club"
    enrolled_email = "michael@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/signup?email={enrolled_email}")

    # Assert
    assert response.status_code == 200
    assert "message" in response.json()
    assert enrolled_email not in activities[activity_name]["participants"]


def test_unregister_unknown_activity(client):
    # Arrange
    activity_name = "Nonexistent Activity"
    email = "student@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 404


def test_unregister_not_enrolled(client):
    # Arrange — this email is not in Chess Club
    activity_name = "Chess Club"
    unenrolled_email = "nobody@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/signup?email={unenrolled_email}")

    # Assert
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

def test_root_redirects(client):
    # Arrange — client is already configured with follow_redirects=False

    # Act
    response = client.get("/")

    # Assert
    assert response.status_code in (307, 308)
    assert response.headers["location"].endswith("/static/index.html")
