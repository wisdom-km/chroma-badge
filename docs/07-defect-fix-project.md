# BADGE-42C 产品缺陷修复项目（先硬件，后固件）

日期：2026-09-15。依据：[当前状态](06-current-status.md)、[合并计划](reviews/2026-09-14/integrated-plan.md)、[本机复审](reviews/2026-09-14/local-review.md)、[r2 复跑](reviews/2026-09-14-r2/rerun.md)。

**Wisdom 指定执行顺序：先修硬件，再修产品固件。** 审查原文曾建议先做固件错误可见（A1），那是为了实机调试时不被假成功骗过；本文件按你选定的「硬件先行」排期。架构不改：四色屏、ESP32-C3、ST25DV、电池+USB、板厚 0.8 mm。

硬件/固件内容基准仍是 `ee978f0`。审查文档基准见 `908d4f4`。缺陷状态一律 **未修复**；没有「实机通过」。error 级 DRC 0 **不等于** 全量检查通过（全量 148 条 DRC warning + 1 条 ERC warning）。

本文件是修复项目说明，**不是** 对任何规格偏离的批准。与规格书冲突的项必须先拿证据和两种方案问 Wisdom，再改 `design.py`。

---

## 1. 现在进度（一句话）

| 层 | 做到哪 | 没做到哪 |
|---|---|---|
| 设计 | 原理图/PCB/外壳/v0.1 自检可构建 | 未下单、无实物 |
| 检查 | error ERC/DRC 0；`--skip-route` 幂等 | 全量 warning、制造包丝印不同步、导出门禁可被绕过 |
| 硬件待决 | USB 0.8 mm 已拍板 | J1.7、升压、LDO、电池料号、模型、BOM 分类 |
| 固件 | v0.1 能编、bin 可复现 | 深睡 GPIO9、BOOT 入口、刷屏假成功、无 NDEF/FTM |

---

## 2. 必须先问 Wisdom 再动铜皮的项

这些不能靠「NC 接地通常没事」自行改板。讨论材料要写清：**保持现状的影响** vs **按规格改的影响**（是否清布线）。

| 编号 | 问题 | 现状 | 两种方向 |
|---|---|---|---|
| F06 | 屏脚 7 | 官方第 7 页 NC Keep Open；板上 GND 缝合 | **A** 书面接受偏离（精确屏版本+批准人）；**B** 改 `design.py` 恢复 NC，并改 `apply_extra_gnd_pads`，防后处理再接地 |
| N01 | 升压与第 29 页不一致 | L1 68 µH vs 47 µH/500 mA；C15 1 µF vs 4.7 µF；GDR 无 1 M 下拉；Q1 型号不同；R14 阻值对、封装功率未锁 | **A** 用现料号给出饱和/DCR/波形依据并接受；**B** 换料（可能动布局，讨论后再说是否 Freerouting） |
| F07 | LDO 电容 | XC6220 近端 C3=1 µF、C4=2.2 µF，未核有效容值 | **A** 锁具体电容料号+DC bias；**B** 改容值/封装 |
| F17 | 电池/充电器 | TP4054 与 MCP73831 并列；电芯未锁 | 锁一颗充电器、带 PCM 的电芯、极性、J2；无电池 USB 场景允许失败但要写明 |
| F05 | 网络类未进工程 | `NET_CLASSES` 声明了 Power/NFC，PCB 只有 Default | 先批准强制最小宽度 vs 首选宽度；**不要**只加分类就声称现板已满足（现板 Power/NFC 有 0.15/0.2 mm 段） |

USB 0.8 mm、NFC 线圈盖绿油：**已决策，本项目不重开。**

---

## 3. 硬件修复怎么排（本阶段）

原则：能不动铜皮就不动；`gen_pcb.py` 会清全部布线，禁止当普通检查。Freerouting 仅在 Wisdom 批准铜皮/焊盘/板框变化后，按交接第 3 节交互 shell + 相对路径。

### 工作包 H1 — 检查与制造门禁（建议最先，几乎不改电路）

不修这些就不要声称「可以下 Gerber」。

| 编号 | 改哪里 | 注意 |
|---|---|---|
| F04 | `hardware/pcb/scripts/export.sh` | 去掉 DRC `\|\| true`；ERC/DRC **违规**和**命令失败**都要非零退出；失败不得写看似可下单的包 |
| F19 | `route_pcb.py::drc_json` | 命令返回 5 时禁止读旧空报告当 PASS |
| F18 / N02 | 制造包流程 | **新建目录/新 zip**，禁止原地更新旧 zip；门禁过后再导出；必须含 **当前** `badge-B_Silkscreen.gbr`（r2 已证实与旧包坐标不同） |
| F15 | BOM/位置 | 工程 BOM 可留 ANT1/TP；另出贴装 BOM，C11 DNP 策略写死 |
| F16（模型） | 补 `lib/3d/TYPE-C-31-M-14.step`；核 J2 官方库路径 | STEP 返回 0 **不能**当模型齐全；缺模型要阻断发布 |

**本机验收（无板）：** `fault_probes` 在修完后必须改断言：DRC 失败不得走到 Gerber；旧报告注入必须失败。再用新隔离目录跑 `tools/review`，全量 warning 列表进豁免表（类型、对象、理由、批准人、失效条件），不能默认吞掉。

### 工作包 H2 — 规格冻结后的原理图/BOM（可能改 `design.py`，尽量不重布）

仅在第 2 节讨论出结论后执行。入口永远是 `design.py`，再 `gen_schematic.py`。不要手改 `.kicad_sch`。

- 只改阻焊/丝印/文档：**不要** `gen_pcb.py`。
- 改网络/焊盘/板框：先备份当前 `badge.kicad_pcb` 与布线指纹 `2d96f275…`，再决定是否 Freerouting。
- 后处理之后核对：设计网络、原理图网络、PCB 焊盘，不能只看 error DRC。
- 全量 148 条 warning 里，真实丝印：D3 参考被阻焊截、Q2 轮廓叠 D3 字、过小文字。若本包顺手修丝印，只动丝印坐标，仍禁止 Freerouting。

### 工作包 H3 — 不改电路、但要登记的硬件债

| 编号 | 做什么 | 不要做什么 |
|---|---|---|
| F13 | 追 USB D+/D− 端到端和回流，写审查笔记 | 不要用网络总长当差分失配；未批准不要重布 USB |
| F14 | C11 DNP/实装调谐表 | 不要为了 3D 好看重开线圈阻焊 |
| F03 硬件侧 | ADR/BOM 里「13 µA / 两年」改为待测 | 未测电流不要改成新的虚假续航数字 |

外壳 FPC/胶/真电池包络：有板再测，H 阶段只补模型与文档，不宣称装配通过。

---

## 4. 固件修复怎么排（硬件门禁和规格讨论之后）

保留 `firmware/output/badge-42c-v0.1.bin` 作基线，新版本升号（如 v0.2），不要覆盖 v0.1 三份 bin 当「没变过」。修完后 `host_probes` **必须改期望**：BUSY 恒高、关电超时不得再报成功。

### 工作包 F1 — 让错误可见（先于收图）

| 编号 | 文件 | 怎么修 | 注意 |
|---|---|---|---|
| F01 | `firmware/src/main.cpp::go_sleep` | 深睡 mask **不要 GPIO9**（本机构建 IDF 4.4.7 只允许 GPIO0–5）；检查 `esp_deep_sleep_enable_gpio_wakeup` 返回值，失败不准打印「可用 BOOT 唤醒」 | GPIO9 是 strap；按住 BOOT+复位是 ROM 下载，不能当应用自检 |
| F02 | `setup` + `firmware/README.md` | 正常启动后用串口命令或明确时间窗做刷白；与烧录入口分开 | 冷启动 / RESET / 烧录后三种都要可重复 |
| F09 | `firmware/src/epd.cpp` | 上电/刷新/关电等待都要进返回值；日志带阶段名 | 第 31 页 OTP 命令本身与规格一致，不要整段推翻；假成功已在 r2 的 20 用例里复现 |
| F12 | `main.cpp` 状态 | 任何失败路径关掉屏电源（`EPD_PWR_EN`） | 无板只能查代码路径；反灌/hold 要实机 |

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

1. H1 合入后：导出门禁故障路径变绿（按新断言），仍无生产 zip。
2. Wisdom 书面回复 F06/N01/F07/F17。
3. 若有铜皮变更：单独提交，带旧板指纹与是否 Freerouting 的说明。
4. 再开 F1 固件会话。
5. 有板之后才做合并计划第 4 节实物单；未测项保持待验证。
