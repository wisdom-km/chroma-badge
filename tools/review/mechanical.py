"""FreeCAD geometry audit, read-only source load (avoids enclosure module's main())."""
import argparse
import ast
import itertools
import json
from pathlib import Path
import sys
import FreeCAD as App
import Part

p = argparse.ArgumentParser()
p.add_argument('--snapshot', required=True)
p.add_argument('--out', required=True)
p.add_argument('--step')
a = p.parse_args()
root = Path(a.snapshot).resolve()
source = root / 'hardware/enclosure/badge_enclosure.py'
tree = ast.parse(source.read_text(encoding='utf-8'))
assert isinstance(tree.body[-1], ast.Expr) and isinstance(tree.body[-1].value, ast.Call) and tree.body[-1].value.func.id == 'main'
tree.body.pop()  # audit-only loading; repository source is not edited
namespace = {'__file__': str(source), '__name__': 'enclosure_audit'}
exec(compile(tree, str(source), 'exec'), namespace)
shapes = {name: namespace[fn]() for name, fn in [('frame', 'front_frame'), ('cover', 'back_cover'), ('panel', 'panel_body'), ('battery_placeholder', 'battery_body')]}
step = Path(a.step) if a.step else root / 'hardware/pcb/output/badge_full.step'
board = Part.Shape()
board.read(str(step))
shapes['pcb_step'] = board

def stats(s):
    b = s.BoundBox
    return {'valid': s.isValid(), 'null': s.isNull(), 'solids': len(s.Solids), 'volume_mm3': s.Volume,
            'bounds_mm': [b.XMin, b.YMin, b.ZMin, b.XMax, b.YMax, b.ZMax]}

overlaps = []
for (n1, s1), (n2, s2) in itertools.combinations(shapes.items(), 2):
    v = s1.common(s2).Volume
    overlaps.append({'a': n1, 'b': n2, 'volume_mm3': v, 'pass_0_05_mm3': v < 0.05})
saved = {}
for name in ['badge_front_frame', 'badge_back_cover']:
    doc = App.openDocument(str(root / 'hardware/enclosure/output' / (name + '.FCStd')))
    saved[name] = [stats(o.Shape) for o in doc.Objects if hasattr(o, 'Shape')]
    App.closeDocument(doc.Name)
result = {'freecad': App.Version(), 'pcb_step': str(step), 'shapes': {n: stats(s) for n, s in shapes.items()},
          'overlaps': overlaps, 'saved_documents': saved,
          'limits': 'Battery placeholder only; no FPC flex, adhesive, wiring, connector motion or manufacturing tolerances. Missing models can make zero overlap misleading.'}
Path(a.out).write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
raise SystemExit(0 if all(x['pass_0_05_mm3'] for x in overlaps) and all(x.isValid() for x in shapes.values()) else 1)
