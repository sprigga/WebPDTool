# 沙箱配置參考

## 完整配置示例

```json
{
  "sandbox": {
    "enabled": true,
    "mode": "autoAllow",
    "allowUnsandboxedCommands": true,
    "filesystem": {
      "allowWrite": ["~/.kube", "//tmp/build"],
      "denyWrite": ["/system/config"],
      "denyRead": ["/secrets"],
      "allowUnixSockets": ["/var/run/docker.sock"]
    },
    "network": {
      "allowedDomains": ["github.com", "api.example.com"],
      "allowManagedDomainsOnly": false,
      "httpProxyPort": 8080,
      "socksProxyPort": 8081
    },
    "excludedCommands": ["docker", "watchman"]
  }
}
```

## 配置參數說明

### 頂層參數

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `enabled` | boolean | `false` | 是否啟用沙箱 |
| `mode` | string | `"autoAllow"` | 沙箱模式: `"autoAllow"` 或 `"regular"` |
| `allowUnsandboxedCommands` | boolean | `true` | 是否允許逃生艙機制 |
| `excludedCommands` | array | `[]` | 在沙箱外運行的命令列表 |

### 檔案系統參數 (`filesystem`)

| 參數 | 類型 | 說明 |
|------|------|------|
| `allowWrite` | array | 允許寫入的路徑列表 |
| `denyWrite` | array | 拒絕寫入的路徑列表 |
| `denyRead` | array | 拒絕讀取的路徑列表 |
| `allowUnixSockets` | array | 允許存取的 Unix socket 路徑 |

**路徑前綴規則:**

| 前綴 | 解析方式 | 範例 |
|------|----------|------|
| `//` | 檔案系統根目錄 | `//tmp/build` → `/tmp/build` |
| `~/` | 使用者主目錄 | `~/.kube` → `$HOME/.kube` |
| `/` | 設定檔案所在目錄 | `/build` → `$SETTINGS_DIR/build` |
| `./` 或無 | 相對路徑 | `./output` |

### 網路參數 (`network`)

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `allowedDomains` | array | `[]` | 允許存取的域名列表 |
| `allowManagedDomainsOnly` | boolean | `false` | 是否只允許清單中的域名 (拒絕其他) |
| `httpProxyPort` | number | - | 自訂 HTTP 代理埠 |
| `socksProxyPort` | number | - | 自訂 SOCKS 代理埠 |

## Settings 順序

當在多個 settings scopes 中定義時，陣列會被 **合併**:

1. Global settings (使用者層級)
2. Project settings (專案層級)

例如，如果全局設定允許 `//opt/company-tools`，專案設定新增 `~/.kube`，則兩個路徑都包含在最終配置中。

## 安全建議配置

### 開發環境

```json
{
  "sandbox": {
    "enabled": true,
    "mode": "autoAllow",
    "filesystem": {
      "allowWrite": ["~/.kube", "~/.aws", "//tmp"]
    },
    "network": {
      "allowedDomains": ["github.com", "pypi.org", "npmjs.com", "docker.io"]
    }
  }
}
```

### 生產環境 (更嚴格)

```json
{
  "sandbox": {
    "enabled": true,
    "mode": "regular",
    "allowUnsandboxedCommands": false,
    "filesystem": {
      "denyWrite": ["~/.ssh", "/etc"],
      "denyRead": ["/secrets", "~/.aws/credentials"]
    },
    "network": {
      "allowedDomains": ["github.com"],
      "allowManagedDomainsOnly": true
    }
  }
}
```

## 與權限規則的整合

沙箱設定與權限規則合併：

| 目的 | 沙箱設定 | 權限規則 |
|------|----------|----------|
| 控制檔案讀取 | `filesystem.denyRead` | `Read` 拒絕規則 |
| 控制檔案寫入 | `filesystem.allowWrite/denyWrite` | `Edit` 拒絕規則 |
| 控制網路存取 | `network.allowedDomains` | `WebFetch` 規則 |

兩者的路徑和域名列表會被合併到最終配置中。
