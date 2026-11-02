"""v2-Messung im selben Ablauf wie tools/measure_v1.py: kalt, warm, kleine Änderung – mit frischem Cache im Scratch-Ordner.

  python3 tools/measure_v2.py --work <scratch> --out <json> [--jobs 8]

kalt     leerer Cache, alle registrierten Blätter, alle Stufen (Zeiten je Stufe aus pipeline.run)
warm     zweiter Lauf ohne Änderung
klein    eine Zahl in einem BALLON-Modell (Kopie des Snapshots, BASIC-05) → betrifft 3 Blätter (A/B/C)
klein-1  dieselbe Art Änderung, aber nur ein Blatt gebaut (python -m formgen.pipeline BA05), Vergleich zu v1 je Blatt
Keine Datei im Repo oder im echten BALLON-Snapshot wird verändert.
"""
import argparse, json, os, platform, re, shutil, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from formgen import ballon, pipeline, variants  # noqa: E402


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--work", type=Path, required=True); p.add_argument("--out", type=Path, required=True)
    p.add_argument("--jobs", type=int, default=max(1, min(8, (os.cpu_count() or 2) - 2)))
    a = p.parse_args(argv)
    if a.work.exists() and any(a.work.iterdir()):
        raise SystemExit(f"{a.work} muss leer sein (frischer Cache)")
    out, cache = a.work / "out", a.work / "cache"
    cfg = ballon.config(); snap = ballon.snapshot()
    selection = pipeline.select()
    res = {"commit_v2": os.popen(f"git -C {ROOT} rev-parse HEAD").read().strip(), "ballon_commit": cfg["commit"],
           "machine": platform.platform(), "cpus": os.cpu_count(), "jobs": a.jobs, "sheets": len(selection),
           "load_before": os.getloadavg(), "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "runs": {}}
    log = lambda line: print(line, flush=True)

    def measure(name, sel, **kw):
        t = time.perf_counter()
        _, timing = pipeline.run(sel, out, cache, jobs=a.jobs, log=log, **kw)
        timing["wall_seconds"] = round(time.perf_counter() - t, 3)
        res["runs"][name] = timing
        log(f"== {name}: {timing['wall_seconds']} s, {timing['built']} gebaut, {timing['cached']} Treffer")

    measure("cold", selection)
    measure("warm", selection)
    changed = a.work / "ballon-changed" / ("0" * 40)
    shutil.copytree(snap, changed)
    module = ballon.module_file(changed, "05")
    text = module.read_text()
    new = re.sub(r"\[\((-?\d+), ", lambda m: f"[({int(m.group(1)) + 1}, ", text, count=1)
    assert new != text
    module.write_text(new)
    res["small_change"] = {"file": module.relative_to(changed).as_posix(), "what": "erster Profilpunkt +1 mm"}
    measure("small_change_3_sheets", selection, snap=changed)
    module.write_text(re.sub(r"\[\((-?\d+), ", lambda m: f"[({int(m.group(1)) + 1}, ", new, count=1))
    measure("small_change_1_sheet", {"BA05": selection["BA05"]}, snap=changed)
    res["load_after"] = os.getloadavg(); res["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
