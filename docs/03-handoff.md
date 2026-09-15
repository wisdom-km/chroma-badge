# 项目交接文档

进度快照：**2026-09-15 H2 + 固件 v0.2 F1**。历史 2026-09-14 旧板（57 件 / 564 段 / 脚 7 GND）只在第 7 节。

给接手的下一位（人或 AI）：先读 [AGENTS.md](../AGENTS.md)、本文、[01-architecture-decisions.md](01-architecture-decisions.md)、[09-process.md](09-process.md)。**不要推翻 ADR。** 硬件改动一律先改 `hardware/pcb/scripts/design.py`，再跑生成脚本。不要手改 `.kicad_sch`。

## 新会话请直接粘贴这段

```
继续 BADGE-42C（4.2 寸四色墨水屏 NFC 工牌）。先读 AGENTS.md、docs/03-handoff.md、docs/01-architecture-decisions.md、docs/09-process.md。

用户 Wisdom，始终用中文回复。硬件改动从 hardware/pcb/scripts/design.py 开始，不要手改 .kicad_sch；不要跑 gen_pcb.py 除非铜皮/焊盘/板框变了并准备好重新 Freerouting（会清布线）。只改阻焊/丝印用 apply_hygiene.py，不要重布。Freerouting 必须按 docs/03-handoff.md 第 3 节从交互 shell、相对路径启动。文档和板上事实冲突时先问用户。3D/截图不确定时先读 docs/05-visual-check.md。

当前板：58 封装、680 段 / 115 过孔，J1.7 NC Keep Open。KiCad 10.0.6 全量 ERC/DRC 0。固件 v0.2 F1（深睡仅 GPIO1；串口 W 刷白）。不要覆盖 firmware/output/badge-42c-v0.1*.bin。不要把候选 Gerber 当生产包。

下一步：有板实测 USB/充电/BUSY/NFC/电流；F2 须 Wisdom 选定 NDEF/FTM 或 BLE/SoftAP 一条路线。

提交前：hardware/pcb 下 python scripts/check_netlist.py；有 KiCad 时 ./scripts/export.sh --check-only。不要建 PR，除非用户明确要求。
```

---

## 0. 一句话

4.2 寸四色墨水屏 NFC 工牌（**BADGE-42C**）：ESP32-C3-MINI-1-N4 + ST25DV64KC + 超薄锂电 + USB-C，整机约 6.3 mm。

**当前板已通过 KiCad 10.0.6 全量 ERC/DRC。** USB 按 0.8 mm 打样。J1.7 NC。固件 v0.2 是上电自检，不是工牌传图。没有授权生产 zip。

## 1. 仓库结构

```
LICENSE.md / LICENSES/MIT.txt     硬件 CERN-OHL-P-2.0；固件/脚本 MIT
.github/workflows/ci.yml          网表 + host_probes + pio（不是 DRC）
docs/
  01-architecture-decisions.md    选型（先读）
  02-bom-and-cost.md              人读 BOM；屏贴胶 3M 467MP
  03-handoff.md                   本文
  04-review-checklist.md          打样前人工复核
  05-visual-check.md              3D/截图：拍错 vs 板上问题
  06-current-status.md            审查状态入口
  07-defect-fix-project.md        H/F 工作包
  08-h2-h3-questions.md           已关闭拍板记录
  09-process.md                   许可证 / CI / 贴胶 / 生产包
  hardware/drc-warning-register.md  全量 warning（现为 0）
hardware/pcb/                     KiCad 工程（原理图由脚本生成）
  scripts/design.py               **唯一事实来源**
  scripts/gen_schematic.py
  scripts/gen_pcb.py              清全部布线；仅铜皮/焊盘/板框
  scripts/apply_hygiene.py        活板丝印/FPID/NC；不动走线
  scripts/route_pcb.py            导入 + GND 缝合 + DRC
  scripts/export.sh               默认候选目录，不是生产包
firmware/                         PlatformIO v0.2 自检；output/ 里 v0.1 是基线 bin
```

全量 ERC/DRC 用 **KiCad 10.0.6**（`C:\Users\19612\AppData\Local\Programs\KiCad\10.0\bin`）。KiCad 9 读不了工程里的 `Espressif.kicad_sym`（10 格式）。`pcbnew` 脚本（`apply_hygiene.py`）仍可用本机 KiCad 9 Python，以免改写板文件格式。

## 2. 环境

| 工具 | 版本 / 位置 |
|---|---|
| KiCad 全量检查 | **10.0.6**，`C:\Users\19612\AppData\Local\Programs\KiCad\10.0\bin` |
| KiCad pcbnew 脚本 | 可选 9.0.x `python.exe`（`apply_hygiene` / 部分生成） |
| FreeCAD | 本机 Windows：`D:\FreeCAD\bin\freecadcmd.exe`（1.1.3） |
| Freerouting | 2.4 + Java 25；jar 本机自备，不入库 |
| PlatformIO | **6.2.0** + `espressif32@7.1.3`（见 `firmware/platformio.ini`） |
| 固件 host 探针 | g++（本机 MinGW 13.1.0） |

## 3. 完整复现流程

不要把下面 `gen_pcb.py` 当成日常命令。只改丝印/阻焊：`apply_hygiene.py`。只补 GND：`--skip-route`。

```bash
cd hardware/pcb
python3 scripts/gen_nfc_footprint.py
python3 scripts/gen_schematic.py
kicad-cli sch export netlist -o output/badge.net badge.kicad_sch && python3 scripts/check_netlist.py
python3 scripts/gen_pcb.py                # 会清掉全部布线
python3 -c "import pcbnew; b=pcbnew.LoadBoard('badge.kicad_pcb'); pcbnew.ExportSpecctraDSN(b,'output/badge.dsn')"
cd output && rm -f badge.ses && java -jar <freerouting.jar> \
      -de badge.dsn -do badge.ses -mp 100 -mt 1 > freerouting.log 2>&1 && cd ..
python3 scripts/route_pcb.py --import-only
./scripts/export.sh --check-only          # 日常；不要 --production
```

Freerouting 必须从**交互 shell、相对路径**启动，输出重定向到文件。Python `subprocess` 或绝对 `-do` 会得到 0 字节 `.ses`。

只补 GND、不动走线：

```bash
cd hardware/pcb
python3 scripts/route_pcb.py --skip-route
```

只动丝印/封装前缀/NC 网（不清布线）：

```bash
cd hardware/pcb
python3 scripts/apply_hygiene.py
python3 scripts/gen_schematic.py
```

**已知坑**

1. Freerouting 必须交互 shell + 相对路径，见上。
2. `ZONE_FILLER` 对内存中新建的 `BOARD()` 会段错误，必须先保存再 `LoadBoard`。
3. `FOOTPRINT.Flip(LEFT_RIGHT)` 后要用 `GetOrientationDegrees()+rot` 叠加。
4. 乐鑫符号是 **KiCad 10** 格式。全量检查用 10.0.6；`gen_schematic.py` 按 10 嵌入，**不要再剥 v10 token**。
5. `.kicad_sch` 的 `lib_symbols` 子单元名必须是裸的 `Name_0_1`。
6. 板边铜间距 0.1 mm（沉板 USB-C 外壳焊盘贴边）。
7. **只改阻焊不要重布线。** 旧文档曾写「改 NFC 封装必须 `gen_pcb.py`」。线圈铜皮没变时清布线会丢掉已验证走线。
8. 文档和板上事实冲突：**先问用户**，不要自行换流程或 Freerouting。
9. 3D/截图看不清：`docs/05-visual-check.md`。拍错自己修图。
10. `export.sh --production` 会直接拒绝。候选目录不是下单包。

## 4. 当前状态（H2 板）

| 项 | 状态 |
|---|---|
| 原理图 | **58** 元件；KiCad 10.0.6 全量 ERC 0；网表 == `design.py`。J1 pin **7 = NC Keep Open** |
| PCB | 91×84 mm，2 层 0.8 mm，元件全在 B.Cu。**680 段 / 115 过孔**。全量 DRC 0、未连接 0、parity 0 |
| 线宽 | Power ≥0.3 mm（GND 靠铺铜）；NFC 0.5 mm；USB 0.8 mm |
| 过孔 | 最小 0.4 mm、钻孔 0.2 mm |
| U2 | `Badge:ST25DV64KC-SO8N`（8 脚，不是官方 UFDFPN+EP） |
| NFC 线圈 | 11 圈约 35×41.5 mm；SMD 盖绿油；通孔 pad 2 仍开窗；C11 **DNP** |
| 外壳 | 约 94×93×6.3 mm；`ACTIVE_TOP=6.7` |
| 固件 | **v0.2 F1**：USB 日志、VBAT、I²C ACK、串口 `W` 刷白、深睡仅 GPIO1。v0.1 bin 在 `firmware/output/` 作基线 |
| 制造 | 无生产 zip。旧 `output/gerbers` 不要当下单文件 |

`output/drc_all_h2.json` / `erc_all_h2.json`：全量 0。`drc_final.json`：error 级 0。全量 0 ≠ 生产包。

## 5. 下一步

1. 授权生产包后再打样（新目录 + manifest）。见 [09-process.md](09-process.md)。
2. 有板：USB、充电、`W` 刷白、NFC 唤醒、电流。
3. F2：Wisdom 选定 **一条** 传图路线后再写。
4. 不要重开 USB 0.8 mm、NFC 绿油、脚 7 NC。

## 6. 约定

- 硬件从 `design.py` 起手；`gen_pcb.py` 会清布线。
- 单位 mm。PCB：正面视角、原点左上、Y 向下。
- 提交前：`check_netlist.py`；有 KiCad 则 `export.sh --check-only`。
- 用户 Wisdom，回复中文。不要推翻 ADR。
- 许可证与 CI 见 [09-process.md](09-process.md)。

## 7. 历史：2026-09-14 旧板（不要当现板）

当时指纹：**57 件、564 段、128 过孔、J1.7 被后处理接到 GND**。复审证据在 `docs/reviews/2026-09-14/`。H2 已重布为 680/115，脚 7 空网；`apply_extra_gnd_pads` **禁止再把脚 7 接地**。

GND 缝合策略仍在 `route_pcb.py --skip-route`（现板应保持 680/115 幂等）。不要用「每个几何孤岛都打孔」或 `ZONE_CONNECTION_NONE` 那套已否决路径。

NFC 盖绿油的正确做法未变：只改 ANT1 SMD 的 Mask/Paste，不要为此 `gen_pcb.py`。
