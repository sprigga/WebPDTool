# 從 Git 倉庫移除已追蹤的截圖檔案

## 問題描述

`screenshots/` 目錄中存在大量以 `test` 開頭的 `.png` 截圖檔案（共 35 個），這些檔案已被 Git 追蹤並推送到遠端 GitHub 倉庫。需要將它們從版本控制中移除，但保留本地檔案，同時防止未來再次被提交。

### 涉及的檔案類型

- `test_*.png` — 帶底線的截圖（如 `test_results.png`、`test_execution.png`）
- `test*.png` — 不帶底線的截圖（如 `testmain.png`、`testplan_manage.png`）
- `testhistory-*.png` — 測試歷史頁面截圖（23 個）
- `testresults-*.png` — 測試結果頁面截圖（1 個）

---

## 問題分析

### 為什麼不能直接刪除檔案？

直接用 `rm` 刪除檔案後 commit，會同時刪除本地和遠端的檔案。我們的目標是：

1. **本地保留** — 檔案在開發機上仍然存在
2. **遠端移除** — GitHub 倉庫不再包含這些檔案
3. **未來防護** — 新增的同類檔案不會再被誤 commit

### 常見錯誤做法

| 做法 | 問題 |
|------|------|
| `rm screenshots/test*.png` + commit | 本地檔案也會被刪除 |
| 只加 `.gitignore` 不 `git rm --cached` | 已追蹤的檔案仍會被 commit |
| 用 `git rm`（不加 `--cached`） | 同時刪除本地和追蹤記錄 |

---

## 解決步驟

### 步驟 1：確認哪些檔案被 Git 追蹤

```bash
git ls-files --cached screenshots/test*.png
```

這會列出所有已被 Git 追蹤的 `test*.png` 檔案。共找到 35 個。

### 步驟 2：在 `.gitignore` 新增規則

在專案根目錄的 `.gitignore` 中新增：

```gitignore
# Test screenshots in screenshots/ directory
screenshots/test*.png
```

> **注意：** 最初使用的是 `screenshots/test_*.png`（只匹配含底線的），後來修正為 `screenshots/test*.png` 以涵蓋所有 `test` 開頭的檔案（如 `testmain.png`、`testplan_manage.png`）。

### 步驟 3：從 Git index 移除但保留本地檔案

```bash
git rm --cached screenshots/test*.png
```

`git rm --cached` 的作用：
- 從 Git 追蹤中移除（`deleted` 狀態）
- **不刪除**本地實體檔案
- 後續 commit 時會記錄為刪除操作

執行後 `git status` 顯示：

```
Changes to be committed:
  deleted:    screenshots/test_execution.png
  deleted:    screenshots/test_main_nav.png
  ...（共 35 個檔案）

Changes not staged for commit:
  modified:   .gitignore
```

### 步驟 4：一起 Commit .gitignore 和刪除操作

```bash
git add .gitignore
git commit -m "chore: remove test screenshots from repo and add gitignore rule"
```

> **關鍵：** `.gitignore` 的修改和 `git rm --cached` 的結果必須在**同一個 commit** 中，否則其他開發者 pull 後，已追蹤的檔案仍會出現在他們的工作目錄中。

### 步驟 5：推送到遠端

```bash
git push origin main
```

推送後 GitHub 倉庫中的 35 個截圖檔案被移除，但本地檔案完好。

---

## 除錯過程

### 問題 1：`.gitignore` 規則不完整

**現象：** 初始寫的 `screenshots/test_*.png` 無法匹配 `testmain.png`、`testplan_manage.png` 等不含底線的檔案。

**排查：** 使用 `git ls-files --cached screenshots/test*.png` 確認所有被追蹤的檔案，發現有 35 個，其中很多不含底線。

**修正：** 將 glob 模式從 `test_*` 改為 `test*`。

### 問題 2：確認 `.gitignore` 對已追蹤檔案無效

**觀念釐清：** `.gitignore` 只對**未追蹤**的檔案生效。已被 `git add` 或 commit 過的檔案，即使加入 `.gitignore` 仍會被 Git 管控。必須搭配 `git rm --cached` 才能真正停止追蹤。

---

## 總結

| 操作 | 命令 | 效果 |
|------|------|------|
| 查看已追蹤檔案 | `git ls-files --cached <pattern>` | 列出 Git 追蹤中的檔案 |
| 停止追蹤但保留本地 | `git rm --cached <pattern>` | 從 index 移除，本地檔案不變 |
| 防止未來追蹤 | 編輯 `.gitignore` | 新增的同類檔案不再被追蹤 |
| 一起提交 | `git add .gitignore && git commit` | 確保規則和移除同步生效 |
