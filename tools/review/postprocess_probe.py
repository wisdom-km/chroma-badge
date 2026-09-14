"""Test --skip-route on an isolated second copy, never the live board."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

p=argparse.ArgumentParser()
p.add_argument('--audit', required=True)
p.add_argument('--kicad-bin', required=True)
p.add_argument('--out')
a=p.parse_args()
audit=Path(a.audit).resolve()
dest=Path(a.out).resolve() if a.out else audit/'postprocess'
if dest.exists():
    raise SystemExit('Use a new postprocess directory; existing evidence is preserved.')
shutil.copytree(audit/'snapshot/hardware/pcb', dest)
kb=Path(a.kicad_bin).resolve()
env=dict(os.environ, PATH=str(kb)+os.pathsep+os.environ['PATH'], PYTHONUTF8='1', KICAD_CONFIG_HOME=str(audit/'kicad-config'))
env['KICAD9_3DMODEL_DIR']=str(kb.parent/'share/kicad/3dmodels')
py=kb/'python.exe'
helper=Path(__file__).with_name('pcb_audit.py').resolve()
records=[]
for n in range(3):
    if n:
        run=subprocess.run([str(py), 'scripts/route_pcb.py','--skip-route'],cwd=dest,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=600)
        (dest/f'cycle-{n}.log').write_bytes(run.stdout)
        if run.returncode:
            raise SystemExit(f'postprocess cycle {n} failed: {run.returncode}')
        shutil.copy2(dest/'output/drc_final.json',dest/f'cycle-{n}-drc.json')
    subprocess.run([str(py),str(helper),'--pcb',str(dest),'--out',str(dest/f'cycle-{n}.json')],env=env,check=True)
    data=json.loads((dest/f'cycle-{n}.json').read_text())
    records.append({k:data[k] for k in ['segments','vias','routing_sha256','net_assignment_problems']})
(dest/'summary.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
print(json.dumps(records,indent=2))
raise SystemExit(0 if records[0] == records[1] == records[2] else 1)
