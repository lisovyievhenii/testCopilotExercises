"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all available activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) > 0
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities

    def test_get_activities_returns_correct_structure(self, client):
        """Test that each activity has the required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, details in activities.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)
            assert isinstance(details["max_participants"], int)

    def test_get_activities_has_initial_participants(self, client):
        """Test that activities have the expected initial participants"""
        response = client.get("/activities")
        activities = response.json()
        
        # Chess Club should have 2 participants
        assert len(activities["Chess Club"]["participants"]) == 2
        assert "michael@mergington.edu" in activities["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in activities["Chess Club"]["participants"]


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_for_activity_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball Team/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Basketball Team" in data["message"]

    def test_signup_adds_participant_to_activity(self, client):
        """Test that signing up actually adds the student to the activity"""
        # Sign up a student
        client.post("/activities/Soccer Club/signup?email=test@mergington.edu")
        
        # Verify participant was added
        response = client.get("/activities")
        activities = response.json()
        assert "test@mergington.edu" in activities["Soccer Club"]["participants"]

    def test_signup_duplicate_prevention(self, client):
        """Test that duplicate signup is prevented"""
        email = "duplicate@mergington.edu"
        activity = "Art Club"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]

    def test_signup_invalid_activity(self, client):
        """Test signup for a non-existent activity"""
        response = client.post(
            "/activities/NonExistentActivity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_multiple_students_same_activity(self, client):
        """Test that multiple different students can sign up for the same activity"""
        activity = "Drama Club"
        
        # Sign up first student
        response1 = client.post(
            f"/activities/{activity}/signup?email=student1@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Sign up second student
        response2 = client.post(
            f"/activities/{activity}/signup?email=student2@mergington.edu"
        )
        assert response2.status_code == 200
        
        # Verify both are in the activity
        response = client.get("/activities")
        activities = response.json()
        assert "student1@mergington.edu" in activities[activity]["participants"]
        assert "student2@mergington.edu" in activities[activity]["participants"]


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        email = "test@mergington.edu"
        activity = "Debate Club"
        
        # First sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Then unregister
        response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregistering actually removes the student from the activity"""
        email = "removeme@mergington.edu"
        activity = "Science Club"
        
        # Sign up student
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Verify participant was added
        response = client.get("/activities")
        activities = response.json()
        assert email in activities[activity]["participants"]
        
        # Unregister student
        client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Verify participant was removed
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities[activity]["participants"]

    def test_unregister_non_existent_participant(self, client):
        """Test unregistering a student not in the activity"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not registered" in data["detail"].lower()

    def test_unregister_invalid_activity(self, client):
        """Test unregistering from a non-existent activity"""
        response = client.delete(
            "/activities/FakeActivity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_unregister_existing_participant(self, client):
        """Test unregistering an existing initial participant"""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Verify participant is initially there
        response = client.get("/activities")
        activities = response.json()
        assert email in activities[activity]["participants"]
        
        # Unregister
        response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Verify participant was removed
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities[activity]["participants"]


class TestIntegration:
    """Integration tests for signup and unregister workflows"""

    def test_signup_unregister_cycle(self, client):
        """Test complete signup and unregister cycle"""
        email = "cycle@mergington.edu"
        activity = "Basketball Team"
        
        # Sign up
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify participant is added
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200
        
        # Verify participant is removed
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]

    def test_participant_list_updates_correctly(self, client):
        """Test that participant list updates correctly after multiple operations"""
        activity = "Programming Class"
        emails = ["user1@mergington.edu", "user2@mergington.edu", "user3@mergington.edu"]
        
        # Sign up multiple students
        for email in emails:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all are registered
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        for email in emails:
            assert email in participants
        
        # Unregister middle student
        client.delete(f"/activities/{activity}/unregister?email={emails[1]}")
        
        # Verify correct list
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        assert emails[0] in participants
        assert emails[1] not in participants
        assert emails[2] in participants
