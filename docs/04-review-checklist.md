# 打样前人工复核清单

对照规格书逐项打勾。结论先写「通过 / 有风险 / 必须改」，再写页码或 URL。
`design.py` 是唯一事实来源；改脚序或电阻必须先改它再 `gen_schematic.py`。

**「还开着」= 还没拍板或还没实机，不是脚本没跑完。** 官方 GDEM042F86 规格书（2026-06-17，40 页）已对照。H2 规格项已落地，见 [08-h2-h3-questions.md](08-h2-h3-questions.md)。

已勾：USB 0.8 mm、脚 7 NC、RESE=2.2 Ω、ACTIVE_TOP=6.7、NFC 绿油。贴胶规格见 [09-process.md](09-process.md)（3M 467MP）。

仍要实机/生产授权的：电流、充电、USB 枚举、NFC 谐振、**生产 Gerber**（候选包不算）。

已用官方 PDF 勾掉：脚序（6/7=NC，8=BS1）、RESE=2.2 Ω、ACTIVE_TOP=6.7 mm（第 6 页机械图）。

调研日期：2026-09-13。GDEM042F86 官方 PDF 下载被站点 WAF 拦截，下列屏脚主要依据 **Waveshare 4.2inch e-Paper (G)** 用户手册（与 GDEM042F86 同外形 91×77、同 400×300 BWRY、同 24P 0.5 mm）。**打板前必须用佳显官方规格书复核。**

## 1. 屏幕 GDEM042F86 / 24P FPC

| 项 | 设计现状 | 调研结论 | 状态 |
|---|---|---|---|
| 外形 / 有效区 | 91×77×1.0，有效 84.8×63.6 | 与佳显产品页、Waveshare G 一致 | 通过（尺寸） |
| 驱动 IC | SSD2683ZA | 佳显产品页 | 通过 |
| 24P 脚序 | J1：2 GDR, 3 RESE, 5 VSH2, **7 NC**, 8 GND, 9 BUSY, 10 RST, 11 DC, 12 CS, 13 SCK, 14 MOSI, 15–16 VCI, 17 GND, 18 VDD, 20 VSH1, 21 VGH, 22 VSL, 23 VGL, 24 VCOM；NC = 1,4,6,**7**,19 | **GDEM042F86 第 7 页**：1/4/6/7 NC Keep Open。pin 8 接 GND = 4 线 SPI | **通过（H2 已按脚表：脚 7 空网）** |
| RESE（R14） | 2.2 Ω | 官方第 29 页参考电路 R2=**2.2 Ω**（RESE 到地） | **通过** |
| FPC 出线 | `FPC_SLOT=(27,77.6,57,79.6)`，J1 at (40, 73, 0) | 第 6 页：FPC 从短边下沿出，弯折区在屏下方。槽在板底、开口朝槽 | **通过** |

资料：

- 佳显产品页：https://www.good-display.com/product/1048.html
- 官方规格书 GDEM042F86（2026-06-17，40 页）：本机 `c:\Users\19612\Downloads\GDEM042F86.pdf`（版权文件，不入库）
- Waveshare G 手册（交叉核对）：https://files.waveshare.com/wiki/4.2inch%20e-Paper%20Module%20(G)/4.2inch_e-Paper_(G).pdf
- 不要用这份老 4.2" 规格（脚 6/7 是 TSCL/TSDA）：https://files.waveshare.com/upload/6/6a/4.2inch-e-paper-specification.pdf

## 2. USB-C TYPE-C-31-M-14

| 项 | 设计现状 | 调研结论 | 状态 |
|---|---|---|---|
| 型号 / LCSC | HRO TYPE-C-31-M-14，C223907 | 16P USB2.0 沉板母座 | 通过（选型） |
| 板厚 | `BOARD_THICKNESS=0.8` | 韩荣产品页写沉板 **0.75 mm**。嘉立创生产档只有 0.4/0.6/**0.8**/1.0/1.2/1.6/2.0，无 0.75。T&lt;1.0 mm 公差 ±0.1 → 下 0.8 实物 0.7–0.9，含 0.75 | **通过（拍板 0.8）**：2026-09-14 按嘉立创可做厚度打样，不换座。首件仍可量台阶 |
| 开口 | 板底边开槽，J3 at (75.0, BOARD_H-2.7) | 沉板中置，与外壳 USB 孔对准。外壳按 `PCB_T=0.8` | **通过（外壳 STEP）**：frame/cover vs USB 干涉 0 |

资料：LCSC C223907；https://en.krhro.com/Product-Details/728.html

## 3. LDO XC6220B331MR vs AP2112K

| 项 | 设计现状 | 调研结论 | 状态 |
|---|---|---|---|
| 符号 | `AP2112K-3.3` 符号，`U4` 取值 `XC6220B331MR-G` | SOT-25 脚序相同：1 VIN, 2 VSS/GND, 3 CE/EN, 4 NC, 5 VOUT | **通过（封装兼容）** |
| 电气 | 目标 Iq 8 µA、1 A | XC6220：1 A、PS 模式 ~8 µA；AP2112K：600 mA、~55 µA。BOM 主选 XC6220 正确 | 通过 |
| CE | 脚 3 接 `VBAT`，常使能 | 两颗都是高电平使能 | **通过** |

Torex XC6220 PDF：https://www.torexsemi.com/file/xc6220/XC6220.pdf

## 4. FPC 连接器 FH12-24S-0.5SH

| 项 | 设计现状 | 调研结论 | 状态 |
|---|---|---|---|
| 型号 | Hirose FH12-24S-0.5SH 或 JUSHUO AFC07-S24FCA-00，LCSC C262657 | 0.5 mm、24P、**Bottom contact**、前翻盖 ZIF、高 2.0 mm | 通过（型号） |
| 开口方向 | 元件在 B.Cu，J1 在槽上方 | Bottom contact：FPC 导电面朝 PCB。插拔方向应朝板下缘 `FPC_SLOT` | **通过（2026-09-14 3D）**：棕色翻盖朝槽，焊脚朝 ESP。图：`output/j1_back_close.png`、`j1_from_slot.png`。不用转 180° |
| FPC 厚度 | 未在设计里写 | FH12 推荐 0.30 mm FPC | 买屏时确认补强厚度 |

Hirose FH12：https://www.hirose.com/product/series/FH12

## 5. 外壳开窗 `ACTIVE_TOP`

| 项 | 设计现状 | 调研结论 | 状态 |
|---|---|---|---|
| `ACTIVE_TOP=6.7` | `design.py` → 外壳 | 官方第 6 页：外形 91.00×77.00×1.00，AA 84.80×63.60，左右各 **3.10**。竖直方向 AA 居中：(77−63.60)/2 = **6.70**。旧值 4.5 会挡住画面顶约 2.2 mm | **已改为 6.7**（2026-09-14） |

水平：左右各 (91-84.8)/2 = 3.1 mm，脚本用 `(PANEL_W-ACTIVE_W)/2`，与此一致。

## 6. 其它打样项（未在本轮展开）

- USB D+/D− 是否等长：Freerouting 结果能用但不好看，C3 全速不严格要求差分。
- 升压回路 L1/Q1/D1/C16 尽量短（已集中在 24–43, 57–65 一带）。
- 电池仓无零件（B.Cu rule area）。
- NFC 线圈盖绿油（ANT1 SMD 无 Mask；通孔 pad 2 仍开窗）。光线追踪里线圈是**绿的**（油盖铜），不是黄的；黄 = 露铜。圈内小黄点是通孔。铜皮 11 圈仍在，见 `output/nfc_coil_close.png`。
- 外壳脚本从 `design.py` 读 SW1/SW2、FPC 槽、电池仓、LED（2026-09-14 已按 PCB 对齐：BOOT `(22.5, 80.5)`，槽 `(27,77.6,57,79.6)`）。
- 屏贴胶：首件 **3M 467MP**（0.06 mm），只贴非 AA 边框。PETG 粘框用 300LSE。见 `docs/09-process.md`。

## 7. 建议的「通过才下单」门槛

1. ~~USB-C 沉板与 0.8 mm 板匹配或改料号~~：已拍板 0.8，见第 2 节。
2. 脚 7：官方 NC Keep Open，**H2 已空网**。不要再缝 GND。
3. ~~FH12 开口朝槽 / NFC 盖绿油 / ACTIVE_TOP=6.7 / RESE=2.2 Ω / 贴胶 467MP~~ 已写进 BOM 与 `docs/09-process.md`。
4. 生产包仍须 Wisdom 授权；CI 绿和全量 DRC 0 都不是下单文件。
