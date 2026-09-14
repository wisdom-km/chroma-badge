"""Run fresh KiCad checks/exports on a prepared snapshot, preserving every return code.

An audit recorder, NOT a manufacturing release command. Exports are diagnostic only.
"""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import shutil
import subprocess


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--audit', required=True)
    p.add_argument('--kicad-bin', required=True)
    p.add_argument('--export', action='store_true')
    args = p.parse_args()
    audit = Path(args.audit).resolve()
    pcb = audit / 'snapshot/hardware/pcb'
    dest = audit / 'kicad'
    if dest.exists():
        raise SystemExit('Use a new audit directory; existing KiCad evidence is not overwritten.')
    dest.mkdir()
    kb = Path(args.kicad_bin).resolve()
    cli = kb / ('kicad-cli.exe' if os.name == 'nt' else 'kicad-cli')
    py = kb / ('python.exe' if os.name == 'nt' else 'python3')
    env = dict(os.environ, PYTHONUTF8='1')
    share = kb.parent / 'share/kicad'
    config = audit / 'kicad-config'
    config.mkdir(exist_ok=True)
    env['KICAD_CONFIG_HOME'] = str(config)
    # Resolve official libraries without changing the user's KiCad preferences.
    for folder in [config, config / '9.0', config / '10.0']:
        folder.mkdir(exist_ok=True)
        for table in ['sym-lib-table', 'fp-lib-table']:
            template = share / 'template' / table
            if template.exists():
                shutil.copy2(template, folder / table)
    for major in (9, 10):
        env[f'KICAD{major}_SYMBOL_DIR'] = str(share / 'symbols')
        env[f'KICAD{major}_FOOTPRINT_DIR'] = str(share / 'footprints')
        env[f'KICAD{major}_3DMODEL_DIR'] = str(share / '3dmodels')
    env['PATH'] = str(kb) + os.pathsep + env['PATH']
    records = []

    def run(name, cmd):
        result = subprocess.run([str(x) for x in cmd], cwd=pcb, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
        (dest / (name + '.log')).write_bytes(result.stdout)
        records.append({'name': name, 'command': [str(x) for x in cmd], 'returncode': result.returncode})
        (dest / 'commands.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
        print(name, result.returncode, flush=True)
        return result.returncode

    run('version', [cli, '--version'])
    run('erc-all', [cli, 'sch', 'erc', '--format', 'json', '--exit-code-violations', '-o', dest / 'erc-all.json', 'badge.kicad_sch'])
    run('erc-errors', [cli, 'sch', 'erc', '--severity-error', '--format', 'json', '--exit-code-violations', '-o', dest / 'erc-errors.json', 'badge.kicad_sch'])
    run('drc-all-parity', [cli, 'pcb', 'drc', '--schematic-parity', '--format', 'json', '--exit-code-violations', '-o', dest / 'drc-all-parity.json', 'badge.kicad_pcb'])
    run('drc-errors', [cli, 'pcb', 'drc', '--severity-error', '--format', 'json', '--exit-code-violations', '-o', dest / 'drc-errors.json', 'badge.kicad_pcb'])
    run('netlist-export', [cli, 'sch', 'export', 'netlist', '-o', 'output/badge.net', 'badge.kicad_sch'])
    run('netlist-check', [py, 'scripts/check_netlist.py'])
    run('board-audit', [py, Path(__file__).with_name('pcb_audit.py'), '--pcb', pcb, '--out', dest / 'board-audit.json'])
    if args.export:
        run('gerbers', [cli, 'pcb', 'export', 'gerbers', '--layers', 'F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts', '--subtract-soldermask', '--no-protel-ext', '-o', str(dest / 'gerbers') + '/', 'badge.kicad_pcb'])
        run('drill', [cli, 'pcb', 'export', 'drill', '--format', 'excellon', '--excellon-separate-th', '--generate-map', '--map-format', 'gerberx2', '-o', str(dest / 'gerbers') + '/', 'badge.kicad_pcb'])
        run('pos', [cli, 'pcb', 'export', 'pos', '--side', 'back', '--format', 'csv', '--units', 'mm', '--use-drill-file-origin', '-o', dest / 'positions.csv', 'badge.kicad_pcb'])
        run('bom', [cli, 'sch', 'export', 'bom', '--fields', 'Reference,Value,Footprint,Description,LCSC,${QUANTITY},${DNP}', '--labels', 'Ref,Value,Footprint,Description,LCSC,Qty,DNP', '--group-by', 'Value,Footprint,LCSC', '-o', dest / 'bom.csv', 'badge.kicad_sch'])
        run('step', [cli, 'pcb', 'export', 'step', '--no-dnp', '--subst-models', '-o', dest / 'badge-fresh.step', 'badge.kicad_pcb'])
        run('render-back', [cli, 'pcb', 'render', '--side', 'bottom', '--width', '1600', '--height', '1500', '--quality', 'high', '-o', dest / 'render-back.png', 'badge.kicad_pcb'])
        run('render-j1', [cli, 'pcb', 'render', '--side', 'bottom', '--pivot', '-0.55,-3.1,0', '--zoom', '7', '--width', '1400', '--height', '1000', '--quality', 'high', '-o', dest / 'render-j1.png', 'badge.kicad_pcb'])
    summary = {}
    for path in dest.glob('*.json'):
        if path.name in ('commands.json', 'summary.json', 'board-audit.json'):
            continue
        data = json.loads(path.read_text(encoding='utf-8'))
        items = list(data.get('violations', [])) + list(data.get('unconnected_items', [])) + list(data.get('schematic_parity', []))
        for sheet in data.get('sheets', []):
            items.extend(sheet.get('violations', []))
        summary[path.name] = {'count': len(items), 'severity': dict(Counter(x.get('severity') for x in items)), 'types': dict(Counter(x.get('type') for x in items))}
    (dest / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))
    # Nonzero checks remain visible to callers, including expected warning findings.
    raise SystemExit(1 if any(x['returncode'] for x in records) else 0)


if __name__ == '__main__':
    main()
