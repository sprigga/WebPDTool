# User Management UI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a complete user management interface for admins to create, edit, and delete users, extending the existing User model and auth infrastructure with full CRUD operations.

**Architecture:** Backend follows the modular router pattern established in `main.py` with PermissionChecker-based authorization. Frontend mirrors the `ProjectManage.vue` pattern with a single-page table view, Element Plus dialogs for forms, and centralized API client functions.

**Tech Stack:** FastAPI (backend), Vue 3 + Element Plus + Pinia (frontend), bcrypt password hashing, JWT tokens, MySQL database

---

## Task 1: Backend - Create Users API Router

**Files:**
- Create: `backend/app/api/users.py`
- Modify: `backend/app/main.py:130` (register router)
- Test: `backend/tests/test_api/test_users.py`

**Step 1: Write the failing test**

Create test file: `backend/tests/test_api/test_users.py`

```python
"""Tests for users API endpoints"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models.user import User, UserRole

client = TestClient(app)

@pytest.fixture
def admin_token(db_session):
    """Create admin user and return token"""
    from app.core.security import create_access_token
    from app.services import auth as auth_service

    user = auth_service.create_user(db_session, {
        "username": "admin_test",
        "password": "admin123",
        "role": UserRole.ADMIN,
        "full_name": "Test Admin",
        "email": "admin@test.com"
    })

    token = create_access_token(
        data={"sub": user.username, "role": user.role.value, "id": user.id}
    )
    return token

def test_get_users_success(admin_token):
    """Test getting list of users"""
    response = client.get(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_user_success(admin_token):
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
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 201
    assert response.json()["username"] == "testuser"
    assert "password_hash" not in response.json()

def test_create_user_duplicate_username(admin_token):
    """Test creating user with duplicate username fails"""
    user_data = {
        "username": "admin_test",
        "password": "password123",
        "role": "operator"
    }
    response = client.post(
        "/api/users",
        json=user_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400

def test_update_user_success(admin_token, db_session):
    """Test updating user information"""
    # First create a user
    from app.services import auth as auth_service
    user = auth_service.create_user(db_session, {
        "username": "updateme",
        "password": "pass123",
        "role": UserRole.ENGINEER,
        "full_name": "Original Name"
    })

    update_data = {
        "full_name": "Updated Name",
        "email": "updated@example.com"
    }
    response = client.put(
        f"/api/users/{user.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"

def test_delete_user_success(admin_token, db_session):
    """Test deleting a user"""
    from app.services import auth as auth_service
    user = auth_service.create_user(db_session, {
        "username": "deleteme",
        "password": "pass123",
        "role": UserRole.ENGINEER
    })

    response = client.delete(
        f"/api/users/{user.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 204

def test_non_admin_cannot_create_user(engineer_token):
    """Test that non-admin cannot create users"""
    user_data = {
        "username": "shouldnotwork",
        "password": "pass123",
        "role": "operator"
    }
    response = client.post(
        "/api/users",
        json=user_data,
        headers={"Authorization": f"Bearer {engineer_token}"}
    )
    assert response.status_code == 403
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_api/test_users.py -v`
Expected: FAIL with "ImportError" or module not found errors

**Step 3: Write minimal implementation**

Create: `backend/app/api/users.py`

```python
"""Users API endpoints for user management"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.api_helpers import PermissionChecker
from app.core.constants import ErrorMessages
from app.schemas.user import User, UserCreate, UserUpdate, UserInDB
from app.models.user import User as UserModel
from app.services import auth as auth_service
from app.dependencies import get_current_active_user

router = APIRouter()


@router.get("", response_model=List[UserInDB])
async def get_users(
    offset: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get list of all users

    Args:
        offset: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of users (without password_hash)
    """
    users = db.query(UserModel).offset(offset).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=UserInDB)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get user by ID

    Args:
        user_id: User ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        User details
    """
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorMessages.USER_NOT_FOUND if hasattr(ErrorMessages, 'USER_NOT_FOUND') else "User not found"
        )
    return user


@router.post("", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Create new user (Admin only)

    Args:
        user: User creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created user
    """
    PermissionChecker.check_admin(current_user, "create users")

    # Check if username already exists
    existing_user = db.query(UserModel).filter(
        UserModel.username == user.username
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Create user using service layer
    db_user = auth_service.create_user(db, user)

    return db_user


@router.put("/{user_id}", response_model=UserInDB)
async def update_user(
    user_id: int,
    user: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Update user (Admin only)

    Note: Password changes should use a separate change_password endpoint
    for better security practices.

    Args:
        user_id: User ID
        user: User update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated user
    """
    PermissionChecker.check_admin(current_user, "update users")

    # Get existing user
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update fields using model_dump for Pydantic v2
    update_data = user.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)

    return db_user


@router.put("/{user_id}/password", response_model=UserInDB)
async def change_user_password(
    user_id: int,
    new_password: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Change user password (Admin only or self)

    Args:
        user_id: User ID
        new_password: New password
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated user
    """
    # Allow admins or users changing their own password
    if current_user.get("role") != "admin" and current_user.get("id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only change your own password"
        )

    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    from app.core.security import get_password_hash
    db_user.password_hash = get_password_hash(new_password)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Delete user (Admin only)

    Note: Prevents deletion of the current user to avoid self-deletion

    Args:
        user_id: User ID
        db: Database session
        current_user: Current authenticated user
    """
    PermissionChecker.check_admin(current_user, "delete users")

    # Prevent self-deletion
    if current_user.get("id") == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    db.delete(db_user)
    db.commit()

    return None
```

Modify: `backend/app/main.py` (around line 130)

```python
# Add to the import section
from app.api import auth, projects, stations, tests, measurements, dut_control, users

# Add router registration after auth.router
app.include_router(users.router, prefix="/api/users", tags=["Users"])
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_api/test_users.py -v`
Expected: PASS for all tests

**Step 5: Commit**

```bash
git add backend/app/api/users.py backend/app/main.py backend/tests/test_api/test_users.py
git commit -m "feat: add users CRUD API endpoints with admin authorization"
```

---

## Task 2: Backend - Add ErrorMessages Constant

**Files:**
- Modify: `backend/app/core/constants.py`

**Step 1: Add USER_NOT_FOUND constant**

If `ErrorMessages.USER_NOT_FOUND` doesn't exist, add it to the constants file:

```python
class ErrorMessages:
    PROJECT_NOT_FOUND = "Project not found"
    STATION_NOT_FOUND = "Station not found"
    USER_NOT_FOUND = "User not found"  # Add this line
    # ... other messages
```

**Step 2: Commit**

```bash
git add backend/app/core/constants.py
git commit -m "feat: add USER_NOT_FOUND error message constant"
```

---

## Task 3: Frontend - Create Users API Client

**Files:**
- Create: `frontend/src/api/users.js`

**Step 1: Create API client file**

```javascript
import apiClient from './client'

/**
 * Get all users
 * @param {number} offset - Number of records to skip
 * @param {number} limit - Maximum records to return
 * @returns {Promise}
 */
export function getUsers(offset = 0, limit = 100) {
  return apiClient.get('/api/users', {
    params: { offset, limit }
  })
}

/**
 * Get user by ID
 * @param {number} id - User ID
 * @returns {Promise}
 */
export function getUser(id) {
  return apiClient.get(`/api/users/${id}`)
}

/**
 * Create new user
 * @param {Object} data - User data
 * @returns {Promise}
 */
export function createUser(data) {
  return apiClient.post('/api/users', data)
}

/**
 * Update user
 * @param {number} id - User ID
 * @param {Object} data - Updated user data
 * @returns {Promise}
 */
export function updateUser(id, data) {
  return apiClient.put(`/api/users/${id}`, data)
}

/**
 * Change user password
 * @param {number} id - User ID
 * @param {string} newPassword - New password
 * @returns {Promise}
 */
export function changeUserPassword(id, newPassword) {
  return apiClient.put(`/api/users/${id}/password`, null, {
    params: { new_password: newPassword }
  })
}

/**
 * Delete user
 * @param {number} id - User ID
 * @returns {Promise}
 */
export function deleteUser(id) {
  return apiClient.delete(`/api/users/${id}`)
}
```

**Step 2: Commit**

```bash
git add frontend/src/api/users.js
git commit -m "feat: add users API client functions"
```

---

## Task 4: Frontend - Create Users Pinia Store

**Files:**
- Create: `frontend/src/stores/users.js`

**Step 1: Create users store**

```javascript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getUsers, createUser, updateUser, deleteUser } from '@/api/users'

export const useUsersStore = defineStore('users', () => {
  const users = ref([])
  const loading = ref(false)

  async function fetchUsers() {
    loading.value = true
    try {
      const response = await getUsers()
      users.value = response.data || response
    } catch (error) {
      console.error('Failed to fetch users:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function addUser(userData) {
    try {
      const response = await createUser(userData)
      await fetchUsers() // Refresh list
      return response.data || response
    } catch (error) {
      console.error('Failed to create user:', error)
      throw error
    }
  }

  async function modifyUser(userId, userData) {
    try {
      const response = await updateUser(userId, userData)
      await fetchUsers() // Refresh list
      return response.data || response
    } catch (error) {
      console.error('Failed to update user:', error)
      throw error
    }
  }

  async function removeUser(userId) {
    try {
      await deleteUser(userId)
      await fetchUsers() // Refresh list
    } catch (error) {
      console.error('Failed to delete user:', error)
      throw error
    }
  }

  return {
    users,
    loading,
    fetchUsers,
    addUser,
    modifyUser,
    removeUser
  }
})
```

**Step 2: Commit**

```bash
git add frontend/src/stores/users.js
git commit -m "feat: add users Pinia store for state management"
```

---

## Task 5: Frontend - Create UserManagement View

**Files:**
- Create: `frontend/src/views/UserManage.vue`
- Modify: `frontend/src/router/index.js:45-50` (add route)

**Step 1: Create UserManagement component**

```vue
<template>
  <div class="user-manage-container">
    <el-alert
      v-if="!isAdmin"
      title="僅供查看"
      description="您沒有管理員權限，無法新增、編輯或刪除使用者"
      type="info"
      :closable="false"
      style="margin-bottom: 20px"
    />

    <el-card>
      <template #header>
        <div class="card-header">
          <h2>使用者管理</h2>
          <el-button
            v-if="canEdit"
            type="primary"
            :icon="Plus"
            @click="handleAddUser"
          >
            新增使用者
          </el-button>
        </div>
      </template>

      <!-- Users Table -->
      <div v-if="usersStore.users.length === 0 && !loading" class="empty-state">
        <el-empty description="尚無使用者資料，點擊「新增使用者」開始建立" />
      </div>
      <el-table
        v-else
        v-loading="loading"
        :data="usersStore.users"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="username" label="使用者名稱" width="150" />

        <el-table-column prop="full_name" label="全名" min-width="150" />

        <el-table-column prop="email" label="電子郵件" min-width="200" />

        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="getRoleTagType(row.role)" size="small">
              {{ getRoleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="狀態" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '啟用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="建立時間" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-tooltip content="需要管理員權限" :disabled="canEdit">
              <span>
                <el-button
                  size="small"
                  :disabled="!canEdit"
                  @click="handleEditUser(row)"
                >
                  編輯
                </el-button>
              </span>
            </el-tooltip>
            <el-tooltip content="需要管理員權限" :disabled="canEdit">
              <span>
                <el-button
                  size="small"
                  type="warning"
                  :disabled="!canEdit"
                  @click="handleChangePassword(row)"
                >
                  密碼
                </el-button>
              </span>
            </el-tooltip>
            <el-tooltip content="需要管理員權限" :disabled="canEdit">
              <span>
                <el-button
                  size="small"
                  type="danger"
                  :disabled="!canEdit || row.id === currentUserId"
                  @click="handleDeleteUser(row)"
                >
                  刪除
                </el-button>
              </span>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <el-text>共 {{ usersStore.users.length }} 個使用者</el-text>
      </div>
    </el-card>

    <!-- User Create/Edit Dialog -->
    <el-dialog
      v-model="showUserDialog"
      :title="editingUser.id ? '編輯使用者' : '新增使用者'"
      width="600px"
    >
      <el-form
        ref="userFormRef"
        :model="editingUser"
        :rules="userFormRules"
        label-width="120px"
      >
        <el-form-item label="使用者名稱" prop="username">
          <el-input
            v-model="editingUser.username"
            placeholder="請輸入使用者名稱"
            :disabled="!!editingUser.id"
          />
        </el-form-item>

        <el-form-item v-if="!editingUser.id" label="密碼" prop="password">
          <el-input
            v-model="editingUser.password"
            type="password"
            placeholder="請輸入密碼"
            show-password
          />
        </el-form-item>

        <el-form-item label="全名" prop="full_name">
          <el-input
            v-model="editingUser.full_name"
            placeholder="請輸入全名"
          />
        </el-form-item>

        <el-form-item label="電子郵件" prop="email">
          <el-input
            v-model="editingUser.email"
            type="email"
            placeholder="請輸入電子郵件"
          />
        </el-form-item>

        <el-form-item label="角色" prop="role">
          <el-select
            v-model="editingUser.role"
            placeholder="請選擇角色"
            style="width: 100%"
          >
            <el-option label="工程師" value="engineer" />
            <el-option label="操作員" value="operator" />
            <el-option label="管理員" value="admin" />
          </el-select>
        </el-form-item>

        <el-form-item v-if="editingUser.id" label="狀態">
          <el-switch
            v-model="editingUser.is_active"
            active-text="啟用"
            inactive-text="停用"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showUserDialog = false">取消</el-button>
        <el-button
          type="primary"
          :loading="savingUser"
          @click="handleSaveUser"
        >
          儲存
        </el-button>
      </template>
    </el-dialog>

    <!-- Change Password Dialog -->
    <el-dialog
      v-model="showPasswordDialog"
      title="變更密碼"
      width="500px"
    >
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordFormRules"
        label-width="100px"
      >
        <el-form-item label="使用者">
          <el-text>{{ changingPasswordUser?.username }}</el-text>
        </el-form-item>

        <el-form-item label="新密碼" prop="newPassword">
          <el-input
            v-model="passwordForm.newPassword"
            type="password"
            placeholder="請輸入新密碼"
            show-password
          />
        </el-form-item>

        <el-form-item label="確認密碼" prop="confirmPassword">
          <el-input
            v-model="passwordForm.confirmPassword"
            type="password"
            placeholder="請再次輸入新密碼"
            show-password
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showPasswordDialog = false">取消</el-button>
        <el-button
          type="primary"
          :loading="changingPassword"
          @click="handleSavePassword"
        >
          變更
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUsersStore } from '@/stores/users'
import { useAuthStore } from '@/stores/auth'
import { createUser, updateUser, changeUserPassword, deleteUser } from '@/api/users'

const usersStore = useUsersStore()
const authStore = useAuthStore()

// State
const loading = ref(false)
const currentUserId = computed(() => authStore.user?.id)

// Dialog state
const showUserDialog = ref(false)
const savingUser = ref(false)
const userFormRef = ref(null)

// Form data
const editingUser = reactive({
  id: null,
  username: '',
  password: '',
  full_name: '',
  email: '',
  role: 'operator',
  is_active: true
})

// Form rules
const userFormRules = {
  username: [
    { required: true, message: '請輸入使用者名稱', trigger: 'blur' },
    { min: 3, max: 50, message: '使用者名稱長度需在 3 到 50 個字元之間', trigger: 'blur' },
    {
      pattern: /^[a-zA-Z0-9_-]+$/,
      message: '只能包含字母、數字、底線和破折號',
      trigger: 'blur'
    }
  ],
  password: [
    { required: true, message: '請輸入密碼', trigger: 'blur' },
    { min: 6, message: '密碼至少需要 6 個字元', trigger: 'blur' }
  ],
  full_name: [
    { max: 100, message: '全名最多 100 個字元', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '請輸入有效的電子郵件地址', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '請選擇角色', trigger: 'change' }
  ]
}

// Password dialog state
const showPasswordDialog = ref(false)
const changingPassword = ref(false)
const passwordFormRef = ref(null)
const changingPasswordUser = ref(null)

const passwordForm = reactive({
  newPassword: '',
  confirmPassword: ''
})

const passwordFormRules = {
  newPassword: [
    { required: true, message: '請輸入新密碼', trigger: 'blur' },
    { min: 6, message: '密碼至少需要 6 個字元', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '請再次輸入新密碼', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('兩次輸入的密碼不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// Computed
const isAdmin = computed(() => authStore.user?.role === 'admin')
const canEdit = computed(() => isAdmin.value)

// Helper functions
const getRoleLabel = (role) => {
  const roleMap = {
    admin: '管理員',
    engineer: '工程師',
    operator: '操作員'
  }
  return roleMap[role] || role
}

const getRoleTagType = (role) => {
  const typeMap = {
    admin: 'danger',
    engineer: 'warning',
    operator: 'info'
  }
  return typeMap[role] || 'info'
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Handlers
const handleAddUser = () => {
  Object.assign(editingUser, {
    id: null,
    username: '',
    password: '',
    full_name: '',
    email: '',
    role: 'operator',
    is_active: true
  })
  showUserDialog.value = true
}

const handleEditUser = (row) => {
  Object.assign(editingUser, {
    id: row.id,
    username: row.username,
    password: '', // Don't populate password for security
    full_name: row.full_name || '',
    email: row.email || '',
    role: row.role,
    is_active: row.is_active
  })
  showUserDialog.value = true
}

const handleDeleteUser = async (row) => {
  try {
    await ElMessageBox.confirm(
      `確定要刪除使用者 "${row.username}" 嗎？此操作無法復原。`,
      '確認刪除',
      {
        confirmButtonText: '確定',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )

    loading.value = true
    await deleteUser(row.id)
    ElMessage.success('使用者刪除成功')
    await usersStore.fetchUsers()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete user failed:', error)
      const message = error.response?.data?.detail || '刪除失敗'
      ElMessage.error(message)
    }
  } finally {
    loading.value = false
  }
}

const handleSaveUser = async () => {
  if (!userFormRef.value) return

  await userFormRef.value.validate(async (valid) => {
    if (!valid) return

    savingUser.value = true
    try {
      const userData = {
        username: editingUser.username,
        full_name: editingUser.full_name || null,
        email: editingUser.email || null,
        role: editingUser.role
      }

      if (editingUser.id) {
        // Update existing user
        userData.is_active = editingUser.is_active
        await updateUser(editingUser.id, userData)
        ElMessage.success('使用者更新成功')
      } else {
        // Create new user
        userData.password = editingUser.password
        await createUser(userData)
        ElMessage.success('使用者建立成功')
      }

      showUserDialog.value = false
      loading.value = true
      await usersStore.fetchUsers()
      loading.value = false
    } catch (error) {
      console.error('Save user failed:', error)
      const message = error.response?.data?.detail || '操作失敗'
      ElMessage.error(message)
    } finally {
      savingUser.value = false
    }
  })
}

const handleChangePassword = (row) => {
  changingPasswordUser.value = row
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
  showPasswordDialog.value = true
}

const handleSavePassword = async () => {
  if (!passwordFormRef.value) return

  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return

    changingPassword.value = true
    try {
      await changeUserPassword(changingPasswordUser.value.id, passwordForm.newPassword)
      ElMessage.success('密碼變更成功')
      showPasswordDialog.value = false
    } catch (error) {
      console.error('Change password failed:', error)
      const message = error.response?.data?.detail || '密碼變更失敗'
      ElMessage.error(message)
    } finally {
      changingPassword.value = false
    }
  })
}

onMounted(async () => {
  loading.value = true
  try {
    await usersStore.fetchUsers()
  } catch (error) {
    console.error('Failed to load users:', error)
    ElMessage.error('載入使用者列表失敗')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.user-manage-container {
  padding: 20px;
  height: calc(100vh - 180px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  font-size: 20px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.table-footer {
  margin-top: 16px;
  text-align: right;
}

:deep(.el-table .el-button + .el-button) {
  margin-left: 4px;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .user-manage-container {
    padding: 10px;
  }

  :deep(.el-table .el-button) {
    margin-bottom: 4px;
  }
}
</style>
```

**Step 2: Add router configuration**

Modify: `frontend/src/router/index.js` (add after the `/projects` route)

```javascript
  {
    path: '/users',
    name: 'UserManage',
    component: () => import('@/views/UserManage.vue'),
    meta: { requiresAuth: true }
  }
```

**Step 3: Commit**

```bash
git add frontend/src/views/UserManage.vue frontend/src/router/index.js
git commit -m "feat: add user management view with CRUD operations"
```

---

## Task 6: Frontend - Add Navigation Menu Item

**Files:**
- Modify: Find the navigation component (likely in TestMain.vue or a shared navigation component)

**Step 1: Identify and update navigation**

The navigation appears to be within individual views. Add a link or button to access `/users` route. Based on the codebase structure, you may want to add it to the main navigation or create a settings menu entry.

First, check where the navigation menu is defined:

Run: `grep -r "專案管理\|项目管理" frontend/src/`

If navigation is in each view, add a menu item. For now, document that users can access via `/users` URL directly.

**Step 2: Commit** (if navigation file is modified)

```bash
git add frontend/src/views/[navigation-file].vue
git commit -m "feat: add user management link to navigation menu"
```

---

## Task 7: Backend - Add Pagination and Filtering Support

**Files:**
- Modify: `backend/app/api/users.py`

**Step 1: Enhance GET /users endpoint with search and filter**

```python
from sqlalchemy import or_

@router.get("", response_model=List[UserInDB])
async def get_users(
    offset: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get list of all users with optional filtering

    Args:
        offset: Number of records to skip (pagination)
        limit: Maximum number of records to return
        search: Search in username, full_name, or email
        role: Filter by user role
        is_active: Filter by active status
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of users
    """
    query = db.query(UserModel)

    # Apply search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                UserModel.username.like(search_pattern),
                UserModel.full_name.like(search_pattern),
                UserModel.email.like(search_pattern)
            )
        )

    # Apply role filter
    if role:
        query = query.filter(UserModel.role == role)

    # Apply active status filter
    if is_active is not None:
        query = query.filter(UserModel.is_active == is_active)

    # Order by username
    query = query.order_by(UserModel.username)

    users = query.offset(offset).limit(limit).all()
    return users
```

**Step 2: Commit**

```bash
git add backend/app/api/users.py
git commit -m "feat: add search and filtering to users API"
```

---

## Task 8: Integration Testing

**Files:**
- Create: `backend/tests/integration/test_user_management_flow.py`

**Step 1: Create integration test**

```python
"""Integration test for complete user management workflow"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models.user import User, UserRole

client = TestClient(app)

def test_complete_user_management_workflow(db_session):
    """Test the full user management flow"""
    # 1. Create admin user
    from app.core.security import create_access_token
    from app.services import auth as auth_service

    admin = auth_service.create_user(db_session, {
        "username": "admin_workflow",
        "password": "admin123",
        "role": UserRole.ADMIN,
        "full_name": "Workflow Admin"
    })

    admin_token = create_access_token(
        data={"sub": admin.username, "role": admin.role.value, "id": admin.id}
    )

    headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. List users (should only have admin)
    response = client.get("/api/users", headers=headers)
    assert response.status_code == 200
    users = response.json()
    assert len(users) == 1
    assert users[0]["username"] == "admin_workflow"

    # 3. Create engineer user
    engineer_data = {
        "username": "engineer1",
        "password": "pass123",
        "role": "engineer",
        "full_name": "Engineer One",
        "email": "engineer1@test.com"
    }
    response = client.post("/api/users", json=engineer_data, headers=headers)
    assert response.status_code == 201
    engineer_id = response.json()["id"]

    # 4. Verify engineer appears in list
    response = client.get("/api/users", headers=headers)
    assert response.status_code == 200
    users = response.json()
    assert len(users) == 2

    # 5. Update engineer
    update_data = {"full_name": "Senior Engineer", "email": "senior@test.com"}
    response = client.put(f"/api/users/{engineer_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["full_name"] == "Senior Engineer"

    # 6. Change engineer password
    response = client.put(
        f"/api/users/{engineer_id}/password",
        params={"new_password": "newpass123"},
        headers=headers
    )
    assert response.status_code == 200

    # 7. Verify engineer can login with new password
    login_response = client.post("/api/auth/login", json={
        "username": "engineer1",
        "password": "newpass123"
    })
    assert login_response.status_code == 200

    # 8. Test that engineer cannot create users
    engineer_token = login_response.json()["access_token"]
    engineer_headers = {"Authorization": f"Bearer {engineer_token}"}

    response = client.post(
        "/api/users",
        json={"username": "shouldfail", "password": "pass123", "role": "operator"},
        headers=engineer_headers
    )
    assert response.status_code == 403

    # 9. Delete engineer
    response = client.delete(f"/api/users/{engineer_id}", headers=headers)
    assert response.status_code == 204

    # 10. Verify deletion
    response = client.get(f"/api/users/{engineer_id}", headers=headers)
    assert response.status_code == 404
```

**Step 2: Run integration test**

Run: `uv run pytest tests/integration/test_user_management_flow.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add backend/tests/integration/test_user_management_flow.py
git commit -m "test: add user management integration test"
```

---

## Task 9: Documentation Updates

**Files:**
- Modify: `CLAUDE.md` (add user management section)
- Create: `docs/api/users-api.md` (API documentation)

**Step 1: Update CLAUDE.md**

Add to the "Common Development Tasks" section:

```markdown
### Managing Users

The user management system is located at:

- **Backend:** `backend/app/api/users.py` - User CRUD endpoints
- **Frontend:** `frontend/src/views/UserManage.vue` - User management UI
- **Store:** `frontend/src/stores/users.js` - Pinia state management
- **API Client:** `frontend/src/api/users.js` - API functions

**User Roles:**
- `admin` - Full access including user management
- `engineer` - Can manage test plans and projects
- `operator` - Can only execute tests

**API Endpoints:**
- `GET /api/users` - List all users (admin only)
- `GET /api/users/{id}` - Get user by ID
- `POST /api/users` - Create new user (admin only)
- `PUT /api/users/{id}` - Update user (admin only)
- `PUT /api/users/{id}/password` - Change password (admin or self)
- `DELETE /api/users/{id}` - Delete user (admin only)
```

**Step 2: Create API documentation**

Create: `docs/api/users-api.md`

```markdown
# Users API Documentation

## Endpoints

### GET /api/users
List all users with optional filtering.

**Query Parameters:**
- `offset` (integer, default: 0) - Number of records to skip
- `limit` (integer, default: 100) - Maximum records to return
- `search` (string, optional) - Search in username, full_name, or email
- `role` (string, optional) - Filter by role (admin/engineer/operator)
- `is_active` (boolean, optional) - Filter by active status

**Response:** Array of User objects

**Authorization Required:** Yes (any authenticated user)

### POST /api/users
Create a new user.

**Request Body:**
```json
{
  "username": "string (3-50 chars)",
  "password": "string (min 6 chars)",
  "role": "admin|engineer|operator",
  "full_name": "string (optional, max 100 chars)",
  "email": "email (optional)"
}
```

**Response:** Created User object

**Authorization Required:** Yes (admin only)

### PUT /api/users/{id}
Update user information.

**Request Body:**
```json
{
  "full_name": "string (optional)",
  "email": "email (optional)",
  "is_active": "boolean (optional)"
}
```

**Response:** Updated User object

**Authorization Required:** Yes (admin only)

### PUT /api/users/{id}/password
Change user password.

**Query Parameters:**
- `new_password` (string, required) - New password (min 6 chars)

**Response:** Updated User object

**Authorization Required:** Yes (admin or user themselves)

### DELETE /api/users/{id}
Delete a user.

**Response:** 204 No Content

**Authorization Required:** Yes (admin only, cannot delete self)

## User Object

```json
{
  "id": 1,
  "username": "string",
  "full_name": "string",
  "email": "string",
  "role": "admin|engineer|operator",
  "is_active": true,
  "created_at": "ISO 8601 datetime",
  "updated_at": "ISO 8601 datetime"
}
```
```

**Step 3: Commit**

```bash
git add CLAUDE.md docs/api/users-api.md
git commit -m "docs: add user management documentation"
```

---

## Summary

This plan implements a complete user management system with:

1. **Backend:** Full CRUD API with admin authorization
2. **Frontend:** Vue 3 + Element Plus UI following ProjectManage.vue patterns
3. **State Management:** Pinia store for user data
4. **Security:** Admin-only operations, password change endpoint
5. **Testing:** Unit and integration tests
6. **Documentation:** API docs and usage guide

**Total Tasks:** 9
**Estimated Complexity:** Medium
**Key Patterns:** Follows existing ProjectManage.vue and projects API patterns

---

**Implementation Notes:**
- All password hashing uses bcrypt via `app.core.security`
- User validation matches Pydantic schema constraints
- Frontend uses Element Plus components consistent with existing UI
- Permission checks use `PermissionChecker.check_admin()` helper
- Pagination follows the offset/limit pattern used in projects API
