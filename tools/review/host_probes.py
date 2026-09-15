"""Compile firmware epd.cpp against host I/O stubs. Success only on a normal BUSY cycle."""
import argparse
import json
import os
from pathlib import Path
import subprocess

p=argparse.ArgumentParser()
p.add_argument('--compiler',required=True)
p.add_argument('--out',required=True)
a=p.parse_args()
root=Path(__file__).resolve().parents[2]
out=Path(a.out).resolve()
out.mkdir(parents=True,exist_ok=True)
compiler=Path(a.compiler).resolve()
env=dict(os.environ,PATH=str(compiler.parent)+os.pathsep+os.environ['PATH'])
exe=out/('epd-probe.exe' if os.name=='nt' else 'epd-probe')
cmd=[str(compiler),'-std=c++17','-Wall','-Wextra','-I'+str(root/'tools/review/host'),'-I'+str(root/'firmware/include'),str(root/'firmware/src/epd.cpp'),str(root/'tools/review/host/epd_probe.cpp'),'-o',str(exe)]
build=subprocess.run(cmd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(out/'compile.log').write_bytes(build.stdout)
build.check_returncode()
rows=[]
for scenario in ['normal','always-high','always-low','poweroff-timeout','refresh-timeout']:
    for color in range(4):
        row=json.loads(subprocess.check_output([str(exe),scenario,str(color)],env=env))
        rows.append(row)
        assert row['rail_off'], row
        if scenario in ('normal', 'refresh-timeout', 'poweroff-timeout'):
            assert row['frame_bytes']==30000 and row['pixels_match'], row
        expected = scenario == 'normal'
        assert row['reported_success']==expected, row
(out/'epd-probes.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print('20 host cases passed; BUSY stuck-high / power-off timeout no longer report success.')
