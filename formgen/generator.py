"""Waffen-Generator: BALLON-Grundform (per Quellhash) + Variantenparameter → v2-Autorenmodell.

Keine eigene Grundgeometrie. Erlaubte Eingriffe (docs/generator.md):
  front  Faktor auf die Vorderlänge Socket_Hand → Socket_Muzzle; Schnitt zwischen Stützhand und Mündung
  rear   Faktor auf die Hinterlänge hinter Socket_Hand; nur mit Baugruppe `stock`, Schnitt im Schaft
  drop   Teil-ID-Muster (fnmatch); Teile mit Ankern oder Kindteilen bleiben (Bericht nennt sie)
Ein Schnitt `at` trennt: Teile ganz jenseits werden verschoben, lange Teile über dem Schnitt (Gehäuse, Lauf,
Schiene) gedehnt bzw. gestaucht, kurze Teile werden nie verzerrt. Gestaucht wird höchstens bis zur freien Zone
hinter dem Schnitt; Begrenzungen stehen im Bericht. Alle Zahlen in mm im BALLON-Rahmen (f vorn, u oben, x links).
"""
from __future__ import annotations

import copy
import fnmatch

from . import ballon, geom, model

SHORT_MM = 60.0     # Teile kürzer als das werden nie gedehnt (Annahme: Detailteile behalten ihre Form)
GAP_MM = 1.0        # Restabstand beim Stauchen (SEAM aus BALLON common.SEAM)
POINT_KEYS = ("pivot", "tip", "nock")
FRONT_WINDOW = (0.25, 0.75)   # Annahme: Schnitt in der mittleren Hälfte Stützhand→Mündung, weg von Gehäuse- und Mündungsdetails
STOCK_MARGIN = 0.2            # Annahme: Schnitt nicht in den äußeren 20 % des Schafts (Schulterstütze, Gehäuseanschluss)


# ------------------------------------------------------------------ f-Koordinaten je Form

def _f_values(p):
    s = p["shape"]
    if s in ("prof", "plan"):
        return [q[0] for q in p["pts"]]
    if s in ("box", "frame", "xbox"):
        return [p["f0"], p["f1"]]
    if s == "cyl":
        return [p["a0"], p["a1"]] if p["axis"] == "f" else [p["c"][0]]
    raise ValueError(f"{p['id']}: Form {s} im Generator nicht unterstützt")


def _map_f(p, fn):
    s = p["shape"]
    if s in ("prof", "plan"):
        p["pts"] = [(fn(q[0]), *q[1:]) for q in p["pts"]]
    elif s in ("box", "frame", "xbox"):
        p["f0"], p["f1"] = fn(p["f0"]), fn(p["f1"])
    elif p["axis"] == "f":
        p["a0"], p["a1"] = fn(p["a0"]), fn(p["a1"])
    else:
        p["c"] = (fn(p["c"][0]), *p["c"][1:])
    move = p.get("move")
    if move:
        for key in POINT_KEYS:
            if move.get(key) is not None:
                move[key] = (fn(move[key][0]), *move[key][1:])
        if move.get("expect"):
            point, direction = move["expect"]
            move["expect"] = ((fn(point[0]), *point[1:]), direction)


def _extent(p):
    v = _f_values(p)
    return min(v), max(v)


def _mirror(model):
    for p in model["PARTS"]:
        _map_f(p, lambda f: -f)
    for a in model["ANCHORS"].values():
        a["at"] = (-a["at"][0], *a["at"][1:])


# ------------------------------------------------------------------ Schnitt und Dehnung (vorwärts; hinten = gespiegelt)

def _classify(parts, at):
    far, cross, near = [], [], []
    for p in parts:
        lo, hi = _extent(p)
        if lo >= at:
            far.append(p)
        elif hi > at and hi - lo >= SHORT_MM:
            cross.append(p)
        else:
            near.append(p)
    return far, cross, near


def _room(parts, at):
    """Largest safe shortening at `at`: free zone behind the cut for crossing parts and far parts."""
    far, cross, near = _classify(parts, at)
    room = float("inf")
    for p in cross:
        beyond = [f for f in _f_values(p) if f > at]
        room = min(room, min(beyond) - at)
    near_hi = max((_extent(p)[1] for p in near), default=-float("inf"))
    for p in far:
        room = min(room, _extent(p)[0] - max(near_hi, at))
    return room - GAP_MM


def _choose_cut(parts, lo, hi, shortening):
    """Cut in [lo, hi]: no short part crossed, fewest parts stretched, most free room when shortening, then centred."""
    best = None
    steps = 48
    for i in range(steps + 1):
        at = lo + (hi - lo) * i / steps
        crossed = [p for p in parts if _extent(p)[0] < at < _extent(p)[1]]
        bad = sum(1 for p in crossed if _extent(p)[1] - _extent(p)[0] < SHORT_MM)
        room = _room(parts, at) if shortening else 0.0
        # erst keine kurzen Teile kreuzen, dann möglichst wenige Teile dehnen (Leitmerkmale wie Schildflügel bleiben), dann Platz
        score = (bad, len(crossed), -room, abs(at - (lo + hi) / 2))
        if best is None or score < best[0]:
            best = (score, at, room)
    return best[1], best[2]


def _stretch(model, at, delta):
    far, cross, near = _classify(model["PARTS"], at)
    moved = {p["id"]: "translate" for p in far} | {p["id"]: "stretch" for p in cross}
    for p in far:
        _map_f(p, lambda f: f + delta)
    for p in cross:
        _map_f(p, lambda f: f + delta if f > at else f)
    for a in model["ANCHORS"].values():
        how = moved.get(a.get("part"))
        if how == "translate" or (how == "stretch" and a["at"][0] > at):
            a["at"] = (a["at"][0] + delta, *a["at"][1:])
    return sorted(p["id"] for p in far), sorted(p["id"] for p in cross)


def _anchor_f(model, name):
    a = model["ANCHORS"].get(name)
    return a["at"][0] if a else None


def stretch_front(model, factor):
    hand, muzzle = _anchor_f(model, "Socket_Hand"), _anchor_f(model, "Socket_Muzzle")
    support = _anchor_f(model, "Socket_SupportHand")
    if muzzle - hand < 100:
        return {"op": "front", "factor": factor, "skipped": "keine Längsachse (Socket_Muzzle < 100 mm vor Socket_Hand)"}
    start = support if support is not None and hand < support < muzzle else hand
    lo, hi = start + FRONT_WINDOW[0] * (muzzle - start), start + FRONT_WINDOW[1] * (muzzle - start)
    want = (factor - 1.0) * (muzzle - hand)
    at, room = _choose_cut(model["PARTS"], lo, hi, want < 0)
    delta = want if want >= 0 else -min(-want, max(room, 0.0))
    far, cross = _stretch(model, at, delta)
    return {"op": "front", "factor": factor, "anchors": ["Socket_Hand", "Socket_Muzzle"] + (["Socket_SupportHand"] if support is not None else []),
            "cut_f_mm": round(at, 3), "wanted_mm": round(want, 3), "delta_mm": round(delta, 3),
            "limited": abs(delta - want) > 1e-9, "translated": far, "stretched": cross}


def stretch_rear(model, factor):
    stock = [p for p in model["PARTS"] if p["asm"] == "stock"]
    if not stock:
        return {"op": "rear", "factor": factor, "skipped": "keine Baugruppe stock (kein Schaft)"}
    hand = _anchor_f(model, "Socket_Hand")
    lo = min(_extent(p)[0] for p in stock); hi = min(max(_extent(p)[1] for p in stock), hand)
    rear = min(_extent(p)[0] for p in model["PARTS"])
    want = (factor - 1.0) * (hand - rear)
    _mirror(model)
    try:
        at, room = _choose_cut(model["PARTS"], -hi + STOCK_MARGIN * (hi - lo), -lo - STOCK_MARGIN * (hi - lo), want < 0)
        delta = want if want >= 0 else -min(-want, max(room, 0.0))
        far, cross = _stretch(model, at, delta)
    finally:
        _mirror(model)
    return {"op": "rear", "factor": factor, "anchors": ["Socket_Hand"], "cut_f_mm": round(-at, 3),
            "wanted_mm": round(want, 3), "delta_mm": round(delta, 3), "limited": abs(delta - want) > 1e-9,
            "translated": far, "stretched": cross}


def drop(model, patterns):
    keep_ids = {a["part"] for a in model["ANCHORS"].values()} | {p.get("parent_part") for p in model["PARTS"]}
    dropped, protected = [], []
    for p in list(model["PARTS"]):
        if any(fnmatch.fnmatchcase(p["id"], pat) for pat in patterns):
            (protected if p["id"] in keep_ids else dropped).append(p["id"])
    model["PARTS"] = [p for p in model["PARTS"] if p["id"] not in set(dropped)]
    return {"op": "drop", "patterns": list(patterns), "dropped": dropped, "protected": protected}


# ------------------------------------------------------------------ BALLON → v2-Autorenmodell

def adapt(data):
    """Return an editable copy plus the list of documented adaptations of BALLON data."""
    model = {k: copy.deepcopy(data[k]) for k in ("META", "PARTS", "ASSEMBLIES", "ANCHORS")}
    notes = []
    for p in model["PARTS"]:
        if p["shape"] == "cyl" and p.get("r_in") and p["r_in"] >= min(p["r"], p.get("r1", p["r"])):
            r, r1 = p["r"], p.get("r1", p["r"])
            # BALLON skaliert r_in an a1 mit r1/r; ein r_in ≥ r am kleinen Ende stülpt die Wand um. Annahme: r_in gilt
            # am großen Ende (Wand r_obj − 3 mm wie beim Objektivglas), also r_in(a0) = r_in·r/r1.
            new = p["r_in"] * r / r1 if r1 > r else p["r_in"] * r1 / r
            notes.append({"part": p["id"], "kind": "Annahme", "field": "r_in", "ballon": p["r_in"], "v2": round(new, 6),
                          "reason": "BALLON-Hohlkegel mit r_in ≥ Außenradius stülpt die Wand um; r_in auf das große Ende bezogen"})
            p["r_in"] = new
    return model, notes


def _finish(model, notes):
    used = {p["asm"] for p in model["PARTS"]}
    empty = [a["id"] for a in model["ASSEMBLIES"] if a["id"] not in used]
    if empty:
        notes.append({"kind": "Annahme", "field": "assemblies", "removed": empty,
                      "reason": "leere Baugruppe ohne Teile (in BALLON nur deklariert)"})
    model["ASSEMBLIES"] = [a for a in model["ASSEMBLIES"] if a["id"] in used]
    ids = {p["id"] for p in model["PARTS"]}
    missing = sorted(n for n, a in model["ANCHORS"].items() if a["part"] not in ids)
    if missing:
        raise ValueError(f"Anker verweisen auf entfernte Teile: {missing}")


def generate(data, variant, num, source):
    """BALLON data of one type + register entry → (v2 author model, generator report)."""
    model, notes = adapt(data)
    params = variant.get("params", {})
    ops = []
    if "drop" in params:
        ops.append(drop(model, params["drop"]))
    if "front" in params:
        ops.append(stretch_front(model, params["front"]))
    if "rear" in params:
        ops.append(stretch_rear(model, params["rear"]))
    _finish(model, notes)
    meta = model["META"]
    sid = f"B{variant['letter']}{num}"
    # Commit bewusst nicht im Geometriedokument: gleicher Quellhash = gleiches Ergebnis (Commit steht im Blatt-Spec)
    provenance = {"kind": "Vorgabe", "source": (
        f"BALLON {meta['id']} (Quellhash {source['source_sha256'][:12]}); "
        f"Variante {variant['letter']} „{variant['name']}“ aus data/variants.toml; Maße in mm wie BALLON")}
    info = {"id": sid, "kind": "weapon", "name_de": f"{meta['type_de']} · {variant['name']}",
            "name_en": f"{meta['type_en']} · {variant['name']}",
            "summary": f"{meta.get('summary', '')} Linie {variant['letter']} „{variant['name']}“: {variant['idea']}",
            "provenance": provenance,
            "facts": [["Variante", f"{variant['letter']} · {variant['name']}"],
                      ["Grundform", f"{meta['id']} „{meta['name']}“"],
                      ["BALLON-Quellhash", source["source_sha256"][:12]],
                      ["Skin", variant.get("skin", "standard")]]}
    parts = []
    for p in model["PARTS"]:
        q = {k: v for k, v in p.items() if k not in ("en", "func", "attach", "iface")}
        q["name_en"] = p.get("en")
        parts.append(q)
    author = {"INFO": info, "PARTS": parts, "ASSEMBLIES": model["ASSEMBLIES"], "ANCHORS": model["ANCHORS"]}
    report = {"variant": {k: variant[k] for k in ("letter", "name", "idea", "since", "skin", "params")},
              "type": {k: meta.get(k) for k in ("id", "num", "type", "type_de", "type_en", "name", "nick")},
              "ballon": source, "ops": ops, "adaptations": notes}
    return author, report


def build(variant, num, snap=None, source=None):
    snap = snap or ballon.snapshot()
    source = source or ballon.source(snap, num)
    return generate(ballon.load(snap, num), variant, num, source)


def evaluate(data, variant, num, source, ballon_dims=None, **options):
    """Generate and evaluate one sheet; the geometry stage's code closure starts here (geom, model, ballon)."""
    author, report = generate(data, variant, num, source)
    report["ballon_dimensions_mm"] = ballon_dims
    document = geom.evaluate(model.normalize(author), **options)
    document["generator"] = report
    return document
