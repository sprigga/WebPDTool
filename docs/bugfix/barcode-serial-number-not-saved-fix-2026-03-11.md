# Bug Fix: 產品序號未寫入資料庫

**Date**: 2026-03-11
**Status**: ✅ Fixed
**Files Modified**: `frontend/src/views/TestMain.vue`

---

## 問題描述

在 `TestMain.vue` 的「測試控制」區塊中，使用者輸入產品序號（例如 `666666`）後按下「開始測試」，資料庫 `test_sessions.serial_number` 欄位卻儲存 `AUTO-1773214047567`（自動生成的時間戳），而不是使用者輸入的 `666666`。

---

## 除錯過程

### Step 1：確認資料庫欄位存在

查看 `backend/app/models/test_session.py`，確認 `serial_number` 欄位已正確定義：

```python
serial_number = Column(String(100), nullable=False, index=True)
```

✅ 欄位存在，排除 schema 問題。

### Step 2：確認 API 端點功能正常

用 curl 直接呼叫 `POST /api/tests/sessions`，傳入 `serial_number: "123456"`：

```bash
curl -s -X POST http://localhost:9100/api/tests/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"serial_number": "123456", "station_id": 1}'
```

回應：`{"id":136,"serial_number":"123456",...}`

資料庫查詢驗證：

```bash
docker exec webpdtool-db mysql -updtool -ppdtool123 webpdtool -e \
  "SELECT id, serial_number FROM test_sessions WHERE serial_number='123456';"
```

結果：`136 | 123456`

✅ API 和 DB 功能正常，問題在前端邏輯。

### Step 3：找出前端 Bug

定位到 `handleStartTest()` 中的序號產生邏輯（`TestMain.vue` 第 1307 行）：

```javascript
// 原本的程式碼（有 bug）
const serialNumber = requireBarcode.value ? barcode.value.trim() : 'AUTO-' + Date.now()
```

**根本原因**：`requireBarcode` 預設為 `false`（第 454 行）。三元運算子邏輯為：
- `requireBarcode=true` → 使用 `barcode.value`
- `requireBarcode=false` → **永遠使用** `AUTO-<timestamp>`

這導致即使使用者有輸入序號，只要 `requireBarcode` 為 `false`，輸入值就會被忽略。

---

## 修正方法

### Bug Fix 1：序號邏輯修正

**檔案**: `frontend/src/views/TestMain.vue` 第 1307 行

```javascript
// 修正前（bug）
const serialNumber = requireBarcode.value ? barcode.value.trim() : 'AUTO-' + Date.now()

// 修正後
// 修正(2026-03-11): 當使用者有輸入序號時，優先使用輸入值；requireBarcode 只控制是否強制需要輸入
const serialNumber = barcode.value.trim() || 'AUTO-' + Date.now()
```

**說明**：使用 `||` 短路運算，`barcode.value.trim()` 有值時優先使用，空字串才 fallback 到自動生成。`requireBarcode` 的職責僅限於「是否禁用空白序號開始測試」，不影響序號來源。

**行為對照表**：

| 條件 | 修正前 | 修正後 |
|------|--------|--------|
| `requireBarcode=false`，輸入 `666666` | `AUTO-<timestamp>` ❌ | `666666` ✅ |
| `requireBarcode=false`，無輸入 | `AUTO-<timestamp>` ✅ | `AUTO-<timestamp>` ✅ |
| `requireBarcode=true`，輸入 `666666` | `666666` ✅ | `666666` ✅ |
| `requireBarcode=true`，無輸入 | 空字串 ❌（阻止開始） | 被按鈕 disabled 阻止 ✅ |

### Bug Fix 2：requireBarcode 改為 UI Checkbox

`requireBarcode` 原本是程式碼內的靜態預設值（`ref(false)`），使用者無法從介面切換。將其改為 Config Panel 中的 checkbox。

**修改位置**：Config Panel 的 checkbox 群組（`TestMain.vue` 第 88-95 行附近）

```html
<!-- 新增「強制序號」checkbox，與既有 SFC、全測模式並排 -->
<el-checkbox
  v-model="requireBarcode"
  size="large"
  style="margin-left: 20px"
>
  強制序號
</el-checkbox>
```

**效果**：
- 未勾選（預設）：空白序號自動生成 `AUTO-<timestamp>`，有輸入則使用輸入值
- 勾選「強制序號」：序號欄位空白時，「開始測試」按鈕被禁用（`:disabled="(requireBarcode && !barcode) || testing"` 既有邏輯已處理）

---

## 相關程式碼

- `frontend/src/views/TestMain.vue:454` — `const requireBarcode = ref(false)`
- `frontend/src/views/TestMain.vue:255` — `:disabled="(requireBarcode && !barcode) || testing"`
- `frontend/src/views/TestMain.vue:1307` — 序號產生邏輯（已修正）
- `backend/app/api/tests.py:48-81` — `POST /api/tests/sessions` 端點
- `backend/app/models/test_session.py:20` — `serial_number` DB 欄位
