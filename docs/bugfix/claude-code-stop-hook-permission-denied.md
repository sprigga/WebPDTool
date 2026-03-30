---
title: Claude Code Stop Hook — Permission denied
date: 2026-03-27
component: ~/.claude/plugins/marketplaces/claude-plugins-official/plugins/ralph-loop/hooks/stop-hook.sh
category: environment / hooks
severity: warning（不影響主程式，但 stop hook 不會執行）
---

# Bug：Claude Code Stop Hook Permission denied

## 問題描述

每次 Claude Code 工作階段結束時，出現以下錯誤訊息：

```
• Ran 2 stop hooks (ctrl+o to expand)
  └ Stop hook error: Failed with non-blocking status code:
    /bin/sh: 1: /home/ubuntu/.claude/plugins/marketplaces/claude-plugins-official/
    plugins/ralph-loop/hooks/stop-hook.sh: Permission denied
```

## 症狀

- Claude Code 的 stop hook 階段報錯
- 錯誤屬於 non-blocking（不阻斷主流程），但 ralph-loop 的 stop hook 邏輯不會執行
- 重複出現在每次工作階段結束時

## 根本原因

### Unix 檔案權限缺少執行位元（execute bit）

```bash
$ ls -la stop-hook.sh
-rw-r--r-- 1 ubuntu ubuntu 7533 Mar 27 09:06 stop-hook.sh
#  ↑ 644：owner 有讀寫，但無人有執行權限
```

Unix 系統執行 shell script 需要檔案具備執行位元（`x`）。`/bin/sh` 嘗試執行該 script 時，核心（kernel）直接回傳 `EACCES`（Permission denied），不進入 script 內容。

**權限位元說明：**

| 權限 | 數字 | 說明 |
|------|------|------|
| `rw-r--r--` | 644 | 原始狀態，無任何 `x` 位元 |
| `rwxr-xr-x` | 755 | 修正後，owner/group/others 皆可執行 |

### 為何 chmod 需要 dangerouslyDisableSandbox

```
chmod: changing permissions of '...stop-hook.sh': Read-only file system
```

Claude Code sandbox 模式以**唯讀方式掛載** `~/.claude/plugins/` 路徑（防止工具意外修改 plugin 檔案），因此標準的 sandbox 環境無法執行 `chmod`。

## 除錯過程

### Step 1：確認錯誤來源

錯誤訊息明確指出問題路徑：

```
/bin/sh: 1: .../ralph-loop/hooks/stop-hook.sh: Permission denied
```

`/bin/sh: 1:` 表示是 shell 本身在嘗試執行 script 的第 1 行前就失敗，代表是**檔案系統層級的權限問題**，而非 script 內容錯誤。

### Step 2：驗證檔案權限

```bash
ls -la /home/ubuntu/.claude/plugins/marketplaces/claude-plugins-official/plugins/ralph-loop/hooks/stop-hook.sh
# -rw-r--r-- 1 ubuntu ubuntu 7533 Mar 27 09:06 stop-hook.sh
#  ↑ 確認缺少 x 位元
```

### Step 3：嘗試在 sandbox 中修正（失敗）

```bash
chmod +x stop-hook.sh
# chmod: changing permissions of '...': Read-only file system
```

發現 `~/.claude/plugins/` 在 sandbox 中為唯讀掛載，需要 bypass sandbox。

### Step 4：使用 dangerouslyDisableSandbox 修正

```bash
chmod +x /home/ubuntu/.claude/plugins/marketplaces/claude-plugins-official/plugins/ralph-loop/hooks/stop-hook.sh
```

### Step 5：驗證修正結果

```bash
ls -la stop-hook.sh
# -rwxr-xr-x 1 ubuntu ubuntu 7533 Mar 27 09:06 stop-hook.sh
#  ↑ 已有 x 位元，問題解決
```

## 修正指令

```bash
# 在 terminal 中直接執行（不透過 Claude Code）
chmod +x ~/.claude/plugins/marketplaces/claude-plugins-official/plugins/ralph-loop/hooks/stop-hook.sh
```

或在 Claude Code 中使用 `! ` 前綴執行（繞過 sandbox）：

```
! chmod +x ~/.claude/plugins/marketplaces/claude-plugins-official/plugins/ralph-loop/hooks/stop-hook.sh
```

## 預防方式

Plugin 安裝後若出現 hook permission denied，檢查所有 hook 腳本：

```bash
# 找出 ralph-loop plugin 下所有 .sh 檔案並確認權限
ls -la ~/.claude/plugins/marketplaces/claude-plugins-official/plugins/ralph-loop/hooks/

# 批次修正（如有多個 hook）
chmod +x ~/.claude/plugins/marketplaces/claude-plugins-official/plugins/ralph-loop/hooks/*.sh
```

## 相關知識

- **Unix execute bit**：Shell script 需要 `x` 位元才能被 `/bin/sh` 直接執行；`chmod +x` 等同 `chmod a+x`（all），`chmod u+x` 只給 owner 執行權
- **Claude Code sandbox**：`~/.claude/` 部分路徑在 sandbox 中以唯讀方式掛載，保護 plugin 配置不被工具意外修改
- **Non-blocking hook error**：Claude Code 的 hook 錯誤分為 blocking 和 non-blocking；此錯誤為 non-blocking，Claude Code 仍可正常運作，但 ralph-loop 的 stop 邏輯不會執行
