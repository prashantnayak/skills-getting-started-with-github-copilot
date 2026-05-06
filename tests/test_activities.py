from contextlib import contextmanager
from copy import deepcopy
from urllib.parse import quote

from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)


@contextmanager
def preserved_activities_state():
    snapshot = deepcopy(activities)

    try:
        yield
    finally:
        activities.clear()
        activities.update(snapshot)


def encode_activity_name(activity_name: str) -> str:
    return quote(activity_name, safe="")


def test_get_activities_returns_activity_data():
    # Arrange
    activity_name = "Chess Club"

    # Act
    response = client.get("/activities")
    payload = response.json()

    # Assert
    assert response.status_code == 200
    assert activity_name in payload
    assert payload[activity_name]["max_participants"] == 12
    assert "michael@mergington.edu" in payload[activity_name]["participants"]


def test_signup_adds_a_new_participant():
    with preserved_activities_state():
        # Arrange
        activity_name = "Chess Club"
        encoded_activity_name = encode_activity_name(activity_name)
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{encoded_activity_name}/signup",
            params={"email": email},
        )
        payload = response.json()

        # Assert
        assert response.status_code == 200
        assert payload == {"message": f"Signed up {email} for {activity_name}"}
        assert email in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant():
    with preserved_activities_state():
        # Arrange
        activity_name = "Chess Club"
        encoded_activity_name = encode_activity_name(activity_name)
        email = "michael@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{encoded_activity_name}/signup",
            params={"email": email},
        )
        payload = response.json()

        # Assert
        assert response.status_code == 400
        assert payload == {"detail": "Student already signed up"}


def test_signup_rejects_full_activity():
    with preserved_activities_state():
        # Arrange
        activity_name = "Full Activity"
        encoded_activity_name = encode_activity_name(activity_name)
        email = "waitlist@mergington.edu"
        activities[activity_name] = {
            "description": "Already at capacity",
            "schedule": "Fridays, 4:00 PM - 5:00 PM",
            "max_participants": 1,
            "participants": ["filled@mergington.edu"],
        }

        # Act
        response = client.post(
            f"/activities/{encoded_activity_name}/signup",
            params={"email": email},
        )
        payload = response.json()

        # Assert
        assert response.status_code == 400
        assert payload == {"detail": "Activity is full"}
        assert email not in activities[activity_name]["participants"]


def test_signup_returns_not_found_for_unknown_activity():
    # Arrange
    activity_name = "Unknown Activity"
    encoded_activity_name = encode_activity_name(activity_name)
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{encoded_activity_name}/signup",
        params={"email": email},
    )
    payload = response.json()

    # Assert
    assert response.status_code == 404
    assert payload == {"detail": "Activity not found"}


def test_unregister_removes_existing_participant():
    with preserved_activities_state():
        # Arrange
        activity_name = "Chess Club"
        encoded_activity_name = encode_activity_name(activity_name)
        email = "michael@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{encoded_activity_name}/participants",
            params={"email": email},
        )
        payload = response.json()

        # Assert
        assert response.status_code == 200
        assert payload == {"message": f"Removed {email} from {activity_name}"}
        assert email not in activities[activity_name]["participants"]


def test_unregister_returns_not_found_for_missing_participant():
    with preserved_activities_state():
        # Arrange
        activity_name = "Chess Club"
        encoded_activity_name = encode_activity_name(activity_name)
        email = "absent@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{encoded_activity_name}/participants",
            params={"email": email},
        )
        payload = response.json()

        # Assert
        assert response.status_code == 404
        assert payload == {"detail": "Participant not found"}


def test_unregister_returns_not_found_for_unknown_activity():
    # Arrange
    activity_name = "Unknown Activity"
    encoded_activity_name = encode_activity_name(activity_name)
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{encoded_activity_name}/participants",
        params={"email": email},
    )
    payload = response.json()

    # Assert
    assert response.status_code == 404
    assert payload == {"detail": "Activity not found"}