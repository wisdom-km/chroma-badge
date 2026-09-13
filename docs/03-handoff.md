# 项目交接文档（进度快照：2026-09-13）

给接手的下一位（人或 AI 模型）：这份文档说明项目现在做到哪、怎么复现、下一步做什么。
读完这一份 + `01-architecture-decisions.md` 就能继续。

## 0. 一句话

4.2 寸四色墨水屏 NFC 工牌，ESP32-C3 + ST25DV64KC + 超薄锂电，整机 6.3 mm。
**原理图、PCB（已自动布线）、外壳（FreeCAD）、BOM 都已生成并通过基本检查，处于"可打样前的复核阶段"。**
固件和手机/网页端尚未开始。

## 1. 仓库结构

```
docs/
  01-architecture-decisions.md   选型与取舍（屏/供电/NFC/厚度/续航），先读这个
  02-bom-and-cost.md             人读 BOM + 成本估算 + 替代料说明
  03-handoff.md                  本文
hardware/pcb/                    KiCad 9 工程（全部由脚本生成，不要手改 .kicad_sch）
  scripts/design.py              **唯一事实来源**：所有元件、封装、引脚→网络、PCB 坐标、板框/禁布区参数
  scripts/gen_schematic.py       design.py -> badge.kicad_sch（网表式原理图，每个引脚挂全局标签）
  scripts/gen_nfc_footprint.py   生成 NFC 螺旋天线封装 lib/badge.pretty/NFC_Loop.kicad_mod（net-tie，自定义焊盘）
  scripts/gen_pcb.py             design.py -> badge.kicad_pcb（放置、板框、开槽、禁布区、GND 铺铜；不布线）
  scripts/route_pcb.py           Freerouting 自动布线导入 + 缺口修补 + GND 缝合过孔 + DRC（JSON）
  scripts/check_netlist.py       校验原理图导出网表 == design.py
  scripts/export.sh              ERC/DRC、BOM、Gerber、钻孔、坐标、STEP、PDF/SVG/渲染图一键导出
  lib/                           项目库：Espressif 符号库、ESP32-C3-MINI-1 封装+STEP、TYPE-C-31-M-14 沉板 USB-C、NFC_Loop
  badge.kicad_pro / badge.kicad_sch / badge.kicad_pcb / fp-lib-table / sym-lib-table
  output/                        生成物：gerbers/、badge_gerbers.zip、badge_bom.csv、badge_pos_back.csv、
                                 badge_full.step、badge_schematic.pdf、render_back.png、drc_final.json ...
hardware/enclosure/
  badge_enclosure.py             FreeCAD 参数化脚本（前框 + 后盖 + 装配 + 干涉检查）
  output/                        badge_front_frame.{FCStd,step,stl}、badge_back_cover.*、badge_assembly.{FCStd,step}
firmware/README.md               引脚表、I²C 地址、刷屏时序约定（固件本身未写）
```

## 2. 环境（云端机器上已装好；换机器需要重装）

| 工具 | 版本 / 位置 | 用途 |
|---|---|---|
| KiCad | 9.0.9，PPA `ppa:kicad/kicad-9.0-releases`，`kicad-cli` + `python3 -c "import pcbnew"` | 原理图/PCB 生成、DRC、导出 |
| FreeCAD | 1.1.3 AppImage 解压在 `/opt/freecad/squashfs-root`，`freecad` / `freecadcmd` 在 PATH | 外壳建模（脚本驱动，不用 GUI） |
| Freerouting | 2.4.1 jar `/opt/freerouting/freerouting.jar`，需 Java 25：`/opt/freerouting/jre25/bin/java` | 自动布线 |
| Python 库 | `sexpdata`、`cadquery`（备用） | |
| 其他 | `openscad`、`rsvg-convert`、`zip` | 渲染、导出 |

## 3. 完整复现流程

```bash
cd hardware/pcb
python3 scripts/gen_nfc_footprint.py      # 若改了线圈参数
python3 scripts/gen_schematic.py          # -> badge.kicad_sch
kicad-cli sch export netlist -o output/badge.net badge.kicad_sch && python3 scripts/check_netlist.py
python3 scripts/gen_pcb.py                # -> badge.kicad_pcb（未布线）
python3 -c "import pcbnew; b=pcbnew.LoadBoard('badge.kicad_pcb'); pcbnew.ExportSpecctraDSN(b,'output/badge.dsn')"
cd output && rm -f badge.ses && /opt/freerouting/jre25/bin/java -jar /opt/freerouting/freerouting.jar \
      -de badge.dsn -do badge.ses -mp 100 -mt 1 > freerouting.log 2>&1 && cd ..
python3 scripts/route_pcb.py --import-only   # 导入 .ses、补缺口、GND 缝合、DRC
./scripts/export.sh                          # 全部生成物
cd ../enclosure && freecadcmd badge_enclosure.py   # 外壳 + 装配干涉检查（会读取 pcb/output/badge_full.step）
```

**已知坑（都已绕过，但要知道）**

1. Freerouting 2.4.1 只能从**交互 shell 直接启动**并用**相对路径**、输出重定向到文件；
   从 Python `subprocess` 启动（无论怎么重定向）或给绝对输出路径，都会留下 0 字节的 `.ses`。
   所以 `route_pcb.py` 默认的自动调用不可靠，请按上面的方式手动跑 java 再 `--import-only`。
2. pcbnew 的 `ZONE_FILLER` 对内存中新建的 `BOARD()` 会段错误，必须先保存再 `LoadBoard` 再填充（脚本已处理）。
3. `FOOTPRINT.Flip(LEFT_RIGHT)` 会把方向变成 180°，之后要用 `GetOrientationDegrees()+rot` 叠加而不是覆盖，否则变成上下镜像。
4. 乐鑫官方符号库是 KiCad 10 格式，`kicad_sym.py` 会剥掉 v10 才有的 token。
5. `.kicad_sch` 内 `lib_symbols` 的子单元名必须是裸的 `Name_0_1`，不能带 `Lib:` 前缀。
6. 板边铜间距规则被放宽到 0.1 mm，因为沉板 USB-C 的外壳焊盘紧贴开槽边。

## 4. 当前状态与检查结果

| 项 | 状态 |
|---|---|
| 原理图 | 57 个元件、41 个网络，ERC 0 error；网表与 design.py 一致 |
| PCB | 91×84 mm 两层 0.8 mm；562 段走线、78 过孔；**所有焊盘间连接均已布通**；DRC 仅剩 18 条 "GND 铺铜孤岛" unconnected（B.Cu 地铺铜被走线切成小岛，见下一步 #1） |
| NFC 线圈 | 11 圈 35×41.5 mm，估算 4.6 µH，与 ST25DV 内部 28.5 pF 谐振约 13.96 MHz（偏高 3%，C11 留了调谐位） |
| 外壳 | 94×93×6.3 mm，前框 + 后盖，与真实 PCB STEP（含元件）、面板、电池、USB 均无干涉 |
| 输出 | Gerber/钻孔/坐标/BOM/STEP/PDF 已在 `hardware/pcb/output/` |

关键截图：`hardware/pcb/output/render_back.png`（PCB 背面）、`render_front.png`、`badge_schematic.pdf`。

## 5. 下一步（按优先级）

1. **GND 铺铜孤岛**：在 `route_pcb.py` 里对"仅含 Zone 的 unconnected 对"处理——要么把 B.Cu 地铺铜孤岛移除策略改为
   `ISLAND_REMOVAL_MODE_AREA`（面积阈值），要么在孤岛内补缝合过孔（`Stitcher` 已有 `via_fits/add_via`，
   缺的是从 DRC JSON 拿到孤岛位置——可用 `zone.GetFilledPolysList(layer)` 遍历各多边形，取质心）。
2. **NFC 线圈盖绿油**：`gen_nfc_footprint.py` 里自定义焊盘 layers 去掉 `F.Mask`/`B.Mask`（现在线圈是裸铜）。改完要重新生成 + 重新布线。
3. **人工复核封装/引脚**（打板前必须）：
   - GDEM042F86 规格书 24P 引脚顺序、Reference Circuit 的 RESE 电阻值（R14 现为 2.2 Ω）、FPC 出线位置（决定 `FPC_SLOT` 和 J1 位置/朝向）
   - TYPE-C-31-M-14 沉板深度与 0.8 mm 板厚是否匹配
   - XC6220B331MR 引脚（VIN/VSS/CE/NC/VOUT）与 AP2112K 封装一致性
   - FH12-24S 连接器开口方向（现在开口朝板下缘的 FPC 开槽）
   - 面板有效区相对外形的上边距 `ACTIVE_TOP=4.5`（外壳开窗位置）
4. **走线质量**：Freerouting 结果能用但不好看；有条件的话在 KiCad GUI 里手工整理 USB D+/D−（差分）、电池大电流路径、升压回路（L1/Q1/D1/C16 尽量短）。
5. **外壳细节**：后盖卡扣只在长边（薄板可弯入），需打印验证；按键孔目前是直接露出按键，需要时加按键帽；挂绳槽 16×2.6。
6. **固件**（未开始）：ESP-IDF 或 Arduino，见 `firmware/README.md` 引脚表。建议顺序：屏驱动（佳显 GDEM042F86 ESP32 示例）→ 深睡/唤醒 → ST25DV NDEF+FTM 收图 → BLE/SoftAP 网页传图。
7. **手机/网页端**：NFC 碰一碰打开网页 → 编辑图片 → 走 FTM 或 BLE 下发。
8. **v2**：Qi 无线充电（电池仓背面贴接收线圈 + BQ51013B）、六色屏版本（4.0" GDEP040E01，需改外壳与升压参数）。

## 6. 约定

- 一切硬件改动从 `design.py` 开始，再跑生成脚本；不要在 KiCad GUI 里改 `.kicad_sch`（会被覆盖）。`.kicad_pcb` 的布线可以在 GUI 里手改，但重新跑 `gen_pcb.py` 会清掉。
- 所有单位 mm；PCB 坐标系：正面视角、原点左上、Y 向下。FreeCAD 坐标系：X 同 PCB，Y = −PCB y，Z 朝正面。
- 提交前跑 `check_netlist.py` 和 `export.sh` 里的 ERC/DRC。
