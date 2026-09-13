"""Single source of truth for the badge electronics.

Every component is described once here (symbol, footprint, value, pin->net map).
gen_schematic.py turns this into a KiCad 9 schematic, gen_pcb.py into a PCB.
Coordinates for PCB placement are in mm, board frame = front view, origin at
top-left corner of the board, X right, Y down (KiCad convention).
"""
from dataclasses import dataclass, field

KICAD_SYM = "/usr/share/kicad/symbols"
KICAD_FP = "/usr/share/kicad/footprints"
PROJECT_FP = "lib"          # relative to hardware/pcb
ESPRESSIF_SYM = "lib/Espressif.kicad_sym"

# ----------------------------------------------------------------------------
# Board geometry
# ----------------------------------------------------------------------------
BOARD_W = 91.0
PANEL_H = 77.0            # e-paper panel outline 91 x 77, glued to the FRONT
STRIP_H = 7.0             # extra strip under the panel: USB-C mid-mount + buttons
BOARD_H = PANEL_H + STRIP_H
BOARD_CORNER_R = 2.0
BOARD_THICKNESS = 0.8

# Zones on the BACK side (all components live on B.Cu)
BATTERY_POCKET = (3.0, 3.0, 50.0, 53.0)     # x0,y0,x1,y1 : keep free of parts & antenna
NFC_COIL_RECT = (53.0, 3.5, 88.0, 45.0)      # outer rectangle of the loop antenna
NFC_TURNS = 11
FPC_SLOT = (30.0, 77.6, 60.0, 79.6)        # slot for the panel FPC to pass to the back
ESP_ANT_KEEPOUT = (53.0, 60.0, 67.0, 76.0)  # no copper under/in front of the module antenna
NFC_TRACE_W = 0.5
NFC_TRACE_GAP = 0.5

# ----------------------------------------------------------------------------
# Component model
# ----------------------------------------------------------------------------
@dataclass
class Part:
    ref: str
    lib: str                 # symbol library nickname
    symbol: str              # symbol name inside that library
    footprint: str           # "LibNick:FootprintName"
    value: str
    pins: dict               # pin number -> net name
    nc: list = field(default_factory=list)   # pin numbers intentionally unconnected
    section: str = ""
    desc: str = ""           # BOM description / MPN hint
    lcsc: str = ""
    # PCB placement (x, y, rotation_deg). None -> placed in an overflow row
    at: tuple = None
    dnp: bool = False


def R(ref, value, n1, n2, at=None, fp="Resistor_SMD:R_0402_1005Metric", section="", desc="", dnp=False):
    return Part(ref, "Device", "R", fp, value, {"1": n1, "2": n2}, section=section, desc=desc or f"{value} 0402 1%", at=at, dnp=dnp)


def C(ref, value, n1, n2, at=None, fp="Capacitor_SMD:C_0402_1005Metric", section="", desc="", dnp=False):
    return Part(ref, "Device", "C", fp, value, {"1": n1, "2": n2}, section=section, desc=desc or f"{value} 0402", at=at, dnp=dnp)


C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"

PARTS = [
    # ------------------------------------------------------------------ USB-C
    Part("J3", "Connector", "USB_C_Receptacle_USB2.0_16P", "badge:TYPE-C-31-M-14",
         "USB-C 16P 沉板 (TYPE-C-31-M-14)",
         {"A1": "GND", "B1": "GND", "A12": "GND", "B12": "GND", "S1": "GND",
          "A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS",
          "A5": "CC1", "B5": "CC2",
          "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DN", "B7": "USB_DN"},
         nc=["A8", "B8"], section="USB", desc="HRO TYPE-C-31-M-14, 16P USB 2.0 mid-mount receptacle", lcsc="C223907",
         at=(75.0, BOARD_H - 2.7, 0)),
    R("R1", "5.1k", "CC1", "GND", at=(67.5, 78.5, 90), section="USB"),
    R("R2", "5.1k", "CC2", "GND", at=(83.0, 78.5, 90), section="USB"),
    C("C1", "4.7u", "VBUS", "GND", at=(87.5, 72.0, 90), fp=C0603, section="USB", desc="4.7uF 10V X5R 0603"),

    # ------------------------------------------------------- Charger + battery
    Part("U3", "Battery_Management", "MCP73831-2-OT", "Package_TO_SOT_SMD:SOT-23-5",
         "TP4054 / MCP73831T-2ACI/OT",
         {"1": "CHRG_STAT", "2": "GND", "3": "VBAT", "4": "VBUS", "5": "PROG"},
         section="POWER", desc="Li-ion linear charger 4.2V, SOT-23-5 (TP4054 pin-compatible)", lcsc="C32574",
         at=(80.0, 70.0, 0)),
    R("R3", "5.1k", "PROG", "GND", at=(76.5, 72.5, 0), section="POWER", desc="5.1k -> ~200mA charge current"),
    R("R4", "1k", "VBUS", "LED_CHRG_A", at=(86.5, 77.5, 90), section="POWER"),
    Part("D4", "Device", "LED", "LED_SMD:LED_0603_1608Metric", "RED",
         {"1": "CHRG_STAT", "2": "LED_CHRG_A"}, section="POWER", desc="LED 0603 red, charging indicator",
         at=(86.5, 81.0, 0)),
    C("C2", "4.7u", "VBAT", "GND", at=(83.5, 73.5, 0), fp=C0603, section="POWER", desc="4.7uF 10V X5R 0603"),
    Part("J2", "Connector_Generic", "Conn_01x02", "Connector_JST:JST_SHL_SM02B-SHLS-TF_1x02-1MP_P1.00mm_Horizontal",
         "BATT JST-SH 1.0mm", {"1": "VBAT", "2": "GND"}, section="POWER",
         desc="JST SM02B-SHLS-TF 1.0mm 2P horizontal; LiPo <=2.0mm thick, 150-300mAh with PCM", lcsc="C145956",
         at=(10.0, 58.0, 0)),

    # ----------------------------------------------------------------- LDO 3V3
    Part("U4", "Regulator_Linear", "AP2112K-3.3", "Package_TO_SOT_SMD:SOT-23-5", "XC6220B331MR-G",
         {"1": "VBAT", "2": "GND", "3": "VBAT", "5": "+3V3"}, nc=["4"], section="POWER",
         desc="LDO 3.3V, Iq 8uA, 1A, SOT-25 (pinout VIN/GND/CE/NC/VOUT). Alt: TLV75533PDBV, AP2112K-3.3", lcsc="C86534",
         at=(74.0, 66.5, 0)),
    C("C3", "1u", "VBAT", "GND", at=(70.5, 66.5, 90), section="POWER"),
    C("C4", "2.2u", "+3V3", "GND", at=(77.5, 63.5, 0), fp=C0603, section="POWER", desc="2.2uF 10V 0603"),
    # battery voltage sense divider (2uA standby)
    R("R5", "1M", "VBAT", "BAT_SENSE", at=(70.0, 60.5, 0), section="POWER"),
    R("R6", "1M", "BAT_SENSE", "GND", at=(73.0, 60.5, 0), section="POWER"),
    C("C5", "100n", "BAT_SENSE", "GND", at=(76.0, 60.5, 0), section="POWER"),
    Part("TP4", "Connector", "TestPoint", "TestPoint:TestPoint_Pad_D1.0mm", "VBAT", {"1": "VBAT"},
         section="POWER", desc="test pad", at=(5.0, 62.0, 0)),
    Part("TP2", "Connector", "TestPoint", "TestPoint:TestPoint_Pad_D1.0mm", "3V3", {"1": "+3V3"},
         section="POWER", desc="test pad", at=(5.0, 65.0, 0)),
    Part("TP3", "Connector", "TestPoint", "TestPoint:TestPoint_Pad_D1.0mm", "GND", {"1": "GND"},
         section="POWER", desc="test pad", at=(5.0, 68.0, 0)),

    # --------------------------------------------------------------------- MCU
    Part("U1", "Espressif", "ESP32-C3-MINI-1", "badge:ESP32-C3-MINI-1", "ESP32-C3-MINI-1-N4",
         {**{str(p): "GND" for p in [1, 2, 11, 14] + list(range(36, 54))},
          "3": "+3V3", "8": "EN",
          "12": "BAT_SENSE",      # GPIO0 / ADC1_CH0
          "13": "NFC_GPO",        # GPIO1  (RTC wake)
          "5": "EPD_PWR_EN",      # GPIO2  strapping: pulled high, P-MOS off by default
          "6": "EPD_BUSY",        # GPIO3
          "18": "I2C_SDA",        # GPIO4
          "19": "I2C_SCL",        # GPIO5
          "20": "EPD_SCK",        # GPIO6
          "21": "EPD_MOSI",       # GPIO7
          "22": "LED_STAT_n",     # GPIO8  strapping: LED sink, idles high
          "23": "BOOT_n",         # GPIO9  strapping: boot button / user button
          "16": "EPD_CS",         # GPIO10
          "26": "USB_DN",         # GPIO18
          "27": "USB_DP",         # GPIO19
          "30": "EPD_DC",         # GPIO20
          "31": "EPD_RST"},       # GPIO21
         nc=[str(p) for p in [4, 7, 9, 10, 15, 17, 24, 25, 28, 29, 32, 33, 34, 35]],
         section="MCU", desc="Espressif ESP32-C3-MINI-1-N4 Wi-Fi/BLE module, 13.2x16.6x2.4mm", lcsc="C2934569",
         at=(60.0, 57.0, 180)),
    C("C6", "10u", "+3V3", "GND", at=(51.5, 52.5, 90), fp=C0603, section="MCU", desc="10uF 6.3V X5R 0603"),
    C("C7", "100n", "+3V3", "GND", at=(51.5, 55.5, 90), section="MCU"),
    R("R7", "10k", "+3V3", "EN", at=(51.5, 58.5, 90), section="MCU"),
    C("C8", "1u", "EN", "GND", at=(51.5, 61.5, 90), section="MCU"),
    R("R8", "10k", "+3V3", "BOOT_n", at=(69.0, 54.0, 90), section="MCU"),
    R("R10", "10k", "+3V3", "EPD_PWR_EN", at=(69.0, 56.8, 90), section="MCU"),
    R("R9", "1k", "+3V3", "LED_STAT_A", at=(65.0, 78.0, 0), section="MCU"),
    Part("D5", "Device", "LED", "LED_SMD:LED_0603_1608Metric", "GREEN",
         {"1": "LED_STAT_n", "2": "LED_STAT_A"}, section="MCU", desc="LED 0603 green, status", at=(65.0, 81.0, 0)),
    Part("SW1", "Switch", "SW_Push", "Button_Switch_SMD:SW_SPST_PTS810", "RESET",
         {"1": "EN", "2": "GND"}, section="MCU", desc="C&K PTS810 low-profile tactile 1.5mm", lcsc="C221929",
         at=(14.0, BOARD_H - 3.5, 0)),
    Part("SW2", "Switch", "SW_Push", "Button_Switch_SMD:SW_SPST_PTS810", "BOOT/USER",
         {"1": "BOOT_n", "2": "GND"}, section="MCU", desc="C&K PTS810 low-profile tactile 1.5mm", lcsc="C221929",
         at=(24.0, BOARD_H - 3.5, 0)),

    # --------------------------------------------------------------------- NFC
    Part("U2", "RF_NFC", "ST25DV64K-IER8C3", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "ST25DV64KC-IER6S3",
         {"1": "NFC_VEH", "2": "NFC_AC0", "3": "NFC_AC1", "4": "GND", "5": "I2C_SDA", "6": "I2C_SCL",
          "7": "NFC_GPO", "8": "+3V3"}, section="NFC",
         desc="ST25DV64KC dynamic NFC tag, 64Kbit, FTM mailbox, energy harvesting, SO8N", lcsc="C2830253",
         at=(74.0, 51.5, 0)),
    C("C9", "100n", "+3V3", "GND", at=(68.5, 49.0, 90), section="NFC"),
    C("C10", "1u", "NFC_VEH", "GND", at=(68.5, 51.4, 90), section="NFC"),
    Part("TP1", "Connector", "TestPoint", "TestPoint:TestPoint_Pad_D1.0mm", "V_EH", {"1": "NFC_VEH"},
         section="NFC", desc="test pad (energy harvesting output)", at=(87.5, 49.6, 0)),
    R("R11", "4.7k", "+3V3", "I2C_SDA", at=(80.0, 51.5, 90), section="NFC"),
    R("R12", "4.7k", "+3V3", "I2C_SCL", at=(82.0, 51.5, 90), section="NFC"),
    R("R13", "100k", "+3V3", "NFC_GPO", at=(84.0, 51.5, 90), section="NFC"),
    Part("ANT1", "Device", "Antenna_Loop", "badge:NFC_Loop", "PCB loop 35x41.5mm 11T",
         {"1": "NFC_AC0", "2": "NFC_AC1"}, section="NFC",
         desc="PCB spiral antenna, net-tie footprint generated by gen_nfc_footprint.py; tune with C11",
         at=((NFC_COIL_RECT[0] + NFC_COIL_RECT[2]) / 2, (NFC_COIL_RECT[1] + NFC_COIL_RECT[3]) / 2, 0)),
    C("C11", "DNP", "NFC_AC0", "NFC_AC1", at=(82.5, 48.9, 0), section="NFC",
      desc="antenna tuning cap (fit after measuring resonance; ST25DV has 28.5pF internal)", dnp=True),

    # ------------------------------------------------------------------ E-PAPER
    Part("J1", "Connector_Generic", "Conn_01x24", "Connector_FFC-FPC:Hirose_FH12-24S-0.5SH_1x24-1MP_P0.50mm_Horizontal",
         "EPD FPC 24P 0.5mm",
         {"2": "EPD_GDR", "3": "EPD_RESE", "5": "EPD_VSH2", "8": "GND",
          "9": "EPD_BUSY", "10": "EPD_RST", "11": "EPD_DC", "12": "EPD_CS", "13": "EPD_SCK", "14": "EPD_MOSI",
          "15": "EPD_VCI", "16": "EPD_VCI", "17": "GND", "18": "EPD_VDD",
          "20": "EPD_VSH1", "21": "EPD_VGH", "22": "EPD_VSL", "23": "EPD_VGL", "24": "EPD_VCOM"},
         nc=["1", "4", "6", "7", "19"], section="EPD",
         desc="24P 0.5mm FPC connector, bottom contact, flip lock (Hirose FH12-24S-0.5SH or JUSHUO AFC07-S24FCA-00)",
         lcsc="C262657", at=(43.0, 73.0, 0)),
    Part("Q2", "Transistor_FET", "AO3401A", "Package_TO_SOT_SMD:SOT-23", "AO3401A",
         {"1": "EPD_PWR_EN", "2": "+3V3", "3": "EPD_VCI"}, section="EPD",
         desc="P-MOSFET load switch for panel + boost", lcsc="C15127", at=(38.5, 57.5, 0)),
    C("C12", "10u", "EPD_VCI", "GND", at=(42.5, 57.5, 0), fp=C0603, section="EPD", desc="10uF 6.3V X5R 0603"),
    C("C13", "1u", "EPD_VCI", "GND", at=(45.5, 57.5, 0), section="EPD"),
    C("C14", "1u", "EPD_VDD", "GND", at=(38.5, 64.5, 0), section="EPD"),
    Part("L1", "Device", "L", "Inductor_SMD:L_Changjiang_FNR3015S", "68uH",
         {"1": "EPD_VCI", "2": "EPD_SW"}, section="EPD",
         desc="68uH shielded power inductor, Isat>=0.2A, h<=1.5mm (Sunlord SWPA3015S680MT / FNR3015S680MT)", lcsc="C2827366",
         at=(24.5, 57.5, 0)),
    Part("Q1", "Transistor_FET", "AO3400A", "Package_TO_SOT_SMD:SOT-23", "AO3400A",
         {"1": "EPD_GDR", "2": "EPD_RESE", "3": "EPD_SW"}, section="EPD",
         desc="N-MOSFET for EPD boost (alt. Si1304BDL SOT-323)", lcsc="C20917", at=(29.0, 57.5, 0)),
    R("R14", "2.2R", "EPD_RESE", "GND", at=(24.5, 61.0, 0), section="EPD",
      desc="RESE current-sense resistor: confirm value from GDEM042F86 spec (0.47R / 2.2R / 3R variants)"),
    Part("D1", "Diode", "MBR0530", "Diode_SMD:D_SOD-123", "MBR0530",
         {"1": "EPD_VGH", "2": "EPD_SW"}, section="EPD", desc="Schottky 30V 0.5A SOD-123", lcsc="C77896", at=(33.5, 57.5, 0)),
    C("C15", "1u/50V", "EPD_SW", "EPD_PUMP", at=(29.0, 61.0, 0), fp=C0805, section="EPD", desc="1uF 50V X7R 0805 charge pump"),
    Part("D2", "Diode", "MBR0530", "Diode_SMD:D_SOD-123", "MBR0530",
         {"1": "GND", "2": "EPD_PUMP"}, section="EPD", desc="Schottky 30V 0.5A SOD-123", lcsc="C77896", at=(33.5, 61.0, 0)),
    Part("D3", "Diode", "MBR0530", "Diode_SMD:D_SOD-123", "MBR0530",
         {"1": "EPD_PUMP", "2": "EPD_VGL"}, section="EPD", desc="Schottky 30V 0.5A SOD-123", lcsc="C77896", at=(38.7, 61.0, 0)),
    C("C16", "1u/50V", "EPD_VGH", "GND", at=(43.0, 61.0, 0), fp=C0805, section="EPD", desc="1uF 50V X7R 0805"),
    C("C17", "1u/50V", "EPD_VGL", "GND", at=(46.8, 61.0, 0), fp=C0805, section="EPD", desc="1uF 50V X7R 0805"),
    C("C18", "1u/25V", "EPD_VSH1", "GND", at=(24.5, 64.5, 0), fp=C0603, section="EPD", desc="1uF 25V X7R 0603"),
    C("C19", "1u/25V", "EPD_VSH2", "GND", at=(28.0, 64.5, 0), fp=C0603, section="EPD", desc="1uF 25V X7R 0603"),
    C("C20", "1u/25V", "EPD_VSL", "GND", at=(31.5, 64.5, 0), fp=C0603, section="EPD", desc="1uF 25V X7R 0603"),
    C("C21", "1u/25V", "EPD_VCOM", "GND", at=(35.0, 64.5, 0), fp=C0603, section="EPD", desc="1uF 25V X7R 0603"),
]

# Nets that need a PWR_FLAG for ERC (no power-output pin drives them)
PWR_FLAG_NETS = ["GND", "VBUS"]

# Net classes for the PCB (clearance / width in mm)
NET_CLASSES = {
    "Default": {"clearance": 0.15, "track": 0.2, "via": 0.6, "via_drill": 0.3, "nets": []},
    "Power": {"clearance": 0.2, "track": 0.4, "via": 0.6, "via_drill": 0.3,
              "nets": ["GND", "VBUS", "VBAT", "+3V3", "EPD_VCI", "EPD_SW", "EPD_RESE"]},
    "NFC": {"clearance": 0.3, "track": 0.5, "via": 0.6, "via_drill": 0.3, "nets": ["NFC_AC0", "NFC_AC1"]},
}

SECTION_NOTES = {
    "USB": "USB-C 2.0, mid-mount receptacle in the 7mm strip below the panel. CC pulled down 5.1k = UFP. D+/D- go straight to the ESP32-C3 native USB.",
    "POWER": "LiPo (<=2.0mm, 150-300mAh, with PCM) -> 200mA linear charger -> low-Iq LDO 3.3V. VBAT sensed through 1M/1M (ADC1_CH0). Standby budget ~13uA.",
    "MCU": "ESP32-C3-MINI-1. Strapping pins: GPIO2 pulled high (P-MOS off at boot), GPIO8 LED sink (idles high), GPIO9 boot/user button. No UART bridge: program/log over native USB.",
    "NFC": "ST25DV64KC: NDEF URL + fast-transfer mailbox (256B) + RF field wake on GPO -> GPIO1. Loop antenna is drawn on B.Cu in gen_pcb.py; internal tuning cap 28.5pF, target L ~4.8uH; C11 is a DNP trim cap.",
    "EPD": "4.2\" BWRY panel, 24P 0.5mm FPC (GDEM042F86 / Waveshare 4.2 G / GDEY042F51). Standard Good Display boost: 68uH, N-MOS, 3x MBR0530, RESE. BS1=GND -> 4-wire SPI. VDDIO tied to VCI. Panel power gated by Q2.",
}


def all_nets():
    nets = {}
    for p in PARTS:
        for pin, net in p.pins.items():
            nets.setdefault(net, []).append((p.ref, pin))
    return nets


if __name__ == "__main__":
    nets = all_nets()
    print(f"{len(PARTS)} parts, {len(nets)} nets")
    for n, pins in sorted(nets.items()):
        print(f"{n:14s} {len(pins):2d}  {' '.join(f'{r}.{p}' for r, p in pins)}")
