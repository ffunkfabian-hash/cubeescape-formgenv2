"""Linie A gegen BALLONs eigenen Neubau am Pin (0.6 „Hangar“): je Typ das unveränderte Grundmodul (neuester Pilot, sonst
Formstudie) mit BALLONs `tools/blender_build.py` bauen und mit `out/assets/BAnn.glb` vergleichen – Bytes, Netze/Dreiecke je Netz und
Material, Materialien samt PBR, Knotenbaum, Weltdreiecke (tools/ballon_compare.compare_asset). Zusätzlich, nur zur Information,
gegen BALLONs Cache-GLB (~/Library/Caches/CubeEscapeBallon/out, Stand des letzten BALLON-Laufs, nicht des Pins).

  ~/Claude/cubeescape-nexogen/ce lock blender -- .venv/bin/python tools/line_a_parity.py [--types 01,16]

Voraussetzung: Stufe asset gebaut (`python -m formgen.pipeline --variants A --stages geometry,asset`). Exitcode 0 nur, wenn
jedes gewählte BAnn bytegleich zum Neubau ist. Bericht: <EVIDENCE>/belege/line_a_parity.json, Neubauten <EVIDENCE>/ballon_ref/.
"""
import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from formgen import asset, ballon, ballon_kit, variants  # noqa: E402
import ballon_compare  # noqa: E402

BALLON_CACHE = Path.home() / "Library/Caches/CubeEscapeBallon/out"


def rebuild(kit: Path, module: str, wid: str, folder: Path, blender: str) -> Path:
    """BALLONs Modul unverändert (model = None) über formgen/blender/asset_build.py bauen → folder/<wid>.glb."""
    folder.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"formgen-ref-{wid}-") as out:
        asset.run_blender({"snapshot": str(kit), "module": module, "model": None, "id": wid, "out": out}, blender)
        for ext in ("glb", "spec.json"):
            (folder / f"{wid}.{ext}").write_bytes((Path(out) / f"{wid}.{ext}").read_bytes())
    return folder / f"{wid}.glb"


def check(types, out: Path, evidence: Path) -> dict:
    cfg = asset.settings()
    snap, kit = ballon.snapshot(), ballon_kit.snapshot()
    line_a = next(v for v in variants.load() if v["letter"] == "A")
    report = {"ballon_commit": ballon.config()["commit"], "blender": asset.blender_version(cfg["blender"]), "types": {}}
    for num in types:
        sid = variants.sheet_id("A", num)
        base = ballon.resolve_base(snap, num, line_a["base"])
        version = ballon.pilot_version(base)
        wid = f"BASIC-{num}" + (f"-v{version}" if version else "")
        module = ballon_kit.module_name(kit, ballon.module_file(kit, num, base))
        mine = out / f"assets/{sid}.glb"
        entry = {"sheet": sid, "base": base, "module": module}
        if not mine.is_file():
            entry["status"] = f"{mine} fehlt"
        else:
            ref = rebuild(kit, module, wid, evidence / "ballon_ref", cfg["blender"])
            r = ballon_compare.compare_asset(mine, ref)
            entry.update(status="verglichen", rebuild=str(ref), bytes_equal=r["bytes_equal"], equal=r["equal"],
                         triangles=r["triangles"]["asset"], spec_equal=((ref.parent / f"{wid}.spec.json").read_bytes()
                                                                        == ballon.spec_path(snap, num, base).read_bytes()))
            cached = BALLON_CACHE / wid / f"{wid}.glb"
            if cached.is_file():
                c = ballon_compare.compare_asset(mine, cached)
                entry["ballon_cache"] = {"glb": str(cached), "equal": c["equal"], "bytes_equal": c["bytes_equal"],
                                         "triangles": c["triangles"]["ballon"],
                                         "differing": c["meshes_differing"][:5] + c["positions_differing"][:5]}
        report["types"][num] = entry
        print(sid, wid, entry["status"], "bytegleich" if entry.get("bytes_equal") else "", entry.get("triangles", ""),
              "| BALLON-Cache " + ("gleich" if entry.get("ballon_cache", {}).get("equal") else "abweichend")
              if "ballon_cache" in entry else "")
    report["all_bytes_equal"] = bool(report["types"]) and all(e.get("bytes_equal") for e in report["types"].values())
    return report


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--types", help="BASIC-Nummern, kommagetrennt (Standard alle 17)")
    p.add_argument("--out-dir", type=Path, default=ROOT / "out")
    p.add_argument("--evidence", type=Path, default=asset.EVIDENCE)
    a = p.parse_args(argv)
    report = check(a.types.split(",") if a.types else ballon.TYPES, a.out_dir, a.evidence)
    path = a.evidence / "belege/line_a_parity.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
    print(path)
    return 0 if report["all_bytes_equal"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
