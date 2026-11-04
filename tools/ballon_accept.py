"""Abnahme durch BALLON: Bake-Pakete (Format 2) mit BALLONs unverändertem `tools/formgen_import.py` aus dem gepinnten Schnappschuss einlesen.

  .venv/bin/python tools/ballon_accept.py BJ01 BK05 BL13 BM09 [--out <json>]

Je Paket: ZIP in einen Ordner `<tmp>/<ID>` entpacken (`asset.unpack`), BALLONs `formgen_import.entry` rechnet den Eintrag von `ego.json`
aus dem Datensatz (Bauteil-Hash, `variant.problems`, Grundtyp, Skin der Linie als Standard). Gegenprobe je Paket: derselbe Ordner mit
verfälschtem Datensatz (ein Teil verschoben: Hash passt nicht; Weltpunkt entfernt) muss abgelehnt werden. BALLON bleibt unberührt.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from formgen import asset, ballon_kit  # noqa: E402

CHECK = r'''
import json, os, sys
sys.path.insert(0, sys.argv[1])
from tools import formgen_import as FI
folder = sys.argv[2]
sid = os.path.basename(folder)
path = os.path.join(folder, f'{sid}.package.json')
M = json.load(open(path, encoding='utf-8'))
out = {}
e = FI.entry(folder)
out['accepted'] = dict(name=e['weapon']['name'], base=e['origin']['base_id'], points=e['origin']['points'], skin=e['origin']['skin'],
                       gameplay=e['origin']['gameplay'], parts=len(e['weapon'].get('parts', [])) if isinstance(e['weapon'].get('parts'), list) else None,
                       atlas=e.get('atlas'), live=sorted(k for k, v in (e['weapon'].get('live') or {}).items() if v))
def refused(change):
    T = json.loads(json.dumps(M))
    change(T)
    json.dump(T, open(path, 'w', encoding='utf-8'))
    try:
        FI.entry(folder)
        return None
    except (FI.PackageError, KeyError) as err:
        return str(err)[:160]
    finally:
        json.dump(M, open(path, 'w', encoding='utf-8'))
def move(T):
    p = T['model']['PARTS'][-1]
    p['bevel'] = p.get('bevel', 1) + 1
def drop_point(T):
    T['model']['POINTS'].pop(sorted(T['model']['POINTS'])[0])
out['refused_changed_part'] = refused(move)
out['refused_missing_point'] = refused(drop_point)
print('RESULT ' + json.dumps(out, ensure_ascii=False))
'''


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("ids", nargs="+")
    p.add_argument("--out", type=Path, default=asset.EVIDENCE / "belege/ballon_accept.json")
    a = p.parse_args(argv)
    kit = ballon_kit.snapshot()
    result, ok = {}, True
    with tempfile.TemporaryDirectory(prefix="formgen-accept-") as tmp:
        script = Path(tmp) / "check.py"
        script.write_text(CHECK)
        for sid in a.ids:
            folder = asset.unpack(ROOT / f"out/assets/{sid}.bake.zip", Path(tmp) / "packages")
            run = subprocess.run([sys.executable, str(script), str(kit), str(folder)], capture_output=True, text=True,
                                 cwd=tmp, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
            line = next((x for x in run.stdout.splitlines() if x.startswith("RESULT ")), None)
            if line is None:
                result[sid] = {"error": (run.stderr or run.stdout)[-600:]}
                ok = False
            else:
                result[sid] = json.loads(line[7:])
                ok = ok and bool(result[sid]["refused_changed_part"]) and bool(result[sid]["refused_missing_point"])
            print(sid, json.dumps(result[sid], ensure_ascii=False)[:400])
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
