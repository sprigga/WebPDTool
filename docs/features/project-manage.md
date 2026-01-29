# Project Management Feature

## Overview

The Project Management page (`/projects`) provides a master-detail interface for managing projects and their associated stations.

## Features

### Project Management (Left Panel)
- View all projects in a table
- Create new projects (admin only)
- Edit existing projects (admin only)
- Delete projects with cascade deletion (admin only)
- Highlight selected project

### Station Management (Right Panel)
- View stations for selected project
- Create new stations (admin only)
- Edit existing stations (admin only)
- Delete stations (admin only)

## Permissions

- **Admin users:** Full CRUD access to projects and stations
- **Non-admin users:** Read-only access

## User Flow

1. Projects load automatically on page mount
2. Select a project from the left panel
3. Stations for that project load in the right panel
4. Use action buttons to create, edit, or delete items
5. Selection persists in localStorage across sessions

## API Endpoints Used

### Projects
- `GET /api/projects` - List all projects
- `POST /api/projects` - Create project
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

### Stations
- `GET /api/projects/{project_id}/stations` - List stations
- `POST /api/stations` - Create station
- `PUT /api/stations/{id}` - Update station
- `DELETE /api/stations/{id}` - Delete station

## Validation

### Project Form
- `project_code`: Required, alphanumeric + underscore/dash, unique
- `project_name`: Required, min 2 chars

### Station Form
- `station_code`: Required, alphanumeric + underscore/dash
- `station_name`: Required, min 2 chars

## Error Handling

- Network errors: "網路連線失敗，請檢查網路狀態後重試"
- Permission errors (403): "權限不足，僅管理員可執行此操作"
- Not found (404): "資料不存在，可能已被刪除"
- Duplicate (400): Shows server error message
- Generic errors: "操作失敗，請稍後重試"

## Responsive Design

- Desktop (>1200px): Side-by-side layout
- Tablet (768-1200px): Narrower panels
- Mobile (<768px): Stacked vertically
