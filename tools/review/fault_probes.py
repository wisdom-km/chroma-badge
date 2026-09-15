"""Reproduce unsafe export and stale DRC handling in isolated fixtures.

After F04/F19 the *new* expectation is fail-closed: injected DRC rc=5 must
not return an old empty report, and ERC/DRC failures must not reach Gerbers.
"""
import argparse
import ast
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import types

p = argparse.ArgumentParser()
p.add_argument('--out', required=True)
p.add_argument('--bash', required=True)
a = p.parse_args()
root = Path(__file__).resolve().parents[2]
out = Path(a.out).resolve()
out.mkdir(parents=True, exist_ok=True)
results = {}
# Extract only the production function. Do not import the mutating routing module.
tree = ast.parse((root / 'hardware/pcb/scripts/route_pcb.py').read_text(encoding='utf-8'))
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'drc_json')
stale = out / 'stale'
stale.mkdir(exist_ok=True)
(stale / 'drc_tmp.json').write_text('{"violations":[],"unconnected_items":[],"marker":"OLD_REPORT"}')
namespace = {
    'os': os, 'json': json, 'time': time, 'OUT_DIR': str(stale),
    'subprocess': types.SimpleNamespace(
        run=lambda *x, **y: subprocess.CompletedProcess(x, 5, '', 'injected failure')),
}
exec(compile(ast.Module(body=[fn], type_ignores=[]), 'route_pcb.py', 'exec'), namespace)
try:
    readback = namespace['drc_json']('unused.kicad_pcb')
    results['stale_drc'] = {
        'injected_returncode': 5, 'returned': readback,
        'failed_closed': False, 'error': None,
    }
except Exception as e:
    results['stale_drc'] = {
        'injected_returncode': 5, 'returned': None,
        'failed_closed': True, 'error_type': type(e).__name__, 'error': str(e),
    }

for failed_stage in ['erc', 'drc']:
    fixture = out / ('export-' + failed_stage)
    (fixture / 'scripts').mkdir(parents=True, exist_ok=True)
    (fixture / 'fake').mkdir(exist_ok=True)
    shutil.copy2(root / 'hardware/pcb/scripts/export.sh', fixture / 'scripts/export.sh')
    for helper in (
        'check_kicad_report.py', 'check_netlist.py', 'classify_bom.py',
        'check_3d_models.py', 'zip_dir.py', 'write_candidate_manifest.py',
    ):
        src = root / 'hardware/pcb/scripts' / helper
        if src.exists():
            shutil.copy2(src, fixture / 'scripts' / helper)
    fake = '''#!/usr/bin/env bash
echo "$*" >> "$AUDIT_TRACE"
if [[ "$1 $2" == "sch erc" || "$1 $2" == "pcb drc" ]]; then
  stage="$2"
  while [[ $# -gt 0 ]]; do
    if [[ "$1" == "-o" ]]; then shift; mkdir -p "$(dirname "$1")"; echo "Found 1 violation" > "$1"; fi
    shift
  done
  [[ "$stage" == "$AUDIT_FAIL" ]] && exit 5
  exit 0
fi
if [[ "$1 $2 $3" == "pcb export gerbers" ]]; then exit 99; fi
exit 0
'''
    (fixture / 'fake/kicad-cli').write_text(fake, encoding='utf-8', newline='\n')
    (fixture / 'fake/python3').write_text('#!/usr/bin/env bash\nexit 0\n', encoding='utf-8', newline='\n')
    env = dict(os.environ, AUDIT_TRACE=str(fixture / 'trace.txt'), AUDIT_FAIL=failed_stage)
    run = subprocess.run(
        [a.bash, '-c', 'chmod +x fake/kicad-cli fake/python3; export PATH="$PWD/fake:$PATH"; bash scripts/export.sh --check-only'],
        cwd=fixture, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    (fixture / 'output.log').write_bytes(run.stdout)
    trace = (fixture / 'trace.txt').read_text() if (fixture / 'trace.txt').exists() else ''
    results['export_' + failed_stage] = {
        'injected_returncode': 5,
        'script_returncode': run.returncode,
        'gerbers_reached': 'pcb export gerbers' in trace,
        'commands': trace.splitlines(),
        'stdout': run.stdout.decode('utf-8', errors='replace')[-2000:],
    }

# Also prove default (candidate) mode does not reach gerbers on DRC failure.
fixture = out / 'export-drc-candidate'
(fixture / 'scripts').mkdir(parents=True, exist_ok=True)
(fixture / 'fake').mkdir(exist_ok=True)
shutil.copy2(root / 'hardware/pcb/scripts/export.sh', fixture / 'scripts/export.sh')
(fixture / 'fake/kicad-cli').write_text(
    (out / 'export-drc/fake/kicad-cli').read_text(encoding='utf-8'), encoding='utf-8', newline='\n')
(fixture / 'fake/python3').write_text('#!/usr/bin/env bash\nexit 0\n', encoding='utf-8', newline='\n')
env = dict(os.environ, AUDIT_TRACE=str(fixture / 'trace.txt'), AUDIT_FAIL='drc')
run = subprocess.run(
    [a.bash, '-c', 'chmod +x fake/kicad-cli fake/python3; export PATH="$PWD/fake:$PATH"; bash scripts/export.sh'],
    cwd=fixture, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
)
(fixture / 'output.log').write_bytes(run.stdout)
trace = (fixture / 'trace.txt').read_text() if (fixture / 'trace.txt').exists() else ''
results['export_drc_candidate'] = {
    'injected_returncode': 5,
    'script_returncode': run.returncode,
    'gerbers_reached': 'pcb export gerbers' in trace,
    'commands': trace.splitlines(),
}

results['interpretation'] = (
    'F19: stale_drc.failed_closed must be true (must not return OLD_REPORT). '
    'F04: ERC/DRC injected rc=5 must yield non-zero script status and must not reach gerbers. '
    '99 was the old Gerber sentry; reaching it meant the gate was bypassed.'
)
(out / 'faults.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != 'stdout'} if isinstance(v, dict) else v
                   for k, v in results.items()}, indent=2))
assert results['stale_drc']['failed_closed'], results['stale_drc']
assert results['export_erc']['script_returncode'] != 0
assert not results['export_erc']['gerbers_reached']
assert results['export_drc']['script_returncode'] != 0
assert not results['export_drc']['gerbers_reached']
assert results['export_drc_candidate']['script_returncode'] != 0
assert not results['export_drc_candidate']['gerbers_reached']
