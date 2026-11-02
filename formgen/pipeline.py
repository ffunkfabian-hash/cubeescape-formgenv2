"""Waffen-Pipeline Formgen v2: BALLON-Grundform → Variante → Geometrie → Spec/Prompts → Ansichten → Blatt → Vorschau → Viewer.

  python -m formgen.pipeline                       # alle registrierten Blätter (Variante × 17 Typen)
  python -m formgen.pipeline BA01 BB01             # einzelne Blätter
  python -m formgen.pipeline --variants A --types 01,02 --stages geometry,specs

Jede Stufe ist ein eigener Cacheeintrag (formgen/cache.py). Schlüssel nur aus Inhalten: BALLON-Quellhash und Spec-Hash
des Typs, Registereintrag, Quellen-Closure des Stufencodes, Komponentenversionen, Render-Einstellungen und Umgebung
(Python/numpy/Pillow) – nie Pfade oder Dateizeiten. Ohne --force wird nur Fehlendes/Veraltetes gebaut; ein zweiter Lauf
ohne Änderung ist reiner Treffer. Zeiten je Stufe stehen in out/timing.json.
"""
from __future__ import annotations

import argparse
import dataclasses
import functools
import hashlib
import json
import os
import platform
import time
from pathlib import Path

from . import ballon, build, variants, versions
from .cache import Artifact, canonical, file_hash, run_artifacts

ROOT = build.ROOT
STAGES = ("geometry", "specs", "prompts", "views", "sheets", "previews", "viewer")
CODE = {"geometry": "formgen/generator.py", "specs": "formgen/wspec.py", "prompts": "formgen/prompts.py",
        "views": "formgen/raster.py", "sheets": "formgen/sheet.py", "previews": "formgen/raster.py",
        "viewer": "formgen/viewer.py"}
IMAGE_STAGES = ("views", "previews")


# Dateien mit den Builder-Funktionen selbst (build_geometry/build_spec hier, build_view/build_sheet/… in build.py).
# Nur der Dateiinhalt zählt, nicht ihre Closure: build.py importiert lazy die ganze Engine.
BUILDERS = ("formgen/pipeline.py", "formgen/build.py")


@functools.lru_cache(maxsize=None)
def code_hash(rel: str) -> str:
    """SHA256 over the stage module's static local import closure plus the builder files (relative names, content only)."""
    hashes = build.source_hashes(ROOT / rel)
    relative = {str(Path(k).relative_to(ROOT)): v for k, v in hashes.items()}
    relative.update({f"builder:{b}": file_hash(ROOT / b) for b in BUILDERS})
    return hashlib.sha256(canonical(relative)).hexdigest()


@functools.lru_cache(maxsize=None)
def environment() -> dict:
    import numpy, PIL
    return {"python": ".".join(platform.python_version_tuple()[:2]), "numpy": numpy.__version__, "pillow": PIL.__version__}


def _ballon_dims(spec):
    if not spec:
        return None
    d = spec["dimensions"]
    return {k: round(d[f"{k}_m"] * 1000, 2) for k in ("length", "height", "width")}


def geometry_plan(selection, snap, commit):
    artifacts = []
    for sid, entry in selection.items():
        variant, num = entry["variant"], entry["num"]
        src = ballon.source(snap, num)
        record = {k: variant[k] for k in ("letter", "name", "idea", "since", "skin", "params")}
        source = hashlib.sha256(canonical({"ballon": src["source_sha256"], "ballon_spec": src["spec_sha256"],
                                           "variant": record, "num": num})).hexdigest()
        params = {"booleans": True, "bevels": True, "code": code_hash(CODE["geometry"])}
        artifacts.append(Artifact(sid, "geometry", source, params, {"MODEL": versions.MODEL, "GEOM": versions.GEOM},
                                  f"geometry/{sid}.json", "formgen.pipeline:build_geometry",
                                  {"snapshot": str(snap), "num": num, "variant": record, "source": src,
                                   "ballon_dims": _ballon_dims(ballon.load_spec(snap, num))}))
    return artifacts


def build_geometry(artifact: Artifact) -> bytes:
    from . import generator
    inputs = artifact.inputs
    snap = Path(inputs["snapshot"])
    if ballon.source(snap, inputs["num"]) != inputs["source"]:
        raise RuntimeError("BALLON-Snapshot weicht vom geplanten Quellhash ab")
    document = generator.evaluate(ballon.load(snap, inputs["num"]), inputs["variant"], inputs["num"], inputs["source"],
                                  inputs["ballon_dims"], **{k: artifact.params[k] for k in ("booleans", "bevels")})
    if document["info"]["id"] != artifact.model_id:
        raise ValueError("Blatt-ID widerspricht dem Plan")
    return canonical(document) + b"\n"


def spec_plan(ids, out, commit):
    artifacts = []
    for sid in ids:
        path = Path(out).resolve() / "geometry" / f"{sid}.json"
        artifacts.append(Artifact(sid, "specs", file_hash(path), {"code": code_hash(CODE["specs"]), "ballon_commit": commit},
                                  {"WSPEC": versions.WSPEC}, f"specs/{sid}.spec.json", "formgen.pipeline:build_spec",
                                  {"geometry_path": str(path)}))
    return artifacts


def build_spec(artifact: Artifact) -> bytes:
    from . import wspec
    document = build._document(artifact)
    document["generator"]["ballon"] = dict(document["generator"]["ballon"], commit=artifact.params["ballon_commit"])
    return json.dumps(wspec.build(document), indent=1, ensure_ascii=False, sort_keys=True).encode() + b"\n"


def _with(artifacts, stage, **extra):
    params = {"code": code_hash(CODE[stage]), **extra}
    if stage in IMAGE_STAGES:
        params["env"] = environment()
    return [dataclasses.replace(a, params={**a.params, **params}) for a in artifacts]


def downstream(stage, ids, out, selection):
    if stage == "views" or stage == "previews":
        artifacts = []
        for sid in ids:
            artifacts += build.downstream_plan([sid], out, stage, skin=selection[sid]["variant"]["skin"])
        return _with(artifacts, stage)
    return _with(build.downstream_plan(ids, out, stage), stage)


def select(ids=(), letters=None, types=None, entries=None):
    sheets = variants.sheets(entries)
    if ids:
        unknown = [i for i in ids if i not in sheets]
        if unknown:
            raise SystemExit(f"Unbekannte Blatt-ID: {', '.join(unknown)}")
        return {i: sheets[i] for i in ids}
    return {sid: e for sid, e in sheets.items()
            if (not letters or e["variant"]["letter"] in letters) and (not types or e["num"] in types)}


def run(selection, out, cache, stages=STAGES, jobs=1, force=False, log=print, snap=None, commit=None):
    """Build the selection stage by stage; `snap`/`commit` override the pinned BALLON snapshot (measurements, tests)."""
    out, cache = Path(out), Path(cache)
    cfg = ballon.config()
    if commit:
        cfg["commit"] = commit
    snap = Path(snap) if snap else ballon.snapshot(cfg["commit"], cfg["repo"])
    ids = list(selection)
    timing = {"ballon_commit": cfg["commit"], "sheets": len(ids), "jobs": jobs, "force": force,
              "env": environment(), "stages": {}}
    results = []
    t_all = time.perf_counter()

    def stage(name, artifacts):
        t = time.perf_counter()
        res = run_artifacts(artifacts, out, cache, jobs=jobs, force=force)
        dt = time.perf_counter() - t
        built = sum(r.built for r in res)
        timing["stages"][name] = {"seconds": round(dt, 3), "built": built, "cached": len(res) - built}
        log(f"{name:9} {built:4} gebaut · {len(res) - built:4} aus dem Cache · {dt:7.2f} s")
        results.extend(res)

    stage("geometry", geometry_plan(selection, snap, cfg["commit"]))
    if "specs" in stages:
        stage("specs", spec_plan(ids, out, cfg["commit"]))
    if "prompts" in stages:
        stage("prompts", downstream("prompts", ids, out, selection))
    if "views" in stages or "sheets" in stages:
        stage("views", downstream("views", ids, out, selection))
    if "sheets" in stages:
        stage("fonts", build.font_plan())
        stage("sheets", downstream("sheets", ids, out, selection))
    if "previews" in stages:
        stage("previews", downstream("previews", ids, out, selection))
    if "viewer" in stages:
        from . import viewer
        t = time.perf_counter()
        res = viewer.build(out, cache, force=force)
        timing["stages"]["viewer"] = {"seconds": round(time.perf_counter() - t, 3), "built": sum(r.built for r in res),
                                      "cached": sum(not r.built for r in res)}
        log(f"{'viewer':9} {sum(r.built for r in res):4} gebaut · {sum(not r.built for r in res):4} aus dem Cache")
        results.extend(res)
    timing["total_seconds"] = round(time.perf_counter() - t_all, 3)
    built = sum(r.built for r in results)
    timing["built"], timing["cached"] = built, len(results) - built
    (out / "timing.json").write_text(json.dumps(timing, indent=1) + "\n")
    log(f"gesamt    {built:4} gebaut · {len(results) - built:4} aus dem Cache · {timing['total_seconds']:7.2f} s")
    return results, timing


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("ids", nargs="*", help="Blatt-IDs (BA01 …); ohne Angabe alle registrierten")
    p.add_argument("--variants", help="Kennbuchstaben, kommagetrennt")
    p.add_argument("--types", help="BASIC-Nummern 01–17, kommagetrennt")
    p.add_argument("--stages", help="Kommagetrennt aus " + ",".join(STAGES) + "; geometry läuft immer")
    p.add_argument("--out", type=Path, default=ROOT / "out")
    p.add_argument("--cache", type=Path, default=build.DEFAULT_CACHE)
    p.add_argument("--jobs", type=int, default=max(1, min(8, (os.cpu_count() or 2) - 2)))
    p.add_argument("--force", action="store_true", help="ausgewählte Artefakte neu bauen (Cache wird erneuert)")
    a = p.parse_args(argv)
    stages = a.stages.split(",") if a.stages else list(STAGES)
    if any(s not in STAGES for s in stages):
        p.error("Unbekannte Stufe")
    selection = select(a.ids, a.variants and a.variants.split(","), a.types and a.types.split(","))
    if not selection:
        p.error("Auswahl ist leer")
    run(selection, a.out, a.cache, stages, a.jobs, a.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
