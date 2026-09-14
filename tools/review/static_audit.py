"""Portable static audit: source syntax, firmware pin parity, BOM/ZIP and binary hashes."""
import argparse
import ast
import csv
import hashlib
import importlib
import json
from pathlib import Path
import re
import sys
import zipfile


def sexpr(text):
    stack, root = [], None
    for token in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text):
        if token == '(':
            node = []
            if stack:
                stack[-1].append(node)
            stack.append(node)
        elif token == ')':
            root = stack.pop()
        else:
            stack[-1].append(json.loads(token) if token.startswith('"') else token)
    return root


def walk(node):
    if isinstance(node, list):
        yield node
        for child in node:
            yield from walk(child)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


p = argparse.ArgumentParser()
p.add_argument('--root', default=str(Path(__file__).resolve().parents[2]))
p.add_argument('--out', required=True)
p.add_argument('--build')
a = p.parse_args()
root = Path(a.root).resolve()
sys.path.insert(0, str(root / 'hardware/pcb/scripts'))
D = importlib.import_module('design')
syntax = []
for path in sorted((root / 'hardware').rglob('*.py')):
    ast.parse(path.read_text(encoding='utf-8'))
    syntax.append(path.relative_to(root).as_posix())
lib = sexpr((root / 'hardware/pcb/lib/Espressif.kicad_sym').read_text(encoding='utf-8'))
symbol = next(n for n in lib if isinstance(n, list) and n[:2] == ['symbol', 'ESP32-C3-MINI-1'])
pin_names = {}
for n in walk(symbol):
    if n and n[0] == 'pin':
        props = {v[0]: v[1] for v in n if isinstance(v, list) and len(v) >= 2}
        if 'name' in props and 'number' in props:
            pin_names[props['number']] = props['name']
u1 = next(p for p in D.PARTS if p.ref == 'U1')
gpio_map = {net: int(re.search(r'(?:IO|GPIO)(\d+)(?:/|$)', pin_names[pin]).group(1)) for pin, net in u1.pins.items() if re.search(r'(?:IO|GPIO)(\d+)(?:/|$)', pin_names.get(pin, ''))}
header = (root / 'firmware/include/pins.h').read_text()
fw = {name: int(num) for name, num in re.findall(r'constexpr int\s+(\w+)\s*=\s*(\d+)', header)}
pin_errors = {n: [v, gpio_map.get(n)] for n, v in fw.items() if gpio_map.get(n) != v}
out = root / 'hardware/pcb/output'
bom = list(csv.DictReader((out / 'badge_bom.csv').open(encoding='utf-8-sig')))
pos = list(csv.DictReader((out / 'badge_pos_back.csv').open(encoding='utf-8-sig')))
with zipfile.ZipFile(out / 'badge_gerbers.zip') as z:
    names = {n for n in z.namelist() if not n.endswith('/')}
    actual = {f.name for f in (out / 'gerbers').iterdir() if f.is_file()}
    diff = [n for n in sorted(names & actual) if z.read(n) != (out / 'gerbers' / n).read_bytes()]
    archive = {'members': sorted(names), 'stale_members': sorted(names - actual), 'missing_members': sorted(actual - names), 'content_differences': diff}
bins = {f.name: {'bytes': f.stat().st_size, 'sha256': sha(f)} for f in (root / 'firmware/output').glob('*.bin')}
build = {f.name: {'bytes': f.stat().st_size, 'sha256': sha(f)} for f in Path(a.build).glob('*.bin')} if a.build else {}
results = {'syntax_pass': syntax, 'design_parts': len(D.PARTS), 'design_nets': len(D.all_nets()),
           'firmware_pins': fw, 'symbol_derived_gpio_nets': gpio_map, 'pin_mismatches': pin_errors,
           'bom': {'rows': len(bom), 'blank_lcsc': sum(not row.get('LCSC') for row in bom), 'entries': bom},
           'positions': pos, 'archive': archive, 'committed_firmware': bins, 'clean_build': build,
           'dnp_parts': [p.ref for p in D.PARTS if p.dnp],
           'limits': 'Pin equality is not electrical function. Archive equality is not proof of current PCB provenance. Binary hash differences may include build metadata.'}
Path(a.out).write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps({k: results[k] for k in ['design_parts', 'design_nets', 'pin_mismatches', 'archive', 'committed_firmware', 'clean_build']}, indent=2))
raise SystemExit(bool(pin_errors))
