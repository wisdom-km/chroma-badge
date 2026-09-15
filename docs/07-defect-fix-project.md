# BADGE-42C 产品缺陷修复项目（先硬件，后固件）

日期：2026-09-15。依据：[当前状态](06-current-status.md)、[合并计划](reviews/2026-09-14/integrated-plan.md)、[本机复审](reviews/2026-09-14/local-review.md)、[r2 复跑](reviews/2026-09-14-r2/rerun.md)。

**Wisdom 指定执行顺序：先修硬件，再修产品固件。** 审查原文曾建议先做固件错误可见（A1），那是为了实机调试时不被假成功骗过；本文件按你选定的「硬件先行」排期。架构不改：四色屏、ESP32-C3、ST25DV、电池+USB、板厚 0.8 mm。

硬件/固件内容基准：旧板 `ee978f0`；**H2 当前板** 680 段 / 115 过孔。KiCad 10.0.6 **全量 ERC/DRC 0**。仍不是生产包。

本文件记录修复项目。H2 规格项已按 2026-09-15 Wisdom「矫枉必须过正」授权改到 `design.py` 并重布。USB 0.8 mm、NFC 线圈盖绿油仍不重开。

---

## 1. 现在进度（一句话）

| 层 | 做到哪 | 没做到哪 |
|---|---|---|
| 设计 | 原理图/PCB/外壳/v0.1 自检可构建 | 未下单、无实物 |
| 检查 | H1：error 门禁 fail-closed；候选目录导出；**KiCad 10.0.6 全量 ERC/DRC 0** | 无生产 zip |
| 硬件 H2 | 脚7 NC、升压第29页、LDO 近端电容、TP4054+202545、Power/NFC 宽度、包络 3D、丝印/parity、U1/J3/Q1 对齐 10.0 | 无实机；候选≠生产 |
| 固件 | v0.2 源码 F1 已改（GPIO1 唤醒 / 串口 W / BUSY 失败可见）；v0.1 bin 保留 | 无实机；无 NDEF/FTM |

---

## 2. H2 规格项（2026-09-15 已按授权落地）

原「必须先问再动铜皮」表已执行。USB 0.8 mm、NFC 线圈盖绿油：**已决策，不重开。**

| 编号 | 落地 |
|---|---|
| F06 | J1.7 NC Keep Open；`apply_extra_gnd_pads` 禁止再接地 |
| N01 | L1=47µH FNR4018S470MT；C15=4.7µF/25V；R15=1M；Q1=Si1308EDL；R14=2.2Ω 0603 |
| F07 | C3=10µF CIN、C4=4.7µF CL |
| F17 | U3=TP4054；电芯 202545 250mAh 2.0mm PCM |
| F05 | Power 走线 ≥0.3 mm（GND 以铺铜为电流路径）；NFC 0.5 mm。Freerouting 会收细，`enforce_netclass_widths` 后处理 |
| F03 | ADR 续航改为待测 |
| F16 | J3/J2 包络 STEP 在仓库；包络 ≠ 官方 CAD |

---

## 3. 硬件修复怎么排（本阶段）

原则：能不动铜皮就不动；`gen_pcb.py` 会清全部布线，禁止当普通检查。Freerouting 仅在 Wisdom 批准铜皮/焊盘/板框变化后，按交接第 3 节交互 shell + 相对路径。

### 工作包 H1 — 检查与制造门禁（建议最先，几乎不改电路）

不修这些就不要声称「可以下 Gerber」。

| 编号 | 改哪里 | 注意 |
|---|---|---|
| F04 | `hardware/pcb/scripts/export.sh` | **已实现门禁**：去掉 DRC `\|\| true`；`--exit-code-violations`；失败非零；失败不写 zip。`--production` 直接拒绝 |
| F19 | `route_pcb.py::drc_json` | **已实现**：每次新文件；rc 非 0/5 或无新报告则抛错，不读旧 `drc_tmp.json` |
| F18 / N02 | 制造包流程 | **已实现候选流**：`output/exports/<stamp>-candidate/` 新目录+新 zip；不碰 `output/gerbers` 与旧 zip。**不是生产发布** |
| F15 | BOM/位置 | **已实现分类**：`badge_bom_engineering.csv` / `badge_bom_assembly.csv`；C11 首件 DNP |
| F16（模型） | `lib/3d/README.md` + `check_3d_models.py` | **H2 包络 STEP 已就位**（≠ 官方 CAD）。`--fail-missing` 0。STEP rc=0 ≠ 装配覆盖 |

**本机验收（无板）：** `fault_probes` 断言已改为 fail-closed。全量 warning 进 [drc-warning-register.md](hardware/drc-warning-register.md)，**全部未豁免**。H2/H3 提问见 [08-h2-h3-questions.md](08-h2-h3-questions.md)。

H1 关闭范围：检查/导出**流程**。H2 规格已落地。仍不关闭「可下生产 Gerber」。

### 工作包 H2 — 规格冻结后的原理图/BOM（**已执行 2026-09-15**）

入口 `design.py` → `gen_schematic.py` → 备份旧板 → `gen_pcb.py` → Freerouting → 缝合 → 宽度后处理。不要手改 `.kicad_sch`。

- 当前板 680/115。KiCad 10.0.6 全量 ERC/DRC 0。旧指纹 `2d96f275…` 的板在 `agent-tools/badge-pre-h2.kicad_pcb`。
- 丝印与 schematic_parity 已在活板清零。禁止为丝印再 Freerouting。

### 工作包 H3 — 不改电路、但要登记的硬件债

| 编号 | 做什么 | 不要做什么 |
|---|---|---|
| F13 | 追 USB D+/D− 端到端和回流，写审查笔记 | 不要用网络总长当差分失配；未批准不要重布 USB |
| F14 | C11 DNP/实装调谐表 | 不要为了 3D 好看重开线圈阻焊 |
| F03 硬件侧 | ADR 已改为待测 | 未测电流不要编新的虚假续航数字 |

外壳 FPC/胶/真电池包络：有板再测，H 阶段只补模型与文档，不宣称装配通过。

---

## 4. 固件修复怎么排（硬件门禁和规格讨论之后）

保留 `firmware/output/badge-42c-v0.1.bin` 作基线，新版本升号（如 v0.2），不要覆盖 v0.1 三份 bin 当「没变过」。修完后 `host_probes` **必须改期望**：BUSY 恒高、关电超时不得再报成功。

### 工作包 F1 — 让错误可见（先于收图）

| 编号 | 文件 | 怎么修 | 注意 |
|---|---|---|---|
| F01 | `firmware/src/main.cpp::go_sleep` | **已改**：mask 仅 GPIO1；检查返回值 | 无实机 100 次 GPO 唤醒 |
| F02 | `setup` + `firmware/README.md` | **已改**：USB 就绪后 5 s 内发 `W`；BOOT+RESET = ROM 下载 | 冷启动/RESET/烧录后未实机复测 |
| F09 | `firmware/src/epd.cpp` | **已改**：BUSY 须 LOW→HIGH；上电/刷新/关电进返回值；`last_fail` 阶段名 | 第 31 页 OTP 未推翻；实屏时序未测 |
| F12 | `main.cpp` 状态 | 失败路径仍 `power_off()` 拉高 `EPD_PWR_EN` | 反灌/hold 要实机 |

本包 **不要** 同时做 NDEF、FTM、BLE、工牌 UI。

### 工作包 F2 — NFC 与一图（F1 之后）

| 编号 | 内容 |
|---|---|
| F10 | UID/型号/配置可读回；ACK ≠ FTM ready |
| F08 | Wisdom 选定 **一条** 路线：原生 FTM **或** NDEF 打开页再 BLE/SoftAP。Chrome Web NFC **不能**当 FTM 邮箱 |
| F11 | 30 KB 图 > 8 KB EEPROM；256 B 邮箱分片；校验完再刷屏；半图不显示 |
| F20 | 锁定已验证的 PlatformIO 平台版本；不替你选许可证 |

---

## 5. 验收用词（禁止混用）

| 说法 | 含义 |
|---|---|
| 已讨论 / 已批准偏离 | 有 Wisdom 记录、型号版本、批次 |
| 已实现 | 代码或 `design.py` 已改 |
| 本机验证 | 隔离审查/编译/探针按 **新** 期望通过 |
| 实机通过 | 有板号、条件、日志/波形 |
| 生产包 | 门禁通过后的新 zip+manifest；诊断 Gerber 不算 |

关闭模板仍用合并计划第 5 节。不要用「排上计划」「编译过了」「DRC 无 error」代替关闭。

---

## 6. 下一会话：先贴硬件提示词；做完再贴固件

### 6.1 硬件修复提示词（先用这一段）

```text
继续 BADGE-42C 硬件缺陷修复（产品固件先不要改）。
先读 AGENTS.md、docs/03-handoff.md、docs/01-architecture-decisions.md、
docs/06-current-status.md、docs/07-defect-fix-project.md、
docs/reviews/2026-09-14/integrated-plan.md 与 local-review.md。
始终中文。先 git status；不要提交或重置 hardware/pcb/badge.kicad_pro、不要动 tools/freerouting/。

本包只做 docs/07 的工作包 H1，以及把 H2/H3 里需要 Wisdom 拍板的项写成「证据 + 两种方案」提问，未经确认不要改网络/铜皮。
优先：F04 export.sh 门禁、F19 drc_json 旧报告、F18/N02 新目录导出流程（还不要当生产发布）、F16 登记/补 USB 3D 模型路径、F15 BOM 分类说明。
不要运行 gen_pcb.py；不要 Freerouting；不要为丝印或截图清布线。
不要因为 DRC error 0 声称全量通过；全量 warning 必须列表或进豁免表，不能默认忽略。
硬件改动若获批准，只从 hardware/pcb/scripts/design.py 起手，再 gen_schematic.py。
提交前：故障路径（DRC 命令失败、旧报告注入）按修后的新期望验证；正常路径（error ERC/DRC、网表）再跑一遍。
写明未覆盖的实物场景。不要建 PR。不要把诊断 Gerber 当生产包。历史推送授权不是生产发布授权。
```

### 6.2 固件修复提示词（硬件 H1 完成、规格讨论有结论后再用）

```text
继续 BADGE-42C 产品固件修复（v0.2 自检可靠性；不要做 NDEF/FTM/工牌画面）。
先读 AGENTS.md、docs/07-defect-fix-project.md 第 4 节、firmware/README.md、
docs/reviews/2026-09-14/local-review.md 第 4 节、docs/reviews/2026-09-14-r2/rerun.md。
始终中文。先 git status；不要改 PCB/design.py/制造包，除非只改固件文档里过时的操作说明。
不要覆盖 firmware/output/badge-42c-v0.1*.bin；新构建用新版本号。

本包只做 F01、F02、F09，必要时 F12 的关电路径。
- go_sleep：去掉 GPIO9 深睡，检查 API 返回值。
- 自检入口与 ROM 下载（按住 BOOT+复位）分开，更新 firmware/README.md。
- epd.cpp：上电/刷新/关电失败必须失败；修改 tools/review/host_probes.py 期望，使恒高/关电超时不再被当成成功。
用 D:\PlatformIO\penv\Scripts\pio.exe 在隔离或干净目录编译。不要装 VS Code 的 PIO vsix。

提交前跑 host_probes 与 pio run；正常四色仍 30000 字节；故障路径按新断言。
未覆盖：实屏 BUSY、USB 烧录、深睡电流、NFC 真场。不要建 PR。不要宣称实机通过。
```

---

## 7. 建议的检查点

1. H1 本机：`fault_probes` 按新断言绿（旧 DRC 注入失败；ERC/DRC 失败不到 Gerber）。`export.sh --check-only` error ERC/DRC 0、网表匹配。候选目录已能出当前 B.Silk，**仍无生产 zip**。
2. Wisdom 书面回复 F06/N01/F07/F17。
3. 若有铜皮变更：单独提交，带旧板指纹与是否 Freerouting 的说明。
4. 再开 F1 固件会话。
5. 有板之后才做合并计划第 4 节实物单；未测项保持待验证。
