# 项目交接文档（进度快照：2026-09-13 晚）

给接手的下一位（人或 AI 模型）：读完这一份 + `docs/01-architecture-decisions.md` 就能继续。
**不要推翻 ADR。** 硬件改动一律先改 `hardware/pcb/scripts/design.py`，再跑生成脚本。不要手改 `.kicad_sch`。

## 新会话请直接粘贴这段

```
继续 BADGE-42C（4.2 寸四色墨水屏 NFC 工牌）。先读 docs/03-handoff.md 和 docs/01-architecture-decisions.md。

用户 Wisdom，始终用中文回复。硬件改动从 hardware/pcb/scripts/design.py 开始，不要手改 .kicad_sch；不要跑 gen_pcb.py 除非准备好重新 Freerouting（会清布线）。Freerouting 必须按 docs/03-handoff.md 第 3 节从交互 shell、相对路径启动。

当前优先级：
1. 把 GND 缝合做成可从 78 过孔原板复现的 DRC 清零（见交接文档第 5 节第 1 步；板本身已经是 564 段/128 过孔、DRC 0，但脚本从干净板 skip-route 还会剩 1 个 B.Cu 孤岛）。
2. NFC 线圈盖绿油（gen_nfc_footprint.py 去掉 F.Mask/B.Mask）后按第 3 节重布线。
3. 写完 docs/04-review-checklist.md（草稿已有调研结论，缺官方 GDEM042F86 PDF 页码）。
4. 固件第一版，见 firmware/README.md。

提交前跑 check_netlist.py 和 export.sh。不要建 PR，除非用户明确要求。
```

---

## 0. 一句话

4.2 寸四色墨水屏 NFC 工牌（产品名 **BADGE-42C**）：ESP32-C3-MINI-1-N4 + ST25DV64KC + 超薄锂电 + USB-C，整机约 6.3 mm。
原理图、PCB（已自动布线 + GND 缝合）、外壳（FreeCAD）、BOM 都已生成。
**打样前还差：NFC 盖绿油重布线、封装人工复核、固件。**

## 1. 仓库结构

```
docs/
  01-architecture-decisions.md   选型与取舍（屏/供电/NFC/厚度/续航）——先读
  02-bom-and-cost.md             人读 BOM + 成本估算 + 替代料
  03-handoff.md                  本文
  04-review-checklist.md         打样前人工复核（进行中，已有部分结论）
hardware/pcb/                    KiCad 9 工程（由脚本生成）
  scripts/design.py              **唯一事实来源**
  scripts/gen_schematic.py       -> badge.kicad_sch
  scripts/gen_nfc_footprint.py   -> lib/badge.pretty/NFC_Loop.kicad_mod
  scripts/gen_pcb.py             -> badge.kicad_pcb（放置/板框/禁布区/铺铜；不布线）
  scripts/route_pcb.py           Freerouting 导入 + 缺口修补 + GND 缝合 + DRC
  scripts/check_netlist.py
  scripts/export.sh
  lib/                           Espressif 符号、ESP32-C3-MINI-1、TYPE-C-31-M-14、NFC_Loop
hardware/enclosure/              FreeCAD 前框 + 后盖
firmware/README.md               引脚表；固件代码尚未开始
```

## 2. 环境

| 工具 | 版本 / 位置 |
|---|---|
| KiCad | 9.0.9，`kicad-cli` + `python3 -c "import pcbnew"` |
| FreeCAD | 1.1.3，`/opt/freecad/squashfs-root`，`freecadcmd` |
| Freerouting | 2.4.1 `/opt/freerouting/freerouting.jar`，Java 25：`/opt/freerouting/jre25/bin/java` |

## 3. 完整复现流程

```bash
cd hardware/pcb
python3 scripts/gen_nfc_footprint.py
python3 scripts/gen_schematic.py
kicad-cli sch export netlist -o output/badge.net badge.kicad_sch && python3 scripts/check_netlist.py
python3 scripts/gen_pcb.py                # 会清掉全部布线，只在改封装/板框时跑
python3 -c "import pcbnew; b=pcbnew.LoadBoard('badge.kicad_pcb'); pcbnew.ExportSpecctraDSN(b,'output/badge.dsn')"
cd output && rm -f badge.ses && /opt/freerouting/jre25/bin/java -jar /opt/freerouting/freerouting.jar \
      -de badge.dsn -do badge.ses -mp 100 -mt 1 > freerouting.log 2>&1 && cd ..
python3 scripts/route_pcb.py --import-only
./scripts/export.sh
cd ../enclosure && freecadcmd badge_enclosure.py
```

只补 GND、不动走线：

```bash
cd hardware/pcb
python3 scripts/route_pcb.py --skip-route
```

**已知坑**

1. Freerouting 2.4.1 必须从**交互 shell、相对路径**启动，输出重定向到文件。Python `subprocess` 或绝对 `-do` 路径会得到 0 字节 `.ses`。`route_pcb.py` 里已改成 `os.system` + `cwd=output`，但仍建议按上面手工跑 java 再 `--import-only`。
2. `ZONE_FILLER` 对内存中新建的 `BOARD()` 会段错误，必须先保存再 `LoadBoard`。
3. `FOOTPRINT.Flip(LEFT_RIGHT)` 后要用 `GetOrientationDegrees()+rot` 叠加。
4. 乐鑫符号库是 KiCad 10 格式，`kicad_sym.py` 会剥 v10 token。
5. `.kicad_sch` 的 `lib_symbols` 子单元名必须是裸的 `Name_0_1`。
6. 板边铜间距放到 0.1 mm（沉板 USB-C 外壳焊盘贴边）。

## 4. 当前状态

| 项 | 状态 |
|---|---|
| 原理图 | 57 元件、41 网络；ERC 0；网表与 `design.py` 一致。J1 pin 7 已改为 GND（屏上该脚在 Waveshare 4.2" G 规格为 NC） |
| PCB 文件 | **91×84 mm，2 层 0.8 mm，元件全在 B.Cu**。当前板：**564 段走线、128 过孔，DRC error = 0，unconnected = 0** |
| 过孔规则 | 最小过孔 0.4 mm、钻孔 0.2 mm（`gen_pcb.py` / `badge.kicad_pro` / `route_pcb.py`） |
| ESP32 | 封装 `ESP32-C3-MINI-1.kicad_mod` 加了 GND `net_tie_pad_groups`（脚 1,2,11,14,36–53 模组内部共地） |
| NFC 线圈 | 11 圈约 35×41.5 mm，L≈4.6 µH，与 ST25DV 28.5 pF 约 13.96 MHz。**焊盘仍带 F.Mask/B.Mask（裸铜），未盖绿油** |
| 外壳 | 94×93×6.3 mm，前框+后盖，与 PCB STEP 无干涉 |
| 固件 | 未写，只有 `firmware/README.md` 引脚表 |

`output/drc_final.json` 应对应当前板：`violations: []`、`unconnected_items: []`。Gerber/STEP/渲染若与 128 过孔板不同步，跑一次 `./scripts/export.sh`。

## 5. 下一步（按优先级）

### 1. GND 铺铜孤岛（进行中，板已清零，脚本尚未可复现）

**根因**：DRC 报的是同一 `GND_B.Cu` 的 Zone vs Zone，不是焊盘未连。B.Cu 被走线切成带 GND 焊盘的多边形，`ISLAND_REMOVAL_MODE_ALWAYS` 不会删它们。F.Cu 原本是整块地。

**已写进 `route_pcb.py` 的策略**（`--skip-route` 即可，不要重跑 Freerouting）：

1. `via_fits` 用 `pad.HitTest`，同网络铜允许重叠；默认间距 0.22 mm。
2. `apply_extra_gnd_pads()`：J1 pin 7 → GND（现有 PCB 上改网络，避免 `gen_pcb.py`）。
3. `apply_esp_gnd_nettie()`：运行时给 U1 加 GND net-tie。
4. 电池仓 GND 过孔网格（约 27 个）。
5. 两阶段 `stitch_islands`：先任意孤岛一孔，再尽量打到另一层主铺铜。
6. `stitch_leftover_to_main`：孤岛 ∩ F.Cu 主铺铜上打 0.4/0.2 孔。
7. `stitch_cluster_overlaps`：剩余簇的 F.Cu 孤岛 ∩ 主簇 B.Cu。
8. `jumper_islands`：并查集后短跳线（密集区几乎走不通）。
9. `nudge_clearance_vias`：DRC clearance 时把 GND 过孔挪 0.08–0.25 mm。

**已验证有效、写进当前 `badge.kicad_pcb` 的两处手工微调**（从干净 78 过孔板 skip-route 时可能再现 0.18 mm 间距）：

- C7 附近：`(51.50, 54.45)` → **`(51.39, 54.55)`**（躲开 F.Cu `EPD_PWR_EN` y≈53.97）
- overlap 过孔：`(66.09, 49.47)` → **`(66.09, 49.62)`**（躲开 F.Cu `NFC_GPO` y≈48.99）

**脚本复现缺口（2026-09-13 晚测过）**：`git` 上的 78 过孔原板 + 当前 `route_pcb.py --skip-route` → 约 564 段 / 127 过孔，**还剩 1 条 B.Cu Zone vs Zone**（C7 附近约 2.57 mm²，bbox ≈ 50.9,52.9–53.5,54.7）。原因：第一轮 `stitch_islands` 已经在孤岛上打了孔，但不在 F.Cu 主铺铜上；`leftover` 再打 overlap 孔时 `via_fits` 的 GND 过孔最小间距 0.55 mm 把位置挡死。

**下一步该怎么改脚本（不要再走失败路线）**：

- 在 `stitch_leftover_to_main` 里：对仍不与 F.Cu 主铺铜 overlap 的孤岛，**先删掉该孤岛上不在 fmain 上的 GND 过孔**，再打 overlap 孔。
- 或：第一轮 `stitch_islands` 不要在「无法打到另一层主铺铜」的孤岛上占坑。
- 清零后应用 `nudge_clearance_vias`（Power 网络要 0.20 mm，0.20 clr 会放到 0.18）。

**不要再走**：

- 每个几何孤岛每轮都打孔（电已通仍打）→ 过孔爆炸、大量 DRC。
- B.Cu `ZONE_CONNECTION_NONE` + 给孤立焊盘打孔+线 → 短路。
- 把 `EPD_RESE` 整段 y=69.98 挪开 → 和 `EPD_VSH2` 短路。
- 移动 `I2C_SCL` 过孔合并 F.Cu → 更差。

验证：`cd hardware/pcb && python3 scripts/route_pcb.py --skip-route` 应 exit 0；`output/drc_final.json` 空 violations / unconnected。

### 2. NFC 线圈盖绿油（未做）

`hardware/pcb/scripts/gen_nfc_footprint.py`：

- pad 1：`(layers "F.Cu" "F.Mask")` → 只留 `"F.Cu"`
- pad 2 自定义桥：`(layers "B.Cu" "B.Mask")` → 只留 `"B.Cu"`
- 通孔 pad 2 保留 `*.Mask`

然后必须：`gen_nfc_footprint.py` → `gen_pcb.py`（清布线）→ **手工 Freerouting**（第 3 节）→ `route_pcb.py --import-only`（此时缝合逻辑应已可用）。

### 3. 打样前复核

见 `docs/04-review-checklist.md`。关键未闭合项：官方 GDEM042F86 规格书 PDF（站点 WAF 403），TYPE-C-31-M-14 图纸写 0.75 mm 板厚 vs 我们 0.8 mm。

### 4. 固件

`firmware/README.md`。建议：屏驱动 → 深睡/唤醒 → ST25DV NDEF+FTM → BLE/SoftAP。

## 6. 约定

- 一切硬件改动从 `design.py` 开始；`.kicad_pcb` 布线可手改，但 `gen_pcb.py` 会清掉。
- 单位 mm。PCB：正面视角、原点左上、Y 向下。FreeCAD：X 同 PCB，Y = −PCB y，Z 朝正面。
- 提交前跑 `check_netlist.py` 和 `export.sh` 的 ERC/DRC。
- 用户 Wisdom，回复用中文。不要为「继续」去推翻 ADR。
