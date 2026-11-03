"""Waffen-Generator: BALLON-Grundform (per Quellhash) + Variantenparameter → v2-Autorenmodell.

Keine eigene Grundgeometrie. Grundform ist der neueste BALLON-Spielpilot des Typs (Linie mit `base = "pilot"`, ab 0.6 alle),
ohne Piloten (BASIC-16/17) die Formstudie – im Blatt als „Formstudie – kein Pilot“ gekennzeichnet (`ballon.resolve_base`). Erlaubte Eingriffe (docs/generator.md), in dieser Reihenfolge:
  sight        Visier tauschen gegen einen Baustein aus BALLON common.py (Visier-Baukasten v3), Sitz auf der Schiene BRI-22
  stock        Schaft S1/S2 aus BALLON (stock_s1/stock_s2) an Gehäuseende und Laufachse; stock_scale = Längenfaktor s
  grip         Griffgruppe grip_rifle(top) → grip_v21(top) (BGM-1)
  mag          Magazinlänge (BMW-R) entlang der Entnahmerichtung
  muzzle       Länge der Mündung (BMZ-15); muzzle_r Radiusfaktor
  glow         Leuchtstreifen (BALLON glow) auf der Gehäuseseite
  drop         Teil-ID-Muster (fnmatch); Teile mit Ankern, Kindteilen oder Bewegung bleiben (Bericht nennt sie mit Grund)
  front/rear   Faktor auf die Vorder-/Hinterlänge; Schnitt zwischen Stützhand und Mündung bzw. im Schaft
  limbs        Bogen: Faktor auf die Wurfarmlänge (oben und unten, Schnitt im Wurfarm)
Ein Schnitt `at` trennt: Teile ganz jenseits werden verschoben, lange Teile über dem Schnitt gedehnt bzw. gestaucht, kurze
Teile werden nie verzerrt. Weltpunkte (`POINTS`, BALLON 0.41: Auswurf, Griffkontakte; Form wie ANCHORS) folgen ihrem Teil nach
derselben Regel wie die Anker (0.7); ein getauschtes Teil gibt seine Punkte an das neue Teil gleicher ID oder das nächste neue Teil
weiter, beides steht im Bericht. Gestaucht wird höchstens bis zur freien Zone hinter dem Schnitt; Begrenzungen stehen im Bericht.
Alle Zahlen in mm im BALLON-Rahmen (f vorn, u oben, x links). Bausteine liest `ballon.call` aus dem gepinnten Snapshot.
"""
from __future__ import annotations

import copy
import fnmatch
import math

from . import ballon, geom, model, variants

SHORT_MM = 60.0     # Teile kürzer als das werden nie gedehnt (Annahme: Detailteile behalten ihre Form)
GAP_MM = 1.0        # Restabstand beim Stauchen (SEAM aus BALLON common.SEAM)
POINT_KEYS = ("pivot", "tip", "nock")
FRONT_WINDOW = (0.25, 0.75)   # Annahme: Schnitt in der mittleren Hälfte Stützhand→Mündung, weg von Gehäuse- und Mündungsdetails
STOCK_MARGIN = 0.2            # Annahme: Schnitt nicht in den äußeren 20 % des Schafts (Schulterstütze, Gehäuseanschluss)
LIMB_WINDOW = (0.25, 0.75)    # Annahme: Schnitt in der mittleren Hälfte des Wurfarms (Aufnahme und Rolle bleiben unverzerrt)
MAG_CUT = 0.5                 # Annahme: Magazin in halber Länge geteilt (Schacht oben, Boden unten unverzerrt)
SIGHT_LINE_MM = (60.0, 80.0)  # Vorgabe BALLON docs/designvertrag.md: Visierlinie 60–80 mm über der Laufachse
SCOPE_LINE_MM = 66.0          # Vorgabe BALLON reticles.SIGHT height_mm: Zielfernrohre richten sich nur nach der Visierhöhe
FOOT_MM = 46.0                # Vorgabe BALLON common.sight_platform: H0-Klemmfuß 46 mm lang
SCOPE_LEN_MM = {"scope_tropfen": 120.0, "gabel": 120.0, "lang": 200.0}   # Vorgabe BALLON: Standardlängen der Bausteine
EYE_RELIEF_MM = 90.0          # Vorgabe BALLON reticles.SIGHT types.scope.eye_relief_mm
NO_SIGHT_SWAP = ("07",)       # Annahme: das Pinvisier des Bogens gehört zur Bogenform (kein Holo am Bogen)
S1_LEN_MM, S2_LEN_MM = 179.0, 170.0   # gemessen aus BALLON stock_s1/stock_s2 bei s = 1 (Schaftkappe hinten)
GLOW_H_MM, GLOW_GAP_MM, GLOW_SPAN = 3.0, 3.0, (0.3, 0.7)   # Annahme: Streifen 3 mm hoch, 3 mm Abstand, mittlere 40 % des Teils
GLOW_MIN_MM = 30.0            # Annahme: kürzere Streifen lesen sich im Blatt als Punkt, nicht als Linie
GLOW_EDGE_MM = 3.0            # Annahme: Abstand zur Profilkante (Fase R_BODY 5 mm soll den Streifen nicht anschneiden)
GLOW_W_MM, GLOW_INSET_MM = 1.0, 0.2   # Vorgabe BALLON glow(w=1.0); Annahme Mitte 0,2 mm vor der Fläche (0,3 mm eingelassen; BALLON-Salvenanzeigen 0,1 mm)
GLOW_TOUCH_MM = 1.0           # Annahme: Teile, die bis 1 mm an die Seitenfläche reichen, blockieren den Streifen
ACCENT_LIMIT = 3              # Vorgabe Designvertrag: höchstens drei Akzent-Bedienfunktionen je Waffe
ACCENT_EXEMPT = ("Munitionskennung", "Grafikelement", "Kennzeichnet")   # Designvertrag: Munitionskennung ist keine Bedienfunktion
HAND_ROLES = ("graphite", "rubber")   # Designvertrag „Hand = Graphit“; BALLON 0.32 Softgrip: Griff der Haupthand Gummi
SIGHT_KEEP_ROLE = "sight_anod"        # Rolle für entfärbte Visier-Akzente (BALLON SIGHT_MAT)


class GeneratorError(ValueError):
    pass


# ------------------------------------------------------------------ Koordinaten je Form (ax 0 = f, 1 = u)

def _vals(p, ax):
    s = p.get("shape", "box")
    if s == "prof":
        return [q[ax] for q in p["pts"]]
    if s == "plan":
        return [q[0] for q in p["pts"]] if ax == 0 else [p["u0"], p["u1"]]
    if s == "box":
        return [p["f0"], p["f1"]] if ax == 0 else [p["u0"], p["u1"]]
    if s in ("frame", "xbox"):
        return [p["f0"], p["f1"]] if ax == 0 else [p["cu"]]
    if s == "xprof":
        return [p["f0"], p["f1"]] if ax == 0 else [p["cu"] + q[1] for q in p["pts"]]
    if s == "cyl":
        if p["axis"] == "fu"[ax]:
            return [p["a0"], p["a1"]]
        return [p["c"][ax]] if p["axis"] == "x" else [p["c"][0]]
    if s == "multi":
        return [v for q in p["items"] for v in _vals(q, ax)]
    if s == "tube":
        return [q[ax] for q in p["path"]]
    if s == "text":                 # Schriftzug: Ankerpunkt (f, u); Glyphen bleiben unverzerrt
        return [p["fu"[ax]]]
    raise GeneratorError(f"{p.get('id', 'Teil')}: Form {s} im Generator nicht unterstützt")


def _set(point, ax, fn):
    return tuple(fn(v) if i == ax else v for i, v in enumerate(point))


def _map(p, ax, fn):
    s = p.get("shape", "box")
    if s in ("prof", "tube"):
        key = "pts" if s == "prof" else "path"
        p[key] = [_set(q, ax, fn) for q in p[key]]
    elif s == "plan":
        if ax == 0:
            p["pts"] = [_set(q, 0, fn) for q in p["pts"]]
        else:
            p["u0"], p["u1"] = fn(p["u0"]), fn(p["u1"])
    elif s == "box":
        k0, k1 = ("f0", "f1") if ax == 0 else ("u0", "u1")
        p[k0], p[k1] = fn(p[k0]), fn(p[k1])
    elif s in ("frame", "xbox", "xprof"):
        if ax == 0:
            p["f0"], p["f1"] = fn(p["f0"]), fn(p["f1"])
        else:                       # Querschnitt bleibt, die Mitte wandert (Visier- und Rahmenteile sind kurz)
            p["cu"] = fn(p["cu"])
    elif s == "cyl":
        if p["axis"] == "fu"[ax]:
            p["a0"], p["a1"] = fn(p["a0"]), fn(p["a1"])
        elif p["axis"] == "x":
            p["c"] = _set(p["c"], ax, fn)
        else:
            p["c"] = _set(p["c"], 0, fn)
    elif s == "multi":
        for q in p["items"]:
            _map(q, ax, fn)
    elif s == "text":
        p["fu"[ax]] = fn(p["fu"[ax]])
    else:
        raise GeneratorError(f"{p.get('id', 'Teil')}: Form {s} im Generator nicht unterstützt")
    for cut in p.get("cuts", []):
        _map(cut, ax, fn)
    move = p.get("move")
    if move:
        for key in POINT_KEYS:
            if move.get(key) is not None:
                move[key] = _set(move[key], ax, fn)
        if move.get("expect"):
            point, direction = move["expect"]
            move["expect"] = (_set(point, ax, fn), direction)


def _extent(p, ax=0):
    v = _vals(p, ax)
    return min(v), max(v)


def _located(model):
    """Anker und Weltpunkte: alles mit `at` und Teilbezug, das Teilen folgt (BALLON-Regel für Generatoren, 0.41)."""
    return [*model["ANCHORS"].values(), *model.get("POINTS", {}).values()]


def _mirror(model, ax=0):
    for p in model["PARTS"]:
        _map(p, ax, lambda v: -v)
    for a in _located(model):
        a["at"] = _set(a["at"], ax, lambda v: -v)


def _descendants(parts, ids):
    ids = set(ids)
    grew = True
    while grew:
        more = {p["id"] for p in parts if p.get("parent_part") in ids} - ids
        ids |= more
        grew = bool(more)
    return ids


# ------------------------------------------------------------------ Schnitt und Dehnung (vorwärts; rückwärts = gespiegelt)

def _classify(parts, at, ax=0, force=()):
    far, cross, near = [], [], []
    for p in parts:
        lo, hi = _extent(p, ax)
        if lo >= at:
            far.append(p)
        elif hi > at and (hi - lo >= SHORT_MM or p["id"] in force):
            cross.append(p)
        else:
            near.append(p)
    return far, cross, near


def _room(parts, at, ax=0):
    """Largest safe shortening at `at`: free zone behind the cut for crossing parts and far parts."""
    far, cross, near = _classify(parts, at, ax)
    room = float("inf")
    for p in cross:
        beyond = [f for f in _vals(p, ax) if f > at]
        room = min(room, min(beyond) - at)
    near_hi = max((_extent(p, ax)[1] for p in near), default=-float("inf"))
    for p in far:
        room = min(room, _extent(p, ax)[0] - max(near_hi, at))
    return room - GAP_MM


def _choose_cut(parts, lo, hi, shortening, ax=0):
    """Cut in [lo, hi]: no short part crossed, fewest parts stretched, most free room when shortening, then centred."""
    best = None
    steps = 48
    for i in range(steps + 1):
        at = lo + (hi - lo) * i / steps
        crossed = [p for p in parts if _extent(p, ax)[0] < at < _extent(p, ax)[1]]
        bad = sum(1 for p in crossed if _extent(p, ax)[1] - _extent(p, ax)[0] < SHORT_MM)
        room = _room(parts, at, ax) if shortening else 0.0
        # erst keine kurzen Teile kreuzen, dann möglichst wenige Teile dehnen (Leitmerkmale wie Schildflügel bleiben), dann Platz
        score = (bad, len(crossed), -room, abs(at - (lo + hi) / 2))
        if best is None or score < best[0]:
            best = (score, at, room)
    return best[1], best[2]


def _stretch(model, at, delta, ax=0, force=()):
    far, cross, near = _classify(model["PARTS"], at, ax, force)
    moved = {p["id"]: "translate" for p in far} | {p["id"]: "stretch" for p in cross}
    for p in far:
        _map(p, ax, lambda v: v + delta)
    for p in cross:
        _map(p, ax, lambda v: v + delta if v > at else v)
    for a in _located(model):
        how = moved.get(a.get("part"))
        if how == "translate" or (how == "stretch" and a["at"][ax] > at):
            a["at"] = _set(a["at"], ax, lambda v: v + delta)
    return sorted(p["id"] for p in far), sorted(p["id"] for p in cross)


def _anchor(model, name, ax=0):
    a = model["ANCHORS"].get(name)
    return a["at"][ax] if a else None


def stretch_front(model, factor):
    hand, muzzle = _anchor(model, "Socket_Hand"), _anchor(model, "Socket_Muzzle")
    support = _anchor(model, "Socket_SupportHand")
    if muzzle is None or muzzle - hand < 100:
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
    hand = _anchor(model, "Socket_Hand")
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


def limbs(model, factor):
    """Bogen: oberen und unteren Wurfarm (Baugruppe `limbs`) in u strecken; Sehne, Rollen und Bewegungspunkte folgen."""
    if not any(p["asm"] == "limbs" for p in model["PARTS"]):
        return {"op": "limbs", "factor": factor, "skipped": "keine Baugruppe limbs (kein Bogen)"}
    sides = []
    for side, name in ((1, "oben"), (-1, "unten")):
        if side < 0:
            _mirror(model, 1)
        try:
            arm = [p for p in model["PARTS"] if p["asm"] == "limbs" and sum(_extent(p, 1)) > 0]
            lo, hi = min(_extent(p, 1)[0] for p in arm), max(_extent(p, 1)[1] for p in arm)
            want = (factor - 1.0) * (hi - lo)
            at, room = _choose_cut(model["PARTS"], lo + LIMB_WINDOW[0] * (hi - lo), lo + LIMB_WINDOW[1] * (hi - lo), want < 0, ax=1)
            delta = want if want >= 0 else -min(-want, max(room, 0.0))
            far, cross = _stretch(model, at, delta, ax=1)
        finally:
            if side < 0:
                _mirror(model, 1)
        sides.append({"side": name, "cut_u_mm": round(at * side, 3), "wanted_mm": round(want, 3), "delta_mm": round(delta, 3),
                      "limited": abs(delta - want) > 1e-9, "translated": far, "stretched": cross})
    return {"op": "limbs", "factor": factor, "sides": sides}


def drop(model, patterns):
    """Teile per Muster weglassen; geschützt bleiben Teile mit Anker oder Weltpunkt, mit Kindteilen und bewegte Teile (`move`: Mechanik
    der BALLON-Aktionen wie Abzug, Ladehebel, Auswurfklappe, Magazin – ohne sie liefen Aktionen ins Leere)."""
    anchored = {a["part"] for a in model["ANCHORS"].values()}
    pointed = {a["part"] for a in model.get("POINTS", {}).values()}
    parents = {p.get("parent_part") for p in model["PARTS"]}
    dropped, protected, why = [], [], {}
    for p in list(model["PARTS"]):
        if any(fnmatch.fnmatchcase(p["id"], pat) for pat in patterns):
            reasons = [r for r, hit in (("Anker", p["id"] in anchored), ("Weltpunkt", p["id"] in pointed),
                                        ("Kindteile", p["id"] in parents), ("bewegt", bool(p.get("move")))) if hit]
            if reasons:
                protected.append(p["id"]); why[p["id"]] = reasons
            else:
                dropped.append(p["id"])
    model["PARTS"] = [p for p in model["PARTS"] if p["id"] not in set(dropped)]
    report = {"op": "drop", "patterns": list(patterns), "dropped": dropped, "protected": protected}
    return {**report, "protected_why": why} if why else report   # ohne Schutzfall bytegleich zu 0.2


# ------------------------------------------------------------------ Baukasten: Teile aus BALLON-Bausteinen tauschen

def _nearest(parts, at):
    """Teil-ID des Teils mit dem kleinsten Abstand seines (f, u)-Rahmens zum Punkt (bei Gleichstand das erste)."""
    def gap(p):
        return math.hypot(*(max(lo - at[ax], 0.0, at[ax] - hi) for ax, (lo, hi) in enumerate((_extent(p, 0), _extent(p, 1)))))
    return min(parts, key=gap)["id"]


def _replace(model, remove, new_parts, new_anchors=None):
    """Remove part IDs (with descendants), insert BALLON parts at the first removed position, update anchors. Weltpunkte eines
    entfernten Teils bleiben an Ort und Stelle und gehen an das neue Teil gleicher ID, sonst an das nächste neue Teil; ohne neue
    Teile ist das ein Fehler (Punkt ohne Teil). Rückgabe: entfernte IDs, entfallene Anker, {Punkt: [altes, neues Teil]}."""
    remove = _descendants(model["PARTS"], remove)
    keep = [p for p in model["PARTS"] if p["id"] not in remove]
    clash = sorted({p["id"] for p in new_parts} & {p["id"] for p in keep})
    if clash:
        raise GeneratorError(f"Teil-IDs schon vergeben: {clash}")
    first = next(i for i, p in enumerate(model["PARTS"]) if p["id"] in remove)
    pos = sum(1 for p in model["PARTS"][:first] if p["id"] not in remove)
    model["PARTS"] = keep[:pos] + new_parts + keep[pos:]
    gone = sorted(n for n, a in model["ANCHORS"].items() if a["part"] not in {p["id"] for p in model["PARTS"]})
    for name in gone:
        del model["ANCHORS"][name]
    model["ANCHORS"].update(copy.deepcopy(new_anchors or {}))
    new_ids = {p["id"] for p in new_parts}
    handed = {}
    for name, pt in sorted(model.get("POINTS", {}).items()):
        if pt["part"] in remove:
            if not new_parts:
                raise GeneratorError(f"Weltpunkt {name}: Teil {pt['part']} entfernt, kein neues Teil")
            new = pt["part"] if pt["part"] in new_ids else _nearest(new_parts, pt["at"])
            handed[name] = [pt["part"], new]
            pt["part"] = new
    return sorted(remove), gone, handed


def _handed(handed):
    return {"points_handed": handed} if handed else {}


def _rails(model):
    return sorted((p for p in model["PARTS"] if p.get("iface") == "BRI-22" and p["asm"] != "sight" and p["shape"] == "box"),
                  key=lambda p: p["f0"])


def _line(model):
    eye, bore = _anchor(model, "Socket_Eye", 1), _anchor(model, "Socket_Muzzle", 1)
    return None if eye is None or bore is None else round(eye - bore, 3)


def _in_band(line):
    return line is not None and SIGHT_LINE_MM[0] - 1e-6 <= line <= SIGHT_LINE_MM[1] + 1e-6


def swap_sight(model, kind, num, kit):
    op = {"op": "sight", "kind": kind}
    rails, old = _rails(model), [p for p in model["PARTS"] if p["asm"] == "sight"]
    bore = _anchor(model, "Socket_Muzzle", 1)
    if num in NO_SIGHT_SWAP:
        return {**op, "skipped": "Bogen: Pinvisier gehört zur Bogenform"}
    if not rails or not old or bore is None:
        return {**op, "skipped": "keine Schiene BRI-22 mit Visier oder keine Laufachse"}
    feet = [p for p in old if p.get("iface") == "BRI-22"] or old
    center = (min(_extent(p)[0] for p in feet) + max(_extent(p)[1] for p in feet)) / 2
    wtype = model["META"]["type"]
    if kind in variants.SCOPES:
        front, rear = rails[-1], rails[0]
        length = SCOPE_LEN_MM[kind]
        cu = bore + SCOPE_LINE_MM
        if len(rails) == 1:
            if front["f1"] - front["f0"] < length - 2:
                return {**op, "skipped": f"Schiene kürzer als das Zielfernrohr ({length - 2:g} mm)"}
            f_obj = min(max(center + (length - 2) / 2, front["f0"] + length - 2), front["f1"])
            kw = {}
        else:                       # v2.1: Sattel auf der hinteren, Fuß auf der vorderen Schiene (Konzept A)
            f_obj, fe = front["f1"], front["f1"] - length
            sf = (max(fe + 2, rear["f0"]), min(fe + 42 if kind == "lang" else f_obj - EYE_RELIEF_MM - 2, rear["f1"]))
            if sf[1] - sf[0] < 10:
                return {**op, "skipped": "hintere Schiene trägt den Sattel nicht"}
            kw = {"seat_u": rear["u1"], "saddle_f": sf}
        parts, anchors = kit(kind, f_obj, front["u1"], cu, size="M", weapon_type=wtype, **kw)
        op.update(f_mm=round(f_obj, 3))
    else:
        rail = min(rails, key=lambda r: 0 if r["f0"] <= center <= r["f1"] else min(abs(center - r["f0"]), abs(center - r["f1"])))
        if rail["f1"] - rail["f0"] < FOOT_MM:
            return {**op, "skipped": f"Schiene kürzer als der Klemmfuß ({FOOT_MM:g} mm)"}
        f = min(max(center - FOOT_MM / 2, rail["f0"]), rail["f1"] - FOOT_MM)
        size = {} if kind == "reflex_sight_v21" else {"size": "M"}
        parts, anchors = kit(kind, f, rail["u1"], weapon_type=wtype, **size)
        op.update(f_mm=round(f, 3))
    before, after = _line(model), round(anchors["Socket_Eye"]["at"][1] - bore, 3)
    if not _in_band(after) and (_in_band(before) or before is None or abs(after - 70) > abs(before - 70)):
        return {**op, "skipped": f"Visierlinie {after:g} mm verletzt 60–80 mm (Grundform {before} mm)"}
    removed, anchors_gone, handed = _replace(model, [p["id"] for p in old], parts, anchors)
    return {**op, "removed": removed, "added": [p["id"] for p in parts], "anchors_replaced": anchors_gone,
            "sight_line_mm": {"before": before, "after": after}, **_handed(handed)}


def _stock_kind(model):
    P = {p["id"]: p for p in model["PARTS"]}
    if {"stock_joint", "stock_spine", "butt_pad"} <= set(P):
        j = P["stock_joint"]
        f0, ua = j["f1"] - 1, j["u0"] + 22                      # Vorgabe BALLON stock_s1: Verbindung f0−11…f0+1, ua−22…ua+20
        return "S1", f0, ua, (f0 - _extent(P["butt_pad"])[0]) / S1_LEN_MM, "cheek_rest" in P
    if "stock" in P and P["stock"].get("iface") == "BST-2" and "butt_pad" in P:
        f, u = P["stock"]["pts"][0]
        f0, ua = f - 2, u + 40                                  # Vorgabe BALLON stock_s2: erster Punkt (f0 + 2, ua − 40)
        return "S2", f0, ua, (f0 - _extent(P["butt_pad"])[0]) / S2_LEN_MM, False
    return None


def swap_stock(model, kind, scale, kit):
    op = {"op": "stock", "kind": kind, "scale": scale}
    found = _stock_kind(model)
    if not found:
        return {**op, "skipped": "kein Schaft S1/S2 (eigener oder kein Schaft)"}
    cur, f0, ua, s_cur, cheek = found
    kind = kind or cur
    s = scale if scale is not None else round(s_cur, 3)
    old = [p["id"] for p in model["PARTS"] if p["asm"] == "stock"]
    pinned = sorted(n for n, a in model["ANCHORS"].items() if a["part"] in _descendants(model["PARTS"], old))
    if pinned:
        return {**op, "skipped": f"Anker am Schaft: {pinned}"}
    parts = kit("stock_s1", f0, ua, s=s, cheek=cheek or kind != cur) if kind == "S1" else kit("stock_s2", f0, ua, s=s)
    removed, _, handed = _replace(model, old, parts)
    return {**op, "kind": kind, "from": cur, "scale": s, "receiver_rear_f_mm": round(f0, 3), "bore_u_mm": round(ua, 3),
            "removed": removed, "added": [p["id"] for p in parts], **_handed(handed)}


def swap_grip(model, kind, kit):
    op = {"op": "grip", "kind": kind}
    P = {p["id"]: p for p in model["PARTS"]}
    g = P.get("grip")
    if not g or g.get("iface") != "BGM-1" or g["shape"] != "prof" or "grip_cap" in P:
        return {**op, "skipped": "keine Griffgruppe grip_rifle (BGM-1) oder schon v2.1"}
    top = g["pts"][0][1]
    ref = kit("grip_rifle", top=top)
    same = all(r["id"] in P and [tuple(q) for q in P[r["id"]].get("pts", [])] == [tuple(q) for q in r["pts"]]
               and P[r["id"]].get("w") == r["w"] for r in ref)
    if not same:
        return {**op, "skipped": "Griffgruppe weicht von grip_rifle(top) ab (Neigung, Breite oder ohne Bügel)"}
    parts = kit("grip_v21", top=top)
    removed, _, handed = _replace(model, [r["id"] for r in ref], parts)
    return {**op, "top_mm": top, "removed": removed, "added": [p["id"] for p in parts], **_handed(handed)}


def stretch_mag(model, factor):
    """Magazin (BMW-R oder Magazin im Griff, Entnahme per translate) entlang der Entnahmerichtung strecken."""
    op = {"op": "mag", "factor": factor}
    mags = [p for p in model["PARTS"] if (p.get("iface") == "BMW-R" or p["id"] == "magazine") and p["asm"] == "ammo"
            and p["shape"] == "prof" and (p.get("move") or {}).get("kind") == "translate"]
    if len(mags) != 1:
        return {**op, "skipped": "kein entnehmbares Stangenmagazin"}
    m = mags[0]
    (vf, vu), (cf, cu) = m["move"]["vector_mm"][:2], m["move"]["pivot"][:2]
    n = math.hypot(vf, vu)
    d = (vf / n, vu / n)
    s = lambda q: (q[0] - cf) * d[0] + (q[1] - cu) * d[1]  # noqa: E731
    s0 = min(s(q) for q in m["pts"])
    length = max(s(q) for q in m["pts"]) - s0
    cut, delta = s0 + MAG_CUT * length, (factor - 1.0) * length
    group = [p for p in model["PARTS"] if p["id"] in _descendants(model["PARTS"], [m["id"]])]
    side = {p["id"]: {s(q) > cut for q in _corners(p)} for p in group}
    for p in group:
        if p["shape"] != "prof" and len(side[p["id"]]) > 1:
            return {**op, "skipped": f"{p['id']}: Form {p['shape']} über dem Schnitt"}
    for p in group:
        if p["shape"] == "prof":
            p["pts"] = [(q[0] + d[0] * delta, q[1] + d[1] * delta) if s(q) > cut else tuple(q) for q in p["pts"]]
        elif side[p["id"]] == {True}:          # ganz jenseits: entlang der Entnahmerichtung verschieben
            _map(p, 0, lambda v: v + d[0] * delta)
            _map(p, 1, lambda v: v + d[1] * delta)
    ids = {p["id"] for p in group}
    for a in _located(model):                  # wie die Profilpunkte: jenseits des Schnitts verschoben (Griff am Magazinboden)
        if a["part"] in ids and s(a["at"]) > cut:
            a["at"] = (a["at"][0] + d[0] * delta, a["at"][1] + d[1] * delta, *a["at"][2:])
    return {**op, "direction": [round(d[0], 6), round(d[1], 6)], "length_mm": round(length, 3), "cut_mm": round(cut, 3),
            "delta_mm": round(delta, 3), "parts": sorted(p["id"] for p in group)}


def _corners(p):
    return [(f, u) for f in _extent(p, 0) for u in _extent(p, 1)]


def stretch_muzzle(model, factor, radius):
    op = {"op": "muzzle", "factor": factor, "radius": radius}
    m = next((p for p in model["PARTS"] if p["id"] == "muzzle"), None)
    if m is None or (m["shape"] == "cyl" and m["axis"] != "f"):
        return {**op, "skipped": "kein Mündungsteil `muzzle` entlang der Laufachse"}
    lo, hi = _extent(m)
    delta = (factor - 1.0) * (hi - lo)
    far, cross = _stretch(model, lo + 0.5 * (hi - lo), delta, force={"muzzle"}) if delta else ([], [])
    if radius != 1.0:
        if m["shape"] != "cyl":
            return {**op, "skipped": "Radius nur an zylindrischer Mündung", "delta_mm": round(delta, 3)}
        m["r"] = m["r"] * radius
        if "r1" in m:
            m["r1"] = m["r1"] * radius
    return {**op, "length_mm": round(hi - lo, 3), "delta_mm": round(delta, 3), "translated": far, "stretched": cross}


def _span_u(pts, f):
    """u-Bereich eines Profils an der Stelle f (alle Kantenschnitte)."""
    us = []
    for (f0, u0), (f1, u1) in zip(pts, pts[1:] + pts[:1]):
        if min(f0, f1) <= f <= max(f0, f1) and f0 != f1:
            us.append(u0 + (u1 - u0) * (f - f0) / (f1 - f0))
    return (min(us), max(us)) if len(us) >= 2 else None


def _x_range(p):
    s = p.get("shape", "box")
    if s in ("prof", "box"):
        return p.get("x", 0) - p["w"] / 2, p.get("x", 0) + p["w"] / 2
    if s == "cyl" and p["axis"] == "x":
        return min(p["a0"], p["a1"]), max(p["a0"], p["a1"])
    return None


def add_glow(model, count, kit):
    op = {"op": "glow", "count": count}
    if count <= 0:
        return {**op, "skipped": "keine Streifen"}
    shells = sorted((p for p in model["PARTS"] if p["shape"] == "prof" and p["mat"] == "shell" and not p.get("move")
                     and p["asm"] in ("receiver", "barrel", "support", "riser", "blade", "shaft")),
                    key=lambda p: -(_extent(p)[1] - _extent(p)[0]))
    total = count * GLOW_H_MM + (count - 1) * GLOW_GAP_MM
    for p in shells:
        lo, hi = _extent(p)
        f0, f1 = lo + GLOW_SPAN[0] * (hi - lo), lo + GLOW_SPAN[1] * (hi - lo)
        spans = [_span_u([tuple(q) for q in p["pts"]], f) for f in (f0, (f0 + f1) / 2, f1)]
        if f1 - f0 < GLOW_MIN_MM or None in spans:
            continue
        ulo, uhi = max(s[0] for s in spans) + GLOW_EDGE_MM, min(s[1] for s in spans) - GLOW_EDGE_MM
        if uhi - ulo < total:
            continue
        u0 = (ulo + uhi) / 2 - total / 2
        for side in (1, -1):                       # links zuerst (Akzente kameranah, BALLON 0.30)
            surface = p.get("x", 0) + side * p["w"] / 2
            boxes = [(f0, f1, u0 + i * (GLOW_H_MM + GLOW_GAP_MM), u0 + i * (GLOW_H_MM + GLOW_GAP_MM) + GLOW_H_MM) for i in range(count)]
            blocked = []
            for q in model["PARTS"]:
                xr = _x_range(q)
                if q is p or xr is None or side * (xr[1] if side > 0 else xr[0]) < abs(surface) - GLOW_TOUCH_MM:
                    continue
                (qf0, qf1), (qu0, qu1) = _extent(q, 0), _extent(q, 1)
                if any(qf0 < b[1] and qf1 > b[0] and qu0 < b[3] and qu1 > b[2] for b in boxes):
                    blocked.append(q["id"])
            if blocked:
                continue
            parts = [kit("glow", f"glow_line_{i + 1}", f"Leuchtstreifen {i + 1}", f"Glow line {i + 1}", p["asm"], b[0], b[1], b[2], b[3],
                         w=GLOW_W_MM, x=surface + side * GLOW_INSET_MM, func="Leuchtstreifen (Ladezustand)", attach=f"in {p['id']} eingelassen",
                         parent_part=p["id"]) for i, b in enumerate(boxes)]
            model["PARTS"] += parts
            return {**op, "on": p["id"], "side": "links" if side > 0 else "rechts", "f_mm": [round(f0, 3), round(f1, 3)],
                    "u0_mm": round(u0, 3), "added": [q["id"] for q in parts]}
    return {**op, "skipped": "keine freie Gehäuseseite"}


# ------------------------------------------------------------------ Designvertrag (gemessen am Autorenmodell)

def accent_functions(parts):
    return sorted({p["func"] for p in parts if p["mat"] == "accent" and not any(k in p["func"] for k in ACCENT_EXEMPT)})


def contract(model):
    P = {p["id"]: p for p in model["PARTS"]}
    return {"sight_line_mm": _line(model), "accent_functions": accent_functions(model["PARTS"]),
            "hand_roles": {n: P[model["ANCHORS"][n]["part"]]["mat"] for n in ("Socket_Hand", "Socket_SupportHand")
                           if n in model["ANCHORS"]}}


def _keep_accents(model, base, added, notes):
    """Neue Akzent-Bedienelemente aus Bausteinen entfärben, bis höchstens max(3, Grundform) Funktionen bleiben."""
    limit = max(ACCENT_LIMIT, len(base["accent_functions"]))
    for p in reversed([p for p in model["PARTS"] if p["id"] in added and p["mat"] == "accent"]):
        if len(accent_functions(model["PARTS"])) <= limit:
            break
        role = SIGHT_KEEP_ROLE if p["asm"] == "sight" else "graphite"
        notes.append({"part": p["id"], "kind": "Annahme", "field": "mat", "ballon": "accent", "v2": role,
                      "reason": f"Designvertrag: höchstens {limit} Akzent-Bedienfunktionen (Grundform {len(base['accent_functions'])})"})
        p["mat"] = role


# ------------------------------------------------------------------ BALLON → v2-Autorenmodell

def adapt(data):
    """Return an editable copy plus the list of documented adaptations of BALLON data."""
    model = {k: copy.deepcopy(data[k]) for k in ("META", "PARTS", "ASSEMBLIES", "ANCHORS")}
    model["POINTS"] = copy.deepcopy(data.get("POINTS") or {})
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
    missing = sorted(n for n, a in model["POINTS"].items() if a["part"] not in ids)
    if missing:
        raise ValueError(f"Weltpunkte verweisen auf entfernte Teile: {missing}")


def _apply(model, params, num, kit, notes):
    """Run the Baukasten steps in fixed order; returns the op reports and the IDs of parts added from BALLON blocks."""
    ops, added = [], set()
    before = copy.deepcopy(model["POINTS"])

    def run(report):
        moved = {n: [round(b - a, 3) for a, b in zip(before[n]["at"], q["at"])] for n, q in model["POINTS"].items()
                 if any(abs(b - a) > 1e-9 for a, b in zip(before[n]["at"], q["at"]))}
        before.update(copy.deepcopy(model["POINTS"]))
        ops.append({**report, "points_moved": moved} if moved else report)
        added.update(report.get("added", []))

    if params.get("sight"):
        run(swap_sight(model, params["sight"], num, kit))
    if "stock" in params or "stock_scale" in params:
        run(swap_stock(model, params.get("stock"), params.get("stock_scale"), kit))
    if params.get("grip"):
        run(swap_grip(model, params["grip"], kit))
    if "mag" in params:
        run(stretch_mag(model, params["mag"]))
    if "muzzle" in params or "muzzle_r" in params:
        run(stretch_muzzle(model, params.get("muzzle", 1.0), params.get("muzzle_r", 1.0)))
    if params.get("glow"):
        run(add_glow(model, params["glow"], kit))
    if "drop" in params:
        run(drop(model, params["drop"]))
    if "front" in params:
        run(stretch_front(model, params["front"]))
    if "rear" in params:
        run(stretch_rear(model, params["rear"]))
    if "limbs" in params:
        run(limbs(model, params["limbs"]))
    return ops, added


def _kit(snap):
    def call(name, *args, **kwargs):
        if snap is None:
            raise GeneratorError(f"Baustein {name} braucht den BALLON-Snapshot")
        return ballon.call(snap, name, *args, **kwargs)
    return call


def vary(data, variant, num, snap=None):
    """BALLON data + register entry → variant model in BALLON's vocabulary (parts with all metadata, before `generate`
    strips it for the v2 author model) plus the run record; shared by `generate` (sheets) and `asset.kit_model` (GLB)."""
    model, notes = adapt(data)
    sid = variants.sheet_id(variant["letter"], num)
    params, draws = variants.resolve(variant.get("params", {}), sid)
    before = contract(model)
    ops, added = _apply(model, params, num, _kit(snap), notes)
    _keep_accents(model, before, added, notes)
    _finish(model, notes)
    return model, {"sid": sid, "params": params, "draws": draws, "ops": ops, "notes": notes, "before": before}


def generate(data, variant, num, source, snap=None, base="standard"):
    """BALLON data of one type + register entry → (v2 author model, generator report). `base` = tatsächliche Grundform."""
    model, run = vary(data, variant, num, snap)
    sid, params, draws, ops, notes, before = (run[k] for k in ("sid", "params", "draws", "ops", "notes", "before"))
    meta = model["META"]
    wanted = variant.get("base", "standard")
    version = ballon.pilot_version(base)
    if wanted != "standard" and not version:
        notes.append({"kind": "Annahme", "field": "base", "ballon": wanted, "v2": base,
                      "reason": f"kein BALLON-Spielpilot für BASIC-{num}; Formstudie (basic/weapons)"})
    label = f"v{version}-Pilot" if version else "Formstudie"
    shape = f"{meta['id']} „{meta['name']}“" + (f" · v{version}" if version else
                                                 " · Formstudie" + (" – kein Pilot" if wanted != "standard" else ""))
    # Commit bewusst nicht im Geometriedokument: gleicher Quellhash = gleiches Ergebnis (Commit steht im Blatt-Spec)
    provenance = {"kind": "Vorgabe", "source": (
        f"BALLON {meta['id']} {label} (Quellhash {source['source_sha256'][:12]}); "
        f"Variante {variant['letter']} „{variant['name']}“ aus data/variants.toml; Maße in mm wie BALLON")}
    kit_ops = [o for o in ops if o["op"] in ("sight", "stock", "grip", "glow") and "skipped" not in o]
    facts = [["Variante", f"{variant['letter']} · {variant['name']}"],
             ["Grundform", shape],
             ["BALLON-Quellhash", source["source_sha256"][:12]],
             ["Skin", variant.get("skin", "standard")]]
    if kit_ops:
        facts.append(["Baukasten", " · ".join(f"{o['op']} {o.get('kind') or o.get('count')}" for o in kit_ops)])
    if draws:
        facts.append(["Seed", variants.seed(sid)])
    info = {"id": sid, "kind": "weapon", "name_de": f"{meta['type_de']} · {variant['name']}",
            "name_en": f"{meta['type_en']} · {variant['name']}",
            "summary": f"{meta.get('summary', '')} Linie {variant['letter']} „{variant['name']}“: {variant['idea']}",
            "provenance": provenance, "facts": facts}
    parts = []
    for p in model["PARTS"]:
        q = {k: v for k, v in p.items() if k not in ("en", "func", "attach", "iface")}
        q["name_en"] = p.get("en")
        parts.append(q)
    author = {"INFO": info, "PARTS": parts, "ASSEMBLIES": model["ASSEMBLIES"], "ANCHORS": model["ANCHORS"]}
    record = {k: variant[k] for k in ("letter", "name", "idea", "since", "skin", "params")}
    report = {"variant": {**record, "base": wanted},
              "type": {k: meta.get(k) for k in ("id", "num", "type", "type_de", "type_en", "name", "nick")},
              "ballon": source, "base": base, "variation": {"seed": variants.seed(sid), "draws": draws, "values": params},
              "ops": ops, "adaptations": notes, "contract": {"base": before, "variant": contract(model)}}
    return author, report


def build(variant, num, snap=None, source=None, base=None):
    snap = snap or ballon.snapshot()
    base = base or ballon.resolve_base(snap, num, variant.get("base", "standard"))
    source = source or ballon.source(snap, num, base)
    return generate(ballon.load(snap, num, base), variant, num, source, snap, base)


def evaluate(data, variant, num, source, ballon_dims=None, snap=None, base="standard", **options):
    """Generate and evaluate one sheet; the geometry stage's code closure starts here (geom, model, ballon, variants)."""
    author, report = generate(data, variant, num, source, snap, base)
    report["ballon_dimensions_mm"] = ballon_dims
    document = geom.evaluate(model.normalize(author), **options)
    document["generator"] = report
    return document
