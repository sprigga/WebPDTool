# L6MPU POSssh_cmd API 分析文檔

## 概述

`POSssh_cmd.py` 是專為 Point-of-Sale (POS) 系統設計的混合測試工具，用於測試 L6MPU (i.MX8MP) 的 UART 串列埠回傳功能。此工具可同時控制遠端 UART 裝置 (透過 SSH) 和本地串列埠，主要用於驗證雙向串列埠通訊。

**檔案位置**: `src/lowsheen_lib/L6MPU/POSssh_cmd.py`

## 相依套件

```python
import paramiko      # SSH 連線
import time
import numpy as np
import math
import threading
import os
import sys
import serial        # 串列埠通訊
from scipy import optimize as op
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt
```

## 全域變數

```python
sUsername = "root"    # SSH 登入帳號
sPassword = ""        # SSH 密碼
sHostname = ""        # SSH 主機位址
port = 22             # SSH 連接埠
```

## 主要類別

### OPjudge_confirm

操作員確認對話框

#### 建構函式

```python
def __init__(self, ImagePath, content, parent=None)
```

**參數:**
- `ImagePath` (str): 參考圖片路徑
- `content` (str): 對話框訊息
- `parent` (QWidget, optional): 父視窗

#### 方法

```python
def on_click(self)
```
確認按鈕點擊處理，列印 "Yes" 並呼叫 `self.accept()`

```python
def closeEvent(self, event)
```
視窗關閉處理，列印 "No" 並呼叫 `self.reject()`

## 串列埠函數

### get_response(ser, timeout)

**功能:** 從串列埠讀取所有可用資料

```python
def get_response(ser, timeout)
```

**參數:**
- `ser` (serial.Serial): 串列埠物件
- `timeout` (float): 超時時間 (未使用)

**返回:** `bytes` - 串列埠接收資料

**行為:**
- 使用 `ser.read_all()` 讀取緩衝區
- 列印除錯訊息: `"comport get: <data>"`

---

### comport_send(ser, comport_command, timeout)

**功能:** 向串列埠發送指令

```python
def comport_send(ser, comport_command, timeout)
```

**參數:**
- `ser` (serial.Serial): 串列埠物件
- `comport_command` (str): 要發送的指令
- `timeout` (float): 讀取超時時間

**行為:**
1. 設定串列埠超時
2. 編碼並發送指令
3. 列印除錯訊息: `"comport send: <command>"`

**注意:** 此函數不會讀取回應，僅發送資料

## 主要測試函數

### charger()

**功能:** AMR/AGV 機器人充電控制 (與 ssh_cmd.py 相同)

```python
def charger()
```

**行為:**
1. 建立 SSH 連線
2. 執行 `./NPI_tool/test/roboteq_cmd rpm=0 time=2`
3. 執行 `./NPI_tool/test/roboteq_cmd rpm=1500 time=10`
4. 等待 10 秒
5. 關閉連線

---

### MPOQC_RECORD()

**功能:** MPO 品質記錄 (與 ssh_cmd.py 相同)

```python
def MPOQC_RECORD()
```

**行為:**
1. 執行 `./NPI_tool/AMR_tools/test_record.sh`
2. 等待 30 秒
3. 執行 `./NPI_tool/AMR_tools/test_record_stop.sh`

---

### f_1(x, A, B)

**功能:** 線性函數 (數據擬合用)

```python
def f_1(x, A, B)
```

**返回:** `A * x + B`

---

### line_angle(A0, A1)

**功能:** 計算兩線夾角

```python
def line_angle(A0, A1)
```

**返回:** 弧度表示的夾角

## test(num) - 主測試函數

**命令列參數:**
```bash
python POSssh_cmd.py <IP_ADDRESS> <COMMAND_TYPE> <COM_PORT> <BAUDRATE>
```

### 支援的命令類型

#### 1. LTE 模組測試

**命令格式:** `LTE*`

**範例:**
```bash
python POSssh_cmd.py 192.168.5.1 LTE_TEST COM3 115200
```

**執行流程:**
1. 建立 SSH 連線
2. 開啟互動式 shell
3. 執行 `busybox microcom /dev/ttyUSB3` (連接 LTE 模組)
4. 發送 AT 指令序列:
   - `AT+cfun=0` (關閉射頻功能)
   - `AT+cgdcont=1,"IP","internet"` (設定 PDP 上下文)
   - `AT+cfun=1` (啟用射頻功能)
5. 檢查每個指令回應是否為 "OK"
6. 列印 "PASS" 或 "FAIL"
7. 關閉連線

**特點:**
- 完整的 LTE 初始化流程
- 每個步驟都驗證回應
- 使用 busybox microcom 工具

#### 2. 串列埠回傳測試 (POS 專用)

**命令格式:** `command:<UART_ECHO_COMMAND>`

**特殊格式:** 當指令包含 `> /outout &` 時，觸發串列埠回傳測試

**範例:**
```bash
# 測試 ttymxc0 (UART1)
python POSssh_cmd.py 192.168.5.1 \
  "command:cat /dev/ttymxc0 > /outout &" \
  COM10 115200

# 測試 ttymxc3 (UART4)
python POSssh_cmd.py 192.168.5.1 \
  "command:cat /dev/ttymxc3 > /outout &" \
  COM8 115200
```

**執行流程:**
1. 建立 SSH 連線
2. 執行 `rm /outout` (清除舊檔案)
3. 從命令中提取 UART 裝置路徑 (如 `/dev/ttymxc0`)
4. 執行 `stty < /dev/ttymxc0 -echo 115200` (設定串列埠參數)
5. 執行 `cat /dev/ttymxc0 > /outout &` (背景接收資料)
6. 等待 1 秒
7. 透過本地串列埠發送 `Hello1\n`
8. 等待 1 秒
9. 執行 `cat /outout` 讀取遠端接收到的資料
10. 列印接收資料
11. 清除 `/outout` 檔案
12. 關閉連線

**測試原理:**
```
本地 PC (COM10) ──串列線──> DUT UART1 (/dev/ttymxc0)
                                    ↓
                              寫入 /outout
                                    ↓
                              SSH 讀取
```

**用途:** 驗證 UART 接收功能是否正常

#### 3. 一般指令執行

**命令格式:** `command:<LINUX_COMMAND>` (不包含 `> /outout &`)

**範例:**
```bash
python POSssh_cmd.py 192.168.5.1 "command:ls -la" COM5 115200
```

**執行流程:**
1. 建立 SSH 連線
2. 執行指令 (透過 `exec_command`)
3. 不處理串列埠回傳邏輯
4. 關閉連線

#### 4. 需要確認的指令

**命令格式:** `Confirmcommand:<LINUX_COMMAND>`

**範例:**
```bash
python POSssh_cmd.py 192.168.5.1 \
  "Confirmcommand:reboot" \
  COM3 115200 \
  ./image.jpg
```

**執行流程:**
1. 建立 SSH 連線
2. 執行指令 (背景執行)
3. 彈出 `OPjudge_confirm` 對話框
4. 等待操作員確認
5. 讀取指令結果
6. 關閉連線

**注意:** 圖片路徑從 `sys.argv[3]` 讀取

## 主程式流程

```python
if __name__ == '__main__':
    # 解析命令列參數
    comport_name = sys.argv[3]      # COM port
    comport_baudrate = sys.argv[4]  # Baudrate
    timeout = 2

    # 開啟串列埠
    try:
        ser = serial.Serial(comport_name, comport_baudrate, timeout=timeout)
    except serial.SerialException as e:
        print("Failed to connect to the serial port:", e)
        sys.exit(10)

    # 等待串列埠穩定
    time.sleep(1)

    # 執行測試
    test(sys.argv)
```

## 使用範例

### 範例 1: LTE 模組完整測試

```bash
uv run python src/lowsheen_lib/L6MPU/POSssh_cmd.py \
  192.168.5.1 \
  LTE_INIT \
  COM3 \
  115200
```

**預期輸出:**
```
192.168.5.1
AT+cfun=0
OK
AT+cgdcont=1,"IP","internet"
OK
AT+cfun=1
OK
PASS
Connect END
```

### 範例 2: UART1 回傳測試

```bash
uv run python src/lowsheen_lib/L6MPU/POSssh_cmd.py \
  192.168.5.1 \
  "command:cat /dev/ttymxc0 > /outout &" \
  COM10 \
  115200
```

**執行過程:**
1. 遠端設備開始監聽 `/dev/ttymxc0`
2. 本地 PC 透過 COM10 發送 "Hello1\n"
3. 遠端設備接收並寫入 `/outout`
4. SSH 讀取 `/outout` 內容

**預期輸出:**
```
192.168.5.1
comport send: Hello1

cat_stdout: Hello1
Connect END
```

### 範例 3: UART4 回傳測試

```bash
uv run python src/lowsheen_lib/L6MPU/POSssh_cmd.py \
  192.168.5.1 \
  "command:cat /dev/ttymxc3 > /outout &" \
  COM8 \
  115200
```

**UART 裝置對應:**
| Linux 裝置 | UART 編號 | 用途 |
|-----------|----------|------|
| /dev/ttymxc0 | UART1 | 主串列埠 |
| /dev/ttymxc1 | UART2 | 調試串列埠 |
| /dev/ttymxc2 | UART3 | 外部擴充 |
| /dev/ttymxc3 | UART4 | POS 外設 |

## 與 PDTool4 整合

在測試計劃 CSV 中的使用:

```csv
項次,品名規格,下限值,上限值,test_type,extra_params
1,LTE Module Init,PASS,PASS,CommandTest,"{'command': 'uv run python src/lowsheen_lib/L6MPU/POSssh_cmd.py 192.168.5.1 LTE_INIT COM3 115200'}"
2,UART1 Loopback,Hello1,Hello1,CommandTest,"{'command': 'uv run python src/lowsheen_lib/L6MPU/POSssh_cmd.py 192.168.5.1 \"command:cat /dev/ttymxc0 > /outout &\" COM10 115200'}"
3,UART4 Loopback,Hello1,Hello1,CommandTest,"{'command': 'uv run python src/lowsheen_lib/L6MPU/POSssh_cmd.py 192.168.5.1 \"command:cat /dev/ttymxc3 > /outout &\" COM8 115200'}"
```

## stty 參數說明

```bash
stty < /dev/ttymxc0 -echo 115200
```

| 參數 | 說明 |
|------|------|
| `< /dev/ttymxc0` | 指定設備 |
| `-echo` | 關閉回顯 (不把輸入字元回傳) |
| `115200` | 設定鮑率為 115200 |

**其他常用 stty 參數:**
- `raw` - 原始模式 (無特殊字元處理)
- `-icanon` - 非標準模式
- `cs8` - 8 資料位元
- `-parenb` - 無同位檢查
- `-cstopb` - 1 停止位元

## 錯誤處理

### SSH 連線失敗

```python
try:
    # SSH 操作
except Exception:
    print('Exception!!')
    client.close()
    t.close()
    raise
```

### 串列埠連線失敗

```python
try:
    ser = serial.Serial(comport_name, comport_baudrate, timeout=timeout)
except serial.SerialException as e:
    print("Failed to connect to the serial port:", e)
    sys.exit(10)
```

### LTE 測試失敗

```python
if output != 'OK':
    print('FAIL')
    t.close()
    return
```

## 與其他模組的差異

| 特性 | ssh_cmd.py | ssh_comport.py | POSssh_cmd.py |
|------|-----------|----------------|---------------|
| 主要用途 | 通用 SSH 測試 | AT 指令測試 | UART 回傳測試 |
| LTE 測試 | 查詢狀態 | AT 指令 | 完整初始化 |
| UART 測試 | 無 | 無 | 回傳驗證 |
| stty 設定 | 無 | 無 | 有 |
| 測試資料 | 無 | 無 | Hello1 |

## 限制與注意事項

1. **硬編碼測試資料:** 固定發送 "Hello1\n"
2. **臨時檔案:** 使用 `/outout` 作為暫存檔案
3. **時序相依:** 硬編碼的 `time.sleep(1)` 可能不足
4. **單向測試:** 僅測試 PC → DUT 方向
5. **裝置路徑:** 需要正確對應 UART 裝置
6. **背景程序:** `cat` 命令在背景執行，需手動清除

## 除錯技巧

### 檢查 UART 裝置

```bash
# SSH 到 DUT
ssh root@192.168.5.1

# 列出所有 UART 裝置
ls -l /dev/ttymxc*

# 檢查裝置權限
chmod 666 /dev/ttymxc0
```

### 手動測試 UART

**在 DUT 上:**
```bash
# 監聽 UART
cat /dev/ttymxc0

# 或寫入檔案
cat /dev/ttymxc0 > /tmp/uart_log &
```

**在 PC 上:**
```bash
# Windows (PowerShell)
"Hello" | Out-File -FilePath COM10 -Encoding ASCII

# Linux
echo "Hello" > /dev/ttyUSB0
```

### 監控背景程序

```bash
# 查看 cat 程序
ps aux | grep cat

# 殺掉殘留程序
killall cat
```

## 常見問題

### Q1: 為什麼要用 busybox microcom?

A: 因為標準的 `cat` 或 `screen` 可能不支援 AT 指令的特殊回應格式，microcom 更適合 modem 通訊。

### Q2: 為什麼使用 /outout 而非 /tmp/outout?

A: 可能是歷史原因或權限考量，使用根目錄的檔案。建議改為 `/tmp/outout`。

### Q3: Hello1 資料可以修改嗎?

A: 可以，但需修改程式碼第 209 行:
```python
comport_send(ser,'Hello1\n',1)
```

### Q4: 如何測試雙向通訊?

A: 需要額外腳本，先從 DUT 發送，再從 PC 接收。

## 改進建議

1. **參數化測試資料:** 允許命令列指定測試字串
2. **超時處理:** 改進 sleep 為動態超時檢查
3. **清理機制:** 自動清除背景 cat 程序
4. **錯誤訊息:** 提供更詳細的失敗原因
5. **日誌記錄:** 將測試結果記錄到檔案
6. **雙向測試:** 增加 DUT → PC 測試

## 版本歷史

- **2025-01-08:** 移除未使用的 `pyModbusTCP` 匯入

## 參考連結

- [i.MX8MP UART 配置](https://www.nxp.com/docs/en/reference-manual/IMX8MPRM.pdf)
- [Paramiko SSH 庫](http://docs.paramiko.org/)
- [PySerial 文檔](https://pyserial.readthedocs.io/)
- [Linux stty 手冊](https://man7.org/linux/man-pages/man1/stty.1.html)
- [Busybox microcom](https://git.busybox.net/busybox/tree/miscutils/microcom.c)
