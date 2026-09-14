"""Diagnostic exports and metadata-only Gerber comparison for a completed audit."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

p=argparse.ArgumentParser()
p.add_argument('--audit',required=True)
p.add_argument('--kicad-bin',required=True)
p.add_argument('--compare-only',action='store_true')
a=p.parse_args()
audit=Path(a.audit).resolve()
pcb=audit/'snapshot/hardware/pcb'
out=audit/'kicad'
cli=Path(a.kicad_bin).resolve()/'kicad-cli.exe'
env=dict(os.environ,KICAD_CONFIG_HOME=str(audit/'kicad-config'))
commands=[
    ('schematic-pdf',['sch','export','pdf','-o',str(out/'schematic.pdf'),'badge.kicad_sch']),
    ('schematic-svg',['sch','export','svg','-o',str(out/'sch-svg'),'--no-background-color','badge.kicad_sch']),
    ('pcb-front-svg',['pcb','export','svg','--layers','F.Cu,F.SilkS,Edge.Cuts','--page-size-mode','2','--exclude-drawing-sheet','-o',str(out/'pcb-front.svg'),'badge.kicad_pcb']),
    ('pcb-back-svg',['pcb','export','svg','--layers','B.Cu,B.SilkS,Edge.Cuts','--mirror','--page-size-mode','2','--exclude-drawing-sheet','-o',str(out/'pcb-back.svg'),'badge.kicad_pcb']),
    ('board-only-step',['pcb','export','step','--board-only','--no-dnp','-o',str(out/'board-only.step'),'badge.kicad_pcb'])]
results=json.loads((out/'extra-exports.json').read_text())['commands'] if a.compare_only else []
for name,cmd in ([] if a.compare_only else commands):
    run=subprocess.run([str(cli),*cmd],cwd=pcb,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=300)
    (out/(name+'.log')).write_bytes(run.stdout)
    results.append({'name':name,'command':[str(cli),*cmd],'returncode':run.returncode})

def normalize(text):
    # Remove ONLY KiCad creation-date metadata, not coordinates, attributes or apertures.
    return '\n'.join(s for s in text.splitlines() if not s.startswith(('%TF.CreationDate,','G04 Created by KiCad ','; #@! TF.CreationDate,','; DRILL file {KiCad ')))

comparisons=[]
for fresh in sorted((out/'gerbers').iterdir()):
    old=pcb/'output/gerbers'/fresh.name
    if fresh.suffix not in ('.gbr','.drl'):
        continue
    norm_new=normalize(fresh.read_text())
    norm_old=normalize(old.read_text()) if old.exists() else ''
    comparisons.append({'file':fresh.name,'normalized_equal':norm_new==norm_old,
                        'fresh_normalized_sha256':hashlib.sha256(norm_new.encode()).hexdigest(),
                        'old_normalized_sha256':hashlib.sha256(norm_old.encode()).hexdigest()})
(out/'extra-exports.json').write_text(json.dumps({'commands':results,'gerber_drill_comparison':comparisons,'normalization':'Only four creation-date line prefixes stripped; gbrjob not compared.'},indent=2),encoding='utf-8')
print(json.dumps({'commands':results,'comparison':comparisons},indent=2))
raise SystemExit(1 if any(x['returncode'] for x in results) else 0)
