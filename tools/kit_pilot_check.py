"""Baut BALLONs Spiel-Piloten (basic/pilot/*_v21.py) unverändert mit BALLONs Kit und prüft je Objekt gegen BALLONs Unity-Export.

  ~/Claude/cubeescape-nexogen/ce lock blender -- .venv/bin/python tools/kit_pilot_check.py [--out <ordner>] [--json <bericht>]

Frage aus 0.4: Baut das Kit `xprof` (Visiere der v2.1-Piloten), das v2s eigene Geometrie nicht kann? Referenz ist
`unity/Assets/Ballon/Generated/ego.json` am Pin: `weapons[].mesh_bounds.objects` (Dreiecke und Grenzen je Objekt nach den
Modifikatoren, von BALLONs export_unity gemessen). Verglichen werden Dreiecke je Netz der GLB aus tools/blender_build.py.
Ausgabe außerhalb des Repos (Standard ~/Library/Caches/CubeEscapeFormgen2/0.5/pilots/).
"""
import argparse
import collections
import importlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from formgen import asset, ballon_kit  # noqa: E402


def shapes(snap, module):
    """Formen eines Moduls inklusive Unterformen (multi) und Durchbrüche, gezählt (reines Python, ohne bpy)."""
    sys.path.insert(0, str(snap))
    try:
        W = importlib.import_module(module)
    finally:
        sys.path.remove(str(snap))
    count = collections.Counter()

    def visit(p):
        count[p.get("shape", "box")] += 1
        for q in p.get("items", ()):
            visit(q)
        for q in p.get("cuts") or ():
            count["cut:" + q.get("shape", "box")] += 1
    for p in W.PARTS:
        visit(p)
    return W.META["id"] + (f"-{W.META['variant']}" if W.META.get("variant") else ""), dict(sorted(count.items()))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", type=Path, default=asset.EVIDENCE / "pilots")
    p.add_argument("--json", type=Path)
    a = p.parse_args(argv)
    snap = ballon_kit.snapshot()
    ego = json.loads((snap / ballon_kit.EGO_JSON).read_text(encoding="utf-8"))
    refs = {w["id"]: {o["name"]: o["tris"] for o in w["mesh_bounds"]["objects"]} for w in ego["weapons"]}
    blender = asset.settings()["blender"]
    report = {"ballon_commit": snap.name.split(".")[0], "pilots": {}}
    for path in sorted((snap / "basic/pilot").glob("*_v21.py")):
        module = ballon_kit.module_name(snap, path)
        wid, count = shapes(snap, module)
        out = a.out / wid
        out.mkdir(parents=True, exist_ok=True)
        entry = {"module": module, "shapes": count}
        try:
            asset.run_blender({"snapshot": str(snap), "module": module, "model": None, "id": wid, "out": str(out)}, blender)
            info = asset.glb_info(out / f"{wid}.glb")
            got = {k: sum(x["triangles"] for x in v) for k, v in info["meshes"].items()}
            ref = refs.get(wid)
            entry.update(built=True, triangles=info["triangles"], objects=len(got))
            if ref is None:
                entry["ego_json"] = "keine Referenz (nicht im Unity-Export)"
            else:
                diff = sorted(k for k in set(got) | set(ref) if got.get(k) != ref.get(k))
                entry.update(ego_json_triangles=sum(ref.values()), equal=not diff, differing=diff[:10])
        except RuntimeError as e:
            entry.update(built=False, error=str(e)[-600:])
        report["pilots"][wid] = entry
        print(wid, "xprof" if any(k.endswith("xprof") for k in count) else "     ", entry.get("built"),
              entry.get("triangles"), entry.get("ego_json_triangles"), entry.get("equal", entry.get("ego_json", entry.get("error", ""))))
    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    return verdict(report)


def verdict(report) -> int:
    """0 nur, wenn Piloten gefunden, alle gebaut, alle mit Referenz und alle objektgleich sind."""
    pilots = report["pilots"].values()
    ok = bool(pilots) and all(e.get("built") and e.get("equal") is True for e in pilots)
    print("Ergebnis:", "alle gleich" if ok else "ABWEICHUNG oder fehlende Referenz")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
