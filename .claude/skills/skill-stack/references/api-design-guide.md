# RESTful API 設計指南

## API 設計原則

### RESTful 資源命名
- 使用複數名詞: `/api/users`, `/api/products`
- 資源層級結構: `/api/users/{id}/orders`
- 使用小寫字母和連字符: `/api/user-profiles`
- 避免動詞: 使用 HTTP 方法表達動作

### HTTP 方法使用
- **GET**: 查詢資源 (不改變狀態)
- **POST**: 創建新資源
- **PUT**: 完整更新資源
- **PATCH**: 部分更新資源
- **DELETE**: 刪除資源

### 狀態碼規範
- **2xx 成功**
  - 200 OK: 請求成功
  - 201 Created: 資源創建成功
  - 204 No Content: 成功但無返回內容
- **4xx 客戶端錯誤**
  - 400 Bad Request: 請求格式錯誤
  - 401 Unauthorized: 未認證
  - 403 Forbidden: 無權限
  - 404 Not Found: 資源不存在
  - 422 Unprocessable Entity: 驗證失敗
- **5xx 伺服器錯誤**
  - 500 Internal Server Error: 伺服器錯誤
  - 503 Service Unavailable: 服務不可用

## FastAPI API 結構範例

### 基本 CRUD 操作

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

router = APIRouter(prefix="/api/users", tags=["users"])

# 列表查詢 (支援分頁)
@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    查詢使用者列表
    - skip: 跳過筆數 (分頁)
    - limit: 每頁筆數
    """
    users = await user_service.get_users(db, skip=skip, limit=limit)
    return users

# 單筆查詢
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """查詢單一使用者"""
    user = await user_service.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# 創建資源
@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """創建新使用者"""
    return await user_service.create_user(db, user=user)

# 完整更新
@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    """完整更新使用者資訊"""
    updated_user = await user_service.update_user(db, user_id=user_id, user=user)
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

# 部分更新
@router.patch("/{user_id}", response_model=UserResponse)
async def partial_update_user(
    user_id: int,
    user: UserPartialUpdate,
    db: AsyncSession = Depends(get_db)
):
    """部分更新使用者資訊"""
    updated_user = await user_service.partial_update_user(db, user_id=user_id, user=user)
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

# 刪除資源
@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """刪除使用者"""
    success = await user_service.delete_user(db, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
```

### Pydantic 模型定義

```python
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

# 基礎模型 (共用欄位)
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None

# 創建模型 (請求)
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

# 更新模型 (請求)
class UserUpdate(UserBase):
    password: Optional[str] = Field(None, min_length=8)

# 部分更新模型 (所有欄位可選)
class UserPartialUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)

# 響應模型
class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True  # Pydantic v2 (舊版為 orm_mode = True)
```

### 認證與授權

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# 獲取當前使用者
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """從 JWT Token 獲取當前使用者"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await user_service.get_user(db, user_id=user_id)
    if user is None:
        raise credentials_exception
    return user

# 檢查使用者是否啟用
async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """檢查使用者是否啟用"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# 使用依賴注入保護 API
@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    """獲取當前登入使用者資訊"""
    return current_user
```

### 登入端點

```python
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

@router.post("/auth/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    使用者登入
    - username: 使用者名稱或 Email
    - password: 密碼
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }
```

## 前端 Axios 整合

### Axios 實例配置

```typescript
// src/utils/request.ts
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

// 創建 axios 實例
const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:9100',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 請求攔截器
service.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    // 添加 Token
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// 響應攔截器
service.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    // 錯誤處理
    if (error.response) {
      const { status, data } = error.response

      switch (status) {
        case 401:
          ElMessage.error('未授權,請重新登入')
          // 清除 Token 並跳轉登入頁
          const userStore = useUserStore()
          userStore.logout()
          break
        case 403:
          ElMessage.error('拒絕訪問')
          break
        case 404:
          ElMessage.error('請求的資源不存在')
          break
        case 422:
          ElMessage.error(data.detail || '資料驗證失敗')
          break
        case 500:
          ElMessage.error('伺服器錯誤')
          break
        default:
          ElMessage.error(data.detail || '請求失敗')
      }
    } else if (error.request) {
      ElMessage.error('網路錯誤,請檢查網路連線')
    }

    return Promise.reject(error)
  }
)

export default service
```

### API 服務封裝

```typescript
// src/api/user.ts
import request from '@/utils/request'

export interface LoginData {
  username: string
  password: string
}

export interface UserInfo {
  id: number
  email: string
  username: string
  full_name?: string
  is_active: boolean
  created_at: string
}

// 登入
export const login = (data: LoginData) => {
  return request({
    url: '/api/auth/login',
    method: 'post',
    data: new URLSearchParams(data), // OAuth2PasswordRequestForm 格式
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  })
}

// 獲取使用者資訊
export const getUserInfo = () => {
  return request<UserInfo>({
    url: '/api/users/me',
    method: 'get',
  })
}

// 獲取使用者列表
export const getUserList = (params?: { skip?: number; limit?: number }) => {
  return request<UserInfo[]>({
    url: '/api/users',
    method: 'get',
    params,
  })
}

// 創建使用者
export const createUser = (data: any) => {
  return request<UserInfo>({
    url: '/api/users',
    method: 'post',
    data,
  })
}

// 更新使用者
export const updateUser = (id: number, data: any) => {
  return request<UserInfo>({
    url: `/api/users/${id}`,
    method: 'put',
    data,
  })
}

// 刪除使用者
export const deleteUser = (id: number) => {
  return request({
    url: `/api/users/${id}`,
    method: 'delete',
  })
}
```

## 錯誤處理最佳實踐

### 自定義異常

```python
# backend/app/exceptions.py
class AppException(Exception):
    """應用程式基礎異常"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class NotFoundException(AppException):
    """資源不存在異常"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)

class UnauthorizedException(AppException):
    """未授權異常"""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)

class ValidationException(AppException):
    """驗證失敗異常"""
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status_code=422)
```

### 全域異常處理器

```python
# backend/main.py
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.exceptions import AppException

app = FastAPI()

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """處理應用程式自定義異常"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """處理未預期的異常"""
    # 記錄錯誤
    logger.error(f"Unexpected error: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )
```

## API 文件最佳實踐

### OpenAPI 標籤組織

```python
from fastapi import FastAPI

app = FastAPI(
    title="My API",
    description="API for My Application",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "users",
            "description": "使用者管理相關 API",
        },
        {
            "name": "auth",
            "description": "認證相關 API",
        },
        {
            "name": "products",
            "description": "產品管理相關 API",
        },
    ]
)
```

### 端點文件撰寫

```python
@router.post(
    "/",
    response_model=UserResponse,
    status_code=201,
    summary="創建新使用者",
    description="創建一個新的使用者帳號。需要提供 email、username 和 password。",
    response_description="成功創建的使用者資訊",
    responses={
        201: {
            "description": "使用者創建成功",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "email": "user@example.com",
                        "username": "johndoe",
                        "full_name": "John Doe",
                        "is_active": True,
                        "created_at": "2024-01-01T00:00:00"
                    }
                }
            }
        },
        422: {"description": "資料驗證失敗"},
    }
)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    創建新使用者帳號

    參數:
    - **email**: 使用者 Email (必填,格式驗證)
    - **username**: 使用者名稱 (必填,3-50字元)
    - **password**: 密碼 (必填,至少8字元)
    - **full_name**: 全名 (可選)

    返回:
    - 創建成功的使用者資訊
    """
    return await user_service.create_user(db, user=user)
```

## 效能優化

### 資料庫查詢優化

```python
# 避免 N+1 查詢問題
from sqlalchemy.orm import selectinload

@router.get("/users-with-orders")
async def get_users_with_orders(db: AsyncSession = Depends(get_db)):
    """一次查詢獲取使用者及其訂單"""
    result = await db.execute(
        select(User).options(selectinload(User.orders))
    )
    users = result.scalars().all()
    return users
```

### 回應快取

```python
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

@router.get("/products")
@cache(expire=60)  # 快取 60 秒
async def get_products(db: AsyncSession = Depends(get_db)):
    """獲取產品列表 (帶快取)"""
    products = await product_service.get_products(db)
    return products
```
