# BADGE-42C 审查复跑（2026-09-14-r2）

日期：2026-09-14 23:44（UTC+8）。隔离目录：`agent-tools/review-20260914-234456`（gitignore，不入库整包）。

**工作包：** 按 `tools/review/README.md` 在新目录复跑审查与测试文档。不修产品固件/硬件缺陷，不跑 `gen_pcb.py`，不跑 Freerouting，不覆盖 [2026-09-14 归档证据](../2026-09-14/evidence/README.md)，不发布生产包。本地 `hardware/pcb/badge.kicad_pro` 与 `tools/freerouting/` 未改、未提交。

审查输入 HEAD：`11ab832815d8f10327e432e152d641957101a5e1`。硬件/固件内容仍对齐 [ee978f0](https://github.com/wisdom-km/chroma-badge/commit/ee978f08cbdb7b61bbe2c78fea0e9c7cd2c34a7b)。F01–F20 / N01 / N02 关闭标准仍见 [integrated-plan.md](../2026-09-14/integrated-plan.md)；本轮没有把任何项改成“已修复”或“实机通过”。

## 1. 本机工具

| 工具 | 本轮 |
|---|---|
| KiCad | 9.0.8，`D:/chroma-badge/agent-tools/kicad-9.0.8`（审查用独立安装，不因 PATH 上的 10 改版本） |
| 用户 KiCad | 亦存在 `%LOCALAPPDATA%\Programs\KiCad\9.0`；本轮 CLI 用 agent-tools 副本 |
| FreeCAD | 1.1.3，`D:/FreeCAD/bin/python.exe` |
| PlatformIO | 6.2.0，`D:/PlatformIO/penv/Scripts/pio.exe` |
| 主机 g++ | MinGW 13.1.0 |
| Git Bash | `G:/BaseWare/Git/bin/bash.exe` |

`prepare.py` 快照使用 **HEAD 的** `.kicad_pro`；工作区未提交工程文件另存为隔离目录内 `local-project.kicad_pro`。

## 2. 正常路径（本机软件/几何）

这些只证明当前数据在本机工具下可重复，**不是** 生产通过或实机通过。

| 路径 | 结果 |
|---|---|
| error 级 ERC | 0，CLI 0 |
| error 级 DRC | 0 错误、0 未连接，CLI 0 |
| 新网表 + `check_netlist.py` | 通过；57 元件、41 功能网络 |
| 原理图/NFC 生成器副本 | 成功；`gen_pcb.py` **未执行**；NFC 封装忽略换行后相同 |
| `--skip-route` 两次 | 三次快照均为 564 段 / 128 过孔；指纹 `2d96f2751cfe29874e19817df79bebdc1da593ffc553671f2aa7306423b1d7c4`，与 2026-09-14 轮相同 |
| 干净固件构建 | SUCCESS；RAM 15312、Flash 283588；三份 bin SHA256 与仓库 `firmware/output` 一致 |
| EPD 替身 **normal** 四色 | 各 30000 字节，编码 00/55/AA/FF，请求关电 |
| FreeCAD 外壳重建 | 94×93×6.3 mm；扩展 10 组交叠 0（新旧 STEP 各一次） |
| 诊断 Gerber/钻孔/BOM/STEP/渲染 | 各 KiCad 命令返回 0（诊断用，不是下单包） |

## 3. 故障路径（旧缺陷仍复现）

`host_probes` / `fault_probes` 通过 = **缺陷被再次抓住**，不是产品正确。

| 路径 | 结果 | 对应项 |
|---|---|---|
| 全量 ERC + DRC+parity | 审查程序返回 **1**；全量 ERC 1 warning（`lib_symbol_issues`）；DRC 148 warning（57+1+6+62+22） | 不得写成“所有检查通过” |
| BUSY 恒高 / 关电超时 | 四色均 `reported_success=true` | F09 未修 |
| `drc_json` 注入返回码 5 | 读回带 `OLD_REPORT` 的空旧报告 | F19 |
| `export.sh` ERC 失败 | 脚本退出 5，未到 Gerber | ERC 可阻断 |
| `export.sh` DRC 失败 | Gerber 哨兵 99，**已走到** `pcb export gerbers` | F04，`\|\| true` |
| 原 `export.sh` 在 Git Bash | `python3` 不存在，退出 127，未到制造导出 | 原入口本机仍不可作为发布路径 |
| 背面丝印归一化比较 | 13 份中 12 份相同，`badge-B_Silkscreen.gbr` **不同** | N02 仍在 |
| J3/J2 3D 模型 | 源 STEP 缺失/官方库无法解析；完整 STEP 命令仍返回 0 | F16；缺模型不是板上没封装 |

F01 GPIO9 深睡、F02 BOOT 入口冲突、F06 J1.7、N01 升压差异：**未改代码，状态仍为未修复/待讨论。**

## 4. 未覆盖的实物场景

本轮 **没有** 板、屏、电池、手机、示波器、电流表、VNA。下列全部仍是 [操作单](../2026-09-14/integrated-plan.md) 第 4 节未执行项：

首次供电、USB 枚举/烧录、LDO 波形、EPD 真刷新、NFC/GPO、深睡 100 次、传图、充电温升、装机 RF、FPC/胶/真电池装配、续航电荷。

主机毫秒是替身时钟，不是屏实测。

## 5. 给 Wisdom 仍待讨论（未改板）

与首轮相同，本轮只重复证据，不代替批准：J1.7 Keep Open vs GND；升压 L1/C15/GDR/Q1；XC6220 近端电容；续航 13 µA 叙述；全量 warning 豁免表；是否重建同步制造包（N02）。

## 6. 结论

工程样机闭环验证阶段不变。error 级 DRC 0 **且** 全量 warning 148 **同时成立**。产品缺陷未修。诊断导出不是生产发布。下一工作包仍是计划阶段 A（A1 固件错误可见，或 A2 导出门禁），需 Wisdom 明确授权后才改产品代码或 `design.py`。
