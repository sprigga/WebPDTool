# useTestTimeline Composable

**File:** `frontend/src/composables/useTestTimeline.js`
**Purpose:** Encapsulates ECharts lifecycle management for a stacked bar + line combo chart that visualizes test session results over time (pass / fail / abort counts + pass-rate trend line).

## Table of Contents

- [Overview](#overview)
- [Imports](#imports)
- [API Signature](#api-signature)
- [Reactive State](#reactive-state)
- [Data Transformation (`chartData`)](#data-transformation-chartdata)
- [Chart Lifecycle Methods](#chart-lifecycle-methods)
  - [`initChart()`](#initchart)
  - [`handleResize()`](#handleresize)
  - [`updateChart()`](#updatechart)
  - [`disposeChart()`](#disposechart)
- [ECharts Configuration Deep Dive](#echarts-configuration-deep-dive)
  - [Global Text Style](#global-text-style)
  - [Title](#title)
  - [Tooltip](#tooltip)
  - [Legend](#legend)
  - [Grid](#grid)
  - [X Axis](#x-axis)
  - [Y Axes (Dual Axis)](#y-axes-dual-axis)
  - [Series (Stacked Bars + Line)](#series-stacked-bars--line)
- [Responsive Adaptation Logic](#responsive-adaptation-logic)
- [Memory Leak Prevention](#memory-leak-prevention)
- [Usage Example (TestResults.vue)](#usage-example-testresultsvue)

---

## Overview

`useTestTimeline` is a **Vue 3 Composition API composable** that manages the full lifecycle of an Apache ECharts instance bound to a DOM element. It:

1. **Accepts** a `Ref<Array>` of test session objects as input.
2. **Transforms** raw sessions into date-grouped aggregates (pass / fail / abort counts per day).
3. **Initializes** an ECharts instance and renders a dual-axis chart (stacked bars + pass-rate line).
4. **Handles** window resize events to keep the chart responsive.
5. **Cleans up** the chart instance and event listeners on route leave or component unmount.

The composable follows the **Extract and Share** pattern from Vue's Composition API — reusable stateful logic that would otherwise live inside a single component.

---

## Imports

```js
import { ref, computed, onUnmounted } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import * as echarts from 'echarts'
```

| Import | Source | Purpose |
|--------|--------|---------|
| `ref` | `vue` | Creates mutable reactive references for the DOM element ref and the ECharts instance |
| `computed` | `vue` | Creates a derived reactive property that auto-aggregates session data by date |
| `onUnmounted` | `vue` | Registers a cleanup callback when the host component is destroyed |
| `onBeforeRouteLeave` | `vue-router` | Registers a cleanup callback when navigating away from the current route (catches cases where the component may not unmount immediately) |
| `echarts` | `echarts` (npm) | Full ECharts bundle — provides `echarts.init()`, chart instance methods (`setOption`, `dispose`, `resize`) |

### Why `* as echarts`?

Importing the full bundle (`* as echarts`) rather than tree-shaken modules (`echarts/core` + individual renderers) trades bundle size for simplicity. This project prioritizes developer ergonomics over minimal bundle weight, since ECharts is the only charting library.

---

## API Signature

```js
export function useTestTimeline(sessions)
```

**Parameter:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `sessions` | `Ref<Array<TestSession>>` | Reactive reference to an array of test session objects. Each object must contain `start_time` (ISO date string) and `final_result` (`'PASS'`, `'FAIL'`, or `'ABORT'`). |

**Returns:**

```js
{ chartRef, chartData, initChart, updateChart, disposeChart }
```

| Return Value | Type | Description |
|---------------|------|-------------|
| `chartRef` | `Ref<HTMLElement>` | Template ref — bind this to a `<div>` element in the template via `ref="chartRef"` |
| `chartData` | `ComputedRef<Array<{date, pass, fail, abort, total}>>` | Read-only computed array of date-grouped aggregates, sorted chronologically |
| `initChart` | `() => void` | Creates (or re-creates) the ECharts instance, calls `updateChart()`, and attaches a resize listener |
| `updateChart` | `() => void` | Recalculates the ECharts option from current `chartData` and applies it |
| `disposeChart` | `() => void` | Removes the resize listener and destroys the ECharts instance |

---

## Reactive State

```js
const chartRef = ref(null)        // Line 7
const chartInstance = ref(null)    // Line 8
```

### `chartRef` (line 7)

- **Type:** `Ref<HTMLElement | null>`
- **Purpose:** Template ref that points to the `<div>` container element in the DOM. The consumer component must bind it: `<div ref="chartRef"></div>`.
- **Grammar:** `ref(null)` initializes to `null` because the DOM element doesn't exist yet at composable call time. Vue will populate it after the component mounts and the template is rendered.

### `chartInstance` (line 8)

- **Type:** `Ref<ECharts | null>`
- **Purpose:** Holds the active ECharts instance returned by `echarts.init()`. Used by all methods to interact with the chart (set options, resize, dispose).
- **Null-safe pattern:** Every method checks `if (chartInstance.value)` before calling methods on it, preventing errors if the chart hasn't been initialized or has been disposed.

---

## Data Transformation (`chartData`)

```js
const chartData = computed(() => {   // Line 10
  const grouped = {}
  sessions.value.forEach(session => {
    const date = new Date(session.start_time).toISOString().split('T')[0]
    if (!grouped[date]) {
      grouped[date] = { pass: 0, fail: 0, abort: 0 }
    }
    if (session.final_result === 'PASS') grouped[date].pass++
    else if (session.final_result === 'FAIL') grouped[date].fail++
    else if (session.final_result === 'ABORT') grouped[date].abort++
  })

  return Object.entries(grouped)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, counts]) => ({
      date,
      ...counts,
      total: counts.pass + counts.fail + counts.abort
    }))
})
```

### How it works

1. **Iterates** over every session in the reactive `sessions.value` array.
2. **Extracts** the date portion (`YYYY-MM-DD`) from `session.start_time`:
   - `new Date(session.start_time)` parses the ISO string into a `Date` object.
   - `.toISOString()` converts back to ISO 8601 format (UTC).
   - `.split('T')[0]` takes everything before the `T` separator → the date part.
   - This ensures consistent date keys regardless of the original timezone offset.
3. **Accumulates** counters (`pass`, `fail`, `abort`) into a `grouped` object keyed by date string.
4. **Sorts** dates chronologically using `String.prototype.localeCompare()` — a locale-aware string comparison that correctly orders ISO date strings (since `YYYY-MM-DD` format sorts lexicographically).
5. **Maps** to flat objects with a computed `total` field.

### Input → Output example

**Input** (sessions):
```js
[
  { start_time: '2026-03-25T10:30:00Z', final_result: 'PASS' },
  { start_time: '2026-03-25T14:20:00Z', final_result: 'FAIL' },
  { start_time: '2026-03-25T16:00:00Z', final_result: 'PASS' },
  { start_time: '2026-03-26T09:00:00Z', final_result: 'ABORT' },
  { start_time: '2026-03-26T11:30:00Z', final_result: 'PASS' },
]
```

**Output** (chartData):
```js
[
  { date: '2026-03-25', pass: 2, fail: 1, abort: 0, total: 3 },
  { date: '2026-03-26', pass: 1, fail: 0, abort: 1, total: 2 },
]
```

### Reactivity chain

```
sessions (Ref) → sessions.value (array) → forEach loop → grouped object
→ Object.entries() → sort → map → chartData (ComputedRef)
→ read by updateChart() → ECharts setOption()
```

Since `chartData` is a `computed`, it re-evaluates automatically whenever `sessions.value` changes. The consumer (`TestResults.vue`) triggers this via a `watch` on `historySessions`.

---

## Chart Lifecycle Methods

### `initChart()`

```js
const initChart = () => {    // Line 32
  if (!chartRef.value) return       // Guard: DOM not mounted yet
  if (chartInstance.value) {
    chartInstance.value.dispose()   // Clean up any previous instance
  }
  chartInstance.value = echarts.init(chartRef.value)
  updateChart()
  window.addEventListener('resize', handleResize)
}
```

**Execution flow:**

| Step | Line | Action |
|------|------|--------|
| 1 | 33 | Early return if the template ref hasn't been bound to a DOM element yet |
| 2 | 35–37 | If an ECharts instance already exists, call `.dispose()` to free memory and DOM event bindings. This prevents "Cannot add a duplicate echarts instance" errors when re-initializing (e.g., after the tab becomes visible again) |
| 3 | 38 | `echarts.init(chartRef.value)` creates a new ECharts instance bound to the DOM element |
| 4 | 39 | Immediately calls `updateChart()` to render the current data |
| 5 | 40 | Registers a `resize` event listener on `window` so the chart adapts when the browser window changes size |

**Grammar note — `echarts.init()` signature:**
```js
echarts.init(
  dom: HTMLElement,       // The container DOM element (required)
  theme?: string | object, // Optional theme name or theme object
  opts?: object           // Optional: { renderer: 'canvas'|'svg', devicePixelRatio, ... }
)
```
Here only `dom` is passed; theme and renderer default to `'canvas'`.

---

### `handleResize()`

```js
const handleResize = () => {   // Line 43
  if (chartInstance.value) {
    chartInstance.value.resize()
  }
}
```

- **Purpose:** Event handler for `window.resize`. Calls `chartInstance.resize()` which recalculates the chart dimensions to fit its container.
- **Null guard:** Only calls `resize()` if the instance exists — prevents errors during teardown.
- **`echarts.Instance.resize()`** automatically detects the container's new `clientWidth`/`clientHeight` and re-renders.

---

### `updateChart()`

```js
const updateChart = () => {    // Line 49
  if (!chartInstance.value) return   // Guard: chart not initialized
  // ... builds `option` object (see ECharts Configuration Deep Dive)
  chartInstance.value.setOption(option, true)
}
```

- **Purpose:** Reads the current `chartData`, constructs a full ECharts `option` object, and applies it.
- **`setOption(option, true)`** — the second argument `true` means **"not merge"**: replaces the entire option instead of merging with the previous one. This is important because the series array may change (abort bars conditionally included/excluded), so partial merging could leave stale series artifacts.
- **Guard:** Returns immediately if the chart instance hasn't been created yet (e.g., if `updateChart()` is called before `initChart()`).

---

### `disposeChart()`

```js
const disposeChart = () => {    // Line 253
  window.removeEventListener('resize', handleResize)
  if (chartInstance.value) {
    chartInstance.value.dispose()
    chartInstance.value = null
  }
}
```

- **Purpose:** Full cleanup — removes the resize listener and destroys the ECharts instance.
- **`removeEventListener`** must reference the **exact same function reference** (`handleResize`) that was passed to `addEventListener`. This is why `handleResize` is defined as a named `const` arrow function rather than an anonymous one — it preserves the reference identity needed for removal.
- **`.dispose()`** frees internal memory, removes internal DOM event listeners, and clears the rendering canvas.
- **`chartInstance.value = null`** prevents any stale references from being used after disposal.

---

## ECharts Configuration Deep Dive

This section documents every property in the ECharts `option` object built inside `updateChart()` (lines 72–248).

### Global Text Style

```js
textStyle: { fontFamily: font, fontSize: 13 },   // Line 73
```

Sets the default font for all chart text. The `font` variable (line 55) is:
```js
const font = '"Microsoft JhengHei", "PingFang TC", "Noto Sans TC", sans-serif'
```

This is a **CJK-optimized font stack** targeting Traditional Chinese text rendering:
1. `Microsoft JhengHei` — Windows (Microsoft's Traditional Chinese font)
2. `PingFang TC` — macOS / iOS
3. `Noto Sans TC` — Linux / cross-platform fallback (Google's open-source CJK font)
4. `sans-serif` — final system fallback

### Title

```js
title: {
  text: '測試趨勢',                    // Chart title (Traditional Chinese: "Test Trends")
  subtext: `共 ${itemCount} 天 · ${totalTests} 次測試`,  // Dynamic subtitle
  left: 'center',                       // Horizontal centering
  top: 6,                               // 6px from top edge
  textStyle: { ... },
  subtextStyle: { ... }
}
```

- `left: 'center'` uses CSS-like horizontal positioning.
- `top: 6` is a pixel value from the top edge of the chart container.
- The subtitle dynamically shows the total number of days and test sessions in the current dataset.

### Tooltip

```js
tooltip: {
  trigger: 'axis',              // Line 85 — show tooltip when hovering over an axis category
  axisPointer: { type: 'shadow' },  // Semi-transparent shadow band highlights the hovered column
  confine: true,                // Line 87 — prevents tooltip from overflowing the chart container
  backgroundColor: 'rgba(255,255,255,0.97)',  // Near-white background (light theme)
  borderColor: '#dcdfe6',       // Subtle border (Element Plus gray-300)
  borderWidth: 1,
  textStyle: { ... },
  formatter(params) { ... }     // Line 92 — custom HTML formatter function
}
```

#### `trigger: 'axis'`

Sets the tooltip to trigger when hovering over any point on the X axis, rather than individual data points. This means hovering anywhere in a column shows all series values for that date.

#### `confine: true`

Clips the tooltip to the chart's bounding box. Without this, tooltips near edges can overflow and cause horizontal scrollbars.

#### Custom `formatter` (lines 92–110)

The formatter receives `params` — an array of data point objects for the hovered axis category. It builds an HTML tooltip:

```
┌────────────────────────────┐
│  2026-03-25                │  ← bold date header with bottom border
│  ● 通過：2 次              │  ← only bars with value > 0 are shown
│  ● 失敗：1 次              │
│  ─────────────────────────  │
│  合計：3 次                │  ← total count
│  ● 通過率：66.7%           │  ← pass rate (only if exists)
└────────────────────────────┘
```

**Key logic in the formatter:**
- `params.filter(p => p.seriesType === 'bar' && p.value > 0)` — filters out zero-value bars to keep the tooltip concise.
- `params.find(p => p.seriesName === '通過率%')` — locates the pass-rate line data point.
- `ratePt?.value != null` — uses `!=` (not `!==`) to match both `null` and `undefined`, since `passRates` can contain `null` for days with zero total tests.

### Legend

```js
legend: {
  data: legendItems,       // Dynamic: ['通過', '失敗', '中止', '通過率%'] or without '中止'
  bottom: 4,               // 4px from bottom edge
  left: 'center',          // Horizontal center
  orient: 'horizontal',    // Items laid out in a row
  itemWidth: 12,           // Color swatch width
  itemHeight: 12,          // Color swatch height
  itemGap: 20,             // Space between items
  textStyle: { ... }
}
```

**Conditional legend entries** (lines 68–70):
```js
const legendItems = hasAbort
  ? ['通過', '失敗', '中止', '通過率%']
  : ['通過', '失敗', '通過率%']
```

If no sessions have `final_result === 'ABORT'`, the "中止" legend entry is omitted to avoid showing an empty legend item.

### Grid

```js
grid: {
  top: 60,                        // Space for the 2-line title
  left: 8,                        // Minimal left padding
  right: 8,                       // Minimal right padding
  bottom: xRotate > 0 ? 68 : 44, // Dynamic bottom padding
  containLabel: true              // Auto-expand to contain axis labels
}
```

**`containLabel: true`** is critical: it tells ECharts to expand the grid area inward to ensure axis labels aren't clipped. The `left: 8` and `right: 8` values are then treated as minimum padding rather than fixed boundaries.

**Dynamic bottom:**
- When X axis labels are rotated (`xRotate > 0`), more vertical space is needed → `68px`.
- When labels are horizontal, less space needed → `44px` (enough for the legend at 24px + some margin).

### X Axis

```js
xAxis: {
  type: 'category',          // Discrete categories (dates), not continuous values
  data: data.map(d => d.date),
  boundaryGap: true,         // Bars start from the center of the tick, not the edge
  axisLine: { lineStyle: { color: '#dcdfe6' } },
  axisTick: { alignWithLabel: true, lineStyle: { color: '#dcdfe6' } },
  axisLabel: {
    fontFamily: font,
    fontSize: 12,
    color: '#606266',
    rotate: xRotate,         // Dynamic rotation (see Responsive section)
    formatter: xFormatter,   // Dynamic format (see Responsive section)
    hideOverlap: true         // Auto-hide labels that would overlap
  }
}
```

- **`type: 'category'`** means each data point is a named category (date string), not a numeric value on a continuous scale.
- **`boundaryGap: true`** offsets the bars so they sit centered on their tick marks rather than spanning between ticks. This is the default for bar charts in ECharts.
- **`hideOverlap: true`** tells ECharts to automatically hide labels that would visually overlap, complementing the manual rotation logic.

### Y Axes (Dual Axis)

```js
yAxis: [
  { /* Left axis — test count */ },
  { /* Right axis — pass rate % */ }
]
```

ECharts supports **multiple Y axes** by using an array. Each series specifies which Y axis it uses via `yAxisIndex`.

#### Left Y Axis (index 0) — Test Count

```js
{
  type: 'value',
  minInterval: 1,         // Minimum step between tick values is 1 (no 0.5, 2.5, etc.)
  min: 0,                 // Always start from zero
  axisLabel: { fontFamily: font, fontSize: 11, color: '#606266' },
  axisLine: { show: false },    // Hide the axis line (clean look)
  axisTick: { show: false },    // Hide tick marks
  splitLine: { lineStyle: { color: '#f0f0f0', type: 'dashed' } }  // Light dashed grid lines
}
```

**`minInterval: 1`** is important: without it, ECharts might choose decimal intervals (0.5, 1.5, ...) when values are small, which doesn't make sense for integer test counts.

#### Right Y Axis (index 1) — Pass Rate %

```js
{
  type: 'value',
  min: 0,                 // 0%
  max: 100,               // 100%
  interval: 25,           // Ticks at 0, 25, 50, 75, 100
  axisLabel: {
    fontFamily: font,
    fontSize: 11,
    color: '#409EFF',     // Blue — matches the pass-rate line color
    formatter: '{value}%'  // Append % to each tick label
  },
  axisLine: { show: false },
  axisTick: { show: false },
  splitLine: { show: false }  // No grid lines — avoids visual clutter from two overlapping grids
}
```

**`splitLine: { show: false }`** — only the left axis shows grid lines, preventing visual noise from two overlapping grids.

### Series (Stacked Bars + Line)

The chart has **3–4 series** depending on whether abort data exists:

#### 通過 (Pass) — Bar (line 182–198)

```js
{
  name: '通過',
  type: 'bar',
  stack: 'total',          // Stacked on top of each other
  yAxisIndex: 0,           // Uses left Y axis
  data: data.map(d => d.pass),
  itemStyle: { color: '#67C23A' },           // Element Plus success green
  emphasis: { itemStyle: { color: '#529b2e' } },  // Darker on hover
  label: {
    show: itemCount <= 14,  // Only show when ≤14 dates (avoids clutter)
    position: 'inside',     // Label inside the bar
    formatter: p => p.value > 0 ? p.value : ''  // Hide "0" labels
  }
}
```

- **`stack: 'total'`** groups this series with other bars that share the same stack ID. Bars stack vertically — the total height equals the sum of all stacked series for that date.
- **`position: 'inside'`** places the numeric label inside the bar rectangle, centered.

#### 失敗 (Fail) — Bar (line 199–216)

```js
{
  name: '失敗',
  type: 'bar',
  stack: 'total',
  yAxisIndex: 0,
  data: data.map(d => d.fail),
  itemStyle: {
    color: '#F56C6C',                                              // Element Plus danger red
    borderRadius: hasAbort ? [0, 0, 0, 0] : [3, 3, 0, 0]         // Conditional rounding
  },
  // ...
}
```

**Conditional `borderRadius`:**
- When there IS abort data → `[0, 0, 0, 0]` (no rounding) because this bar is not the topmost in the stack.
- When there is NO abort data → `[3, 3, 0, 0]` (rounded top-left and top-right) because this bar IS the topmost — rounding only the top gives a polished look.

`borderRadius` array format: `[topLeft, topRight, bottomRight, bottomLeft]`.

#### 中止 (Abort) — Bar (conditional, line 217–233)

```js
...(hasAbort ? [{
  name: '中止',
  type: 'bar',
  stack: 'total',
  yAxisIndex: 0,
  data: data.map(d => d.abort),
  itemStyle: { color: '#E6A23C', borderRadius: [3, 3, 0, 0] },  // Warning amber, rounded top
  // ...
}] : [])
```

- **Conditional inclusion via spread operator:** The ternary operator returns either a one-element array (spread into the parent array) or an empty array (spread adds nothing).
- This bar always sits at the top of the stack, so it always gets rounded top corners.
- Color `#E6A23C` is Element Plus's warning amber.

#### 通過率% (Pass Rate) — Line (line 234–246)

```js
{
  name: '通過率%',
  type: 'line',
  yAxisIndex: 1,           // Uses the RIGHT Y axis (0–100%)
  data: passRates,         // Array of numbers or nulls
  smooth: true,            // Bezier curve interpolation
  symbol: 'circle',        // Data point marker shape
  symbolSize: itemCount > 20 ? 4 : 7,  // Smaller dots when many dates
  lineStyle: { color: '#409EFF', width: 2 },        // Element Plus primary blue
  itemStyle: { color: '#409EFF', borderColor: '#fff', borderWidth: 2 },
  connectNulls: false,     // Break the line at null values
  z: 10                    // Render on top of bars
}
```

- **`yAxisIndex: 1`** binds this line to the right Y axis (0–100% scale).
- **`smooth: true`** uses cubic Bezier curves instead of straight line segments.
- **`connectNulls: false`** — when a day has zero total tests (producing `null`), the line is broken rather than connecting across the gap. This correctly represents "no data" rather than interpolating.
- **`z: 10`** raises the line's z-index above the stacked bars, ensuring it's always visible.

**`passRates` calculation** (line 59–61):
```js
const passRates = data.map(d =>
  d.total > 0 ? parseFloat((d.pass / d.total * 100).toFixed(1)) : null
)
```
- Returns `null` for days with zero tests (no pass rate to show).
- Uses `toFixed(1)` for one decimal place, then `parseFloat()` to convert the string back to a number (ECharts requires numbers, not strings, for `type: 'value'` axes).

---

## Responsive Adaptation Logic

The chart dynamically adjusts its layout based on the number of date entries:

| Condition | X-axis rotation | Date format | Bottom grid | Symbol size | Labels visible |
|-----------|----------------|-------------|-------------|-------------|----------------|
| ≤ 7 dates | 0° | `YYYY-MM-DD` | 44px | 7px | Yes |
| 8–14 dates | 30° | `MM-DD` | 68px | 7px | Yes |
| 15–20 dates | 45° | `MM-DD` | 68px | 7px | No |
| > 20 dates | 45° | `MM-DD` | 68px | 4px | No |

```js
const xRotate = itemCount > 14 ? 45 : itemCount > 7 ? 30 : 0      // Line 64
const xFormatter = value => itemCount > 7 ? value.slice(5) : value // Line 65
```

- **`value.slice(5)`** removes the first 5 characters (`YYYY-`) from the ISO date string, leaving `MM-DD`.
- **Bar labels** are hidden when `itemCount > 14` (`show: itemCount <= 14`) because they'd overlap.
- **Line symbol dots** shrink when `itemCount > 20` (`symbolSize: itemCount > 20 ? 4 : 7`).

---

## Memory Leak Prevention

The composable uses **two cleanup hooks** to ensure resources are freed:

```js
onBeforeRouteLeave(() => { disposeChart() })   // Line 261
onUnmounted(() => { disposeChart() })           // Line 262
```

| Hook | When it fires | Why both are needed |
|------|---------------|---------------------|
| `onBeforeRouteLeave` | Before navigating to a different route | In Vue Router with `<keep-alive>`, a component might not immediately unmount when leaving a route. This guard ensures cleanup happens regardless. |
| `onUnmounted` | When the component instance is destroyed | Covers the case where the component is destroyed for other reasons (e.g., `v-if` condition becomes false, parent re-renders without this child). |

**What `disposeChart()` cleans up:**
1. Removes the `window.resize` event listener (prevents the handler from firing on a disposed chart).
2. Calls `chartInstance.dispose()` which frees:
   - Internal rendering context (Canvas 2D context or SVG DOM).
   - Internal event handlers (mouse, touch, etc.).
   - Internal timers (animations, transitions).
3. Sets `chartInstance.value = null` so any delayed/queued calls won't crash.

---

## Usage Example (TestResults.vue)

```js
// In TestResults.vue setup():

// 1. Get sessions from the history composable
const { sessions: historySessions, ... } = useTestHistory()

// 2. Destructure the timeline composable
const { chartRef, initChart, updateChart } = useTestTimeline(historySessions)

// 3. In template: bind chartRef to a div
// <div ref="chartRef" style="width:100%;height:400px;"></div>

// 4. Watch for session changes and update/re-init the chart
watch(historySessions, async (newVal, oldVal) => {
  const wasEmpty = !oldVal || oldVal.length === 0
  const nowHasData = newVal && newVal.length > 0
  if (wasEmpty && nowHasData) {
    await nextTick()
    setTimeout(initChart, CHART_INIT_DELAY_MS)  // Delay ensures DOM is ready
  } else if (activeTab.value === 'history') {
    updateChart()
  }
}, { deep: true })
```

**Why `setTimeout(initChart, CHART_INIT_DELAY_MS)` instead of just `nextTick()`?**

When switching from an empty state to a data-populated state, the container `<div>` may exist in the DOM but might not have its final layout dimensions computed yet. A small delay ensures the container has explicit width/height before ECharts tries to initialize. Without it, ECharts may render a zero-dimension chart.
