# chroma-badge / BADGE-42C

给 **本地 Cursor** 和任何切换过来的模型。先读这一份，再读 `docs/03-handoff.md`。
3D、渲染、截图看不清或像有缺陷时，先读并遵守 `docs/05-visual-check.md`（先查源文件、对准重拍，分清拍错还是板上真问题）。
用户 Wisdom，**始终用中文回复**。

## 这是什么

4.2 寸四色（BWRY）墨水屏 NFC 工牌。ESP32-C3-MINI-1-N4 + ST25DV64KC + 超薄锂电 + USB-C。
架构决策以 `docs/01-architecture-decisions.md` 为准，不要推翻。

## 硬性约定

- 硬件改动一律先改 `hardware/pcb/scripts/design.py`，再跑生成脚本。**不要手改** `.kicad_sch`。
- **不要跑 `gen_pcb.py`**，除非铜皮/焊盘位置/板框变了，并且准备好重新 Freerouting（会清掉全部布线）。只改阻焊不要重布。
- Freerouting 必须按 `docs/03-handoff.md` 第 3 节：交互 shell、**相对路径**、输出重定向到文件。Python `subprocess` 或绝对 `-do` 会得到 0 字节 `.ses`。
- 提交前：`hardware/pcb` 下 `python3 scripts/check_netlist.py` 和 `./scripts/export.sh` 里的 ERC/DRC。
- 不要新建 PR，除非用户明确要求。
- 发现文档写错或和板上事实冲突：**先问用户，讨论后再动手**，不要自行换流程。
- 3D/截图不确定时走 `docs/05-visual-check.md`：先审查源文件和对准的图。**拍错了自己重拍**；**板上真有问题才问 Wisdom**。同类坑追加到该文档并推 GitHub。

## 当前进度（2026-09-14）

| 项 | 状态 |
|---|---|
| 原理图 | 57 元件，ERC 0，网表 == design.py。J1 pin 7 接 GND |
| PCB | 91×84 mm，2 层 0.8 mm，元件全在 B.Cu。**564 段 / 128 过孔，DRC 0**。GND 缝合可复现；NFC 线圈已盖绿油；J1 开口朝槽；B.Silk 已排开 |
| 外壳 | FreeCAD 前框+后盖，约 6.3 mm |
| 固件 | 未写，只有 `firmware/README.md` |

## 下一步（按顺序）

1. **收口 `docs/04-review-checklist.md`**（缺官方 GDEM042F86 PDF）。
2. 固件第一版。

## 本地怎么跑

需要：KiCad 9（`kicad-cli` + Python `pcbnew`）、可选 FreeCAD、Freerouting 2.4 + Java 25。
没有这些也能改脚本和文档；不要在没装 KiCad 时跑生成脚本。

```bash
git clone https://github.com/wisdom-km/chroma-badge.git
cd chroma-badge
```

只补 GND、不动走线：

```bash
cd hardware/pcb
python3 scripts/route_pcb.py --skip-route
```
