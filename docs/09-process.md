# 流程（许可证、CI、贴胶、生产包）

日期：2026-09-15。把「文档和板上事实打架、没有 CI、没许可证、没贴胶规格」从口头债变成可执行约定。架构仍以 [01-architecture-decisions.md](01-architecture-decisions.md) 为准。

## 1. 许可证

见根目录 [LICENSE.md](../LICENSE.md)。硬件 **CERN-OHL-P-2.0**，固件/脚本/文档 **MIT**。第三方库保持原许可。要改成 CERN-OHL-W/S 必须 Wisdom 改 `LICENSE.md`。

## 2. 文档哪份是当前板

| 文件 | 角色 |
|---|---|
| [AGENTS.md](../AGENTS.md) | 硬性约定 + **当前** 进度一行表 |
| [06-current-status.md](06-current-status.md) | 审查状态入口 |
| [03-handoff.md](03-handoff.md) | 复现步骤与**当前**板指纹（680/115） |
| [08-h2-h3-questions.md](08-h2-h3-questions.md) | **已关闭的拍板记录**，不是待办问卷 |
| [reviews/2026-09-14/](reviews/2026-09-14/) | 旧 57 件 / 564 段板的证据档案，不要当现板 |

正文里再写「57 元件 / 564 段 / 脚 7 GND / v0.1 BOOT 刷白」即为过期，应改或标成「历史」。

## 3. CI（GitHub Actions）

工作流：[`.github/workflows/ci.yml`](../.github/workflows/ci.yml)。依据 [PlatformIO GitHub Actions](https://docs.platformio.org/en/stable/integration/ci/github-actions.html)，并按 ESPHome 做法把 `platformio.ini` 哈希放进 cache key。

CI **会做**：Python 编译、`check_netlist.py`、`host_probes`、钉死版本的 `pio run`、确认 v0.1 三份 bin 仍在且应用 296 512 B。

CI **不会做**：KiCad 全量 ERC/DRC、Freerouting、生产 Gerber、实机。那些仍须本机 KiCad **10.0.6**。CI 绿 ≠ 可以下单。

固件钉死：`espressif32@7.1.3` + CI 里 `platformio==6.2.0`（本机 v0.2 构建）。espressif32 7.x 不要搭配 Core 6.1.18。

## 4. 生产包 vs 候选包

- `export.sh` 默认写入 `output/exports/<stamp>-candidate/`。**候选 ≠ 生产。**
- 覆盖 `output/gerbers` 或 `output/badge_gerbers.zip` 必须有 Wisdom 书面「生产包」授权，并带 commit、KiCad 版本、BOM、全量 ERC/DRC 报告 SHA。
- 旧 zip 若 B.Silk 与现板不一致，禁止当下单文件。

## 5. 屏贴胶（首件）

屏 FR4 背面贴到 PCB 正面（元件在 B.Cu）。佳显未公布指定胶带；按 3M 图形/铭牌粘接惯例锁首件料：

| | 规格 |
|---|---|
| 主选 | **3M 467MP**（200MP 丙烯酸转移胶，标称 **0.06 mm / 2.3 mil**） |
| 为什么 | 金属与高表面能塑料（FR4、ABS）常用；薄，不顶高 6.3 mm 叠层。数据页：[3M 467MP](https://multimedia.3m.com/mws/media/1854916O/3m-adhesive-transfer-tape-467mp.pdf) |
| 贴法 | 只贴 **非 AA 边框**：左右各 3.1 mm、顶/底各 6.7 mm 里靠外侧的一圈，**不要**贴到 84.8×63.6 有效区、FPC 根、线圈对应区域加厚块 |
| PETG 后盖/前框若粘不牢 | 改 **3M 300LSE**（低表面能，0.06–0.13 mm）。前框是 3D 打印 PETG/ABS 时优先考虑 300LSE 粘框、467MP 贴屏到 PCB |
| 禁止 | 泡棉胶把屏顶离 FPC 翻盖工作行程；丙酮类清洗液碰屏 |

未指定宽度的裁切：用 6–8 mm 宽转移胶条沿边框，总胶厚按 **0.06 mm** 计入装配，不改 `ACTIVE_TOP`。

## 6. C11 / USB 走线（流程口径，不是改板）

- **C11**：首件 **DNP**，SMT 按装配 BOM 不贴。封装保持 0402。测谐振后再填容值并记调谐表。
- **USB**：不把网络总长差当差分失配去重布。未批准不要 Freerouting USB。
