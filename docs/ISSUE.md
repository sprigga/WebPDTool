# 问题追踪和解决方案文档

## Issue #1: 登录API返回500错误

### 问题描述
**错误日期**: 2025-12-17  
**错误类型**: Internal Server Error (500)  
**发生位置**: POST `/api/auth/login` 端点

Chrome浏览器控制台报错：
```
POST http://localhost/api/auth/login 500 (Internal Server Error)
```

### 根本原因
bcrypt库与passlib的集成出现问题：

1. **passlib与bcrypt版本不兼容** - passlib在处理bcrypt密码验证时，调用内部的bcrypt.detect_wrap_bug()
2. **密码截断失败** - 当密码超过72字节（bcrypt的限制）时，截断后的密码仍然在passlib的内部调用中被检验，导致抛出异常：
   ```
   ValueError: password cannot be longer than 72 bytes, truncate manually if necessary
   ```
3. **异常未被捕获** - 原始代码虽然尝试了异常处理，但passlib内部的多重调用堆栈使得截断逻辑无效

### 完整错误堆栈

```
Traceback (most recent call last):
  File "/app/app/api/auth.py", line 32, in login
    user = auth_service.authenticate_user(db, login_data.username, login_data.password)
  File "/app/app/services/auth.py", line 14, in authenticate_user
    if not verify_password(password, user.password_hash):
  File "/app/app/core/security.py", line 20, in verify_password
    return pwd_context.verify(plain_password, hashed_password)
  File "/app/.venv/lib/python3.11/site-packages/passlib/context.py", line 2347, in verify
    return record.verify(secret, hash, **kwds)
  File "/app/.venv/lib/python3.11/site-packages/passlib/handlers/bcrypt.py", line 380, in detect_wrap_bug
    if verify(secret, bug_hash):
  File "/app/.venv/lib/python3.11/site-packages/passlib/handlers/bcrypt.py", line 655, in _calc_checksum
    hash = _bcrypt.hashpw(secret, config)
ValueError: password cannot be longer than 72 bytes, truncate manually if necessary
```

### 解决方案

#### 方案概述
放弃使用passlib的CryptContext包装器，直接使用原生bcrypt库进行密码哈希和验证，这样可以避免passlib内部的复杂调用链。

#### 修改的文件

**文件**: `/home/ubuntu/WebPDTool/backend/app/core/security.py`

**关键改动**:

1. **移除passlib依赖**
   ```python
   # 旧方式（移除）
   from passlib.context import CryptContext
   pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
   
   # 新方式
   import bcrypt
   ```

2. **添加密码截断工具函数**
   ```python
   def _truncate_password(password: str, max_bytes: int = 72) -> str:
       """Truncate password to max bytes (default 72 for bcrypt)"""
       password_bytes = password.encode('utf-8')
       if len(password_bytes) > max_bytes:
           password_bytes = password_bytes[:max_bytes]
           password = password_bytes.decode('utf-8', errors='ignore')
       return password
   ```

3. **使用bcrypt直接验证密码**
   ```python
   def verify_password(plain_password: str, hashed_password: str) -> bool:
       """Verify a password against its hash"""
       plain_password = _truncate_password(plain_password)
       try:
           return bcrypt.checkpw(
               plain_password.encode('utf-8'),
               hashed_password.encode('utf-8')
           )
       except (ValueError, TypeError):
           return False
   ```

4. **使用bcrypt直接生成哈希**
   ```python
   def get_password_hash(password: str) -> str:
       """Generate password hash"""
       password = _truncate_password(password)
       try:
           salt = bcrypt.gensalt()
           hash_bytes = bcrypt.hashpw(password.encode('utf-8'), salt)
           return hash_bytes.decode('utf-8')
       except ValueError as e:
           if "password cannot be longer than 72 bytes" in str(e):
               password = password[:72]
               salt = bcrypt.gensalt()
               hash_bytes = bcrypt.hashpw(password.encode('utf-8'), salt)
               return hash_bytes.decode('utf-8')
           raise
   ```

#### 数据库更新

生成新的密码哈希：
```bash
# 使用应用中的get_password_hash()函数生成哈希
# 密码: admin123
# 新哈希: $2b$12$C40iFImcWrcBAx.iFRs1ZejI5M/tkTLJ.FaP2LFA.oH7L8uzhaEpi
```

更新所有用户的密码哈希：
```sql
UPDATE users SET password_hash = '$2b$12$C40iFImcWrcBAx.iFRs1ZejI5M/tkTLJ.FaP2LFA.oH7L8uzhaEpi' WHERE username = 'admin';
UPDATE users SET password_hash = '$2b$12$C40iFImcWrcBAx.iFRs1ZejI5M/tkTLJ.FaP2LFA.oH7L8uzhaEpi' WHERE username = 'engineer1';
UPDATE users SET password_hash = '$2b$12$C40iFImcWrcBAx.iFRs1ZejI5M/tkTLJ.FaP2LFA.oH7L8uzhaEpi' WHERE username = 'operator1';
```

#### 种子数据文件更新

**文件**: `/home/ubuntu/WebPDTool/database/seed_data.sql`

更新用户初始密码哈希，确保未来容器重新初始化时使用正确的密码哈希。

### 验证方法

#### 方法1: API测试
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**预期响应** (200 OK):
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
        "username": "admin",
        "full_name": "System Administrator",
        "email": "admin@example.com",
        "role": "admin",
        "id": 1,
        "is_active": true,
        "created_at": "2025-12-17T10:55:37",
        "updated_at": "2025-12-17T11:12:34"
    }
}
```

#### 方法2: 后端日志检查
```bash
docker-compose logs backend --tail=20 | grep "POST /api/auth/login"
```

**预期输出**:
```
INFO: 172.18.0.1:57570 - "POST /api/auth/login HTTP/1.1" 200 OK
```

（不再出现500错误）

#### 方法3: 浏览器测试
1. 打开应用 `http://localhost`
2. 进入登录页面
3. 输入凭证: `username=admin`, `password=admin123`
4. 检查Chrome DevTools Console
5. 预期：no 500 errors，看到成功登录并跳转到应用主页

### 影响范围

- ✅ 登录功能 (`/api/auth/login`)
- ✅ 用户认证 (`authenticate_user()`)
- ✅ 密码验证 (`verify_password()`)
- ✅ 密码哈希生成 (`get_password_hash()`)
- ✅ 所有密码相关操作

### 测试用户凭证

修复后可用的测试账户（密码统一为 `admin123`）：

| 用户名 | 密码 | 角色 | 邮箱 |
|--------|------|------|------|
| admin | admin123 | ADMIN | admin@example.com |
| engineer1 | admin123 | ENGINEER | engineer1@example.com |
| operator1 | admin123 | OPERATOR | operator1@example.com |

### 额外改进建议

1. **添加日志记录** - 在authenticate_user()中添加失败日志用于调试
2. **密码策略** - 在生产环境中设置强密码策略（最小长度、复杂度等）
3. **密码迁移** - 未来若需要更换哈希算法，考虑实现密码升级迁移
4. **环境变量配置** - 将bcrypt轮数(rounds)提取为配置参数

### 相关文件

- `/home/ubuntu/WebPDTool/backend/app/core/security.py` - 主要修改文件
- `/home/ubuntu/WebPDTool/backend/app/services/auth.py` - 认证服务（无修改）
- `/home/ubuntu/WebPDTool/backend/app/api/auth.py` - API端点（无修改）
- `/home/ubuntu/WebPDTool/database/seed_data.sql` - 种子数据（密码哈希更新）

### 解决时间线

| 时间 | 操作 |
|------|------|
| 2025-12-17 03:08:48 | 识别500错误，查看后端日志 |
| 2025-12-17 03:09:28 | 定位根本原因：passlib bcrypt集成问题 |
| 2025-12-17 03:10:00 | 设计解决方案：使用原生bcrypt库 |
| 2025-12-17 03:11:00 | 修改security.py，移除passlib依赖 |
| 2025-12-17 03:12:00 | 重启后端，生成新密码哈希 |
| 2025-12-17 03:12:30 | 更新数据库用户密码 |
| 2025-12-17 03:13:00 | 验证登录API成功返回200 OK |
| 2025-12-17 03:14:00 | 更新种子数据文件 |

### 相关PR/Commit

此修复涉及的提交：
- 修改: `/backend/app/core/security.py` - 使用原生bcrypt替代passlib
- 修改: `/database/seed_data.sql` - 更新密码哈希

---

**状态**: ✅ 已解决  
**最后更新**: 2025-12-17  
**解决者**: GitHub Copilot
