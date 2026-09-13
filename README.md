# BADGE-42C：4.2 寸四色墨水屏 NFC 工牌

一块 **6.3 mm 厚**的电子工牌：4.2" 黑白红黄四色墨水屏 + ESP32-C3（Wi-Fi/BLE/原生 USB）+ ST25DV64KC NFC 动态标签
+ ≤2 mm 超薄锂电 + USB-C 充电。手机碰一碰唤醒/传图，或通过网页下发图片（固件与 App 为后续工作）。

| 背面 PCB 渲染 | 外壳（FreeCAD） |
|---|---|
| ![pcb](hardware/pcb/output/render_back.png) | 见 `hardware/enclosure/output/badge_assembly.step` |

## 仓库

- `docs/01-architecture-decisions.md`：为什么选四色而不是六色、为什么 v1 带电池而不是纯 NFC 无源、厚度堆叠、续航估算
- `docs/02-bom-and-cost.md`：BOM 与单件成本（≈ ¥150–225）
- `docs/03-handoff.md`：**当前进度、复现步骤、已知坑、下一步清单**（接手先读这个；文首有新会话粘贴提示）
- `docs/04-review-checklist.md`：打样前封装/引脚复核（进行中）
- `hardware/pcb/`：KiCad 9 工程，全部由 `scripts/design.py` 生成（原理图、PCB、NFC 天线封装、Gerber、BOM、STEP）
- `hardware/enclosure/`：FreeCAD 参数化外壳脚本与输出（前框、后盖、装配、干涉检查）
- `firmware/README.md`：引脚表与时序约定

## 快速开始

需要 KiCad 9（含 `kicad-cli` 与 Python `pcbnew`）、FreeCAD 1.x（`freecadcmd`）、Java 25 + Freerouting 2.4（仅自动布线时）。

```bash
cd hardware/pcb
python3 scripts/gen_schematic.py && python3 scripts/gen_pcb.py     # 生成原理图与未布线 PCB
./scripts/export.sh                                                 # ERC/DRC + 全部生产文件到 output/
cd ../enclosure && freecadcmd badge_enclosure.py                    # 外壳 + 装配干涉检查
```

自动布线的完整流程和注意事项见 `docs/03-handoff.md` 第 3 节。

## 状态

v0.2（2026-09-13）：原理图 ERC 通过；PCB **564 段 / 128 过孔，DRC error 0**（GND 孤岛已在当前板上缝合；脚本从 78 过孔原板复现仍差 1 个孤岛，见交接文档）。
下一步：把缝合做成可复现 → NFC 线圈盖绿油并重布线 → 完成 `docs/04-review-checklist.md` → 固件。

## 新会话怎么接

把 `docs/03-handoff.md` 文首的代码块贴给新对话即可。架构以 `docs/01-architecture-decisions.md` 为准。

## 第三方内容

- 乐鑫 KiCad 库（ESP32-C3-MINI-1 符号/封装/STEP）：CC-BY-SA 4.0
- HRO TYPE-C-31-M-14 封装：来自 jenschr/USB-C-Connectors，公有领域
- 其余符号/封装来自 KiCad 官方库
