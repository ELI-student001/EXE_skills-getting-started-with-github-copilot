"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

# Create a test client
client = TestClient(app)


class TestRootEndpoint:
    """Test the root endpoint"""
    
    def test_root_redirects_to_static(self):
        """Test that the root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200


class TestActivitiesEndpoint:
    """Test the activities endpoint"""
    
    def test_get_activities(self):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        
        # Verify structure of activity
        for activity_name, activity_details in data.items():
            assert isinstance(activity_name, str)
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)
    
    def test_activities_have_initial_participants(self):
        """Test that activities have initial participants"""
        response = client.get("/activities")
        data = response.json()
        
        # At least some activities should have participants
        has_participants = any(
            len(activity["participants"]) > 0 
            for activity in data.values()
        )
        assert has_participants


class TestSignupEndpoint:
    """Test the signup endpoint"""
    
    def test_signup_for_activity(self):
        """Test signing up for an activity"""
        response = client.post(
            "/activities/Soccer/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]
        assert "Soccer" in data["message"]
    
    def test_signup_duplicate_student(self):
        """Test that duplicate signups are rejected"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            "/activities/Basketball/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            "/activities/Basketball/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
    
    def test_signup_invalid_activity(self):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/NonExistentActivity/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestUnregisterEndpoint:
    """Test the unregister endpoint"""
    
    def test_unregister_participant(self):
        """Test unregistering a participant"""
        email = "unregister@mergington.edu"
        
        # First, sign up
        client.post(
            "/activities/Art Club/signup",
            params={"email": email}
        )
        
        # Then unregister
        response = client.post(
            "/activities/Art Club/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"]
    
    def test_unregister_non_participant(self):
        """Test unregistering someone who isn't signed up"""
        response = client.post(
            "/activities/Music Band/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_unregister_invalid_activity(self):
        """Test unregistering from non-existent activity"""
        response = client.post(
            "/activities/NonExistent/unregister",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestActivityValidation:
    """Test activity data validation"""
    
    def test_all_activities_have_required_fields(self):
        """Test that all activities have required fields"""
        response = client.get("/activities")
        data = response.json()
        
        required_fields = [
            "description",
            "schedule",
            "max_participants",
            "participants"
        ]
        
        for activity_name, activity_details in data.items():
            for field in required_fields:
                assert field in activity_details, \
                    f"Activity '{activity_name}' missing '{field}'"
            
            # Verify data types
            assert isinstance(activity_details["description"], str)
            assert isinstance(activity_details["schedule"], str)
            assert isinstance(activity_details["max_participants"], int)
            assert isinstance(activity_details["participants"], list)
            
            # Verify max_participants is positive
            assert activity_details["max_participants"] > 0
