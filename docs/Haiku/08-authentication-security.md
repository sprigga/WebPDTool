# 08 - 認證與安全

## 安全架構概覽

```
User Credentials
    │ username + password
    ▼
├─ Validation (存在性檢查)
├─ Authentication (身份驗證)
│   └─ bcrypt 密碼比對
├─ JWT Token Generation (令牌生成)
│   └─ 包含：user_id, username, role, exp
├─ Token Transmission (傳輸)
│   └─ Authorization header
├─ Token Validation (驗證)
│   └─ 簽名檢查 + 過期檢查
└─ Authorization (授權)
    └─ 基於 role 的訪問控制
```

## JWT 認證流程

### 1. 登入流程

```
前端：POST /api/auth/login
    {
      "username": "engineer1",
      "password": "password123"
    }
         │
         ▼
後端：AuthService.authenticate_user()
    │
    ├─ 查詢資料庫：SELECT * FROM users WHERE username=?
    │
    ├─ 密碼驗證：bcrypt.verify(password, password_hash)
    │       │ (不匹配 → 返回 401)
    │       ▼
    │   (匹配 → 繼續)
    │
    ├─ 生成 JWT token
    │   payload = {
    │       "sub": "engineer1",
    │       "user_id": 2,
    │       "role": "ENGINEER",
    │       "exp": now + 8hours
    │   }
    │
    ├─ 簽名：encode(payload, SECRET_KEY, HS256)
    │
    └─ 返回到前端
         {
           "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
           "token_type": "bearer",
           "user": {
             "id": 2,
             "username": "engineer1",
             "role": "ENGINEER"
           }
         }
         │
         ▼
前端：localStorage.setItem('token', access_token)
     Pinia auth store 儲存 token 和 user
```

### 2. 後續請求流程

```
前端發起請求:
    GET /api/users
         │
         ├─ Axios 請求攔截器:
         │   headers['Authorization'] = 'Bearer ' + token
         │
         ▼
後端：dependencies.get_current_user()
    │
    ├─ 從 Authorization header 提取 token
    │
    ├─ jwt.decode(token, SECRET_KEY, HS256)
    │   │
    │   ├─ 驗證簽名 (使用 SECRET_KEY)
    │   │
    │   ├─ 檢查 exp (是否過期)
    │   │   │ (過期 → 返回 401)
    │   │   ▼
    │   │ (有效 → 繼續)
    │   │
    │   └─ 返回 payload
    │
    ├─ 提取 sub (username) / user_id
    │
    ├─ 查詢資料庫獲取 User 物件
    │
    └─ 返回給 endpoint 處理器
         │
         ▼
    endpoint 訪問 current_user 物件
    (可用於權限檢查、日誌記錄等)
```

### 3. Token 重新整理流程 (可選)

```
Token 即將過期 (remaining < 1h)
    │
    ▼
前端：POST /api/auth/refresh
    {
      "access_token": "當前 token..."
    }
         │
         ▼
後端：驗證 token (仍在有效期內)
    │
    ├─ 解析 payload
    └─ 生成新 token (相同 user_id，新的 exp)
         │
         ▼
前端：更新 localStorage 和 store 裡的 token
```

## 密碼安全管理

### Bcrypt 密碼哈希

```python
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=10  # 安全性和效能平衡
)

# 密碼哈希
def hash_password(password: str) -> str:
    """哈希密碼，存入資料庫"""
    return pwd_context.hash(password)

# 密碼驗證
def verify_password(plain: str, hashed: str) -> bool:
    """驗證使用者輸入的密碼"""
    return pwd_context.verify(plain, hashed)
```

### 密碼策略

```python
# password 必須滿足的條件

def validate_password_strength(password: str) -> bool:
    """
    密碼強度要求:
    - 最少 8 個字元
    - 包含大寫字母
    - 包含小寫字母
    - 包含數字
    - 包含特殊字元 (可選)
    """

    if len(password) < 8:
        raise ValueError("密碼至少需要 8 個字元")

    if not any(c.isupper() for c in password):
        raise ValueError("密碼需要包含大寫字母")

    if not any(c.islower() for c in password):
        raise ValueError("密碼需要包含小寫字母")

    if not any(c.isdigit() for c in password):
        raise ValueError("密碼需要包含數字")

    return True
```

### 預設密碼與強制更改

```python
# 新使用者建立時生成臨時密碼
DEFAULT_PASSWORD = "Temp@" + secrets.token_hex(4)  # 如 Temp@a1b2c3d4

# 首次登入時強制更改密碼
@router.post("/auth/change-password-required")
async def change_password_on_first_login(
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """首次登入強制更改密碼"""
    if not current_user.password_changed:
        # 更新密碼和標誌
        current_user.password_hash = hash_password(new_password)
        current_user.password_changed = True
        await db.commit()
        return {"message": "密碼已更新"}
```

## 基於角色的訪問控制 (RBAC)

### 使用者角色

```python
class UserRole(str, Enum):
    ADMIN = "ADMIN"        # 系統管理員 - 全部權限
    ENGINEER = "ENGINEER"  # 工程師 - 專案和測試權限
    OPERATOR = "OPERATOR"  # 操作員 - 僅執行權限
```

### 權限矩陣

| 操作 | ADMIN | ENGINEER | OPERATOR |
|------|-------|----------|----------|
| 使用者管理 (CRUD) | ✅ | ❌ | ❌ |
| 專案管理 | ✅ | ✅ | ❌ |
| 工站管理 | ✅ | ✅ | ❌ |
| 測試計劃 (CRUD) | ✅ | ✅ | ❌ |
| CSV 匯入 | ✅ | ✅ | ❌ |
| 執行測試 | ✅ | ✅ | ✅ |
| 檢視結果 | ✅ | ✅ | ✅ |
| 匯出資料 | ✅ | ✅ | ✅ |
| 系統配置 | ✅ | ❌ | ❌ |

### 權限檢查實現

```python
# 方式 1: 在 endpoint 上檢查
@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """刪除使用者 - 僅 ADMIN"""

    # 權限檢查
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="只有管理員可以刪除使用者"
        )

    # 不能刪除自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="不能刪除自己"
        )

    # 執行刪除
    user = await db.get(User, user_id)
    await db.delete(user)
    await db.commit()

    return {"message": "使用者已刪除"}

# 方式 2: 使用權限裝飾器
def require_admin(f):
    @wraps(f)
    async def wrapper(*args, current_user=None, **kwargs):
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403)
        return await f(*args, current_user=current_user, **kwargs)
    return wrapper

@router.delete("/users/{user_id}")
@require_admin
async def delete_user(user_id: int, db, current_user):
    # ...
```

## 前端 Token 管理

### Auth Store (Pinia)

```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, logout as apiLogout } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // 狀態
  const token = ref(localStorage.getItem('token') || null)
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  // 計算屬性
  const isAuthenticated = computed(() => !!token.value)

  const isAdmin = computed(() => user.value?.role === 'ADMIN')
  const isEngineer = computed(() => user.value?.role === 'ENGINEER')
  const isOperator = computed(() => user.value?.role === 'OPERATOR')

  // 方法
  async function login(username, password) {
    try {
      const response = await apiLogin(username, password)

      token.value = response.access_token
      user.value = response.user

      // 持久化到 localStorage
      localStorage.setItem('token', response.access_token)
      localStorage.setItem('user', JSON.stringify(response.user))

      return true
    } catch (error) {
      console.error('登入失敗:', error)
      throw error
    }
  }

  async function logout() {
    try {
      await apiLogout()  // 可選，通知伺服器
    } finally {
      token.value = null
      user.value = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }

  function clearAuth() {
    """強制清除認證資訊 (token 失效時)"""
    token.value = null
    user.value = null
    localStorage.clear()
  }

  return {
    token,
    user,
    isAuthenticated,
    isAdmin,
    isEngineer,
    isOperator,
    login,
    logout,
    clearAuth
  }
})
```

### Axios 攔截器

```javascript
// frontend/src/api/client.js

import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:9100',
  timeout: 30000
})

// 請求攔截器 - 新增 JWT token
client.interceptors.request.use(
  config => {
    const authStore = useAuthStore()

    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }

    return config
  },
  error => Promise.reject(error)
)

// 響應攔截器 - 錯誤處理
client.interceptors.response.use(
  response => response.data,

  error => {
    const authStore = useAuthStore()
    const status = error.response?.status
    const data = error.response?.data

    // 401: Unauthorized - token 無效或過期
    if (status === 401) {
      ElMessage.error('認證資訊已過期，請重新登入')
      authStore.clearAuth()
      location.href = '/login'
    }

    // 403: Forbidden - 權限不足
    else if (status === 403) {
      ElMessage.error('您沒有權限訪問此資源')
    }

    // 其他錯誤
    else {
      const message = data?.detail || '請求失敗'
      ElMessage.error(message)
    }

    return Promise.reject(error)
  }
)

export default client
```

## 路由守衛

```javascript
// frontend/src/router/index.js

import { useAuthStore } from '@/stores/auth'

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // requiresAuth 元標記檢查
  if (to.meta.requiresAuth !== false && !authStore.isAuthenticated) {
    next('/login')
    return
  }

  // 角色檢查
  if (to.meta.requiredRole) {
    if (to.meta.requiredRole === 'ADMIN' && !authStore.isAdmin) {
      next('/test-main')
      return
    }
    if (to.meta.requiredRole === 'ENGINEER' &&
        !authStore.isEngineer && !authStore.isAdmin) {
      next('/test-main')
      return
    }
  }

  next()
})

// 路由定義
const routes = [
  {
    path: '/login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/user-manage',
    component: UserManage,
    meta: { requiredRole: 'ADMIN' }
  },
  {
    path: '/test-plan-manage',
    component: TestPlanManage,
    meta: { requiredRole: 'ENGINEER' }  // ADMIN 也可訪問
  },
  {
    path: '/test-main',
    component: TestMain
    // 登入使用者都可訪問
  }
]
```

## API 端點安全

### 依賴注入獲取當前使用者

```python
from dependencies import get_current_user

@router.get("/users")
async def list_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    獲取使用者列表

    自動檢查:
    1. Authorization header 存在
    2. Token 有效且未過期
    3. 提取 user_id 和檢查權限
    """

    # current_user 已自動注入和驗證
    # 可直接使用 current_user.role 等屬性

    if current_user.role != UserRole.ADMIN:
        # 普通使用者只能看自己
        return [current_user]

    # 管理員可看全部
    return await db.query(User).all()
```

## 生產環境配置

### 環境變數

```bash
# .env

# JWT 配置
SECRET_KEY=your-secret-key-at-least-32-characters-long-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480  # 8 小時

# HTTPS (生產必須)
SECURE_SCHEME=https
SECURE_COOKIES=true
```

### HTTPS 和 CORS

```python
# backend/app/main.py

from fastapi.middleware.cors import CORSMiddleware

# 僅允許特定域名訪問
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://webpdtool.company.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# HTTPS 重定向 (在 Nginx 層或 FastAPI)
# 建議在 Nginx 層處理
```

### 密碼策略

```python
PASSWORD_MIN_LENGTH = 12  # 增加到 12 字元
PASSWORD_REQUIRE_SPECIAL_CHARS = True
PASSWORD_REQUIRE_NUMBERS = True
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_EXPIRY_DAYS = 90  # 90 天強制更改
PASSWORD_HISTORY = 5  # 不能重複最近 5 個密碼
```

## 安全檢查清單

### 部署前檢查

- [ ] SECRET_KEY 已更改 (>32 字元)
- [ ] 預設密碼已更改 (admin/engineer/operator)
- [ ] HTTPS 已啟用 (生產環境)
- [ ] CORS 已限制到允許的域名
- [ ] Token 過期時間合理 (建議 8 小時)
- [ ] 資料庫密碼已更改
- [ ] 日誌中不記錄敏感資訊
- [ ] SQL 注入防護檢查 (ORM 保護)
- [ ] CSRF 保護已啟用
- [ ] XSS 防護已驗證

### 維運檢查

- [ ] 定期備份資料庫
- [ ] 監控登入失敗次數 (防暴力破解)
- [ ] 定期更新依賴包
- [ ] 定期審計使用者權限
- [ ] 記錄管理操作日誌
- [ ] 監控 API 異常呼叫

## 常見問題

**Q: Token 過期後怎麼辦？**
A: 前端在獲得 401 時自動跳轉登入頁面。可實現重新整理 token 端點提前續期。

**Q: 如何防止暴力破解？**
A: 實現失敗次數限制（如 5 次失敗後鎖定 15 分鐘）。

**Q: 可以在多個裝置登入嗎？**
A: 當前實現支援。可改為單 token 制（註冊裝置）來限制併發登入。

**Q: 密碼忘記怎麼辦？**
A: 實現郵件重置連結（需額外開發）或管理員強制重置。

## 下一步

- **學習部署**: [09-deployment-devops.md](09-deployment-devops.md)
- **開發指南**: [10-development-guide.md](10-development-guide.md)
- **API 端點**: [06-api-endpoints.md](06-api-endpoints.md)
