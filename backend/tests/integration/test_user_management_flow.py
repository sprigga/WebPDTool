"""Integration tests for complete user management workflow

This test file validates the end-to-end user management flow, simulating
real-world usage scenarios where an admin user performs a series of operations
to manage users in the system.
"""
import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.models.user import User, UserRole
from app.core.database import Base
from app.core.constants import ErrorMessages


# Refactored: Fixtures moved inline to avoid conftest.py dependency
# Original code assumed fixtures were in conftest.py
@pytest.fixture(scope="function")
def db_session():
    """Get database session with fresh schema for each test"""
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
        except FileNotFoundError:
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


def test_complete_user_management_flow(client, db_session):
    """
    Integration test: Complete user management workflow

    This test simulates a real-world scenario where:
    1. An admin user is created and logs in
    2. The admin lists all users (should only have themselves)
    3. The admin creates an engineer user
    4. The admin verifies the engineer appears in the user list
    5. The admin updates the engineer's information
    6. The admin changes the engineer's password
    7. The engineer logs in with the new password
    8. The engineer verifies they cannot create users (403 Forbidden)
    9. The admin deletes the engineer
    10. The admin verifies the engineer is removed from the system
    """
    # ============================================================
    # STEP 1: Create admin user and log in
    # ============================================================
    admin_data = {
        "username": "admin_flow",
        "password": "admin123",
        "role": UserRole.ADMIN,  # FIXED: Use UserRole enum instead of string literal
        "full_name": "Flow Admin",
        "email": "admin@flowexample.com"
    }

    # Create admin directly in DB (bypassing API since no admin exists yet)
    from app.services import auth as auth_service
    from app.schemas.user import UserCreate

    admin_create = UserCreate(**admin_data)
    admin_user = auth_service.create_user(db_session, admin_create)

    # Login as admin
    login_response = client.post(
        "/api/auth/login",
        json={"username": admin_data["username"], "password": admin_data["password"]}
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    admin_token = login_data["access_token"]
    assert "user" in login_data
    assert login_data["user"]["username"] == admin_data["username"]

    # ============================================================
    # STEP 2: List users (should only have admin)
    # ============================================================
    list_response = client.get(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert list_response.status_code == 200
    users = list_response.json()
    assert len(users) == 1
    assert users[0]["username"] == admin_data["username"]
    assert users[0]["role"] == "admin"

    # ============================================================
    # STEP 3: Create engineer user
    # ============================================================
    engineer_data = {
        "username": "engineer_flow",
        "password": "eng123",
        "role": UserRole.ENGINEER,  # FIXED: Use UserRole enum instead of string literal
        "full_name": "Flow Engineer",
        "email": "engineer@flowexample.com"
    }

    create_response = client.post(
        "/api/users",
        json=engineer_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert create_response.status_code == 201
    created_engineer = create_response.json()
    engineer_id = created_engineer["id"]
    assert created_engineer["username"] == engineer_data["username"]
    assert created_engineer["role"] == "engineer"
    assert created_engineer["full_name"] == engineer_data["full_name"]
    assert "password_hash" not in created_engineer  # Password should not be exposed

    # ============================================================
    # STEP 4: Verify engineer appears in user list
    # ============================================================
    list_response = client.get(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert list_response.status_code == 200
    users = list_response.json()
    assert len(users) == 2
    usernames = [u["username"] for u in users]
    assert admin_data["username"] in usernames
    assert engineer_data["username"] in usernames

    # ============================================================
    # STEP 5: Update engineer information
    # ============================================================
    update_data = {
        "full_name": "Updated Flow Engineer",
        "email": "updated@flowexample.com",
        "is_active": True
    }

    update_response = client.put(
        f"/api/users/{engineer_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert update_response.status_code == 200
    updated_engineer = update_response.json()
    assert updated_engineer["full_name"] == update_data["full_name"]
    assert updated_engineer["email"] == update_data["email"]
    assert updated_engineer["username"] == engineer_data["username"]  # Unchanged

    # ============================================================
    # STEP 6: Change engineer password
    # ============================================================
    new_password = "newengpass456"
    password_response = client.put(
        f"/api/users/{engineer_id}/password",
        json={"new_password": new_password},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert password_response.status_code == 200

    # ============================================================
    # STEP 7: Verify engineer can login with new password
    # ============================================================
    engineer_login_response = client.post(
        "/api/auth/login",
        json={"username": engineer_data["username"], "password": new_password}
    )
    assert engineer_login_response.status_code == 200
    engineer_token = engineer_login_response.json()["access_token"]

    # Verify old password no longer works
    old_login_response = client.post(
        "/api/auth/login",
        json={"username": engineer_data["username"], "password": engineer_data["password"]}
    )
    assert old_login_response.status_code == 401

    # ============================================================
    # STEP 8: Verify engineer cannot create users (403 Forbidden)
    # ============================================================
    operator_data = {
        "username": "operator_flow",
        "password": "operator123",
        "role": UserRole.OPERATOR,  # FIXED: Use UserRole enum instead of string literal
        "full_name": "Should Not Be Created"
    }

    forbidden_response = client.post(
        "/api/users",
        json=operator_data,
        headers={"Authorization": f"Bearer {engineer_token}"}
    )
    assert forbidden_response.status_code == 403
    # FIXED: Verify the error message indicates permission is denied
    # PermissionChecker generates: "Only admin can create users"
    detail = forbidden_response.json()["detail"]
    assert "admin" in detail.lower() and "can create users" in detail.lower()

    # ============================================================
    # STEP 9: Admin deletes engineer
    # ============================================================
    delete_response = client.delete(
        f"/api/users/{engineer_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert delete_response.status_code == 204

    # ============================================================
    # STEP 10: Verify engineer is removed from the system
    # ============================================================
    # Verify engineer no longer appears in list
    list_response = client.get(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert list_response.status_code == 200
    users = list_response.json()
    assert len(users) == 1
    assert users[0]["username"] == admin_data["username"]

    # Verify engineer cannot be fetched by ID
    get_response = client.get(
        f"/api/users/{engineer_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert get_response.status_code == 404

    # Verify engineer cannot login anymore
    engineer_login_after_delete = client.post(
        "/api/auth/login",
        json={"username": engineer_data["username"], "password": new_password}
    )
    assert engineer_login_after_delete.status_code == 401


def test_admin_self_password_change_flow(client, db_session):
    """
    Integration test: Admin changing their own password

    Tests that an admin can:
    1. Login
    2. Change their own password
    3. Login with the new password
    4. Not login with the old password
    """
    # ============================================================
    # Create and login admin
    # ============================================================
    from app.services import auth as auth_service
    from app.schemas.user import UserCreate

    admin_data = UserCreate(
        username="admin_self",
        password="oldpass123",
        role=UserRole.ADMIN,
        full_name="Self Admin"
    )
    admin_user = auth_service.create_user(db_session, admin_data)

    login_response = client.post(
        "/api/auth/login",
        json={"username": "admin_self", "password": "oldpass123"}
    )
    assert login_response.status_code == 200
    admin_token = login_response.json()["access_token"]

    # ============================================================
    # Change own password
    # ============================================================
    new_password = "newpass456"
    password_response = client.put(
        f"/api/users/{admin_user.id}/password",
        json={"new_password": new_password},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert password_response.status_code == 200

    # ============================================================
    # Verify new password works
    # ============================================================
    new_login_response = client.post(
        "/api/auth/login",
        json={"username": "admin_self", "password": new_password}
    )
    assert new_login_response.status_code == 200

    # ============================================================
    # Verify old password no longer works
    # ============================================================
    old_login_response = client.post(
        "/api/auth/login",
        json={"username": "admin_self", "password": "oldpass123"}
    )
    assert old_login_response.status_code == 401


def test_operator_self_update_flow(client, db_session):
    """
    Integration test: Operator cannot update their own profile

    Tests that a non-admin user:
    1. Can login
    2. Cannot update their own profile (requires admin role)
    3. Can change their own password
    """
    # ============================================================
    # Create admin and operator
    # ============================================================
    from app.services import auth as auth_service
    from app.schemas.user import UserCreate

    admin_data = UserCreate(
        username="admin_op_test",
        password="admin123",
        role=UserRole.ADMIN,
        full_name="Test Admin"
    )
    auth_service.create_user(db_session, admin_data)

    operator_data = UserCreate(
        username="operator_self",
        password="operator123",
        role=UserRole.OPERATOR,
        full_name="Original Name",
        email="original@example.com"
    )
    operator_user = auth_service.create_user(db_session, operator_data)

    # Login as operator
    login_response = client.post(
        "/api/auth/login",
        json={"username": "operator_self", "password": "operator123"}
    )
    assert login_response.status_code == 200
    operator_token = login_response.json()["access_token"]

    # ============================================================
    # Verify operator cannot update their own profile (admin only)
    # ============================================================
    update_data = {
        "full_name": "Updated Name",
        "email": "updated@test.com"
    }
    update_response = client.put(
        f"/api/users/{operator_user.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {operator_token}"}
    )
    assert update_response.status_code == 403

    # ============================================================
    # Verify operator CAN change their own password
    # ============================================================
    password_response = client.put(
        f"/api/users/{operator_user.id}/password",
        json={"new_password": "newoperator123"},
        headers={"Authorization": f"Bearer {operator_token}"}
    )
    assert password_response.status_code == 200

    # Verify password was changed by logging in with new password
    new_login_response = client.post(
        "/api/auth/login",
        json={"username": "operator_self", "password": "newoperator123"}
    )
    assert new_login_response.status_code == 200


def test_user_not_found_after_deletion_flow(client, db_session):
    """
    Integration test: Verify cascading behavior after user deletion

    Tests that after deleting a user:
    1. The user no longer appears in the user list
    2. The user cannot be fetched by ID
    3. The user cannot login
    """
    # ============================================================
    # Create admin and test user
    # ============================================================
    from app.services import auth as auth_service
    from app.schemas.user import UserCreate

    admin_data = UserCreate(
        username="admin_del_test",
        password="admin123",
        role=UserRole.ADMIN,
        full_name="Delete Test Admin"
    )
    auth_service.create_user(db_session, admin_data)

    test_user_data = UserCreate(
        username="delete_test_user",
        password="test123",
        role=UserRole.ENGINEER,
        full_name="To Be Deleted"
    )
    test_user = auth_service.create_user(db_session, test_user_data)

    # Login as admin
    login_response = client.post(
        "/api/auth/login",
        json={"username": "admin_del_test", "password": "admin123"}
    )
    assert login_response.status_code == 200
    admin_token = login_response.json()["access_token"]

    # Verify user exists
    get_response = client.get(
        f"/api/users/{test_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert get_response.status_code == 200
    assert get_response.json()["username"] == "delete_test_user"

    # Delete user
    delete_response = client.delete(
        f"/api/users/{test_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert delete_response.status_code == 204

    # Verify not found by ID
    get_response = client.get(
        f"/api/users/{test_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert get_response.status_code == 404

    # Verify cannot login
    login_after_delete = client.post(
        "/api/auth/login",
        json={"username": "delete_test_user", "password": "test123"}
    )
    assert login_after_delete.status_code == 401
