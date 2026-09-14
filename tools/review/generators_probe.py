"""Regenerate schematic/NFC footprint in a third copy; never run gen_pcb.py."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

p=argparse.ArgumentParser()
p.add_argument('--audit',required=True)
p.add_argument('--kicad-bin',required=True)
p.add_argument('--python-deps',required=True)
p.add_argument('--out')
a=p.parse_args()
audit=Path(a.audit).resolve()
dest=Path(a.out).resolve() if a.out else audit/'generators'
if dest.exists(): raise SystemExit('Use a new audit directory.')
shutil.copytree(audit/'snapshot/hardware/pcb',dest)
kb=Path(a.kicad_bin).resolve()
py=kb/'python.exe'
cli=kb/'kicad-cli.exe'
env=dict(os.environ,PYTHONUTF8='1',PYTHONPATH=str(Path(a.python_deps).resolve()),KICAD9_SYMBOL_DIR=str(kb.parent/'share/kicad/symbols'),KICAD_CONFIG_HOME=str(audit/'kicad-config'))
records=[]
for name,cmd in [
    ('dependency',[py,'-c','import sys; sys.path.insert(0,sys.argv[1]); import importlib.metadata; print(importlib.metadata.version("sexpdata"))', str(Path(a.python_deps).resolve())]),
    ('nfc-generator',[py,'scripts/gen_nfc_footprint.py']),
    ('schematic-generator',[py,'scripts/gen_schematic.py']),
    ('net-export',[cli,'sch','export','netlist','-o','output/badge.net','badge.kicad_sch']),
    ('net-check',[py,'scripts/check_netlist.py']),
    ('generated-erc',[cli,'sch','erc','--severity-error','--format','json','--exit-code-violations','-o','generated-erc.json','badge.kicad_sch'])]:
    if cmd[0] == py and cmd[1] != '-c':
        cmd=[py,'-c','import sys,runpy; sys.path.insert(0,sys.argv[1]); runpy.run_path(sys.argv[2],run_name="__main__")',str(Path(a.python_deps).resolve()),cmd[1]]
    run=subprocess.run([str(x) for x in cmd],cwd=dest,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=300)
    (dest/(name+'.log')).write_bytes(run.stdout)
    records.append({'name':name,'command':[str(x) for x in cmd],'returncode':run.returncode})
    if run.returncode: break
fp=Path('lib/badge.pretty/NFC_Loop.kicad_mod')
result={'commands':records,'nfc_footprint_equal_ignoring_newlines':(dest/fp).read_text()==(audit/'snapshot/hardware/pcb'/fp).read_text(),'gen_pcb_executed':False}
(dest/'summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
raise SystemExit(1 if any(x['returncode'] for x in records) or not result['nfc_footprint_equal_ignoring_newlines'] else 0)
