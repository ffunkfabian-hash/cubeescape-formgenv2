"""Blatt-Spec Formgen v2 (Format `formgenv2/weapon-sheet-spec`, Version 1) aus dem ausgewerteten Geometriedokument.

Ab Version 1 gilt: jede Formatänderung erhöht FORMAT_VERSION, bekommt eine Migration in MIGRATIONS (alte Version →
nächste) und einen Test. Schema: docs/schemas/weapon-sheet-spec-1.schema.json. Keine Netze, keine Pfade, keine Zeiten.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORMAT = "formgenv2/weapon-sheet-spec"
FORMAT_VERSION = 1
SCHEMA = ROOT / "docs/schemas/weapon-sheet-spec-1.schema.json"
MIGRATIONS: dict = {}   # {von_version: funktion(doc) -> doc der nächsten Version}


class SpecError(ValueError):
    pass


def _r(value):
    return round(float(value), 2)


def _bounds(vertices):
    lo = [min(v[i] for v in vertices) for i in range(3)]
    hi = [max(v[i] for v in vertices) for i in range(3)]
    return lo, hi


def _mm_fux(point_m):
    """Ausgaberaum Meter (x links, −y vorn, z oben) → BALLON-Autorenmaß mm (f, u, x)."""
    x, y, z = point_m
    return [_r(-y * 1000), _r(z * 1000), _r(x * 1000)]


def build(document: dict) -> dict:
    gen = document["generator"]
    info = document["info"]
    vertices = [v for p in document["parts"] for v in p["mesh"]["vertices"]]
    lo, hi = _bounds(vertices)
    parts = []
    for p in document["parts"]:
        plo, phi = _bounds(p["mesh"]["vertices"])
        f0, u0, x0 = _mm_fux(plo); f1, u1, x1 = _mm_fux(phi)
        parts.append({"id": p["id"], "assembly": p["assembly"], "role": p["role"], "shape": p["shape"],
                      "name_de": p.get("label"), "name_en": p.get("name_en"),
                      "extent_mm": {"f": sorted([f0, f1]), "u": sorted([u0, u1]), "x": sorted([x0, x1])},
                      "triangles": len(p["mesh"]["faces"]), "moving": bool(p.get("move"))})
    anchors = {name: {"part": a["part"], "position_mm": [_r(v) for v in a["at"]]}
               for name, a in sorted(document.get("anchors", {}).items())}
    ballon_dims = gen.get("ballon_dimensions_mm")
    doc = {
        "format": FORMAT, "format_version": FORMAT_VERSION,
        "id": info["id"], "name_de": info["name_de"], "name_en": info["name_en"],
        "variant": gen["variant"], "type": gen["type"],
        "ballon": {k: gen["ballon"][k] for k in ("commit", "basic_id", "source_sha256", "spec_sha256", "files")},
        "generator": {"ops": gen["ops"], "adaptations": gen["adaptations"]},
        "dimensions_mm": {"length": _r((hi[1] - lo[1]) * 1000), "height": _r((hi[2] - lo[2]) * 1000),
                          "width": _r((hi[0] - lo[0]) * 1000)},
        "ballon_dimensions_mm": ballon_dims,
        "counts": {"parts": len(parts), "assemblies": len(document["assemblies"]),
                   "triangles": document["counts"]["triangles"]},
        "assemblies": [{"id": a["id"], "de": a.get("de"), "en": a.get("en")} for a in document["assemblies"]],
        "parts": parts, "anchors": anchors,
        "provenance": info["provenance"],
        "warnings": [w for w in document.get("warnings", []) if "Fase:" not in w],
    }
    validate(doc)
    return doc


def schema() -> dict:
    return json.loads(SCHEMA.read_text())


def validate(doc: dict) -> None:
    import jsonschema
    try:
        jsonschema.validate(doc, schema())
    except jsonschema.ValidationError as error:
        raise SpecError(f"{doc.get('id')}: {error.message} @ {list(error.absolute_path)}") from None
    for name, a in doc["anchors"].items():
        if a["part"] not in {p["id"] for p in doc["parts"]}:
            raise SpecError(f"{doc['id']}: Anker {name} verweist auf fehlendes Teil {a['part']}")
    if doc["id"] != f"B{doc['variant']['letter']}{doc['type']['num']}":
        raise SpecError(f"{doc['id']}: ID passt nicht zu Variante/Typ")


def migrate(doc: dict) -> dict:
    """Bring an older spec to FORMAT_VERSION via MIGRATIONS; newer or unknown versions are errors."""
    if doc.get("format") != FORMAT:
        raise SpecError(f"Fremdes Format {doc.get('format')!r}")
    version = doc.get("format_version")
    if not isinstance(version, int) or version < 1 or version > FORMAT_VERSION:
        raise SpecError(f"Unbekannte Spec-Version {version!r} (aktuell {FORMAT_VERSION})")
    while version < FORMAT_VERSION:
        if version not in MIGRATIONS:
            raise SpecError(f"Migration {version}→{version + 1} fehlt")
        doc = MIGRATIONS[version](doc)
        version += 1
        if doc.get("format_version") != version:
            raise SpecError(f"Migration nach {version} setzt format_version nicht")
    validate(doc)
    return doc
