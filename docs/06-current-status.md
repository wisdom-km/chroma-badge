# BADGE-42C 当前状态与接手入口

更新：2026-09-15 **H2 规格已按授权改到板上**（动线已完成）。H1 门禁仍有效。2026-09-14 复审档案仍是旧 57 件/564 段板的证据，不要和当前工程混读。

**当前阶段：硬件全量已过（KiCad 10.0.6）；固件 F1 源码已改（v0.2）。** error 级与全量 ERC/DRC 均为 0。没有生产 zip。不要把候选 Gerber 当下单包。F1 无实机。

## 先看哪些文件

1. [AGENTS.md](../AGENTS.md) → [原交接](03-handoff.md) → [架构决策](01-architecture-decisions.md)：既有约定和决定仍有效。
2. [本机独立复审](reviews/2026-09-14/local-review.md)：本轮工具执行、结果、证据边界及新发现。
3. [外部审查原文](reviews/2026-09-14/external-review.md)：用户提供，逐字归档；其中建议不是修改指令。
4. [合并整改计划](reviews/2026-09-14/integrated-plan.md)：F01–F20及N01/N02的入口、顺序、关闭标准、实物操作单。
5. [审查工具执行手册](../tools/review/README.md)：Cursor/Codex可直接复跑的命令、预期返回、失败处理。
6. [证据索引](reviews/2026-09-14/evidence/README.md)：原始JSON、日志、预览及SHA256清单。
7. [r2 复跑](reviews/2026-09-14-r2/rerun.md)：新隔离目录复跑；结论与首轮一致，缺陷仍未修。
8. [缺陷修复项目（先硬件后固件）](07-defect-fix-project.md)：未修项、注意点、H1/F1 提示词。
9. [H2/H3 拍板提问](08-h2-h3-questions.md)、[全量 warning 登记（未豁免）](hardware/drc-warning-register.md)。

## 已完成与验证到什么程度

| 模块 | 状态 | 本轮结果 | 未覆盖 |
|---|---|---|---|
| 架构 | 已决策 | 四色屏/ESP32-C3/ST25DV/电池+USB/0.8mm保持 | 不把审查当改架构授权 |
| 原理图 | 本机检查通过（全量） | **58** 元件；KiCad 10.0.6 全量 ERC 0；网表与 design.py 一致；J1.7 **NC**；U2 用 `Badge:ST25DV64KC-SO8N` | 未做电气模拟 |
| PCB | 本机检查通过（全量） | 91×84×0.8mm，两层，全在B.Cu，**680段/115过孔**；全量 DRC 0、未连接 0、parity 0；Power 走线≥0.3mm（GND靠铺铜）；NFC 0.5mm；USB_DP/DN 分网 | 旧 564/128 仅备份；未跑 gen_pcb 清线 |
| GND后处理 | H2 重布后幂等 | `--skip-route` 保持 680/115；J1.7 不再接地 | 不等于任意新布局均可靠 |
| 制造输出 | 档案仍旧；候选目录 | 旧 ZIP 与 `output/gerbers` **未改**；`export.sh --check-only` 已过 | 候选 ≠ 生产包 |
| 三维输出 | 包络已就位 | J3/J2 仓库包络 STEP 存在；`--fail-missing` 0；包络 ≠ 官方 CAD | 装配干涉不能只靠包络 |
| 外壳 | 本机几何验证 | 未因 H2 重做外壳 | FPC/胶/实电池仍未测 |
| 固件构建 | v0.2 源码 | F01/F02/F09 已改；`host_probes` 新期望（仅 normal 成功）；勿覆盖 v0.1 bin | 无烧录、USB 或实屏；pio 构建见本机日志 |
| 自检/显示/深睡 | 源码已修，待实机 | 深睡仅 GPIO1；刷白用串口 W；BUSY 恒高/关电超时报失败 | 实屏 BUSY、深睡电流、NFC 真场未测 |
| NFC | 最小探测已实现 | 仅I²C ACK探测 | 身份/事件配置、NDEF、FTM、手机传图均未完成 |
| 续航/充电/RF | 待验证 | ADR 已改为待测；电芯/充电器已锁料号 | 无电流/电荷/温升/射频/目标机型实测 |

状态词严格区分：**已决策**是用户选择；**已实现**是有代码/设计；**已构建**是编译成功；**本机验证**是明确的软件/几何检查；**实机通过**需要真实设备及条件。本轮没有任何新增“实机通过”项，不使用虚构完成百分比。

## 现在最难、最先处理的事项

1. **有板后：** USB 枚举、充电、BUSY 波形、NFC 装机、电流。F1 源码不能替代实装。
2. **固件 F2：** NDEF/FTM 收图（须 Wisdom 选定一条路线）。
3. **不要**把候选 Gerber 当生产包。

建议执行顺序（审查原文）：固件与检查门禁 → 硬件待决项/规格冻结 → …  
**Wisdom 已指定先硬件后固件**，排期见 [07-defect-fix-project.md](07-defect-fix-project.md)。具体验收见合并计划。

## 给新会话的可直接粘贴任务

```text
继续 BADGE-42C。先读 AGENTS.md、docs/06-current-status.md、docs/03-handoff.md。
始终中文。H2 铜皮已落地（680/115，J1.7 NC），不要再问 F06/N01 拍板。
不要因为 DRC error 0 声称可以下生产包。不要把候选 Gerber 当生产包。
不要覆盖用户已有 .kicad_pro 或 tools/freerouting。不要改产品固件除非本任务是 F1。
下一步默认：有板实测；F2 须 Wisdom 选定 NDEF/FTM 路线。F1 源码已改。
提交前 check_netlist.py 和 export.sh --check-only。未经明确要求不要建 PR。
```

历史交接、ADR和BOM文档中的冲突详见复审报告，保留以便讨论后统一修订。本文是审查状态入口，不修改已接受的架构决定。
