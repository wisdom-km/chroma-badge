"""Create an isolated audit copy; never regenerate or overwrite the working PCB."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', required=True)
    args = p.parse_args()
    root = Path(__file__).resolve().parents[2]
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    snapshot = out / 'snapshot'
    if snapshot.exists():
        raise SystemExit('Use a new output directory; existing audit evidence is not overwritten.')
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0')
    records = {}
    for name in filter(None, tracked):
        src = root / name
        if not src.is_file():
            continue
        records[name] = {'sha256': sha(src), 'bytes': src.stat().st_size}
        if name.startswith(('hardware/', 'firmware/')):
            dst = snapshot / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    pro = 'hardware/pcb/badge.kicad_pro'
    # Record pre-existing local edits but validate the immutable committed project first.
    shutil.copy2(root / pro, out / 'local-project.kicad_pro')
    (snapshot / pro).write_bytes(subprocess.check_output(['git', 'show', 'HEAD:' + pro], cwd=root))
    manifest = {
        'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root).decode().strip(),
        'initial_status': subprocess.check_output(['git', 'status', '--short'], cwd=root).decode(),
        'working_tree_files': records,
        'snapshot_project_sha256': sha(snapshot / pro),
        'note': 'Snapshot uses committed project settings; local settings preserved separately. No routing performed.'
    }
    (out / 'inputs.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    print(snapshot)


if __name__ == '__main__':
    main()
