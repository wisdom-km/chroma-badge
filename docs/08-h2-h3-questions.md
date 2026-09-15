# H2/H3 拍板记录（已关闭）

日期：2026-09-15。本文是**决定日志**，不是待办问卷。不要再按文末「请选 A/B」执行。

**Wisdom 授权（同日）：矫枉必须过正。** USB 0.8 mm 与 NFC 线圈盖绿油保持已决策，不重开。

现板：**58 封装、680 段 / 115 过孔**，KiCad 10.0.6 全量 ERC/DRC 0。旧 564/128 备份 `agent-tools/badge-pre-h2.kicad_pcb`。仍禁止把候选 Gerber 当生产包。

流程口径（C11 DNP、USB 不重布、贴胶）见 [09-process.md](09-process.md)。

## 已落地

| 编号 | 决定 | 板上事实 |
|---|---|---|
| F06 | 跟第 7 页：脚 7 **NC Keep Open** | `design.py` pin 7 进 `nc`；`apply_extra_gnd_pads` 禁止再接地 |
| N01 | 跟第 29 页升压 | L1=47µH FNR4018S470MT；C15=4.7µF/25V；R15=1M；Q1=Si1308EDL；R14=2.2Ω 0603 |
| F07 | 跟 Torex 3.3V 表 | 近端 CIN C3=10µF、CL C4=4.7µF |
| F17 | 锁一颗充电器 + 电芯 | U3=**TP4054** C32574；202545 250mAh 2.0mm 带 PCM；J2-1=VBAT |
| F05 | 强制最小宽度 | Power 0.3 mm、NFC 0.5 mm，不够宽已重布 |
| F03 | 禁止假续航 | ADR 待机为待测，禁止写 13µA/两年 |
| F16 | 包络 3D | `lib/3d/` 有 J3/J2 仓库包络 STEP。包络 ≠ 官方 CAD |
| F14 | C11 | 首件 **DNP**，SMT 不贴；封装仍 0402；测谐振后再填 |
| F13 | USB | 只做路径笔记。**未批准不要重布** |

原问卷（方案 A/B、旧料号 68µH / C3=1µF 等）是授权**之前**的证据，已过期。需要对照当时论证时读 [local-review.md](reviews/2026-09-14/local-review.md)，不要把那些表里的「当前设计」当成现板。
