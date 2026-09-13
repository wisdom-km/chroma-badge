"""Autoroute hardware/pcb/badge.kicad_pcb with Freerouting, then stitch isolated GND islands.

Run after gen_pcb.py:   python3 route_pcb.py [--skip-route]
Steps: DSN export -> Freerouting -> SES import -> zone fill -> DRC (kicad-cli, JSON) ->
add GND vias next to GND pads that are not tied to the ground pour -> repeat -> final DRC.
"""
import json
import math
import os
import subprocess
import sys
import time

import pcbnew
from pcbnew import VECTOR2I, FromMM

sys.path.insert(0, os.path.dirname(__file__))
import design as D

HERE = os.path.dirname(os.path.abspath(__file__))
PCB_DIR = os.path.abspath(os.path.join(HERE, ".."))
BOARD = os.path.join(PCB_DIR, "badge.kicad_pcb")
OUT_DIR = os.path.join(PCB_DIR, "output")
FREEROUTING_JAR = "/opt/freerouting/freerouting.jar"
JAVA = "/opt/freerouting/jre25/bin/java"


def P(x, y):
    return VECTOR2I(FromMM(x), FromMM(y))


def export_dsn(board):
    """Export the Specctra DSN with the GND pours removed, so Freerouting routes GND with
    tracks like any other net. Otherwise it treats the pour as a plane, routes nothing for GND
    and the dense B.Cu routing chops the pour into islands with unconnected pads."""
    dsn = os.path.join(OUT_DIR, "badge.dsn")
    pours = [z for z in board.Zones() if not z.GetIsRuleArea()]
    for z in pours:
        board.Remove(z)
    try:
        if not pcbnew.ExportSpecctraDSN(board, dsn):
            raise RuntimeError("DSN export failed")
    finally:
        for z in pours:
            board.Add(z)
    return dsn


def run_freerouting(board):
    ses = os.path.join(OUT_DIR, "badge.ses")
    if os.path.exists(ses):
        os.remove(ses)
    dsn = export_dsn(board)
    java = JAVA if os.path.exists(JAVA) else "java"
    # Freerouting 2.4 writes an empty .ses when given an absolute output path -> run inside OUT_DIR
    cmd = [java, "-jar", FREEROUTING_JAR, "-de", os.path.basename(dsn), "-do", os.path.basename(ses),
           "-mp", "100", "-mt", "1"]
    print("running (cwd=output):", " ".join(cmd), flush=True)
    # Output must go to a file, not a pipe: with piped stdout Freerouting exits before its
    # asynchronous session save completes and leaves an empty .ses behind.
    # ...and, empirically, only when launched through os.system(): with subprocess.run() the
    # JVM exits before the save thread writes anything (0-byte .ses), so we shell out here.
    log = os.path.join(OUT_DIR, "freerouting.log")
    import shlex
    os.system(f"cd {shlex.quote(OUT_DIR)} && {' '.join(shlex.quote(c) for c in cmd)} > {shlex.quote(log)} 2>&1")
    with open(log) as lf:
        lines = [l.rstrip() for l in lf if "nalytics" not in l and l.strip()]
    print("\n".join(lines[-6:]), flush=True)
    last = -1
    for _ in range(90):
        size = os.path.getsize(ses) if os.path.exists(ses) else 0
        if size > 0 and size == last:
            break
        last = size
        time.sleep(1)
    if not os.path.exists(ses) or os.path.getsize(ses) == 0:
        raise RuntimeError("Freerouting produced no .ses")
    if not pcbnew.ImportSpecctraSES(board, ses):
        raise RuntimeError("SES import failed")


def fill(board):
    board.BuildConnectivity()
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.BuildConnectivity()


def drc_json(path):
    rpt = os.path.join(OUT_DIR, "drc_tmp.json")
    subprocess.run(["kicad-cli", "pcb", "drc", "--severity-error", "--format", "json", "-o", rpt, path],
                   capture_output=True, text=True)
    with open(rpt) as f:
        return json.load(f)


def isolated_gnd_pads(report):
    """Return [(x, y)] of GND pads listed in 'unconnected_items' violations."""
    pads = []
    for v in report.get("unconnected_items", []):
        for it in v.get("items", []):
            d = it.get("description", "")
            if d.startswith("Pad") and "[GND]" in d:
                pads.append((it["pos"]["x"], it["pos"]["y"]))
    # de-duplicate
    return sorted(set(pads))


class Stitcher:
    def __init__(self, board):
        self.board = board
        self.gnd = board.FindNet("GND")

    def via_fits(self, x, y):
        if x < 1.2 or y < 1.2 or x > D.BOARD_W - 1.2 or y > D.BOARD_H - 1.2:
            return False
        for rect in (D.NFC_COIL_RECT, D.ESP_ANT_KEEPOUT, D.FPC_SLOT):
            if rect[0] - 1.0 <= x <= rect[2] + 1.0 and rect[1] - 1.0 <= y <= rect[3] + 1.0:
                return False
        p = P(x, y)
        r_via = FromMM(0.3)
        clr = FromMM(0.2)
        for fp in self.board.GetFootprints():
            for pad in fp.Pads():
                same = pad.GetNetCode() == self.gnd.GetNetCode()
                bb = pad.GetBoundingBox()
                half = max(bb.GetWidth(), bb.GetHeight()) // 2
                if (pad.GetPosition() - p).EuclideanNorm() < r_via + half + (FromMM(0.05) if same else clr):
                    return False
        circle = pcbnew.SHAPE_CIRCLE(p, r_via)
        for t in self.board.GetTracks():
            same = t.GetNetCode() == self.gnd.GetNetCode()
            if t.GetClass() == "PCB_VIA":
                if (t.GetPosition() - p).EuclideanNorm() < FromMM(0.6) + (FromMM(0.05) if same else clr):
                    return False
            else:
                seg = pcbnew.SHAPE_SEGMENT(t.GetStart(), t.GetEnd(), t.GetWidth())
                if seg.Collide(circle, FromMM(0.05) if same else clr):
                    return False
        return True

    def add_via(self, x, y):
        v = pcbnew.PCB_VIA(self.board)
        v.SetPosition(P(x, y))
        v.SetDrill(FromMM(0.3))
        v.SetWidth(FromMM(0.6))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(self.gnd)
        self.board.Add(v)

    def add_track(self, x1, y1, x2, y2, w=0.3):
        t = pcbnew.PCB_TRACK(self.board)
        t.SetStart(P(x1, y1))
        t.SetEnd(P(x2, y2))
        t.SetWidth(FromMM(w))
        t.SetLayer(pcbnew.B_Cu)
        t.SetNet(self.gnd)
        self.board.Add(t)

    def stitch(self, pads):
        added = 0
        for (px, py) in pads:
            done = False
            for radius in (1.0, 1.3, 1.7, 2.2, 2.8):
                for k in range(16):
                    ang = k * math.pi / 8
                    x, y = px + radius * math.cos(ang), py + radius * math.sin(ang)
                    if self.via_fits(x, y):
                        self.add_via(x, y)
                        self.add_track(px, py, x, y)
                        added += 1
                        done = True
                        break
                if done:
                    break
            if not done:
                print(f"    could not place a stitching via near GND pad at ({px:.2f}, {py:.2f})")
        return added


class Fixups:
    """Repair the small connectivity gaps the Freerouting -> SES -> KiCad round trip leaves behind."""

    def __init__(self, board, stitcher):
        self.board = board
        self.st = stitcher

    def item(self, uuid):
        it = self.board.GetItem(pcbnew.KIID(uuid))
        if it is None or it.GetClass() == "DELETED_BOARD_ITEM":
            return None
        return it.Cast()

    def join_duplicate_pads(self):
        """Pads sharing a number inside one footprint (tactile switches) are internally
        connected in the part; give KiCad a copper link so connectivity agrees."""
        n = 0
        for fp in self.board.GetFootprints():
            # only tactile switches need this; ANT1 is handled by its custom pad, J3's shield
            # pads are tied together by the GND pour
            if not fp.GetReference().startswith("SW"):
                continue
            groups = {}
            for pad in fp.Pads():
                if pad.GetNetCode() > 0:
                    groups.setdefault(pad.GetNumber(), []).append(pad)
            for num, pads in groups.items():
                for a, b in zip(pads, pads[1:]):
                    t = pcbnew.PCB_TRACK(self.board)
                    t.SetStart(a.GetPosition())
                    t.SetEnd(b.GetPosition())
                    t.SetWidth(FromMM(0.4))
                    t.SetLayer(pcbnew.B_Cu)
                    t.SetNet(a.GetNet())
                    self.board.Add(t)
                    n += 1
        return n

    def repair(self, report):
        """Extend dangling track ends into their pad / add a via where a B.Cu track meets an F.Cu track."""
        fixed = 0
        for v in report.get("unconnected_items", []):
            items = v.get("items", [])
            if len(items) != 2:
                continue
            objs = [self.item(it["uuid"]) for it in items]
            descs = [it.get("description", "") for it in items]
            if any(o is None for o in objs):
                continue
            kinds = [o.GetClass() for o in objs]
            if "PCB_TRACK" in kinds and "PAD" in kinds:
                tr = objs[kinds.index("PCB_TRACK")]
                pad = objs[kinds.index("PAD")]
                pp = pad.GetPosition()
                d_start = (tr.GetStart() - pp).EuclideanNorm()
                d_end = (tr.GetEnd() - pp).EuclideanNorm()
                if min(d_start, d_end) < FromMM(3.0):
                    if d_start < d_end:
                        tr.SetStart(pp)
                    else:
                        tr.SetEnd(pp)
                    fixed += 1
            elif kinds == ["PCB_TRACK", "PCB_TRACK"] and objs[0].GetLayer() != objs[1].GetLayer():
                best = None
                for pa in (objs[0].GetStart(), objs[0].GetEnd()):
                    for pb in (objs[1].GetStart(), objs[1].GetEnd()):
                        d = (pa - pb).EuclideanNorm()
                        if best is None or d < best[0]:
                            best = (d, pa)
                if best and best[0] < FromMM(0.6):
                    x, y = pcbnew.ToMM(best[1].x), pcbnew.ToMM(best[1].y)
                    via = pcbnew.PCB_VIA(self.board)
                    via.SetPosition(best[1])
                    via.SetDrill(FromMM(0.3))
                    via.SetWidth(FromMM(0.6))
                    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                    via.SetNet(objs[0].GetNet())
                    self.board.Add(via)
                    fixed += 1
        return fixed


def pad_pad_unrouted(report):
    n = 0
    for v in report.get("unconnected_items", []):
        descs = [it.get("description", "") for it in v.get("items", [])]
        if len(descs) == 2 and all(d.startswith("Pad") for d in descs) and not any("[GND]" in d for d in descs):
            n += 1
    return n


def summarize(report):
    counts = {}
    for k in ("violations", "unconnected_items", "schematic_parity"):
        for viol in report.get(k, []):
            t = viol.get("type", k)
            counts[t] = counts.get(t, 0) + 1
    return counts


def unconnected_pairs(report):
    """Human-readable list of unconnected item pairs that are NOT GND-pour related."""
    out = []
    for v in report.get("unconnected_items", []):
        descs = [it.get("description", "") for it in v.get("items", [])]
        if not any("[GND]" in d for d in descs):
            out.append(" <-> ".join(descs))
    return out


def main():
    board = pcbnew.LoadBoard(BOARD)
    if "--export-dsn" in sys.argv:
        print("wrote", export_dsn(board))
        return 0
    for z in board.Zones():
        if not z.GetIsRuleArea():
            z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    st = Stitcher(board)
    fx = Fixups(board, st)
    print("joined duplicate pads with", fx.join_duplicate_pads(), "tracks", flush=True)
    # --import-only: a badge.ses already exists in output/ (e.g. Freerouting was run by hand
    #                from a shell, see README) -> import it and do the fix-up/stitching passes.
    # --skip-route:  do not touch routing at all, only fix-ups + GND stitching on the saved board.
    import_only = "--import-only" in sys.argv
    rounds = 0 if "--skip-route" in sys.argv else (1 if import_only else 2)
    for rnd in range(rounds):
        if import_only:
            ses = os.path.join(OUT_DIR, "badge.ses")
            if not pcbnew.ImportSpecctraSES(board, ses):
                raise RuntimeError("SES import failed")
        else:
            run_freerouting(board)
        fill(board)
        pcbnew.SaveBoard(BOARD, board)
        rep = drc_json(BOARD)
        n = fx.repair(rep)
        print(f"routing round {rnd}: repaired {n} gaps; DRC: {summarize(rep)}", flush=True)
        fill(board)
        pcbnew.SaveBoard(BOARD, board)
        rep = drc_json(BOARD)
        if pad_pad_unrouted(rep) == 0:
            break
        print(f"   {pad_pad_unrouted(rep)} pad-to-pad connections still unrouted -> another Freerouting round", flush=True)
    fill(board)
    pcbnew.SaveBoard(BOARD, board)
    if rounds == 0:
        rep = drc_json(BOARD)
        print("repaired", fx.repair(rep), "gaps")
        fill(board)
        pcbnew.SaveBoard(BOARD, board)

    for it in range(8):
        rep = drc_json(BOARD)
        pads = isolated_gnd_pads(rep)
        print(f"GND stitching pass {it}: {len(pads)} isolated GND pads; DRC: {summarize(rep)}", flush=True)
        if not pads:
            break
        n = st.stitch(pads)
        print(f"    added {n} vias", flush=True)
        if n == 0:
            break
        fill(board)
        pcbnew.SaveBoard(BOARD, board)

    rep = drc_json(BOARD)
    counts = summarize(rep)
    n_tracks = sum(1 for t in board.GetTracks() if t.GetClass() == "PCB_TRACK")
    n_vias = sum(1 for t in board.GetTracks() if t.GetClass() == "PCB_VIA")
    print(f"final: {n_tracks} track segments, {n_vias} vias; DRC (errors only): {counts or 'clean'}")
    for line in unconnected_pairs(rep):
        print("   unrouted:", line)
    with open(os.path.join(OUT_DIR, "drc_final.json"), "w") as f:
        json.dump(rep, f, indent=1)
    return 0 if not counts else 1


if __name__ == "__main__":
    sys.exit(main())
