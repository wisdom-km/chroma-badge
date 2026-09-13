# 打样前人工复核清单

对照规格书逐项打勾。结论先写「通过 / 有风险 / 必须改」，再写页码或 URL。
`design.py` 是唯一事实来源；改脚序或电阻必须先改它再 `gen_schematic.py`。

调研日期：2026-09-13。GDEM042F86 官方 PDF 下载被站点 WAF 拦截，下列屏脚主要依据 **Waveshare 4.2inch e-Paper (G)** 用户手册（与 GDEM042F86 同外形 91×77、同 400×300 BWRY、同 24P 0.5 mm）。**打板前必须用佳显官方规格书复核。**

## 1. 屏幕 GDEM042F86 / 24P FPC

| 项 | 设计现状 | 调研结论 | 状态 |
|---|---|---|---|
| 外形 / 有效区 | 91×77×1.0，有效 84.8×63.6 | 与佳显产品页、Waveshare G 一致 | 通过（尺寸） |
| 驱动 IC | SSD2683ZA | 佳显产品页 | 通过 |
| 24P 脚序 | J1：2 GDR, 3 RESE, 5 VSH2, 7 GND, 8 GND, 9 BUSY, 10 RST, 11 DC, 12 CS, 13 SCK, 14 MOSI, 15–16 VCI, 17 GND, 18 VDD, 20 VSH1, 21 VGH, 22 VSL, 23 VGL, 24 VCOM；NC = 1,4,6,19 | Waveshare G 手册：1 NC, 2 GDR, 3 RESE, 4 NC, 5 VSH2, **6 NC, 7 NC, 8 BS1**, 9 BUSY … 17 VSS, 19 VPP Keep open。**pin 8 接 GND = BS1=L，强制 4 线 SPI**，与 ADR「BS1=GND」一致。pin 7 规格写 Keep open，现为缝合 GND；若实板是 TSDA（老型号 GDEY042Z98 才是）会出事 | **有风险**：pin 7 需官方 PDF 确认是 NC。不要用 GDEY042Z98 的脚序 |
| RESE（R14） | 2.2 Ω | 佳显参考电路常见 0.47 / 2.2 / 3 Ω。未拿到 GDEM042F86 参考电路页 | **必须改或确认**：用官方 PDF 的 RESE 值 |
| FPC 出线 | `FPC_SLOT=(27,77.6,57,79.6)`，J1 at (40, 73, 0)，元件在 B.Cu | 屏 FPC 从板下缘绕到背面。槽在板底、连接器在槽上方 | 待对照面板机械图确认出线在短边下沿 |

资料：

- 佳显产品页：https://www.good-display.com/product/1048.html
- 规格书入口（需过 WAF）：https://www.good-display.com/companyfile/2073.html
- Waveshare G 手册：https://files.waveshare.com/wiki/4.2inch%20e-Paper%20Module%20(G)/4.2inch_e-Paper_(G).pdf
- 不要用这份老 4.2" 规格（脚 6/7 是 TSCL/TSDA）：https://files.waveshare.com/upload/6/6a/4.2inch-e-paper-specification.pdf

## 2. USB-C TYPE-C-31-M-14

| 项 | 设计现状 | 调研结论 | 状态 |
|---|---|---|---|
| 型号 / LCSC | HRO TYPE-C-31-M-14，C223907 | 16P USB2.0 沉板母座 | 通过（选型） |
| 板厚 | `BOARD_THICKNESS=0.8` | 韩荣产品页写 **0.75 mm PCB**。0.8 mm 可能略厚，壳体台阶贴合变差或焊盘悬空 | **有风险**：打样前量封装台阶；备选同系列适配 0.8 mm 的料号，或接受 0.05 mm 偏差并首件确认 |
| 开口 | 板底边开槽，J3 at (75.0, BOARD_H-2.7) | 沉板中置，与外壳 USB 孔对准 | 待装配 STEP 再看一次 |

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
| 开口方向 | 元件在 B.Cu，J1 在槽上方 | Bottom contact：FPC 导电面朝 PCB。插拔方向应朝板下缘 `FPC_SLOT`。KiCad 封装 `Hirose_FH12-24S-0.5SH_1x24-1MP` 开口朝 footprint 哪一侧，叠加 Flip+rot=0 后必须朝 +Y（槽） | **必须在 PCB 上目视**：背面看连接器开口是否朝槽；若朝上则 J1 旋转 180° |
| FPC 厚度 | 未在设计里写 | FH12 推荐 0.30 mm FPC | 买屏时确认补强厚度 |

Hirose FH12：https://www.hirose.com/product/series/FH12

## 5. 外壳开窗 `ACTIVE_TOP`

| 项 | 设计现状 | 调研结论 | 状态 |
|---|---|---|---|
| `ACTIVE_TOP=4.5` | `hardware/enclosure/badge_enclosure.py` | 有效区 84.8×63.6，外形 91×77。若垂直居中，上下各 (77-63.6)/2 = **6.7 mm**。FPC 在底边时有效区通常上边距更小、下边距更大。4.5 比居中少 2.2 mm，方向合理但数值未对图纸 | **必须改或确认**：用 GDEM042F86 机械图的 Viewing Area 到 Top 尺寸替换 4.5 |

水平：左右各 (91-84.8)/2 = 3.1 mm，脚本用 `(PANEL_W-ACTIVE_W)/2`，与此一致。

## 6. 其它打样项（未在本轮展开）

- USB D+/D− 是否等长：Freerouting 结果能用但不好看，C3 全速不严格要求差分。
- 升压回路 L1/Q1/D1/C16 尽量短（已集中在 24–43, 57–65 一带）。
- 电池仓无零件（B.Cu rule area）。
- NFC 线圈目前裸铜，盖绿油（下一步 #2）后再出 Gerber。
- 0.4/0.2 mm 过孔：0.8 mm 板厚 4:1，多数板厂能做，下单时写明。

## 7. 建议的「通过才下单」门槛

1. 官方 GDEM042F86 PDF：脚 6/7/8、RESE、机械尺寸、FPC 方向。
2. USB-C 沉板与 0.8 mm 板匹配或改料号。
3. KiCad 3D/渲染确认 FH12 开口朝槽。
4. NFC 盖绿油并 DRC 清零后再导 Gerber。
