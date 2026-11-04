"""Design-Serien (0.8 „Hallmark“): eigene Formensprache als Verkleidung über dem BALLON-Piloten (Parameter `series`).

Die Linien A–H wandeln Parameter ab; eine Serie setzt zusätzlich Schalen, Klemmen, Blöcke und Leuchtführung außen auf die Grundform,
wie die von Hand modellierten Serien aus Formgen v1 (dort H „Werkstatt“, J „Black Ice“, G „Cube-Escape-Farbwelt“) – aber nur mit
BALLONs Kit-Vokabular (`common.part`, Formen prof, box, xprof, frame, cyl, multi, tube) und generisch über alle 17 Typen:

  facet  Stealth: wenige große Facetten (Querprofil mit Schrägen, Hüllkontur), Keil über dem Lauf, Sechskanthülse, Leuchtkanten
  bench  Werkstatt: Klemmbänder mit Sechskantschrauben, Lochschienen, Kühlrippen, Schlauchleitung, Prüfkopf an der Mündung
  block  Cube-Farbwelt: Rasterblöcke (Modul 24 mm) in klaren Farbflächen, Würfel an der Mündung, Stufenkanten, Fugenlinie
  flow   Organisch-glatt: gerundete Schalen in zwei Lagen, Spindel um den Lauf, geschwungene Leuchtlinie, Kiemen

Nur außen und nichts Funktionales: vorhandene Teile, Anker und Weltpunkte bleiben unverändert. Jede Schale wird in der Seitenansicht
gegen die Freizonen geschnitten (`Body.keepout`): Wege bewegter Teile (`move`, auch Kinder), Griffe und Hände (`grip.*`), Magazine,
Auswurf (`eject`), Leuchtanzeigen. Nach oben begrenzt `Body.allow` alles: vor dem Auge nicht über die Grundform und die Sichtlinie
(Socket_Eye, SIGHT_DEG unter der Horizontalen), hinter dem Auge nicht über die Grundform; nach vorn hält jede Schale Abstand zur Mündung.
Teile eines bewegten Trägers (Pistolenschlitten) hängen als Kind daran (`parent_part`) und laufen mit, ohne ihn zu ändern.

Alle Zahlen in mm im BALLON-Rahmen (f vorn, u oben, x links). Flächen rechnet manifold3d.CrossSection (ganzzahlig, deterministisch).
"""
from __future__ import annotations

import hashlib
import math
import re

import numpy as np
from manifold3d import CrossSection, FillRule, JoinType

KINDS = ("facet", "bench", "block", "flow")
SIGHT_DEG = 3.0        # Annahme: Blick durch das Visier bleibt frei bis 3° unter der Visierlinie (Fenster 20 mm in ≈ 190 mm Abstand: ≈ 3°)
TOP_MM = 3.5           # Annahme: Schalen dürfen die Grundform oben so weit überragen (Klemmband, Schalendicke)
JUMP_MM = 1.0          # Annahme: größere Sprünge der Oberkante je mm sind Kanten, keine Schräge
SIDE_SIGHT_MM = 20.0   # Annahme: ein Auge so weit neben der Mittelebene sieht seitlich an der Waffe vorbei
MARGIN_MM = 2.5        # Annahme: Luft zwischen Schale und Weg eines bewegten Teils
HAND_MM = 4.0          # Annahme: Luft um Griffteile
HAND_R_MM = 18.0       # Annahme: Freikreis um einen Handkontakt (grip.*)
SUPPORT_MM = (50.0, 12.0, 40.0)   # Annahme: Stützhand frei ±50 mm längs, 12 mm unter, 40 mm über dem Kontakt (Finger umgreifen die Seiten)
EJECT_MM = (34.0, 24.0)           # Annahme: Hülsenfenster ±34 mm längs, ±24 mm hoch auf der Auswurfseite
FACE_MM, ROUND_MM = 3.0, 4.0   # Annahme: Aussparungen 3 mm weiter gefast bzw. gerundet, Schalenecken der Serie flow mit 4 mm
MUZZLE_GAP_MM = 2.0    # Annahme: Schalen enden vor Socket_Muzzle
MIN_AREA_MM2 = 90.0    # Annahme: kleinere Reststücke entfallen (lesen sich als Fehler, nicht als Form)
MIN_STRIP_MM = 2.5     # Annahme: dünnere Stege als das werden aus den Schalen geöffnet
HARD_ASM = ("grip_controls", "ammo", "arrow", "string")   # Baugruppen, die nie überdeckt werden
GLOW_ROLES = ("energy", "charge_core", "pin_glow", "draw_light", "sight_line")
MOVING_HOSTS = {"05": ("slide",)}   # bewegter Träger: Schale hängt als Kind daran (Pistolenschlitten)
SKIP_ZONE = re.compile(r"rail$|^muzzle|foregrip|^loop|clamp|band|collar|plug|bezel|window|recoil|emitter|cheek|butt|bridge|hatch|spine")   # keine Schalenträger
HAND_SHAPE = {"facet": 6, "bench": 0, "block": 0, "flow": 24}   # Ecken des Freikreises um Handkontakte; 0 = Quadrat (Formensprache der Aussparung)
GRAPHIC = "Grafikelement der Serie"  # enthält „Grafikelement“: keine Bedienfunktion nach Designvertrag (generator.ACCENT_EXEMPT)


# ------------------------------------------------------------------ Flächen

def poly(pts) -> CrossSection:
    return CrossSection([np.asarray(pts, float)], FillRule.Positive if _area2(pts) > 0 else FillRule.Negative)


def _area2(pts):
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, list(pts[1:]) + [pts[0]]))


def rect(f0, f1, u0, u1) -> CrossSection:
    return poly([(f0, u0), (f1, u0), (f1, u1), (f0, u1)])


def circle(f, u, r, n=24) -> CrossSection:
    return poly([(f + r * math.cos(2 * math.pi * i / n), u + r * math.sin(2 * math.pi * i / n)) for i in range(n)])


def union(items) -> CrossSection:
    items = [c for c in items if not c.is_empty()]
    return CrossSection.batch_boolean(items, _ADD) if len(items) > 1 else (items[0] if items else CrossSection())


try:                                    # Name der Boole-Art je nach manifold3d-Stand
    from manifold3d import OpType
    _ADD = OpType.Add
except ImportError:                     # pragma: no cover
    _ADD = None


def outlines(area: CrossSection):
    """Teilflächen → Liste von (Außenkontur, [Löcher]) als gerundete Punktlisten, deterministisch nach Lage sortiert."""
    out = []
    for piece in area.decompose():
        rings = [_ring(ring) for ring in piece.to_polygons()]
        rings = [r for r in rings if len(r) >= 3 and abs(_area2(r)) > 0.5]
        if not rings:
            continue
        rings.sort(key=lambda r: -abs(_area2(r)))
        out.append((rings[0], rings[1:], piece))
    return sorted(out, key=lambda o: (o[2].bounds()[0], o[2].bounds()[1]))


def _ring(ring):
    """Punkte runden (0,01 mm), durch das Runden zusammengefallene Nachbarn entfernen."""
    pts = [(round(float(a), 2), round(float(b), 2)) for a, b in ring]
    return [q for q, n in zip(pts, pts[1:] + pts[:1]) if q != n]


def clean(area: CrossSection, strip=MIN_STRIP_MM) -> CrossSection:
    """Dünne Stege und Splitter entfernen: Öffnen mit strip/2, Eckpunkte vereinfachen."""
    r = strip / 2
    return area.offset(-r, JoinType.Miter, 2.0).offset(r, JoinType.Miter, 2.0).simplify(0.15)


def chaikin(pts, n=2):
    """Eckenschneiden (geschlossen): aus einem Polygon wird eine glatte Kurve."""
    for _ in range(n):
        out = []
        for a, b in zip(pts, list(pts[1:]) + [pts[0]]):
            out += [(.75 * a[0] + .25 * b[0], .75 * a[1] + .25 * b[1]), (.25 * a[0] + .75 * b[0], .25 * a[1] + .75 * b[1])]
        pts = out
    return pts


def spline(pts, n=4):
    """Offene Linie glätten (Eckenschneiden, Endpunkte bleiben)."""
    for _ in range(n):
        out = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            out += [(.75 * a[0] + .25 * b[0], .75 * a[1] + .25 * b[1]), (.25 * a[0] + .75 * b[0], .25 * a[1] + .75 * b[1])]
        pts = out + [pts[-1]]
    return pts


# ------------------------------------------------------------------ Ausdehnung der Teile

def bounds(p):
    """(f0, f1, u0, u1, x0, x1) einer Form."""
    s = p.get("shape", "box")
    if s == "multi":
        b = [bounds(q) for q in p["items"]]
        return tuple((min if i % 2 == 0 else max)(q[i] for q in b) for i in range(6))
    if s == "prof":
        f, u = zip(*[q[:2] for q in p["pts"]])
        return min(f), max(f), min(u), max(u), p.get("x", 0) - p["w"] / 2, p.get("x", 0) + p["w"] / 2
    if s == "box":
        return (min(p["f0"], p["f1"]), max(p["f0"], p["f1"]), min(p["u0"], p["u1"]), max(p["u0"], p["u1"]),
                p.get("x", 0) - p["w"] / 2, p.get("x", 0) + p["w"] / 2)
    if s == "plan":
        f, x = zip(*[q[:2] for q in p["pts"]])
        return min(f), max(f), min(p["u0"], p["u1"]), max(p["u0"], p["u1"]), min(x), max(x)
    if s == "xprof":
        x, u = zip(*[q[:2] for q in p["pts"]])
        return (min(p["f0"], p["f1"]), max(p["f0"], p["f1"]), p["cu"] + min(u), p["cu"] + max(u),
                p.get("cx", 0) + min(x), p.get("cx", 0) + max(x))
    if s in ("frame", "xbox"):
        w, h = (p["ow"], p["oh"]) if s == "frame" else (p["ww"], p["hh"])
        return (min(p["f0"], p["f1"]), max(p["f0"], p["f1"]), p["cu"] - h / 2, p["cu"] + h / 2,
                p.get("cx", 0) - w / 2, p.get("cx", 0) + w / 2)
    if s == "cyl":
        r = max(p["r"], p.get("r1", p["r"]))
        a0, a1 = min(p["a0"], p["a1"]), max(p["a0"], p["a1"])
        c0, c1 = p["c"][:2]
        if p["axis"] == "f":
            return a0, a1, c0 - r, c0 + r, c1 - r, c1 + r
        if p["axis"] == "u":
            return c0 - r, c0 + r, a0, a1, c1 - r, c1 + r
        return c0 - r, c0 + r, c1 - r, c1 + r, a0, a1
    if s == "tube":
        f, u, x = zip(*[tuple(q) + (0,) * (3 - len(q)) for q in p["path"]])
        return min(f) - p["r"], max(f) + p["r"], min(u) - p["r"], max(u) + p["r"], min(x) - p["r"], max(x) + p["r"]
    if s == "text":
        return p["f"], p["f"], p["u"], p["u"], p.get("x", 0), p.get("x", 0)
    raise ValueError(f"{p.get('id')}: Form {s}")


def silhouette(p) -> CrossSection:
    """Seitenansicht eines Teils (f, u)."""
    s = p.get("shape", "box")
    if s == "prof":
        return poly([tuple(q[:2]) for q in p["pts"]])
    if s == "cyl" and p["axis"] == "f":
        c, r, r1 = p["c"][0], p["r"], p.get("r1", p["r"])
        return poly([(p["a0"], c - r), (p["a1"], c - r1), (p["a1"], c + r1), (p["a0"], c + r)]) if p["a1"] > p["a0"] else \
            poly([(p["a1"], c - r1), (p["a0"], c - r), (p["a0"], c + r), (p["a1"], c + r1)])
    if s == "multi":
        return union([silhouette(q) for q in p["items"]])
    if s == "tube":
        quads = []
        for a, b in zip(p["path"], p["path"][1:]):
            d = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
            nf, nu = -(b[1] - a[1]) / d * p["r"], (b[0] - a[0]) / d * p["r"]
            quads.append(poly([(a[0] + nf, a[1] + nu), (a[0] - nf, a[1] - nu), (b[0] - nf, b[1] - nu), (b[0] + nf, b[1] + nu)]))
        return union(quads)
    b = bounds(p)
    return rect(b[0], b[1], b[2], b[3]) if b[1] > b[0] and b[3] > b[2] else CrossSection()


def _rotate(point, pivot, axis, deg):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    i, j = {"x": (0, 1), "f": (1, 2), "u": (0, 2)}[axis]
    q = list(point)
    d0, d1 = q[i] - pivot[i], q[j] - pivot[j]
    q[i], q[j] = pivot[i] + d0 * ca - d1 * sa, pivot[j] + d0 * sa + d1 * ca
    return q


def swept(p, parents):
    """Ausdehnung über den ganzen Weg: eigene Bewegung und die aller Eltern (translate, rotate; andere Arten bleiben stehen)."""
    b = bounds(p)
    corners = [(f, u, x) for f in b[:2] for u in b[2:4] for x in b[4:6]]
    chain, q = [], p
    while q is not None:
        if q.get("move"):
            chain.append(q["move"])
        q = parents.get(q.get("parent_part"))
    for mv in chain:
        moved = list(corners)
        if mv.get("kind") == "translate":
            v = tuple(mv.get("vector_mm", (0, 0, 0))) + (0,) * 3
            moved += [tuple(c[i] + v[i] for i in range(3)) for c in corners]
        elif mv.get("kind") == "rotate" and mv.get("pivot") is not None:
            lo, hi = mv.get("range_deg", (0, 0))[:2] if isinstance(mv.get("range_deg"), (list, tuple)) else (0, 360)
            piv = tuple(mv["pivot"]) + (0,) * (3 - len(mv["pivot"]))
            for k in range(1, 9):
                moved += [tuple(_rotate(c, piv, mv.get("axis", "x"), lo + (hi - lo) * k / 8)) for c in corners]
        corners = moved
    a = np.asarray(corners, float)
    lo, hi = a.min(0), a.max(0)
    return float(lo[0]), float(hi[0]), float(lo[1]), float(hi[1]), float(lo[2]), float(hi[2])


# ------------------------------------------------------------------ Grundform lesen

class Zone:
    """Seitenfläche einer Baugruppe: Kontur, Baugruppe, Außenflächen links/rechts, bewegter Träger."""

    def __init__(self, name, area, asm, x0, x1, parent=None, ids=()):
        self.name, self.area, self.asm, self.x0, self.x1, self.parent, self.ids = name, area, asm, x0, x1, parent, set(ids)
        self.inner = None      # bei zusammengelegten Zonen: engste Außenfläche, bis dorthin reicht die Schale nach innen

    def face(self, side):
        return self.x1 if side > 0 else -self.x0

    def depth(self, side):
        """Wie tief eine Schale hinter die Außenfläche reicht (bis zur engsten Stelle, sonst bleibt seitlich eine Lücke)."""
        return self.face(side) - (self.inner if self.inner is not None else self.face(side)) + 0.3


class Body:
    """Was die Sprachen über die Grundform wissen müssen; alle Maße gemessen aus den Teilen."""

    def __init__(self, model, num, kit, kind="flow"):
        self.model, self.num, self.kit, self.kind = model, num, kit, kind
        self.parts = model["PARTS"]
        self.by_id = {p["id"]: p for p in self.parts}
        self.ext = {p["id"]: bounds(p) for p in self.parts}
        self.sweep = {p["id"]: swept(p, self.by_id) for p in self.parts}
        A = model["ANCHORS"]
        self.muzzle = A["Socket_Muzzle"]["at"] if "Socket_Muzzle" in A else None
        self.eye = A["Socket_Eye"]["at"] if "Socket_Eye" in A else None
        self.bow = any(p["asm"] == "limbs" for p in self.parts)
        self.melee = num in ("16", "17")
        self.side_sight = self.eye is not None and abs(self.eye[2]) > SIDE_SIGHT_MM     # BASIC-14: Blick seitlich am Rohr vorbei, nicht darüber
        self.static = [p for p in self.parts if not self._moves(p) and p["asm"] not in ("sight",) and p.get("shape") != "text"]
        self.base = union([silhouette(p) for p in self.static])
        self.allow = self._allow()
        self.added = []

    def _moves(self, p):
        while p is not None:
            if p.get("move") and p["move"].get("kind") not in ("glow", None):
                return True
            p = self.by_id.get(p.get("parent_part"))
        return False

    def top(self, f, area=None):
        """Oberkante einer Fläche an der Stelle f (None außerhalb)."""
        return self._edge(f, area or self.base, max)

    def bottom(self, f, area=None):
        return self._edge(f, area or self.base, min)

    @staticmethod
    def _edge(f, area, pick):
        us = []
        for ring in area.to_polygons():
            a, b = ring, np.roll(ring, -1, axis=0)
            hit = (np.minimum(a[:, 0], b[:, 0]) <= f) & (f <= np.maximum(a[:, 0], b[:, 0])) & (a[:, 0] != b[:, 0])
            a, b = a[hit], b[hit]
            us += (a[:, 1] + (b[:, 1] - a[:, 1]) * (f - a[:, 0]) / (b[:, 0] - a[:, 0])).tolist()
        return pick(us) if us else None

    def _allow(self):
        f0, f1, u0, u1 = self.base.bounds()[0], self.base.bounds()[2], self.base.bounds()[1], self.base.bounds()[3]
        front = (self.muzzle[0] - MUZZLE_GAP_MM) if self.muzzle and not self.melee else f1 + 40
        if self.bow or self.melee or self.eye is None or self.side_sight:
            return rect(f0 - 40, front, u0 - 200, u1 + 200)
        rise = math.tan(math.radians(SIGHT_DEG))
        low = u0 - 200
        steps = [float(f) for f in np.arange(f0, front, 1.0)] + [float(front)]
        caps = []
        for f in steps:
            cap = self.top(f)
            cap = u0 if cap is None else cap + TOP_MM
            caps.append(max(cap, self.eye[1] - rise * (f - self.eye[0])) if f > self.eye[0] else cap)
        line = []                           # an Sprüngen der Oberkante gilt die kleinere Nachbarhöhe, dazwischen bleibt die Linie glatt
        for a, b, ca, cb in zip(steps, steps[1:], caps, caps[1:]):
            line += [(a, min(ca, cb)), (b, min(ca, cb))] if abs(ca - cb) > JUMP_MM else [(a, ca), (b, cb)]
        return poly([(f0, low), (front, low)] + line[::-1]).simplify(0.1)

    def room(self, f0, f1):
        """Höchste erlaubte Oberkante über einem Abschnitt (kleinster Wert von `allow`)."""
        tops = [self.top(float(f), self.allow) for f in np.linspace(f0, f1, 7)]
        room = min((t for t in tops if t is not None), default=-1e9)
        if self.side_sight and f1 > self.eye[0]:       # Blick neben dem Rohr: seitlich nicht über die Grundform (Schraubenköpfe mitgerechnet)
            ahead = [self.ext[p["id"]] for p in self.static if self.ext[p["id"]][1] > self.eye[0] and self.ext[p["id"]][5] < self.eye[2] - 5]
            room = min(room, self.muzzle[1] + max(max(abs(b[4]), abs(b[5])) for b in ahead) + TOP_MM - 2.0)
        return room

    def keepout(self, side, inner, outer, zone=None) -> CrossSection:
        """Freizonen einer Seite (+1 links, −1 rechts) für eine Schale zwischen den Beträgen inner und outer."""
        own = zone.ids if zone else set()
        areas = []
        for p in self.parts:
            if p["id"] in own or (zone and zone.parent and p.get("parent_part") == zone.parent):
                continue
            b = self.sweep[p["id"]]
            far = b[5] if side > 0 else -b[4]
            hard = p["asm"] in HARD_ASM or p["mat"] == "rubber" or "well" in p["id"] or "lip" in p["id"]
            live = p["mat"] in GLOW_ROLES or self._moves(p)
            if hard:
                m = HAND_MM
            elif live and far >= inner - 1.0:
                m = MARGIN_MM
            elif not live and far > outer + 0.5:
                m = MARGIN_MM
            else:
                continue
            areas.append(rect(b[0] - m, b[1] + m, b[2] - m, b[3] + m))
        for name, pt in self.model.get("POINTS", {}).items():
            f, u, x = pt["at"]
            if name == "grip.support":
                a, lo, hi = SUPPORT_MM
                areas.append(rect(f - a, f + a, u - lo, u + hi))
            elif name.startswith("grip."):
                n = HAND_SHAPE[self.kind]
                areas.append(circle(f, u, HAND_R_MM, n) if n else rect(f - HAND_R_MM, f + HAND_R_MM, u - HAND_R_MM, u + HAND_R_MM))
            elif name.startswith("eject") and x * side > 0:
                a, h = EJECT_MM
                areas.append(rect(f - a, f + a, u - h, u + h))
        return union(areas)

    def fit(self, area, side, inner, outer, zone, strip=MIN_STRIP_MM):
        """Fläche auf `allow` begrenzen und um die Freizonen schneiden; die Aussparung spricht die Formensprache der Serie
        (facet: gefaste Ecken, flow: gerundet, bench/block: rechtwinklig)."""
        keep = self.keepout(side, inner, outer, zone)
        if self.kind == "facet":
            keep = keep.offset(FACE_MM, JoinType.Bevel)
        elif self.kind == "flow":
            keep = keep.offset(FACE_MM, JoinType.Round, circular_segments=24)
        cut = clean((area ^ self.allow) - keep, strip)
        if self.kind == "flow" and strip >= MIN_STRIP_MM:
            cut = cut.offset(-ROUND_MM, JoinType.Round, circular_segments=24).offset(ROUND_MM, JoinType.Round, circular_segments=24).simplify(0.15)
        return (cut ^ self.allow).simplify(0.1)    # Öffnen mit Gehrung kann Spitzen wenige Zehntel über die Grenze schieben

    # -------------------------------------------------------------- Teile anlegen

    def add(self, pid, de, en, asm, shape, mat, func, attach, bevel=0.8, parent=None, **geo):
        if parent:
            geo["parent_part"] = parent
        p = self.kit("part", pid, de, en, asm, shape, mat, func, attach, bevel=bevel, **geo)
        self.added.append(p)
        return p

    def plate(self, zone, area, side, t, mat, pid, de, en, inset=0.3, bevel=0.8, func=GRAPHIC, smooth=False, lift=0.0, segs=None,
              strip=MIN_STRIP_MM, least=MIN_AREA_MM2):
        """Flache Schale auf der Seitenfläche einer Zone, gegen die Freizonen geschnitten; Rückgabe: Fläche, die wirklich entstand."""
        face = zone.face(side) + lift
        cut = self.fit(area, side, face - inset, face + t, zone, strip)
        kept = []
        for i, (ring, holes, piece) in enumerate(outlines(cut)):
            if piece.area() < least:
                continue
            geo = dict(pts=ring, w=t + inset, x=side * (face + (t - inset) / 2))
            if holes:
                geo["cuts"] = [dict(shape="prof", pts=h, w=t + inset + 2, x=geo["x"]) for h in holes]
            if smooth:
                geo["smooth"] = True
            if segs:
                geo["segs_bevel"] = segs
            sfx = "l" if side > 0 else "r"
            self.add(f"{pid}_{sfx}{i + 1}", f"{de} {'links' if side > 0 else 'rechts'} {i + 1}", f"{en} {'left' if side > 0 else 'right'} {i + 1}",
                     zone.asm, "prof", mat, func, f"außen auf {zone.name}", bevel=bevel, parent=zone.parent, **geo)
            kept.append(piece)
        return union(kept)


def zones(body: Body):
    """Seitenzonen der Grundform: je Familie die großen festen Flächen, an denen Schalen sitzen."""
    B, out = body, []
    num = B.num

    def make(name, parts, clip=None, parent=None, asm=None):
        parts = list(parts)
        if not parts:
            return None
        area = union([silhouette(p) for p in parts])
        if clip is not None:
            area = area ^ clip
        if area.is_empty():
            return None
        hosts = [B.ext[p["id"]] for p in parts]
        x0, x1 = min(h[4] for h in hosts), max(h[5] for h in hosts)
        lo = area.bounds()
        for p in B.parts:                     # flach aufliegende feste Teile (Paneele, Panzerplatten) zählen zur Fläche
            b = B.ext[p["id"]]
            if p in parts or B._moves(p) or p["asm"] in HARD_ASM or p["asm"] == "sight" or p["mat"] in GLOW_ROLES:
                continue
            if b[0] < lo[2] and b[1] > lo[0] and b[2] < lo[3] and b[3] > lo[1]:
                if x1 < b[5] <= x1 + 3.5:
                    x1 = b[5]
                if x0 - 3.5 <= b[4] < x0:
                    x0 = b[4]
        return Zone(name, area, asm or parts[0]["asm"], x0, x1, parent, [p["id"] for p in parts])

    def big(p, length=45.0):
        b = B.ext[p["id"]]
        return p.get("shape") in ("prof", "box", "plan", "cyl") and (b[1] - b[0] >= length or b[3] - b[2] >= length) and \
            p["mat"] not in GLOW_ROLES and p["mat"] not in ("rubber", "metal", "trim") and not SKIP_ZONE.search(p["id"])

    if B.bow:
        out.append(make("Mittelstück", [B.by_id["riser"]]))
        for pid, name in (("limb_top", "Wurfarm oben"), ("limb_bottom", "Wurfarm unten")):
            out.append(make(name, [B.by_id[pid]]))
        return [z for z in out if z]
    if num == "16":
        out.append(make("Klingenrücken", [B.by_id["blade_spine"], B.by_id["blade_core"]]))
        out.append(make("Parierstück", [B.by_id["guard"]]))
        return [z for z in out if z]
    if num == "17":
        out.append(make("Kern", [B.by_id["core"]]))
        out.append(make("Klingenfuß", [B.by_id["blade_mount"]]))
        return [z for z in out if z]
    moving = MOVING_HOSTS.get(num, ())
    for pid in moving:
        out.append(make("Schlitten", [B.by_id[pid]], parent=pid, asm=B.by_id[pid]["asm"]))
    stock = [p for p in B.parts if p["asm"] == "stock" and big(p) and not B._moves(p)]
    main = [p for p in B.parts if p["asm"] in ("receiver", "support", "barrel") and big(p) and not B._moves(p)
            and not (p.get("shape") == "cyl" and (p.get("axis") != "f" or p["r"] < 14 or num == "14"))]   # 14: Rohr bekommt Mäntel, keine Tangentenplatten
    if not main:
        return [z for z in out if z]
    ends = [B.ext[p["id"]][1] for p in main if p["id"] in ("lower", "receiver", "frame", "upper")]
    split = max(ends) if ends else 0.0
    far = B.muzzle[0] + 50 if B.muzzle else max(B.ext[p["id"]][1] for p in main) + 50
    near = min(B.ext[p["id"]][0] for p in main) - 50
    rear = [p for p in main if B.ext[p["id"]][0] < split]
    fore = [p for p in main if B.ext[p["id"]][1] > split]
    out.append(make("Gehäuse", rear, rect(near, split, -500, 500)))
    out.append(make("Vorderteil" if num in ("04", "05") else "Vorderschaft", fore, rect(split, far, -500, 500), asm=fore[-1]["asm"] if fore else None))
    if stock:
        out.append(make("Schaft", stock))
    return [z for z in out if z]


# ------------------------------------------------------------------ Bausteine der Sprachen

def contains(area: CrossSection, pts) -> np.ndarray:
    """Punkte (n, 2) in der Fläche (gerade-ungerade über alle Ringe)."""
    pts = np.asarray(pts, float)
    hit = np.zeros(len(pts), bool)
    for ring in area.to_polygons():
        a, b = ring, np.roll(ring, -1, axis=0)
        for (f0, u0), (f1, u1) in zip(a, b):
            if u0 == u1:
                continue
            cross = ((u0 > pts[:, 1]) != (u1 > pts[:, 1])) & (pts[:, 0] < f0 + (pts[:, 1] - u0) * (f1 - f0) / (u1 - u0))
            hit ^= cross
    return hit


def merge(zs, name="Körper"):
    """Mehrere Zonen als eine Fläche; Außenfläche = die weiteste, die Schale reicht innen bis zur engsten."""
    z = Zone(name, union([q.area for q in zs]), zs[0].asm, min(q.x0 for q in zs), max(q.x1 for q in zs), None,
             set().union(*[q.ids for q in zs]))
    z.inner = min(min(q.x1 for q in zs), min(-q.x0 for q in zs))
    return z


def spans(B: Body):
    """Runde Abschnitte, die als Rohr verkleidet werden können: [(f0, f1, cu, r)] in der Reihenfolge von hinten nach vorn."""
    P, E = B.by_id, B.ext
    if B.num == "14":
        return [(E["rear_tube"][0] + 40, min(E["rear_tube"][1] - 30, B.eye[0] - 4), P["rear_tube"]["c"][0], P["rear_tube"]["r"]),
                (E["load_hatch"][1] + 22, E["tube"][1] - 18, P["tube"]["c"][0], P["tube"]["r"])]
    if B.num == "17":
        c, r = P["shaft"]["c"][0], P["shaft"]["r"]
        return [(E["shaft"][0] + 20, E["core"][0] - 20, c, r), (E["core"][1] + 15, E["support_grip"][0] - 10, c, r),
                (E["support_grip"][1] + 10, E["shield_l"][0] - 5, c, r)]
    if B.bow or B.num == "16" or "barrel" not in P or P["barrel"].get("shape") != "cyl":
        return []
    body = [E[i] for z in B.zones if z.name in ("Gehäuse", "Vorderschaft", "Vorderteil", "Schlitten") for i in z.ids if i not in ("muzzle", "emitter")]
    end = max((e[1] for e in body), default=E["barrel"][0])
    mz = E["muzzle"][0] if "muzzle" in E else E["barrel"][1]
    return [(end, mz, P["barrel"]["c"][0], P["barrel"]["r"])] if mz - end >= 30 else []


def clear_stations(B: Body, lo, hi, width, step=6.0):
    """Stellen f in [lo, hi], an denen ein Band der Breite `width` um den Körper frei von Freizonen liegt."""
    out = []
    keep = union([B.keepout(1, 20, 26), B.keepout(-1, 20, 26)])
    rails = union([rect(B.ext[p["id"]][0] - 3, B.ext[p["id"]][1] + 3, -999, 999) for p in B.parts
                   if p["id"] == "rail" or p["asm"] == "sight"])
    block = keep + rails
    f = lo
    while f <= hi:
        t, b = B.top(f), B.bottom(f)
        band = rect(f - width / 2, f + width / 2, b - 4, t + 3) if t is not None and b is not None else None
        if band is not None and (band ^ block).area() < 1 and (band - B.allow).area() < 1:
            out.append(round(float(f), 1))
        f += step
    return out


def pick(items, n):
    """n Einträge gleichmäßig über die Liste."""
    if len(items) <= n:
        return list(items)
    return [items[round(i * (len(items) - 1) / (n - 1))] for i in range(n)] if n > 1 else [items[len(items) // 2]]


def hexbolts(pts, x, r=3.0, h=2.0):
    s = 1 if x > 0 else -1
    return [dict(shape="cyl", axis="x", c=tuple(p), a0=x - s * 0.5, a1=x + s * h, r=r, segs=6) for p in pts]


# ------------------------------------------------------------------ facet: Stealth

def cheek(B: Body, zone, area, side, t, mat, pid, de, en, inner=None, bevel=0.5, chamfer=2.6):
    """Facettenschale: Querprofil mit oberer und unterer Schräge, Kontur als Schnitt; je Teilfläche ein xprof."""
    face = zone.face(side)
    start = inner if inner is not None else face - 0.3
    cut = B.fit(area, side, start, face + t, zone)
    kept = []
    for i, (_, _, piece) in enumerate(outlines(cut)):
        if piece.area() < MIN_AREA_MM2:
            continue
        f0, u0, f1, u1 = piece.bounds()
        h = u1 - u0
        c = min(h * 0.36, t * chamfer)
        outer_x = face + t
        cuts = [dict(shape="prof", pts=r, w=outer_x - start + 4, x=side * (start + outer_x) / 2) for r in negative(piece)]
        section = [(start, -h / 2), (outer_x, -h / 2 + c), (outer_x, h / 2 - c), (start, h / 2)]
        if side < 0:
            section = [(-x, u) for x, u in reversed(section)]
        sfx = "l" if side > 0 else "r"
        B.add(f"{pid}_{sfx}{i + 1}", f"{de} {'links' if side > 0 else 'rechts'} {i + 1}", f"{en} {'left' if side > 0 else 'right'} {i + 1}",
              zone.asm, "xprof", mat, GRAPHIC, f"außen auf {zone.name}", bevel=bevel, parent=zone.parent,
              f0=round(f0, 2), f1=round(f1, 2), cu=round((u0 + u1) / 2, 2), pts=[(round(x, 2), round(u, 2)) for x, u in section], cuts=cuts)
        kept.append(piece)
    return union(kept)


def negative(piece):
    """Umgebung einer Fläche im Rahmen (+3 mm) als einfache Polygone: an der Mitte geteilt, damit der Ring zwei C-Formen ergibt."""
    f0, u0, f1, u1 = piece.bounds()
    mid = (f0 + f1) / 2
    rest = rect(f0 - 3, f1 + 3, u0 - 3, u1 + 3) - piece
    return [r for half in (rect(f0 - 4, mid, u0 - 4, u1 + 4), rect(mid, f1 + 4, u0 - 4, u1 + 4)) for r, _, _ in outlines(rest ^ half)]


def facet_outline(area, eps, grow=1.5):
    return area.hull().offset(grow, JoinType.Miter, 3.0).simplify(eps)


def facet(B: Body):
    Z = {z.name: z for z in B.zones}
    main = [Z[n] for n in ("Gehäuse", "Vorderschaft", "Vorderteil") if n in Z]
    run = spans(B)
    if main:
        z = merge(main)
        tip = []
        if B.muzzle and not B.melee and not B.bow:
            mf, mu = B.muzzle[0], B.muzzle[1]
            end = run[-1][1] if run and B.num != "14" else mf
            tip = [circle(end - 6, mu, 6.0, 8)]
        out = facet_outline(union([z.area] + tip), 7.0)
        for side in (1, -1):
            got = cheek(B, z, out, side, 5.0, "shell", "facet_cheek", "Facettenschale", "Facet cheek", inner=z.inner - 0.3)
            if not got.is_empty():
                facet_detail(B, z, got, side, 5.0)
    for z in B.zones:
        if z.name in ("Gehäuse", "Vorderschaft", "Vorderteil"):
            continue
        out = facet_outline(z.area, 5.0, 1.0)
        for side in (1, -1):
            cheek(B, z, out, side, 3.5 if z.name != "Klingenrücken" else 1.6, "shell", f"facet_{_slug(z.name)}", f"Facette {z.name}", f"Facet {_slug(z.name)}")
    facet_spans(B, run)


def facet_spans(B, run):
    for i, (f0, f1, cu, r) in enumerate(run):
        lead = 0 if B.num in ("14", "17") else 12
        if B.num == "14":                       # Rohr ohne Schalen: Leuchtring an jedem Mantel
            B.add(f"facet_ring_{i + 1}", f"Leuchtring {i + 1}", f"Ice ring {i + 1}", _span_asm(B), "cyl", "energy", f"{GRAPHIC}: Leuchtführung", "am Mantel", bevel=0,
                  axis="f", c=(cu, 0.0), a0=f1 - 14.0, a1=f1 - 11.0, r=r + 5.5, segs=6)
        B.add(f"facet_sleeve_{i + 1}", f"Sechskantmantel {i + 1}", f"Hex sleeve {i + 1}", _span_asm(B), "cyl", "shell" if B.num == "14" else "anodized", GRAPHIC, "um das Rohr geklemmt", bevel=0.5,
              axis="f", c=(cu, 0.0), a0=f0 - lead, a1=f1, r=max(min(r + (5.0 if B.num == "14" else 11.0), B.room(f0 - lead, f1) - cu), r + 1.0), r1=r + (5.0 if B.num == "14" else 1.0), segs=6)


def slant(f0, f1, u0, u1, lean=.8):
    """Parallelogramm mit schrägen Enden (Formensprache Stealth)."""
    d = (u1 - u0) * lean
    return poly([(f0, u0), (f1, u0), (f1 + d, u1), (f0 + d, u1)])


def facet_detail(B, z, got, side, t):
    """Auf dem flachen Band der Schale: Leuchtkante, dunkle Felder, schräge Schlitze."""
    f0, u0, f1, u1 = got.bounds()
    h = u1 - u0
    c = min(h * .36, t * 2.6)
    lo, hi = u0 + c, u1 - c
    top = Zone(z.name, z.area, z.asm, z.x0 - t, z.x1 + t, None, z.ids)
    mid = lo + (hi - lo) * .34
    B.plate(top, rect(f0, f1, mid - .9, mid + .9) ^ got, side, .6, "energy", "facet_ice", "Leuchtkante", "Ice edge", inset=.15, bevel=.1,
            func=f"{GRAPHIC}: Leuchtführung", strip=1.0, least=20.0)
    L = f1 - f0
    fields = [slant(f0 + L * a, f0 + L * b, mid + 3.0, hi - 1.0) for a, b in ((.10, .24), (.30, .52), (.58, .72))]
    B.plate(top, union(fields) ^ got, side, .5, "graphite", "facet_field", "Dunkles Feld", "Dark field", inset=.15, bevel=.15, least=60.0)
    vents = [slant(f0 + L * .78 + i * 11.0, f0 + L * .78 + i * 11.0 + 5.0, lo + 2.0, mid - 3.0, 1.0) for i in range(4)]
    B.plate(top, union(vents) ^ got, side, .5, "anodized", "facet_vent", "Schrägschlitze", "Slant vents", inset=.15, bevel=.1, strip=2.0, least=15.0)


def _span_asm(B):
    for a in ("barrel", "shaft", "receiver"):
        if any(p["asm"] == a for p in B.parts):
            return a
    return B.parts[0]["asm"]


def _slug(name):
    return {"Gehäuse": "body", "Vorderschaft": "fore", "Vorderteil": "fore", "Schaft": "stock", "Wurfarm oben": "limb_top", "Wurfarm unten": "limb_bottom", "Mittelstück": "riser", "Klingenrücken": "blade", "Parierstück": "guard", "Kern": "core",
            "Klingenfuß": "mount", "Schlitten": "slide"}.get(name, "zone")


# ------------------------------------------------------------------ bench: Werkstatt-Prototyp

BOLT_MM = 7.0          # Annahme: Schraube sitzt so weit von der Plattenkante
BAND_MM = 14.0         # Annahme: Klemmband 14 mm breit
FIN_PITCH_MM, FIN_MM = 9.0, 3.5   # Annahme: Kühlrippen 3,5 mm dick im Abstand 9 mm


def chamfered(area, c=5.0):
    return area.offset(-c, JoinType.Miter, 2.0).offset(c, JoinType.Bevel)


def holes(f0, f1, u, r, pitch):
    n = max(int((f1 - f0) // pitch), 0)
    start = (f0 + f1) / 2 - (n - 1) * pitch / 2
    return [circle(start + i * pitch, u, r, 12) for i in range(n)]


def bench_plate(B, z, area, side, t, mat, pid, de, en):
    got = B.plate(z, area, side, t, mat, pid, de, en, bevel=0.6)
    if got.is_empty():
        return got
    x = side * (z.face(side) + t)
    pts = []
    for ring, _, piece in outlines(got):
        f0, u0, f1, u1 = piece.bounds()
        for f in (f0 + BOLT_MM, f1 - BOLT_MM):
            for u in (u0 + BOLT_MM, u1 - BOLT_MM):
                if contains(piece.offset(-3.5, JoinType.Miter, 2.0), [(f, u)])[0]:
                    pts.append((round(f, 2), round(u, 2)))
    if pts:
        B.add(f"{pid}_bolts_{'l' if side > 0 else 'r'}", f"{de} Schrauben", f"{en} bolts", z.asm, "multi", "trim", "Hält die Platte (Sechskant)",
              f"in {z.name} geschraubt", bevel=0.3, parent=z.parent, items=hexbolts(pts, x, 2.6, 1.8))
    return got


def bench_band(B, z, f, i):
    t, b = B.top(f, z.area), B.bottom(f, z.area)
    if t is None or b is None:
        return
    cu = (t + b) / 2
    x0, x1 = z.x0, z.x1
    cx = (x0 + x1) / 2
    w, h = x1 - x0, t - b
    B.add(f"bench_band_{i}", f"Klemmband {i}", f"Clamp band {i}", z.asm, "frame", "accent", f"{GRAPHIC}: hält die Schalen zusammen",
          "um den Körper gespannt", bevel=0.6, f0=f - BAND_MM / 2, f1=f + BAND_MM / 2, cu=round(cu, 2), cx=round(cx, 2), ow=round(w + 6, 2), oh=round(h + 6, 2),
          iw=round(w + 0.4, 2), ih=round(h + 0.4, 2), r_out=2.0, r_in=1.0)
    pts = [(f, round(t - 7, 2)), (f, round(b + 7, 2))]
    B.add(f"bench_band_{i}_bolts", f"Klemmband {i} Schrauben", f"Clamp band {i} bolts", z.asm, "multi", "trim", "Spannt das Klemmband (Sechskant)",
          "im Klemmband", bevel=0.3, items=hexbolts(pts, x1 + 3, 3.0, 2.2) + hexbolts(pts, x0 - 3, 3.0, 2.2))


def bench_hose(B, z, fa, fb):
    """Schlauch von Klemmband zu Klemmband, außen an der Seite durchhängend; Seite, auf der er keine Freizone kreuzt."""
    for side in (1, -1):
        face = z.face(side) + 3
        keep = B.keepout(side, face, face + 16, z)
        ua, ub = B.top(fa, z.area), B.top(fb, z.area)
        if ua is None or ub is None:
            continue
        ua, ub = ua - 9, ub - 9
        mid = (fa + fb) / 2
        sag = min(ua, ub) - 16
        path = [(fa, ua, side * face), (fa + (fb - fa) * .2, ua - 8, side * (face + 7)), (mid, sag, side * (face + 10)),
                (fb - (fb - fa) * .2, ub - 8, side * (face + 7)), (fb, ub, side * face)]
        line = [(a[0] + (b[0] - a[0]) * k / 8, a[1] + (b[1] - a[1]) * k / 8) for a, b in zip(path, path[1:]) for k in range(8)]
        if not contains(keep, line).any():
            sfx = "l" if side > 0 else "r"
            B.add(f"bench_hose_{sfx}", "Kühlschlauch", "Coolant hose", z.asm, "tube", "graphite", f"{GRAPHIC}: Prototyp-Leitung", "an den Klemmbändern",
                  bevel=0, path=[tuple(round(v, 2) for v in q) for q in path], r=3.2)
            return True
    return False


def bench_fins(B, run):
    for k, (f0, f1, cu, r) in enumerate(run):
        n = int((f1 - f0 - 10) // FIN_PITCH_MM)
        if n < 2:
            continue
        rear = B.side_sight and f1 < B.eye[0]        # hinter dem Auge liegt nichts im Blick: Rohr darf kräftiger tragen
        side = 2 * max(min(r + (14.0 if rear else 9.0), B.room(f0, f1) - cu), r + 1.0)
        start = (f0 + f1) / 2 - (n - 1) * FIN_PITCH_MM / 2
        B.add(f"bench_fins_{k + 1}", f"Kühlrippen {k + 1}", f"Cooling fins {k + 1}", _span_asm(B), "multi", "dark_metal", f"{GRAPHIC}: Kühlkörper", "auf das Rohr gepresst",
              bevel=0.3, items=[dict(shape="xbox", f0=round(start + i * FIN_PITCH_MM - FIN_MM / 2, 2), f1=round(start + i * FIN_PITCH_MM + FIN_MM / 2, 2), cu=cu, ww=side, hh=side)
                                for i in range(n)])


def muzzle_box(B, length=26.0, grow=7.0):
    """Maße eines Kastens um das Mündungsteil: (f0, f1, cu, Kante) oder None."""
    if "muzzle" not in B.by_id or B.by_id["muzzle"].get("shape") != "cyl" or B.muzzle is None:
        return None
    m = B.by_id["muzzle"]
    f1 = B.muzzle[0] - 5.0
    r = max(m["r"], m.get("r1", m["r"]))
    half = min(r + grow, B.room(f1 - length, f1) - m["c"][0])
    return (f1 - length, f1, m["c"][0], 2 * half) if half >= r else None


def bench(B: Body):
    Z = {z.name: z for z in B.zones}
    run = spans(B)
    main = [Z[n] for n in ("Gehäuse", "Vorderschaft", "Vorderteil") if n in Z]
    for z in B.zones:
        f0, u0, f1, u1 = z.area.bounds()
        h = u1 - u0
        slug = _slug(z.name)
        if z.name in ("Gehäuse", "Vorderschaft", "Vorderteil"):
            mid = (B.top((f0 + f1) / 2, z.area) + B.bottom((f0 + f1) / 2, z.area)) / 2 + 4 if B.top((f0 + f1) / 2, z.area) is not None else (u0 + u1) / 2
            hh = min(20.0, h * .36)
            slab = rect(f0 + 8, f1 - 8, mid - hh, mid + hh)
            strip = holes(f0 + 22, f1 - 22, mid, 3.4, 15.0)
            area = chamfered(slab, 6.0) - union(strip)
            for side in (1, -1):
                bench_plate(B, z, area, side, 3.0, "dark_metal", f"bench_rail_{slug}", f"Lochschiene {z.name}", f"Drilled rail {slug}")
        elif z.name == "Schaft":
            area = chamfered(z.area.hull().offset(-3, JoinType.Miter, 2.0), 7.0)
            c = area.bounds()
            big = [circle(c[0] + (c[2] - c[0]) * k, (c[1] + c[3]) / 2, 11.0, 16) for k in (.33, .66)]
            for side in (1, -1):
                bench_plate(B, z, area - union(big), side, 3.0, "dark_metal", "bench_stock", "Schaftplatte", "Stock plate")
        else:
            area = chamfered(z.area.hull().offset(-1, JoinType.Miter, 2.0), 5.0)
            area = area - union(holes(f0 + 16, f1 - 16, (u0 + u1) / 2, 3.0, 14.0)) if f1 - f0 > h else area
            for side in (1, -1):
                bench_plate(B, z, area, side, 2.4 if z.name != "Klingenrücken" else 1.4, "dark_metal", f"bench_{slug}", f"Platte {z.name}", f"Plate {slug}")
    placed = []
    fixed = [z for z in main if not z.parent and not any(q.parent for q in B.zones)]
    for z in B.zones:                       # bewegter Träger: Bänder kämen dem Schlitten in den Weg, Klemmbacken laufen als Kinder mit
        if z.parent:
            f0, u0, f1, u1 = z.area.bounds()
            backs = union([rect(f0 + (f1 - f0) * k - BAND_MM / 2, f0 + (f1 - f0) * k + BAND_MM / 2, u0, u1) for k in (.28, .62, .9)])
            for side in (1, -1):
                B.plate(z, backs, side, 4.5, "accent", "bench_jaw", "Klemmbacke", "Clamp jaw", bevel=0.6, func=f"{GRAPHIC}: hält die Schalen zusammen")
    if fixed:
        z = merge(fixed)
        f0, u0, f1, u1 = z.area.bounds()
        free = clear_stations(B, f0 + 14, min(f1 - 14, (B.muzzle[0] if B.muzzle else f1) - 2 * BAND_MM), BAND_MM + 2)
        for i, f in enumerate(pick(free, 3)):
            bench_band(B, z, f, i + 1)
            placed.append(f)
        if len(placed) >= 2:
            bench_hose(B, z, placed[0], placed[-1])
    bench_fins(B, run)
    box = muzzle_box(B)
    if box:
        f0, f1, cu, e = box
        B.add("bench_head", "Prüfkopf", "Test head", _span_asm(B), "xbox", "accent", f"{GRAPHIC}: Prüfkopf an der Mündung", "auf die Mündung geklemmt", bevel=0.8,
              f0=f0, f1=f1, cu=cu, ww=e, hh=e,
              cuts=[dict(shape="cyl", axis="x", c=(round((f0 + f1) / 2, 2), cu), a0=-e, a1=e, r=4.5, segs=12)])
        pts = [(f0 + 5, cu + e / 2 - 5), (f1 - 5, cu + e / 2 - 5), (f0 + 5, cu - e / 2 + 5), (f1 - 5, cu - e / 2 + 5)]
        B.add("bench_head_bolts", "Prüfkopf Schrauben", "Test head bolts", _span_asm(B), "multi", "trim", "Klemmt den Prüfkopf (Sechskant)", "im Prüfkopf",
              bevel=0.3, items=hexbolts(pts, e / 2, 2.2, 1.4) + hexbolts(pts, -e / 2, 2.2, 1.4))


# ------------------------------------------------------------------ block: Cube-Farbwelt

CELL_MM, GAP_MM = 24.0, 2.0   # Annahme: Raster 24 mm (zwei Fingerbreiten), Fuge 2 mm wie doppelte BALLON-Fuge SEAM
BLOCK_ROLES = (("shell", 6.0), ("graphite", 3.5), ("shell", 6.0), ("accent", 8.0), ("graphite", 3.5), ("shell", 6.0))


def _roll(*key):
    return int(hashlib.sha256("|".join(map(str, key)).encode()).hexdigest()[:8], 16)


def block_rows(B, z, side):
    """Rasterzellen einer Zone als Läufe: {(Rolle, Dicke): [Rechtecke]}; Zellen in Freizonen oder außerhalb von `allow` entfallen."""
    f0, u0, f1, u1 = z.area.bounds()
    keep = B.keepout(side, z.face(side), z.face(side) + 8, z)
    near = z.area.offset(3.0, JoinType.Miter, 2.0)
    out = {}
    start = _roll(B.num, z.name) % len(BLOCK_ROLES)
    j0, j1 = math.floor(u0 / CELL_MM), math.ceil(u1 / CELL_MM)
    i0, i1 = math.floor(f0 / CELL_MM), math.ceil(f1 / CELL_MM)
    for j in range(j0, j1):
        cells = []
        for i in range(i0, i1 + 1):
            c = rect(i * CELL_MM + GAP_MM / 2, (i + 1) * CELL_MM - GAP_MM / 2, j * CELL_MM + GAP_MM / 2, (j + 1) * CELL_MM - GAP_MM / 2)
            ok = (c ^ near).area() >= .55 * c.area() and (c - B.allow).area() < 1 and (c ^ keep).area() < 1
            cells.append(i if ok else None)
        run, runs = [], []
        for i in cells + [None]:
            if i is None:
                if run:
                    runs.append(run)
                run = []
            else:
                run.append(i)
                if len(run) >= 2 + _roll(B.num, z.name, j, run[0]) % 4:
                    runs.append(run)
                    run = []
        for r in runs:
            role = BLOCK_ROLES[start % len(BLOCK_ROLES)]    # fortlaufend über alle Reihen: auch wenige Läufe zeigen alle Farben
            start += 1
            out.setdefault(role, []).append((r[0] * CELL_MM + GAP_MM / 2, (r[-1] + 1) * CELL_MM - GAP_MM / 2, j * CELL_MM + GAP_MM / 2, (j + 1) * CELL_MM - GAP_MM / 2))
    return out


def block(B: Body):
    run = spans(B)
    for z in B.zones:
        slug = _slug(z.name)
        scale = .35 if z.name == "Klingenrücken" else 1.0
        for side in (1, -1):
            sfx = "l" if side > 0 else "r"
            face = z.face(side)
            longest = None
            for (mat, t), cells in sorted(block_rows(B, z, side).items()):
                t *= scale
                items = [dict(shape="box", f0=a, f1=b, u0=c, u1=d, w=t + .3, x=side * (face + (t - .3) / 2)) for a, b, c, d in sorted(cells)]
                B.add(f"block_{slug}_{mat}_{sfx}", f"Farbblöcke {z.name} {'links' if side > 0 else 'rechts'}", f"Colour blocks {slug} {'left' if side > 0 else 'right'}",
                      z.asm, "multi", mat, GRAPHIC, f"außen auf {z.name}", bevel=0.7, parent=z.parent, items=items)
                for a, b, c, d in cells:
                    if longest is None or b - a > longest[1] - longest[0]:
                        longest = (a, b, c, d)
            if longest and z.name in ("Gehäuse", "Vorderschaft"):
                a, b, c, d = longest
                B.add(f"block_line_{slug}_{sfx}", "Fugenlinie", "Seam line", z.asm, "box", "energy", f"{GRAPHIC}: Leuchtführung", "in der Fuge", bevel=0.1,
                      f0=a, f1=b, u0=c - GAP_MM + .4, u1=c - .4, w=2.0, x=side * (face + 1.0))
    asm = _span_asm(B)
    for k, (f0, f1, cu, r) in enumerate(run):
        n = max(int((f1 - f0) // CELL_MM), 1)
        items = {"shell": [], "graphite": []}
        for i in range(n):
            a = f0 + i * CELL_MM + GAP_MM / 2
            e = 2 * max(min(r + 4.0 + 3.0 * (n - i if B.num not in ("14", "17") else 2), B.room(a, a + CELL_MM) - cu), r + 1.0)
            items["shell" if i % 2 == 0 else "graphite"].append(dict(shape="xbox", f0=round(a, 2), f1=round(a + CELL_MM - GAP_MM, 2), cu=cu, ww=round(e, 2), hh=round(e, 2)))
        for mat, its in items.items():
            if its:
                B.add(f"block_stair_{k + 1}_{mat}", f"Stufenblöcke {k + 1}", f"Stair blocks {k + 1}", asm, "multi", mat, GRAPHIC, "um das Rohr gesteckt", bevel=0.7, items=its)
    box = muzzle_box(B, 30.0, 8.0)
    if box:
        f0, f1, cu, e = box
        B.add("block_cube", "Mündungswürfel", "Muzzle cube", asm, "xbox", "accent", f"{GRAPHIC}: Würfel an der Mündung", "auf die Mündung gesteckt", bevel=0.9,
              f0=f0, f1=f1, cu=cu, ww=e, hh=e)


# ------------------------------------------------------------------ flow: organisch-glatt

WAVE = (.48, .16)      # Annahme: Teilungslinie bei 48 % der Höhe, Ausschlag ±16 %
GLOW_SEAM_MM = 1.1     # Annahme: Leuchtlinie in der Mitte der 2,2-mm-Fuge


def soft(area, r=9.0):
    """Konkave und konvexe Ecken runden (Schließen, dann Öffnen) und Kontur glätten."""
    closed = area.offset(r, JoinType.Round, circular_segments=24).offset(-2 * r, JoinType.Round, circular_segments=24).offset(r, JoinType.Round, circular_segments=24)
    return closed.simplify(0.25)


def wave_line(B, z, f0, f1, n=48):
    """Geschwungene Teilungslinie der Körperschale in (f, u)."""
    pts = []
    for i in range(n + 1):
        f = f0 + (f1 - f0) * i / n
        t, b = B.top(f, z.area), B.bottom(f, z.area)
        if t is None or b is None:
            continue
        s = i / n
        pts.append((f, b + (t - b) * (WAVE[0] + WAVE[1] * math.sin(2 * math.pi * s * 1.25 + .6))))
    return spline(pts, 2)


def flow_skin(B, z, slug):
    f0, u0, f1, u1 = z.area.bounds()
    body = soft(z.area.offset(2.0, JoinType.Round, circular_segments=24), 7.0)
    line = wave_line(B, z, f0 - 2, f1 + 2)
    if len(line) < 4:
        return
    upper = poly([(f0 - 40, u1 + 40), (f0 - 40, line[0][1])] + line + [(f1 + 40, line[-1][1]), (f1 + 40, u1 + 40)])
    top, low = soft(body ^ upper, 5.0), soft(body - upper.offset(2.2, JoinType.Round, circular_segments=16), 5.0)
    for side in (1, -1):
        B.plate(z, top, side, 4.5, "shell", f"flow_{slug}_top", f"Glatte Schale {z.name} oben", f"Smooth shell {slug} top", inset=z.depth(side),
                bevel=2.2, smooth=True, segs=3)
        B.plate(z, low, side, 3.0, "graphite", f"flow_{slug}_low", f"Glatte Schale {z.name} unten", f"Smooth shell {slug} low", inset=z.depth(side),
                bevel=1.6, smooth=True, segs=3)
        keep = B.keepout(side, z.face(side), z.face(side) + 5, z) + (rect(-2000, 2000, -2000, 2000) - B.allow)
        seam = [(a, b - GLOW_SEAM_MM) for a, b in line]      # Mitte der Fuge zwischen oberer und unterer Schale
        free = ~contains(keep, seam)
        runs, run = [], []
        for q, ok in zip(seam, free):
            if ok:
                run.append(q)
            else:
                if len(run) >= 8:
                    runs.append(run)
                run = []
        if len(run) >= 8:
            runs.append(run)
        for k, r in enumerate(runs):
            x = side * (z.face(side) + 1.2)
            B.add(f"flow_{slug}_glow_{'l' if side > 0 else 'r'}{k + 1}", "Leuchtlinie", "Glow line", z.asm, "tube", "energy", f"{GRAPHIC}: Leuchtführung", "in der Schalenfuge",
                  bevel=0, parent=z.parent, path=[(round(a, 2), round(b, 2), round(x, 2)) for a, b in r[::3]], r=1.0)


def spindle(B, k, f0, f1, cu, r, swell):
    n = 20
    items = []
    swell = max(min(swell, B.room(f0, f1) - cu - r - 1.2), 0.0)
    prof = [r + 1.2 + swell * math.sin(math.pi * (i / n) ** .8) ** 1.2 for i in range(n + 1)]
    for i in range(n):
        items.append(dict(shape="cyl", axis="f", c=(cu, 0.0), a0=round(f0 + (f1 - f0) * i / n, 2), a1=round(f0 + (f1 - f0) * (i + 1) / n, 2),
                          r=round(prof[i], 2), r1=round(prof[i + 1], 2), segs=32))
    B.add(f"flow_spindle_{k + 1}", f"Spindel {k + 1}", f"Spindle {k + 1}", _span_asm(B), "multi", "decal", GRAPHIC, "um das Rohr gelegt", bevel=0, items=items)
    ring = f0 + (f1 - f0) * .72
    rr = r + 1.2 + swell * math.sin(math.pi * .72 ** .8) ** 1.2 + .3
    B.add(f"flow_ring_{k + 1}", f"Leuchtring {k + 1}", f"Glow ring {k + 1}", _span_asm(B), "cyl", "energy", f"{GRAPHIC}: Leuchtführung", "in der Spindel", bevel=0,
          axis="f", c=(cu, 0.0), a0=round(ring, 2), a1=round(ring + 2.5, 2), r=round(rr, 2), segs=32)


def flow(B: Body):
    Z = {z.name: z for z in B.zones}
    main = [Z[n] for n in ("Gehäuse", "Vorderschaft", "Vorderteil") if n in Z and not Z[n].parent]
    if main:
        flow_skin(B, merge(main), "body")
    for z in B.zones:
        if z.name in ("Gehäuse", "Vorderschaft", "Vorderteil"):
            continue
        slug = _slug(z.name)
        if z.name == "Schaft":
            area = soft(z.area.hull(), 16.0)
            c = area.bounds()
            eye = poly([((c[0] + c[2]) / 2 + 30 * math.cos(a / 16 * 2 * math.pi), (c[1] + c[3]) / 2 + 13 * math.sin(a / 16 * 2 * math.pi) - 6) for a in range(16)])
            for side in (1, -1):
                B.plate(z, area - eye, side, 4.0, "shell", "flow_stock", "Glatte Schaftschale", "Smooth stock shell", bevel=2.0, smooth=True, segs=3)
        else:
            area = soft(z.area.offset(1.0, JoinType.Round, circular_segments=24), 6.0)
            for side in (1, -1):
                B.plate(z, area, side, 3.2 if z.name != "Klingenrücken" else 1.6, "shell", f"flow_{slug}", f"Glatte Schale {z.name}", f"Smooth shell {slug}",
                        bevel=1.4 if z.name != "Klingenrücken" else .5, smooth=True, segs=3)
    for k, (f0, f1, cu, r) in enumerate(spans(B)):
        spindle(B, k, f0 - 10, f1, cu, r, 12.0 if B.num not in ("14", "17") else 5.0)


LANGUAGES = {"facet": facet, "bench": bench, "block": block, "flow": flow}


def apply(model, kind, num, kit):
    """Verkleidung der Serie `kind` an `model` anhängen; Rückgabe: Generatorbericht."""
    B = Body(model, num, kit, kind)
    B.zones = zones(B)
    LANGUAGES[kind](B)
    ids = [p["id"] for p in model["PARTS"]]
    clash = sorted({p["id"] for p in B.added} & set(ids))
    if clash or len({p["id"] for p in B.added}) != len(B.added):
        raise ValueError(f"Serie {kind}: Teil-IDs doppelt: {clash}")
    model["PARTS"] += B.added
    return {"op": "series", "kind": kind, "zones": [z.name for z in B.zones], "added": [p["id"] for p in B.added]}
