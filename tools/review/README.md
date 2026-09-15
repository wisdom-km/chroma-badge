# Cursor / Codex 本机审查执行手册（Windows）

本目录是**隔离审查工具**，不是替换 `hardware/pcb/scripts/export.sh` 的生产发布流程。它不重建PCB、不启动Freerouting、不修改产品固件。`postprocess_probe.py`在第二份副本上验证原`--skip-route`，不会碰工作区PCB。

阅读顺序：根AGENTS → 原交接/ADR → [当前状态](../../docs/06-current-status.md) → [合并计划](../../docs/reviews/2026-09-14/integrated-plan.md)。本轮基准的已知缺陷会使一些检查返回非零；正确记录失败，不要通过删掉警告获得“全绿”。

## 1. 环境发现与前置

本轮可用：KiCad9.0.8安装在 `D:/chroma-badge/agent-tools/kicad-9.0.8`；FreeCAD1.1.3在 `D:/FreeCAD`；PlatformIO6.2.0在 `D:/PlatformIO/penv`；MinGW GCC13.1.0来自CLion工具目录。工具体积大，`agent-tools/`在gitignore中，不入库。其他机器按实际路径修改变量。

```powershell
Set-Location D:/chroma-badge
git status --short
git log -5 --oneline
$kicadBin = 'D:/chroma-badge/agent-tools/kicad-9.0.8/bin'
$freecadPy = 'D:/FreeCAD/bin/python.exe'
$pio = 'D:/PlatformIO/penv/Scripts/pio.exe'
$gitBash = 'G:/BaseWare/Git/bin/bash.exe'
$compiler = 'G:/BaseWare/CodeProgram/CLion 2023.3.4/bin/mingw/bin/g++.exe'
& "$kicadBin/kicad-cli.exe" --version
& "$kicadBin/python.exe" -c "import pcbnew; print(pcbnew.Version())"
& $freecadPy -c "import FreeCAD, Part; print(FreeCAD.Version())"
& $pio --version
& $compiler --version
```

必须确认KiCad为9，不能因PATH上有10就直接采用。原文档记载的用户9.0路径在本轮开始时不存在，本机已有10。winget把安装9当成升级已有包而拒绝；本轮从`winget show --id KiCad.KiCad -e --version 9.0.8`查询官方安装包，校验SHA256后独立安装，没有卸载10。

9.0.8安装包SHA256：`f853f81dd6a90c769c521a35c438c5657fe39aaebe9967c8a74e743540920eb5`。
官方下载：[kicad-9.0.8-x86_64.exe](https://github.com/KiCad/kicad-source-mirror/releases/download/9.0.8/kicad-9.0.8-x86_64.exe)。静默安装需同时指定`/currentuser /S`，最后一个参数才是`/D=安装路径`；仅`/S`本轮返回666660。[KiCad官方打包问题记录](https://gitlab.com/kicad/packaging/kicad-win-builder/-/work_items/135)。安装软件前仍遵循当前任务授权，不把本文当无限安装授权。

受限运行环境可能无法访问用户安装目录/工具缓存。此时先核对权限与路径，不删除PlatformIO缓存、不反复重装。KiCad无需打开GUI即可执行这些测试。

## 2. 新建隔离输入副本

```powershell
$auditRoot = Join-Path (Get-Location) ('agent-tools/review-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
python tools/review/prepare.py --out $auditRoot
if ($LASTEXITCODE -ne 0) { throw 'prepare failed' }
```

`prepare.py`复制Git已跟踪的hardware/firmware文件，记录工作区输入SHA256、源提交与起始git状态。审查副本的`.kicad_pro`使用HEAD版本，原本机修改单独保存为`local-project.kicad_pro`。**如果硬件或固件文件有未提交修改，它们会被复制并在manifest中留痕，不能把该副本谎称纯HEAD。** 本轮只有工程配置有既有修改，已明确隔离。

输出目录必须全新；不复用已归档的 `docs/reviews/.../evidence`。安装器、SDK、模型和厂商PDF不得放到待提交集合。

## 3. KiCad全量检查与诊断导出

```powershell
python tools/review/kicad_checks.py --audit $auditRoot --kicad-bin $kicadBin --export
$auditExit = $LASTEXITCODE
Get-Content "$auditRoot/kicad/summary.json"
Get-Content "$auditRoot/kicad/commands.json"
```

这个审查程序故意继续收集完整诊断数据；任何子命令非零，最终程序返回1。**返回1不是可以忽略的发布成功**，应读 `commands.json` 与对应报告。不会发布制造包。

它逐项执行：

- 全量ERC、error级ERC，均加`--exit-code-violations`。
- 全量DRC加`--schematic-parity`、error级DRC；保留原始JSON。
- 重新导出网表后执行仓库原`check_netlist.py`。
- pcbnew读取PCB，逐个核对设计引脚/显式NC、板尺寸/层数、走线/过孔、网络宽度、3D模型引用和阻焊状态。
- `--export`时诊断导出Gerber、钻孔、BOM、位置、完整STEP，以及全板背面和J1特写。

本轮基准期望：error ERC0/DRC0/未连接0；全量ERC1条warning、DRC含parity148条warning；全量CLI返回5，审查程序返回1。报告类型：57 text_height、1 silk_over_copper、6 silk_overlap、62 footprint_symbol_mismatch、22 net_conflict。后三种不能都视为真实短路，详见复审解释。

模型文件缺失时KiCad STEP仍可能返回0，必须结合`board-audit.json`和`step.log`判断模型覆盖。板尺寸`91×84`取Edge.Cuts端点极值；含0.1mm线条笔画的包围盒是`91.1×84.1`，不要据此改板框。

补充原理图/板图诊断导出以及历史Gerber比较：

```powershell
python tools/review/extra_exports.py --audit $auditRoot --kicad-bin $kicadBin
if ($LASTEXITCODE -ne 0) { throw 'extra diagnostic export failed' }
Get-Content "$auditRoot/kicad/extra-exports.json"
```

比较只移除四类生成日期行，不移除坐标/孔径/属性；gbrjob单独未比较。本轮13份Gerber/钻孔文件中12份一致，背面丝印不同，不能交付旧ZIP当当前完整制造包。`--compare-only`可只重算已存在输出的比较。

## 4. 后处理幂等性（副本测试）

先验证原理图和NFC封装生成（可选扩展，本轮已执行）：

```powershell
& "$kicadBin/python.exe" -m pip install --target agent-tools/review-python-deps sexpdata==1.0.2
if ($LASTEXITCODE -ne 0) { throw 'generator dependency install failed' }
python tools/review/generators_probe.py --audit $auditRoot --kicad-bin $kicadBin --python-deps agent-tools/review-python-deps
if ($LASTEXITCODE -ne 0) { throw 'schematic/NFC generation probe failed' }
```

这会新建第三份副本，运行原生成器，再导出网表、运行原检查器和error ERC。KiCad自带Python的启动路径在本轮未采用外部PYTHONPATH，因此包装器显式添加隔离依赖目录；不改原生成器或Python安装。**不运行gen_pcb.py**。

```powershell
python tools/review/postprocess_probe.py --audit $auditRoot --kicad-bin $kicadBin
if ($LASTEXITCODE -ne 0) { throw 'postprocess changed routing or failed' }
Get-Content "$auditRoot/postprocess/summary.json"
```

它另复制一份PCB，执行两次`--skip-route`，每次保留原始日志和error级DRC，再比较走线/过孔的数量与精确坐标、层、网络、宽度、孔径指纹，以及设计网络分配。本轮三次快照均564/128、相同指纹。原路由日志仍可能写“若干几何islands未stitch”；本轮它们电气连通，不能用这句替代最终未连接检查。

这不验证“从未布线板重新Freerouting”的全链，也不证明任意新设计幂等。`--skip-route`源码仍可能修补走线，只在本轮输入上证实未改变。

## 5. FreeCAD生成和扩展交叠检查

```powershell
& $freecadPy tools/review/mechanical.py --snapshot "$auditRoot/snapshot" --out "$auditRoot/mechanical-saved-step.json"
if ($LASTEXITCODE -ne 0) { throw 'saved STEP geometry check failed' }
& $freecadPy tools/review/mechanical.py --snapshot "$auditRoot/snapshot" --step "$auditRoot/kicad/badge-fresh.step" --out "$auditRoot/mechanical-fresh-step.json"
if ($LASTEXITCODE -ne 0) { throw 'fresh STEP geometry check failed' }
& $freecadPy "$auditRoot/snapshot/hardware/enclosure/badge_enclosure.py"
if ($LASTEXITCODE -ne 0) { throw 'enclosure generation failed' }
& $freecadPy "$auditRoot/snapshot/hardware/enclosure/render_views.py"
if ($LASTEXITCODE -ne 0) { throw 'enclosure render failed' }
```

`mechanical.py`仅在内存中移除外壳脚本末尾`main()`调用后加载几何函数，原源文件不修改。实际原生成器另在副本运行。扩展检查5类物体两两10组，体积交叠容限0.05mm³并检查solid有效性。本轮都为0；但USB/电池座缺模型、FPC和电池等包络不完整，不能批准实装。检查源码后再检查对准的图；遵循`docs/05-visual-check.md`。

## 6. 固件构建、源映射和异常探测

```powershell
$env:PLATFORMIO_BUILD_DIR = Join-Path $auditRoot 'firmware-clean-build'
& $pio run -d firmware *> "$auditRoot/firmware-clean-build.log"
if ($LASTEXITCODE -ne 0) { throw 'firmware build failed' }
python tools/review/static_audit.py --out "$auditRoot/static.json" --build "$auditRoot/firmware-clean-build/badge-42c"
if ($LASTEXITCODE -ne 0) { throw 'source/pin audit failed' }
python tools/review/host_probes.py --compiler $compiler --out "$auditRoot/host"
if ($LASTEXITCODE -ne 0) { throw 'EPD characterization changed or compiler failed' }
python tools/review/fault_probes.py --bash $gitBash --out "$auditRoot/faults"
if ($LASTEXITCODE -ne 0) { throw 'failure-path characterization changed' }
```

这些probe里，**固件** host_probes 在 F1 之后：仅 `normal` 报成功；BUSY 恒高、卡低、关电超时、刷新超时必须失败。测试通过意味着假成功已堵住，不是实屏通过。H1 之后 `fault_probes.py` 已改为 **F04/F19 回归**：旧 DRC 报告注入必须失败；ERC/DRC 失败不得走到 Gerber。所有模拟输出中的毫秒都是替身时钟，不是屏幕测量。

静态审查比较模组符号脚名、design和pins.h，避免只照抄GPIO注释；检查9份原脚本AST、BOM/位置、旧ZIP目录一致性和三份bin哈希。它只记录ZIP/BOM问题，不把发现自动删除或重写。

## 7. export.sh（H1 之后）

H1 已改 `hardware/pcb/scripts/export.sh`：error 级 ERC/DRC 加 `--exit-code-violations`，去掉 DRC `|| true`；解释器为 `python3` / `python` / `py -3`；zip 用 `zip_dir.py`，不依赖 `zip` 命令。默认写入 `output/exports/<stamp>-candidate/`，**禁止**覆盖 `output/gerbers` 与 `output/badge_gerbers.zip`。`--production` 拒绝。全量 warning 见 `docs/hardware/drc-warning-register.md`，全部未豁免。

`fault_probes.py` 中的假 `kicad-cli` 仅用于隔离流程测试。不要仅放一个假的 python3 返回 0 来让真实脚本过关。候选目录不是生产包。

## 8. 证据与提交

本轮原始证据在`docs/reviews/2026-09-14/evidence/`，公开文件都列SHA256。今后新审查用新日期/轮次，不覆盖历史证据；不要提交整个`agent-tools`、安装包、SDK、缓存、厂商PDF或无关用户文件。

每次提交前检查：本轮变更是否只在预期范围、输入哈希是否还对应、报告是否保留失败、全量警告是否明确、网表/DRC是否当次运行、实际测试与未测是否分开。用户没有授权修硬件时不改网络，没有授权新PR时不创建PR；推送只按当前会话授权执行，禁止force push。
