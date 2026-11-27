"""EXTENDED-09 „Theodolite“ und EXTENDED-14 „Keelson“ (0.25 „Pauldron“): Scharfschützengewehr und Raketenwerfer als eigene Modelle.

Prüft die Datensätze ohne Blender: Felder und IDs, Blatt-IDs, Anker/Weltpunkte/Aktionen (BALLONs `variant.problems` als Orakel),
Familienschnittstellen, Budgets des Stilhandbuchs (genau ein Blickfang links außerhalb des Visiers, ≤ 3 Akzent-Bedienfunktionen, eine
Schrift, ein Grafikelement), Visierlinie (Z3 66 ± 4 mm über der Achse; W2 seitlich 66 ± 4 mm neben der Achse mit freier Sicht), Schrift
auf ebener Fläche, Seiten-IoU < 0,85 gegen BASIC-NN und jedes andere EXTENDED-Modell und < 0,70 im Paar (Rahmen aus den Hüllen beider
Modelle; Standardmaß und genaues Maß mit den Seitenschnitten der Querprofile), die Leitmotive (Stativ: Rautenrumpf auf drei Stützen mit
offenen Feldern, Libelle; Rumpf: Tropfenquerschnitt mit tiefem Bauch unter der Achse, Schultersattel als Wiege), gestaltete Querschnitte,
Detaildichte, die Absetzung der beiden Typen, Zusammenhang, Länge und Quellhash. Jede Regelprüfung hat eine Gegenprobe, die aus dem
erwarteten Grund rot wird; Felder, Quellhash und Snapshot-Freigabe sind Bestandsprüfungen.
"""
import copy
import importlib
import math
import re
import sys
import unittest

import numpy as np

from formgen import ballon, extended

try:
    SNAP = ballon.snapshot()
except ballon.BallonError as error:   # z. B. Cloud ohne BALLON-Checkout
    SNAP, REASON = None, str(error)
else:
    REASON = ""

IOU_MAX = 0.85                 # Annahme wie BALLON A1 und test_extended
PAIR_MAX = 0.70                # Annahme wie 0.18/0.22/0.23: die beiden Typen einer Sitzung setzen sich deutlich ab
SIGHT_H = (62.0, 70.0)         # Vorgabe Visier-Standard: Visierhöhe 66 ± 4 mm (Z3 über, W2 neben der Achse)
CLEAR_MIN = 20.0               # Vorgabe Stilhandbuch (BASIC-14): Rohrwand ≥ 20 mm neben der Visierlinie
FRAME_MARGIN = 20.0            # A: Rand um die gemeinsame Hülle (mm)
OWN = {"e09": dict(num="09", type="sniper_rifle", id="EXTENDED-09", sheet="EA09", mod="e09_theodolite"),
       "e14": dict(num="14", type="rocket_launcher", id="EXTENDED-14", sheet="EA14", mod="e14_keelson")}


def frame(*part_lists, margin=FRAME_MARGIN):
    """Gemeinsamer Rasterrahmen (lo, size) aus den Hüllquadern aller Teillisten (wie test_extended_fusion)."""
    bs = [b for parts in part_lists for p in parts if (b := extended.bounds(p))]
    f0, u0 = min(b[0][0] for b in bs) - margin, min(b[0][1] for b in bs) - margin
    f1, u1 = max(b[1][0] for b in bs) + margin, max(b[1][1] for b in bs) + margin
    return dict(lo=(f0, u0), size=(int(f1 - f0) + 2, int(u1 - u0) + 2))


def as_side(p):
    """Querprofil als Seitenprofil seiner Hülle, damit `side_mask` die durchgehenden Seitenschnitte abzieht (das Standardmaß zeichnet
    ein Querprofil als volles Rechteck und sieht weder Spannweite noch Kolbenbogen)."""
    if p.get("shape") != "xprof":
        return p
    us, xs = [u + p["cu"] for _, u in p["pts"]], [x for x, _ in p["pts"]]
    return dict(p, shape="prof", pts=[(p["f0"], min(us)), (p["f1"], min(us)), (p["f1"], max(us)), (p["f0"], max(us))],
                w=max(xs) - min(xs), x=p.get("cx", 0.0) + (max(xs) + min(xs)) / 2)


def iou(a, b):
    return extended.side_iou(a, b, **frame(a, b))


def iou_exact(a, b):
    a, b = [as_side(p) for p in a], [as_side(p) for p in b]
    return extended.side_iou(a, b, **frame(a, b))


def free(parts, box):
    """Anteil belegter Pixel der genauen Seitensilhouette im Fenster (f0, u0, f1, u1)."""
    sp = [as_side(p) for p in parts]
    fr = frame(sp)
    m = extended.side_mask(sp, **fr)
    rows = m.shape[0]
    f0, u0, f1, u1 = box
    j0, j1 = int(f0 - fr["lo"][0]), int(f1 - fr["lo"][0])
    i0, i1 = int(rows - 1 - (u1 - fr["lo"][1])), int(rows - 1 - (u0 - fr["lo"][1]))
    return float(m[i0:i1, j0:j1].mean())


def lights(parts):
    return sorted(p["id"] for p in parts if p["mat"] == "energy" and p["asm"] != "sight")


def accent_functions(parts):
    return sorted({p["id"] for p in parts if p["mat"] == "accent" and p.get("move") and p["asm"] != "sight"})


def graphics(parts):
    return [p["id"] for p in parts if p["mat"] == "accent" and not p.get("move") and p["asm"] != "sight"]


def length(parts):
    bs = [b for p in parts if (b := extended.bounds(p))]
    return max(b[1][0] for b in bs) - min(b[0][0] for b in bs)


def forms(parts, mat=None):
    return sum(len(p["items"]) if p["shape"] == "multi" else 1 for p in parts if mat is None or p["mat"] == mat)


def width_at(pts, u):
    """Breite eines Querprofils (x, u) in Höhe u."""
    xs = [x0 + (x1 - x0) * (u - u0) / (u1 - u0) for (x0, u0), (x1, u1) in zip(pts, pts[1:] + pts[:1])
          if u0 != u1 and min(u0, u1) <= u <= max(u0, u1)]
    return max(xs) - min(xs) if xs else 0.0


def text_span(t):
    """Kit-Schrift ist linksbündig; rechts (side −1) läuft sie nach vorn. Länge ≈ 0,62 × Größe je Zeichen (Annahme, großzügig)."""
    n = 0.62 * t["size"] * len(t["text"])
    return (t["f"], t["f"] + n) if t["side"] == -1 else (t["f"] - n, t["f"])


def crossing(pts):
    """Erster Fehler eines Polygons (doppelter Punkt oder sich schneidende/berührende nicht benachbarte Kanten), sonst None."""
    def side(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    def on(a, b, c):
        return abs(side(a, b, c)) < 1e-6 and min(a[0], b[0]) - 1e-6 <= c[0] <= max(a[0], b[0]) + 1e-6 \
            and min(a[1], b[1]) - 1e-6 <= c[1] <= max(a[1], b[1]) + 1e-6
    keys = [(round(x, 6), round(u, 6)) for x, u in pts]
    if len(set(keys)) < len(keys):
        return "doppelter Punkt"
    edges = list(zip(pts, pts[1:] + pts[:1]))
    n = len(edges)
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            (a, b), (c, d) = edges[i], edges[j]
            if side(a, b, c) * side(a, b, d) < -1e-9 and side(c, d, a) * side(c, d, b) < -1e-9:
                return (i, j)
            if on(a, b, c) or on(a, b, d) or on(c, d, a) or on(c, d, b):
                return (i, j)
    return None


@unittest.skipIf(SNAP is None, REASON)
class TestSchulter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = {k: extended.load(k, SNAP) for k in OWN}
        cls.basic = {k: extended.load_basic(OWN[k]["num"], SNAP) for k in OWN}
        cls.others = {k: extended.load(k, SNAP)["PARTS"] for k in extended.MODELS if k not in OWN}
        cls.ids = {k: {p["id"]: p for p in d["PARTS"]} for k, d in cls.data.items()}
        sys.path.insert(0, str(SNAP))
        try:
            cls.mods = {k: importlib.import_module(extended.module_name(k)) for k in OWN}
            cls.consts = {k: {n: getattr(m, n) for n in dir(m) if not n.startswith('__')} for k, m in cls.mods.items()}
        finally:
            sys.path.remove(str(SNAP))
            extended._purge(tuple(extended.module_name(k) for k in OWN))

    # ---------------------------------------------------------------- Felder, IDs, Anker
    def test_fields_and_ids(self):
        for k, o in OWN.items():
            with self.subTest(k):
                d, ids = self.data[k], self.ids[k]
                self.assertEqual(extended.MODELS[k], o["mod"])
                self.assertEqual(d["META"]["id"], o["id"])
                self.assertEqual(d["META"]["type"], o["type"])
                self.assertEqual(d["META"]["type"], self.basic[k]["META"]["type"], "Typ wie BASIC-NN")
                self.assertEqual(d["META"]["fire"], self.basic[k]["META"]["fire"], "Feuerart wie BASIC-NN")
                self.assertEqual(len(ids), len(d["PARTS"]), "Teil-IDs doppelt")
                asms = {a["id"] for a in d["ASSEMBLIES"]}
                self.assertEqual(asms, {a["id"] for a in self.basic[k]["ASSEMBLIES"]}, "Baugruppen wie BASIC-NN")
                self.assertEqual({p["asm"] for p in d["PARTS"]} - asms, set())
                for p in d["PARTS"]:
                    if p.get("parent_part"):
                        self.assertIn(p["parent_part"], ids, p["id"])
        self.assertEqual(self.data["e09"]["EJECT"]["case"], "rifle")
        self.assertIsNone(self.data["e14"]["EJECT"], "hülsenlos wie BASIC-14")
        self.assertTrue(self.ids["e14"]["rocket"]["caseless"])

    def test_sheet_ids(self):
        for k, o in OWN.items():
            self.assertEqual(extended.sheet_id(k), o["sheet"])
            self.assertEqual(self.data[k]["META"]["sheet_id"], o["sheet"])
            self.assertRegex(o["sheet"], f"^{extended.SHEET_PATTERN}$")
        sids = list(extended.SHEETS.values())
        self.assertEqual(len(set(sids)), len(sids), "Blatt-IDs doppelt")
        self.assertEqual(set(extended.SHEETS), set(extended.MODELS))
        self.assertIsNone(re.match(f"^{extended.SHEET_PATTERN}$", "EI09"))   # Gegenprobe: Linienbuchstabe I ist gesperrt

    def test_anchors_points_actions(self):
        sys.path.insert(0, str(SNAP))
        try:
            variant = importlib.import_module("basic.variant")
            for k, d in self.data.items():
                with self.subTest(k):
                    A, ids = d["ANCHORS"], self.ids[k]
                    self.assertEqual(set(A), set(self.basic[k]["ANCHORS"]), "Anker wie BASIC-NN")
                    for name, a in A.items():
                        self.assertIn(a["part"], ids, name)
                    self.assertEqual(tuple(A["Socket_Hand"]["at"]), (0, 0, 0))
                    self.assertEqual(set(d["POINTS"]), set(self.basic[k]["POINTS"]), "Weltpunkte wie BASIC-NN")
                    self.assertEqual(set(d["ACTIONS"]), set(self.basic[k]["ACTIONS"]), "Aktionen wie BASIC-NN")
                    for name, act in d["ACTIONS"].items():
                        for pid in act["keys"]:
                            self.assertIn("move", ids[pid], f"{name}: {pid} ohne Bewegung")
                    self.assertEqual(variant.problems(variant.as_module(copy.deepcopy(d))), [])
                    bad = copy.deepcopy(d)   # Gegenprobe: Griffpunkt auf ein fehlendes Teil
                    bad["POINTS"]["grip.support"]["part"] = "kein_teil"
                    self.assertTrue(any("kein_teil" in m for m in variant.problems(variant.as_module(bad))))
        finally:
            sys.path.remove(str(SNAP))
            extended._purge()

    def test_family_interfaces(self):
        want = {"e09": {"grip": "BGM-1", "rail": "BRI-22", "rail_front": "BRI-22", "scope_mount_r": "BRI-22", "scope_mount_f": "BRI-22",
                        "mag_well": "BMW-R", "magazine": "BMW-R", "muzzle": "BMZ-15"},
                "e14": {"grip": "BGM-1", "rail": "BRI-22", "sight_mount": "BRI-22"}}

        def problems(ids, w):
            return [pid for pid, iface in w.items() if ids.get(pid, {}).get("iface") != iface]
        for k, ids in self.ids.items():
            with self.subTest(k):
                self.assertEqual(problems(ids, want[k]), [])
                self.assertEqual(ids["grip"]["mat"], "rubber")
        self.assertIn("scope_mount_r", problems(self.ids["e14"], want["e09"]))   # Gegenprobe: der Werfer hat kein Zielfernrohr
        self.assertIn("scope_shade", self.ids["e09"], "Z3 „Lang“ mit Sonnenblende wie BASIC-09")
        self.assertIn("sight_roof", self.ids["e14"], "W2 „Entfernung“ mit Schutzdach wie BASIC-14")

    # ---------------------------------------------------------------- Budgets, Visier, Schrift
    def test_budgets(self):
        for k, d in self.data.items():
            with self.subTest(k):
                P = d["PARTS"]
                self.assertEqual(len(lights(P)), 1, f"genau ein Blickfang außerhalb des Visiers: {lights(P)}")
                glow = self.ids[k][lights(P)[0]]
                self.assertGreater(extended.bounds(glow)[0][2], 0, "Blickfang ganz links (Ego-Seite)")
                self.assertLessEqual(len(accent_functions(P)), 3, accent_functions(P))
                self.assertEqual([p["id"] for p in P if p["shape"] == "text"], ["text_r"])
                self.assertEqual(len(graphics(P)), 1, graphics(P))
        two = self.data["e09"]["PARTS"] + [dict(self.ids["e09"]["level_fluid"], id="level2")]   # Gegenprobe: zweiter Blickfang
        self.assertEqual(len(lights(two)), 2)
        more = self.data["e14"]["PARTS"] + [dict(self.ids["e14"]["safety"], id="a"), dict(self.ids["e14"]["safety"], id="b")]
        self.assertGreater(len(accent_functions(more)), 3)   # Gegenprobe: vier Bedienfunktionen
        head = self.data["e14"]["PARTS"] + [dict(self.ids["e14"]["rocket_head"], id="kopf", mat="accent")]
        self.assertEqual(len(graphics(head)), 2)             # Gegenprobe: oranger Gefechtskopf wie BASIC-14 wäre zweite Grafik

    def test_beacon_exposed(self):
        """Richter R1: Der Blickfang liegt frei – vor dem Muldenboden, hinter dem Glas, unter der engsten Stelle der gewölbten Schale.
        E14: Raute in einer Mulde mit Boden unter der engsten Schalenstelle; E09: Libelle steht über den Muldengrund hinaus."""
        c, ids = self.consts["e14"], self.ids["e14"]
        mulde = [q for q in ids["hull"]["cuts"] if q.get("shape") == "prof" and abs(q.get("x", 0) - (c["LOCK_FLOOR"] + 6.0)) < 1e-6]
        self.assertEqual(len(mulde), 1)
        floor = mulde[0]["x"] - mulde[0]["w"] / 2
        surface = min(c["hull_x"](u) for _, u in ids["lock_frame"]["pts"])

        def problems(light, glass, frame):
            out = []
            lo, hi = light["x"] - light["w"] / 2, light["x"] + light["w"] / 2
            if lo < floor - 0.01 or hi < floor + 0.5:
                out.append("Leuchte verdeckt")
            if glass["x"] - glass["w"] / 2 < hi:
                out.append("Glas hinter der Leuchte")
            if frame["x"] + frame["w"] / 2 > surface:
                out.append("Rahmen steht über die Schale")
            return out
        self.assertEqual(problems(ids["lock_light"], ids["lock_glass"], ids["lock_frame"]), [])
        buried = dict(ids["lock_light"], x=floor - 1.0)    # Gegenprobe: Stand vor R1 (Leuchte auf/hinter dem Muldenboden)
        self.assertIn("Leuchte verdeckt", problems(buried, ids["lock_glass"], ids["lock_frame"]))
        c9, i9 = self.consts["e09"], self.ids["e09"]
        cut = [q for q in i9["upper"]["cuts"] if q.get("shape") == "cyl"][0]

        def level_problems(fluid):
            return [] if fluid["c"][1] + fluid["r"] > cut["c"][1] - cut["r"] + 3 and i9["level_glass"]["r"] > fluid["r"] else ["Libelle verdeckt"]
        self.assertEqual(level_problems(i9["level_fluid"]), [])
        self.assertEqual(level_problems(dict(i9["level_fluid"], c=(cut["c"][0], cut["c"][1] - 8))), ["Libelle verdeckt"])   # Gegenprobe

    def test_sight_line(self):
        """Z3 66 ± 4 mm über der Laufachse (wie BASIC-09); W2 auf Achshöhe 66 ± 4 mm links neben der Achse (wie BASIC-14)."""
        def offset(d):
            eye, muz = d["ANCHORS"]["Socket_Eye"]["at"], d["ANCHORS"]["Socket_Muzzle"]["at"]
            return eye[1] - muz[1], (eye[2] if len(eye) > 2 else 0.0) - muz[2]
        du, dx = offset(self.data["e09"])
        self.assertTrue(SIGHT_H[0] <= du <= SIGHT_H[1] and dx == 0, (du, dx))
        self.assertEqual(self.data["e09"]["ANCHORS"]["Socket_Eye"]["sight_type"], "fullscreen")
        du, dx = offset(self.data["e14"])
        self.assertAlmostEqual(du, 0.0, delta=0.5)
        self.assertTrue(SIGHT_H[0] <= dx <= SIGHT_H[1], dx)
        raised = copy.deepcopy(self.data["e09"])   # Gegenprobe: Zielfernrohr 20 mm höher
        raised["ANCHORS"]["Socket_Eye"]["at"] = tuple(v + (20 if i == 1 else 0) for i, v in enumerate(raised["ANCHORS"]["Socket_Eye"]["at"]))
        self.assertGreater(offset(raised)[0], SIGHT_H[1])

    def test_launcher_view_clear(self):
        """Vor dem Auge ragt kein Teil außerhalb des Visiers in Achshöhe weiter als 66 − 20 mm nach links (Stilhandbuch, BASIC-14):
        das Volumen des Rumpfs liegt unter der Achse, nicht neben der Visierlinie."""
        d = self.data["e14"]
        eye = d["ANCHORS"]["Socket_Eye"]["at"]
        c = self.consts["e14"]
        mount = {"sight_arm", "rail", "sight_clamps", "clamp_screws"}

        def problems(parts):
            out = []
            for p in parts:
                b = extended.bounds(p)
                if not b or p["asm"] == "sight" or p["id"] in mount:
                    continue
                (f0, u0, _), (f1, u1, x1) = b
                if p["id"] == "load_hatch":   # Sektor oben (Schnitte); der Hüllquader des Zylinders zählt nicht
                    x1 = c["HATCH"][2] + 2
                if f1 > eye[0] and u0 < c["BORE"] + 20 and u1 > c["BORE"] - 20 and x1 > eye[2] - CLEAR_MIN:
                    out.append(p["id"])
            return out
        self.assertEqual(problems(d["PARTS"]), [])
        fat = dict(id="dickes_rohr", asm="barrel", shape="cyl", axis="f", c=(c["BORE"], 0), a0=100, a1=400, r=56)
        self.assertEqual(problems(d["PARTS"] + [fat]), ["dickes_rohr"])   # Gegenprobe: Startrohr Ø 112 vor dem Visier
        self.assertLess(c["BORE"] - c["R_HULL"] - min(u for _, u in c["KEEL_LINE"]), 200, "Plausibilität")

    def test_lettering_on_flat_face(self):
        """E09: rechts auf dem senkrechten Gürtel zwischen Auswurffenster und Gratstreifen; E14: rechts auf der fast senkrechten Schale
        in Achshöhe, vor dem Visierausleger, hinter der Stirnfase."""
        c9, c14 = self.consts["e09"], self.consts["e14"]

        def problems(k, t):
            a, b = text_span(t)
            h = 0.75 * t["size"]
            out = []
            if k == "e09":
                stripe = min(q["pts"][0][0] for q in self.ids[k]["band_side"]["items"])
                lo, hi, u0, u1 = c9["PORT"][1] + 2, stripe - 2, c9["SEAM"] + 0.6, c9["BELT"][1]
                surface = c9["HALF"]
            else:
                lo, hi, u0, u1 = c14["ARM"][1] + 10, c14["F1"] - 20, c14["BORE"] - 10, c14["BORE"] + 12
                surface = min(c14["hull_x"](t["u"]), c14["hull_x"](t["u"] + h))
            if a < lo or b > hi:
                out.append("außerhalb der freien Fläche")
            if t["u"] < u0 or t["u"] + h > u1:
                out.append("außerhalb der Höhe")
            if t["x"] > 0 or abs(abs(t["x"]) - surface) > 0.4:
                out.append("nicht rechts auf der Fläche")
            return out
        for k in OWN:
            with self.subTest(k):
                self.assertEqual(problems(k, self.ids[k]["text_r"]), [])
        self.assertIn("außerhalb der freien Fläche", problems("e09", dict(self.ids["e09"]["text_r"], f=c9["PORT"][0])))   # im Fenster
        self.assertIn("außerhalb der Höhe", problems("e09", dict(self.ids["e09"]["text_r"], u=c9["SEAM"] - 3)))       # auf der Fuge
        self.assertIn("nicht rechts auf der Fläche", problems("e14", dict(self.ids["e14"]["text_r"], u=c14["BORE"] + 30)))   # auf der Rundung

    # ---------------------------------------------------------------- Silhouette
    def test_own_silhouette(self):
        """Seiten-IoU < 0,85 gegen BASIC-NN und jedes andere EXTENDED-Modell, < 0,70 im Paar – im Standardmaß und im genauen Maß."""
        for k, d in self.data.items():
            for measure in (iou, iou_exact):
                with self.subTest(k=k, measure=measure.__name__):
                    self.assertLess(measure(self.basic[k]["PARTS"], d["PARTS"]), IOU_MAX)
                    for o, parts in self.others.items():
                        self.assertLess(measure(parts, d["PARTS"]), IOU_MAX, o)
        for measure in (iou, iou_exact):
            self.assertLess(measure(self.data["e09"]["PARTS"], self.data["e14"]["PARTS"]), PAIR_MAX)
        b14 = self.basic["e14"]["PARTS"]   # Gegenproben: gleiche Form 1,0; eine Parameterlinie bleibt über der Schwelle
        self.assertGreaterEqual(iou(b14, b14), 0.99)
        trimmed = [p for p in b14 if p["id"] not in ("muzzle", "muzzle_crown")]
        self.assertGreater(iou(b14, trimmed), IOU_MAX)
        # Gegenprobe: das genaue Maß sieht die Spannweite, das Standardmaß nicht (Querprofil als Rechteck)
        P = self.data["e09"]["PARTS"]
        c = self.consts["e09"]
        window = (c["SPAN"][0] + 10, c["SPAN"][2] - 30, c["SPAN"][1] - 10, c["SPAN"][2] - 2)
        self.assertEqual(free(P, window), 0.0)
        sp = extended.side_mask(P, **frame(P))
        self.assertGreater(sp.sum(), extended.side_mask([as_side(p) for p in P], **frame(P)).sum())

    # ---------------------------------------------------------------- Leitmotiv Stativ (E09)
    def test_theodolite_three_supports(self):
        """Der Rautenrumpf steht auf drei Stützen – Griff mit Magazin, Pylon, Kolbenbein – und spannt dazwischen frei: unter der Spannweite
        (Magazin → Pylon) und unter dem Kolbenbogen (Griff → Kolbenbein) bleibt die Seitensilhouette leer. Runde 5 (Nutzer: dünne Stifte
        unverständlich): Pylon und Kolbenbein stehen auf Gummisohlen, die sich nach unten verbreitern; kein dünner Stift hängt unter dem Rumpf."""
        c, ids, P = self.consts["e09"], self.ids["e09"], self.data["e09"]["PARTS"]
        under = c["_UNDER"]
        span_u = c["SPAN"][2]

        def problems(parts, line):
            out = []
            pid = {p["id"]: p for p in parts}
            low = lambda f0, f1: min(u for f, u in line if f0 <= f <= f1)   # noqa: E731
            if span_u - low(c["PYLON"][0], c["PYLON"][1]) < 40:
                out.append("kein Pylon")
            if c["ARCH"][2] - extended.bounds(pid["toe_foot"])[0][1] < 60:
                out.append("kein Kolbenbein")
            if free(parts, (c["SPAN"][0] + 10, span_u - 40, c["SPAN"][1] - 10, span_u - 2)) > 0.0:
                out.append("Spannweite zu")
            if free(parts, (c["ARCH"][0] + 6, c["ARCH"][2] - 30, c["ARCH"][1] - 6, c["ARCH"][2] - 2)) > 0.0:
                out.append("Kolbenbogen zu")
            for q in parts:
                if q["asm"] in ("support", "stock") and (q["shape"] == "tube" or (q["shape"] == "cyl" and q["axis"] == "u" and q["r"] < 8)):
                    out.append(f"Stift {q['id']}")
            return out
        self.assertEqual(problems(P, under), [])
        for pid in ("pylon_foot", "toe_foot"):
            foot = ids[pid]
            us = [u for _, u in foot["pts"]]
            self.assertEqual(foot["mat"], "rubber")
            self.assertGreaterEqual(max(us) - min(us), 8.0, f"{pid}: Sohle nicht zart")
            self.assertGreaterEqual(width_at(foot["pts"], min(us) + 3) - width_at(foot["pts"], max(us) - 0.5), 10.0, f"{pid}: Sohle verbreitert")
        keel = dict(id="kiel", asm="receiver", shape="box", f0=c["SPAN"][0], f1=c["SPAN"][1], u0=20, u1=span_u + 1, w=20)
        self.assertEqual(problems(P + [keel], under), ["Spannweite zu"])          # Gegenprobe: durchgehender Vorderschaft
        slab = dict(id="platte", asm="stock", shape="box", f0=c["ARCH"][0] - 20, f1=c["ARCH"][1] + 20, u0=0, u1=c["ARCH"][2] + 1, w=30)
        self.assertEqual(problems(P + [slab], under), ["Kolbenbogen zu"])         # Gegenprobe: Keilkolben wie Runde 1
        flat = [(f, max(u, span_u)) if c["SPAN"][1] < f < c["NOSE"] else (f, u) for f, u in under]
        self.assertIn("kein Pylon", problems(P, flat))                            # Gegenprobe: ohne Pylon
        pin = dict(id="monopod", asm="stock", shape="cyl", axis="u", c=(-297, 0), a0=-46, a1=-4, r=5.4)
        self.assertEqual(problems(P + [pin], under), ["Stift monopod"])           # Gegenprobe: Einbeinstift wie Runde 1–4

    def test_theodolite_section(self):
        """Raute mit Gürtel: Oberschale und Kiel sind am Gürtel am breitesten und laufen schräg zu Deck und Kiel; der Gürtel ist senkrecht
        (trägt Schrift und Streifen); Kolben und Pylon sind derselbe Querschnitt (ein Teil vom Butt bis zur Stirn)."""
        c, ids = self.consts["e09"], self.ids["e09"]

        def problems(upper, lower):
            out = []
            belt = width_at(upper, c["BELT"][1] - 0.5)
            if width_at(upper, max(u for _, u in upper) - 0.5) > 0.6 * belt:
                out.append("oben nicht eingezogen")
            if width_at(lower, min(u for _, u in lower) + 4.0) > 0.4 * width_at(lower, c["BELT"][0] - 0.5):
                out.append("unten nicht eingezogen")
            if abs(width_at(upper, c["SEAM"] + 1) - width_at(upper, c["BELT"][1] - 0.5)) > 0.2:
                out.append("kein Gürtel")
            return out
        self.assertEqual(problems(ids["upper"]["pts"], ids["lower"]["pts"]), [])
        box = [(23, 89), (23, 133), (-23, 133), (-23, 89)]
        self.assertEqual(problems(box, ids["lower"]["pts"]), ["oben nicht eingezogen"])   # Gegenprobe: Kasten
        for pid in ("upper", "lower"):
            self.assertEqual((ids[pid]["f0"], ids[pid]["f1"]), (c["BUTT"], c["NOSE"]), "ein Teil vom Butt bis zur Stirn")
        self.assertFalse([p["id"] for p in self.data["e09"]["PARTS"] if p["asm"] == "stock" and p["shape"] in ("box", "prof")
                          and p["mat"] in ("shell", "graphite")], "kein angesetzter Kolbenkörper")

    def test_theodolite_level(self):
        """Blickfang Libelle: leuchtendes Röhrchen längs, die Blase sitzt mittig und steht über das Röhrchen hinaus, Glas und Kappen fassen es."""
        ids = self.ids["e09"]

        def problems(fluid, bubble, glass):
            out = []
            if fluid["axis"] != "f" or fluid["a1"] - fluid["a0"] < 3 * fluid["r"]:
                out.append("kein Röhrchen")
            mid = (fluid["a0"] + fluid["a1"]) / 2
            if abs((bubble["a0"] + bubble["a1"]) / 2 - mid) > 1.0 or bubble["r"] <= fluid["r"]:
                out.append("Blase nicht sichtbar mittig")
            if glass["r"] <= bubble["r"] or glass["a0"] > fluid["a0"] or glass["a1"] < fluid["a1"]:
                out.append("ohne Glas")
            return out
        self.assertEqual(problems(ids["level_fluid"], ids["level_bubble"], ids["level_glass"]), [])
        off = dict(ids["level_bubble"], a0=ids["level_fluid"]["a0"], a1=ids["level_fluid"]["a0"] + 7)
        self.assertEqual(problems(ids["level_fluid"], off, ids["level_glass"]), ["Blase nicht sichtbar mittig"])   # Gegenprobe
        self.assertEqual(len(ids["level_caps"]["items"]), 2)

    # ---------------------------------------------------------------- Leitmotiv Rumpf (E14)
    def test_keelson_hull(self):
        """Tropfenquerschnitt: Kreis um die Bohrung, Flanken laufen zum Kiel zusammen; tiefer Bauch ≥ 60 mm unter dem Rohr, der nach vorn
        zur Stirn (≥ 40 mm) und nach hinten zur Kielhacke steigt."""
        c, ids = self.consts["e14"], self.ids["e14"]

        def problems(shell, keel, line):
            out = []
            if width_at(shell, c["BORE"]) < 2 * c["R_HULL"] - 1 or width_at(shell, c["BORE"] + 0.8 * c["R_HULL"]) > 1.3 * c["R_HULL"]:
                out.append("oben nicht rund")
            if width_at(keel, min(u for f, u in line) + 3) > 0.5 * width_at(keel, c["SEAM"] - 1):
                out.append("kein Kiel")
            low = min(u for _, u in line)
            if c["BORE"] - c["R_HULL"] - low < 60:
                out.append("flacher Bauch")
            front = [u for f, u in line if f >= c["F1"] - 1]
            if min(front) - low < 40:
                out.append("Stirn so tief wie der Bauch")
            if line[0][1] - low < 60:
                out.append("keine Kielhacke")
            return out
        self.assertEqual(problems(ids["hull"]["pts"], ids["keel"]["pts"], c["KEEL_LINE"]), [])
        flat = [(f, max(u, c["BORE"] - c["R_HULL"] - 20)) for f, u in c["KEEL_LINE"]]
        self.assertIn("flacher Bauch", problems(ids["hull"]["pts"], ids["keel"]["pts"], flat))   # Gegenprobe: Rohr auf flachem Kasten
        block = [(46, 100), (46, 10), (-46, 10), (-46, 100)]
        self.assertIn("kein Kiel", problems(ids["hull"]["pts"], block, c["KEEL_LINE"]))         # Gegenprobe: Kastenkiel
        self.assertEqual(ids["hull"]["shape"], "xprof")

    def test_keelson_saddle(self):
        """Schultersattel aus dem Leitmotiv: kleiner Tropfenkiel unter dem Abgasrohr, oben offen (Spannbänder), unten ein Bogen ≥ 15 mm über
        der Schulter, Enden als Keil; hinter dem Auge, unter der Achse."""
        c, ids = self.consts["e14"], self.ids["e14"]
        eye = self.data["e14"]["ANCHORS"]["Socket_Eye"]["at"]

        def problems(sad, line):
            out = []
            if max(u for _, u in sad["pts"]) > c["BORE"] + 8:
                out.append("Muffe statt Wiege")
            mid = [u for f, u in line if abs(f - (c["SADDLE"][0] + c["SADDLE"][1]) / 2) < 3]
            ends = min(u for f, u in line if c["SADDLE"][0] < f < c["SADDLE"][1])
            if max(mid) - ends < 15:
                out.append("kein Bogen")
            if sad["f1"] > eye[0] - 100:
                out.append("nicht auf der Schulter")
            return out
        self.assertEqual(problems(ids["saddle"], c["_sad_line"]), [])
        flat = [(f, 72.0) if c["SADDLE"][0] < f < c["SADDLE"][1] else (f, u) for f, u in c["_sad_line"]]
        self.assertEqual(problems(ids["saddle"], flat), ["kein Bogen"])                       # Gegenprobe: flache Auflage
        sleeve = dict(ids["saddle"], pts=c["drop"](c["R_REAR"] + 6, c["BORE"], 66))
        self.assertEqual(problems(sleeve, c["_sad_line"]), ["Muffe statt Wiege"])              # Gegenprobe: Runde 2
        self.assertEqual(len(ids["saddle_straps"]["items"]), 2)

    def test_keelson_sight_console(self):
        """Runde 5 (Nutzer: Visier „richtig“ befestigen): Die Konsole wächst aus Rumpfschale und Kiel (Wurzel in der Flanke, mindestens
        30 mm hoch), hat einen tragfähigen Querschnitt (≥ 1200 mm², Spitze ≥ 12 mm hoch, ≥ 50 mm lang), trägt die Schiene unter dem Visier
        auf ganzer Länge zwischen zwei Klemmleisten mit blanken Schrauben und hängt mit Rumpf und Visier zusammen."""
        c, ids, P = self.consts["e14"], self.ids["e14"], self.data["e14"]["PARTS"]

        def area(pts):
            return abs(sum(x0 * u1 - x1 * u0 for (x0, u0), (x1, u1) in zip(pts, pts[1:] + pts[:1]))) / 2

        def problems(arm):
            out = []
            pts = arm["pts"]
            root = [u for x, u in pts if x <= c["hull_x"](u) - 1.5]
            if not root or max(root) - min(root) < 30:
                out.append("Wurzel nicht in der Flanke")
            tip = max(x for x, _ in pts)
            tip_us = [u for x, u in pts if x >= tip - 0.5]
            if area(pts) < 1200 or max(tip_us) - min(tip_us) < 12 or arm["f1"] - arm["f0"] < 50:
                out.append("zu dünn")
            rail = ids["rail"]
            if not (arm["f0"] <= rail["f0"] and arm["f1"] >= rail["f1"]) or tip < c["SIDE"] + rail["w"] / 2:
                out.append("Schiene nicht getragen")
            return out
        self.assertEqual(problems(ids["sight_arm"]), [])
        self.assertEqual(ids["sight_arm"]["mat"], "shell", "wächst aus der Creme-Schale")
        self.assertEqual(len(ids["sight_clamps"]["items"]), 2)
        self.assertGreaterEqual(len(ids["clamp_screws"]["items"]), 4)
        self.assertEqual(ids["clamp_screws"]["mat"], "trim")
        group = next(g for g in extended.components(P) if "sight_arm" in g)
        self.assertTrue({"hull", "keel", "sight_mount"} <= set(group))
        old = dict(ids["sight_arm"], f0=2, f1=40, pts=[(38, 92), (77, 98), (77, 106), (38, 112)])
        self.assertIn("zu dünn", problems(old))                                            # Gegenprobe: dünner Winkel bis Runde 4
        loose = dict(ids["sight_arm"], pts=[(x + 14, u) for x, u in ids["sight_arm"]["pts"]])
        self.assertIn("Wurzel nicht in der Flanke", problems(loose))                       # Gegenprobe: Konsole stumpf angesetzt

    def test_keelson_loading(self):
        """Ladeschacht oben: die Rakete passt durch den Schacht, die Klappe deckt ihn, die Bohrung ist hinten geschlossen."""
        c, ids = self.consts["e14"], self.ids["e14"]

        def problems(slot):
            out = []
            if 2 * slot[2] < 2 * (c["R_IN"] - 2) or slot[0] > c["R0"] or slot[1] < c["R2"]:
                out.append("Rakete passt nicht")
            if not (c["HATCH"][0] <= slot[0] and c["HATCH"][1] >= slot[1] and c["HATCH"][2] >= slot[2]):
                out.append("Klappe zu klein")
            return out
        self.assertEqual(problems(c["SLOT"]), [])
        self.assertEqual(problems((c["SLOT"][0] + 20, c["SLOT"][1], c["SLOT"][2])), ["Rakete passt nicht"])   # Gegenprobe
        self.assertEqual(ids["rocket"]["move"]["vector_mm"][1], c["LOWER"])
        self.assertLess(ids["bore_plug"]["a1"], c["R0"])

    # ---------------------------------------------------------------- Querschnitte, Dichte, Profile
    def test_shaped_sections(self):
        """Hauptkörper mit gestalteten Querschnitten (Breite ändert sich über die Höhe um ≥ 1,5 mm) – Front, Rückansicht und Kolben sind
        keine Rechtecke (Nutzer 0.23: nicht kastig)."""
        main = {"e09": ("upper", "lower", "butt_pad", "nose_plate"), "e14": ("hull", "keel", "saddle", "nose_plate")}

        def boxy(p):
            if p["shape"] == "xprof":
                us = [u for _, u in p["pts"]]
                lo, hi = min(us), max(us)
                widths = [width_at(p["pts"], lo + (hi - lo) * t) for t in (0.08, 0.5, 0.92)]
                return max(widths) - min(widths) < 1.5
            shaped = [q for q in p.get("cuts") or () if q.get("shape") in ("xprof", "plan")]
            return not shaped or p.get("bevel", 0) < 3.0
        for k, ids in main.items():
            with self.subTest(k):
                self.assertEqual([pid for pid in ids if boxy(self.ids[k][pid])], [])
        flat = dict(self.ids["e14"]["keel"], pts=[(40, 100), (40, 10), (-40, 10), (-40, 100)])   # Gegenprobe: Rechteck-Querschnitt
        self.assertTrue(boxy(flat))

    def test_detail_density(self):
        """Detaildichte mindestens wie BASIC: Einzelformen ≥ 90 % des Piloten, blanke Teile mindestens so viele wie der Pilot."""
        for k, d in self.data.items():
            with self.subTest(k):
                b = self.basic[k]["PARTS"]
                self.assertGreaterEqual(forms(d["PARTS"]), 0.9 * forms(b))
                self.assertGreaterEqual(forms(d["PARTS"], "trim"), forms(b, "trim"))
        bare = [p for p in self.data["e14"]["PARTS"] if p["mat"] != "trim"]   # Gegenprobe: ohne blanke Teile unter BASIC-14
        self.assertLess(forms(bare, "trim"), forms(self.basic["e14"]["PARTS"], "trim"))

    def test_profiles_simple(self):
        """Kein Seiten- oder Querprofil schneidet sich selbst (auch Schnittprofile)."""
        def problems(parts):
            out = []
            for p in parts:
                for q in (p["items"] if p.get("shape") == "multi" else [p]) + list(p.get("cuts") or ()):
                    if q.get("shape") in ("prof", "xprof") and crossing([tuple(v) for v in q["pts"]]):
                        out.append(p["id"])
            return sorted(set(out))
        for k, d in self.data.items():
            with self.subTest(k):
                self.assertEqual(problems(d["PARTS"]), [])
        bad = dict(self.ids["e09"]["upper"], pts=self.ids["e09"]["upper"]["pts"][:2] + self.ids["e09"]["upper"]["pts"][2:][::-1])
        self.assertEqual(problems([bad]), ["upper"])   # Gegenprobe: zweite Hälfte umgekehrt

    # ---------------------------------------------------------------- Absetzung, Zusammenhang, Länge, Quellhash
    def test_rifle_versus_launcher(self):
        """Gewehr lang, schlank, Raute, Lauf frei; Werfer kürzer, großvolumig, Tropfen, Volumen unter der Achse."""
        c9, c14 = self.consts["e09"], self.consts["e14"]
        l9, l14 = length(self.data["e09"]["PARTS"]), length(self.data["e14"]["PARTS"])
        self.assertGreater(l9 - l14, 200)
        w9 = max(width_at(self.ids["e09"]["upper"]["pts"], u) for u in np.linspace(c9["SEAM"] + 1, c9["COMB"], 20))
        w14 = max(width_at(self.ids["e14"]["hull"]["pts"], u) for u in np.linspace(c14["SEAM"] + 1, c14["BORE"] + 40, 20))
        self.assertGreater(w14, 1.8 * w9, "Werfer großvolumig, Gewehr schlank")
        self.assertGreaterEqual(c14["R_IN"], 2.5 * 9.5, "Bohrung des Werfers vielfach größer als der Lauf")
        self.assertIn("barrel", self.ids["e09"])
        self.assertNotIn("barrel", self.ids["e14"])
        self.assertIn("magazine", self.ids["e09"])
        self.assertIn("rocket", self.ids["e14"])

    def test_no_floating_parts(self):
        for k, d in self.data.items():
            with self.subTest(k):
                self.assertEqual(extended.components(d["PARTS"])[1:], [])
        moved = copy.deepcopy(self.data["e14"]["PARTS"])   # Gegenprobe: Sattel samt Bändern 120 mm nach hinten → eigene Gruppe
        for p in moved:
            if p["asm"] == "stock" and p["id"] not in ("rear_tube",):
                for q in [p] + p.get("items", []):
                    for key in ("a0", "a1", "f0", "f1"):
                        if key in q:
                            q[key] -= 400
                    if q.get("shape") == "prof":
                        q["pts"] = [(f - 400, u) for f, u in q["pts"]]
        self.assertGreater(len(extended.components(moved)), 1)

    def test_proportions(self):
        for k, d in self.data.items():
            with self.subTest(k):
                self.assertAlmostEqual(length(d["PARTS"]) / 1000, d["META"]["reference_length_m"], delta=0.005)
        longer = self.data["e09"]["PARTS"] + [dict(self.ids["e09"]["muzzle_crown"], id="probe", a0=900, a1=910)]   # Gegenprobe
        self.assertGreater(abs(length(longer) / 1000 - self.data["e09"]["META"]["reference_length_m"]), 0.005)

    def test_source_hash(self):
        for k, o in OWN.items():
            with self.subTest(k):
                a = extended.source(k, SNAP)
                self.assertEqual(a, extended.source(k, SNAP))
                self.assertIn(f"formgen/models/extended/{o['mod']}.py", a["files"])
                self.assertFalse([f for f in a["files"] if f.startswith(f"basic/pilot/w{o['num']}_")
                                  or f.startswith(f"basic/weapons/w{o['num']}_")], "kein Umbau von BASIC-NN")

    def test_snapshot_released(self):
        self.assertFalse(any(n == "basic" or n.startswith("basic.") for n in sys.modules))
        self.assertNotIn(str(SNAP), sys.path)


if __name__ == "__main__":
    unittest.main()
