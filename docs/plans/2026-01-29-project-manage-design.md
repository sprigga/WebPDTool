# ProjectManage.vue Design Document

**Date:** 2026-01-29
**Purpose:** Create a master-detail management page for projects and their associated stations

## Overview

A side-by-side layout page that allows administrators to perform full CRUD operations on projects (left panel) and stations (right panel). Non-admin users have read-only access.

## Layout Structure

### Left Panel - Projects Management (35% width)
- **Header:**
  - Title: "專案管理"
  - "新增專案" button (admin only)

- **Projects Table:**
  - Columns: project_code, project_name, enabled status, actions
  - Row selection: Highlights active project with primary color
  - Actions per row: Edit, Delete buttons
  - Stripe pattern with hover effects

### Right Panel - Stations Management (65% width)
- **Header:**
  - Shows selected project info: "{project_code} - {project_name}"
  - "新增站別" button (admin only, disabled when no project selected)

- **Stations Table:**
  - Columns: station_code, station_name, enabled status, actions
  - Actions per row: Edit, Delete buttons
  - Disabled state with placeholder when no project selected
  - Stripe pattern with hover effects

## Data Flow

1. **On Mount:**
   - Load all projects via `projectStore.fetchProjects()`
   - Auto-select first project or restore from localStorage
   - Load stations for selected project

2. **On Project Selection:**
   - Update `selectedProjectId`
   - Save to localStorage
   - Fetch stations via `projectStore.fetchProjectStations(projectId)`
   - Update `projectStore.setCurrentProject()`

3. **CRUD Operations:**
   - All operations check admin role
   - Show loading states during API calls
   - Display success/error messages
   - Refresh relevant table after operation

## Dialog Forms

### Project Create/Edit Dialog

**Title:** "新增專案" / "編輯專案"

**Form Fields:**
- `project_code` (required)
  - Type: text input
  - Max length: 50 chars
  - Pattern: alphanumeric + underscore/dash
  - Unique check on create

- `project_name` (required)
  - Type: text input
  - Max length: 200 chars
  - Min length: 2 chars

- `description` (optional)
  - Type: textarea
  - Max length: 500 chars
  - Rows: 3

- `enabled` (default: true)
  - Type: switch
  - Active text: "啟用"
  - Inactive text: "停用"

**Validation Rules:**
```javascript
{
  project_code: [
    { required: true, message: '請輸入專案代碼', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_-]+$/, message: '只能包含字母、數字、底線和破折號', trigger: 'blur' }
  ],
  project_name: [
    { required: true, message: '請輸入專案名稱', trigger: 'blur' },
    { min: 2, message: '專案名稱至少需要2個字元', trigger: 'blur' }
  ]
}
```

### Station Create/Edit Dialog

**Title:** "新增站別" / "編輯站別"

**Form Fields:**
- `station_code` (required)
  - Type: text input
  - Max length: 50 chars
  - Pattern: alphanumeric + underscore/dash

- `station_name` (required)
  - Type: text input
  - Max length: 200 chars
  - Min length: 2 chars

- `description` (optional)
  - Type: textarea
  - Max length: 500 chars
  - Rows: 3

- `enabled` (default: true)
  - Type: switch
  - Active text: "啟用"
  - Inactive text: "停用"

- `project_id` (hidden)
  - Auto-filled from selected project

**Validation Rules:**
```javascript
{
  station_code: [
    { required: true, message: '請輸入站別代碼', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_-]+$/, message: '只能包含字母、數字、底線和破折號', trigger: 'blur' }
  ],
  station_name: [
    { required: true, message: '請輸入站別名稱', trigger: 'blur' },
    { min: 2, message: '站別名稱至少需要2個字元', trigger: 'blur' }
  ]
}
```

## Delete Operations

### Project Deletion
- **Confirmation Message:** "確定要刪除專案 '{project_name}' 嗎？這將同時刪除所有關聯的站別和測試計劃資料。"
- **Type:** warning (red confirm button)
- **On Confirm:**
  - DELETE /api/projects/{id}
  - Cascade deletes stations (handled by backend)
  - Refresh projects list
  - Auto-select next available project

### Station Deletion
- **Confirmation Message:** "確定要刪除站別 '{station_name}' 嗎？這將同時刪除該站別的所有測試計劃資料。"
- **Type:** warning (red confirm button)
- **On Confirm:**
  - DELETE /api/stations/{id}
  - Refresh stations list for current project

## Error Handling

### Error Messages
- **Network errors:** "網路連線失敗，請檢查網路狀態後重試"
- **403 Forbidden:** "權限不足，僅管理員可執行此操作"
- **404 Not Found:** "資料不存在，可能已被刪除"
- **400 Bad Request (duplicate):** Display server message
- **Generic errors:** Display server detail or "操作失敗，請稍後重試"

### Loading States
- Skeleton loading for projects table on initial load
- Spinner overlay for stations table when switching projects
- Button loading states during operations
- Disabled buttons during operations to prevent double-submission

## State Management

### Component State
```javascript
const selectedProjectId = ref(localStorage.getItem('selectedProjectId') || null)
const loading = reactive({ projects: false, stations: false })
const showProjectDialog = ref(false)
const showStationDialog = ref(false)
const editingProject = reactive({
  id: null,
  project_code: '',
  project_name: '',
  description: '',
  enabled: true
})
const editingStation = reactive({
  id: null,
  station_code: '',
  station_name: '',
  description: '',
  enabled: true,
  project_id: null
})
```

### Computed Properties
```javascript
const isAdmin = computed(() => authStore.currentUser?.role === 'admin')
const canEdit = computed(() => isAdmin.value)
const selectedProject = computed(() =>
  projectStore.projects.find(p => p.id === selectedProjectId.value)
)
const hasSelectedProject = computed(() => !!selectedProjectId.value)
```

### Store Integration
- Use `projectStore` for projects and stations data
- Use `authStore` for current user role
- Sync `selectedProjectId` to localStorage
- Update `projectStore.setCurrentProject()` on selection

## API Endpoints

### Projects (existing)
- GET `/api/projects` - List all projects
- POST `/api/projects` - Create project (admin only)
- PUT `/api/projects/{id}` - Update project (admin only)
- DELETE `/api/projects/{id}` - Delete project (admin only)

### Stations (check if exists, create if needed)
- GET `/api/projects/{project_id}/stations` - List stations by project
- POST `/api/stations` - Create station (admin only)
- PUT `/api/stations/{id}` - Update station (admin only)
- DELETE `/api/stations/{id}` - Delete station (admin only)

## Styling & UX

### Visual Design
- **Container:** Fixed height `calc(100vh - 180px)` with scrolling
- **Panel Gap:** 20px between left and right panels
- **Left Panel:** min-width 400px, max-width 500px
- **Right Panel:** flex-grow to fill remaining space
- **Selected Row:** Light blue background (#ecf5ff)
- **Table Size:** Medium row height, stripe pattern
- **Action Column:** Fixed 160px width

### Empty States
- **No projects:** "尚無專案資料，點擊「新增專案」開始建立"
- **No stations:** "尚無站別資料，點擊「新增站別」為此專案建立站別"
- **No project selected:** "請先在左側選擇一個專案"

### User Feedback
- **Success:** Green toast, 3s duration
- **Error:** Red toast, 5s duration with details
- **Confirmation:** Clear cancel vs confirm button colors
- **Disabled tooltips:** "需要管理員權限" when not admin

### Responsive Behavior
- **Desktop (>1200px):** Side-by-side layout
- **Tablet (768-1200px):** Narrower panels, scrollable tables
- **Mobile (<768px):** Stack vertically (projects top, stations below)

## Accessibility
- Tab navigation through tables and forms
- Enter key submits dialogs
- Escape key closes dialogs
- ARIA labels for screen readers
- Focus management after CRUD operations

## Implementation Notes

1. Check if stations API exists at `/api/stations`, create if needed
2. Reuse Element Plus components from TestPlanManage.vue
3. Follow existing code patterns for consistency
4. Test admin vs non-admin user experiences
5. Ensure proper error boundaries for API failures
6. Add proper TypeScript/JSDoc comments for maintainability
