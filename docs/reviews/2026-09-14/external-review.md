# chroma-badge / BADGE-42C 详细审查报告

审查日期：2026-09-14  
基准提交：[ee978f08cbdb7b61bbe2c78fea0e9c7cd2c34a7b](https://github.com/wisdom-km/chroma-badge/commit/ee978f08cbdb7b61bbe2c78fea0e9c7cd2c34a7b)  
范围：项目定位、设计数据、原理图导出网表、PCB文本、制造输出、固件、外壳脚本、工程复现与后续软件闭环。

## 1. 结论

项目已经具备实质性的工程样机设计基础：4.2寸四色屏、ESP32-C3、ST25DV、参数化PCB与外壳、制造输出，以及最小上电自检固件。保留现有总体架构是合理的。

当前最需要投入的是跨模块验证与首件闭环。仓库已有“设计数据一致、已保存的错误级ERC/DRC报告为空”的证据，但尚不足以支持“稳定唤醒、可靠刷屏、完整手机传图、年级别续航、可直接交付生产”的判断。

本次发现的关键问题：

1. GPIO9被配置为ESP32-C3深睡唤醒脚；配置返回值被忽略。
2. 文档要求按住BOOT复位触发刷白，实际与ROM下载模式冲突。
3. SO8封装ST25DV常供电的待机电流，被误按低功耗模式估算。
4. ERC/DRC没有作为制造导出的可靠阻断条件。
5. design.py声明的Power/NFC网络规则未落实到工程。
6. 屏幕pin 7接地与仓库引用的Keep Open要求存在未关闭的偏离。
7. 更换LDO后，稳定性验证仍主要停留在引脚兼容。
8. “NDEF打开网页”和“网页经FTM传图”之间存在平台能力缺口。

这些发现不意味着整块板必须推倒重来；它们意味着需要在冻结下一版之前，把明确的软件缺陷和硬件验证缺口逐项关闭。

## 2. 本次实际完成的核查

| 核查 | 结果 | 能证明什么 |
|---|---|---|
| 固定提交并读取仓库树 | 90个已跟踪文件，包含输出件 | 审查版本可定位 |
| 读取项目文档与关键源码 | 9个Python文件、3个C++文件，以及头文件、配置与导出脚本等 | 覆盖主要实现链 |
| 运行原check_netlist.py | 通过；解析63个原理图网络，其中设计有41个功能网络，其余包含未连接脚网络 | 已提交网表与design.py一致 |
| 独立解析PCB文本 | 57个封装、564段走线、128个过孔，全部封装在B.Cu | 与仓库进度记录一致 |
| 比较PCB焊盘网络与design.py | 预期连接引脚未见网络不一致或缺少焊盘；显式NC脚未见接入功能网络 | 验证引脚网络分配，不等于验证实际铜连接与电气功能 |
| NFC封装层检查 | 线圈主体在B.Cu，无Mask；桥在F.Cu，通孔保留Mask | 支持“线圈铜仍在、已盖阻焊”的记录 |
| Python AST语法检查 | 9个Python文件通过 | 只证明语法可解析 |
| 导出脚本故障注入 | 模拟DRC返回5，原脚本仍进入Gerber导出 | 已复现导出门禁缺陷 |
| ZIP更新行为实验 | 旧文件从目录删除后仍残留于旧ZIP | 已复现制造包残留风险 |
| 原epd.cpp主机模拟 | BUSY恒高、关电BUSY超时两种情况下均返回成功 | 已复现驱动错误状态表达不足 |
| 官方资料对照 | Espressif、ST、Torex、KiCad、Chrome | 支撑引脚、功耗、稳定性、导出与平台限制判断 |

本环境未安装KiCad、pcbnew、FreeCAD或PlatformIO，且没有实物。因此没有重新运行完整ERC/DRC、目标固件构建、3D布尔干涉、射频、充电或实屏测试。仓库中的既有ERC/DRC记录只覆盖error级别；不能把它表述成所有告警均已消除。

屏幕官方规格下载页可以访问，但本次没有取得仓库所引用的2026-06-17完整规格书。涉及pin 7及驱动时序的判断，分别明确使用仓库自述证据或标为待厂商/实测确认。

## 3. 优先修复的问题

优先级定义：P1为冻结设计或扩展功能前应关闭的问题；P2为首件验证、可靠性与维护改进；P3为后续产品化。优先级与证据强度分开，不把“风险”写成“已实测故障”。

### F01｜P1｜深睡唤醒配置包含不支持的GPIO9

**证据：** [main.cpp](https://github.com/wisdom-km/chroma-badge/blob/ee978f08cbdb7b61bbe2c78fea0e9c7cd2c34a7b/firmware/src/main.cpp) 第31–42行，将NFC_GPO与BOOT_n一起组成唤醒mask；[pins.h](https://github.com/wisdom-km/chroma-badge/blob/ee978f08cbdb7b61bbe2c78fea0e9c7cd2c34a7b/firmware/include/pins.h) 将二者分别定义为GPIO1和GPIO9，调用后没有检查返回值。

ESP32-C3深睡支持的RTC GPIO为0–5，GPIO9不在其中。官方API明确：mask包含无效深睡引脚时返回ESP_ERR_INVALID_ARG。[GPIO说明](https://docs.espressif.com/projects/esp-idf/en/v4.4.8/esp32c3/api-reference/peripherals/gpio.html)、[睡眠API](https://docs.espressif.com/projects/esp-idf/en/v4.4.8/esp32c3/api-reference/system/sleep_modes.html)。

**影响：** BOOT不能按当前方式唤醒深睡。在所核对的ESP-IDF v4.4.8实现中，循环检查到GPIO9后提前返回，最终GPIO唤醒源使能语句不会执行；因此不能假设GPIO1仍可正常唤醒。固件也没有计时唤醒兜底。[官方实现](https://github.com/espressif/esp-idf/blob/v4.4.8/components/esp_hw_support/sleep_modes.c)。

**建议：** 当前硬件先只启用GPIO1深睡唤醒并检查错误；RESET保持作为恢复入口。若用户键必须唤醒深睡，应重新分配支持的引脚，或另行评估light-sleep的功耗代价。记录复位原因、唤醒原因以及失败原因。

**验收：** 唤醒配置返回ESP_OK；反复休眠/触碰可恢复；没有NFC事件时维持稳定待机；无效配置不能打印“唤醒已就绪”。

### F02｜P1｜刷白自检入口与BOOT下载模式冲突

**证据：** [firmware/README.md](https://github.com/wisdom-km/chroma-badge/blob/ee978f08cbdb7b61bbe2c78fea0e9c7cd2c34a7b/firmware/README.md) 的上电步骤要求“按住BOOT复位”；[main.cpp](https://github.com/wisdom-km/chroma-badge/blob/ee978f08cbdb7b61bbe2c78fea0e9c7cd2c34a7b/firmware/src/main.cpp) 第68–73行在setup中等待这个条件。

GPIO9复位时为低会进入ROM下载模式，应用通常不会运行到setup。[Espressif启动模式](https://docs.espressif.com/projects/esptool/en/latest/esp32c3/advanced-topics/boot-mode-selection.html)。

**建议：** 正常复位后设置一个明确的短暂用户输入窗口，或使用串口命令启动显示自检。BOOT下载操作与应用自检操作分别说明。不要依赖用户卡准启动采样后的几十毫秒。

**验收：** 按文档操作能稳定触发自检；下载固件入口保持可用；串口输出能区分下载模式、正常启动与自检状态。

### F03｜P1｜待机预算错误地套用了ST25DV低功耗模式

**证据：** [design.py](https://github.com/wisdom-km/chroma-badge/blob/ee978f08cbdb7b61bbe2c78fea0e9c7cd2c34a7b/hardware/pcb/scripts/design.py) 中U2为SO8器件，VCC直接接+3V3；[ADR](https://github.com/wisdom-km/chroma-badge/blob/ee978f08cbdb7b61bbe2c78fea0e9c7cd2c34a7b/docs/01-architecture-decisions.md) 2.4节按ST25DV小于1µA、整机约13µA推算约两年待机。

ST规格书说明LPD功能仅在10-ball/12-pin封装提供；表249给出常供电静态待机在3.3V下典型约76µA。不能将本SO8设计视为已进入LPD模式。[ST25DVxxKC规格书，第7页及第141页](https://www.st.com/resource/en/datasheet/st25dv64kc.pdf)。

采用仓库的ESP32 5µA假设、Torex PS模式8µA以及1M/1M分压约1.85µA，可得到一个简化基线：

| 项 | 电流 |
|---|---:|
| ST25DV常供电静态待机 | 76µA典型 |
| XC6220 PS静态电流 | 8µA典型 |
| ESP32深睡 | 5µA，沿用仓库估算，未实测 |
| 电池分压，按3.7V | 1.85µA |
| 简化合计 | 90.85µA |

XC6220静态电流来源：[Torex规格书](https://product.torexsemi.com/system/files/series/xc6220.pdf)。

在这个理想化模型下，250mAh约对应115天纯待机，且还没有扣除更新耗电、电池自放电、保护电路、温度、漏电、可用容量及低电压限制。**115天是量级估算，不是实测续航承诺。**

**建议：** 先决定首版是否接受较短续航；若必须一年以上，重新评估NFC供电控制或封装选择。供电控制还会影响I²C、GPO与FTM，不能只加一个关电动作。更新功耗表时同时列明工作模式、供电条件、典型值与实测值。

**验收：** 完整装机、USB断开条件下取得稳定待机电流与一次更新电荷量，用实际电池容量重新计算续航。

### F04｜P1｜制造导出没有可靠的ERC/DRC门禁

**证据：** [export.sh](https://github.com/wisdom-km/chroma-badge/blob/ee978f08cbdb7b61bbe2c78fea0e9c7cd2c34a7b/hardware/pcb/scripts/export.sh) 第9–11行：

- ERC/DRC没有使用--exit-code-violations。
- DRC额外使用“|| true”吞掉失败。
- 后续照常生成Gerber与贴片文件。
- 只筛error，且没有启用schematic-parity。

KiCad需要显式开启按违规返回非零退出码的选项。[KiCad 9 CLI](https://docs.kicad.org/9.0/en/cli/cli.html)。

**本次复现：** 在临时目录运行原export.sh，用模拟kicad-cli让DRC写出错误并返回5；脚本仍越过网表检查，到达Gerber导出。模拟器在那里主动终止，未生成真实生产文件。

**建议：** ERC与DRC明确采用失败阻断；保留完整报告，对允许的警告维护可追踪清单。把检查通过与发布包生成放在同一个受控流程中。检查失败不能覆盖上一次可用生产包。

**验收：** 人为构造检查失败时，生产导出命令不被调用；输出能指出失败阶段及报告位置。

### F05｜P1｜Power/NFC规则没有落地，DRC通过范围比预想更窄

**证据：** [design.py](https://github.com/wisdom-km/chroma-badge/blob/ee978f08cbdb7b61bbe2c78fea0e9c7cd2c34a7b/hardware/pcb/scripts/design.py) 第282–287行声明Default/Power/NFC；但脚本中没有使用NET_CLASSES的代码；[badge.kicad_pro](https://github.com/wisdom-km/chroma-badge/blob/ee978f08cbdb7b61bbe2c78fea0e9c7cd2c34a7b/hardware/pcb/badge.kicad_pro) 的net_settings仅有Default，网络分配为空。

本次从PCB提取到：

| 网络 | 设计声明的track值 | 当前实际线段宽度 |
|---|---:|---|
| VBUS | 0.3mm | 0.2mm |
| VBAT | 0.3mm | 0.15、0.2mm |
| +3V3 | 0.3mm | 0.15、0.2mm |
| EPD_SW | 0.3mm | 0.15、0.2mm |
| NFC_AC0/AC1馈线 | 0.5mm | 0.15、0.2mm |

线圈本体为自定义铜焊盘，不计入上述馈线宽度统计。上述宽度也不能单独用来断言载流或射频失效。

**建议：** 把网络类别、分配和需要强制执行的约束真正写入工程。KiCad中“默认走线宽度”与“DRC强制最小宽度”应分别设置。电源按电流与压降预算、USB按信号完整性、EPD开关回路按回流与寄生参数制定规则。

**验收：** 工程可读到正确分类；导出DSN保留所需规则；故意画一段违反强制约束的线能够被检查拦截。

### F06｜P1｜pin 7的Keep Open偏离应正式关闭，修复不能只改design.py

**证据：** [复核清单](https://github.com/wisdom-km/chroma-badge/blob/ee978f08cbdb7b61bbe2c78fea0e9c7cd2c34a7b/docs/04-review-checklist.md) 引用GDEM042F86第7页为NC Keep Open，但当前[design.py](https://github.com/wisdom-km/chroma-badge/blob/ee978f08cbdb7b61bbe2c78fea0e9c7cd2c34a7b/hardware/pcb/scripts/design.py)及PCB将J1.7接地。

更重要的是，[route_pcb.py](https://github.com/wisdom-km/chroma-badge/blob/ee978f08cbdb7b61bbe2c78fea0e9c7cd2c34a7b/hardware/pcb/scripts/route_pcb.py) 第302–313行的apply_extra_gnd_pads会强制把J1.7接地，第945行无条件调用。即使今后只改design.py，这个补线流程也会把PCB改回去。

**判断：** 已确认存在规格偏离记录和双重网络赋值逻辑；未实测证明屏一定损坏或一定不能工作。本次未独立读取该版屏幕PDF，不能把仓库摘录冒充独立厂商确认。

**建议：** 在没有该确切屏型号、修订版的书面许可前，按Keep Open处理更稳妥。同步修正生成数据与后处理器，禁止布线器擅自改变器件功能网络。恢复NC属于引脚约束修正，不需要推翻四色/电池/ESP32总体选型。

**验收：** 屏幕脚表、design.py、原理图、PCB一致；执行允许的后处理后仍一致；任何偏离有可追溯依据。

### F07｜P1｜XC6220替换验证需要补上电容与动态稳定性

**证据：** [design.py](https://github.com/wisdom-km/chroma-badge/blob/ee978f08cbdb7b61bbe2c78fea0e9c7cd2c34a7b/hardware/pcb/scripts/design.py) 使用AP2112符号、XC6220料号，近端C3=1µF、C4=2.2µF。[复核清单](https://github.com/wisdom-km/chroma-badge/blob/ee978f08cbdb7b61bbe2c78fea0e9c7cd2c34a7b/docs/04-review-checklist.md)确认引脚兼容，但没有关闭环路稳定性问题。

XC6220厂商推荐表将输入电容与输出电容组合关联；在3.0–3.5V输出档，CIN=10µF时推荐CL=4.7µF，CIN=4.7µF时推荐CL=47µF，并要求近端布置与考虑有效容量下降。[Torex规格书，第11页](https://product.torexsemi.com/system/files/series/xc6220.pdf)。

板上还有C2、C6等同网电容，不能忽略它们，也不能把它们的标称容量直接当作LDO引脚处的等效高频电容。因此这是**有依据的稳定性风险，尚不是已实测振荡**。

**建议：** 用实际主选型号重新核对近端CIN/CL、有效容量、ESR及布线；评估睡眠到射频发射、刷屏启动等负载变化。替代料表除pinout还要记录电容条件、压差与静态电流。

**验收：** 电压范围与负载转换下供电稳定，没有异常纹波、复位或明显超调。

### F08｜P1｜手机传图路线需要先做端到端能力验证

**证据：** [ADR](https://github.com/wisdom-km/chroma-badge/blob/ee978f08cbdb7b61bbe2c78fea0e9c7cd2c34a7b/docs/01-architecture-decisions.md) 同时规划NDEF URL、FTM、BLE/SoftAP与网页下发；[nfc.cpp](https://github.com/wisdom-km/chroma-badge/blob/ee978f08cbdb7b61bbe2c78fea0e9c7cd2c34a7b/firmware/src/nfc.cpp)目前只初始化I²C并探测ACK。

Chrome Web NFC仅暴露NDEF读写，不提供这里需要的厂商邮箱底层命令能力。[Chrome官方文档](https://developer.chrome.com/docs/capabilities/nfc)。

**结论：** 手机碰NDEF打开网页可作为入口，但这不意味着网页能直接操作ST25DV FTM。NFC Type 5标签的支持，也不等于Web API开放厂商自定义命令。

**建议：** 先选一个首版闭环：

| 路线 | 用户体验 | 主要工程条件 |
|---|---|---|
| 原生手机端＋NFC FTM | 保持贴靠传完图片 | 验证目标手机命令能力与会话流程 |
| NFC作入口＋原生端BLE | 碰一下后无线传图 | 手机应用、配对、恢复与协议 |
| NFC作入口＋设备SoftAP网页 | 本地网页编辑与传输 | 入网步骤、本地页面、浏览器连接与认证 |
| 已配网设备按需拉取 | 后台管理与批量更新 | 明确唤醒方式、联网时间与续航代价 |

暂时不需要同时实现四种路线。先用真实目标手机完成“一张非纯色图片发到屏幕”，再扩展模板和后台。

深睡时Wi-Fi/BLE连接不维持，因此“后台随时主动推送”还需要另一个唤醒/轮询机制。[Espressif睡眠说明](https://docs.espressif.com/projects/esp-idf/en/v4.4.8/esp32c3/api-reference/system/sleep_modes.html)。

## 4. 固件与协议可靠性

### F09｜P2｜显示驱动可以在异常BUSY状态下报告成功

[epd.cpp](https://github.com/wisdom-km/chroma-badge/blob/ee978f08cbdb7b61bbe2c78fea0e9c7cd2c34a7b/firmware/src/epd.cpp)第43–51、106–152行：

- wait_idle只等待低电平结束，没有证明刷新确实开始。
- power_on内部等待返回值被忽略；refresh_solid随后再次等待，形成隐式重试。
- power_off等待返回值被忽略，最终返回值只表达刷新阶段等待结果。

本次使用原epd.cpp加主机I/O替身运行：

| 模拟条件 | 原驱动返回 |
|---|---|
| BUSY始终为高 | true |
| 关电阶段BUSY一直为低并超时 | true |

第一项证明它无法区分正常空闲与“BUSY从未进入忙”；第二项直接证明关电超时被丢失。模拟中的65ms、5067ms只是替身时钟累计，不能当作真实屏幕时序。

**建议：** 将显示流程的启动、传输、刷新完成、关电结果分别报告；按确切屏规格处理最小命令延迟和BUSY转换，避免盲目要求所有命令都出现相同边沿。增加结构化错误码、有限恢复、低电量拒绝刷新与最小刷新间隔。

**验收：** 模拟异常得到可区分错误；实屏获得时序记录；仅在完整流程成功后更新“显示完成”状态。

### F10｜P2｜NFC探测需要升级成状态明确的驱动

当前ACK只表明地址有人响应，不等于型号、NDEF、邮箱和事件配置均就绪。

建议加入型号/UID识别、配置读回、用户区与系统区封装、I²C错误处理、邮箱状态、超时与恢复。初始化要支持“新芯片”和“已被改过配置的芯片”。

注意：不能断言“没有写GPO配置，所以出厂芯片绝对不产生事件”。KC规格书说明默认提供RF场变化检测；本项目的问题是没有验证、恢复或管理所需配置。[ST规格书](https://www.st.com/resource/en/datasheet/st25dv64kc.pdf)。

### F11｜P2｜图像传输应先定义协议，再写长流程

400×300×2bit为30,000字节；ST25DV64KC用户EEPROM为8KB，FTM为256字节邮箱。[ST规格书](https://www.st.com/resource/en/datasheet/st25dv64kc.pdf)。

推导：未压缩完整图片不能直接放入这8KB EEPROM。按每包最多256字节且忽略头部计算，至少118包；真实协议需要更多空间。邮箱用于分片交换，完整图可在MCU RAM组装，若要求断电恢复则增加可靠持久化。

建议协议明确：

- 版本、图像宽高、像素编码、长度与图像ID。
- 会话ID、分包序号、分片偏移、校验。
- ACK、超时、重试、重复包与断点恢复。
- 完整图验证成功后才允许刷屏。
- “传输完成”和“显示完成”分别确认。
- 上限约束，避免错误长度造成越界或资源耗尽。

无需一开始引入复杂协议框架，先形成一页可执行的协议规范和黄金测试图片。

### F12｜P2｜电源与休眠应成为统一状态机

main负责休眠、epd负责电源开关、NFC未来又需要独立会话，若各自操作电源容易产生时序交叉。

建议采用一个明确的应用流程：启动诊断 → 判断唤醒原因 → 接收会话 → 完整性验证 → 刷屏 → 关电与日志 → 休眠；超时和低电量统一进入恢复分支。电源状态只能有一个管理入口。

同时复核SPI外设停止后引脚是否真的到达预期电平、GPIO hold的设置与释放顺序，以及屏断电后的I/O漏电。当前调用digitalWrite后并不能仅凭源码断言所有外设复用脚都已实现物理隔离，此项需要实测。

## 5. PCB、制造与机械

### F13｜P2｜USB与EPD关键回路需要针对性布线审查

仓库复核清单中的“C3全速不严格要求差分”容易让维护者误解。Espressif仍建议USB并行差分、连续参考地、控制阻抗并减少换层。[USB布局指南](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c3/pcb-layout-design.html)。

当前PCB中USB_DP有4个过孔，USB_DN有2个；它们的全部平面线段总长分别约30.20mm和35.08mm。**这些是网络总量统计，包含分支，不能直接解释为端到端差分长度误差。** 需要沿连接器到芯片路径核查。

EPD_RESE网络全部平面线段合计约31.35mm并有2个过孔，应重点检查电流采样回路和参考地。连接正确不保证动态波形良好。

建议优先人工审查USB、电源主干、升压开关回路、采样回路及NFC馈线，再让自动布线处理一般控制信号。检查USB调试元件预留与接口ESD设计，具体参数按器件指南与测试确定。[USB原理图建议](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c3/schematic-checklist.html)。

### F14｜P2｜NFC与Wi-Fi天线的最终表现仍需装机验证

线圈盖阻焊已由PCB文本证实，不应为了截图显黄而重开窗。几何电感计算适合初选，无法替代装机后的谐振、耦合和手机兼容性测试。

屏幕层、电池、外壳、贴胶、人体与手机壳都应纳入测试条件。C11预留调谐位置是优点，但需要记录实际装配状态、器件值和测量结果。Wi-Fi模组也需验证最终外壳中的净空与实际连接表现。[Espressif模组天线布局建议](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c3/pcb-layout-design.html)。

不要把“目前能清DRC”作为天线设计验收指标，也不应在没有测量的情况下直接断言现有线圈无效。

### F15｜P2｜制造包存在DNP与非贴装项目混入

[位置文件](https://github.com/wisdom-km/chroma-badge/blob/ee978f08cbdb7b61bbe2c78fea0e9c7cd2c34a7b/hardware/pcb/output/badge_pos_back.csv)包含DNP的C11；[BOM](https://github.com/wisdom-km/chroma-badge/blob/ee978f08cbdb7b61bbe2c78fea0e9c7cd2c34a7b/hardware/pcb/output/badge_bom.csv)包含ANT1和TP1–TP4这类板上铜图形/测试焊盘。当前BOM有34行，其中21行没有LCSC编号；部分为空合理，但可采购器件需要补全。

建议区分：

1. 工程全量BOM，包含DNP与板级元素。
2. 实际贴装BOM，仅含装配器件及锁定料号。
3. 贴装位置表，与实际装配BOM一一对应。
4. 备选物料表，列电气、机械和固件兼容条件。

这主要是交付歧义与返工风险，不能据此断言工厂一定会错贴。

### F16｜P2｜模型完整性与机械验收范围不足

[USB封装](https://github.com/wisdom-km/chroma-badge/blob/ee978f08cbdb7b61bbe2c78fea0e9c7cd2c34a7b/hardware/pcb/lib/badge.pretty/TYPE-C-31-M-14.kicad_mod)引用项目内lib/3d/TYPE-C-31-M-14.step，但该文件不在本次仓库树中。仓库内ESP32 STEP存在；不能因为没有下载到本地审查副本就误报它缺失。

缺少USB源模型会影响干净环境下重新导出与机械核查。已有badge_full.step是否包含从旧环境嵌入的USB实体，本次未独立解析，因此不作结论。

[外壳脚本](https://github.com/wisdom-km/chroma-badge/blob/ee978f08cbdb7b61bbe2c78fea0e9c7cd2c34a7b/hardware/enclosure/badge_enclosure.py)还存在以下验证边界：

- 未建立FPC弯折实体、连接器翻盖开启空间、插拔操作空间。
- 电池为仓位简化体，没有实际电芯、保护板、导线和连接器的完整包络。
- 胶层与材料公差尚未完整纳入厚度堆叠。
- 按键目前是后盖孔，没有明确的可触达执行件设计。
- 有干涉时仅打印CHECK，没有失败退出；并且输出文件在检查之前已写入。
- 缺少部分实体之间的检查，例如实际电池/导线与PCB组件的装配关系。

因此“干涉0”只覆盖已建模、已检查对象。建议把模型完整性、最小间隙、实体有效性、运动空间与实际装配公差纳入机械发布门槛。

0.8mm板厚是已接受的首版选择，保留这个决策；但“0.8±0.1包含0.75”不能证明公差区间全部适配连接器。通过供应商允许范围与首件尺寸记录补全验证。

### F17｜P2｜电池与供电路径还没有形成确定的装配规格

仓库明确电池自带PCM，这是合理约束。但具体电芯料号未锁定，充电器仍写TP4054/MCP73831两个选择，且系统从VBAT取电，没有独立系统电源路径管理。

建议先锁定具体受保护电池包和充电器版本，由具备相关经验的硬件人员核对允许充电条件、保护方案、机械包络和热条件；验证系统负载对充电终止、低电压恢复及USB供电启动的影响。保护板存在不等于上述条件已经全部满足。

软件应定义低电量行为、充电期间是否允许传图/刷新、异常重启恢复。此处不将“无电池插USB一定失败”当作已证实结论，而将它作为应测试的用户场景。

### F18｜P2｜制造输出的版本一致性需要加强

[export.sh](https://github.com/wisdom-km/chroma-badge/blob/ee978f08cbdb7b61bbe2c78fea0e9c7cd2c34a7b/hardware/pcb/scripts/export.sh)会清空gerbers目录，却更新既有ZIP，旧ZIP成员可能留下。本次最小实验确实复现：旧文件已从目录删除，重新zip后压缩包仍同时包含旧、新文件。

另一个问题是export.sh只更新drc_final.rpt，不更新drc_final.json；后者来自route_pcb.py，今后容易与当前板产生不同步。

建议每次在新的临时目录生成完整发布包，通过后整体替换。记录源提交、PCB/原理图哈希、工具版本、BOM版本、检查报告与生产文件SHA-256。生产包文件清单应与本次输出严格一致，不保留旧成员。

## 6. 工程维护与产品化

### F19｜P2｜生成器与自动补线器需要收敛为可验证流程

保留design.py作为集中定义是正确方向，但需要让它真正控制所有关键结果：

- pins.h目前是手写副本：增加自动生成或引脚映射一致性检查。
- route_pcb.py不应硬编码改功能网络；检查器应对后处理结果再次比对。
- check_netlist.py仅比对已导出网表，不直接检查PCB；本次独立比对通过不代表未来自动得到保障。
- drc_json未检查子进程退出状态，又复用固定文件名，可能在命令失败时读到旧报告。
- 原理图生成器使用随机UUID及当天日期；无功能修改也会产生大量diff。建议为元件、引脚、标签用稳定标识，并分离生成时间与设计版本。
- 原理图“全局标签拼接”易生成但难审查关键回路；按USB、电源、主控、NFC、EPD分区画清电流路径，特别是升压与采样。
- 外壳模块导入会执行main，渲染脚本靠删除末尾字符串规避；应拆分纯几何函数与命令入口。
- GND聚类和碰撞搜索逻辑有重复；未来提取几何、连通性、修复策略和CLI层，保留有代表性的回归板。
- 简化“--skip-route不动走线”的说法：代码仍执行join_duplicate_pads与repair，应明确它是跳过自动布线，而非严格只读或保证不修改信号线。
- 根README快速开始直接生成未布线PCB后接导出，容易覆盖现有路由并导出未完成板；应提供“检查现有板”与“重新生成并布线”两条清晰入口。

按AGENTS约定，目前不用重跑生成器来验证这些问题，也不需要修改既有ADR来完成本次审查。

### F20｜P2/P3｜构建、文档与产品边界

当前platformio.ini未固定espressif32版本，虽然固件README记录了生成二进制的工具版本。建议固定已验证依赖，保留固件哈希、构建日志和源码提交；先建立编译、网表/引脚一致性、协议边界、检查失败阻断这些少量高价值测试。

当前树未见自动化工作流、测试目录或项目自身LICENSE。建议增加轻量CI、开源许可声明及第三方内容清单；正式分发前确认各资源许可，不把README中的一句来源说明等同于完整许可资料。

文档有局部不同步：

- BOM文档指向不存在的export.py，实际是export.sh。
- ADR写固件另行开发，实际上已有v0.1自检。
- 状态表、复核清单中的“通过”有时表示工程决策，有时表示规格验证或实测。
- 早期erc.rpt有大量库配置警告，较新erc_errors.rpt只是错误级筛选。
- 不应把NDEF、FTM、BLE、Wi-Fi列为同一种“已支持”能力。

建议统一使用“设计完成 / 静态通过 / 已构建 / 实机通过 / 待验证 / 已接受偏离”这些状态，并关联证据。

产品第一阶段建议专注：姓名、职位/组织、品牌色块、二维码、少量模板，以及稳定更新。四色屏适合这类用途；任意照片与渐变效果留到后续。增加离线二维码可读性、模板最小字高与刷新进度反馈。

安全设计应围绕实际写入入口：允许公开读取名片，不代表允许任何邻近手机覆盖工牌。在实现写入前定义设备所有权、授权窗口、传输完整性、重放处理和设备重置。UID用于识别，不能单独作为写权限凭证。当前还没有完整网络服务，不能把未来设计要求写成现存可利用漏洞。

成本方面，仓库150–225元是既有估算，本次没有做实时采购报价核验。后续预算加入SMT装配、测试治具、损耗、装配工时、包装、物流与返修；不能将元件合计直接当成最终交付成本。

## 7. 建议执行顺序

| 阶段 | 工作 | 完成标志 |
|---|---|---|
| A：修复明确阻塞 | F01、F02、F04、F05、F06；复核F07；重算F03 | 启动/睡眠可解释；规则落地；失败阻断；规格偏离关闭 |
| B：冻结首件规格 | 电池/充电器/屏版本锁定；USB与关键回路审查；装配与模型补齐 | 同一提交可导出一致的工程包与装配清单 |
| C：单板闭环 | 串口诊断、四色/条纹测试、NFC事件、一次完整图像更新、异常恢复 | 能重复运行，失败可定位 |
| D：目标手机闭环 | 只选择一条首版传图路线，验证目标机型 | 图片验证成功后刷新，掉线不会显示半图 |
| E：可靠性 | 待机/更新耗电、低电压、装机射频、充电与机械场景 | 用实测修正续航、性能与可用性描述 |
| F：产品化 | 模板、权限、批量配置、生产测试、发布包与许可 | 可交给其他人复现、使用和维护 |

这不是按日历承诺工期。优先把“会不会稳定工作”的证据补齐，再决定是否进入外壳精修与批量生产。

## 8. 最小验收清单

| 场景 | 通过标准 |
|---|---|
| 正常启动 | 日志可读，版本/复位原因明确 |
| 自检入口 | 文档操作可重复触发，且不与下载模式混淆 |
| 深睡与唤醒 | 合法配置；触碰恢复；连续重复不丢失唤醒 |
| NFC身份与事件 | 型号/配置可读回，事件原因清晰 |
| 显示 | 四色、方向、边界、二维码正确；超时不会报告成功 |
| 图像传输 | 错长、错序、重复、断链均可控；完整校验后才刷屏 |
| 低电量 | 不反复刷屏或重启；恢复路径明确 |
| 功耗 | 待机和单次更新分别测量，给出条件与波动范围 |
| USB | 可重复枚举/下载/查看日志，覆盖正反插与典型线缆 |
| 制造包 | 错误会阻断；BOM与位置表一致；无旧ZIP成员 |
| 装配 | 真实FPC/电池/连接器与胶层可装入；按键/USB可操作 |
| 复现 | 固定版本的干净环境可得到通过检查且可追溯的输出 |

建议项目下一里程碑命名为“工程样机闭环验证”，用这些证据定义完成度。

