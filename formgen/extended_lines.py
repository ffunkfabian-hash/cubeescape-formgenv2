"""EXTENDED-Linien und Finish (0.38 „Foundry“): Gestaltungslinien über allen 17 EXTENDED-Modellen, dazu freie Skins.

Eine Linie ist wie bei BASIC ein Eintrag im eigenen Register `data/extended_lines.toml` (Kennbuchstabe, englischer Name, Idee, Skin,
Parameter). Blatt-ID `E<Linie><NN>` mit NN = EXTENDED-Nummer; Linie A ist das EXTENDED-Modell selbst (EA01 … EA17, Nutzerentscheid
23.11.2026). Die Linien nutzen die Eingriffe des BASIC-Generators (`formgen.generator`), aber nur die, die eine eigene Silhouette
erhalten (OPS): Strecken, Mündung, Magazin, Leuchtstreifen, Weglassen, Visiertausch. Keine Design-Serie (Verkleidung über der Form),
kein Schaft- oder Grifftausch (Nutzerentscheid 25.11.2026: eigene EXTENDED-Linien, die Form jedes Modells bleibt erkennbar).

Finish = ein Skin aus `skins.toml`, frei auf jedes Blatt gelegt, ohne neue ID und ohne Formänderung (Rollenfarben, Abnutzung, Muster).
Die Linie bringt ihren eigenen Skin mit; `--finish` ersetzt ihn nur für Vorschau oder Render.

  python -m formgen.extended_lines list
  python -m formgen.extended_lines new <Buchstabe> "<Name>" "<Idee>" --skin <skin> --param front=[1.1,1.2] …
  python -m formgen.extended_lines sketch --out <Ordner> [--view iso] [--finish <skin>]    # Rasterbogen 17 × Linien
  python -m formgen.extended_lines finishes --out <Ordner> [--key e12]                    # ein Modell in allen Finishes

Vorschau ohne Blender über den v2-Raster (`geom.evaluate` + `raster.render`); AAA-Bilder über `tools/extended_render.py --line`.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
import re
from pathlib import Path
import sys
import tomllib

from . import ballon, extended, generator, variants

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data/extended_lines.toml"
SKINS = ROOT / "skins.toml"
SCHEMA = 1
# Eingriffe, die die eigene Silhouette erhalten (Reihenfolge wie generator._apply); Grenzen wie im BASIC-Register (variants.PARAMS)
OPS = ("sight", "mag", "muzzle", "muzzle_r", "glow", "drop", "front", "rear", "limbs")
KEYS = tuple(f"e{n:02d}" for n in range(1, 18))
SHEET = re.compile(r"E([A-HJ-NP-Z])(\d\d)")
CACHE = Path.home() / "Library/Caches/CubeEscapeFormgen2/extended-lines"


class LineError(ValueError):
    pass


def skins() -> dict:
    """Waffen-Skins aus skins.toml (Roboter-Skins ausgenommen); das sind zugleich die Finishes."""
    with SKINS.open("rb") as stream:
        return {k: v for k, v in tomllib.load(stream)["skins"].items() if not v.get("robot")}


def check(entries: list[dict], known: set[str] | None = None) -> None:
    """Namensregel wie BASIC (variants.check), dazu: Buchstabe nicht A (A = EXTENDED-Modell), nur OPS, Name nicht schon eine BASIC-Linie."""
    try:
        variants.check([{**e, "params": {k: v for k, v in e.get("params", {}).items() if k in OPS}} for e in entries], known)
    except variants.VariantError as error:
        raise LineError(str(error)) from None
    basic = {v["name"].lower() for v in variants.load()}
    for e in entries:
        if e["letter"] == "A":
            raise LineError("A ist das EXTENDED-Modell selbst (EA01 … EA17), keine Linie")
        if e["name"].lower() in basic:
            raise LineError(f"{e['letter']}: Name {e['name']!r} ist schon eine BASIC-Linie")
        extra = sorted(set(e.get("params", {})) - set(OPS))
        if extra:
            raise LineError(f"{e['letter']}: Parameter {extra} nicht für EXTENDED-Linien (nur {', '.join(OPS)})")


def load(path: Path = REGISTRY) -> list[dict]:
    with Path(path).open("rb") as stream:
        data = tomllib.load(stream)
    if data.get("schema") != SCHEMA:
        raise LineError(f"EXTENDED-Linienregister: schema {SCHEMA} erwartet")
    entries = data.get("lines", [])
    check(entries, set(skins()))
    for e in entries:
        e.setdefault("skin", "standard"); e.setdefault("params", {})
    return entries


def sheet_id(letter: str, key: str) -> str:
    return f"E{letter}{key[1:]}"


def parse_sheet(sid: str) -> tuple[str, str]:
    m = SHEET.fullmatch(sid)
    if not m or f"e{m.group(2)}" not in KEYS:
        raise LineError(f"Ungültige Blatt-ID {sid!r} (Muster EA01 … EZ17)")
    return m.group(1), f"e{m.group(2)}"


def sheets(entries: list[dict] | None = None) -> dict[str, dict]:
    """Blatt-ID → {line, key} für alle Linien × Modelle, in Registerreihenfolge (ohne Linie A)."""
    entries = load() if entries is None else entries
    return {sheet_id(e["letter"], k): {"line": e, "key": k} for e in entries for k in KEYS}


def seed(sid: str) -> str:
    """Eigener Seed-Raum (nicht der von BASIC): EB01 zieht unabhängig von BB01."""
    letter, _ = parse_sheet(sid)
    return hashlib.sha256(f"formgenv2-extended-line|{sid}|{letter}".encode()).hexdigest()[:16]


def resolve(params: dict, sid: str) -> tuple[dict, dict]:
    """Wie variants.resolve, mit eigenem Seed; die Präzisionsregel für Zielfernrohre gilt für die BASIC-Nummer des Modells."""
    s, (_, key) = seed(sid), parse_sheet(sid)
    values, draws = {}, {}
    for name, value in params.items():
        if name == "drop":
            values[name] = list(value)
        elif name in variants.PARAMS or name in variants.INTS:
            if isinstance(value, list):
                lo, hi = value
                u = variants._uniform(s, name)
                value = lo + int(u * (hi - lo + 1)) if name in variants.INTS else round(lo + u * (hi - lo), 3)
                draws[name] = value
            values[name] = value
        else:
            pool = variants.allowed(name, value if isinstance(value, list) else [value], key[1:])
            pick = pool[int(variants._uniform(s, name) * len(pool))] if pool else None
            if isinstance(value, list) and len(value) > 1:
                draws[name] = pick
            values[name] = pick
    return values, draws


SEE_THROUGH = ("glass", "sight_line")   # Rollenpräfixe: Glas, Absehen und Sichtlinie sitzen frei im Visierrahmen (schon in EA06)


def pieces(parts) -> int:
    """Zusammenhängende Gruppen ohne durchsichtige Visierteile (extended.components über Hüllquader, 0,5 mm Toleranz)."""
    solid = [p for p in parts if not str(p.get("mat", "")).startswith(SEE_THROUGH) and not str(p.get("mat", "")).startswith("reticle")]
    return len(extended.components(solid))


def _tubes(parts, at):
    """Kurze Rohre entlang der Laufachse, die der Schnitt kreuzt: ein Zylinder bleibt beim Dehnen in seiner Achse formgleich."""
    out = set()
    for p in parts:
        lo, hi = generator._extent(p)
        if lo < at < hi and hi - lo < generator.SHORT_MM and p.get("shape") == "cyl" and p.get("axis") == "f":
            out.add(p["id"])
    return out


def stretch_front(model, factor):
    """Wie generator.stretch_front, aber kurze Rohre über dem Schnitt (z. B. die Mündung der MP EA06) werden mitgedehnt statt
    stehen gelassen; sonst wandert ein Teil davor allein nach vorn (EB06, 0.38)."""
    op = generator.stretch_front(copy.deepcopy(model), factor)   # nur zum Finden des Schnitts, Modell bleibt unberührt
    if "skipped" in op:
        return op
    force = _tubes(model["PARTS"], op["cut_f_mm"])
    if not force:
        return generator.stretch_front(model, factor)
    far, cross = generator._stretch(model, op["cut_f_mm"], op["delta_mm"], force=force)
    return {**op, "translated": far, "stretched": cross, "tubes": sorted(force)}


def _run(data, params, key, snap):
    model, notes = generator.adapt(data)
    # Jedes Teil einzeln kopieren: EXTENDED-Module teilen Schnittkörper zwischen Teilen (EA12: Schale, Unterschale und Kolbenkappe dieselben
    # Profil-Dicts); ein gemeinsamer deepcopy erhält das Teilen, und der Generator verschöbe einen Schnitt je Teil erneut (Finne am Heck, EH12).
    model["PARTS"] = [copy.deepcopy(p) for p in model["PARTS"]]
    before = generator.contract(model)
    kit = generator._kit(snap)
    early = {k: v for k, v in params.items() if k not in ("front", "rear", "limbs")}
    ops, added = generator._apply(model, early, key[1:], kit, notes)
    if "front" in params:   # gleiche Reihenfolge wie generator._apply: … drop, front, rear, limbs
        ops.append(stretch_front(model, params["front"]))
    late = {k: params[k] for k in ("rear", "limbs") if k in params}
    if late:
        more, extra = generator._apply(model, late, key[1:], kit, notes)
        ops += more; added |= extra
    generator._keep_accents(model, before, added, notes)
    generator._finish(model, notes)
    return model, notes, ops, before


def vary(sid: str, snap: Path | None = None, entries: list[dict] | None = None):
    """Blatt → (Modell im BALLON-Vokabular, Laufbericht). Linie A gibt das EXTENDED-Modell unverändert zurück.

    Zusammenhalt (0.38): Ein Eingriff, der das Modell in mehr Gruppen zerlegt als die Grundform, entfällt für dieses Modell (Bericht
    `withdrawn`). Anlass EB06: an der kurzen MP kreuzt jeder Frontschnitt die kurze Mündung, die Krone wanderte allein nach vorn.
    Rückzug in fester Reihenfolge, zuletzt angewendete Eingriffe zuerst; der BASIC-Generator bleibt unverändert."""
    snap = Path(snap or ballon.snapshot())
    letter, key = parse_sheet(sid)
    data = extended.load(key, snap)
    if letter == "A":
        return data, {"sid": sid, "params": {}, "draws": {}, "ops": [], "notes": [], "skin": "standard", "withdrawn": []}
    line = next((e for e in (load() if entries is None else entries) if e["letter"] == letter), None)
    if line is None:
        raise LineError(f"{sid}: Linie {letter} nicht im Register")
    params, draws = resolve(line["params"], sid)
    goal, withdrawn = pieces(data["PARTS"]), []
    model, notes, ops, before = _run(data, params, key, snap)
    for name in reversed(OPS):
        if pieces(model["PARTS"]) <= goal:
            break
        if name in params:
            withdrawn.append({"op": name, "value": params.pop(name), "reason": "zerlegt das Modell (Teil ohne Anschluss)"})
            model, notes, ops, before = _run(data, params, key, snap)
    if pieces(model["PARTS"]) > goal:
        raise LineError(f"{sid}: Modell zerfällt auch ohne Eingriffe {[w['op'] for w in withdrawn]}")
    for k in extended.FIELDS:   # Felder, die der Generator nicht bearbeitet (ACTIONS, EJECT, HERO …), bleiben beim Modell
        if k in data and k not in model:
            model[k] = copy.deepcopy(data[k])
    model["META"] = {**model["META"], "line": letter, "line_name": line["name"], "sheet": sid}
    return model, {"sid": sid, "params": params, "draws": draws, "ops": ops, "notes": notes, "skin": line["skin"],
                   "withdrawn": withdrawn, "contract": {"base": before, "line": generator.contract(model)}}


# ------------------------------------------------------------------ Vorschau (v2-Raster, ohne Blender)

def author(model: dict, sid: str) -> tuple[dict, list[dict]]:
    """BALLON-Vokabular → v2-Autorenmodell für den Raster. Zwei Anpassungen nur für diesen Weg (das Modell für Blender bleibt):
    Anker mit (f, u) bekommen x = 0 (BALLON-Konvention), ein Rahmen mit r_in = halbe Öffnung wird um 0,05 mm enger gerundet."""
    notes, anchors, parts = [], {}, []
    for name, a in model["ANCHORS"].items():
        at = list(a["at"])
        if len(at) == 2:
            at.append(0.0)
            notes.append({"kind": "Annahme", "field": f"ANCHORS.{name}", "reason": "BALLON-Anker (f, u) liegt auf x = 0"})
        anchors[name] = {**a, "at": at}
    for p in model["PARTS"]:
        q = {k: v for k, v in p.items() if k not in ("en", "func", "attach", "iface")}
        q["name_en"] = p.get("en")
        if _round_frames(q):
            notes.append({"kind": "Annahme", "field": f"{p['id']}.r_in", "reason": "v2-Geometrie braucht r_in < halbe Öffnung"})
        parts.append(q)
    meta = model["META"]
    info = {"id": sid, "kind": "weapon", "name_de": f"{meta.get('type_de', meta['id'])} · {meta.get('line_name', meta['name'])}",
            "name_en": f"{meta.get('type_en', meta['id'])} · {meta.get('line_name', meta['name'])}",
            "summary": meta.get("summary", ""), "facts": [["Blatt", sid]],
            "provenance": {"kind": "Vorgabe", "source": f"{meta['id']} „{meta['name']}“ (formgen/models/extended), Linie aus data/extended_lines.toml"}}
    used = {p["asm"] for p in parts}   # EA08 deklariert `support` ohne Teile (BALLON erlaubt das, das v2-Modell nicht)
    return {"INFO": info, "PARTS": parts, "ASSEMBLIES": [a for a in model["ASSEMBLIES"] if a["id"] in used], "ANCHORS": anchors}, notes


def _round_frames(q) -> bool:
    """Rahmen (auch in `multi`) mit r_in ≥ halber Öffnung 0,05 mm enger runden; True, wenn etwas geändert wurde."""
    hit = False
    if q.get("shape") == "multi":
        q["items"] = [dict(i) for i in q["items"]]
        for i in q["items"]:
            hit = _round_frames(i) or hit
    elif q.get("shape") == "frame" and q.get("r_in", 0) >= min(q["iw"], q["ih"]) / 2:
        q["r_in"] = min(q["iw"], q["ih"]) / 2 - 0.05
        hit = True
    return hit


def _key(*parts) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def preview(sid: str, view: str = "iso", skin: str | None = None, size=(720, 480), snap=None, cache: Path | None = CACHE,
            entries=None):
    """Rasterbild eines Blatts (PIL). skin None = Skin der Linie (A: standard). Cache nach Modell, Skin, Ansicht und Codeständen."""
    from PIL import Image
    from . import build, geom, model as mdl, raster, versions
    snap = Path(snap or ballon.snapshot())
    data, run = vary(sid, snap, entries)
    skin = skin or run["skin"]
    doc, _ = author(data, sid)
    code = build.source_hashes(Path(raster.__file__))
    with SKINS.open("rb") as stream:   # nur, was die Farbe bestimmt: Rollen und der gewählte Skin (ein neuer Skin entwertet nichts)
        palette = tomllib.load(stream)
    key = _key(doc, view, skin, list(size), versions.MODEL, versions.GEOM, versions.RASTER, code, palette["roles"],
               palette["skins"][skin])
    path = cache / f"{sid}_{view}_{skin}_{key[:16]}.png" if cache else None
    if path and path.exists():
        return Image.open(path).convert("RGB")
    image = raster.render(geom.evaluate(mdl.normalize(doc)), view, size[0], size[1], skin=skin).convert("RGB")
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path)
    return image


def _font(size):
    from PIL import ImageFont
    path = ROOT / "formgen/assets/fonts/Barlow-SemiBold.ttf"
    return ImageFont.truetype(str(path), size)


def sketch(out: Path, view="iso", finish=None, keys=KEYS, letters=None, tile=(300, 200)) -> Path:
    """Rasterbogen: Zeilen = Modelle, Spalten = A + Linien (Skin der Linie oder ein Finish für alle)."""
    from PIL import Image, ImageDraw
    entries = load()
    cols = [("A", "EXTENDED")] + [(e["letter"], e["name"]) for e in entries if not letters or e["letter"] in letters]
    _warm([(sheet_id(letter, key), view, finish, (tile[0] * 2, tile[1] * 2)) for key in keys for letter, _ in cols])
    lw, top = 150, 70
    sheet = Image.new("RGB", (lw + len(cols) * tile[0], top + len(keys) * tile[1]), "#808080")
    d = ImageDraw.Draw(sheet)
    for c, (letter, name) in enumerate(cols):
        skin = finish or ("standard" if letter == "A" else next(e["skin"] for e in entries if e["letter"] == letter))
        d.text((lw + c * tile[0] + 6, 8), f"{letter} · {name}", fill="#111317", font=_font(22))
        d.text((lw + c * tile[0] + 6, 38), skin, fill="#2b2e33", font=_font(16))
    for r, key in enumerate(keys):
        meta = extended.load(key)["META"]
        d.text((8, top + r * tile[1] + tile[1] // 2 - 20), f"{key[1:]} {meta['name']}", fill="#111317", font=_font(20))
        for c, (letter, _) in enumerate(cols):
            im = preview(sheet_id(letter, key), view, finish, (tile[0] * 2, tile[1] * 2), entries=entries)
            sheet.paste(im.resize(tile, Image.LANCZOS), (lw + c * tile[0], top + r * tile[1]))
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"linien_{view}{'_' + finish if finish else ''}.png"
    sheet.save(path)
    return path


def _one(job):
    preview(*job)
    return job[0]


def _warm(jobs, workers=None):
    """Vorschauen parallel in den Cache legen (Prozesse; der Raster ist reines Python, eine Vorschau braucht 5–13 s)."""
    import multiprocessing as mp
    import os
    workers = workers or max(1, min(8, (os.cpu_count() or 2) - 2))
    with mp.get_context("spawn").Pool(workers) as pool:
        for i, sid in enumerate(pool.imap_unordered(_one, jobs), 1):
            if i % 20 == 0 or i == len(jobs):
                print(f"Vorschau {i}/{len(jobs)} ({sid})", flush=True)


def finishes(out: Path, key="e12", view="iso", tile=(360, 240)) -> Path:
    """Ein Modell (Linie A) in allen Finishes."""
    from PIL import Image, ImageDraw
    names = list(skins())
    _warm([(sheet_id("A", key), view, s, (tile[0] * 2, tile[1] * 2)) for s in names])
    cols = 4
    rows = (len(names) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tile[0], rows * (tile[1] + 30)), "#808080")
    d = ImageDraw.Draw(sheet)
    for i, s in enumerate(names):
        x, y = (i % cols) * tile[0], (i // cols) * (tile[1] + 30)
        d.text((x + 6, y + 4), s, fill="#111317", font=_font(20))
        sheet.paste(preview(sheet_id("A", key), view, s, (tile[0] * 2, tile[1] * 2)).resize(tile, Image.LANCZOS), (x, y + 30))
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"finishes_{key}_{view}.png"
    sheet.save(path)
    return path


# ------------------------------------------------------------------ Register

def new(letter, name, idea, since, skin="standard", params=None, path: Path = REGISTRY) -> dict:
    """Linie eintragen (einzige Eintragsstelle); prüft das ganze Register mit dem neuen Eintrag, bevor geschrieben wird."""
    path = Path(path)
    text = path.read_text() if path.exists() else f"schema = {SCHEMA}\n"
    entries = tomllib.loads(text).get("lines", [])
    entry = {"letter": letter, "name": name, "idea": idea, "since": since, "skin": skin, "params": params or {}}
    check(entries + [entry], set(skins()))
    block = (f'\n[[lines]]\nletter = {variants._toml(letter)}\nname = {variants._toml(name)}\nidea = {variants._toml(idea)}\n'
             f'since = {variants._toml(since)}\nskin = {variants._toml(skin)}\n[lines.params]\n'
             + "".join(f"{k} = {variants._toml(v)}\n" for k, v in (params or {}).items()))
    candidate = text.rstrip("\n") + "\n" + block
    if tomllib.loads(candidate)["lines"][-1] != entry:
        raise LineError("TOML-Block liest sich nicht zurück wie der Eintrag")
    path.write_text(candidate)
    return entry


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    n = sub.add_parser("new")
    n.add_argument("letter"); n.add_argument("name"); n.add_argument("idea")
    n.add_argument("--since", default=None); n.add_argument("--skin", default="standard")
    n.add_argument("--param", action="append", default=[], metavar="KEY=JSON")
    s = sub.add_parser("sketch")
    s.add_argument("--out", type=Path, required=True); s.add_argument("--view", default="iso"); s.add_argument("--finish")
    s.add_argument("--letters"); s.add_argument("--keys")
    f = sub.add_parser("finishes")
    f.add_argument("--out", type=Path, required=True); f.add_argument("--key", default="e12"); f.add_argument("--view", default="iso")
    a = p.parse_args(argv)
    if a.cmd == "list":
        for e in load():
            print(f"{e['letter']}  {e['name']:<16} {e['skin']:<10} {json.dumps(e['params'], ensure_ascii=False)}")
        return 0
    if a.cmd == "new":
        from . import __version__
        try:
            params = {k: json.loads(v) for k, v in (item.split("=", 1) for item in a.param)}
            e = new(a.letter, a.name, a.idea, a.since or ".".join(__version__.split(".")[:2]), a.skin, params)
        except (LineError, ValueError) as error:
            print(f"abgelehnt: {error}", file=sys.stderr)
            return 1
        print(f"eingetragen: {e['letter']} · {e['name']} → Blätter E{e['letter']}01 … E{e['letter']}17")
        return 0
    if a.cmd == "sketch":
        keys = tuple(f"e{k}" for k in a.keys.split(",")) if a.keys else KEYS
        print(sketch(a.out, a.view, a.finish, keys, a.letters))
        return 0
    print(finishes(a.out, a.key, a.view))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# ------------------------------------------------------------------ Rollentest (0.38): Flächenanteil je Rolle und Kontrast je Skin

def role_shares(parts, frame=None) -> dict[str, float]:
    """Flächenanteil je Materialrolle in der linken Seitenansicht (Näherung wie extended.side_mask). Malerverfahren: Teile nach
    ihrer äußersten Lage zur Kamera (größtes x, links = +x) gezeichnet, das kameranächste zuletzt; Schrift zählt nicht."""
    import numpy as np
    from PIL import Image, ImageDraw
    lo, size = (frame or {}).get("lo", (-900.0, -600.0)), (frame or {}).get("size", (3000, 1500))
    roles = sorted({p.get("mat", "shell") for p in parts})
    im = Image.new("L", size, 0)
    d = ImageDraw.Draw(im)
    order = sorted((p for p in parts if extended.bounds(p)), key=lambda p: extended.bounds(p)[1][2])
    for p in order:
        idx = roles.index(p.get("mat", "shell")) + 1
        for poly in extended._side_polys(p):
            if len(poly) >= 3:
                d.polygon([((f - lo[0]), size[1] - 1 - (u - lo[1])) for f, u in poly], fill=idx)
    a = np.asarray(im)
    total = int((a > 0).sum())
    return {r: round(int((a == i + 1).sum()) / total, 4) for i, r in enumerate(roles) if (a == i + 1).any()}


def _lab(hex_):
    rgb = [int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    x = (0.4124 * lin[0] + 0.3576 * lin[1] + 0.1805 * lin[2]) / 0.95047
    y = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    z = (0.0193 * lin[0] + 0.1192 * lin[1] + 0.9505 * lin[2]) / 1.08883
    f = [t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116 for t in (x, y, z)]
    return 116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])


def delta_e(a: str, b: str) -> float:
    """CIE76-Farbabstand zweier Hexfarben (sRGB, D65)."""
    return round(sum((p - q) ** 2 for p, q in zip(_lab(a), _lab(b))) ** 0.5, 2)


def role_color(role: str, skin: str) -> str:
    with SKINS.open("rb") as stream:
        data = tomllib.load(stream)
    style = data["skins"][skin]
    if style.get("pattern") and role == "shell":
        return style["pattern"][0]
    return style.get("roles", {}).get(role) or data["roles"].get(role, data["roles"]["shell"])["color"]
