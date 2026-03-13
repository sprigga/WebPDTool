"""Tests for users API endpoints"""
import pytest
import tempfile
import os
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.models.user import User, UserRole
from app.core.database import Base
from app.core.security import get_password_hash


@pytest.fixture(scope="function")
def db_session():
    """Get shared SQLite database (sync + async engines on same file)"""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    # Sync engine for get_db override (used by auth dependencies)
    sync_engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False}
    )
    SyncSession = sessionmaker(bind=sync_engine)

    # Async engine for get_async_db override (used by users endpoints)
    async_engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"check_same_thread": False}
    )
    AsyncSession_ = async_sessionmaker(bind=async_engine, expire_on_commit=False)

    # Create tables using sync engine
    Base.metadata.create_all(bind=sync_engine)

    yield {"sync": SyncSession, "async": AsyncSession_}

    async def _dispose():
        await async_engine.dispose()

    asyncio.get_event_loop().run_until_complete(_dispose())
    sync_engine.dispose()
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def client(db_session):
    """Get test client with both sync and async database overrides"""
    from app.core.database import get_db, get_async_db

    def override_get_db():
        db = db_session["sync"]()
        try:
            yield db
        finally:
            db.close()

    async def override_get_async_db():
        async with db_session["async"]() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_async_db] = override_get_async_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _create_user_sync(session_factory, username, password, role, full_name=None, email=None):
    """Helper: create a user directly in the sync DB"""
    db = session_factory()
    try:
        user = User(
            username=username,
            password_hash=get_password_hash(password),
            role=role,
            full_name=full_name or username,
            email=email,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


@pytest.fixture
def admin_user(db_session):
    """Create admin user"""
    from app.core.security import create_access_token

    user = _create_user_sync(
        db_session["sync"], "admin_test", "admin123", UserRole.ADMIN,
        full_name="Test Admin", email="admin@test.com"
    )
    token = create_access_token(
        data={"sub": user.username, "role": user.role.value, "id": user.id}
    )
    return {"user": user, "token": token}


@pytest.fixture
def engineer_user(db_session):
    """Create engineer user"""
    from app.core.security import create_access_token

    user = _create_user_sync(
        db_session["sync"], "engineer_test", "eng123", UserRole.ENGINEER,
        full_name="Test Engineer"
    )
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

    # Refactored: Original code used query parameter for new_password (security issue)
    # Now using request body with JSON per PasswordChange schema
    response = client.put(
        f"/api/users/{user_id}/password",
        json={"new_password": "newpassword"},
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert response.status_code == 200


def test_non_admin_can_change_own_password(client, engineer_user):
    """Test that non-admin user can change their own password"""
    # Refactored: Original code used query parameter for new_password (security issue)
    # Now using request body with JSON per PasswordChange schema
    # Engineer changing their own password should succeed
    response = client.put(
        f"/api/users/{engineer_user['user'].id}/password",
        json={"new_password": "newengpass123"},
        headers={"Authorization": f"Bearer {engineer_user['token']}"}
    )
    assert response.status_code == 200
    # Verify password was changed by checking response contains the user
    assert response.json()["id"] == engineer_user['user'].id


def test_non_admin_cannot_change_other_password(client, engineer_user, admin_user):
    """Test that non-admin user cannot change another user's password"""
    # Refactored: Original code used query parameter for new_password (security issue)
    # Now using request body with JSON per PasswordChange schema
    # Engineer trying to change admin's password should fail with 403
    response = client.put(
        f"/api/users/{admin_user['user'].id}/password",
        json={"new_password": "hacked123"},
        headers={"Authorization": f"Bearer {engineer_user['token']}"}
    )
    assert response.status_code == 403
    # Verify the error message contains expected text
    assert "can only change your own password" in response.json()["detail"].lower()
