# 本机工具（Windows）

大软件装系统（KiCad / Git / 可选 FreeCAD），可移植的放这里。不要把 KiCad 或 FreeCAD 整个拷进仓库。

## 已约定路径

| 工具 | 路径 |
|---|---|
| KiCad 9 | `C:\Users\19612\AppData\Local\Programs\KiCad\9.0\` （当前用户安装；不是 `C:\Program Files\KiCad\9.0\`） |
| `kicad-cli` | `C:\Users\19612\AppData\Local\Programs\KiCad\9.0\bin\kicad-cli.exe` |
| KiCad Python | `C:\Users\19612\AppData\Local\Programs\KiCad\9.0\bin\python.exe` |
| 符号/封装库 | `...\9.0\share\kicad\symbols` 与 `...\9.0\share\kicad\footprints` |
| Freerouting 2.4.1 | `tools/freerouting/freerouting.jar` |
| 便携 JRE 25 | `tools/jre/bin/java.exe` |

`design.py` 会自动探测 `Program Files\KiCad` 和 `%LOCALAPPDATA%\Programs\KiCad`，并优先 9.x。若你改了安装位置，把实际路径写在上表。

## 装 KiCad 9（不要 8，也不要用 winget 默认的 10）

```powershell
winget install --id KiCad.KiCad -e --version 9.0.8 --accept-package-agreements --accept-source-agreements
```

装完**新开终端**，把 KiCad 加进 PATH（当前会话）：

本机实际路径（winget 当前用户安装）：

```powershell
$kicadBin = "$env:LOCALAPPDATA\Programs\KiCad\9.0\bin"
$env:Path = "$kicadBin;" + $env:Path
git --version
kicad-cli --version
where.exe kicad-cli
& "$kicadBin\python.exe" -c "import pcbnew; print('pcbnew ok')"
```

Git Bash：

```bash
export PATH="$LOCALAPPDATA/Programs/KiCad/9.0/bin:$PATH"
kicad-cli --version
```

`sexpdata` 必须装进 **KiCad 自带的 Python**，不是系统 Python：

```powershell
$py = "$env:LOCALAPPDATA\Programs\KiCad\9.0\bin\python.exe"
& $py -m pip install sexpdata
& $py -c "import sexpdata; print('sexpdata ok')"
```

## Freerouting 2.4.1 + 便携 JRE

jar 和 JRE 都 gitignore 了（体积大）。在仓库根目录执行：

```powershell
New-Item -ItemType Directory -Force -Path tools\freerouting, tools\_download | Out-Null

# Freerouting 2.4.1（不要 1.x）
curl.exe -L --fail -o tools\freerouting\freerouting.jar `
  https://github.com/freerouting/freerouting/releases/download/v2.4.1/freerouting-2.4.1.jar

# Eclipse Temurin JRE 25 x64 zip
curl.exe -L --fail -o tools\_download\OpenJDK25U-jre_x64_windows.zip `
  https://github.com/adoptium/temurin25-binaries/releases/download/jdk-25.0.4.1%2B1/OpenJDK25U-jre_x64_windows_hotspot_25.0.4.1_1.zip
```

把 zip 解压后，把里面那层 `jdk-*-jre\` 的内容挪到 `tools\jre\`，保证存在 `tools\jre\bin\java.exe`。

验证（相对路径；Freerouting 的 `-do` 必须在 `output` 目录下用相对文件名，绝对路径会得到 0 字节 `.ses`）：

```powershell
tools\jre\bin\java.exe -version
```

`route_pcb.py` 会优先用仓库里的 jar / JRE，找不到再回退 `/opt/freerouting/...` 或 PATH 里的 `java`。

**不要用 Python `subprocess` 跑 Freerouting。** 必须 `cd output` 再用相对 `-de`/`-do`。详见 `docs/03-handoff.md` 第 3 节。

## 冒烟测试

在仓库根目录：

```powershell
$kicadBin = "$env:LOCALAPPDATA\Programs\KiCad\9.0\bin"
$env:Path = "$kicadBin;" + $env:Path
cd hardware\pcb
& "$kicadBin\python.exe" scripts\check_netlist.py
# 若还没有 output\badge.net：
# kicad-cli sch export netlist -o output\badge.net badge.kicad_sch

kicad-cli pcb drc --severity-error --format json -o output\drc_tmp.json badge.kicad_pcb
```

期望：`netlist matches design.py`；`drc_tmp.json` 里 `violations` / `unconnected_items` 为空。

不要跑 `gen_pcb.py`（会清布线）。不要跑 Freerouting，除非要做 NFC 盖绿油。

## `export.sh`

Windows 用 Git Bash（不要改成只支持 cmd）：

```bash
cd hardware/pcb
export PATH="$LOCALAPPDATA/Programs/KiCad/9.0/bin:$PATH"
bash ./scripts/export.sh
```

`export.sh` 里的 `python3` 若找不到，用 KiCad Python 跑网表检查（KiCad 的 `python.exe` 一般没有 `python3` 这个名字）：

```bash
export PATH="$LOCALAPPDATA/Programs/KiCad/9.0/bin:$PATH"
"$LOCALAPPDATA/Programs/KiCad/9.0/bin/python.exe" scripts/check_netlist.py
```
