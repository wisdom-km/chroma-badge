# 固件

硬件引脚以 `hardware/pcb/scripts/design.py` 为准。本目录是 **v0.2 上电自检**：USB 日志、电池 ADC、ST25DV I²C 探测；正常启动后串口 5 s 内发 `W` 则按官方 OTP 刷一屏白（不要按住 BOOT 复位，那是 ROM 下载）。然后深睡，只由 `NFC_GPO`（GPIO1）低电平唤醒。GPIO9 不是深睡唤醒源。

屏：GDEM042F86 / SSD2683ZA，400×300，2 bit/像素（00 黑 01 白 10 黄 11 红）。初始化抄规格书 2026-06-17 **第 31 页** LUT from OTP，不写波形 RAM。

## 构建

ESP32-C3-MINI-1，原生 USB-Serial-JTAG（没有外置 UART）。

预编译基线（2026-09-14，不要覆盖）：

- `output/badge-42c-v0.1.bin`（应用，296 512 B）
- `output/badge-42c-v0.1-bootloader.bin`
- `output/badge-42c-v0.1-partitions.bin`

v0.2 用 `pio run` 生成到 `.pio/build/`，有板后再拷新版本号，不要覆盖上面三份。

```bash
cd firmware
pio run
pio run -t upload
pio device monitor
```

没有 PlatformIO 时：安装 [pio](https://platformio.org/) 或 Arduino-ESP32（板选 ESP32C3 Dev Module，CDC on boot）。不要把 PlatformIO IDE 的 `.vsix` 装进 Cursor（那是 VS Code 扩展）。

## 上电行为

1. GPIO2（`EPD_PWR_EN`）保持高：P-MOS 关，屏断电。
2. USB CDC 打 `BADGE-42C firmware v0.1`、电池电压、ST25DV 是否 ACK。
3. USB CDC 就绪后 **5 s 内发字符 `W`**：刷全白（约 20 s），BUSY 未完成周期则报 `TIMEOUT` 并断电。
4. 否则闪三下状态灯，深睡。只唤醒 `NFC_GPO`。**按住 BOOT + RESET = ROM 下载，不是刷白。**

还没做：NDEF URL、FTM 邮箱收图、完整工牌画面。

## 引脚表（ESP32-C3-MINI-1）

| GPIO | 信号 | 方向 | 说明 |
|---|---|---|---|
| 0 | `BAT_SENSE` | ADC1_CH0 | 电池电压 ÷2（1 MΩ / 1 MΩ），满电 4.2 V → 2.1 V |
| 1 | `NFC_GPO` | 输入，RTC 唤醒 | ST25DV GPO，开漏，100 kΩ 上拉。RF 场 / 邮箱新消息拉低 |
| 2 | `EPD_PWR_EN` | 输出 | 低有效。10 kΩ 上拉，P-MOS 默认关（strapping，上电为高） |
| 3 | `EPD_BUSY` | 输入 | 忙时为低（规格书 note 5-4） |
| 4 | `I2C_SDA` | I²C | ST25DV，4.7 kΩ 上拉 |
| 5 | `I2C_SCL` | I²C | 同上 |
| 6 | `EPD_SCK` | SPI CLK | 4 线 SPI（BS1 接地） |
| 7 | `EPD_MOSI` | SPI MOSI | |
| 8 | `LED_STAT_n` | 输出，低有效 | 绿色状态灯（strapping，空闲为高） |
| 9 | `BOOT_n` | 输入 | BOOT / 用户键 SW2，10 kΩ 上拉 |
| 10 | `EPD_CS` | 输出 | |
| 18 | `USB_D-` | USB | 原生 USB-Serial-JTAG |
| 19 | `USB_D+` | USB | |
| 20 | `EPD_DC` | 输出 | |
| 21 | `EPD_RST` | 输出 | |
| EN | RESET | | SW1，10 kΩ + 1 µF |

## 器件地址

- ST25DV64KC：I²C `0x53`（用户区）、`0x57`（系统区），FTM 邮箱 256 B
- 屏：GDEM042F86 = SSD2683ZA；不要用 GDEY042F51（HX8717）的 LUT

## 预算

- 每次刷新（含收图）：1.7–3 J
- 待机目标：≤ 15 µA
