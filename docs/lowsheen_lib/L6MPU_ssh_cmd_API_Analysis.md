# L6MPU ssh_cmd API 分析文檔

## 概述

`ssh_cmd.py` 是用於透過 SSH 連線控制 L6MPU (i.MX8MP 嵌入式系統) 的測試工具。支援 LTE 模組測試、PLC 網路連通性測試、一般 Linux 指令執行，以及需要操作員確認的測試項目。

**檔案位置**: `src/lowsheen_lib/L6MPU/ssh_cmd.py`

## 相依套件

```python
import paramiko      # SSH 連線
import time
import numpy as np
import math
import threading
import os
import sys
from scipy import optimize as op
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt
```

## 全域變數

```python
sUsername = "root"    # SSH 登入帳號
sPassword = ""        # SSH 密碼 (空字串代表免密碼登入)
sHostname = ""        # SSH 主機位址 (由命令列參數指定)
port = 22             # SSH 連接埠
```

## 主要類別

### OPjudge_confirm

操作員確認對話框，用於需要人工判斷的測試項目。

#### 建構函式

```python
def __init__(self, ImagePath, content, parent=None)
```

**參數:**
- `ImagePath` (str): 圖片路徑，顯示測試參考圖片 (如 `blight0.jpg`, `touch_test.jpg`)
- `content` (str): 對話框訊息文字
- `parent` (QWidget, optional): 父視窗

**功能:**
- 建立包含圖片和確認按鈕的對話框
- 圖片縮放至 800x500 像素 (保持長寬比)
- 綠色確認按鈕 (200x80 像素)

#### 方法

```python
def on_click(self)
```
處理確認按鈕點擊，呼叫 `self.accept()` 返回成功。

```python
def closeEvent(self, event)
```
處理視窗關閉事件，呼叫 `self.reject()` 返回失敗。

## 主要函數

### charger()

**功能:** 機器人充電控制測試 (看起來是 AMR/AGV 充電功能)

```python
def charger()
```

**行為:**
1. 建立 SSH 連線
2. 執行 `./NPI_tool/test/roboteq_cmd rpm=0 time=2` (停止馬達)
3. 執行 `./NPI_tool/test/roboteq_cmd rpm=1500 time=10` (啟動馬達)
4. 等待 10 秒
5. 關閉連線

**注意:** 此功能需要 `farobottech` 密碼輸入

---

### MPOQC_RECORD()

**功能:** MPO 品質記錄測試

```python
def MPOQC_RECORD()
```

**行為:**
1. 建立 SSH 連線和 SFTP 通道
2. 啟動互動式 shell
3. 執行 `./NPI_tool/AMR_tools/test_record.sh` (開始記錄)
4. 等待 30 秒
5. 執行 `./NPI_tool/AMR_tools/test_record_stop.sh` (停止記錄)

---

### f_1(x, A, B)

**功能:** 線性函數 (用於數據擬合)

```python
def f_1(x, A, B)
```

**參數:**
- `x` (float): 自變數
- `A` (float): 斜率
- `B` (float): 截距

**返回:** `A * x + B`

---

### line_angle(A0, A1)

**功能:** 計算兩條線的夾角

```python
def line_angle(A0, A1)
```

**參數:**
- `A0` (float): 第一條線的斜率
- `A1` (float): 第二條線的斜率

**返回:** 弧度表示的夾角

**公式:** `angle = arctan((A0 - A1) / (1 + A0 * A1))`

---

### test(num)

**功能:** 主測試函數，根據命令類型執行不同測試

```python
def test(num)
```

**命令列參數:**
```bash
python ssh_cmd.py <IP_ADDRESS> <COMMAND_TYPE>
```

#### 支援的命令類型

##### 1. LTE 模組測試

**命令格式:** `LTE*`

**範例:**
```bash
python ssh_cmd.py 192.168.5.1 LTE_TEST
```

**執行流程:**
1. 建立 SSH 連線
2. 開啟互動式 shell
3. 執行 `microcom -t 2000 -s 115200 /dev/ttyUSB3` (連接 LTE 模組)
4. 發送 AT 指令: `AT+CPIN?` (檢查 SIM 卡狀態)
5. 等待 1.5 秒
6. 讀取並列印回應
7. 關閉連線

**特點:**
- 使用 microcom 工具連接 UART 介面
- 超時時間設定為 2000ms
- 鮑率 115200

##### 2. PLC1 網路測試

**命令格式:** `PLC1*`

**範例:**
```bash
python ssh_cmd.py 192.168.5.1 PLC1_PING
```

**執行流程:**
1. 建立 SSH 連線
2. 執行 `ifconfig eth0` 取得 eth0 的 IP 位址
3. 解析輸出取得 IP (格式: `inet <IP> netmask`)
4. 執行 `ping -c 4 <PLC1_IP>` 進行連通性測試
5. 列印 ping 結果
6. 關閉連線

##### 3. PLC2 網路測試

**命令格式:** `PLC2*`

**範例:**
```bash
python ssh_cmd.py 192.168.5.1 PLC2_PING
```

**執行流程:** 與 PLC1 相同，但測試 `eth1` 介面

##### 4. 一般指令執行

**命令格式:** `command:<LINUX_COMMAND>`

**範例:**
```bash
python ssh_cmd.py 192.168.5.1 "command:ls -la /home"
python ssh_cmd.py 192.168.5.1 "command:cat /proc/cpuinfo"
```

**執行流程:**
1. 建立 SSH 連線
2. 解析 `command:` 後的指令
3. 執行指令
4. 列印執行結果 (stdout)
5. 關閉連線

**用途:** 執行任意 Linux shell 指令

##### 5. 需要確認的指令

**命令格式:** `Confirmcommand:<LINUX_COMMAND>`

**命令列參數:**
```bash
python ssh_cmd.py <IP_ADDRESS> "Confirmcommand:<COMMAND>" <IMAGE_PATH>
```

**範例:**
```bash
python ssh_cmd.py 192.168.5.1 "Confirmcommand:reboot" "./side_button.jpg"
python ssh_cmd.py 192.168.5.1 "Confirmcommand:echo dbg_debug > /proc/ilitek_ctrl" "./touch_test.jpg"
```

**執行流程:**
1. 建立 SSH 連線
2. 執行指令 (在背景執行)
3. 彈出 `OPjudge_confirm` 對話框
   - 顯示參考圖片 (sys.argv[3])
   - 顯示 "Please confirm" 訊息
4. 等待操作員點擊確認或關閉視窗
5. 讀取指令執行結果
6. 關閉連線

**用途:** 需要人工判斷的測試項目，例如:
- 觸控螢幕測試 (顯示觸控圖案)
- 按鈕測試 (顯示按鈕位置)
- LED 測試 (顯示 LED 亮度參考)

## 使用範例

### 範例 1: LTE 模組 SIM 卡檢查

```bash
uv run python src/lowsheen_lib/L6MPU/ssh_cmd.py 192.168.5.1 LTE_CHECK
```

**預期輸出:**
```
AT+CPIN?
+CPIN: READY
OK
Connect END
```

### 範例 2: PLC 網路連通性測試

```bash
uv run python src/lowsheen_lib/L6MPU/ssh_cmd.py 192.168.5.1 PLC1_TEST
```

**預期輸出:**
```
192.168.1.100
PING 192.168.1.100 (192.168.1.100): 56 data bytes
64 bytes from 192.168.1.100: icmp_seq=0 ttl=64 time=1.2 ms
...
--- 192.168.1.100 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss
Connect END
```

### 範例 3: 執行系統資訊查詢

```bash
uv run python src/lowsheen_lib/L6MPU/ssh_cmd.py 192.168.5.1 "command:uname -a"
```

**預期輸出:**
```
['Linux imx8mp 5.15.71 #1 SMP PREEMPT Thu Jan 12 10:23:45 UTC 2023 aarch64 GNU/Linux\n']
Connect END
```

### 範例 4: 觸控測試 (需要確認)

```bash
uv run python src/lowsheen_lib/L6MPU/ssh_cmd.py 192.168.5.1 \
  "Confirmcommand:echo dbg_debug > /proc/ilitek_ctrl" \
  "./src/lowsheen_lib/L6MPU/touch_test.jpg"
```

**行為:**
1. 執行觸控除錯指令
2. 彈出對話框顯示 `touch_test.jpg` 圖片
3. 操作員確認觸控是否正常
4. 點擊確認按鈕後結束

## 錯誤處理

所有測試函數都包含例外處理:

```python
try:
    # SSH 操作
except Exception:
    print ('Exception!!')
    t.close()  # 確保連線關閉
    raise      # 重新拋出例外
```

## 檔案相依性

測試過程可能引用的檔案:

| 檔案 | 用途 |
|------|------|
| `blight0.jpg` | 螢幕亮度參考圖片 |
| `touch_test.jpg` | 觸控測試參考圖片 |
| `side_button.jpg` | 側邊按鈕位置參考 |
| `imx-boot-imx8mp-lpddr4-evk-sd.bin-flash_evk` | Bootloader 映像檔 |
| `imx-image-multimedia-imx8mp-lpddr4-evk.wic.zst` | 系統映像檔 |
| `uuu.exe` | NXP UUU 燒錄工具 |

## 限制與注意事項

1. **SSH 免密碼登入:** 需要事先設定 SSH 金鑰認證
2. **root 權限:** 使用 root 帳號連線，需注意安全性
3. **PyQt5 相依:** 需要 GUI 環境執行確認對話框
4. **固定的裝置路徑:**
   - LTE 模組固定在 `/dev/ttyUSB3`
   - 網路介面固定為 `eth0` 和 `eth1`
5. **時間延遲:** 硬編碼的 `time.sleep()` 可能需要根據硬體調整

## 與 PDTool4 整合

在測試計劃 CSV 中使用方式:

```csv
項次,品名規格,下限值,上限值,test_type,extra_params
1,LTE SIM Card Check,PASS,PASS,CommandTest,"{'command': 'uv run python src/lowsheen_lib/L6MPU/ssh_cmd.py 192.168.5.1 LTE_CHECK'}"
2,PLC1 Network,PASS,PASS,CommandTest,"{'command': 'uv run python src/lowsheen_lib/L6MPU/ssh_cmd.py 192.168.5.1 PLC1_PING'}"
3,Touch Screen Test,PASS,PASS,CommandTest,"{'command': 'uv run python src/lowsheen_lib/L6MPU/ssh_cmd.py 192.168.5.1 \"Confirmcommand:echo dbg_debug > /proc/ilitek_ctrl\" ./src/lowsheen_lib/L6MPU/touch_test.jpg'}"
```

## 版本歷史

- **2025-01-08:** 移除未使用的 `pyModbusTCP` 匯入

## 參考連結

- [Paramiko 文檔](http://docs.paramiko.org/)
- [i.MX8MP 處理器](https://www.nxp.com/products/processors-and-microcontrollers/arm-processors/i-mx-applications-processors/i-mx-8-applications-processors/i-mx-8m-plus-arm-cortex-a53-machine-learning-vision-multimedia-and-industrial-iot:IMX8MPLUS)
- [PyQt5 文檔](https://www.riverbankcomputing.com/static/Docs/PyQt5/)
