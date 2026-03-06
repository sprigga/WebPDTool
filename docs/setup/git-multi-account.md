# Git 多帳號設置指南

## 問題描述

同一台機器需要使用兩個 Git 帳號：
- `sprigga` (email: plin5958tw@gmail.com) — 目前全域預設帳號
- `Polo-Lin-TW` (email: plin5958@gmail.com) — 其他專案使用

## 解決方案：使用 `includeIf` 依目錄自動切換

### 目前設置狀態

全域 `~/.gitconfig` 使用 `sprigga` 作為預設帳號。

`Polo-Lin-TW` 的配置已預先建立於 `~/.gitconfig-polo`：

```ini
[user]
    name = Polo-Lin-TW
    email = plin5958@gmail.com
```

### 當需要在新專案套用 `Polo-Lin-TW` 時

在 `~/.gitconfig` 加入 `includeIf` 區塊，指定目標目錄：

```bash
git config --global --add includeIf."gitdir:~/your-project-dir/".path "~/.gitconfig-polo"
```

或手動編輯 `~/.gitconfig`，加入：

```ini
[includeIf "gitdir:~/your-project-dir/"]
    path = ~/.gitconfig-polo
```

> **注意：** `gitdir:` 路徑末尾的 `/` 是必須的，表示「此目錄及其子目錄」。

### 驗證設定是否生效

在目標 repo 目錄內執行：

```bash
git config user.name
git config user.email
```

應顯示 `Polo-Lin-TW` 和 `plin5958@gmail.com`。

## 其他方案（備用）

### 單一 repo 本地覆蓋

```bash
cd /path/to/repo
git config user.name "Polo-Lin-TW"
git config user.email "plin5958@gmail.com"
```

### 單次 commit 臨時指定

```bash
git -c user.name="Polo-Lin-TW" -c user.email="plin5958@gmail.com" commit -m "message"
```

## GitHub CLI (gh) 帳號管理

### 問題：push 時出現 403 Permission denied

當 gh CLI 登入的帳號與遠端 repo 擁有者不同時，push 會失敗：

```
remote: Permission to sprigga/WebPDTool.git denied to Polo-Lin-TW.
fatal: unable to access '...': The requested URL returned error: 403
```

### 新增帳號登入

```bash
gh auth login
# 選擇 GitHub.com → HTTPS → Login with a web browser
# 複製 one-time code，在瀏覽器完成驗證
```

### 切換 active 帳號

```bash
gh auth switch --user sprigga      # 切換到 sprigga
gh auth switch --user Polo-Lin-TW  # 切換到 Polo-Lin-TW
```

### 確認目前登入狀態

```bash
gh auth status
```

### 推送流程（確保帳號正確）

```bash
gh auth switch --user sprigga
git push origin main
```

---

## Git 設定優先級

命令列 `-c` > 本地 `.git/config` > 全域 `~/.gitconfig` > 系統 `/etc/gitconfig`

> **重要：** GitHub/GitLab 判斷 commit 作者是依 email，所以 email 必須與對應帳號綁定。
