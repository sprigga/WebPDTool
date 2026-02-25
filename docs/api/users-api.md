# Users API Documentation

Complete API reference for user management operations in WebPDTool.

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [User Roles](#user-roles)
4. [Endpoints](#endpoints)
   - [Get Users List](#get-users-list)
   - [Get User by ID](#get-user-by-id)
   - [Create User](#create-user)
   - [Update User](#update-user)
   - [Change User Password](#change-user-password)
   - [Delete User](#delete-user)
5. [User Object Schema](#user-object-schema)
6. [Error Responses](#error-responses)

---

## Overview

Base URL: `http://localhost:9100/api/users`

All endpoints require authentication via JWT token. Admin-only endpoints are marked with the lock icon.

---

## Authentication

All requests must include an Authorization header with a valid JWT token:

```
Authorization: Bearer <your-access-token>
```

Tokens are obtained via the `/api/auth/login` endpoint and expire after 8 hours.

---

## User Roles

WebPDTool supports three user roles with different permission levels:

| Role | Description | Permissions |
|------|-------------|--------------|
| `admin` | Administrator | Full access to all features including user management |
| `engineer` | Test Engineer | Create/edit test plans, view and execute tests |
| `operator` | Test Operator | Execute tests only, view results |

Only users with `admin` role can access user management endpoints (create, update, delete users).

---

## Endpoints

### Get Users List

Retrieve a paginated list of users with optional filtering.

**Endpoint:** `GET /api/users`

**Authorization Required:** Yes (any authenticated user)

**Query Parameters:**

| Parameter | Type | Default | Limits | Description |
|-----------|------|---------|--------|-------------|
| `offset` | integer | 0 | ≥ 0 | Number of records to skip (pagination) |
| `limit` | integer | 100 | 1-1000 | Maximum number of records to return |
| `search` | string | - | - | Search across username, full_name, and email fields |
| `role` | string | - | admin/engineer/operator | Filter by user role |
| `is_active` | boolean | - | true/false | Filter by active status |

**Request Example:**

```bash
# Get first 100 users
GET /api/users

# Get users with pagination
GET /api/users?offset=20&limit=50

# Search users by name or email
GET /api/users?search=john

# Filter by role
GET /api/users?role=operator

# Filter by active status
GET /api/users?is_active=true

# Combined filters
GET /api/users?search=john&role=admin&is_active=true&offset=0&limit=10
```

**Response Example:**

```json
[
  {
    "id": 1,
    "username": "admin",
    "full_name": "System Administrator",
    "email": "admin@example.com",
    "role": "admin",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  },
  {
    "id": 2,
    "username": "engineer1",
    "full_name": "John Engineer",
    "email": "john@example.com",
    "role": "engineer",
    "is_active": true,
    "created_at": "2024-01-02T00:00:00",
    "updated_at": "2024-01-02T00:00:00"
  }
]
```

---

### Get User by ID

Retrieve a single user by their ID.

**Endpoint:** `GET /api/users/{user_id}`

**Authorization Required:** Yes (any authenticated user)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | integer | The ID of the user to retrieve |

**Request Example:**

```bash
GET /api/users/1
```

**Response Example:**

```json
{
  "id": 1,
  "username": "admin",
  "full_name": "System Administrator",
  "email": "admin@example.com",
  "role": "admin",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

**Error Responses:**

- `404 Not Found` - User with specified ID does not exist

---

### Create User

Create a new user account. Admin only.

**Endpoint:** `POST /api/users`

**Authorization Required:** Yes (admin only)

**Request Body:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `username` | string | Yes | 3-50 chars, alphanumeric + underscore/dash | Unique username |
| `password` | string | Yes | Minimum 6 characters | User's password |
| `full_name` | string | No | Maximum 100 characters | User's full name |
| `email` | string | No | Valid email format | User's email address |
| `role` | string | Yes | admin/engineer/operator | User's role |
| `is_active` | boolean | No | true/false | Account status (default: true) |

**Request Example:**

```bash
POST /api/users
Content-Type: application/json

{
  "username": "newuser",
  "password": "securepass123",
  "full_name": "New User",
  "email": "newuser@example.com",
  "role": "engineer",
  "is_active": true
}
```

**Response Example:**

```json
{
  "id": 5,
  "username": "newuser",
  "full_name": "New User",
  "email": "newuser@example.com",
  "role": "engineer",
  "is_active": true,
  "created_at": "2024-02-25T10:30:00",
  "updated_at": "2024-02-25T10:30:00"
}
```

**Error Responses:**

- `400 Bad Request` - Username already exists
- `403 Forbidden` - Current user is not an admin

---

### Update User

Update an existing user's information. Admin only.

**Endpoint:** `PUT /api/users/{user_id}`

**Authorization Required:** Yes (admin only)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | integer | The ID of the user to update |

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `full_name` | string | No | User's full name |
| `email` | string | No | User's email address |
| `is_active` | boolean | No | Account active status |

**Note:** `username` and `role` cannot be updated through this endpoint.

**Request Example:**

```bash
PUT /api/users/5
Content-Type: application/json

{
  "full_name": "Updated Name",
  "email": "updated@example.com",
  "is_active": false
}
```

**Response Example:**

```json
{
  "id": 5,
  "username": "newuser",
  "full_name": "Updated Name",
  "email": "updated@example.com",
  "role": "engineer",
  "is_active": false,
  "created_at": "2024-02-25T10:30:00",
  "updated_at": "2024-02-25T11:00:00"
}
```

**Error Responses:**

- `403 Forbidden` - Current user is not an admin
- `404 Not Found` - User with specified ID does not exist

---

### Change User Password

Change a user's password. Admins can change any user's password; users can change their own.

**Endpoint:** `PUT /api/users/{user_id}/password`

**Authorization Required:** Yes (admin or self)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | integer | The ID of the user whose password to change |

**Request Body:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `new_password` | string | Yes | Minimum 6 characters | The new password |

**Request Example:**

```bash
PUT /api/users/5/password
Content-Type: application/json

{
  "new_password": "newsecurepass123"
}
```

**Response Example:**

```json
{
  "id": 5,
  "username": "newuser",
  "full_name": "Updated Name",
  "email": "updated@example.com",
  "role": "engineer",
  "is_active": true,
  "created_at": "2024-02-25T10:30:00",
  "updated_at": "2024-02-25T11:05:00"
}
```

**Error Responses:**

- `403 Forbidden` - Current user is not an admin and not changing their own password
- `404 Not Found` - User with specified ID does not exist

**Security Note:** This endpoint uses a request body instead of query parameters to prevent passwords from being logged in server access logs.

---

### Delete User

Delete a user account. Admin only. Users cannot delete themselves.

**Endpoint:** `DELETE /api/users/{user_id}`

**Authorization Required:** Yes (admin only)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | integer | The ID of the user to delete |

**Request Example:**

```bash
DELETE /api/users/5
```

**Response:**

- Status Code: `204 No Content`
- Body: (empty)

**Error Responses:**

- `400 Bad Request` - Attempting to delete own account
- `403 Forbidden` - Current user is not an admin
- `404 Not Found` - User with specified ID does not exist

---

## User Object Schema

All user-related responses follow this schema:

```typescript
{
  id: number;           // Unique user ID (auto-generated)
  username: string;     // Unique username (3-50 characters)
  full_name: string;    // Full name (up to 100 characters, optional)
  email: string;        // Email address (optional)
  role: string;         // User role: "admin" | "engineer" | "operator"
  is_active: boolean;   // Account active status
  created_at: string;   // ISO 8601 timestamp of account creation
  updated_at: string;   // ISO 8601 timestamp of last update
}
```

---

## Error Responses

All endpoints may return these common error responses:

### 401 Unauthorized

```json
{
  "detail": "Could not validate credentials"
}
```

**Cause:** Missing or invalid JWT token

### 403 Forbidden

```json
{
  "detail": "Not enough permissions"
}
```

**Cause:** User lacks required permissions (e.g., non-admin accessing admin endpoints)

### 422 Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "username"],
      "msg": "ensure this value has at least 3 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

**Cause:** Request body validation failed

---

## Frontend Integration

The frontend provides a convenient API client for all user operations:

```javascript
import {
  getUsers,
  getUser,
  createUser,
  updateUser,
  changeUserPassword,
  deleteUser
} from '@/api/users'

// Get all users
const users = await getUsers(0, 100)

// Get specific user
const user = await getUser(1)

// Create new user
await createUser({
  username: 'newuser',
  password: 'password123',
  full_name: 'New User',
  email: 'new@example.com',
  role: 'engineer',
  is_active: true
})

// Update user
await updateUser(1, {
  full_name: 'Updated Name',
  is_active: false
})

// Change password
await changeUserPassword(1, 'newpassword123')

// Delete user
await deleteUser(1)
```

---

## Related Documentation

- [User Management UI](../features/user-management.md) - Frontend user interface documentation
- [Authentication API](./auth-api.md) - Login and token management
- [Main API Documentation](http://localhost:9100/docs) - Interactive Swagger UI
