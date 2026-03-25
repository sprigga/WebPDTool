# Test History Timeline View

**Feature:** Timeline-based test history visualization with ECharts chart integration
**Status:** ✅ Complete (2026-03-25)
**Related Files:**
- `frontend/src/views/TestHistory.vue`
- `frontend/src/composables/useTestHistory.js`
- `frontend/src/composables/useTestTimeline.js`
- `frontend/src/utils/dateHelpers.js`

---

## Overview

TestHistory.vue provides a timeline-based view of test sessions, complementing the existing TestResults.vue query page. While TestResults focuses on detailed filtering and inspection, TestHistory emphasizes **temporal visualization** with day-by-day aggregation and an ECharts stacked bar chart.

### Key Features

1. **Timeline View** - Sessions grouped by date with expandable details
2. **Statistics Dashboard** - Global and per-day pass/fail/abort counts
3. **ECharts Visualization** - Stacked bar chart showing test trends
4. **Cascade Filters** - Project → Station dropdown filtering
5. **Results Dialog** - Detailed test item inspection per session
6. **Timezone-Aware** - Asia/Taipei timezone normalization throughout

---

## Architecture

### Component Structure

```
TestHistory.vue (569 lines)
├── Template
│   ├── Filters Row (date range, project, station)
│   ├── Statistics Row (total, pass, fail, pass rate)
│   ├── ECharts Card (.chart-container)
│   └── Timeline List (grouped by date)
├── Script Setup
│   ├── useProjectStore (projects, stations)
│   ├── useTestHistory (sessions, sessionsByDate, dailyStats)
│   ├── useTestTimeline (chartRef, initChart, updateChart)
│   └── Event handlers (loadSessions, showResults, etc.)
└── Styles
    ├── Responsive breakpoints
    ├── Timeline card styles
    └── Chart container styles
```

### Composable Architecture

**useTestHistory.js** (95 lines)
- Fetches test sessions from `GET /api/tests/sessions`
- Groups sessions by date for timeline display
- Calculates daily statistics (pass/fail/abort counts)
- Handles loading/error states

**useTestTimeline.js** (126 lines)
- Manages ECharts instance lifecycle
- Groups sessions by date for chart data
- Provides stacked bar chart configuration
- Handles cleanup on route navigation and unmount

**dateHelpers.js** (32 lines)
- `normalizeTaipeiDate()` - Adds +08:00 timezone if missing
- `formatDateKey()` - Extracts YYYY-MM-DD using local date parts

### Data Flow

```
User selects filters
    ↓
loadSessions() calls queryTestSessions()
    ↓
API returns sessions array
    ↓
useTestHistory processes data
    ├── sessionsByDate computed (for timeline)
    └── dailyStats computed (for statistics)
useTestTimeline processes data
    └── chartData computed (for ECharts)
    ↓
Deep watch triggers updateChart()
    ↓
ECharts renders stacked bar chart
```

---

## Implementation Details

### 1. Date Helper Utility (Prerequisite)

**File:** `frontend/src/utils/dateHelpers.js`

**Critical Bug Fix:** The initial implementation used `toISOString().split('T')[0]` which converts dates to UTC before extracting the date. This caused sessions executed after midnight in Taiwan to be grouped under the previous day.

**Fixed Implementation:**
```javascript
export function formatDateKey(dateStr) {
  const normalized = normalizeTaipeiDate(dateStr)
  if (!normalized) return null
  const date = new Date(normalized)
  // FIXED: Use local date parts instead of toISOString()
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
```

**Why This Matters:**
- `2026-03-26T01:30:00+08:00` → UTC becomes `2026-03-25T17:30:00Z`
- Using `toISOString()` returns `2026-03-25` (WRONG - previous day)
- Using local date parts returns `2026-03-26` (CORRECT)

### 2. Test History Composable

**File:** `frontend/src/composables/useTestHistory.js`

**Key Functions:**
```javascript
export function useTestHistory() {
  const sessions = ref([])
  const loading = ref(false)
  const error = ref(null)

  const sessionsByDate = computed(() => {
    const grouped = {}
    sessions.value.forEach(session => {
      const dateKey = formatDateKey(session.start_time)
      // ... grouping logic
    })
    return grouped
  })

  const dailyStats = computed(() => {
    // Calculate per-day statistics
  })

  const fetchSessions = async (params) => {
    // API call with error handling
  }

  return { sessions, sessionsByDate, dailyStats, loading, error, fetchSessions }
}
```

### 3. Timeline Chart Composable

**File:** `frontend/src/composables/useTestTimeline.js`

**Chart Configuration:**
```javascript
const option = {
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'shadow' }
  },
  legend: {
    data: ['通過', '失敗', '中止']
  },
  xAxis: {
    type: 'category',
    data: chartData.value.map(d => d.date)
  },
  yAxis: {
    type: 'value'
  },
  series: [
    {
      name: '通過',
      type: 'bar',
      stack: 'total',
      data: chartData.value.map(d => d.pass),
      itemStyle: { color: '#67C23A' }
    },
    // ... fail and abort series
  ]
}
```

**Lifecycle Management:**
```javascript
// Cleanup on route leave
onBeforeRouteLeave(() => {
  disposeChart()
})

// Cleanup on component unmount
onUnmounted(() => {
  disposeChart()
})

const disposeChart = () => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance.value) {
    chartInstance.value.dispose()
    chartInstance.value = null
  }
}
```

**Important Constants:**
```javascript
// Chart initialization delay to ensure DOM container has dimensions
// (100ms balances between reliability and responsiveness)
const CHART_INIT_DELAY_MS = 100
```

### 4. Template Integration

**Chart Container:**
```vue
<el-card class="chart-card" shadow="never">
  <div ref="chartRef" class="chart-container"></div>
</el-card>
```

**CSS:**
```css
.chart-card {
  margin-bottom: 20px;
}

.chart-container {
  width: 100%;
  height: 300px;
}
```

**Script Integration:**
```javascript
import { useTestTimeline } from '@/composables/useTestTimeline'
import { watch, nextTick } from 'vue'

const { chartRef, initChart, updateChart } = useTestTimeline(sessions)

// Update chart when sessions change
watch(sessions, () => {
  updateChart()
}, { deep: true })

// Initialize chart after DOM is ready
const initChartWhenReady = async () => {
  await nextTick()
  setTimeout(initChart, CHART_INIT_DELAY_MS)
}

onMounted(async () => {
  // ... load data
  await initChartWhenReady()
})
```

---

## Troubleshooting Guide

### Issue 1: Browser Caching Causing Stale Code

**Symptom:**
- Navigating to `/history` redirects to `/results`
- Navbar doesn't show "測試歷史記錄" button
- Old code appears to run despite source changes

**Root Cause:**
Playwright browser was caching the old JavaScript bundle. The built files were correct, but the browser served cached versions.

**Solution:**
Set cache-busting headers before navigation:
```javascript
await page.route('**/*', route => {
  const headers = route.request().headers();
  headers['Cache-Control'] = 'no-cache';
  headers['Pragma'] = 'no-cache';
  route.continue({ headers });
});
```

**Prevention:**
- Always use cache-busting when testing after builds
- Verify built bundle contents with `docker-compose exec frontend cat /usr/share/nginx/html/assets/index-*.js | grep "TestHistory"`

### Issue 2: Timezone Bug in formatDateKey

**Symptom:**
- Sessions after midnight grouped under previous day
- Daily statistics don't match actual execution dates

**Root Cause:**
`toISOString().split('T')[0]` converts to UTC before extracting date:
```javascript
// WRONG - converts to UTC first
return date.toISOString().split('T')[0]
```

**Solution:**
Use local date parts instead:
```javascript
const year = date.getFullYear()
const month = String(date.getMonth() + 1).padStart(2, '0')
const day = String(date.getDate()).padStart(2, '0')
return `${year}-${month}-${day}`
```

**Verification:**
Test with timestamps near midnight:
```javascript
formatDateKey('2026-03-26T01:30:00+08:00') // Should return '2026-03-26'
formatDateKey('2026-03-25T23:30:00+08:00') // Should return '2026-03-25'
```

### Issue 3: Chart Not Rendering (Blank Canvas)

**Symptom:**
- Chart container exists but canvas is blank
- No error in console

**Root Cause:**
Chart initialization happens before DOM container has computed dimensions.

**Solution:**
Use `nextTick()` + `setTimeout` delay:
```javascript
const initChartWhenReady = async () => {
  await nextTick()
  setTimeout(initChart, CHART_INIT_DELAY_MS)
}
```

**Alternative Solution:**
Use `ResizeObserver` to wait for container size:
```javascript
const observer = new ResizeObserver(() => {
  if (chartRef.value && chartRef.value.offsetHeight > 0) {
    initChart()
    observer.disconnect()
  }
})
observer.observe(chartRef.value)
```

### Issue 4: Chart Not Updating After Filter Change

**Symptom:**
- Changing date range or filters updates timeline but not chart

**Root Cause:**
Missing reactive trigger for chart update.

**Solution:**
Add deep watch on sessions:
```javascript
watch(sessions, () => {
  updateChart()
}, { deep: true })
```

**Why Deep Watch:**
`sessions` is an array of objects. Shallow watch only detects array replacement, not nested property changes.

### Issue 5: Memory Leak on Route Navigation

**Symptom:**
- Multiple ECharts instances created after navigating away and back
- Browser memory usage increases

**Root Cause:**
Chart instance not disposed when leaving route.

**Solution:**
Use `onBeforeRouteLeave` guard:
```javascript
import { onBeforeRouteLeave } from 'vue-router'

onBeforeRouteLeave(() => {
  disposeChart()
})
```

**Double Cleanup Pattern:**
```javascript
// Cleanup on route leave (primary)
onBeforeRouteLeave(() => {
  disposeChart()
})

// Cleanup on component unmount (fallback)
onUnmounted(() => {
  disposeChart()
})
```

---

## Development Commands

### Local Development
```bash
cd frontend
npm run dev  # http://localhost:5678
```

### Docker Build
```bash
docker-compose build frontend
docker-compose up -d frontend
```

### Verification
```bash
# Check router configuration
grep -A5 "path: '/history'" frontend/src/router/index.js

# Check for TestHistory in built bundle
docker-compose exec frontend cat /usr/share/nginx/html/assets/index-*.js | grep -o "TestHistory"

# Verify chart container CSS
grep "chart-container" frontend/src/views/TestHistory.vue
```

### Testing with Playwright
```javascript
// Navigate with cache-busting
await page.route('**/*', route => {
  const headers = route.request().headers();
  headers['Cache-Control'] = 'no-cache';
  route.continue({ headers });
});

await page.goto('http://localhost:9080/history');

// Verify chart rendered
const canvas = await page.$('canvas');
const hasChart = !!canvas;
```

---

## Code Quality Checklist

### Before Committing
- [ ] No unused imports (check with `npx eslint`)
- [ ] No magic numbers (extract to constants)
- [ ] Inline styles moved to CSS classes
- [ ] Proper cleanup in lifecycle hooks
- [ ] Deep watch for reactive objects
- [ ] Error handling for API calls
- [ ] Loading states for user feedback

### After Code Review Fixes
- [ ] Removed `onBeforeMount` (unused import)
- [ ] Extracted `CHART_INIT_DELAY_MS = 100` constant
- [ ] Moved chart height to `.chart-container` CSS class
- [ ] Added JSDoc comments for public functions

---

## Related Documentation

- **Implementation Plan:** `docs/superpowers/plans/2026-03-25-test-history-implementation.md`
- **API Reference:** `backend/app/api/tests.py` - `/api/tests/sessions` endpoint
- **Test Results View:** `frontend/src/views/TestResults.vue` - complementary query view
- **Measurement Architecture:** `docs/lowsheen_lib/README.md` - PDTool4 compatibility

---

## Future Enhancements

1. **Chart Interactivity**
   - Click on bar to filter timeline to that date
   - Zoom/pan for large date ranges

2. **Export Options**
   - Export chart as PNG
   - Export timeline data as Excel

3. **Performance**
   - Virtual scrolling for large session lists
   - Debounced window resize handler

4. **Accessibility**
   - ARIA labels for chart regions
   - Keyboard navigation for timeline items

---

## Changelog

**2026-03-25**
- Initial implementation of TestHistory.vue
- Created useTestHistory composable
- Added ECharts timeline visualization
- Fixed timezone bug in formatDateKey
- Code quality fixes (constants, CSS extraction)

**Commits:**
- `d3f09d1` feat: add results dialog to TestHistory.vue
- `ea25f08` feat: implement TestHistory.vue basic structure with timeline
- `ba43350` feat: add useTestHistory composable for history view
- `421f3e0` fix: use local date parts in formatDateKey to prevent UTC conversion bug
- `3dc6feb` feat: add shared date helper utility for timezone handling
- `96c747c` feat: add ECharts timeline visualization to TestHistory
- `78aa6b4` fix: remove unused import and extract magic numbers to constants
