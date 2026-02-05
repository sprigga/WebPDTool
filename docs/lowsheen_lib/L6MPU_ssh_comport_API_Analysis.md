# L6MPU ssh_comport API 分析文檔

## 概述

`ssh_comport.py` 是結合 SSH 和串列埠通訊的混合測試工具，主要用於 L6MPU (i.MX8MP) 的 AT 指令測試和需要操作員確認的測試項目。此工具可同時控制遠端設備 (透過 SSH) 和本地串列埠。

**檔案位置**: `src/lowsheen_lib/L6MPU/ssh_comport.py`

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

操作員確認對話框 (與 ssh_cmd.py 相同)

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
確認按鈕點擊處理，呼叫 `self.accept()`

```python
def closeEvent(self, event)
```
視窗關閉處理，呼叫 `self.reject()`

## 串列埠函數

### get_response(ser, timeout)

**功能:** 從串列埠讀取所有可用資料

```python
def get_response(ser, timeout)
```

**參數:**
- `ser` (serial.Serial): 串列埠物件
- `timeout` (float): 超時時間 (參數未實際使用)

**返回:** `bytes` - 串列埠接收到的原始資料

**行為:**
- 使用 `ser.read_all()` 讀取所有緩衝區資料
- 不會阻塞等待資料

**注意:** timeout 參數在當前實作中未使用

---

### comport_send(ser, comport_command, timeout)

**功能:** 向串列埠發送指令並讀取回應

```python
def comport_send(ser, comport_command, timeout)
```

**參數:**
- `ser` (serial.Serial): 串列埠物件
- `comport_command` (str): 要發送的指令
- `timeout` (float): 讀取超時時間

**返回:** `bytes` - 串列埠回應

**行為:**
1. 設定串列埠超時時間
2. 將指令編碼為 bytes 並發送
3. 呼叫 `get_response()` 讀取回應
4. 關閉串列埠
5. 返回回應資料

## 主要測試函數

### test(num)

**功能:** 主測試函數，支援多種測試模式

```python
def test(num)
```

**命令列參數:**
```bash
python ssh_comport.py <IP_ADDRESS> <COMMAND_TYPE> <COM_PORT> <BAUDRATE> [IMAGE_PATH]
```

#### 支援的命令類型

##### 1. AT 指令測試

**命令格式:** `ATcommand:<AT_COMMAND>`

**範例:**
```bash
python ssh_comport.py 192.168.5.1 "ATcommand:AT+CPIN?" COM3 115200
```

**執行流程:**
1. 建立 SSH 連線
2. 開啟互動式 shell
3. 執行 `at_cmd_task` (啟動 AT 指令任務)
4. 解析並發送 AT 指令
5. 等待 1 秒
6. 讀取 SSH 回應 (最多 2048 bytes)
7. 列印輸出
8. 關閉 SSH 連線

**用途:**
- LTE/4G 模組 AT 指令測試
- SIM 卡狀態檢查
- 網路註冊狀態查詢

**AT 指令範例:**
```bash
# 檢查 SIM 卡
ATcommand:AT+CPIN?

# 查詢訊號強度
ATcommand:AT+CSQ

# 查詢網路註冊狀態
ATcommand:AT+CREG?
```

##### 2. 一般指令執行

**命令格式:** `command:<LINUX_COMMAND>`

**範例:**
```bash
python ssh_comport.py 192.168.5.1 "command:ls -la" COM3 115200
```

**執行流程:**
1. 建立 SSH 連線
2. 解析 `command:` 後的指令
3. 使用 `client.exec_command()` 執行
4. 列印執行結果
5. 關閉 SSH 連線和串列埠

##### 3. 需要確認的指令

**命令格式:** `Confirmcommand:<LINUX_COMMAND>`

**命令列參數:**
```bash
python ssh_comport.py <IP> "Confirmcommand:<CMD>" <COM> <BAUD> <IMAGE>
```

**範例:**
```bash
python ssh_comport.py 192.168.5.1 \
  "Confirmcommand:echo dbg_debug > /proc/ilitek_ctrl" \
  COM3 115200 \
  ./src/lowsheen_lib/L6MPU/touch_test.jpg
```

**執行流程:**
1. 建立 SSH 連線
2. 執行指令 (背景執行)
3. 彈出 `OPjudge_confirm` 對話框
   - 顯示參考圖片 (sys.argv[5])
   - 顯示 "Please confirm" 訊息
4. 等待操作員確認
5. 讀取指令結果
6. 關閉連線

**注意:** 圖片路徑參數位於 `sys.argv[5]` (與 ssh_cmd.py 的 sys.argv[3] 不同)

## 主程式流程

```python
if __name__ == '__main__':
    # 解析命令列參數
    comport_name = sys.argv[3]      # COM port (e.g., "COM3", "/dev/ttyUSB0")
    comport_baudrate = sys.argv[4]  # Baudrate (e.g., "115200")
    comport_command = 'OUTP OFF\n'  # 預設指令 (未實際使用)
    timeout = 2

    # 開啟串列埠
    try:
        ser = serial.Serial(comport_name, comport_baudrate, timeout=1)
    except serial.SerialException as e:
        print("Failed to connect to the serial port:", e)
        sys.exit(10)

    # 執行測試
    test(sys.argv)

    # 讀取串列埠回應
    response = get_response(ser, 5)
    print(response.decode('utf-8'))
```

## 使用範例

### 範例 1: AT 指令 - 檢查 SIM 卡狀態

```bash
uv run python src/lowsheen_lib/L6MPU/ssh_comport.py \
  192.168.5.1 \
  "ATcommand:AT+CPIN?" \
  COM3 \
  115200
```

**預期輸出:**
```
AT+CPIN?
+CPIN: READY
OK

[串列埠回應資料]
```

### 範例 2: 執行 Linux 指令

```bash
uv run python src/lowsheen_lib/L6MPU/ssh_comport.py \
  192.168.5.1 \
  "command:cat /proc/cpuinfo" \
  COM5 \
  115200
```

**預期輸出:**
```
['processor\t: 0\n', 'BogoMIPS\t: 16.00\n', ...]
[串列埠回應資料]
```

### 範例 3: 觸控測試 (需要確認)

```bash
uv run python src/lowsheen_lib/L6MPU/ssh_comport.py \
  192.168.5.1 \
  "Confirmcommand:echo dbg_debug > /proc/ilitek_ctrl" \
  COM3 \
  115200 \
  ./src/lowsheen_lib/L6MPU/touch_test.jpg
```

**行為:**
1. 啟動觸控除錯模式
2. 顯示觸控測試參考圖片
3. 等待操作員確認觸控功能
4. 讀取串列埠回應

## 與 PDTool4 整合

在測試計劃 CSV 中的使用方式:

```csv
項次,品名規格,下限值,上限值,test_type,extra_params
1,LTE AT Command,PASS,PASS,CommandTest,"{'command': 'uv run python src/lowsheen_lib/L6MPU/ssh_comport.py 192.168.5.1 \"ATcommand:AT+CPIN?\" COM3 115200'}"
2,Touch Screen,PASS,PASS,OPjudge,"{'command': 'uv run python src/lowsheen_lib/L6MPU/ssh_comport.py 192.168.5.1 \"Confirmcommand:echo dbg_debug > /proc/ilitek_ctrl\" COM3 115200 ./src/lowsheen_lib/L6MPU/touch_test.jpg'}"
```

## 串列埠參數

| 參數 | 說明 | 範例值 |
|------|------|--------|
| COM Port | Windows: COMx<br>Linux: /dev/ttyUSBx | COM3, /dev/ttyUSB0 |
| Baudrate | 串列埠傳輸速率 | 115200, 9600, 38400 |
| Timeout | 讀取超時 (秒) | 1, 2, 5 |

## 常見 AT 指令

| AT 指令 | 功能 | 預期回應 |
|---------|------|----------|
| AT+CPIN? | 查詢 SIM 卡狀態 | +CPIN: READY |
| AT+CSQ | 查詢訊號強度 | +CSQ: 25,0 |
| AT+CREG? | 查詢網路註冊狀態 | +CREG: 0,1 |
| AT+CGATT? | 查詢 GPRS 附著狀態 | +CGATT: 1 |
| AT+COPS? | 查詢當前電信商 | +COPS: 0,0,"Chunghwa",7 |
| AT+CGDCONT? | 查詢 PDP 上下文 | +CGDCONT: 1,"IP","internet" |

## 錯誤處理

### SSH 連線錯誤

```python
try:
    # SSH 操作
except Exception:
    print('Exception!!')
    t.close()
    raise
```

### 串列埠連線錯誤

```python
try:
    ser = serial.Serial(comport_name, comport_baudrate, timeout=1)
except serial.SerialException as e:
    print("Failed to connect to the serial port:", e)
    sys.exit(10)  # 返回錯誤碼 10
```

## 與 ssh_cmd.py 的差異

| 特性 | ssh_cmd.py | ssh_comport.py |
|------|------------|----------------|
| 串列埠支援 | 無 | 有 (PySerial) |
| AT 指令測試 | 透過 SSH microcom | 專用 at_cmd_task |
| 確認對話框圖片參數 | sys.argv[3] | sys.argv[5] |
| LTE 測試 | 完整流程 (含配置) | 僅 AT 指令查詢 |
| PLC 測試 | 支援 | 不支援 |
| 主要用途 | 通用 SSH 測試 | AT 指令測試 |

## 限制與注意事項

1. **雙重通訊:** 需同時建立 SSH 和串列埠連線
2. **參數順序:** 嚴格要求參數順序 (IP, CMD, COM, BAUD, [IMAGE])
3. **串列埠占用:** 串列埠必須空閒 (未被其他程式佔用)
4. **at_cmd_task 相依:** AT 指令測試需要遠端設備支援 `at_cmd_task` 程式
5. **跨平台問題:**
   - Windows: COM1, COM2, ...
   - Linux: /dev/ttyUSB0, /dev/ttyACM0, ...
6. **超時處理:** get_response() 未實際使用 timeout 參數

## 除錯技巧

### 檢查串列埠是否可用

**Windows:**
```cmd
mode COM3
```

**Linux:**
```bash
ls -l /dev/ttyUSB*
```

### 測試串列埠通訊

```bash
# 發送測試資料
echo "AT" > COM3

# 監聽串列埠
cat /dev/ttyUSB0
```

### 查看 SSH 連線狀態

```python
import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.5.1', 22, 'root', '')
stdin, stdout, stderr = client.exec_command('uname -a')
print(stdout.read())
```

## 版本歷史

- **2025-01-08:** 移除未使用的 `pyModbusTCP` 匯入

## 參考連結

- [Paramiko 文檔](http://docs.paramiko.org/)
- [PySerial 文檔](https://pyserial.readthedocs.io/)
- [AT 指令集](https://www.developersHome.com/sms/atCommandsIntro.asp)
- [i.MX8MP 處理器](https://www.nxp.com/products/processors-and-microcontrollers/arm-processors/i-mx-applications-processors/i-mx-8-applications-processors/i-mx-8m-plus-arm-cortex-a53-machine-learning-vision-multimedia-and-industrial-iot:IMX8MPLUS)
