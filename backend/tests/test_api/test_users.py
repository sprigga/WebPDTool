"""Tests for users API endpoints"""
import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.main import app
from app.models.user import User, UserRole
from app.core.database import Base


@pytest.fixture(scope="function")
def db_session():
    """Get database session"""
    # Use a file-based database for tests to avoid thread/connection issues
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    # connect_args={"check_same_thread": False} is needed for TestClient
    test_engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(bind=test_engine)

    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        test_engine.dispose()
        # Clean up the temporary file
        try:
            os.unlink(db_path)
        except:
            pass


@pytest.fixture
def client(db_session):
    """Get test client with database override"""
    from app.core.database import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db_session):
    """Create admin user"""
    from app.core.security import create_access_token
    from app.services import auth as auth_service
    from app.schemas.user import UserCreate

    user_data = UserCreate(
        username="admin_test",
        password="admin123",
        role=UserRole.ADMIN,
        full_name="Test Admin",
        email="admin@test.com"
    )
    user = auth_service.create_user(db_session, user_data)

    token = create_access_token(
        data={"sub": user.username, "role": user.role.value, "id": user.id}
    )
    return {"user": user, "token": token}


@pytest.fixture
def engineer_user(db_session):
    """Create engineer user"""
    from app.core.security import create_access_token
    from app.services import auth as auth_service
    from app.schemas.user import UserCreate

    user_data = UserCreate(
        username="engineer_test",
        password="eng123",
        role=UserRole.ENGINEER,
        full_name="Test Engineer"
    )
    user = auth_service.create_user(db_session, user_data)

    token = create_access_token(
        data={"sub": user.username, "role": user.role.value, "id": user.id}
    )
    return {"user": user, "token": token}


def test_get_users_success(client, admin_user):
    """Test getting list of users"""
    response = client.get(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1
    assert response.json()[0]["username"] == "admin_test"


def test_get_user_by_id(client, admin_user):
    """Test getting user by ID"""
    response = client.get(
        f"/api/users/{admin_user['user'].id}",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "admin_test"


def test_create_user_success(client, admin_user):
    """Test creating a new user"""
    user_data = {
        "username": "testuser",
        "password": "password123",
        "role": "operator",
        "full_name": "Test User",
        "email": "test@example.com"
    }
    response = client.post(
        "/api/users",
        json=user_data,
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert response.status_code == 201
    assert response.json()["username"] == "testuser"
    assert "password_hash" not in response.json()


def test_create_user_duplicate_username(client, admin_user):
    """Test creating user with duplicate username fails"""
    user_data = {
        "username": "admin_test",
        "password": "password123",
        "role": "operator"
    }
    response = client.post(
        "/api/users",
        json=user_data,
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_update_user_success(client, admin_user):
    """Test updating user information"""
    # First create a user to update
    user_data = {
        "username": "updateme",
        "password": "pass123",
        "role": "engineer",
        "full_name": "Original Name"
    }
    create_response = client.post(
        "/api/users",
        json=user_data,
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]

    # Now update the user
    update_data = {
        "full_name": "Updated Name",
        "email": "updated@example.com"
    }
    response = client.put(
        f"/api/users/{user_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"
    assert response.json()["email"] == "updated@example.com"


def test_delete_user_success(client, admin_user):
    """Test deleting a user"""
    # First create a user to delete
    user_data = {
        "username": "deleteme",
        "password": "pass123",
        "role": "engineer"
    }
    create_response = client.post(
        "/api/users",
        json=user_data,
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]

    # Now delete the user
    response = client.delete(
        f"/api/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert response.status_code == 204

    # Verify user is deleted
    get_response = client.get(
        f"/api/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert get_response.status_code == 404


def test_non_admin_cannot_create_user(client, engineer_user):
    """Test that non-admin cannot create users"""
    user_data = {
        "username": "shouldnotwork",
        "password": "pass123",
        "role": "operator"
    }
    response = client.post(
        "/api/users",
        json=user_data,
        headers={"Authorization": f"Bearer {engineer_user['token']}"}
    )
    assert response.status_code == 403


def test_non_admin_cannot_update_user(client, engineer_user, admin_user):
    """Test that non-admin cannot update users"""
    update_data = {"full_name": "Should Not Work"}
    response = client.put(
        f"/api/users/{admin_user['user'].id}",
        json=update_data,
        headers={"Authorization": f"Bearer {engineer_user['token']}"}
    )
    assert response.status_code == 403


def test_non_admin_cannot_delete_user(client, engineer_user, admin_user):
    """Test that non-admin cannot delete users"""
    response = client.delete(
        f"/api/users/{admin_user['user'].id}",
        headers={"Authorization": f"Bearer {engineer_user['token']}"}
    )
    assert response.status_code == 403


def test_user_cannot_delete_themselves(client, admin_user):
    """Test that admin cannot delete their own account"""
    response = client.delete(
        f"/api/users/{admin_user['user'].id}",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert response.status_code == 400
    assert "Cannot delete your own account" in response.json()["detail"]


def test_get_user_not_found(client, admin_user):
    """Test getting non-existent user returns 404"""
    response = client.get(
        "/api/users/99999",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert response.status_code == 404


def test_update_user_not_found(client, admin_user):
    """Test updating non-existent user returns 404"""
    update_data = {"full_name": "Should Not Work"}
    response = client.put(
        "/api/users/99999",
        json=update_data,
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert response.status_code == 404


def test_delete_user_not_found(client, admin_user):
    """Test deleting non-existent user returns 404"""
    response = client.delete(
        "/api/users/99999",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert response.status_code == 404


def test_change_password_success(client, admin_user):
    """Test changing user password"""
    # First create a user
    user_data = {
        "username": "passchangeuser",
        "password": "oldpassword",
        "role": "engineer"
    }
    create_response = client.post(
        "/api/users",
        json=user_data,
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]

    # Now change the password
    response = client.put(
        f"/api/users/{user_id}/password",
        params={"new_password": "newpassword"},
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert response.status_code == 200


def test_non_admin_can_change_own_password(client, engineer_user):
    """Test that non-admin user can change their own password"""
    # Engineer changing their own password should succeed
    response = client.put(
        f"/api/users/{engineer_user['user'].id}/password",
        params={"new_password": "newengpass123"},
        headers={"Authorization": f"Bearer {engineer_user['token']}"}
    )
    assert response.status_code == 200
    # Verify password was changed by checking response contains the user
    assert response.json()["id"] == engineer_user['user'].id


def test_non_admin_cannot_change_other_password(client, engineer_user, admin_user):
    """Test that non-admin user cannot change another user's password"""
    # Engineer trying to change admin's password should fail with 403
    response = client.put(
        f"/api/users/{admin_user['user'].id}/password",
        params={"new_password": "hacked123"},
        headers={"Authorization": f"Bearer {engineer_user['token']}"}
    )
    assert response.status_code == 403
    # Verify the error message contains expected text
    assert "can only change your own password" in response.json()["detail"].lower()
