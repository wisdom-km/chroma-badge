"""Read-only pcbnew audit of connectivity assignments, dimensions and model coverage."""
import argparse
from collections import defaultdict
import importlib
import hashlib
import json
import os
from pathlib import Path
import sys
import pcbnew

p = argparse.ArgumentParser()
p.add_argument('--pcb', required=True)
p.add_argument('--out', required=True)
a = p.parse_args()
root = Path(a.pcb).resolve()
sys.path.insert(0, str(root / 'scripts'))
D = importlib.import_module('design')
b = pcbnew.LoadBoard(str(root / 'badge.kicad_pcb'))
fps = {f.GetReference(): f for f in b.GetFootprints()}
problems = []
models = []
for part in D.PARTS:
    fp = fps.get(part.ref)
    if fp is None:
        problems.append(f'missing footprint {part.ref}')
        continue
    pads = defaultdict(list)
    for pad in fp.Pads():
        pads[pad.GetNumber()].append(pad.GetNetname().lstrip('/'))
    for pin, net in part.pins.items():
        if not pads.get(pin) or any(n != net for n in pads[pin]):
            problems.append(f'{part.ref}.{pin}: expected {net}, actual {pads.get(pin)}')
    for pin in part.nc:
        if any(n and not n.startswith('unconnected') for n in pads[pin]):
            problems.append(f'NC connected: {part.ref}.{pin}')
    for m in fp.Models():
        name = m.m_Filename
        resolved = name.replace('${KIPRJMOD}', str(root))
        for key, value in os.environ.items():
            resolved = resolved.replace('${' + key + '}', value)
        target = Path(resolved)
        if not target.is_absolute():
            target = root / target
        exists = target.exists()
        step_substitute = any(target.with_suffix(ext).exists() for ext in ('.step', '.stp', '.STEP'))
        models.append({'ref': part.ref, 'model': name, 'exists': exists, 'step_substitute': step_substitute})
nets = defaultdict(lambda: {'segments': 0, 'vias': 0, 'length_mm': 0.0, 'widths_mm': set()})
route_records = []
for track in b.GetTracks():
    r = nets[track.GetNetname().lstrip('/')]
    if isinstance(track, pcbnew.PCB_VIA):
        r['vias'] += 1
        route_records.append(['via', track.GetNetname(), track.GetPosition().x, track.GetPosition().y, track.GetWidth(pcbnew.F_Cu), track.GetWidth(pcbnew.B_Cu), track.GetDrillValue()])
    else:
        r['segments'] += 1
        r['length_mm'] += pcbnew.ToMM(track.GetLength())
        r['widths_mm'].add(round(pcbnew.ToMM(track.GetWidth()), 6))
        route_records.append(['track', track.GetNetname(), track.GetLayer(), track.GetStart().x, track.GetStart().y, track.GetEnd().x, track.GetEnd().y, track.GetWidth()])
for r in nets.values():
    r['widths_mm'] = sorted(r['widths_mm'])
    r['length_mm'] = round(r['length_mm'], 6)
rect = b.GetBoardEdgesBoundingBox()
points = [pt for edge in b.GetDrawings() if edge.GetLayer() == pcbnew.Edge_Cuts for pt in [edge.GetStart(), edge.GetEnd()]]
data = {'kicad': pcbnew.Version(), 'footprints': len(fps),
        'segments': sum(x['segments'] for x in nets.values()), 'vias': sum(x['vias'] for x in nets.values()),
        'size_mm': [pcbnew.ToMM(max(pt.x for pt in points)-min(pt.x for pt in points)), pcbnew.ToMM(max(pt.y for pt in points)-min(pt.y for pt in points))],
        'edge_graphics_bbox_including_stroke_mm': [pcbnew.ToMM(rect.GetWidth()), pcbnew.ToMM(rect.GetHeight())],
        'size_method': 'Edge.Cuts endpoints extrema, valid for this board with straight sides and quarter-circle corners.',
        'routing_sha256': hashlib.sha256(json.dumps(sorted(route_records)).encode()).hexdigest(),
        'thickness_mm': pcbnew.ToMM(b.GetDesignSettings().GetBoardThickness()),
        'copper_layers': b.GetCopperLayerCount(), 'footprint_layers': sorted(set(f.GetLayerName() for f in fps.values())),
        'net_assignment_problems': problems, 'nets': dict(nets), 'models': models,
        'nfc_pads': [{'number': pad.GetNumber(), 'layers': pad.GetLayerSet().FmtBin(), 'mask_front': pad.IsOnLayer(pcbnew.F_Mask), 'mask_back': pad.IsOnLayer(pcbnew.B_Mask), 'copper_front': pad.IsOnLayer(pcbnew.F_Cu), 'copper_back': pad.IsOnLayer(pcbnew.B_Cu)} for pad in fps['ANT1'].Pads()],
        'design_net_classes': D.NET_CLASSES,
        'project_net_settings': json.loads((root / 'badge.kicad_pro').read_text())['net_settings']}
Path(a.out).write_text(json.dumps(data, indent=2), encoding='utf-8')
print(json.dumps({k: data[k] for k in ['footprints', 'segments', 'vias', 'size_mm', 'thickness_mm', 'net_assignment_problems']}))
raise SystemExit(bool(problems))
