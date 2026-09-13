"""Generate hardware/pcb/badge.kicad_pcb from design.py using the pcbnew Python API.

Steps: board setup -> nets -> footprints (all on B.Cu) -> outline/slot -> NFC spiral
antenna note -> rule areas -> GND pours -> zone fill. Routing lives in route_pcb.py.
Run:  python3 gen_pcb.py   (then route_pcb.py for autorouting + GND stitching)
"""
import math
import os
import sys

import pcbnew
from pcbnew import VECTOR2I, FromMM

sys.path.insert(0, os.path.dirname(__file__))
import design as D

HERE = os.path.dirname(os.path.abspath(__file__))
PCB_DIR = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(PCB_DIR, "badge.kicad_pcb")
OUT_DIR = os.path.join(PCB_DIR, "output")


def P(x, y):
    return VECTOR2I(FromMM(x), FromMM(y))


def fp_lib_path(nick):
    if nick == "badge":
        return os.path.join(PCB_DIR, D.PROJECT_FP, "badge.pretty")
    return os.path.join(D.KICAD_FP, nick + ".pretty")


class Gen:
    def __init__(self):
        self.board = pcbnew.BOARD()
        self.nets = {}
        self.fps = {}
        ds = self.board.GetDesignSettings()
        ds.SetBoardThickness(FromMM(D.BOARD_THICKNESS))
        ds.m_CopperEdgeClearance = FromMM(0.1)   # mid-mount USB-C shell stakes sit right beside the cutout
        ds.m_MinClearance = FromMM(0.15)
        ds.m_TrackMinWidth = FromMM(0.15)
        ds.m_ViasMinSize = FromMM(0.5)
        ds.m_MinThroughDrill = FromMM(0.3)
        ds.m_HoleClearance = FromMM(0.25)

    # ------------------------------------------------------------------ nets
    def net(self, name):
        if name not in self.nets:
            ni = pcbnew.NETINFO_ITEM(self.board, name)
            self.board.Add(ni)
            self.nets[name] = ni
        return self.nets[name]

    # ------------------------------------------------------------ footprints
    def place_parts(self):
        overflow_x = 2.0
        for part in D.PARTS:
            lib, name = part.footprint.split(":")
            fp = pcbnew.FootprintLoad(fp_lib_path(lib), name)
            if fp is None:
                raise RuntimeError(f"footprint not found: {part.footprint}")
            fp.SetReference(part.ref)
            fp.SetValue(part.value)
            self.board.Add(fp)
            if part.at is None:
                x, y, rot = overflow_x, -8.0, 0
                overflow_x += 6
            else:
                x, y, rot = part.at
            fp.SetPosition(P(x, y))
            # Everything lives on the back. KiCad implements a left/right flip as "mirror Y +
            # rotate 180", so the footprint ends up with orientation 180; add the requested
            # rotation on top instead of overwriting it (overwriting would turn the flip into a
            # top/bottom mirror).
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
            fp.SetOrientationDegrees(fp.GetOrientationDegrees() + rot)
            if part.dnp:
                fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_DNP | pcbnew.FP_EXCLUDE_FROM_BOM)
            for pad in fp.Pads():
                net = part.pins.get(pad.GetNumber())
                if net:
                    pad.SetNet(self.net(net))
            # keep reference text small and on B.SilkS
            ref = fp.Reference()
            ref.SetTextSize(VECTOR2I(FromMM(0.6), FromMM(0.6)))
            ref.SetTextThickness(FromMM(0.1))
            fp.Value().SetVisible(False)
            self.fps[part.ref] = fp

    # --------------------------------------------------------------- outline
    def shape(self, layer, width=0.1):
        s = pcbnew.PCB_SHAPE(self.board)
        s.SetLayer(layer)
        s.SetWidth(FromMM(width))
        self.board.Add(s)
        return s

    def line(self, x1, y1, x2, y2, layer=pcbnew.Edge_Cuts, width=0.1):
        s = self.shape(layer, width)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(P(x1, y1))
        s.SetEnd(P(x2, y2))
        return s

    def arc(self, sx, sy, mx, my, ex, ey, layer=pcbnew.Edge_Cuts, width=0.1):
        s = self.shape(layer, width)
        s.SetShape(pcbnew.SHAPE_T_ARC)
        s.SetArcGeometry(P(sx, sy), P(mx, my), P(ex, ey))
        return s

    def rounded_rect(self, x0, y0, x1, y1, r, layer=pcbnew.Edge_Cuts, width=0.1):
        k = r * (1 - math.sqrt(0.5))
        self.line(x0 + r, y0, x1 - r, y0, layer, width)
        self.line(x1, y0 + r, x1, y1 - r, layer, width)
        self.line(x1 - r, y1, x0 + r, y1, layer, width)
        self.line(x0, y1 - r, x0, y0 + r, layer, width)
        self.arc(x1 - r, y0, x1 - k, y0 + k, x1, y0 + r, layer, width)
        self.arc(x1, y1 - r, x1 - k, y1 - k, x1 - r, y1, layer, width)
        self.arc(x0 + r, y1, x0 + k, y1 - k, x0, y1 - r, layer, width)
        self.arc(x0, y0 + r, x0 + k, y0 + k, x0 + r, y0, layer, width)

    def outline(self):
        W, H, r = D.BOARD_W, D.BOARD_H, D.BOARD_CORNER_R
        k = r * (1 - math.sqrt(0.5))
        # notch for the mid-mount USB-C (TYPE-C-31-M-14: 9.35 x 6.05 mm cutout open to the edge)
        j3 = self.fps["J3"]
        ux, uy = pcbnew.ToMM(j3.GetPosition().x), pcbnew.ToMM(j3.GetPosition().y)
        nx0, nx1, ny = ux - 4.675, ux + 4.675, uy - 3.35
        self.line(r, 0, W - r, 0)
        self.line(W, r, W, H - r)
        self.line(W - r, H, nx1, H)
        self.line(nx1, H, nx1, ny)
        self.line(nx1, ny, nx0, ny)
        self.line(nx0, ny, nx0, H)
        self.line(nx0, H, r, H)
        self.line(0, H - r, 0, r)
        self.arc(W - r, 0, W - k, k, W, r)
        self.arc(W, H - r, W - k, H - k, W - r, H)
        self.arc(r, H, k, H - k, 0, H - r)
        self.arc(0, r, k, k, r, 0)
        # FPC slot: two lines + two semicircles
        x0, y0, x1, y1 = D.FPC_SLOT
        rs = (y1 - y0) / 2
        cy = (y0 + y1) / 2
        self.line(x0 + rs, y0, x1 - rs, y0)
        self.line(x1 - rs, y1, x0 + rs, y1)
        self.arc(x1 - rs, y0, x1, cy, x1 - rs, y1)
        self.arc(x0 + rs, y1, x0, cy, x0 + rs, y0)

    def text(self, txt, x, y, layer=pcbnew.B_SilkS, size=1.0, thick=0.15, mirrored=None, angle=0):
        t = pcbnew.PCB_TEXT(self.board)
        t.SetText(txt)
        t.SetPosition(P(x, y))
        t.SetLayer(layer)
        t.SetTextSize(VECTOR2I(FromMM(size), FromMM(size)))
        t.SetTextThickness(FromMM(thick))
        t.SetTextAngleDegrees(angle)
        if mirrored is None:
            mirrored = layer in (pcbnew.B_SilkS, pcbnew.B_Cu, pcbnew.B_Fab)
        t.SetMirrored(mirrored)
        self.board.Add(t)
        return t

    def silkscreen(self):
        bx0, by0, bx1, by1 = D.BATTERY_POCKET
        for (a, b, c, d) in [(bx0, by0, bx1, by0), (bx1, by0, bx1, by1), (bx1, by1, bx0, by1), (bx0, by1, bx0, by0)]:
            self.line(a, b, c, d, pcbnew.B_SilkS, 0.15)
        self.text("LiPo <=2.0mm  150-300mAh  (PCM)", (bx0 + bx1) / 2, (by0 + by1) / 2, size=1.4, thick=0.2)
        cx0, cy0, cx1, cy1 = D.NFC_COIL_RECT
        self.text("NFC", (cx0 + cx1) / 2, (cy0 + cy1) / 2 - 2, size=3.0, thick=0.4)
        self.text("tap phone here (front)", (cx0 + cx1) / 2, (cy0 + cy1) / 2 + 2.5, size=1.0, thick=0.15)
        self.text("EPD 24P FPC  (panel on front side)", 43.0, 68.5, size=0.8, thick=0.12)
        self.text("ESP32-C3 antenna keepout", 60.0, 73.5, size=0.7, thick=0.1)
        self.text("BADGE-42C v0.1", 19.0, 71.0, size=1.2, thick=0.2)
        self.text("ESP32-C3 + ST25DV64KC + 4.2\" BWRY", 19.0, 73.2, size=0.8, thick=0.12)
        self.text("RST", 14.0, 77.9, size=0.8, thick=0.12)
        self.text("BOOT", 22.5, 77.9, size=0.8, thick=0.12)
        self.text("CHG", 86.5, 83.2, size=0.7, thick=0.1)
        self.text("STAT", 65.0, 83.2, size=0.7, thick=0.1)
        # front side marking for the panel & NFC tap area
        self.text("4.2\" BWRY e-paper glued here (91x77)", D.BOARD_W / 2, D.PANEL_H / 2, layer=pcbnew.F_SilkS, size=1.5, thick=0.2)

    # ------------------------------------------------------------ tracks/vias
    def track(self, x1, y1, x2, y2, net, layer=pcbnew.B_Cu, width=0.5, locked=True):
        t = pcbnew.PCB_TRACK(self.board)
        t.SetStart(P(x1, y1))
        t.SetEnd(P(x2, y2))
        t.SetWidth(FromMM(width))
        t.SetLayer(layer)
        t.SetNet(self.net(net))
        t.SetLocked(locked)
        self.board.Add(t)
        return t

    def via(self, x, y, net, locked=True):
        v = pcbnew.PCB_VIA(self.board)
        v.SetPosition(P(x, y))
        v.SetDrill(FromMM(0.3))
        v.SetWidth(FromMM(0.6))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(self.net(net))
        v.SetLocked(locked)
        self.board.Add(v)
        return v

    def pad_pos(self, ref, number):
        fp = self.fps[ref]
        for pad in fp.Pads():
            if pad.GetNumber() == number:
                p = pad.GetPosition()
                return pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
        raise KeyError((ref, number))

    def nfc_note(self):
        import gen_nfc_footprint as N
        L, d_in = N.inductance_uH()
        f0 = 1 / (2 * math.pi * math.sqrt(L * 1e-6 * 28.5e-12)) / 1e6
        print(f"NFC coil (footprint ANT1): L ~ {L:.2f} uH -> f0 ~ {f0:.2f} MHz with ST25DV 28.5 pF (target 13.56 MHz)")

    # ------------------------------------------------------------------ zones
    def rule_area(self, rect, layers, no_pour=True, no_footprints=False, no_tracks=False, no_vias=False, name=""):
        x0, y0, x1, y1 = rect
        z = pcbnew.ZONE(self.board)
        z.SetIsRuleArea(True)
        z.SetDoNotAllowCopperPour(no_pour)
        z.SetDoNotAllowFootprints(no_footprints)
        z.SetDoNotAllowTracks(no_tracks)
        z.SetDoNotAllowVias(no_vias)
        z.SetDoNotAllowPads(False)
        lset = pcbnew.LSET()
        for l in layers:
            lset.addLayer(l)
        z.SetLayerSet(lset)
        z.SetZoneName(name)
        ol = z.Outline()
        ol.NewOutline()
        for (x, y) in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]:
            ol.Append(FromMM(x), FromMM(y))
        self.board.Add(z)
        return z

    def gnd_pour(self, layer):
        z = pcbnew.ZONE(self.board)
        z.SetLayer(layer)
        z.SetNet(self.net("GND"))
        z.SetAssignedPriority(0)
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)   # solid: all parts are reflowed, avoids starved thermals
        z.SetLocalClearance(FromMM(0.25))
        z.SetMinThickness(FromMM(0.2))
        z.SetThermalReliefGap(FromMM(0.3))
        z.SetThermalReliefSpokeWidth(FromMM(0.4))
        z.SetZoneName(f"GND_{pcbnew.LayerName(layer)}")
        ol = z.Outline()
        ol.NewOutline()
        m = 0.5
        for (x, y) in [(m, m), (D.BOARD_W - m, m), (D.BOARD_W - m, D.BOARD_H - m), (m, D.BOARD_H - m)]:
            ol.Append(FromMM(x), FromMM(y))
        self.board.Add(z)
        return z

    def zones(self):
        cu = [pcbnew.F_Cu, pcbnew.B_Cu]
        x0, y0, x1, y1 = D.NFC_COIL_RECT
        self.rule_area((x0 - 1.0, y0 - 1.0, x1 + 1.0, y1 + 1.0), cu, no_pour=True, no_tracks=True, no_vias=True, name="NFC coil: no copper / no routing")
        self.rule_area(D.ESP_ANT_KEEPOUT, cu, no_pour=True, no_tracks=True, no_vias=True, name="ESP32-C3 antenna keepout")
        self.rule_area(D.BATTERY_POCKET, [pcbnew.B_Cu], no_pour=False, no_footprints=True, name="battery pocket: no parts")
        sx0, sy0, sx1, sy1 = D.FPC_SLOT
        self.rule_area((sx0 - 0.8, sy0 - 0.8, sx1 + 0.8, sy1 + 0.8), cu, no_pour=True, no_tracks=True, no_vias=True, name="FPC slot")
        self.gnd_pour(pcbnew.F_Cu)
        self.gnd_pour(pcbnew.B_Cu)

    def fill(self):
        # ZONE_FILLER segfaults on a board created in memory; round-trip through disk so the
        # board gets a proper project/connectivity context first.
        pcbnew.SaveBoard(OUT, self.board)
        self.board = pcbnew.LoadBoard(OUT)
        self.board.BuildConnectivity()
        filler = pcbnew.ZONE_FILLER(self.board)
        filler.Fill(self.board.Zones())

    def save(self):
        pcbnew.SaveBoard(OUT, self.board)
        print("wrote", OUT)

    def report(self):
        b = self.board
        n_tracks = sum(1 for t in b.GetTracks() if t.GetClass() == "PCB_TRACK")
        n_vias = sum(1 for t in b.GetTracks() if t.GetClass() == "PCB_VIA")
        print(f"{len(list(b.GetFootprints()))} footprints, {n_tracks} track segments, {n_vias} vias, {len(list(b.Zones()))} zones")
        # unrouted check via connectivity
        b.BuildConnectivity()
        conn = b.GetConnectivity()
        unrouted = conn.GetUnconnectedCount(True)
        print("unrouted connections:", unrouted)
        return unrouted


def main():
    g = Gen()
    for n in D.all_nets():
        g.net(n)
    g.place_parts()
    g.outline()
    g.silkscreen()
    g.nfc_note()
    g.zones()
    g.fill()
    g.save()
    g.report()


if __name__ == "__main__":
    main()
