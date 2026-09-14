# 项目交接文档（进度快照：2026-09-14）

> **同日本机复审补充：** 接手同时阅读 [06-current-status.md](06-current-status.md)、[独立复审](reviews/2026-09-14/local-review.md)、[合并整改计划](reviews/2026-09-14/integrated-plan.md) 和 [测试手册](../tools/review/README.md)。本页保留原交接历史；error级DRC0不代表全量warning0、固件可构建不代表实机通过。本轮发现的冲突与待决项没有被自动批准或改板。

给接手的下一位（人或 AI 模型）：读完这一份 + `docs/01-architecture-decisions.md` 就能继续。
**不要推翻 ADR。** 硬件改动一律先改 `hardware/pcb/scripts/design.py`，再跑生成脚本。不要手改 `.kicad_sch`。

## 新会话请直接粘贴这段

```
继续 BADGE-42C（4.2 寸四色墨水屏 NFC 工牌）。先读 docs/03-handoff.md 和 docs/01-architecture-decisions.md。

用户 Wisdom，始终用中文回复。硬件改动从 hardware/pcb/scripts/design.py 开始，不要手改 .kicad_sch；不要跑 gen_pcb.py 除非铜皮/焊盘/板框变了并准备好重新 Freerouting（会清布线）。只改阻焊不要重布。Freerouting 必须按 docs/03-handoff.md 第 3 节从交互 shell、相对路径启动。文档和板上事实冲突时先问用户。3D/截图不确定时先读 docs/05-visual-check.md：拍错自己重拍，真问题再问。

当前优先级：
1. ~~GND 缝合可复现~~：`route_pcb.py --skip-route` 从 bce5813 的 78 过孔原板 → **564 段 / 128 过孔，DRC 0**，再跑一遍幂等。
2. ~~NFC 线圈盖绿油~~：ANT1 SMD 焊盘已去掉 Mask（线圈盖绿油），通孔 pad 2 仍开窗。布线仍是 564/128、DRC 0。
3. 写完 docs/04-review-checklist.md。官方 GDEM042F86 PDF 已对照（脚序/RESE/ACTIVE_TOP=6.7）。USB **按 0.8 mm 打样**（嘉立创无 0.75）。剩下脚 7 Keep Open vs GND。
4. 固件 v0.1 上电自检已在 firmware/（PlatformIO）。下一步 NDEF/FTM 收图。

提交前跑 check_netlist.py 和 export.sh。不要建 PR，除非用户明确要求。
```

---

## 0. 一句话

4.2 寸四色墨水屏 NFC 工牌（产品名 **BADGE-42C**）：ESP32-C3-MINI-1-N4 + ST25DV64KC + 超薄锂电 + USB-C，整机约 6.3 mm。
原理图、PCB（已自动布线 + GND 缝合）、外壳（FreeCAD）、BOM 都已生成。
**USB 按 0.8 mm 打样。** 打样前还差：脚 7 可选拍板、固件 NDEF/FTM。GND 缝合可复现；NFC 线圈已盖绿油。

## 1. 仓库结构

```
docs/
  01-architecture-decisions.md   选型与取舍（屏/供电/NFC/厚度/续航）——先读
  02-bom-and-cost.md             人读 BOM + 成本估算 + 替代料
  03-handoff.md                  本文
  04-review-checklist.md         打样前人工复核（进行中，已有部分结论）
  05-visual-check.md              3D/截图：先分清拍错还是板上真问题
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
firmware/                       PlatformIO：ESP32-C3 上电自检 + GDEM042F86 OTP 刷白
```

## 2. 环境

| 工具 | 版本 / 位置 |
|---|---|
| KiCad | 9.0.9，`kicad-cli` + `python3 -c "import pcbnew"` |
| FreeCAD | 本机 Windows：`D:\FreeCAD\bin\freecadcmd.exe`（1.1.3）。Linux 交接机：`/opt/freecad/squashfs-root`，`freecadcmd` |
| Freerouting | 2.4.1 `/opt/freerouting/freerouting.jar`，Java 25：`/opt/freerouting/jre25/bin/java` |

## 3. 完整复现流程

```bash
cd hardware/pcb
python3 scripts/gen_nfc_footprint.py
python3 scripts/gen_schematic.py
kicad-cli sch export netlist -o output/badge.net badge.kicad_sch && python3 scripts/check_netlist.py
python3 scripts/gen_pcb.py                # 会清掉全部布线。只在改铜皮/焊盘位置/板框时跑；只改阻焊或丝印不要跑
python3 -c "import pcbnew; b=pcbnew.LoadBoard('badge.kicad_pcb'); pcbnew.ExportSpecctraDSN(b,'output/badge.dsn')"
cd output && rm -f badge.ses && /opt/freerouting/jre25/bin/java -jar /opt/freerouting/freerouting.jar \
      -de badge.dsn -do badge.ses -mp 100 -mt 1 > freerouting.log 2>&1 && cd ..
python3 scripts/route_pcb.py --import-only
./scripts/export.sh
cd ../enclosure && D:/FreeCAD/bin/freecadcmd.exe badge_enclosure.py   # Linux: freecadcmd badge_enclosure.py
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
7. **只改阻焊不要重布线。** 旧文档曾写「改 NFC 封装必须 `gen_pcb.py` + Freerouting」，那是错的。线圈铜皮没变时，清布线会丢掉已验证的 564/128 板；本机 Freerouting 还把 USB D+/D− 布短路过。`gen_pcb.py` 只在铜皮、焊盘位置或板框变了时才跑。
8. 发现文档和板上事实冲突时：**先问用户，讨论后再改**，不要自行换流程。
9. **3D/截图看不清 ≠ 板上有问题。** 先读 `docs/05-visual-check.md`，对准目标重拍、核对 `design.py` / `badge.kicad_pcb`。拍错了自己修图；确认是板上问题才问 Wisdom。近景没拍到目标时，禁止说「没法 100% 从 3D 断定」。

## 4. 当前状态

| 项 | 状态 |
|---|---|
| 原理图 | 57 元件、41 网络；ERC 0；网表与 `design.py` 一致。J1 pin 7 已改为 GND（屏上该脚在 Waveshare 4.2" G 规格为 NC） |
| PCB 文件 | **91×84 mm，2 层 0.8 mm，元件全在 B.Cu**。当前板：**564 段走线、128 过孔，DRC error = 0，unconnected = 0** |
| 过孔规则 | 最小过孔 0.4 mm、钻孔 0.2 mm（`gen_pcb.py` / `badge.kicad_pro` / `route_pcb.py`） |
| ESP32 | 封装 `ESP32-C3-MINI-1.kicad_mod` 加了 GND `net_tie_pad_groups`（脚 1,2,11,14,36–53 模组内部共地） |
| NFC 线圈 | 11 圈约 35×41.5 mm，L≈4.6 µH，与 ST25DV 28.5 pF 约 13.96 MHz。**SMD 焊盘已去掉 Mask（盖绿油）**；通孔 pad 2 仍 `*.Mask` |
| 外壳 | 94×93×6.3 mm，前框+后盖，与 PCB STEP 无干涉 |
| 固件 | v0.1：USB 日志、VBAT、ST25DV 探测、BOOT 全白 OTP 刷新、GPO/BOOT 深睡唤醒 |

`output/drc_final.json` 应对应当前板：`violations: []`、`unconnected_items: []`。Gerber/STEP/渲染若与 128 过孔板不同步，跑一次 `./scripts/export.sh`。

## 5. 下一步（按优先级）

### 1. GND 铺铜孤岛（已完成，脚本可复现）

**根因**：DRC 报的是同一 `GND_B.Cu` 的 Zone vs Zone，不是焊盘未连。B.Cu 被走线切成带 GND 焊盘的多边形，`ISLAND_REMOVAL_MODE_ALWAYS` 不会删它们。F.Cu 原本是整块地。

**已写进 `route_pcb.py` 的策略**（`--skip-route` 即可，不要重跑 Freerouting）：

1. `via_fits` 用 `pad.HitTest`，同网络铜允许重叠；默认间距 0.22 mm。
2. `apply_extra_gnd_pads()`：J1 pin 7 → GND（现有 PCB 上改网络，避免 `gen_pcb.py`）。
3. `apply_esp_gnd_nettie()`：运行时给 U1 加 GND net-tie。
4. 电池仓 GND 过孔网格（约 27 个）。
5. 两阶段 `stitch_islands`：先任意孤岛一孔，再尽量打到另一层主铺铜。
6. `stitch_leftover_to_main`：只处理并查集里**电学仍孤立**的 B.Cu 簇。先试 overlap 孔；失败才临时删掉该孤岛上不在 F.Cu 主铺铜的占坑过孔再打；overlap 仍失败则把占坑孔加回去，交给 cluster/jumper。
7. `stitch_cluster_overlaps`：剩余簇的 F.Cu 孤岛 ∩ 主簇 B.Cu。
8. `jumper_islands`：并查集后短跳线（密集区几乎走不通）；跳线不得穿过 NFC / 天线 keepout。
9. `nudge_clearance_vias`：DRC clearance 时把 GND 过孔挪 0.08–0.25 mm。

**2026-09-14 已复现（本机 Windows / KiCad 9.0.8）**：`git show bce5813:hardware/pcb/badge.kicad_pcb`（84 个 `(via` / 约 78 个布线过孔）+ 当前 `route_pcb.py --skip-route` → **564 段 / 128 过孔，DRC 0**。C7 孤岛 overlap 孔落在 `(51.45, 54.50)`，`clr=0.22`，无需再手工 nudge。再跑一遍 `--skip-route` 不增孔、仍清零。

**不要再走**：

- 每个几何孤岛每轮都打孔（电已通仍打）→ 过孔爆炸、大量 DRC。
- B.Cu `ZONE_CONNECTION_NONE` + 给孤立焊盘打孔+线 → 短路。
- 把 `EPD_RESE` 整段 y=69.98 挪开 → 和 `EPD_VSH2` 短路。
- 移动 `I2C_SCL` 过孔合并 F.Cu → 更差。

验证：`cd hardware/pcb && python3 scripts/route_pcb.py --skip-route` 应 exit 0；`output/drc_final.json` 空 violations / unconnected。

### 2. NFC 线圈盖绿油（已完成）

正确做法（铜皮没变，**不要** `gen_pcb.py` / Freerouting）：

1. `gen_nfc_footprint.py`：pad 1 只留 `"F.Cu"`，pad 2 桥只留 `"B.Cu"`，通孔 pad 2 仍 `*.Mask`
2. 在现有 DRC 清零板上改 ANT1 两个 SMD 焊盘的层（去掉 Mask/Paste），通孔不动
3. DRC 仍应 0；`badge-B_Mask.gbr` 应变小（线圈不再开窗）

**旧文档写错了**：曾要求改封装后必须 `gen_pcb.py` + 重布。那会清掉已验证的 564/128 走线。2026-09-14 按错流程试过一次 Freerouting，USB D+/D− 在 J3 短路（走线交叉），该结果已丢弃。现板仍是原来的 564/128，只盖了绿油。

以后只有铜皮、焊盘位置或板框变了，才 `gen_pcb.py` + 第 3 节 Freerouting + `route_pcb.py --import-only`。

### 3. 打样前复核

见 `docs/04-review-checklist.md`。官方 GDEM042F86（2026-06-17）已对照：脚 6/7=NC、RESE=2.2 Ω、ACTIVE_TOP=**6.7**（第 6 页，AA 竖直居中）。外壳按键/FPC 槽从 `design.py` 读。USB **已拍板 0.8 mm**（嘉立创无 0.75 档；M-14 标 0.75，公差盖住）。仍未闭合：脚 7 接 GND 缝合 vs Keep Open。

### 4. 固件

`firmware/`。v0.1 已能 USB 日志 / I²C 探测 / 按住 BOOT 刷白。下一步：ST25DV NDEF+FTM 收图 → 工牌画面 → BLE/SoftAP。

## 6. 约定

- 一切硬件改动从 `design.py` 开始；`.kicad_pcb` 布线可手改，但 `gen_pcb.py` 会清掉。
- 单位 mm。PCB：正面视角、原点左上、Y 向下。FreeCAD：X 同 PCB，Y = −PCB y，Z 朝正面。
- 提交前跑 `check_netlist.py` 和 `export.sh` 的 ERC/DRC。
- 用户 Wisdom，回复用中文。不要为「继续」去推翻 ADR。
- **文档或清单和板上事实冲突时，先停下来问用户，讨论确认后再改**，不要自行换流程或重布线。
- 3D/截图流程见 `docs/05-visual-check.md`。新踩的「拍错 vs 真问题」写进该文档再推。
