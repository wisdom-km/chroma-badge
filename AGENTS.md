# chroma-badge / BADGE-42C

**2026-09-14 本机复审补充入口：** [docs/06-current-status.md](docs/06-current-status.md)、[合并整改计划](docs/reviews/2026-09-14/integrated-plan.md)、[可执行测试手册](tools/review/README.md)。下文是原进度快照；本轮复审的完整警告、未修缺陷、制造包同步问题和实物未测范围以补充报告逐项查证。架构决定和以下硬性约定保持。

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
- 提交前：`hardware/pcb` 下 `python scripts/check_netlist.py` 和 `./scripts/export.sh --check-only`（error ERC/DRC）。全量 warning 见 `docs/hardware/drc-warning-register.md`，不能因为 error 0 声称全量通过。候选包 `export.sh` 默认写入新目录，**不是**生产发布。
- 不要新建 PR，除非用户明确要求。
- 发现文档写错或和板上事实冲突：**先问用户，讨论后再动手**，不要自行换流程。
- 3D/截图不确定时走 `docs/05-visual-check.md`：先审查源文件和对准的图。**拍错了自己重拍**；**板上真有问题才问 Wisdom**。同类坑追加到该文档并推 GitHub。

## 当前进度（2026-09-15 H2）

| 项 | 状态 |
|---|---|
| 原理图 | **58** 元件，**全量 ERC 0**（KiCad 10.0.6），网表 == design.py。J1 pin 7 = **NC Keep Open** |
| PCB | 91×84 mm，2 层 0.8 mm，元件全在 B.Cu。**680 段 / 115 过孔，全量 DRC 0（含丝印与 schematic_parity）**。Power≥0.3 mm（GND 靠铺铜）、NFC 0.5 mm。旧 564/128 板备份在 `agent-tools/badge-pre-h2.kicad_pcb` |
| 检查门禁 | H1 仍有效。全量 warning **0**（KiCad 10.0.6）。error 级 0 仍不等于生产包。 |
| 外壳 | FreeCAD 前框+后盖，约 6.3 mm。ACTIVE_TOP=6.7 |
| 固件 | **v0.2 源码已改 F1**（深睡仅 GPIO1；串口 `W` 刷白；BUSY 假成功已堵）。v0.1 bin 未覆盖。无实机 |

## 下一步（按顺序）

1. 有板后测 USB/充电/BUSY/NFC/电流。F1 源码已改，不是实机通过。
2. 固件 F2（NDEF/FTM）须 Wisdom 选定路线后再做。
3. 不要把候选 Gerber 当下单包。全量 ERC/DRC 0 仍不是生产发布。

## 本地怎么跑

需要：KiCad **10.0.6**（全量 ERC/DRC；`C:\Users\19612\AppData\Local\Programs\KiCad\10.0\bin`）、可选 KiCad 9 的 `pcbnew` 脚本、可选 FreeCAD、Freerouting 2.4 + Java 25。
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
