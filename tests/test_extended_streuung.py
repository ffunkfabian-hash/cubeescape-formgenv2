"""EXTENDED-08 „Brace“ und EXTENDED-13 „Mantlet“ (0.23 „Breacher“): Schrotflinte und Granatwerfer als eigene Modelle.

Prüft die Datensätze ohne Blender: Felder und IDs, Blatt-IDs, Anker/Weltpunkte/Aktionen (BALLONs `variant.problems` als Orakel),
Familienschnittstellen, Budgets des Stilhandbuchs (genau ein Blickfang links außerhalb des Visiers, ≤ 3 Akzent-Bedienfunktionen, eine
Schrift, ein Grafikelement), Visierlinie (Kimme/Korn wie BASIC-08, Holo im Vertrag 60–80 mm), Schrift auf ebener Fläche, Seiten-IoU
< 0,85 gegen den eigenen BASIC-Typ, gegen jedes andere EXTENDED-Modell und gegeneinander (Rahmen aus den Hüllen beider Modelle), die
Leitmotive (Brille: zwei Läufe nebeneinander mit offenem Brillenspalt, Wülste im Querschnitt, Zwillingsauge, Schiebemantel; Panzerhaube:
Helmwölbung mit Schirm, Visiergasse als Kanal durch die Wölbung, Kastenmagazin statt Trommel, Ladeanzeige in Geschossform), die Absetzung der
beiden Typen, Zusammenhang, Länge und Quellhash. Jede Regelprüfung hat eine Gegenprobe, die aus dem erwarteten Grund rot wird; Felder,
Quellhash und Snapshot-Freigabe sind Bestandsprüfungen.
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
PAIR_MAX = 0.70                # Annahme wie 0.18/0.22: die beiden Typen einer Sitzung setzen sich deutlich ab
HOLO_RANGE = (60.0, 80.0)      # Vorgabe Visier-Standard (Holo)
IRON_TOL = 4.0                 # A: Kimme/Korn höchstens 4 mm anders als BASIC-08 (39 mm über der Laufachse, gemessen)
FRAME_MARGIN = 20.0            # A: Rand um die gemeinsame Hülle (mm)
GAP_MIN = 10.0                 # A: Brillenspalt und Ringspalt mindestens 10 mm (Nutzer Welle 1: nicht zu zart)
OWN = {"e08": dict(num="08", type="shotgun", id="EXTENDED-08", sheet="EA08", mod="e08_brace"),
       "e13": dict(num="13", type="grenade_launcher", id="EXTENDED-13", sheet="EA13", mod="e13_mantlet")}


def frame(*part_lists, margin=FRAME_MARGIN):
    """Gemeinsamer Rasterrahmen (lo, size) aus den Hüllquadern aller Teillisten (wie test_extended_fusion)."""
    bs = [b for parts in part_lists for p in parts if (b := extended.bounds(p))]
    f0, u0 = min(b[0][0] for b in bs) - margin, min(b[0][1] for b in bs) - margin
    f1, u1 = max(b[1][0] for b in bs) + margin, max(b[1][1] for b in bs) + margin
    return dict(lo=(f0, u0), size=(int(f1 - f0) + 2, int(u1 - u0) + 2))


def iou(a, b):
    return extended.side_iou(a, b, **frame(a, b))


def lights(parts):
    """Leuchtfunktionen außerhalb des Visiers."""
    return sorted(p["id"] for p in parts if p["mat"] == "energy" and p["asm"] != "sight")


def accent_functions(parts):
    return sorted({p["id"].removesuffix("_r") for p in parts if p["mat"] == "accent" and p.get("move") and p["asm"] != "sight"})


def graphics(parts):
    return [p["id"] for p in parts if p["mat"] == "accent" and not p.get("move") and p["asm"] != "sight"]


def length(parts):
    bs = [b for p in parts if (b := extended.bounds(p))]
    return max(b[1][0] for b in bs) - min(b[0][0] for b in bs)


def text_span(t):
    """Kit-Schrift ist linksbündig; rechts (side −1) läuft sie nach vorn. Länge ≈ 0,62 × Größe je Zeichen (Annahme, großzügig)."""
    n = 0.62 * t["size"] * len(t["text"])
    return (t["f"], t["f"] + n) if t["side"] == -1 else (t["f"] - n, t["f"])


def item_boxes(parts):
    """Hüllquader je Einzelform (Mehrfachteile aufgelöst): [(Teil-ID, ((f0, u0, x0), (f1, u1, x1)))]."""
    out = []
    for p in parts:
        for q in (p["items"] if p.get("shape") == "multi" else [p]):
            b = extended.bounds(dict(q, x=q.get("x", p.get("x", 0.0))) if q is not p else q)
            if b:
                out.append((p["id"], b))
    return out


def hits(parts, box, skip=()):
    """Teile, deren Einzelformen den Quader ((f0, u0, x0), (f1, u1, x1)) schneiden (offene Grenzen)."""
    (a0, a1) = box
    return sorted({pid for pid, (lo, hi) in item_boxes(parts) if pid not in skip
                   and all(lo[k] < a1[k] and a0[k] < hi[k] for k in range(3))})


def top_profile(pts, x):
    """Höchster u-Wert eines Querprofils (x, u) bei x (Schnitt mit den Kanten des Polygons)."""
    best = -math.inf
    for (x0, u0), (x1, u1) in zip(pts, pts[1:] + pts[:1]):
        if min(x0, x1) <= x <= max(x0, x1) and x0 != x1:
            best = max(best, u0 + (u1 - u0) * (x - x0) / (x1 - x0))
    return best


def crossing(pts):
    """Erstes Paar nicht benachbarter Kanten eines Polygons, die sich echt schneiden (selbstschneidendes Profil), sonst None."""
    def side(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    edges = list(zip(pts, pts[1:] + pts[:1]))
    n = len(edges)
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            (a, b), (c, d) = edges[i], edges[j]
            if side(a, b, c) * side(a, b, d) < -1e-9 and side(c, d, a) * side(c, d, b) < -1e-9:
                return i, j
    return None


def enclosed(parts, f, u):
    """True, wenn der Punkt (f, u) in der Seitensilhouette frei ist und die Lücke ringsum geschlossen ist (Negativraum)."""
    fr = frame(parts)
    mask = extended.side_mask(parts, **fr)
    rows, cols = mask.shape
    i, j = int(round(rows - 1 - (u - fr["lo"][1]))), int(round(f - fr["lo"][0]))
    if mask[i, j]:
        return False
    seen = np.zeros_like(mask)
    todo = [(i, j)]
    seen[i, j] = True
    while todo:
        a, b = todo.pop()
        if a in (0, rows - 1) or b in (0, cols - 1):
            return False
        for c, d in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
            if not mask[c, d] and not seen[c, d]:
                seen[c, d] = True
                todo.append((c, d))
    return True


@unittest.skipIf(SNAP is None, REASON)
class TestStreuung(unittest.TestCase):
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
                self.assertTrue(d["EJECT"], "Patronenwaffe mit Hülsenauswurf")
        self.assertEqual(self.data["e08"]["EJECT"]["case"], "shotshell")
        self.assertEqual(self.data["e13"]["EJECT"]["case"], "grenade_40")
        self.assertNotIn("on", self.data["e13"]["EJECT"], "Halbautomat: Hülse je Schuss, nicht erst beim Nachladen wie die Trommel")

    def test_sheet_ids(self):
        for k, o in OWN.items():
            self.assertEqual(extended.sheet_id(k), o["sheet"])
            self.assertEqual(self.data[k]["META"]["sheet_id"], o["sheet"])
            self.assertRegex(o["sheet"], f"^{extended.SHEET_PATTERN}$")
        sids = list(extended.SHEETS.values())
        self.assertEqual(len(set(sids)), len(sids), "Blatt-IDs doppelt")
        self.assertEqual(set(extended.SHEETS), set(extended.MODELS))
        self.assertIsNone(re.match(f"^{extended.SHEET_PATTERN}$", "EO08"))   # Gegenprobe: Linienbuchstabe O ist gesperrt

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
        want = {"e08": {"grip": "BGM-1", "rail": "BRI-22"},
                "e13": {"grip": "BGM-1", "rail": "BRI-22", "sight_mount": "BRI-22"}}

        def problems(ids, w):
            return [pid for pid, iface in w.items() if ids.get(pid, {}).get("iface") != iface]
        for k, ids in self.ids.items():
            with self.subTest(k):
                self.assertEqual(problems(ids, want[k]), [])
                self.assertEqual(ids["grip"]["mat"], "rubber")
        self.assertEqual(problems(self.ids["e08"], want["e13"]), ["sight_mount"])   # Gegenprobe: die Flinte hat Kimme/Korn, kein Holo
        self.assertIn("sight_rear", self.ids["e08"], "Kimme K2 wie BASIC-08")
        self.assertIn("sight_marks", self.ids["e13"], "D-Linse W1 mit Fallmarken wie BASIC-13")

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
        two = self.data["e13"]["PARTS"] + [dict(self.ids["e13"]["chamber_lamp"], id="lamp2")]   # Gegenprobe: zweiter Blickfang
        self.assertEqual(len(lights(two)), 2)
        more = self.data["e08"]["PARTS"] + [dict(self.ids["e08"]["pump_release"], id="a"), dict(self.ids["e08"]["pump_release"], id="b")]
        self.assertGreater(len(accent_functions(more)), 3)   # Gegenprobe: vier Bedienfunktionen

    def test_sight_line(self):
        def height(d):
            return d["ANCHORS"]["Socket_Eye"]["at"][1] - d["ANCHORS"]["Socket_Muzzle"]["at"][1]
        b08 = height(self.basic["e08"])
        self.assertLessEqual(abs(height(self.data["e08"]) - b08), IRON_TOL, "Kimme/Korn wie BASIC-08")
        self.assertEqual(self.data["e08"]["ANCHORS"]["Socket_Eye"]["sight_type"], "iron")
        low = copy.deepcopy(self.data["e08"])   # Gegenprobe: Kimme 10 mm tiefer weicht von BASIC-08 ab
        low["ANCHORS"]["Socket_Eye"]["at"] = tuple(v - (10 if i == 1 else 0) for i, v in enumerate(low["ANCHORS"]["Socket_Eye"]["at"]))
        self.assertGreater(abs(height(low) - b08), IRON_TOL)
        self.assertTrue(HOLO_RANGE[0] <= height(self.data["e13"]) <= HOLO_RANGE[1], height(self.data["e13"]))
        raised = copy.deepcopy(self.data["e13"])   # Gegenprobe: Visier 20 mm höher liegt außerhalb des Vertrags
        raised["ANCHORS"]["Socket_Eye"]["at"] = tuple(v + (20 if i == 1 else 0) for i, v in enumerate(raised["ANCHORS"]["Socket_Eye"]["at"]))
        self.assertGreater(height(raised), HOLO_RANGE[1])

    def test_lettering_on_flat_face(self):
        """E08: rechts im Flankenfeld zwischen Auswurffenster und Zwillingsstreifen; E13: rechts hinten auf der Haubenflanke
        zwischen Paneel und Auswurffenster, unter dem Bogenstreifen."""
        c8, c13 = self.consts["e08"], self.consts["e13"]

        def problems(k, t):
            c = self.consts[k]
            a, b = text_span(t)
            h = 0.75 * t["size"]
            if k == "e08":
                band_f0 = min(q["pts"][0][0] for q in self.ids[k]["band_side"]["items"])   # im Flankenfeld (Runde 9)
                lo, hi, u0, u1, half = c["PORT"][1] + 2, min(band_f0, c["REC"][1]) - 2, c["REC"][2] + 1, c["REC"][3] - 1, c["FLANK"]
            else:
                panel = self.ids[k]["side_panel_r"]
                lo, hi, u0, u1, half = panel["f1"] + 2, c["PORT"][0] - 2, c["SPLIT"] + 4, c["hood_top"](b) - 24, c["HALF"]
            out = []
            if a < lo or b > hi:
                out.append("außerhalb der freien Fläche")
            if t["u"] < u0 or t["u"] + h > u1:
                out.append("außerhalb der Höhe")
            if abs(abs(t["x"]) - half) > 0.2 or t["x"] > 0:
                out.append("nicht rechts auf der Seitenfläche")
            return out
        for k in OWN:
            with self.subTest(k):
                self.assertEqual(problems(k, self.ids[k]["text_r"]), [])
        self.assertIn("außerhalb der freien Fläche", problems("e08", dict(self.ids["e08"]["text_r"], f=c8["PORT"][0])))   # im Fenster
        self.assertIn("außerhalb der freien Fläche", problems("e13", dict(self.ids["e13"]["text_r"], f=c13["PORT"][0] - 10)))  # ins Fenster
        self.assertIn("außerhalb der Höhe", problems("e08", dict(self.ids["e08"]["text_r"], u=c8["SPLIT"] - 4)))           # auf der Fuge

    # ---------------------------------------------------------------- Silhouette
    def test_own_silhouette(self):
        """Seiten-IoU < 0,85 gegen den eigenen BASIC-Typ, gegen jedes andere EXTENDED-Modell und gegeneinander (< 0,70)."""
        for k, d in self.data.items():
            with self.subTest(k):
                self.assertLess(iou(self.basic[k]["PARTS"], d["PARTS"]), IOU_MAX)
                for o, parts in self.others.items():
                    self.assertLess(iou(parts, d["PARTS"]), IOU_MAX, o)
        self.assertLess(iou(self.data["e08"]["PARTS"], self.data["e13"]["PARTS"]), PAIR_MAX)
        b13 = self.basic["e13"]["PARTS"]   # Gegenproben: gleiche Form 1,0; eine Parameterlinie bleibt über der Schwelle
        self.assertGreaterEqual(iou(b13, b13), 0.99)
        trimmed = [p for p in b13 if p["id"] not in ("muzzle", "muzzle_crown")]
        self.assertGreater(iou(b13, trimmed), IOU_MAX)
        # Gegenprobe: der Rahmen aus beiden Hüllen trägt auch die 1,6 m lange Glefe, die den Standardrahmen sprengt
        self.assertLess(iou(self.others["e17"], self.data["e08"]["PARTS"]), IOU_MAX)
        with self.assertRaisesRegex(ValueError, "beschnitten"):
            extended.side_mask(self.others["e17"])

    # ---------------------------------------------------------------- Leitmotiv Brille (E08)
    def test_brace_twin_barrels(self):
        """Zwei Läufe nebeneinander auf gleicher Höhe; dazwischen ein offener Brillenspalt ≥ 10 mm vom Mantel bis zum Joch."""
        P, c = self.data["e08"]["PARTS"], self.consts["e08"]
        barrels = self.ids["e08"]["barrel"]["items"]
        self.assertEqual(len(barrels), 2)
        self.assertEqual({q["c"][0] for q in barrels}, {c["BORE"]})
        xs = sorted(q["c"][1] for q in barrels)
        self.assertAlmostEqual(xs[0], -xs[1])

        def gap_problems(parts):
            gap = xs[1] - c["BAR_R"] - (xs[0] + c["BAR_R"])
            out = [] if gap >= GAP_MIN else [f"Spalt {gap:.1f} mm"]
            half = gap / 2 - 0.5
            box = ((c["PUMP"][1] + 1, c["BORE"] - c["BAR_R"], -half), (c["YOKE"][0] - 1, c["BORE"] + c["BAR_R"], half))
            return out + hits(parts, box)
        self.assertEqual(gap_problems(P), [])
        web = dict(id="steg", shape="box", f0=c["PUMP"][1] + 10, f1=c["PUMP"][1] + 40, u0=c["BORE"] - 4, u1=c["BORE"] + 4, w=8)
        self.assertEqual(gap_problems(P + [web]), ["steg"])   # Gegenprobe: Steg im Brillenspalt

    def test_brace_twin_section(self):
        """Gehäuse, Schiebemantel und Joch tragen den Brillen-Querschnitt: zwei Wülste über den Läufen, dazwischen eine Senke."""
        c = self.consts["e08"]

        def twin(pts):
            hump = min(top_profile(pts, c["BX"]), top_profile(pts, -c["BX"]))
            dip = min(top_profile(pts, x) for x in np.linspace(-c["BX"] + 4, c["BX"] - 4, 9))
            return hump - dip
        for pid in ("upper", "pump", "muzzle"):
            with self.subTest(pid):
                p = self.ids["e08"][pid]
                self.assertEqual(p["shape"], "xprof")
                if pid == "upper":   # der Mittelsteg trägt die Schiene: Senke zwischen Wulst und Steg
                    dip = min(top_profile(p["pts"], x) for x in np.linspace(c["BX"] - 10, c["BX"] - 4, 7))
                    self.assertGreaterEqual(top_profile(p["pts"], c["BX"]) - dip, 3.0)
                else:
                    self.assertGreaterEqual(twin(p["pts"]), 5.0)
        flat = [(x, u) for x, u in self.ids["e08"]["pump"]["pts"]]
        flat = [(x, min(u, c["PUMP_U"][1])) for x, u in flat]      # Gegenprobe: oben abgeflacht (Kasten)
        self.assertLess(twin(flat), 5.0)

    def test_brace_pump_and_eye(self):
        """Der Mantel repetiert nach hinten und trifft dabei kein festes Teil (Richter R2: Laufkragen); Zwillingsauge mit zwei Anzeigen."""
        c, ids, P = self.consts["e08"], self.ids["e08"], self.data["e08"]["PARTS"]
        mv = ids["pump"]["move"]
        self.assertLess(mv["vector_mm"][0], -40)
        self.assertEqual(ids["bolt"]["move"]["vector_mm"], mv["vector_mm"], "Verschluss läuft mit dem Mantel")
        moving = {p["id"] for p in P if p["id"] == "pump" or p.get("parent_part") == "pump"}
        (_, u0, x0), (_, u1, x1) = extended.bounds(ids["pump"])

        def problems(travel):
            sweep = ((c["PUMP"][0] - travel, u0, x0), (c["PUMP"][0], u1, x1))
            return hits(P, sweep, skip=moving | {"barrel"})   # die Läufe laufen durch die Mantelbohrungen
        self.assertEqual(problems(-mv["vector_mm"][0]), [])
        self.assertEqual(problems(62), ["barrel_collars"])   # Gegenprobe: alter Hub 62 mm läuft in die Laufkragen
        eyes = ids["chamber_eyes"]["items"]
        self.assertEqual(len(eyes), 2)
        self.assertEqual(len({q["c"][1] for q in eyes}), 1, "auf gleicher Höhe")
        self.assertGreater(abs(eyes[0]["c"][0] - eyes[1]["c"][0]), 2 * eyes[0]["r"], "nebeneinander, getrennt")

    # ---------------------------------------------------------------- Leitmotiv Panzerhaube (E13)
    def test_mantlet_hood(self):
        """Helmwölbung: die Haube steigt ≥ 40 mm vom Kolben zum Scheitel, fällt ≥ 15 mm in den Schirm, der über die Stirn kragt."""
        c = self.consts["e13"]

        def problems(top):
            out = []
            if top(c["APEX"][0]) - top(c["H0"]) < 40.0:
                out.append("kein Anstieg")
            if top(c["APEX"][0]) - top(c["BROW"][0]) < 15.0:
                out.append("vorn flach")
            if top(c["H0"] + 40) - top(c["H0"]) < 0.5 * (top(c["APEX"][0]) - top(c["H0"])):
                out.append("Rücken gerade statt gewölbt")
            return out
        self.assertEqual(problems(c["hood_top"]), [])
        self.assertGreaterEqual(c["BROW"][0] - c["FACE_TOP"][0], 20.0, "Schirm kragt über die Stirn")
        self.assertGreater(c["BROW_LOW"], c["BORE"] + c["BAR_R"] + 8, "Schirm liegt über dem Lauf")
        hood = self.ids["e13"]["hood"]
        self.assertAlmostEqual(max(u for _, u in hood["pts"]), c["hood_top"](c["APEX"][0]), delta=0.5, msg="Scheitel ist der höchste Punkt")
        self.assertEqual(problems(lambda f: 150.0), ["kein Anstieg", "vorn flach"])   # Gegenprobe: flacher Deckel
        ramp = lambda f: 120 + 56 * min(1.0, max(0.0, (f - c["H0"]) / (c["APEX"][0] - c["H0"])))   # noqa: E731  Gegenprobe: Rampe
        self.assertEqual(problems(ramp), ["vorn flach", "Rücken gerade statt gewölbt"])

    def test_mantlet_sight_channel(self):
        """Visiergasse: vor dem Glas ragt kein Teil in den Sichtkanal (Glasbreite), obwohl die Haubenflanken bis zur Linie reichen."""
        c, ids = self.consts["e13"], self.ids["e13"]
        eye = self.data["e13"]["ANCHORS"]["Socket_Eye"]["at"]
        glass = ids["sight_glass"]
        hw = max(abs(x) for x, _ in glass["pts"])
        g_lo = eye[1] + min(u for _, u in glass["pts"])

        def problems(parts, hood_cuts):
            corridor = ((glass["f1"] + 1, g_lo, -hw), (c["BROW"][0] + 20, eye[1] + 1, hw))
            out = hits([p for p in parts if p["asm"] != "sight" and p["id"] != "hood"], corridor)
            if not any(q.get("shape", "box") == "box" and q["u0"] <= g_lo and q["w"] / 2 >= hw + 2 and q["f0"] <= glass["f1"]
                       and q["f1"] >= c["BROW"][0] for q in hood_cuts):
                fs = sorted((q["f0"], q["f1"]) for q in hood_cuts if q.get("shape", "box") == "box" and q["u0"] <= g_lo and q["w"] / 2 >= hw + 2)
                reach, f = glass["f1"], glass["f1"]
                for f0, f1 in fs:
                    if f0 <= reach:
                        reach = max(reach, f1)
                if reach < c["BROW"][0]:
                    out.append("Haube im Sichtkanal")
            return out
        self.assertGreaterEqual(c["hood_top"](c["APEX"][0]), g_lo + 5, "die Flanken reichen über die Glasunterkante (Gasse nötig)")
        self.assertEqual(problems(self.data["e13"]["PARTS"], ids["hood"]["cuts"]), [])
        no_gasse = [q for q in ids["hood"]["cuts"] if not (q.get("shape", "box") == "box" and q["u0"] >= c["GASSE_FLOOR"] - 1)]
        self.assertEqual(problems(self.data["e13"]["PARTS"], no_gasse), ["Haube im Sichtkanal"])   # Gegenprobe: Gasse zu
        post = dict(id="pfosten", asm="receiver", shape="box", f0=100, f1=110, u0=150, u1=180, w=6)
        self.assertEqual(problems(self.data["e13"]["PARTS"] + [post], ids["hood"]["cuts"]), ["pfosten"])   # Gegenprobe: Pfosten im Kanal

    def test_mantlet_channel_depth(self):
        """Visiergasse als Negativraum: ein Kanal ≥ 10 mm tief durch die Wölbung, ≥ 30 mm breit, vom Visiersitz bis vor den Schirm offen."""
        c = self.consts["e13"]

        def problems(floor, half, f1):
            out = []
            if c["hood_top"](c["APEX"][0]) - floor < 10.0:
                out.append("zu flach")
            if 2 * half < 30.0:
                out.append("zu schmal")
            if f1 < c["BROW"][0]:
                out.append("endet in der Haube")
            return out
        gasse = [q for q in self.ids["e13"]["hood"]["cuts"] if q.get("shape", "box") == "box" and q["u0"] >= c["GASSE_FLOOR"] - 1]
        self.assertEqual(len(gasse), 1)
        g = gasse[0]
        self.assertEqual(problems(g["u0"], g["w"] / 2, g["f1"]), [])
        self.assertLessEqual(c["BROW"][1], g["u0"], "die Schirmstirn bleibt ganz (Gasse darüber)")
        self.assertEqual(problems(c["hood_top"](c["APEX"][0]) - 4, g["w"] / 2, g["f1"]), ["zu flach"])   # Gegenprobe: Rille statt Gasse
        self.assertEqual(problems(g["u0"], g["w"] / 2, c["APEX"][0] + 40), ["endet in der Haube"])        # Gegenprobe: Sackgasse

    def test_mantlet_box_magazine(self):
        """Kastenmagazin unter der Haube vor dem Abzugsbügel, nach unten zu wechseln – keine Trommel (BASIC-13 längs, EA15 quer)."""
        ids, c = self.ids["e13"], self.consts["e13"]
        guard_f1 = max(q[0] for q in ids["trigger_guard"]["pts"])

        def problems(parts):
            pid = {p["id"]: p for p in parts}
            mag, out = pid["magazine"], []
            if mag["shape"] != "prof":
                out.append("kein Kastenmagazin")
            elif min(q[0] for q in mag["pts"]) <= guard_f1:
                out.append("im Abzugsbügel")
            if mag["move"]["vector_mm"][0] != 0 or mag["move"]["vector_mm"][1] > -80:
                out.append("nicht nach unten")
            if [p["id"] for p in parts if p["shape"] == "cyl" and p.get("axis") in ("x", "f") and p["r"] >= 60]:
                out.append("Trommel")
            return out
        P = self.data["e13"]["PARTS"]
        self.assertEqual(problems(P), [])
        shifted = [dict(p, pts=[(f - 30, u) for f, u in p["pts"]]) if p["id"] == "magazine" else p for p in P]
        self.assertEqual(problems(shifted), ["im Abzugsbügel"])              # Gegenprobe: Magazin 30 mm zurück (Runde 4)
        drum = dict(id="drum", asm="ammo", shape="cyl", axis="f", c=(66, 0), a0=98, a1=206, r=70)
        self.assertEqual(problems(P + [drum]), ["Trommel"])                   # Gegenprobe: Trommel wie BASIC-13
        lamp = ids["chamber_lamp"]["pts"]   # Ladeanzeige in Geschossform: eine Spitze vorn auf halber Höhe, hinten gerade
        tip = max(lamp, key=lambda q: q[0])
        self.assertAlmostEqual(tip[1], c["LAMP"][2], delta=0.5)
        self.assertEqual(sum(1 for q in lamp if q[0] > tip[0] - 0.5), 1)
        self.assertEqual(len({round(q[0], 3) for q in lamp if q[0] <= c["LAMP"][0] + 0.01}), 1, "hinten gerade")

    def test_brace_body_and_stock(self):
        """Runde 9: Flankenfeld 2–3 mm unter den Wülsten; Mantel mit vorstehender Stirn und Hinterkante und Griffrippen; Spaltkolben
        mit offenem Kolbenspalt (die Brille im Kolben) und einem Hals, der sich vom Gehäuse zu den Wangen verjüngt."""
        c, ids, P = self.consts["e08"], self.ids["e08"], self.data["e08"]["PARTS"]
        self.assertTrue(2.0 <= c["REC_D"] <= 3.0, "Schichtung 2–3 mm")
        fields = [q for q in ids["upper"]["cuts"] if q.get("shape", "box") == "box" and (q["f0"], q["f1"], q["u0"], q["u1"]) == tuple(c["REC"])]
        self.assertEqual(sorted(round(q["x"]) for q in fields), [-33, 33], "Flankenfeld beidseitig")
        body = extended.bounds(ids["pump"])
        for pid, step in (("pump_front", 2.0), ("pump_rear", 1.0)):
            b = extended.bounds(ids[pid])
            self.assertGreaterEqual(b[1][2] - body[1][2], step, pid)
        self.assertGreaterEqual(len(ids["pump_pad"]["items"]), 6, "drei Griffrippen je Flanke")

        def slot_problems(parts):
            half = c["SLOT"] / 2 - 0.5
            box = ((c["_SB"] + 2, 20, -half), (c["_NECK"] - 1, 140, half))   # im Hals ist der Spalt ein Schnitt (Hüllquader zählen ihn nicht)
            return hits(parts, box, skip={"butt_pad"})
        self.assertGreaterEqual(c["SLOT"], GAP_MIN)
        self.assertEqual(slot_problems(P), [])
        solid = [dict(p, items=[dict(q, w=2 * c["_CX"] + c["CHEEK"], x=0) for q in p["items"]]) if p["id"] == "stock_keel" else p for p in P]
        self.assertEqual(slot_problems(solid), ["stock_keel"])   # Gegenprobe: volle Wange schließt den Spalt
        self.assertTrue([q for q in ids["stock_neck"]["cuts"] if q.get("shape") == "plan"], "Hals verjüngt sich in der Draufsicht")

    def test_mantlet_brow_and_stock(self):
        """Runde 9: Schirm mit Materialstärke (≥ 18 mm an der Stirn, ≥ 10 mm an der Spitze), Fase und gerundeten Ecken, über dem
        Blendenkragen; Lamellenkolben: jede Lamelle tiefer und schmaler als die vorige, überlappt, die erste wächst aus der Haube."""
        c, ids = self.consts["e13"], self.ids["e13"]
        top = c["hood_top"]

        def brow_problems(under, low):
            out = []
            if top(c["FACE_TOP"][0] + 10) - under < 18.0:
                out.append("Schirm an der Stirn zu dünn")
            if c["BROW"][1] - low < 10.0:
                out.append("Schirmspitze zu dünn")
            if under - (c["BORE"] + c["BAR_R"] + 3.5) < 3.0:
                out.append("Schirm liegt auf dem Kragen")
            return out
        self.assertEqual(brow_problems(c["BROW_UNDER"], c["BROW_LOW"]), [])
        self.assertEqual(brow_problems(152.0, 146.0), ["Schirm an der Stirn zu dünn", "Schirmspitze zu dünn"])   # Gegenprobe: Blech
        cuts = ids["hood"]["cuts"]
        self.assertEqual(len([q for q in cuts if q.get("shape") == "xprof"]), 2, "Fase unter beiden Schirmkanten")
        self.assertEqual(len([q for q in cuts if q.get("shape") == "plan"]), 2, "beide Schirmecken gerundet")

        def lame_problems(lames, h0):
            out = []
            if lames[0][0] <= h0:
                out.append("erste Lamelle nicht in der Haube")
            for (f0, f1, t, w), (g0, g1, t2, w2) in zip(lames, lames[1:]):
                if not 2.0 <= t - t2 <= 4.0 or not 2.0 <= w - w2 <= 4.0:
                    out.append("keine Stufe")
                if g0 - f1 < 4.0:
                    out.append("keine Überlappung")
            return out
        self.assertEqual(lame_problems(c["LAMES"], c["H0"]), [])
        flat = [(f0, f1, c["LAMES"][0][2], c["LAMES"][0][3]) for f0, f1, _, _ in c["LAMES"]]
        self.assertEqual(lame_problems(flat, c["H0"]), ["keine Stufe", "keine Stufe"])   # Gegenprobe: glatte Platte
        self.assertGreater(c["LAMES"][-1][3], 2 * c["_HW"] + 4, "Lamellen stehen über den Kern")
        self.assertLess(c["LAMES"][0][3], 2 * c["HALF"], "unter der Haube schmaler")

    def test_detail_density(self):
        """Koordination Runde 9: Detaildichte mindestens wie BASIC – Einzelformen ≥ 90 % des Piloten, blanke Teile (Schrauben, Kanten)
        mindestens so viele wie der Pilot; zwei eigene Kolben (Spalt gegen Lamellen)."""
        def forms(P, mat=None):
            return sum(len(p["items"]) if p["shape"] == "multi" else 1 for p in P if mat is None or p["mat"] == mat)
        for k, d in self.data.items():
            with self.subTest(k):
                b = self.basic[k]["PARTS"]
                self.assertGreaterEqual(forms(d["PARTS"]), 0.9 * forms(b))
                self.assertGreaterEqual(forms(d["PARTS"], "trim"), forms(b, "trim"))
        self.assertIn("stock_neck", self.ids["e08"])
        self.assertNotIn("stock_lames", self.ids["e08"])
        self.assertIn("stock_lames", self.ids["e13"])
        self.assertNotIn("stock_neck", self.ids["e13"])
        bare = [p for p in self.data["e13"]["PARTS"] if p["mat"] != "trim"]   # Gegenprobe: ohne blanke Teile unter BASIC-13
        self.assertLess(forms(bare, "trim"), forms(self.basic["e13"]["PARTS"], "trim"))

    # ---------------------------------------------------------------- Absetzung, Zusammenhang, Länge, Quellhash
    def test_shotgun_versus_launcher(self):
        """Flinte lang, flach, zwei Bohrungen, Pumpe; Werfer kurz, gedrungen, eine große Bohrung, Kastenmagazin."""
        l8, l13 = length(self.data["e08"]["PARTS"]), length(self.data["e13"]["PARTS"])
        self.assertGreater(l8 - l13, 120)
        c8, c13 = self.consts["e08"], self.consts["e13"]
        self.assertGreaterEqual(c13["CH_R"], 2 * c8["BORE_R"], "Werferbohrung mindestens doppelt so weit")
        self.assertEqual(len(self.ids["e08"]["barrel"]["items"]), 2)
        self.assertEqual(self.ids["e13"]["barrel"]["shape"], "cyl")
        self.assertIn("pump", self.ids["e08"])
        self.assertNotIn("pump", self.ids["e13"])
        self.assertIn("magazine", self.ids["e13"])
        self.assertNotIn("magazine", self.ids["e08"])

        def height(parts):
            bs = [b for p in parts if (b := extended.bounds(p)) and p["asm"] not in ("sight", "grip_controls")]
            return max(b[1][1] for b in bs) - min(b[0][1] for b in bs)
        self.assertGreater(height(self.data["e13"]["PARTS"]) / l13, 1.5 * height(self.data["e08"]["PARTS"]) / l8, "Werfer gedrungener")

    def test_port_opens_before_eject(self):
        """Richter R5: Ein Teil vor dem Auswurffenster öffnet im Schussablauf vor dem Auswurf und schließt danach wieder."""
        def problems(act, pid):
            keys = act["keys"].get(pid)
            if not keys:
                return [f"{pid} fehlt im Ablauf"]
            eject = [f for f, e in act["events"] if e == "eject"][0]
            val = dict(keys)
            at = max(f for f in val if f <= eject)
            out = [] if val[at] == 1 else ["zu beim Auswurf"]
            return out + ([] if keys[-1][1] == 0 else ["bleibt offen"])
        act = self.data["e13"]["ACTIONS"]["fire"]
        self.assertEqual(problems(act, "port_cover"), [])
        port = self.consts["e13"]["PORT"]
        self.assertGreaterEqual(self.ids["e13"]["port_cover"]["move"]["vector_mm"][0], port[1] - port[0], "Schieber gibt das ganze Fenster frei")
        late = dict(act, keys=dict(act["keys"], port_cover=[(0, 0), (9, 0), (10, 1), (16, 0)]))
        self.assertEqual(problems(late, "port_cover"), ["zu beim Auswurf"])          # Gegenprobe: öffnet erst nach dem Auswurf
        gone = dict(act, keys={k: v for k, v in act["keys"].items() if k != "port_cover"})
        self.assertEqual(problems(gone, "port_cover"), ["port_cover fehlt im Ablauf"])   # Gegenprobe: Stand vor R5

    def test_profiles_simple(self):
        """Kein Seiten- oder Querprofil schneidet sich selbst (Richter R1 fand einen gekreuzten Kantenstreifen)."""
        def problems(parts):
            out = []
            for p in parts:
                for q in (p["items"] if p.get("shape") == "multi" else [p]):
                    if q.get("shape") in ("prof", "xprof") and crossing([tuple(v) for v in q["pts"]]):
                        out.append(p["id"])
            return sorted(set(out))
        for k, d in self.data.items():
            with self.subTest(k):
                self.assertEqual(problems(d["PARTS"]), [])
        edges = self.ids["e13"]["gasse_edges"]   # Gegenprobe: zweite Hälfte umgekehrt wie vor der Korrektur
        half = len(edges["items"][0]["pts"]) // 2
        bad = dict(edges, items=[dict(q, pts=q["pts"][:half] + q["pts"][half:][::-1]) for q in edges["items"]])
        self.assertEqual(problems([bad]), ["gasse_edges"])

    def test_no_floating_parts(self):
        for k, d in self.data.items():
            with self.subTest(k):
                self.assertEqual(extended.components(d["PARTS"])[1:], [])
        moved = copy.deepcopy(self.data["e08"]["PARTS"])   # Gegenprobe: Joch 60 mm nach vorn → eigene Gruppe
        for p in moved:
            if p["id"] in ("muzzle", "muzzle_crown", "sight_post_base"):
                for q in p.get("items", [p]):
                    for key in ("a0", "a1", "f0", "f1"):
                        if key in q:
                            q[key] += 60
                if p["shape"] == "prof":
                    p["pts"] = [(f + 60, u) for f, u in p["pts"]]
        self.assertGreater(len(extended.components(moved)), 1)

    def test_proportions(self):
        for k, d in self.data.items():
            with self.subTest(k):
                self.assertAlmostEqual(length(d["PARTS"]) / 1000, d["META"]["reference_length_m"], delta=0.005)
        longer = self.data["e13"]["PARTS"] + [dict(self.ids["e13"]["muzzle_crown"], id="probe", a0=400, a1=410)]   # Gegenprobe
        self.assertGreater(abs(length(longer) / 1000 - self.data["e13"]["META"]["reference_length_m"]), 0.005)

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
