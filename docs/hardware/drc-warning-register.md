# 全量 ERC/DRC warning 登记表（非豁免）

日期：2026-09-15。检查器：**KiCad 10.0.6**（`C:\Users\19612\AppData\Local\Programs\KiCad\10.0\bin`）。来源：本机 `hardware/pcb/output/erc_all_h2.json`、`drc_all_h2.json`（官方 `sym-lib-table` + `KICAD10_SYMBOL_DIR` + 工程 `hardware/pcb/sym-lib-table`）。

**本表不是豁免批准。** 当前全量 warning **0**。error 级 0 仍不等于「可以下生产包」——候选 Gerber ≠ 生产 zip。

逐条列表：[drc-warning-register.csv](drc-warning-register.csv)（现为空）。2026-09-14 r2 的 148 条是旧 57 件板档案，不要和本表混用。KiCad 9.0.8 读不了工程 `Espressif.kicad_sym`（KiCad 10 格式）；全量以 10.0.6 为准。

## 规则

| 字段 | 含义 |
|---|---|
| 状态 | `未豁免` = 仍算未通过全量检查 |
| 对 error 级候选导出 | 不阻断（`--severity-error`） |
| 对生产包 | 阻断，直到有批准人或已修复 |
| 失效条件 | 换 KiCad 版本、改丝印/封装生成、改网络规则后必须重跑全量 |

## 汇总（H2 板：58 封装，680 段 / 115 过孔）

| 类型 | 条数 | 说明 |
|---|---|---|
| ERC 全量 | **0** | U1 `Espressif:ESP32-C3-MINI-1` 53 脚与封装、`design.py` 一致 |
| DRC 全量（含丝印） | **0** | 含 `schematic_parity` |
| 未连接 | **0** | |

## KiCad 10 相对 KiCad 9 已对齐的项

| 项 | 做法 |
|---|---|
| U1 符号库 | 用 KiCad 10 读工程 `lib/Espressif.kicad_sym`；引脚 1–53 与 `badge:ESP32-C3-MINI-1`、GPIO 映射一致 |
| J3 外壳脚 | KiCad 10 符号为 `SH`；封装/板上焊盘由 `S1` 改为 `SH`（四只沉板支架，仍接 GND） |
| Q1 封装 | 官方 10.0 SOT-323 已重生；活板实例写入 `badge:SOT-323_SC-70`，避免和官方库比丝印 |
| 字段 | Description / Datasheet / LCSC 在封装上隐藏于 `B.Fab` |
| 原理图 | `gen_schematic.py` 按 KiCad 10 符号库嵌入（不再剥 v10 token） |

不要为丝印再跑 `gen_pcb.py` / Freerouting。不要把候选 Gerber 当生产包。
