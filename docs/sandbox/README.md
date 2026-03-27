# Claude Code Sandboxing 使用指南

**根據官方文檔整理**: https://code.claude.com/docs/zh-TW/sandboxing

## 概述

Claude Code 具有原生沙箱化功能，為代理執行提供更安全的環境，同時減少對持續權限提示的需求。沙箱化不是要求每個 bash 命令的權限，而是預先建立定義的邊界，讓 Claude Code 能夠以降低風險的方式更自由地工作。

## 為什麼沙箱化很重要

### 傳統權限模式的問題

- **批准疲勞**: 重複點擊「批准」可能導致使用者對他們批准的內容關注度降低
- **生產力降低**: 持續的中斷會減慢開發工作流程
- **自主性受限**: 當等待批准時，Claude Code 無法高效工作

### 沙箱化的解決方案

1. **定義清晰的邊界**: 精確指定 Claude Code 可以存取的目錄和網路主機
2. **減少權限提示**: 沙箱內的安全命令不需要批准
3. **維持安全性**: 嘗試存取沙箱外的資源會觸發立即通知
4. **啟用自主性**: Claude Code 可以在定義的限制內更獨立地運行

## 入門

### 先決條件

#### macOS
沙箱化使用內建的 Seatbelt 框架，開箱即用。

#### Linux 和 WSL2
首先安裝所需的套件：

```bash
# Ubuntu/Debian
sudo apt-get install bubblewrap socat

# Fedora
sudo dnf install bubblewrap socat
```

**注意**: 不支援 WSL1，因為 bubblewrap 需要僅在 WSL2 中可用的核心功能。

### 啟用沙箱化

執行 `/sandbox` 命令來啟用沙箱化：

```
/sandbox
```

這會開啟一個選單，您可以在其中選擇沙箱模式。如果缺少所需的依賴項，選單會顯示您平台的安裝說明。

## 沙箱模式

Claude Code 提供兩種沙箱模式：

### 1. 自動允許模式 (Auto-Allow Mode)
- Bash 命令將嘗試在沙箱內運行，並自動允許而無需權限
- 無法沙箱化的命令會回退到常規權限流程
- 您配置的明確詢問/拒絕規則始終被尊重

### 2. 常規權限模式 (Regular Permission Mode)
- 所有 bash 命令都通過標準權限流程進行，即使沙箱化也是如此
- 提供更多控制，但需要更多批准

**重要**: 自動允許模式獨立於您的權限模式設定工作。即使您不在「接受編輯」模式中，當啟用自動允許時，沙箱化 bash 命令也會自動運行。

## 沙箱如何運作

### 檔案系統隔離

沙箱化 bash 工具將檔案系統存取限制在特定目錄：

| 行為 | 說明 |
|------|------|
| **預設寫入** | 對目前工作目錄及其子目錄的讀取和寫入存取 |
| **預設讀取** | 對整個電腦的讀取存取，除了某些被拒絕的目錄 |
| **被阻止的存取** | 無法在沒有明確權限的情況下修改目前工作目錄外的檔案 |

這些限制在作業系統級別強制執行：
- **macOS**: 使用 Seatbelt
- **Linux/WSL2**: 使用 bubblewrap

### 網路隔離

網路存取通過在沙箱外運行的代理伺服器進行控制：

- **域名限制**: 只能存取已批准的域名
- **使用者確認**: 新的域名請求會觸發權限提示
- **自訂代理支援**: 進階使用者可以在出站流量上實施自訂規則
- **全面覆蓋**: 限制適用於所有指令碼、程式和由命令產生的子流程

## 配置沙箱化

通過 `settings.json` 檔案自訂沙箱行為。

### 授予子流程對特定路徑的寫入存取

預設情況下，沙箱化命令只能寫入目前工作目錄。如果子流程命令需要寫入專案目錄外，請使用 `sandbox.filesystem.allowWrite`:

```json
{
  "sandbox": {
    "enabled": true,
    "filesystem": {
      "allowWrite": ["~/.kube", "//tmp/build"]
    }
  }
}
```

### 路徑前綴

| 前綴 | 含義 | 範例 |
|------|------|------|
| `//` | 從檔案系統根目錄的絕對路徑 | `//tmp/build` → `/tmp/build` |
| `~/` | 相對於主目錄 | `~/.kube` → `$HOME/.kube` |
| `/` | 相對於設定檔案的目錄 | `/build` → `$SETTINGS_DIR/build` |
| `./` 或無前綴 | 相對路徑 | `./output` |

### 其他配置選項

```json
{
  "sandbox": {
    "enabled": true,
    "filesystem": {
      "allowWrite": ["~/.kube"],
      "denyWrite": ["/system/config"],
      "denyRead": ["/secrets"]
    },
    "network": {
      "allowedDomains": ["github.com", "api.example.com"],
      "httpProxyPort": 8080,
      "socksProxyPort": 8081
    }
  }
}
```

## 安全優勢

### 防止提示注入

即使攻擊者通過提示注入成功操縱 Claude Code 的行為，沙箱也確保您的系統保持安全：

**檔案系統保護:**
- 無法修改關鍵配置檔案，如 `~/.bashrc`
- 無法修改 `/bin/` 中的系統級檔案
- 無法讀取在權限設定中被拒絕的檔案

**網路保護:**
- 無法將資料洩露到攻擊者控制的伺服器
- 無法從未授權的域名下載惡意指令碼
- 無法對未批准的服務進行意外的 API 呼叫

### 減少攻擊面

沙箱化限制了以下可能造成的損害：
- 惡意依賴項 (具有有害程式碼的 NPM 套件)
- 受損指令碼 (具有安全漏洞的構建指令碼)
- 社交工程 (欺騙使用者執行危險命令)
- 提示注入 (欺騙 Claude 執行危險命令)

## 工具相容性注意事項

- 許多 CLI 工具需要存取某些主機。當您使用這些工具時，它們將請求權限以存取這些主機。
- `watchman` 與在沙箱中運行不相容。如果您正在執行 `jest`，請考慮使用 `jest --no-watchman`
- `docker` 與在沙箱中運行不相容。考慮在 `excludedCommands` 中指定 `docker` 以強制其在沙箱外運行。

## 逃生艙機制

Claude Code 包含一個有意的逃生艙機制，允許命令在必要時在沙箱外運行：

1. 當命令因沙箱限制而失敗時
2. Claude 會被提示分析失敗
3. 可能使用 `dangerouslyDisableSandbox` 參數重試命令
4. 使用此參數的命令通過需要使用者權限執行的常規 Claude Code 權限流程進行

您可以通過設定 `"allowUnsandboxedCommands": false` 來禁用此逃生艙。

## 最佳實踐

1. **從限制性開始**: 從最小權限開始，根據需要擴展
2. **監控日誌**: 檢查沙箱違規嘗試以了解 Claude Code 的需求
3. **使用環境特定配置**: 開發與生產環境的不同沙箱規則
4. **與權限結合**: 將沙箱化與 IAM 策略一起使用以實現全面安全
5. **測試配置**: 驗證您的沙箱設定不會阻止合法工作流程

## 沙箱化與權限的關係

沙箱化和權限是協同工作的互補安全層：

| 特性 | 權限 | 沙箱化 |
|------|------|--------|
| **範圍** | 所有工具 (Bash、Read、Edit、WebFetch、MCP) | 僅 Bash 命令及其子流程 |
| **執行時機** | 工具運行之前 | 作業系統級別強制執行 |
| **控制內容** | 哪些工具可用 | 檔案系統和網路存取 |

## 進階用法

### 自訂代理配置

對於需要進階網路安全的組織：

```json
{
  "sandbox": {
    "network": {
      "httpProxyPort": 8080,
      "socksProxyPort": 8081
    }
  }
}
```

### 開源沙箱運行時

沙箱執行時可作為開源 npm 套件供您在自己的代理專案中使用：

```bash
npx @anthropic-ai/sandbox-runtime <command-to-sandbox>
```

詳細資訊: [GitHub repository](https://github.com/anthropics-experimental/sandbox-runtime)

## 限制

- **效能開銷**: 最小，但某些檔案系統操作可能稍慢
- **相容性**: 某些需要特定系統存取模式的工具可能需要配置調整
- **平台支援**: 支援 macOS、Linux 和 WSL2。不支援 WSL1。計劃提供原生 Windows 支援

## 參考資料

- [Security](https://code.claude.com/docs/zh-TW/security) - 全面的安全功能和最佳實踐
- [Permissions](https://code.claude.com/docs/zh-TW/permissions) - 權限配置和存取控制
- [Settings](https://code.claude.com/docs/zh-TW/settings) - 完整配置參考
