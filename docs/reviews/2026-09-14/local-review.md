# BADGE-42C 本机独立复审报告

审查日期：2026-09-14。审查对象：[基准提交 ee978f0](https://github.com/wisdom-km/chroma-badge/commit/ee978f08cbdb7b61bbe2c78fea0e9c7cd2c34a7b)。本机起始 HEAD 与远端 main 均为该提交。审查输入包括用户提供的报告、本机源码、KiCad 工程、已有制造输出、FreeCAD 几何、固件工具链及官方规格资料。

## 1. 结论和证据边界

项目已经形成可编辑的硬件设计、已布线 PCB、可生成外壳和可构建固件。当前里程碑应定义为 **工程样机闭环验证**，不能定义为“已可交付生产”或“仅剩手机传图”。

外部审查的核心方向成立。本机复审进一步独立核对了确切屏幕 PDF，完成固件干净构建和异常路径探测、FreeCAD 实体/交叠检查、制造包内部一致性和固件引脚映射检查。新的重要发现是屏升压参考电路与当前物料存在多处尚未说明的差异；不要把 RESE 电阻值相同视为升压方案全部核准。

**本轮未接入实物板、电池、屏幕、逻辑分析仪、示波器、VNA或目标手机。** USB枚举/刷机、真实刷屏、RF通讯、续航、充电热行为、实际装配和耐久均未测试。主机 I/O 替身不会模拟显示器模拟电路，也不会证明任何真实波形。

本轮没有改 `design.py`、原理图、PCB、现有生产输出或产品固件。根 AGENTS 要求规格/文档冲突先讨论，本报告将冲突作为待决项，不覆盖历史 ADR，也不批准硬件偏离。

## 2. 审查基准和环境

会话开始前存在 `hardware/pcb/badge.kicad_pro` 本地修改，以及未跟踪 `tools/freerouting/`。工程差异主要为新版本 KiCad 增加的配置字段；它们不属于本轮成果，保留原样、不推送。审查副本首先使用 HEAD 中的 `.kicad_pro`，防止混淆已提交设计与本地编辑器状态。输入文件 SHA256、大小和起始状态存于 [inputs.json](evidence/inputs.json)。

| 工具 | 本轮环境 / 用途 |
|---|---|
| FreeCAD | 1.1.3，`D:/FreeCAD/bin/python.exe` 可直接导入 FreeCAD/Part；真实 OCC 布尔运算 |
| PlatformIO Core | 6.2.0；已有安装 `D:/PlatformIO/penv/Scripts/pio.exe` |
| PlatformIO 平台 | espressif32 7.1.3 |
| Arduino framework | `4.20017.260907+sha.dcc1105b`；实际 SDK 头文件为 ESP-IDF 4.4.7 |
| 目标编译器 | riscv32-esp 8.4.0+2021r2-patch5 |
| 主机测试编译器 | MinGW GCC 13.1.0；直接编译未修改的 `firmware/src/epd.cpp` |
| PDF | 本地 `GDEM042F86.pdf`，40页；逐页渲染核对6/7/29/31页；原PDF及页面图不入库 |
| GitHub | 起始远端 main 与本地 HEAD 一致；提交只包含本轮文档、证据、审查脚本 |

KiCad 9.0.8 已校验官方安装包后独立安装到 `agent-tools/kicad-9.0.8`（不入Git）。全量报告见 [证据索引](evidence/README.md)。所有诊断导出保存在隔离目录；即使 CLI 导出成功，也不能将其视为生产许可。

### 2.1 当次 KiCad 结果和制造输出同步性

| 检查 | 当次结果 | 判断 |
|---|---|---|
| ERC error级 | 0错误，CLI返回0 | 缓存原理图可检查 |
| ERC全量 | 1条 `lib_symbol_issues`，CLI返回5 | U1来源Espressif符号库解析/查找未闭合，不能写全量零警告 |
| DRC error级 | 0错误，0未连接，CLI返回0 | 当前规则下通过 |
| DRC全量+parity | 64条板级warning +84条parity warning，CLI返回5 | 全量检查不通过，需分类处理 |
| 本机未提交工程配置交叉检查 | error DRC仍0 | 起始配置变化没有改变本轮error结论；原本机文件保留 |
| 新网表 | 原检查器通过，63个原理图网络，其中41个功能网络 | 其余为未连接脚网络 |
| 生成器复现 | 隔离副本重跑`gen_nfc_footprint.py`、`gen_schematic.py`成功；再导出网表/检查匹配，生成原理图ERC error0 | sexpdata1.0.2隔离依赖；NFC封装忽略换行后与原文件相同；未运行`gen_pcb.py` |
| PCB直接读取 | 57封装，全B.Cu，91×84×0.8mm，两层，564段/128过孔；设计引脚/NC分配无差异 | 包围盒含Edge.Cuts笔画会得到91.1×84.1，不能误报为板变大 |
| 后处理两次 | 每次564/128，布线指纹 `2d96f2751cfe29874e19817df79bebdc1da593ffc553671f2aa7306423b1d7c4` 不变，DRC error0 | 本输入上幂等，没启动Freerouting |
| 模型覆盖 | J3项目USB模型缺失；J2引用模型在已安装官方9.0.8库无法解析 | STEP导出仍返回0，缺模型不是板上没封装 |
| 诊断输出 | Gerber、钻孔、BOM、位置、整板/裸板STEP、原理图PDF/SVG、PCB SVG及两张渲染均成功 | 原export.sh入口未跑通，但上述KiCad命令分别已执行 |
| 新旧制造数据 | 13份Gerber/钻孔类文件去除生成日期后12份一致 | 背面丝印不同，有真实坐标变化；旧ZIP包含旧丝印，见N02 |

148条warning分布：`text_height`57、`silk_over_copper`1、`silk_overlap`6、`footprint_symbol_mismatch`62、`net_conflict`22。57条封装名告警主要是PCB保存裸封装名而原理图有库前缀，另外5条是ANT1/TP1–TP4的BOM排除属性差异。22条net_conflict为原理图命名的unconnected网络与PCB无网表示不同；直接引脚核对没有发现功能网错接。它们仍需生成流程和明确规则处理，不能把warning全部当真短路或全部默认忽略。

真实丝印项包括D3参考文字被阻焊截断、Q2轮廓与D3文字重叠、若干小于0.8mm的文字；本轮只是定位，没有改板。原DRC只取error所以这些不在原“DRC0”语义内。

USB_DP网络平面线段总长30.19643mm/4过孔，USB_DN35.077666mm/2过孔；EPD_RESE31.350637mm/2过孔。它们是含分支的网络总量，不能直接当端到端长度差。Power/NFC馈线宽度实际包含0.15/0.2mm，和未落地的声明宽度0.3/0.5mm不同。

### 2.2 新发现N02：旧制造包背面丝印未同步

本机用同版KiCad9.0.8、当前PCB重新导出，比较只移除生成日期，不移除坐标、孔径或其他属性。铜层/阻焊/焊膏/板框/正面丝印/孔数据一致，`badge-B_Silkscreen.gbr`不一致。坐标命令多重集合也不同，因此不是文件块重排：例如一组线端Y从`-78263855`变到`-77963855`（Gerber 4.6单位mm，对应0.3mm）。

当前ZIP与旧目录内部一致，所以也携带该旧丝印。此项从外部报告的“版本一致性风险”升级为**已证实的交付文件不一致**。见 [manufacturing-diff.json](evidence/manufacturing-diff.json) 与 `extra-exports.json`。本轮未替换原制造包；修复发布门禁、确认警告处理后应重新导出并一次性发布同步包，禁止只更新渲染截图。

## 3. 本轮已执行的非 KiCad 测试

| 检查 | 实际结果 | 证明范围 |
|---|---|---|
| 9个原有Python脚本 AST | 全部通过 | 语法可解析，不代表生成与硬件功能正确 |
| `pins.h` 对照 design + 库中模组脚名 | 13个固件GPIO定义一致，0差异 | 自动从符号脚名取GPIO，避免只抄注释；GPIO9用途是否合法另行核查 |
| 干净目标构建 | 通过，RAM 15,312 / 327,680 B，Flash 283,588 / 1,310,720 B | 能构建，不代表板上能运行 |
| 二进制可重复性 | 应用296,512 B、bootloader13,248 B、partitions3,072 B；三份SHA256均与仓库既有bin相同 | 本机现有工具链可字节复现这三份固件；不保证未锁依赖的新机器未来仍相同 |
| EPD替身场景 | 5种BUSY场景 × 4色，共20次调用 | 真实生产代码的字节输出、返回状态、关电请求 |
| 正常四色路径 | 每色发送30,000字节；00/55/AA/FF编码正确；请求关断屏电源 | 不验证真实颜色、方向或刷新波形 |
| BUSY恒高 | 四色均报告成功 | 驱动无法区分空闲与刷新从未启动 |
| 关电BUSY超时 | 四色均报告成功 | 明确丢失关电超时状态 |
| BUSY恒低 / 刷新超时 | 均返回失败；请求关电 | 有部分失败处理，但阶段信息不完整 |
| DRC命令失败注入 | 返回5后仍走到Gerber命令；测试哨兵退出99 | `export.sh` 中 `|| true` 确实破坏门禁 |
| ERC命令失败注入 | 返回5后脚本立即停止，没有走到Gerber | 不应笼统声称任何ERC进程失败都会被吞掉 |
| 旧DRC报告注入 | 命令返回5，`drc_json`仍返回带 `OLD_REPORT` 标记的空旧报告 | 已复现旧证据误当本次通过，建议优先修复 |
| 当前ZIP与gerbers目录 | 14个文件成员，无多余/缺少/内容不同 | 当前包内部一致；不证明它们与当前板同源，也不排除以后原地更新残留 |
| BOM/位置表 | BOM34行，21行无LCSC；C11(DNP)仍在位置表 | 工程清单不能直接作为无歧义的SMT交付清单 |
| FreeCAD原生成脚本 | 隔离副本真实运行成功，前框/后盖/装配STEP、STL、FCStd成功写出 | 没有覆盖仓库生产文件 |
| FreeCAD原渲染脚本 | 5张预览重新生成成功 | 外壳预览可重现；不是实物装配照片 |
| OCC扩展交叠检查 | 5类实体两两10组，交叠体积均0；所有实体有效 | 只覆盖已建模物体；原始脚本9组检查也均为0 |

上述结果分别见 `static.json`、`firmware-clean-build.log`、`epd-probes.json`、`faults.json`、`mechanical-saved-step.json`、`enclosure-generation.log` 和 `enclosure-render.log`。详情与复跑命令见 [证据索引](evidence/README.md) 和 [工具手册](../../../tools/review/README.md)。

## 4. 固件审查

### 4.1 GPIO9深睡唤醒：与真实构建SDK核对

`main.cpp::go_sleep` 将GPIO1与GPIO9同时加入mask，忽略 `esp_deep_sleep_enable_gpio_wakeup` 返回值，随后无条件打印可由NFC或BOOT唤醒并进入深睡。本轮使用的SDK `soc_caps.h` 明确只允许 BIT0–BIT5；实际 `esp_idf_version.h` 为4.4.7，不能将外部报告引用的4.4.8当作本机构建版本。

核对 [ESP-IDF v4.4.7实现](https://github.com/espressif/esp-idf/blob/v4.4.7/components/esp_hw_support/sleep_modes.c) 与 [睡眠API说明](https://docs.espressif.com/projects/esp-idf/en/v4.4.8/esp32c3/api-reference/system/sleep_modes.html)：非法脚会导致配置失败。修复应检查返回码，并保留可解释的恢复入口；不能假定GPIO1虽合法就一定已经成功启用。

GPIO9同时是启动strap。[官方启动模式说明](https://docs.espressif.com/projects/esptool/en/latest/esp32c3/advanced-topics/boot-mode-selection.html) 支持“按住BOOT复位进入ROM下载”这一判断。现有文档将相同操作描述成应用自检入口，存在冲突。建议正常启动后明确输入窗口/串口命令；变更操作文档之前先按AGENTS讨论确认。

### 4.2 显示流程与官方程序

独立读取GDEM042F86第31页后，`init_otp()` 的10组初始化命令与图中参数一致；400×300、2bit编码及30,000字节帧大小一致。这个正面结果应保留，不能因错误处理缺陷否定全部驱动实现。

主要缺陷在流程状态：`power_on()` 丢弃首次等待结果；`power_off()` 丢弃关电等待结果；`refresh_solid()` 的最终bool仅能反映刷新阶段的一次空闲等待。BUSY卡高和关电超时均已本机复现假成功。完整证据不是真实毫秒测量；`fake_elapsed_ms`只是替身虚拟时钟。

还需实物验证：最小命令延迟、BUSY实际变化、电源开关、断电后SPI复用脚电平、GPIO hold跨睡眠行为、低电拒绝刷新。不要在没有屏时序依据时简单要求每条命令都必须出现相同BUSY边沿。结构化错误应至少区分上电、数据、刷新、关电。

### 4.3 NFC、协议和手机路线

`nfc.cpp`目前只有Wire初始化、100kHz设置和用户区地址ACK检查；NDEF、FTM、UID/配置管理、会话恢复均不存在。ACK成功只能证明某地址应答。

30,000字节整图大于ST25DV64KC的8KB EEPROM，256B邮箱适用于分片交换；忽略头部至少118包，实际协议更多。定义长度/版本/编码/偏移/序号/CRC、重复包幂等、超时和授权窗口，完整校验后才刷屏。型号/容量依据 [ST规格书](https://www.st.com/resource/en/datasheet/st25dv64kc.pdf)。

[Chrome Web NFC文档](https://developer.chrome.com/docs/capabilities/nfc) 将能力限制在NDEF。由此推断，“碰NDEF打开网页”不能自动形成“网页向ST25DV厂商邮箱传图”闭环。首版必须选定真实目标手机和一条可实现路线，先完成一张非纯色图再扩展模板。

## 5. 电气、器件和电源审查

### 5.1 屏脚7：本轮已取得独立规格证据

本地40页PDF第7页将1/4/6/7标NC Keep Open，19为VPP Keep Open。当前J1.7在design、原理图、PCB和后处理硬编码均为GND。第29页参考电路对6/7又采用TSCL/TSDA标识，存在资料内部差异；不能据此自行免除脚表约束。

结论是**规格偏离未关闭**，不是“已测到损坏”，也不是“NC接地通常没事所以通过”。如要保持GND，需精确屏版本的认可依据；如要恢复NC，需讨论后同步全部赋值位置，防止 `apply_extra_gnd_pads` 再次接地。

### 5.2 新发现N01：升压电路不能只复核RESE

| 对象 | 当前设计 | 第29页参考 / 本轮判断 |
|---|---|---|
| 电感L1 | 68µH；描述Isat≥0.2A；C2827366 | 图为47µH/500mA；不是同一参数组合，需确切器件DCR/饱和电流和动态依据 |
| 飞跨/泵电容C15 | 1µF/50V，0805 | 参考相应C3为4.7µF/25V；较高耐压不等于满足容量条件 |
| GDR下拉 | 当前GDR网络只有屏脚和Q1栅极 | 参考R1为1M到地；缺少该件需解释关断/浮空行为，不直接断言必定失效 |
| Q1 | AO3400A，备选描述Si1304BDL | 参考Si1308EDL；应比对驱动电压下Rds(on)、栅电荷、耐压及封装，而非只看N-MOS |
| RESE R14 | 2.2Ω、默认0402，额定功率未锁定 | 阻值一致；参考元件表给0603/0805及功率要求，脉冲能力仍需依据 |

本轮未更换任何元件。应将此项列为首件电源/显示验证前的P1调查任务，并核对供应商例程是否对应当前屏修订。不能未经讨论拿参考值机械替换现有设计后直接重布线。

### 5.3 LDO与续航

XC6220引脚兼容不能证明动态稳定性。[Torex第11页](https://product.torexsemi.com/system/files/series/xc6220.pdf) 的3.0–3.5V档将CIN/CL成对规定；当前近端C3=1µF、C4=2.2µF，尚缺实际电容有效容量和布局依据。同网的C2/C6不能忽略，也不能仅把标称值相加当近端补偿容量。

SO8的ST25DV未提供其他封装的LPD控制脚。[ST表249](https://www.st.com/resource/en/datasheet/st25dv64kc.pdf) 的3.3V常供电静态待机为76µA典型。用76+8+5+1.85=90.85µA作简化基线，250mAh纯待机约115天；这是估算，未计刷新、自放电、保护、漏电、温度、有效容量等。现有“13µA/约两年/一年充一次”尚无支撑，待讨论后统一修订ADR、固件和design说明。

### 5.4 USB、充电和射频

USB0.8mm是用户已确认的首版决策，保持。公差范围包含0.75mm不能证明整个区间适配座子。须补供应商机械范围、实际座子型号与首件量测。[Espressif布局指南](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c3/pcb-layout-design.html) 仍要求关注USB差分与回流；应沿端到端路径分析，网络总长统计包含分支。

充电器主料仍写TP4054/MCP73831，实际电池未锁；系统从VBAT取电，没有独立负载电源路径管理。需要指定充电允许条件、受保护电池包、极性和连接器，测试系统负载对终止/恢复的影响。不能宣称无电池USB一定失败，也不能将此场景视为已验证。

NFC铜线圈盖阻焊是既有设计，不因截图颜色改变而重开窗。电感公式不能替代带屏、电池、外壳、人体后的谐振和手机兼容性测量；C11初始DNP与后续调谐状态都应在装配表中明确。

## 6. 机械审查

FreeCAD重建得到94×93×6.3mm，前框有效体积7827.4907mm³、后盖7095.0721mm³，两者均单一有效solid。既有STEP含403个solid，经OCC读取有效。10组扩展两两交叠为0，包含此前未显式检查的电池占位与PCB STEP。

新导出的STEP同样含403个有效solid；扩展10组检查仍全部0，见 `mechanical-fresh-step.json`。这是严格限定的几何结果：电池为45×48×2mm占位体，未包含实际保护板/出线/连接器；屏是平板、没有FPC；按键为孔而无执行件；胶厚和公差链不足；J3源STEP在仓库缺失，J2源模型也无法从本机官方库解析。原脚本会在检查前先写文件，发现交叠仅打印CHECK，未形成发布阻断。后续应先验证实体及干涉，再原子发布。

屏第6页开窗位置支持ACTIVE_TOP=6.7mm，0.30mm补强尾端信息可用于FPC厚度复核；动态弯折包络、翻盖开启/插拔空间和实际接触面仍需实装。图片若未对准目标必须重拍，遵循 `docs/05-visual-check.md`。

## 7. 工程与制造流程审查

- `NET_CLASSES`没有被生成流程使用；Default、Power、NFC的声明不能自动约束当前PCB。应区分首选走线宽度与DRC强制最小宽度。
- `check_netlist.py`只检查导出网表，不读PCB，也依赖固定输出路径。新增审查工具补充了设计→PCB焊盘和符号→固件GPIO比较，但不是产品生产门禁的替代。
- `route_pcb.py::drc_json`在失败时读旧报告已复现。应让失败不能产生PASS；每次报告使用独立路径/输入指纹并验证返回码。
- `export.sh`的ERC真实进程失败可停止；DRC进程失败被吞。两者都缺少违规退出码，完整warnings与原理图一致性检查没有形成生产要求。
- 原地更新ZIP存在未来旧成员残留风险；本轮当前ZIP成员与目录完全一致，不能把流程风险写成当前包已污染。此机未独立重复原报告所用zip工具的旧成员更新实验。
- BOM工程清单包括ANT1与测试点；位置表包括C11。需另做装配清单和对应的位置文件，不应自动删除工程记录中的这些对象。
- UUID随机/当天日期会制造非功能diff；外壳模块导入即运行main，渲染通过删末尾调用绕开；这些是可维护性工作，不应为审查而大幅重构。
- README快速开始会重建未布线PCB再导出；`tools/README.md`尾部仍有“盖绿油才Freerouting”的旧说法，和根AGENTS冲突；BOM文档指向不存在的export.py。这些冲突在本轮登记，未擅自改写旧流程。
- 依赖版本未固定、许可决定未完整、缺少自动化CI。当前二进制可复现是正面证据，但不能取代版本锁和长期发布追溯。

## 8. 如何使用本报告

原审查原样保存在 [external-review.md](external-review.md)，没有把其中命令当作用户授权。逐项F01–F20与新增N01的合并结论、优先级、修改入口、批准点和关闭标准见 [integrated-plan.md](integrated-plan.md)。后续执行请使用 [tools/review/README.md](../../../tools/review/README.md)，不要覆盖本次审查证据。

没有实测的项保持“待验证”；没有修改的缺陷保持“未修复”。审查提交不是硬件生产发布，也不是下一版固件发布。
