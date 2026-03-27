# Claude Code 沙箱模式快速啟動

## 1 分鐘啟用沙箱

### Step 1: 安裝依賴 (Linux/WSL2)

```bash
# Ubuntu/Debian
sudo apt-get install bubblewrap socat

# Fedora
sudo dnf install bubblewrap socat
```

**macOS 使用者**: 無需安裝任何東西，開箱即用。

### Step 2: 啟用沙箱

在 Claude Code 中執行：

```
/sandbox
```

### Step 3: 選擇模式

- **自動允許模式**: 沙箱內的命令自動執行，無需批准 (推薦)
- **常規權限模式**: 沙箱內的命令仍需權限批准

## 基本配置示例

### 最小配置 (僅允許工作目錄)

```json
{
  "sandbox": {
    "enabled": true
  }
}
```

### 允許額外寫入路徑

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

### 限制網路存取

```json
{
  "sandbox": {
    "enabled": true,
    "network": {
      "allowedDomains": ["github.com", "pypi.org", "npmjs.com"]
    }
  }
}
```

## 常見問題

### Q: Docker 命令無法在沙箱中運行？

在 `settings.json` 中添加：

```json
{
  "sandbox": {
    "excludedCommands": ["docker"]
  }
}
```

### Q: 如何檢查沙箱是否啟用？

查看 Claude Code 狀態列，應該顯示沙箱狀態。

### Q: 如何允許特定網域？

首次請求時批准，或在配置中預先添加到 `allowedDomains`。

## 配置檔案位置

| 平台 | 配置檔案位置 |
|------|-------------|
| macOS | `~/Library/Application Support/Claude Code/settings.json` |
| Linux | `~/.claude/settings.json` |
| Windows | `%APPDATA%\Claude Code\settings.json` |
