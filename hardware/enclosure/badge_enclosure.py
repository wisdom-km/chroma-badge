"""FreeCAD script: enclosure for the 4.2" BWRY e-paper NFC badge.

Run headless:   freecadcmd badge_enclosure.py
or from the FreeCAD GUI: Macro -> execute this file.

Coordinate frame = KiCad STEP frame of hardware/pcb/badge.kicad_pcb:
  X = PCB x (mm), Y = -PCB y, Z up = towards the FRONT (panel side).
  PCB back face at Z=0, PCB front face at Z=PCB_T. Components hang below Z=0.
Everything is parametric; edit the constants block and re-run.
"""
import os
import sys

import FreeCAD as App
import Part

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
OUT = os.path.join(HERE, "output")
PCB_STEP = os.path.join(HERE, "..", "pcb", "output", "badge_full.step")
os.makedirs(OUT, exist_ok=True)

# Board numbers come from design.py so holes/slots cannot drift from the PCB.
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "pcb", "scripts")))
import design as D  # noqa: E402


def _xy(ref):
    p = next(p for p in D.PARTS if p.ref == ref)
    return (p.at[0], p.at[1])


# ----------------------------------------------------------------------------- inputs (from the PCB)
PCB_W, PCB_H, PCB_T = D.BOARD_W, D.BOARD_H, D.BOARD_THICKNESS
PANEL_W, PANEL_H, PANEL_T = D.BOARD_W, D.PANEL_H, D.PANEL_T
ACTIVE_W, ACTIVE_H = D.ACTIVE_W, D.ACTIVE_H
ACTIVE_TOP = D.ACTIVE_TOP                        # GDEM042F86 p.6: 6.7 mm from panel top to AA
USB_CUT_HALF = 4.675                            # TYPE-C-31-M-14 9.35 mm cutout, same as gen_pcb.py
USB_X0, USB_X1 = _xy("J3")[0] - USB_CUT_HALF, _xy("J3")[0] + USB_CUT_HALF
USB_Z0, USB_Z1 = -2.0, 1.25                     # connector body extent relative to PCB back face (mid-mount)
BUTTONS = [_xy("SW1"), _xy("SW2")]              # RST @ (14.0, 80.5), BOOT @ (22.5, 80.5)
LEDS = [_xy("D4"), _xy("D5")]                   # CHG / STAT
COMP_H = 2.4                                    # tallest part on the back: ESP32-C3-MINI-1
BATTERY = (*D.BATTERY_POCKET, 2.0)             # pocket x0,y0,x1,y1 (PCB coords), thickness
FPC_SLOT = D.FPC_SLOT                           # (27.0, 77.6, 57.0, 79.6)

# ----------------------------------------------------------------------------- enclosure parameters
CLR = 0.3            # PCB edge to inner wall
WALL = 1.2
BEZEL_T = 1.0        # front plate thickness over the panel
STRIP_RELIEF = 0.4   # extra pocket in the bezel underside over the strip (USB body pokes up 0.25 above the panel plane... plus margin)
BACK_CLR = 0.3       # tallest component to back-cover inner face
COVER_T = 0.8
CORNER_R = 3.0
TOP_BAR = 6.0        # solid bar above the PCB cavity for the lanyard slot
LANYARD_SLOT = (16.0, 2.6)
WINDOW_TOL = 0.3
COVER_TOL = 0.15     # cover plate to cavity, per side
TONGUE = 0.35        # snap tongue on the two long cover edges
GROOVE_Z = None      # computed
RIB_W = 1.4

# derived Z levels (PCB back face = 0)
Z_PANEL_TOP = PCB_T + PANEL_T                   # 1.8
Z_FRONT = Z_PANEL_TOP + BEZEL_T                 # 2.8
Z_COVER_IN = -(COMP_H + BACK_CLR)               # -2.7
Z_BACK = Z_COVER_IN - COVER_T                   # -3.5
TOTAL_T = Z_FRONT - Z_BACK

# cavity (inner) and outer box, in badge frame
IX0, IX1 = -CLR, PCB_W + CLR
IY0, IY1 = -(PCB_H + CLR), CLR
OX0, OX1 = IX0 - WALL, IX1 + WALL
OY0, OY1 = IY0 - WALL, IY1 + WALL + TOP_BAR


def V(x, y, z):
    return App.Vector(x, y, z)


def box(x0, y0, z0, x1, y1, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def fillet_vertical(shape, r):
    edges = [e for e in shape.Edges
             if abs(e.Vertexes[0].X - e.Vertexes[1].X) < 1e-6 and abs(e.Vertexes[0].Y - e.Vertexes[1].Y) < 1e-6]
    return shape.makeFillet(r, edges)


def rrect(x0, y0, z0, x1, y1, z1, r):
    return fillet_vertical(box(x0, y0, z0, x1, y1, z1), r)


def cyl(x, y, z0, z1, d):
    return Part.makeCylinder(d / 2, z1 - z0, V(x, y, z0))


def py(y_pcb):
    """PCB y (down) -> badge Y (up)."""
    return -y_pcb


# ============================================================================= front frame
def front_frame():
    body = rrect(OX0, OY0, Z_BACK, OX1, OY1, Z_FRONT, CORNER_R)
    # main cavity: from the back all the way up to the bezel underside
    body = body.cut(box(IX0, IY0, Z_BACK - 1, IX1, IY1, Z_PANEL_TOP))
    # display window
    wx0 = (PANEL_W - ACTIVE_W) / 2 - WINDOW_TOL
    wx1 = wx0 + ACTIVE_W + 2 * WINDOW_TOL
    wy1 = py(ACTIVE_TOP) + WINDOW_TOL
    wy0 = wy1 - ACTIVE_H - 2 * WINDOW_TOL
    body = body.cut(box(wx0, wy0, Z_PANEL_TOP - 1, wx1, wy1, Z_FRONT + 1))
    # relief pocket in the bezel underside over the strip (no panel there, USB body sticks up)
    body = body.cut(box(IX0, IY0 - 1, Z_PANEL_TOP - 0.01, IX1, py(PANEL_H) - 0.5, Z_PANEL_TOP + STRIP_RELIEF))
    # USB-C opening through the bottom wall
    body = body.cut(box(USB_X0 - 0.5, OY0 - 1, USB_Z0 - 0.4, USB_X1 + 0.5, IY0 + 0.5, USB_Z1 + 0.3))
    # lanyard slot in the top bar
    lw, lh = LANYARD_SLOT
    cx = (OX0 + OX1) / 2
    ly = OY1 - WALL - lh / 2 - 1.2
    slot = box(cx - lw / 2, ly - lh / 2, Z_BACK - 1, cx + lw / 2, ly + lh / 2, Z_FRONT + 1)
    slot = fillet_vertical(slot, lh / 2 * 0.98)
    body = body.cut(slot)
    # snap grooves on the two long walls (top & bottom of the cavity) for the cover tongue
    gz0, gz1 = Z_BACK + 0.3, Z_BACK + 0.3 + COVER_T + 0.1
    body = body.cut(box(IX0 + 4, IY1 - 0.01, gz0, IX1 - 4, IY1 + TONGUE, gz1))
    body = body.cut(box(IX0 + 4, IY0 - TONGUE, gz0, IX1 - 4, IY0 + 0.01, gz1))
    # tiny pry notch on the bottom wall outer face
    body = body.cut(box(cx - 4, OY0 - 1, Z_BACK - 1, cx + 4, OY0 + 0.6, Z_BACK + 0.6))
    return body


# ============================================================================= back cover
def back_cover():
    x0, x1 = IX0 + COVER_TOL, IX1 - COVER_TOL
    y0, y1 = IY0 + COVER_TOL, IY1 - COVER_TOL
    plate = box(x0, y0, Z_BACK, x1, y1, Z_COVER_IN)
    # snap tongues on the long edges (they engage the grooves in front_frame)
    tz0, tz1 = Z_BACK + 0.35, Z_BACK + 0.35 + COVER_T
    plate = plate.fuse(box(IX0 + 4.5, y1 - 0.01, tz0, IX1 - 4.5, IY1 + TONGUE - 0.05, tz1))
    plate = plate.fuse(box(IX0 + 4.5, IY0 - TONGUE + 0.05, tz0, IX1 - 4.5, y0 + 0.01, tz1))
    # ribs that press the PCB against the panel/bezel (component-free zones only)
    rib_top = Z_COVER_IN + (COMP_H + BACK_CLR)       # = 0 = PCB back face
    plate = plate.fuse(box(0.3, py(84.0) + 0.3, Z_COVER_IN - 0.01, 0.3 + RIB_W, py(0.3), rib_top))          # left edge
    plate = plate.fuse(box(PCB_W - 0.3 - RIB_W, py(76.0), Z_COVER_IN - 0.01, PCB_W - 0.3, py(0.3), rib_top))  # right edge (stops above C1/D4)
    plate = plate.fuse(box(3.0, py(2.2), Z_COVER_IN - 0.01, 52.0, py(0.3), rib_top))                          # top edge (battery/coil start at y=3)
    for (bx, by) in [(5.0, 82.5), (33.0, 82.5), (61.0, 82.5)]:
        plate = plate.fuse(cyl(bx, py(by), Z_COVER_IN - 0.01, rib_top, 2.4))
    # button holes and LED light pipes
    for (bx, by) in BUTTONS:
        plate = plate.cut(cyl(bx, py(by), Z_BACK - 1, Z_COVER_IN + 1, 2.8))
    for (lx, ly) in LEDS:
        plate = plate.cut(cyl(lx, py(ly), Z_BACK - 1, Z_COVER_IN + 1, 1.2))
    return plate


# ============================================================================= reference bodies
def panel_body():
    return box(0, py(PANEL_H), PCB_T, PANEL_W, 0, PCB_T + PANEL_T)


def pcb_body():
    b = rrect(0, py(PCB_H), 0, PCB_W, 0, PCB_T, 2.0)
    b = b.cut(box(USB_X0, py(PCB_H) - 1, -1, USB_X1, py(PCB_H - 6.05), 2))
    sx0, sy0, sx1, sy1 = FPC_SLOT
    b = b.cut(box(sx0, py(sy1), -1, sx1, py(sy0), 2))
    return b


def battery_body():
    x0, y0, x1, y1, t = BATTERY
    return box(x0 + 1, py(y1) + 1, -t, x1 - 1, py(y0) - 1, 0)


def esp_body():
    return box(53.2, py(65.5), -COMP_H, 66.8, py(48.5), 0)


def usb_body():
    return box(USB_X0 + 0.2, py(PCB_H) - 1.2, USB_Z0, USB_X1 - 0.2, py(PCB_H - 7.35), USB_Z1)


def load_pcb_step():
    if os.path.exists(PCB_STEP):
        s = Part.Shape()
        s.read(PCB_STEP)
        return s
    return None


# ============================================================================= build documents
def add(doc, shape, name, color=None):
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    if color and hasattr(obj, "ViewObject") and obj.ViewObject:
        obj.ViewObject.ShapeColor = color
    return obj


def main():
    frame = front_frame()
    cover = back_cover()
    print(f"enclosure: outer {OX1-OX0:.1f} x {OY1-OY0:.1f} x {TOTAL_T:.1f} mm  (front face Z={Z_FRONT}, back Z={Z_BACK})")
    print(f"frame volume {frame.Volume/1000:.2f} cm3, cover volume {cover.Volume/1000:.2f} cm3, valid={frame.isValid() and cover.isValid()}")

    # individual parts
    for name, shp in [("badge_front_frame", frame), ("badge_back_cover", cover)]:
        d = App.newDocument(name)
        add(d, shp, name)
        d.saveAs(os.path.join(OUT, name + ".FCStd"))
        shp.exportStep(os.path.join(OUT, name + ".step"))
        shp.exportStl(os.path.join(OUT, name + ".stl"))
        App.closeDocument(d.Name)

    # assembly
    d = App.newDocument("badge_assembly")
    add(d, frame, "FrontFrame", (0.20, 0.22, 0.25))
    add(d, cover, "BackCover", (0.20, 0.22, 0.25))
    add(d, panel_body(), "EPaperPanel_4p2", (0.92, 0.92, 0.88))
    pcb = load_pcb_step()
    if pcb is not None:
        add(d, pcb, "PCB_from_KiCad", (0.1, 0.45, 0.2))
    else:
        add(d, pcb_body(), "PCB_placeholder", (0.1, 0.45, 0.2))
        add(d, esp_body(), "ESP32_C3_MINI_1", (0.85, 0.85, 0.85))
        add(d, usb_body(), "USB_C_midmount", (0.6, 0.6, 0.6))
    add(d, battery_body(), "LiPo_2mm", (0.75, 0.75, 0.8))
    d.recompute()
    d.saveAs(os.path.join(OUT, "badge_assembly.FCStd"))
    Part.makeCompound([o.Shape for o in d.Objects]).exportStep(os.path.join(OUT, "badge_assembly.step"))

    # interference checks (common shapes should be empty)
    checks = {
        "frame vs panel": frame.common(panel_body()).Volume,
        "frame vs battery": frame.common(battery_body()).Volume,
        "frame vs usb": frame.common(usb_body()).Volume,
        "cover vs battery": cover.common(battery_body()).Volume,
        "cover vs esp": cover.common(esp_body()).Volume,
        "cover vs usb": cover.common(usb_body()).Volume,
        "frame vs cover": frame.common(cover).Volume,
    }
    if pcb is not None:
        checks["frame vs PCB(step)"] = frame.common(pcb).Volume
        checks["cover vs PCB(step)"] = cover.common(pcb).Volume
    for k, v in checks.items():
        print(f"  interference {k:22s}: {v:8.3f} mm3 {'OK' if v < 0.05 else '<-- CHECK'}")
    App.closeDocument(d.Name)


main()
