# Test Results View Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a test results query and display interface that allows users to filter test results by project, station, test plan, and serial number, with clear presentation of test sessions and their individual test item results.

**Architecture:**
- Frontend: Vue 3 Composition API with Element Plus UI components, following existing patterns from TestPlanManage.vue and UserManage.vue
- Backend: Use existing API endpoints (`GET /api/tests/sessions`, `GET /api/tests/sessions/{id}/results`) with added filtering support
- Data Flow: Filter selections → API call with query parameters → Paginated results display with expandable session details

**Tech Stack:** Vue 3, Element Plus, Pinia, Axios, FastAPI (backend), SQLAlchemy 2.0

---

## Backend API Enhancements

### Task 1: Add Test Results Query Endpoint with Filtering

**Files:**
- Modify: `backend/app/api/tests.py:560-603` (extend list_test_sessions endpoint)
- Create: `backend/app/schemas/test_result_query.py`

**Step 1: Write the failing test**

Create test file `backend/tests/api/test/test_results_query.py`:

```python
"""Test Results Query API Tests"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta


def test_list_sessions_with_project_filter(client: TestClient, test_data):
    """Test filtering sessions by project_id"""
    # Given: A project with ID 1 has multiple test sessions
    project_id = 1

    # When: Query sessions with project filter
    response = client.get(
        "/api/tests/sessions",
        params={"project_id": project_id, "limit": 10}
    )

    # Then: Return only sessions belonging to the project
    assert response.status_code == 200
    sessions = response.json()
    assert all(s["station"]["project_id"] == project_id for s in sessions)


def test_list_sessions_with_date_range_filter(client: TestClient, test_data):
    """Test filtering sessions by date range"""
    # Given: Sessions exist in the database
    start_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
    end_date = datetime.utcnow().isoformat()

    # When: Query sessions with date range
    response = client.get(
        "/api/tests/sessions",
        params={
            "start_date": start_date,
            "end_date": end_date,
            "limit": 10
        }
    )

    # Then: Return sessions within date range
    assert response.status_code == 200
    sessions = response.json()
    # Verify all sessions are within range


def test_list_sessions_with_result_filter(client: TestClient, test_data):
    """Test filtering sessions by final_result (PASS/FAIL/ABORT)"""
    # Given: Sessions with different results exist
    final_result = "PASS"

    # When: Query sessions filtered by result
    response = client.get(
        "/api/tests/sessions",
        params={"final_result": final_result, "limit": 10}
    )

    # Then: Return only sessions with that result
    assert response.status_code == 200
    sessions = response.json()
    assert all(s["final_result"] == final_result for s in sessions if s["final_result"] is not None)


def test_list_sessions_with_serial_search(client: TestClient, test_data):
    """Test searching sessions by serial_number (partial match)"""
    # Given: Sessions with specific serial numbers exist
    serial_partial = "SN123"

    # When: Query sessions with serial search
    response = client.get(
        "/api/tests/sessions",
        params={"serial_number": serial_partial, "limit": 10}
    )

    # Then: Return sessions with matching serial numbers
    assert response.status_code == 200
    sessions = response.json()
    assert all(serial_partial in s["serial_number"] for s in sessions)


def test_list_sessions_pagination(client: TestClient, test_data):
    """Test pagination with offset and limit"""
    # Given: More than 10 sessions exist
    limit = 10

    # When: Query first page
    response_page1 = client.get(
        "/api/tests/sessions",
        params={"limit": limit, "offset": 0}
    )

    # When: Query second page
    response_page2 = client.get(
        "/api/tests/sessions",
        params={"limit": limit, "offset": limit}
    )

    # Then: Return different sessions for each page
    assert response_page1.status_code == 200
    assert response_page2.status_code == 200
    page1_ids = {s["id"] for s in response_page1.json()}
    page2_ids = {s["id"] for s in response_page2.json()}
    assert len(page1_ids.intersection(page2_ids)) == 0  # No overlap


def test_get_session_with_station_and_project_details(client: TestClient, test_data):
    """Test that session details include station and project information"""
    # Given: A session ID exists
    session_id = 1

    # When: Get session details
    response = client.get(f"/api/tests/sessions/{session_id}")

    # Then: Include nested station and project data
    assert response.status_code == 200
    session = response.json()
    assert "station" in session
    assert "project" in session.get("station", {})
    assert session["station"]["project"]["id"] is not None
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest backend/tests/api/test/test_results_query.py -v`
Expected: FAIL with "validation errors", "missing query parameters", or "field not found"

**Step 3: Write minimal implementation**

Create `backend/app/schemas/test_result_query.py`:

```python
"""Test Result Query Schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TestSessionListResponse(BaseModel):
    """Enhanced test session response with nested details"""
    id: int
    serial_number: str
    station_id: int
    user_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    final_result: Optional[str] = None
    total_items: Optional[int] = None
    pass_items: Optional[int] = None
    fail_items: Optional[int] = None
    test_duration_seconds: Optional[int] = None
    created_at: datetime

    # Nested relationships
    station: Optional[dict] = None  # Will include project via eager load
    user: Optional[dict] = None

    class Config:
        from_attributes = True


class TestResultsQueryParams(BaseModel):
    """Query parameters for test results filtering"""
    project_id: Optional[int] = None
    station_id: Optional[int] = None
    serial_number: Optional[str] = None
    final_result: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    test_plan_name: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
```

Modify `backend/app/api/tests.py` list_test_sessions endpoint (lines 560-603):

```python
# Original: @router.get("/sessions", response_model=List[TestSession])
# Modified: Enhanced with filtering and nested relationships
@router.get("/sessions", response_model=List[TestSessionListResponse])
async def list_test_sessions(
    project_id: int = None,
    station_id: int = None,
    serial_number: str = None,
    final_result: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    List test sessions with advanced filtering

    Args:
        project_id: Filter by project ID
        station_id: Filter by station ID
        serial_number: Filter by serial number (partial match)
        final_result: Filter by result (PASS/FAIL/ABORT)
        start_date: Filter by start date (ISO format)
        end_date: Filter by end date (ISO format)
        limit: Maximum number of results
        offset: Number of results to skip
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of test sessions with nested station and project data
    """
    from sqlalchemy.orm import joinedload

    # Build query with eager loading for nested relationships
    query = db.query(TestSessionModel).options(
        joinedload(TestSessionModel.station).joinedload(Station.project)
    )

    # Apply filters
    if project_id:
        query = query.join(Station).filter(Station.project_id == project_id)

    if station_id:
        query = query.filter(TestSessionModel.station_id == station_id)

    if serial_number:
        from sqlalchemy import func
        query = query.filter(
            TestSessionModel.serial_number.like(func.concat('%', serial_number, '%'))
        )

    if final_result:
        query = query.filter(TestSessionModel.final_result == final_result)

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(TestSessionModel.start_time >= start_dt)
        except ValueError:
            pass  # Invalid date format, ignore filter

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(TestSessionModel.start_time <= end_dt)
        except ValueError:
            pass  # Invalid date format, ignore filter

    # Order by start_time descending (newest first)
    from sqlalchemy import desc
    sessions = query.order_by(
        desc(TestSessionModel.start_time)
    ).limit(limit).offset(offset).all()

    return sessions
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest backend/tests/api/test/test_results_query.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/api/tests.py backend/app/schemas/test_result_query.py backend/tests/api/test/test_results_query.py
git commit -m "feat: add test results query API with filtering support"
```

---

### Task 2: Add Test Plan Name Filtering

**Files:**
- Modify: `backend/app/models/test_session.py` (add test_plan_id column)
- Create: `backend/alembic/versions/xxx_add_test_plan_id_to_sessions.py`

**Step 1: Write database migration**

Create migration file `backend/alembic/versions/20260306_add_test_plan_id_to_sessions.py`:

```python
"""Add test_plan_id to test_sessions

Revision ID: 20260306_add_test_plan_id
Revises: (find latest)
Create Date: 2026-03-06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '20260306_add_test_plan_id'
down_revision = None  # Set to latest revision ID
branch_labels = None
depends_on = None


def upgrade():
    """Add test_plan_id column to test_sessions"""
    op.add_column(
        'test_sessions',
        sa.Column('test_plan_id', sa.Integer(), nullable=True)
    )
    op.add_column(
        'test_sessions',
        sa.Column('test_plan_name', sa.String(100), nullable=True)
    )
    op.create_foreign_key(
        'fk_test_sessions_test_plan_id',
        'test_sessions', 'test_plans',
        ['test_plan_id'], ['id']
    )
    # Create index for filtering
    op.create_index(
        'ix_test_sessions_test_plan_id',
        'test_sessions',
        ['test_plan_id']
    )


def downgrade():
    """Remove test_plan_id column"""
    op.drop_index('ix_test_sessions_test_plan_id', 'test_sessions')
    op.drop_constraint('fk_test_sessions_test_plan_id', 'test_sessions')
    op.drop_column('test_sessions', 'test_plan_name')
    op.drop_column('test_sessions', 'test_plan_id')
```

**Step 2: Apply migration**

Run: `uv run alembic upgrade head`
Expected: SUCCESS message with test_plan_id added

**Step 3: Update model**

Modify `backend/app/models/test_session.py` line 22:

```python
# Original: user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
# Modified: Add test_plan_id after user_id
user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
test_plan_id = Column(Integer, ForeignKey("test_plans.id"), nullable=True)
test_plan_name = Column(String(100), nullable=True)
```

**Step 4: Commit**

```bash
git add backend/alembic/versions/20260306_add_test_plan_id_to_sessions.py backend/app/models/test_session.py
git commit -m "feat: add test_plan_id and test_plan_name to test_sessions"
```

---

## Frontend Implementation

### Task 3: Create Test Results API Client

**Files:**
- Create: `frontend/src/api/testResults.js`

**Step 1: Write the API client functions**

Create `frontend/src/api/testResults.js`:

```javascript
/**
 * Test Results API client
 * Handles queries for test sessions and their results
 */
import apiClient from './client'

/**
 * Query test sessions with filters
 * @param {Object} params - Query parameters
 * @param {number} params.project_id - Filter by project ID
 * @param {number} params.station_id - Filter by station ID
 * @param {string} params.serial_number - Filter by serial number (partial match)
 * @param {string} params.final_result - Filter by result (PASS/FAIL/ABORT)
 * @param {string} params.start_date - Filter by start date (ISO format)
 * @param {string} params.end_date - Filter by end date (ISO format)
 * @param {string} params.test_plan_name - Filter by test plan name
 * @param {number} params.limit - Maximum results (default: 50)
 * @param {number} params.offset - Pagination offset (default: 0)
 * @returns {Promise} Array of test sessions
 */
export const queryTestSessions = (params = {}) => {
  return apiClient.get('/api/tests/sessions', { params })
}

/**
 * Get session details with results
 * @param {number} sessionId - Test session ID
 * @returns {Promise} Test session with results
 */
export const getSessionWithResults = (sessionId) => {
  return apiClient.get(`/api/tests/sessions/${sessionId}/results`)
}

/**
 * Export test results to CSV
 * @param {Object} params - Query parameters for filtering
 * @returns {Promise} Blob - CSV file blob
 */
export const exportTestResults = (params = {}) => {
  return apiClient.get('/api/tests/sessions/export', {
    params,
    responseType: 'blob'
  })
}
```

**Step 2: Commit**

```bash
git add frontend/src/api/testResults.js
git commit -m "feat: add test results API client"
```

---

### Task 4: Create Test Results View Component

**Files:**
- Create: `frontend/src/views/TestResults.vue`
- Modify: `frontend/src/router/index.js` (add route)

**Step 1: Write the component structure**

Create `frontend/src/views/TestResults.vue`:

```vue
<template>
  <div class="test-results-container">
    <!-- Navigation -->
    <el-card class="nav-card" shadow="never">
      <el-row :gutter="10" align="middle" justify="space-between">
        <el-col :span="18">
          <div class="nav-buttons">
            <el-button size="default" @click="navigateTo('/main')">
              測試主畫面
            </el-button>
            <el-button size="default" @click="navigateTo('/testplan')">
              測試計劃管理
            </el-button>
            <el-button type="primary" size="default" disabled>
              測試結果查詢
            </el-button>
            <el-button size="default" @click="navigateTo('/projects')">
              專案管理
            </el-button>
            <el-button size="default" @click="navigateTo('/users')">
              使用者管理
            </el-button>
          </div>
        </el-col>
        <el-col :span="6" style="text-align: right">
          <el-text type="info">{{ authStore.user?.username || '-' }}</el-text>
          <el-button type="danger" size="small" @click="handleLogout" style="margin-left: 10px">
            登出
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card>
      <template #header>
        <div class="card-header">
          <h2>測試結果查詢</h2>
          <div class="header-actions">
            <el-button
              type="success"
              :icon="Download"
              :disabled="sessions.length === 0"
              @click="handleExport"
            >
              匯出結果
            </el-button>
          </div>
        </div>
      </template>

      <!-- Filter Section -->
      <el-card class="filter-card" shadow="never">
        <el-form :model="filters" label-width="100px">
          <el-row :gutter="20">
            <!-- Project Selection -->
            <el-col :span="6">
              <el-form-item label="專案">
                <el-select
                  v-model="filters.project_id"
                  placeholder="選擇專案"
                  clearable
                  filterable
                  @change="handleProjectChange"
                  style="width: 100%"
                >
                  <el-option
                    v-for="project in projectStore.projects"
                    :key="project.id"
                    :label="`${project.project_code} - ${project.project_name}`"
                    :value="project.id"
                  />
                </el-select>
              </el-form-item>
            </el-col>

            <!-- Station Selection -->
            <el-col :span="6">
              <el-form-item label="站別">
                <el-select
                  v-model="filters.station_id"
                  placeholder="選擇站別"
                  clearable
                  filterable
                  :disabled="!filters.project_id"
                  style="width: 100%"
                >
                  <el-option
                    v-for="station in filteredStations"
                    :key="station.id"
                    :label="`${station.station_code} - ${station.station_name}`"
                    :value="station.id"
                  />
                </el-select>
              </el-form-item>
            </el-col>

            <!-- Test Plan Name -->
            <el-col :span="6">
              <el-form-item label="測試計劃">
                <el-select
                  v-model="filters.test_plan_name"
                  placeholder="選擇測試計劃"
                  clearable
                  filterable
                  :disabled="!filters.station_id"
                  style="width: 100%"
                >
                  <el-option
                    v-for="planName in testPlanNames"
                    :key="planName"
                    :label="planName"
                    :value="planName"
                  />
                </el-select>
              </el-form-item>
            </el-col>

            <!-- Final Result -->
            <el-col :span="6">
              <el-form-item label="測試結果">
                <el-select
                  v-model="filters.final_result"
                  placeholder="選擇結果"
                  clearable
                  style="width: 100%"
                >
                  <el-option label="通過" value="PASS" />
                  <el-option label="失敗" value="FAIL" />
                  <el-option label="中止" value="ABORT" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="20">
            <!-- Serial Number -->
            <el-col :span="8">
              <el-form-item label="序號">
                <el-input
                  v-model="filters.serial_number"
                  placeholder="輸入序號"
                  clearable
                />
              </el-form-item>
            </el-col>

            <!-- Date Range -->
            <el-col :span="10">
              <el-form-item label="日期範圍">
                <el-date-picker
                  v-model="dateRange"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="開始日期"
                  end-placeholder="結束日期"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>

            <!-- Search Button -->
            <el-col :span="6">
              <el-button type="primary" @click="handleSearch" :loading="loading">
                查詢
              </el-button>
              <el-button @click="handleReset">重置</el-button>
            </el-col>
          </el-row>
        </el-form>
      </el-card>

      <!-- Results Summary -->
      <el-alert
        v-if="sessions.length > 0"
        :title="`找到 ${totalSessions} 筆測試記錄，顯示第 ${currentPage + 1} 頁`"
        type="success"
        :closable="false"
        style="margin-bottom: 20px"
      />

      <!-- Results Table -->
      <el-table
        :data="sessions"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="expanded-content">
              <el-descriptions :column="3" border>
                <el-descriptions-item label="專案">
                  {{ getProjectName(row) }}
                </el-descriptions-item>
                <el-descriptions-item label="站別">
                  {{ getStationName(row) }}
                </el-descriptions-item>
                <el-descriptions-item label="測試計劃">
                  {{ row.test_plan_name || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="開始時間">
                  {{ formatDateTime(row.start_time) }}
                </el-descriptions-item>
                <el-descriptions-item label="結束時間">
                  {{ row.end_time ? formatDateTime(row.end_time) : '進行中' }}
                </el-descriptions-item>
                <el-descriptions-item label="測試時長">
                  {{ row.test_duration_seconds ? `${row.test_duration_seconds}秒` : '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="總項目">
                  {{ row.total_items || 0 }}
                </el-descriptions-item>
                <el-descriptions-item label="通過">
                  <el-text type="success">{{ row.pass_items || 0 }}</el-text>
                </el-descriptions-item>
                <el-descriptions-item label="失敗">
                  <el-text type="danger">{{ row.fail_items || 0 }}</el-text>
                </el-descriptions-item>
              </el-descriptions>

              <!-- View Results Button -->
              <div style="margin-top: 15px; text-align: center">
                <el-button
                  type="primary"
                  size="small"
                  @click="handleViewResults(row)"
                >
                  查看詳細結果
                </el-button>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="id" label="Session ID" width="100" />

        <el-table-column prop="serial_number" label="序號" width="180" />

        <el-table-column label="專案/站別" min-width="200">
          <template #default="{ row }">
            <div>
              <div>{{ getProjectName(row) }}</div>
              <el-text type="info" size="small">{{ getStationName(row) }}</el-text>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="test_plan_name" label="測試計劃" width="150">
          <template #default="{ row }">
            {{ row.test_plan_name || '-' }}
          </template>
        </el-table-column>

        <el-table-column label="結果" width="100">
          <template #default="{ row }">
            <el-tag
              :type="getResultTagType(row.final_result)"
              v-if="row.final_result"
            >
              {{ getResultLabel(row.final_result) }}
            </el-tag>
            <el-text v-else type="info">進行中</el-text>
          </template>
        </el-table-column>

        <el-table-column label="統計" width="180">
          <template #default="{ row }">
            <span v-if="row.total_items">
              通過: <el-text type="success">{{ row.pass_items || 0 }}</el-text>
              / 失敗: <el-text type="danger">{{ row.fail_items || 0 }}</el-text>
              / 總計: {{ row.total_items }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column prop="start_time" label="測試時間" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.start_time) }}
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100, 200]"
          :total="totalSessions"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- Results Detail Dialog -->
    <el-dialog
      v-model="showResultsDialog"
      title="測試結果詳情"
      width="90%"
      top="5vh"
    >
      <div v-if="selectedSession">
        <el-descriptions :column="2" border style="margin-bottom: 20px">
          <el-descriptions-item label="Session ID">
            {{ selectedSession.id }}
          </el-descriptions-item>
          <el-descriptions-item label="序號">
            {{ selectedSession.serial_number }}
          </el-descriptions-item>
          <el-descriptions-item label="專案">
            {{ getProjectName(selectedSession) }}
          </el-descriptions-item>
          <el-descriptions-item label="站別">
            {{ getStationName(selectedSession) }}
          </el-descriptions-item>
          <el-descriptions-item label="測試計劃">
            {{ selectedSession.test_plan_name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="最終結果">
            <el-tag :type="getResultTagType(selectedSession.final_result)">
              {{ getResultLabel(selectedSession.final_result) }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <el-table
          :data="sessionResults"
          v-loading="resultsLoading"
          stripe
          max-height="500"
        >
          <el-table-column prop="item_no" label="項次" width="80" />
          <el-table-column prop="item_name" label="測試項目" min-width="200" />
          <el-table-column prop="measured_value" label="測量值" width="120" />
          <el-table-column label="限制值" width="150">
            <template #default="{ row }">
              <span v-if="row.lower_limit !== null || row.upper_limit !== null">
                {{ row.lower_limit ?? '-' }} ~ {{ row.upper_limit ?? '-' }}
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="unit" label="單位" width="80" />
          <el-table-column label="結果" width="100">
            <template #default="{ row }">
              <el-tag :type="getResultTagType(row.result)">
                {{ row.result }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="error_message" label="錯誤訊息" min-width="200" show-overflow-tooltip />
        </el-table>
      </div>

      <template #footer>
        <el-button @click="showResultsDialog = false">關閉</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import { queryTestSessions, getSessionWithResults } from '@/api/testResults'
import { getStationTestPlanNames } from '@/api/testplans'

const router = useRouter()
const authStore = useAuthStore()
const projectStore = useProjectStore()

// Navigation
const navigateTo = (path) => {
  router.push(path)
}

const handleLogout = async () => {
  try {
    await authStore.logout()
    router.push('/login')
  } catch (error) {
    console.error('Logout failed:', error)
    router.push('/login')
  }
}

// Filters
const filters = reactive({
  project_id: null,
  station_id: null,
  test_plan_name: null,
  final_result: null,
  serial_number: null,
  start_date: null,
  end_date: null
})

const dateRange = ref([])

// Data
const sessions = ref([])
const loading = ref(false)
const totalSessions = ref(0)
const currentPage = ref(1)
const pageSize = ref(50)

// Test plan names
const testPlanNames = ref([])

// Dialog
const showResultsDialog = ref(false)
const selectedSession = ref(null)
const sessionResults = ref([])
const resultsLoading = ref(false)

// Computed
const filteredStations = computed(() => {
  if (!filters.project_id) return []
  return projectStore.stations.filter(s => s.project_id === filters.project_id)
})

// Methods
const handleProjectChange = async (projectId) => {
  filters.station_id = null
  filters.test_plan_name = null
  testPlanNames.value = []

  if (projectId) {
    try {
      await projectStore.fetchProjectStations(projectId)
    } catch (error) {
      ElMessage.error('載入站別列表失敗')
    }
  }
}

const handleStationChange = async (stationId) => {
  filters.test_plan_name = null
  testPlanNames.value = []

  if (stationId && filters.project_id) {
    try {
      const names = await getStationTestPlanNames(stationId, filters.project_id)
      testPlanNames.value = names
    } catch (error) {
      ElMessage.error('載入測試計劃列表失敗')
    }
  }
}

const handleSearch = async () => {
  currentPage.value = 1
  await loadSessions()
}

const handleReset = () => {
  filters.project_id = null
  filters.station_id = null
  filters.test_plan_name = null
  filters.final_result = null
  filters.serial_number = null
  dateRange.value = []
  testPlanNames.value = []
  sessions.value = []
  totalSessions.value = 0
}

const loadSessions = async () => {
  loading.value = true
  try {
    const params = {
      ...filters,
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value
    }

    // Add date range filters
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = new Date(dateRange.value[0]).toISOString()
      params.end_date = new Date(dateRange.value[1] + 'T23:59:59').toISOString()
    }

    // Remove null values
    Object.keys(params).forEach(key => {
      if (params[key] === null || params[key] === undefined) {
        delete params[key]
      }
    })

    sessions.value = await queryTestSessions(params)
    // For pagination, we need total count - this is a simplification
    // In production, you'd want a separate count endpoint or include total in response
    totalSessions.value = sessions.value.length >= pageSize.value
      ? (currentPage.value * pageSize.value) + 1
      : (currentPage.value - 1) * pageSize.value + sessions.value.length
  } catch (error) {
    console.error('Failed to load sessions:', error)
    ElMessage.error('載入測試記錄失敗')
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page) => {
  currentPage.value = page
  loadSessions()
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  loadSessions()
}

const handleViewResults = async (session) => {
  selectedSession.value = session
  showResultsDialog.value = true
  resultsLoading.value = true

  try {
    sessionResults.value = await getSessionWithResults(session.id)
  } catch (error) {
    console.error('Failed to load results:', error)
    ElMessage.error('載入測試結果失敗')
  } finally {
    resultsLoading.value = false
  }
}

const handleExport = () => {
  ElMessage.info('匯出功能開發中')
}

// Utility functions
const getProjectName = (row) => {
  return row.station?.project?.project_name || '-'
}

const getStationName = (row) => {
  return row.station?.station_name || '-'
}

const getResultTagType = (result) => {
  const types = {
    'PASS': 'success',
    'FAIL': 'danger',
    'ABORT': 'warning',
    'ERROR': 'danger'
  }
  return types[result] || 'info'
}

const getResultLabel = (result) => {
  const labels = {
    'PASS': '通過',
    'FAIL': '失敗',
    'ABORT': '中止',
    'ERROR': '錯誤'
  }
  return labels[result] || result
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

onMounted(async () => {
  try {
    await projectStore.fetchProjects()
  } catch (error) {
    ElMessage.error('載入專案列表失敗')
  }
})
</script>

<style scoped>
.test-results-container {
  padding: 20px;
}

.nav-card {
  margin-bottom: 20px;
}

.nav-buttons {
  display: flex;
  gap: 8px;
}

.nav-buttons .el-button {
  margin: 0;
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

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-card :deep(.el-card__body) {
  padding: 15px 20px;
}

.expanded-content {
  padding: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

:deep(.el-table) {
  font-size: 14px;
}
</style>
```

**Step 2: Add router configuration**

Modify `frontend/src/router/index.js` after line 55:

```javascript
// Original: Last route was UserManage
// Modified: Add TestResults route
{
  path: '/results',
  name: 'TestResults',
  component: () => import('@/views/TestResults.vue'),
  meta: { requiresAuth: true }
}
```

**Step 3: Test the component**

Run: `cd frontend && npm run dev`
Expected: Component loads without errors, displays filter form

**Step 4: Commit**

```bash
git add frontend/src/views/TestResults.vue frontend/src/router/index.js
git commit -m "feat: add test results view with filtering"
```

---

### Task 5: Add Navigation Link to Test Results

**Files:**
- Modify: `frontend/src/views/TestMain.vue`
- Modify: `frontend/src/views/TestPlanManage.vue`
- Modify: `frontend/src/views/UserManage.vue`
- Modify: `frontend/src/views/ProjectManage.vue`

**Step 1: Update navigation in all management views**

Add "測試結果查詢" button to each view's navigation section:

In each view's navigation card, add:

```vue
<el-button size="default" @click="navigateTo('/results')">
  測試結果查詢
</el-button>
```

**Step 2: Test navigation**

Run: `cd frontend && npm run dev`
Click navigation buttons to verify routing

**Step 3: Commit**

```bash
git add frontend/src/views/TestMain.vue frontend/src/views/TestPlanManage.vue frontend/src/views/UserManage.vue frontend/src/views/ProjectManage.vue
git commit -m "feat: add navigation links to test results view"
```

---

### Task 6: Add Results Count Endpoint

**Files:**
- Modify: `backend/app/api/tests.py`

**Step 1: Add count endpoint**

Add to `backend/app/api/tests.py` after the list sessions endpoint:

```python
@router.get("/sessions/count")
async def count_test_sessions(
    project_id: int = None,
    station_id: int = None,
    serial_number: str = None,
    final_result: str = None,
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Count test sessions matching filters

    Args:
        Same filters as list_test_sessions

    Returns:
        Total count of matching sessions
    """
    from sqlalchemy import func

    query = db.query(func.count(TestSessionModel.id))

    # Apply same filters as list_test_sessions
    if project_id:
        query = query.join(Station).filter(Station.project_id == project_id)

    if station_id:
        query = query.filter(TestSessionModel.station_id == station_id)

    if serial_number:
        query = query.filter(
            TestSessionModel.serial_number.like(func.concat('%', serial_number, '%'))
        )

    if final_result:
        query = query.filter(TestSessionModel.final_result == final_result)

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(TestSessionModel.start_time >= start_dt)
        except ValueError:
            pass

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(TestSessionModel.start_time <= end_dt)
        except ValueError:
            pass

    count = query.scalar()
    return {"total": count}
```

**Step 2: Update frontend to use count**

Modify `frontend/src/views/TestResults.vue` loadSessions function:

```javascript
// Add to imports at top
import { countTestSessions } from '@/api/testResults'

// In loadSessions function, replace total calculation:
const [sessionsData, countData] = await Promise.all([
  queryTestSessions(params),
  countTestSessions(params)
])

sessions.value = sessionsData
totalSessions.value = countData.total
```

**Step 3: Commit**

```bash
git add backend/app/api/tests.py frontend/src/api/testResults.js frontend/src/views/TestResults.vue
git commit -m "feat: add test sessions count endpoint for accurate pagination"
```

---

## Documentation and Cleanup

### Task 7: Update API Documentation

**Files:**
- Create: `docs/api/test-results-api.md`

**Step 1: Write API documentation**

Create `docs/api/test-results-api.md`:

```markdown
# Test Results API Documentation

## Query Test Sessions

List and filter test sessions with pagination.

### Endpoint
`GET /api/tests/sessions`

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| project_id | integer | No | Filter by project ID |
| station_id | integer | No | Filter by station ID |
| serial_number | string | No | Partial match on serial number |
| final_result | string | No | Filter by result: PASS, FAIL, ABORT |
| start_date | string | No | ISO format date string (e.g., 2026-03-01T00:00:00) |
| end_date | string | No | ISO format date string |
| test_plan_name | string | No | Filter by test plan name |
| limit | integer | No | Max results per page (default: 50, max: 500) |
| offset | integer | No | Pagination offset (default: 0) |

### Response
Array of test session objects with nested station and project data.

### Example

```bash
curl "http://localhost:9100/api/tests/sessions?project_id=1&final_result=PASS&limit=10"
```

## Count Test Sessions

Get total count of sessions matching filters.

### Endpoint
`GET /api/tests/sessions/count`

### Query Parameters
Same as query endpoint.

### Response

```json
{
  "total": 123
}
```

## Get Session Results

Get detailed test results for a session.

### Endpoint
`GET /api/tests/sessions/{session_id}/results`

### Response
Array of test result objects.
```

**Step 2: Commit**

```bash
git add docs/api/test-results-api.md
git commit -m "docs: add test results API documentation"
```

---

### Task 8: Integration Testing

**Files:**
- Create: `backend/tests/integration/test/test_results_workflow.py`

**Step 1: Write integration test**

```python
"""Test Results Workflow Integration Tests"""
import pytest
from fastapi.testclient import TestClient


def test_full_results_query_workflow(client: TestClient, test_data):
    """
    Test complete workflow: filter → list → view details
    """
    # 1. Query sessions with filters
    response = client.get(
        "/api/tests/sessions",
        params={
            "project_id": 1,
            "final_result": "PASS",
            "limit": 10
        }
    )
    assert response.status_code == 200
    sessions = response.json()
    assert len(sessions) > 0

    # 2. Verify nested data is present
    session = sessions[0]
    assert "station" in session
    assert "project" in session["station"]

    # 3. Get detailed results for first session
    response = client.get(f"/api/tests/sessions/{session['id']}/results")
    assert response.status_code == 200
    results = response.json()
    assert len(results) > 0

    # 4. Verify result structure
    result = results[0]
    assert "item_name" in result
    assert "result" in result
    assert result["result"] in ["PASS", "FAIL", "SKIP", "ERROR"]
```

**Step 2: Run integration test**

Run: `uv run pytest backend/tests/integration/test/test_results_workflow.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add backend/tests/integration/test/test_results_workflow.py
git commit -m "test: add test results workflow integration test"
```

---

## Summary

This plan implements a complete test results query interface with:

1. **Backend API enhancements** - Filtering by project, station, test plan, serial number, date range, and result
2. **Frontend view component** - Comprehensive filter form with expandable session details
3. **Pagination support** - Accurate count endpoint for proper pagination
4. **Navigation integration** - Links from all management views
5. **Documentation** - Complete API reference

`★ Insight ─────────────────────────────────────`
- **Eager Loading Pattern**: Using SQLAlchemy's `joinedload()` prevents N+1 queries when fetching nested relationships (station → project), critical for performance
- **Filter Form UX**: Cascading dropdowns (project → station → test plan) reduce invalid filter combinations and guide user selection
- **Date Handling**: ISO format strings with timezone awareness prevent ambiguity in cross-timezone deployments
`─────────────────────────────────────────────────`
