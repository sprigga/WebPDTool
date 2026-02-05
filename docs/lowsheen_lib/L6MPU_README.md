# L6MPU 測試工具組文檔

## 目錄

- [概述](#概述)
- [硬體架構](#硬體架構)
- [工具組成](#工具組成)
- [快速開始](#快速開始)
- [測試場景](#測試場景)
- [常見問題](#常見問題)

## 概述

L6MPU 是基於 **NXP i.MX8M Plus** 處理器的嵌入式 Linux 系統，用於工業控制、POS 系統或 AMR/AGV 機器人應用。本工具組提供完整的製造測試解決方案，涵蓋網路、LTE、UART、觸控螢幕等功能驗證。

**處理器規格:**
- ARM Cortex-A53 四核心
- Neural Processing Unit (NPU)
- 4x UART, 2x Ethernet, USB, PCIe
- 支援 LTE/4G 模組擴充

## 硬體架構

```
┌─────────────────────────────────────────┐
│         L6MPU (i.MX8M Plus)             │
│  ┌─────────────────────────────────┐   │
│  │  Linux (Yocto/Buildroot)        │   │
│  │  - SSH Server (port 22)         │   │
│  │  - at_cmd_task (LTE control)    │   │
│  │  - NPI_tool (test scripts)      │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌──────┐  ┌──────┐  ┌──────┐         │
│  │UART1 │  │UART4 │  │ USB3 │         │
│  │ttymxc│  │ttymxc│  │ttyUSB│         │
│  │  0   │  │  3   │  │  3   │         │
│  └───┬──┘  └───┬──┘  └───┬──┘         │
│      │         │          │            │
│  ┌───┴────┐ ┌─┴────┐ ┌───┴────┐       │
│  │ eth0   │ │ eth1 │ │  LTE   │       │
│  │(PLC1)  │ │(PLC2)│ │ Module │       │
│  └────────┘ └──────┘ └────────┘       │
└─────────────────────────────────────────┘
         │         │          │
         ↓         ↓          ↓
    ┌────────────────────────────┐
    │   測試 PC                   │
    │   - SSH Client              │
    │   - Serial Port (COM3-10)   │
    │   - Python + Paramiko       │
    └────────────────────────────┘
```

## 工具組成

本工具組包含三個 Python 腳本，位於 `src/lowsheen_lib/L6MPU/` 目錄:

### 1. ssh_cmd.py - 通用 SSH 測試工具

**用途:** 執行 SSH 遠端指令、LTE 狀態查詢、網路測試

**主要功能:**
- LTE 模組 AT 指令查詢 (透過 microcom)
- PLC 網路連通性測試 (ping)
- 一般 Linux 指令執行
- 操作員確認測試 (顯示圖片)

**詳細文檔:** [L6MPU_ssh_cmd_API_Analysis.md](L6MPU_ssh_cmd_API_Analysis.md)

---

### 2. ssh_comport.py - SSH + 串列埠混合工具

**用途:** 結合 SSH 和本地串列埠的測試，主要用於 AT 指令測試

**主要功能:**
- 專用 AT 指令任務 (at_cmd_task)
- SSH 指令執行
- 本地串列埠讀取
- 操作員確認測試

**詳細文檔:** [L6MPU_ssh_comport_API_Analysis.md](L6MPU_ssh_comport_API_Analysis.md)

---

### 3. POSssh_cmd.py - POS 系統專用工具

**用途:** UART 回傳測試、LTE 完整初始化

**主要功能:**
- UART 串列埠回傳驗證 (loopback)
- LTE 模組完整配置流程
- stty 串列埠參數設定
- 串列埠資料收發測試

**詳細文檔:** [L6MPU_POSssh_cmd_API_Analysis.md](L6MPU_POSssh_cmd_API_Analysis.md)

## 快速開始

### 環境需求

**測試 PC (Windows/Linux):**
```bash
# Python 套件
uv pip install paramiko pyserial PyQt5 numpy scipy

# 或使用 requirement.txt
uv pip install -r requirement.txt
```

**L6MPU 設備:**
- SSH 服務已啟動
- root 免密碼登入 (或設定密碼)
- 必要工具: microcom, at_cmd_task, stty

### 基本測試流程

#### 1. 檢查 SSH 連線

```bash
# 測試連線
ssh root@192.168.5.1 "uname -a"

# 預期輸出
Linux imx8mp 5.15.71 #1 SMP PREEMPT ... aarch64 GNU/Linux
```

#### 2. 執行簡單指令測試

```bash
uv run python src/lowsheen_lib/L6MPU/ssh_cmd.py \
  192.168.5.1 \
  "command:hostname"
```

#### 3. LTE 模組測試

```bash
uv run python src/lowsheen_lib/L6MPU/ssh_comport.py \
  192.168.5.1 \
  "ATcommand:AT+CPIN?" \
  COM3 \
  115200
```

#### 4. UART 回傳測試

```bash
uv run python src/lowsheen_lib/L6MPU/POSssh_cmd.py \
  192.168.5.1 \
  "command:cat /dev/ttymxc0 > /outout &" \
  COM10 \
  115200
```

## 測試場景

### 場景 1: 生產線快速驗證

**目標:** 驗證基本功能 (網路、LTE、UART)

```bash
# 1. 網路測試
uv run python ssh_cmd.py 192.168.5.1 PLC1_PING

# 2. LTE SIM 卡
uv run python ssh_comport.py 192.168.5.1 "ATcommand:AT+CPIN?" COM3 115200

# 3. UART1 回傳
uv run python POSssh_cmd.py 192.168.5.1 "command:cat /dev/ttymxc0 > /outout &" COM10 115200
```

**預期時間:** 約 30 秒

---

### 場景 2: LTE 模組完整測試

**目標:** 驗證 LTE 模組從初始化到網路註冊

```bash
# 使用 POSssh_cmd.py (包含完整流程)
uv run python POSssh_cmd.py 192.168.5.1 LTE_INIT COM3 115200
```

**測試步驟:**
1. AT+cfun=0 (關閉射頻)
2. AT+cgdcont=1,"IP","internet" (設定 APN)
3. AT+cfun=1 (啟用射頻)
4. 驗證每步驟回應為 "OK"

---

### 場景 3: 觸控螢幕人工測試

**目標:** 需要操作員確認的視覺測試

```bash
uv run python ssh_comport.py \
  192.168.5.1 \
  "Confirmcommand:echo dbg_debug > /proc/ilitek_ctrl" \
  COM3 115200 \
  ./src/lowsheen_lib/L6MPU/touch_test.jpg
```

**測試流程:**
1. 啟動觸控除錯模式
2. 彈出對話框顯示觸控參考圖片
3. 操作員測試觸控功能
4. 點擊確認按鈕完成

---

### 場景 4: 多 UART 並行測試

**目標:** 同時驗證多個 UART 介面

**測試計劃 CSV:**
```csv
項次,品名規格,test_type,extra_params
1,UART1 Loopback,CommandTest,"{'command': 'uv run python POSssh_cmd.py 192.168.5.1 \"command:cat /dev/ttymxc0 > /outout &\" COM10 115200'}"
2,UART4 Loopback,CommandTest,"{'command': 'uv run python POSssh_cmd.py 192.168.5.1 \"command:cat /dev/ttymxc3 > /outout &\" COM8 115200'}"
```

## 功能對照表

| 功能 | ssh_cmd.py | ssh_comport.py | POSssh_cmd.py |
|------|:----------:|:--------------:|:-------------:|
| SSH 指令執行 | ✓ | ✓ | ✓ |
| LTE 狀態查詢 | ✓ | - | - |
| LTE 完整初始化 | - | - | ✓ |
| AT 指令 (microcom) | ✓ | - | - |
| AT 指令 (at_cmd_task) | - | ✓ | - |
| 本地串列埠讀取 | - | ✓ | ✓ |
| UART 回傳測試 | - | - | ✓ |
| PLC 網路測試 | ✓ | - | - |
| 操作員確認對話框 | ✓ | ✓ | ✓ |
| stty 參數設定 | - | - | ✓ |

## 工具選擇指南

### 我應該用哪個工具?

```
┌─────────────────────────────────────┐
│  需要本地串列埠?                     │
└───────┬─────────────────────────────┘
        │
    ┌───┴───┐
    NO      YES
    │       │
    │   ┌───┴────────────────────────┐
    │   │  測試 UART 回傳?            │
    │   └───┬────────────────────────┘
    │       │
    │   ┌───┴───┐
    │   NO      YES
    │   │       │
    │   │       └──> POSssh_cmd.py
    │   │
    │   └──> ssh_comport.py
    │
    └──> ssh_cmd.py
```

**簡單判斷:**
- 只需 SSH 遠端執行 → `ssh_cmd.py`
- AT 指令 + 本地監聽 → `ssh_comport.py`
- UART 收發驗證 → `POSssh_cmd.py`

## 常見問題

### Q1: SSH 連線失敗

**錯誤訊息:**
```
Exception!!
socket.timeout: timed out
```

**解決方法:**
1. 檢查網路連線: `ping 192.168.5.1`
2. 確認 SSH 服務: `ssh root@192.168.5.1`
3. 檢查防火牆設定
4. 驗證 IP 位址是否正確

---

### Q2: 串列埠被佔用

**錯誤訊息:**
```
Failed to connect to the serial port: [Errno 5] Access is denied
```

**解決方法:**

**Windows:**
```cmd
# 查看串列埠占用
mode COM3

# 關閉占用程式 (裝置管理員 → 連接埠)
```

**Linux:**
```bash
# 查看占用程序
lsof /dev/ttyUSB0

# 釋放串列埠
sudo killall -9 <process_name>

# 修改權限
sudo chmod 666 /dev/ttyUSB0
```

---

### Q3: LTE 模組無回應

**問題:** AT 指令沒有輸出或超時

**檢查步驟:**
1. 確認 SIM 卡已插入
2. 檢查 USB 裝置: `ls -l /dev/ttyUSB*`
3. 手動測試:
   ```bash
   ssh root@192.168.5.1
   microcom -t 2000 -s 115200 /dev/ttyUSB3
   AT+CPIN?
   ```
4. 檢查 LTE 模組電源

---

### Q4: UART 回傳測試失敗

**問題:** POSssh_cmd.py 沒有接收到資料

**除錯步驟:**

**1. 檢查線路連接**
```
PC COM10 ─┬─ TX ──> RX ─┐
          └─ GND ─────── GND
                         │
              DUT UART1 ─┘
```

**2. 手動測試 UART**
```bash
# DUT 端
cat /dev/ttymxc0

# PC 端 (另一個終端)
echo "TEST" > COM10
```

**3. 檢查 stty 設定**
```bash
stty < /dev/ttymxc0 -a
```

---

### Q5: 操作員對話框無法顯示

**問題:** PyQt5 視窗不出現

**原因:**
- 沒有圖形環境 (SSH 遠端執行)
- 缺少 DISPLAY 環境變數

**解決方法:**
```bash
# Linux 設定 DISPLAY
export DISPLAY=:0

# Windows 必須在本地執行 (不能透過 SSH)
# 使用 RDP 或 VNC 遠端桌面
```

---

### Q6: 如何修改測試資料?

**問題:** 想用不同的字串測試 UART

**修改 POSssh_cmd.py:**
```python
# 第 209 行
comport_send(ser,'Hello1\n',1)

# 改為
comport_send(ser,'MyTestData\n',1)
```

或建立參數化版本:
```python
test_data = sys.argv[5] if len(sys.argv) > 5 else 'Hello1\n'
comport_send(ser, test_data, 1)
```

## 進階配置

### SSH 免密碼登入設定

**1. 產生 SSH 金鑰 (PC 端)**
```bash
ssh-keygen -t rsa -b 2048
```

**2. 複製公鑰到 DUT**
```bash
ssh-copy-id root@192.168.5.1
```

**3. 測試**
```bash
ssh root@192.168.5.1  # 不需輸入密碼
```

---

### 自動化測試腳本

**批次測試所有功能:**
```bash
#!/bin/bash
# test_l6mpu.sh

IP="192.168.5.1"
COM_LTE="COM3"
COM_UART1="COM10"
BAUD="115200"

echo "=== L6MPU 自動化測試 ==="

echo "[1/4] 測試 PLC1 網路..."
uv run python ssh_cmd.py $IP PLC1_PING

echo "[2/4] 測試 LTE SIM 卡..."
uv run python ssh_comport.py $IP "ATcommand:AT+CPIN?" $COM_LTE $BAUD

echo "[3/4] 測試 LTE 初始化..."
uv run python POSssh_cmd.py $IP LTE_INIT $COM_LTE $BAUD

echo "[4/4] 測試 UART1 回傳..."
uv run python POSssh_cmd.py $IP "command:cat /dev/ttymxc0 > /outout &" $COM_UART1 $BAUD

echo "=== 測試完成 ==="
```

**執行:**
```bash
chmod +x test_l6mpu.sh
./test_l6mpu.sh
```

## 檔案清單

```
src/lowsheen_lib/L6MPU/
├── ssh_cmd.py                 # 通用 SSH 測試工具
├── ssh_comport.py             # SSH + 串列埠混合工具
├── POSssh_cmd.py              # POS 系統專用工具
├── blight0.jpg                # 螢幕亮度參考圖
├── touch_test.jpg             # 觸控測試參考圖
├── side_button.jpg            # 側邊按鈕位置圖
├── imx-boot-*.bin-flash_evk   # Bootloader 映像檔
├── imx-image-*.wic.zst        # 系統映像檔
└── uuu.exe                    # NXP 燒錄工具

docs/lowsheen_lib/
├── L6MPU_README.md            # 本文件
├── L6MPU_ssh_cmd_API_Analysis.md
├── L6MPU_ssh_comport_API_Analysis.md
└── L6MPU_POSssh_cmd_API_Analysis.md
```

## 版本資訊

- **文檔版本:** 1.0.0
- **最後更新:** 2025-02-04
- **適用韌體:** i.MX8MP Linux 5.15.x
- **相容 PDTool4:** v0.7.0+

## 參考資源

### 官方文檔
- [i.MX8M Plus 處理器](https://www.nxp.com/products/processors-and-microcontrollers/arm-processors/i-mx-applications-processors/i-mx-8-applications-processors/i-mx-8m-plus-arm-cortex-a53-machine-learning-vision-multimedia-and-industrial-iot:IMX8MPLUS)
- [i.MX8MP 參考手冊](https://www.nxp.com/docs/en/reference-manual/IMX8MPRM.pdf)

### Python 套件
- [Paramiko 文檔](http://docs.paramiko.org/)
- [PySerial 文檔](https://pyserial.readthedocs.io/)
- [PyQt5 文檔](https://www.riverbankcomputing.com/static/Docs/PyQt5/)

### 通訊協定
- [AT 指令參考](https://www.developersHome.com/sms/atCommandsIntro.asp)
- [UART 通訊原理](https://en.wikipedia.org/wiki/Universal_asynchronous_receiver-transmitter)

## 技術支援

如遇到問題，請提供以下資訊:
1. 使用的工具 (ssh_cmd/ssh_comport/POSssh_cmd)
2. 完整的命令列參數
3. 錯誤訊息 (完整輸出)
4. DUT IP 位址和網路狀態
5. 串列埠名稱和占用狀態
6. 相關硬體連接圖

**聯繫方式:** 請透過 GitHub Issues 回報問題
