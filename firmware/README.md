# 固件（v1 不在本次交付范围）

这里只记录硬件对固件的接口约定，方便后续开发。硬件定义的唯一来源是
`hardware/pcb/scripts/design.py`，如有冲突以它为准。

## 引脚表（ESP32-C3-MINI-1）

| GPIO | 信号 | 方向 | 说明 |
|---|---|---|---|
| 0 | `BAT_SENSE` | ADC1_CH0 | 电池电压 ÷2（1 MΩ / 1 MΩ），满电 4.2 V → 2.1 V |
| 1 | `NFC_GPO` | 输入，RTC 唤醒 | ST25DV GPO，开漏，100 kΩ 上拉。RF 场出现 / 邮箱有新消息时拉低，用作深睡唤醒源 |
| 2 | `EPD_PWR_EN` | 输出 | 低有效。10 kΩ 上拉，P-MOS Q2 默认关断（strapping pin，上电为高） |
| 3 | `EPD_BUSY` | 输入 | 屏 BUSY |
| 4 | `I2C_SDA` | I²C | ST25DV，4.7 kΩ 上拉 |
| 5 | `I2C_SCL` | I²C | 同上 |
| 6 | `EPD_SCK` | SPI CLK | 4 线 SPI（面板 BS1 接地） |
| 7 | `EPD_MOSI` | SPI MOSI | |
| 8 | `LED_STAT_n` | 输出，低有效 | 绿色状态灯，灌电流（strapping pin，空闲为高） |
| 9 | `BOOT_n` | 输入 | BOOT / 用户按键 SW2，10 kΩ 上拉，按下为低 |
| 10 | `EPD_CS` | 输出 | |
| 18 | `USB_D-` | USB | 原生 USB-Serial-JTAG，用于烧录和日志 |
| 19 | `USB_D+` | USB | |
| 20 | `EPD_DC` | 输出 | |
| 21 | `EPD_RST` | 输出 | |
| EN | RESET | | SW1，10 kΩ + 1 µF |

没有 UART 引出，串口日志走 USB CDC。

## 器件地址

- ST25DV64KC：I²C 地址 `0x53`（用户区）、`0x57`（系统配置区），FTM 邮箱 256 B
- 屏：GDEM042F86 = SSD2683ZA；Waveshare 4.2" (G) 与 GDEY042F51 (HX8717) 驱动时序不同，按实际型号选驱动

## 上电与刷屏时序（约定）

1. 深睡待机，`NFC_GPO`（GPIO1）低电平唤醒，或按键唤醒
2. `EPD_PWR_EN` 拉低 → 面板与升压电路上电，等待 ≥ 10 ms
3. `EPD_RST` 复位 → 初始化 → 写入 400×300×2 bit（30 000 B，2 bit/像素：00 黑 01 白 10 黄 11 红）→ 刷新 → 等 `BUSY`
4. 面板进入 deep sleep，`EPD_PWR_EN` 拉高断电；SPI 引脚拉低避免漏电
5. 回到深睡

## 预算

- 每次刷新（含收图）：1.7–3 J
- 待机电流目标：≤ 15 µA（ESP32-C3 深睡 5 µA + ST25DV < 1 µA + LDO 8 µA + 分压 2 µA）
