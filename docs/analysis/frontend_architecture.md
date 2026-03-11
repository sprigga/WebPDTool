# Frontend Architecture Analysis

## Overview

The WebPDTool frontend is a modern Vue 3 application with Composition API, Element Plus UI components, Pinia state management, and comprehensive routing with authentication guards.

## Project Structure

```
frontend/src/
├── views/           # Page components (10 views)
├── components/      # Reusable components
├── stores/         # Pinia state management (3 stores)
├── api/            # Axios API clients (9 modules)
├── router/         # Vue Router configuration
├── assets/         # Static assets
├── utils/          # Utility functions
└── hooks/          # Custom composables
```

## Main Views Analysis

### 1. TestMain.vue (495 lines)

**Purpose:** Primary test execution interface - the "heart" of the application

**Key Features:**
- PDTool4 UI clone with modern web interface
- Real-time test progress display
- runAllTest mode toggle and status
- Error collection and display
- Session control (start, pause, abort, reset)
- Instrument status monitoring
- Dynamic parameter input forms
- Results summary with pass/fail counts

**Component Structure:**
```vue
<script setup>
// Composition API hooks for test execution
const { testSession, startTest, pauseTest, abortTest } = useTestExecution()
const { instruments } = useInstrumentStatus()
const { currentProject, currentStation } = useProjectSelection()
</script>

<template>
  <div class="test-main-container">
    <!-- Header: Project/Station Selection -->
    <ProjectStationSelector />

    <!-- Control Panel: Start/Pause/Abort/Reset -->
    <TestControlPanel />

    <!-- Test Progress Display -->
    <TestProgressDisplay />

    <!-- Results Summary -->
    <ResultsSummary />

    <!-- Error Display (runAllTest mode) -->
    <ErrorDisplay />
  </div>
</template>
```

### 2. ReportAnalysis.vue (new, 2026-03-10)

**Purpose:** Statistical analysis and visualization of test results

**Key Features:**
- Time range filtering (date from/to)
- Station and test plan selection
- Statistical calculations: mean, median, standard deviation, MAD
- Charts using ECharts library
- Duration analysis (execution_time_ms)
- Session duration analysis
- Export functionality

**Integration:**
- Calls `/api/results/analysis` endpoint
- Uses `analysis.js` API client
- Connects to Pinia `project` store for selection state

### 3. TestPlanManage.vue

**Purpose:** CRUD operations for test plan management

**Key Features:**
- Test plan list with search and pagination
- CSV upload for bulk import
- Individual test item editing
- Enable/disable test items
- Sequence reordering
- Validation rule editing

**Integration:**
- Uses `testplans.js` API client
- CSV upload handled by Element Plus Upload component
- Real-time validation feedback

### 4. UserManage.vue (Admin Only)

**Purpose:** User account management with role-based access control

**Key Features:**
- User list with search and filtering
- Create, edit, delete users
- Password management
- Role assignment (ADMIN, ENGINEER, OPERATOR)
- Status management (active/inactive)

**Access Control:**
- Protected by `authGuard` in router
- Role check via `useAuthStore().user.role`
- Admin-only operations prevent self-deletion

## State Management (Pinia)

### 1. auth.js

**Purpose:** Authentication state management with JWT tokens

**State:**
```javascript
state: {
  token: null,
  user: null,
  isAuthenticated: false,
  loginLoading: false,
  logoutLoading: false
}
```

**Key Actions:**
- `login(credentials)` - Authenticate and store JWT
- `logout()` - Clear authentication state
- `refreshToken()` - Token refresh logic
- `setUser(user)` - Set user information

**Persistence:**
- localStorage for token and user info
- Auto-refresh on page load
- Token validation on API calls

### 2. project.js

**Purpose:** Project and station data management with caching

**State:**
```javascript
state: {
  projects: [],
  stations: [],
  currentProject: null,
  currentStation: null,
  projectLoading: false,
  stationLoading: false
}
```

**Key Features:**
- Automatic project/station loading on app start
- Current selection persistence
- Station filtering by project
- Cached data with auto-refresh

### 3. users.js

**Purpose:** User management state for admin operations

**State:**
```javascript
state: {
  users: [],
  userLoading: false,
  userFormVisible: false,
  editingUser: null
}
```

**Key Actions:**
- `loadUsers()` - Fetch user list with pagination
- `createUser(user)` - Create new user
- `updateUser(id, data)` - Update existing user
- `deleteUser(id)` - Delete user account

## API Layer

### Structure

```javascript
frontend/src/api/
├── client.js          # Axios instance with JWT interceptor
├── auth.js           # Login/logout endpoints
├── projects.js       # Project CRUD operations
├── stations.js       # Station management
├── testplans.js      # Test plan management
├── tests.js          # Test execution control
├── measurements.js   # Measurement type queries
├── testResults.js    # Test result queries
├── users.js          # User management
└── analysis.js       # Statistical analysis data
```

### client.js (Axios Instance)

**Key Features:**
- Base URL configuration (`VITE_API_BASE_URL`)
- JWT Authorization header injection
- Response interceptor for error handling
- Request interceptor for token refresh
- Automatic retry on network errors
- Timeout configuration

```javascript
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// JWT Interceptor
apiClient.interceptors.request.use(
  (config) => {
    const token = authStore.token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response Interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401, 403, 500 errors
    return Promise.reject(error)
  }
)
```

### Error Handling Strategy

**Response Interceptors:**
- 401 Unauthorized: Redirect to login
- 403 Forbidden: Show access denied message
- 500 Server Error: Show server error message
- Network errors: Show retry option

**API Client Patterns:**
- All methods return Promise with standardized error format
- Error messages include user-friendly descriptions
- Automatic retry on transient network errors
- Timeout handling with user feedback

## Router Configuration

### Location
`frontend/src/router/index.js`

### Route Structure

```javascript
const routes = [
  // Public Routes
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false }
  },

  // Protected Routes (require authentication)
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/test/main',
    name: 'TestMain',
    component: () => import('../views/TestMain.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/test/plan',
    name: 'TestPlanManage',
    component: () => import('../views/TestPlanManage.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/test/results',
    name: 'TestResults',
    component: () => import('../views/TestResults.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/test/history',
    name: 'TestHistory',
    component: () => import('../views/TestHistory.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/analysis',
    name: 'ReportAnalysis',
    component: () => import('../views/ReportAnalysis.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/project',
    name: 'ProjectManage',
    component: () => import('../views/ProjectManage.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/user',
    name: 'UserManage',
    component: () => import('../views/UserManage.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/config',
    name: 'SystemConfig',
    component: () => import('../views/SystemConfig.vue'),
    meta: { requiresAuth: true }
  }
]
```

### Navigation Guards

**Authentication Guard:**
```javascript
router.beforeEach((to, from, next) => {
  const requiresAuth = to.meta.requiresAuth
  const isAuthenticated = store.state.auth.isAuthenticated

  if (requiresAuth && !isAuthenticated) {
    next('/login')
  } else if (!requiresAuth && isAuthenticated) {
    next('/')
  } else {
    next()
  }
})
```

**Admin Guard:**
```javascript
router.beforeEach((to, from, next) => {
  const requiresAdmin = to.meta.requiresAdmin
  const isAdmin = store.state.auth.user?.role === 'ADMIN'

  if (requiresAdmin && !isAdmin) {
    next('/')
    // Show access denied message
  } else {
    next()
  }
})
```

## Component Architecture

### Reusable Components

**AppNavBar.vue:**
- Project/station selector dropdown
- User menu with profile and logout
- Navigation links with active state
- Responsive design (mobile menu)

**ProjectStationSelector.vue:**
- Cascading dropdown selection
- Auto-loading of stations based on project
- Selection persistence
- Error handling for invalid selections

**DynamicParamForm.vue:**
- Dynamic form generation based on test parameters
- Validation rule enforcement
- Real-time parameter validation
- Conditional field rendering

### Composition API Usage

**useTestExecution():**
```javascript
export function useTestExecution() {
  const testSession = ref(null)
  const isRunning = ref(false)
  const isPaused = ref(false)

  const startTest = async (params) => {
    // Start test session
  }

  const pauseTest = async () => {
    // Pause test execution
  }

  const abortTest = async () => {
    // Abort test execution
  }

  return { testSession, isRunning, isPaused, startTest, pauseTest, abortTest }
}
```

**useInstrumentStatus():**
```javascript
export function useInstrumentStatus() {
  const instruments = ref([])
  const isLoading = ref(false)

  const loadInstruments = async () => {
    try {
      const response = await apiClient.get('/api/measurements/instruments')
      instruments.value = response.data
    } catch (error) {
      console.error('Failed to load instruments:', error)
    }
  }

  return { instruments, isLoading, loadInstruments }
}
```

## State Management Patterns

### Pinia Store Structure

**Actions:**
- Use async/await for API calls
- Handle loading states with `loading` flags
- Error handling with try/catch blocks
- State updates via `patch()` for partial updates

**Getters:**
- Computed properties for derived state
- Filtering and sorting logic
- Caching of expensive computations

**Modules:**
- Each store is a separate module
- Namespaced for clear organization
- Dependency injection via `inject()` and `provide()`

### State Flow

```
API Response → Store Action → State Update → Component Re-render
   ↓                ↓              ↓              ↓
   Store           Loading        UI             User
   Error           States         State         Interactions
```

## Integration with Backend

### Authentication Flow

```
1. Login.vue → POST /api/auth/login → JWT Token
2. Token stored in localStorage + Pinia store
3. Axios interceptor adds Authorization header
4. Backend validates token via JWT middleware
5. User context injected into requests
```

### Test Execution Flow

```
1. TestMain.vue → useTestExecution() hook
2. startTest() → POST /api/tests/sessions/start
3. TestEngine orchestrates execution (backend)
4. MeasurementService dispatches measurements
5. Results streamed back to frontend via polling
6. UI updates with real-time progress
```

### Data Loading Patterns

**Lazy Loading:**
- Components load data on mount
- Use suspense for loading states
- Cancel pending requests on unmount

**Caching Strategy:**
- Pinia stores cache data
- Auto-refresh with configurable intervals
- Cache invalidation on mutations

**Error Recovery:**
- Retry logic for transient errors
- Fallback data for offline mode
- User-friendly error messages

## UI/UX Considerations

### Responsive Design
- Mobile-first approach
- Breakpoints for different screen sizes
- Touch-friendly interfaces for tablets
- Desktop-optimized layouts for large screens

### Accessibility
- Semantic HTML5 elements
- ARIA labels and roles
- Keyboard navigation support
- Screen reader compatibility

### Performance Optimization
- Virtual scrolling for large lists
- Debounced search and filtering
- Lazy loading of images and components
- Code splitting by route

## Development Workflow

### Component Development
1. Create Composition API function in `hooks/`
2. Build component with `<script setup>`
3. Add to appropriate view or create new view
4. Update router configuration
5. Add to navigation menu

### State Management
1. Define store structure in `stores/`
2. Implement actions and getters
3. Add to main Pinia instance
4. Use in components via `useStore()`

### API Integration
1. Add method to appropriate API client
2. Create store action that calls API
3. Handle loading and error states
4. Update UI based on API response

## Testing Strategy

### Unit Testing
- Vue Test Utils for component testing
- Mock API calls with Jest
- Test store actions and getters
- Test Composition API functions

### Integration Testing
- End-to-end tests with Cypress
- Test complete user workflows
- Verify authentication and authorization
- Test API integration

### Component Testing
- Mount components with mocked dependencies
- Test user interactions and events
- Verify computed properties and watchers
- Test error and loading states

## Key Strengths

1. **Modern Architecture:** Vue 3 Composition API with TypeScript support
2. **Comprehensive State Management:** Pinia stores with clear separation
3. **Robust API Integration:** Axios clients with JWT authentication
4. **Component Reusability:** Well-structured reusable components
5. **Responsive Design:** Mobile-first approach with accessibility
6. **Error Handling:** Comprehensive error handling and user feedback
7. **Performance Optimization:** Code splitting, lazy loading, and caching

## Areas for Improvement

1. **Type Safety:** Could benefit from TypeScript for better type checking
2. **Testing Coverage:** Unit tests for components and stores
3. **Real-time Updates:** WebSocket support for live test progress
4. **Offline Support:** Service worker for offline functionality
5. **Internationalization:** i18n support for multi-language interfaces

This frontend architecture provides a solid foundation for the WebPDTool application with modern web development practices, comprehensive state management, and robust API integration.