"""0.42 „Canon“: Design-Kanon von BASIC und EXTENDED messen und als Beispielpaket für eine weitere Waffen-Generation bündeln.

Die Zahlen des Kanons (`docs/design-kanon.md`, Block zwischen den Markern) stammen nur von hier: je Modell (BASIC Linie A = BALLON-Pilot,
EXTENDED EA01–EA17) Länge, Höhe, Breite, Streckung, Füllgrad der Seitenansicht, Visierlinie, Akzentfunktionen, Handrollen, die zwei
größten Materialrollen und der nächste Nachbar der Familie (Seiten-IoU); dazu die Detaildichte (Patch kanon-detail): Teile, Formen,
Anteil Rundkörper und Quader, Zahl der Materialrollen, blanke Kanten. `--check` vergleicht den Block mit einer frischen Messung, so
veraltet der Kanon nicht still, wenn ein Modell sich ändert. `zeile` nennt die Werte außerhalb des Bands der Klasse.

    python -m formgen.kanon messen [--check]
    python -m formgen.kanon zeile <Kurzname>     # neue Waffe gegen die Familie (Stilprüfung)
    python -m formgen.kanon paket --out <Ordner> [--bilder <Ordner mit Übersicht>]
"""
from __future__ import annotations

from collections import Counter
import argparse
import math
import shutil
import statistics
import sys
from pathlib import Path

import numpy as np

from . import ballon, extended, extended_lines, generator, variants, variety
from .models.weapons import AUTHORED

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/design-kanon.md"
BEGIN, END = "<!-- kanon:messung:anfang -->", "<!-- kanon:messung:ende -->"
SIDE = variety.VIEWS["side"]
PAD_MM = 4   # Vorgabe: Rand des Messrasters wie variety.iou (0.4), damit Kanten nicht am Bildrand abgeschnitten werden
# Waffenklassen nach Typnummer (BASIC-Typ = EXTENDED-Nummer): Bänder nur innerhalb einer Klasse sinnvoll
CLASSES = {"Langwaffe": ("01", "02", "03", "08", "09", "10", "11", "12", "15"), "Kompakt": ("04", "05", "06"),
           "Werfer": ("13", "14"), "Bogen": ("07",), "Nahkampf": ("16", "17")}
# Musterlösungen für das Paket (Auswahl begründet in docs/design-kanon.md › Beispielpaket)
EXAMPLES = ("e01_spearhead", "e04_sledge", "e07_caliper", "e09_theodolite", "e12_shuttle", "e13_mantlet", "e14_keelson", "e16_sweepguard")


def _basic(snap):
    a = next(v for v in variants.load() if v["letter"] == "A")
    for num in ballon.TYPES:
        data = ballon.load(snap, num, ballon.resolve_base(snap, num, a.get("base", "standard")))
        author, _ = generator.build(a, num, snap)
        yield f"BA{num}", data, generator.adapt(data)[0], author


def _extended(snap):
    for key in extended_lines.KEYS:
        model = extended.load(key, snap)
        sid = extended.sheet_id(key)
        yield sid, model, model, extended_lines.author(model, sid)[0]


def _fill(tris) -> float:
    """Anteil der Seitensilhouette an ihrem Rechteck: klein = luftig (Fenster, Bügel), groß = geschlossener Block."""
    pts = tris.reshape(-1, 3)[:, list(SIDE)] * 1000
    lo = pts.min(0) - PAD_MM
    shape = tuple(int(x) for x in ((pts.max(0) + PAD_MM - lo) / variety.MM_PX)[::-1] + 1)
    mask = variety._mask(tris, SIDE, lo, shape)
    rows, cols = np.flatnonzero(mask.any(1)), np.flatnonzero(mask.any(0))
    if not rows.size:
        return 0.0
    box = (rows[-1] - rows[0] + 1) * (cols[-1] - cols[0] + 1)   # Ausdehnung, nicht Zahl belegter Zeilen (Lücken zählen mit)
    return float(mask.sum() / box)


def _side_iou(a, b) -> float:
    both = np.concatenate([a.reshape(-1, 3), b.reshape(-1, 3)])[:, list(SIDE)] * 1000
    lo = both.min(0) - PAD_MM
    shape = tuple(int(x) for x in ((both.max(0) + PAD_MM - lo) / variety.MM_PX)[::-1] + 1)
    ma, mb = variety._mask(a, SIDE, lo, shape), variety._mask(b, SIDE, lo, shape)
    return float((ma & mb).sum() / (ma | mb).sum())


def _forms(parts):
    """Einzelformen: `multi` (ein logisches Teil aus mehreren Formen, modellsprache.md) zählt mit jedem Element."""
    for p in parts:
        if p.get("shape") == "multi":
            yield from _forms(p.get("items") or [])
        else:
            yield p


def detail(parts) -> dict:
    """Detaildichte aus dem Modell, nicht aus dem Bild: wenige Teile, kaum Rundkörper und viele Quader lesen sich blockig
    (Astra-Formstudie 22.11.: rund zehn extrudierte Umrisse; EXTENDED 20–66 Teile)."""
    forms = list(_forms(parts))
    n = len(forms) or 1
    return {"parts": len(parts), "forms": len(forms),
            "round": round(sum(f.get("shape") == "cyl" for f in forms) / n, 2),
            "boxy": round(sum(f.get("shape") == "box" for f in forms) / n, 2),
            "mats": len({p.get("mat") for p in parts}), "trim": sum(p.get("mat") == "trim" for p in parts)}


def clarity(parts) -> dict:
    """Kanon 0.42.2: Profilkanten ab 8 mm, Achstoleranz 2°, sechs häufigste 5°-Richtungen."""
    axis = total = 0.0
    directions = Counter()
    for form in _forms(parts):
        if form.get("shape") != "prof":
            continue
        points = form["pts"]
        for a, b in zip(points, points[1:] + points[:1]):
            df, du = b[0] - a[0], b[1] - a[1]
            length = math.hypot(df, du)
            if length < 8:
                continue
            angle = math.degrees(math.atan2(du, df)) % 180
            total += length
            if min(angle % 90, 90 - angle % 90) < 2:
                axis += length
            directions[round(angle / 5) * 5 % 180] += length
    if not total:
        return {"axis": "–", "dirs": "–"}
    return {"axis": round(axis / total, 2),
            "dirs": round(sum(sorted(directions.values(), reverse=True)[:6]) / total, 2)}


def _row(sid, data, model, author):
    t = variety.triangles(author)
    ext = (t.reshape(-1, 3).max(0) - t.reshape(-1, 3).min(0)) * 1000
    width, length, height = (round(float(v)) for v in ext)
    c = generator.contract(model)
    shares = sorted(extended_lines.role_shares(model["PARTS"]).items(), key=lambda kv: -kv[1])[:2]
    meta = data["META"]
    row = {"id": sid, "name": meta.get("name") or "", "type": meta.get("type_de") or meta.get("type") or "",
           "length": length, "height": height, "width": width, "stretch": round(length / height, 1), "fill": round(_fill(t), 2),
           "sight": "–" if c["sight_line_mm"] is None else f"{c['sight_line_mm']:g}", "accents": len(c["accent_functions"]),
           "hands": "/".join(c["hand_roles"].get(n, "–") for n in ("Socket_Hand", "Socket_SupportHand")),
           "roles": " ".join(f"{r} {s:.0%}" for r, s in shares), **detail(model["PARTS"]), **clarity(model["PARTS"])}
    return row, t


def _neighbour(sid, tris, family) -> str:
    """Nächster Nachbar in der Familie (gemeinsamer Ursprung am Griff, Seitenansicht)."""
    best = max((_side_iou(tris, other), oid) for oid, other in family.items() if oid != sid)
    return f"{best[1]} {best[0]:.2f}"


def _family(snap):
    rows, tris = [], {}
    for item in [*_basic(snap), *_extended(snap)]:
        row, t = _row(*item)
        rows.append(row)
        tris[row["id"]] = t
    return rows, tris


def measure(snap=None) -> list[dict]:
    """Eine Zeile je Modell; Längen in mm (gerundet), Anteile gerundet auf zwei Stellen."""
    rows, tris = _family(Path(snap or ballon.snapshot()))
    for row in rows:
        row["neighbour"] = _neighbour(row["id"], tris[row["id"]], tris)
    return rows


def measure_model(model: dict, sid: str, snap=None, family=None) -> dict:
    """Messzeile einer neuen Waffe (Modell im Vokabular von formgen.extended, wie EA) gegen die ganze Familie – für die Stilprüfung.
    `family` = Ergebnis von `_family(snap)`, wenn der Aufrufer es schon hat (Messung dauert etwa 90 s)."""
    _, tris = family or _family(Path(snap or ballon.snapshot()))
    row, t = _row(sid, model, model, extended_lines.author(model, sid)[0])
    row["neighbour"] = _neighbour(sid, t, tris)
    return row


def klasse(sid: str) -> str:
    """Klasse nach der Typnummer am Ende der Blatt-ID (BA01, EA13, HA04 …); Zuordnung nur aus CLASSES (BALLON-Typen, design-kanon.md › 2)."""
    return next(name for name, nums in CLASSES.items() if sid[-2:] in nums)


def clarity_limits(rows):
    limits = {}
    for key in ("axis", "dirs"):
        values = [r[key] for r in rows if isinstance(r.get(key), (float, int))]
        if values:
            low = round(float(np.percentile(values, 25)), 2) if key == "axis" else min(values)
            limits[key] = low, max(values)
    return limits


def outside(row: dict, rows: list[dict]) -> list[tuple]:
    """Werte einer Zeile außerhalb von min … max ihrer Klasse (BASIC und EXTENDED): (Schlüssel, Wert, min, max); Detaildichte nur auf
    der blockigen Seite (ONLY). Außerhalb ist kein Verbot, braucht aber einen Grund aus dem Konzept (Stilprüfung Nr. 3)."""
    sub = [r for r in rows if r["id"] != row["id"] and klasse(r["id"]) == klasse(row["id"])]
    out = []
    for key in BAND_KEYS:
        vals = [float(r[key]) for r in sub if r[key] != "–"]
        if row[key] == "–" or not vals:
            continue
        low, high = float(row[key]) < min(vals), float(row[key]) > max(vals)
        if (low and ONLY.get(key) != "high") or (high and ONLY.get(key) != "low"):
            out.append((key, row[key], min(vals), max(vals)))
    for key, (minimum, maximum) in clarity_limits(sub).items():
        if isinstance(row.get(key), (float, int)) and row[key] < minimum:
            out.append((key, row[key], minimum, maximum))
    return out


COLUMNS = (("id", "Blatt"), ("name", "Name"), ("type", "Art"), ("length", "Länge mm"), ("height", "Höhe mm"), ("width", "Breite mm"),
           ("stretch", "L/H"), ("fill", "Füllgrad"), ("sight", "Visierlinie mm"), ("accents", "Akzente"), ("hands", "Hände"),
           ("roles", "größte Rollen"), ("neighbour", "Nachbar (Seiten-IoU)"))
DETAIL = (("id", "Blatt"), ("parts", "Teile"), ("forms", "Formen"), ("round", "Rundkörper"), ("boxy", "Quader"), ("mats", "Materialrollen"),
          ("trim", "blanke Kanten"), ("axis", "Achsen"), ("dirs", "Richtungen"))
BAND_KEYS = ("length", "height", "width", "stretch", "fill", "sight", "accents", "parts", "forms", "round", "boxy", "mats", "trim")
LABEL = dict(COLUMNS + DETAIL)
# Detaildichte hat eine Richtung: zu wenig Teile, Formen, Rundkörper, Rollen, Kanten oder zu viele Quader lesen sich blockig, das Gegenteil nicht
ONLY = {"parts": "low", "forms": "low", "round": "low", "mats": "low", "trim": "low", "boxy": "high"}


def _band(rows, key):
    vals = [float(r[key]) if key == "sight" else r[key] for r in rows if r[key] != "–"]
    if not vals:
        return "–"
    return f"{min(vals):g} / {statistics.median(vals):g} / {max(vals):g}"


def _table(rows, columns) -> list[str]:
    out = ["| " + " | ".join(h for _, h in columns) + " |", "|" + "---|" * len(columns)]
    return out + ["| " + " | ".join(str(r[k]) for k, _ in columns) + " |" for r in rows]


def table(rows) -> str:
    out = _table(rows, COLUMNS)
    out += ["", "Detaildichte (Teile und Formen aus `PARTS`, `multi` je Element; Rundkörper und Quader als Anteil der Formen; blanke Kanten =",
            "Teile mit Rolle `trim`; Klarheit der Seitenprofile nach Kantenlänge):", ""] + _table(rows, DETAIL)
    out += ["", "Bänder je Klasse über BASIC und EXTENDED (min / Median / max):", ""]
    for name, nums in CLASSES.items():
        sub = [r for r in rows if r["id"][2:] in nums]
        few = ", nur zwei Modelle: Spanne statt Band" if len(sub) < 3 else ""
        limits = clarity_limits(sub)
        out.append(f"- **{name}** ({len(sub)}{few}): " + " · ".join(f"{LABEL[k]} {_band(sub, k)}" for k in (*BAND_KEYS, "axis", "dirs"))
                   + "".join(f" · Untergrenze {LABEL[k]} {low:g}" for k, (low, _) in limits.items()))
    return "\n".join(out)


def block(text: str) -> str:
    if BEGIN not in text or END not in text:
        raise ValueError(f"Marker {BEGIN} … {END} fehlen")
    return text.split(BEGIN, 1)[1].split(END, 1)[0].strip()


def write(rows, path: Path = DOC) -> bool:
    """Messblock in der Doku ersetzen; True, wenn sich etwas geändert hat."""
    text = path.read_text(encoding="utf-8")
    new = text.split(BEGIN, 1)[0] + BEGIN + "\n" + table(rows) + "\n" + END + text.split(END, 1)[1]
    if new != text:
        path.write_text(new, encoding="utf-8")
    return new != text


def pack(out: Path, images: Path | None = None) -> list[Path]:
    """Beispielpaket für ein fremdes Modell: Kanon, Modellsprache, Musterlösungen, Register, Skins, optional Übersichtsbilder."""
    out.mkdir(parents=True, exist_ok=True)
    files = [DOC, ROOT / "docs/modellsprache.md", ROOT / "docs/kanon-stilpruefung.md", ROOT / "skins.toml",
             ROOT / "data/variants.toml", ROOT / "data/extended_lines.toml"]
    files += [ROOT / "formgen/models/extended" / f"{name}.py" for name in EXAMPLES]
    copied = []
    for f in files:
        sub = out / ("muster" if f.suffix == ".py" else "")
        sub.mkdir(exist_ok=True)
        shutil.copy2(f, sub / f.name)
        copied.append(sub / f.name)
    if images:
        target = out / "bilder"
        shutil.copytree(images, target, dirs_exist_ok=True)
        copied.append(target)
    return copied


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="formgen.kanon", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("messen", help="Proportionen der 34 Modelle messen und in docs/design-kanon.md schreiben")
    m.add_argument("--check", action="store_true", help="nur vergleichen, Exit 1 bei Abweichung")
    z = sub.add_parser("zeile", help="Messzeile eines Modells aus formgen.extended (Kurzname) gegen die Familie")
    z.add_argument("key")
    k = sub.add_parser("paket", help="Beispielpaket für eine neue Generation bündeln")
    k.add_argument("--out", type=Path, required=True)
    k.add_argument("--bilder", type=Path, help="Ordner mit Übersichtsbildern (außerhalb des Repos)")
    a = p.parse_args(argv)
    if a.cmd == "messen":
        rows = measure()
        if a.check:
            same = block(DOC.read_text(encoding="utf-8")) == table(rows).strip()
            print("Kanon-Messung aktuell" if same else "Kanon-Messung veraltet: python -m formgen.kanon messen")
            return 0 if same else 1
        print("geschrieben" if write(rows) else "unverändert", DOC)
        return 0
    if a.cmd == "zeile":
        snap = ballon.snapshot()
        family = _family(snap)
        if a.key in AUTHORED:
            raw, sid = AUTHORED[a.key].make(snap), a.key
        else:
            raw, sid = extended.load(a.key, snap), extended.sheet_id(a.key)
        row = measure_model(raw, sid, snap, family)
        print("\n".join(_table([row], COLUMNS) + [""] + _table([row], DETAIL)))
        off = outside(row, family[0])
        print(f"\nKlasse {klasse(row['id'])}: " + ("alle Werte im Band" if not off else "außerhalb des Bands: " + " · ".join(
            f"{LABEL[k]} {v} (Band {lo:g} … {hi:g})" for k, v, lo, hi in off)))
        return 0
    for f in pack(a.out, a.bilder):
        print(f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
