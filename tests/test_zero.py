"""ZERO-01 „Crosshair“ (0.46 „Zero“): eigenständiges Automatikgewehr der BASIC-Familie mit offenem Nullrahmen-Gehäuse.

Prüft den Datensatz ohne Blender nach dem Design-Kanon (docs/design-kanon.md › 7): Felder und IDs, Blatt-ID ZA01, Weltpunkte mit BALLONs
`variant.problems` als Orakel, Budgets, Visierlinie, eigene Silhouette gegen BASIC-01 und alle EXTENDED-Langwaffen, keine schwebenden
Teile, das Leitmotiv (geschlossene Lücke im Rahmen, Fadenkreuz aus Säule, Schelle und Steg), Magazin vor dem Bügel, gestaltete
Querschnitte, keine Stifte, Schrift auf ebener Fläche, Verschlussweg im Rahmen, einfache Profile und die Messzeile im Band der
Langwaffen. Jede Regel hat eine Gegenprobe, die aus dem erwarteten Grund rot wird. Dazu: das Renderwerkzeug baut z01 und nicht EA01.
"""
import argparse
import copy
import importlib
import sys
import unittest

import numpy as np
from PIL import Image, ImageDraw

from formgen import ballon, extended
from tests.test_extended import SIGHT_RANGE, IOU_MAX, accent_functions, lights
from tests.test_extended_schulter import crossing, text_span, width_at
from tests.test_extended_sonder import graphics, sticks

try:
    SNAP = ballon.snapshot()
except ballon.BallonError as error:   # z. B. Cloud ohne BALLON-Checkout
    SNAP, REASON = None, str(error)
else:
    REASON = ""

LONG = ("e01", "e02", "e03", "e08", "e09", "e10", "e11", "e12", "e15")   # V: Klasse Langwaffe (formgen.kanon.CLASSES)
FRAME = dict(lo=(-420.0, -200.0), size=(1500, 520))   # V: wie 0.19 – Langwaffen über f 780 (EA09, EA11) brauchen den längeren Rahmen
HOLE_MIN = 3000     # A: geschlossene Lücke im Rahmen mindestens 3000 mm² (Öffnung 244 × 68 abzüglich Achse und Fadenkreuz ≈ 6000)


def enclosed(mask, box, lo=(-420.0, -200.0)) -> int:
    """Fläche (mm²) der Lücken in box = (f0, f1, u0, u1), die von außen nicht erreichbar sind (Negativraum ganz umschlossen, an der
    Silhouette gemessen; extended.side_mask: 1 mm je Pixel, Zeile 0 = oben). Die Box trennt den Rahmen vom Abzugsbügel."""
    im = Image.fromarray(np.pad(mask, 1).astype(np.uint8) * 255).copy()   # eigene Kopie: floodfill schreibt sonst still nicht
    ImageDraw.floodfill(im, (0, 0), 128)
    holes = (np.asarray(im) == 0)[1:-1, 1:-1]
    f0, f1, u0, u1 = box
    rows = lo[1] + mask.shape[0] - 1 - np.arange(mask.shape[0])
    cols = np.arange(mask.shape[1]) + lo[0]
    return int(holes[np.ix_((rows >= u0) & (rows <= u1), (cols >= f0) & (cols <= f1))].sum())


def holes(model, sid) -> int:
    """Fläche (mm²) aller umschlossenen Lücken der Seitensilhouette am ausgewerteten Netz mit Bool-Schnitten (`geom.evaluate`; die
    Kanon-Dreiecke und `extended.side_mask` sehen Schnitte an Querprofilen nicht). 1 mm je Pixel."""
    from formgen import extended_lines, geom, kanon, model as mdl
    ev = geom.evaluate(mdl.normalize(extended_lines.author(model, sid)[0]))
    polys = [np.asarray(m["vertices"], float)[list(f)][:, list(kanon.SIDE)] * 1000 for p in ev["parts"]
             for m in [p["mesh"]] for f in m["faces"]]
    allp = np.concatenate(polys)
    lo, hi = allp.min(0) - 4, allp.max(0) + 4
    im = Image.new("L", tuple(int(v) + 1 for v in hi - lo), 0)
    d = ImageDraw.Draw(im)
    for q in polys:
        d.polygon([(float(a - lo[0]), float(hi[1] - b)) for a, b in q], fill=255)
    ImageDraw.floodfill(im, (0, 0), 128)
    return int((np.asarray(im) == 0).sum())


def inside(pt, poly) -> bool:
    """Punkt (f, u) im Polygon (Strahlverfahren)."""
    f, u = pt
    hit = False
    for (f0, u0), (f1, u1) in zip(poly, poly[1:] + poly[:1]):
        if (u0 > u) != (u1 > u) and f < f0 + (u - u0) * (f1 - f0) / (u1 - u0):
            hit = not hit
    return hit


def touch(a, b, tol=0.5) -> bool:
    (lo1, hi1), (lo2, hi2) = extended.bounds(a), extended.bounds(b)
    return all(lo1[k] <= hi2[k] + tol and lo2[k] <= hi1[k] + tol for k in range(3))


@unittest.skipIf(SNAP is None, REASON)
class TestCrosshair(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = extended.load("z01", SNAP)
        cls.parts = cls.data["PARTS"]
        cls.ids = {p["id"]: p for p in cls.parts}
        cls.basic = extended.load_basic("01", SNAP)
        from formgen import kanon, variety, extended_lines
        cls.rows, cls.tris = kanon._family(SNAP)   # Familie (BASIC A, EA01–EA17) einmal messen, wie formgen.kanon
        cls.own = variety.triangles(extended_lines.author(cls.data, "ZA01")[0])

    def test_fields_and_ids(self):
        for k in ("META", "PARTS", "ASSEMBLIES", "ANCHORS", "POINTS", "ACTIONS"):
            self.assertIn(k, self.data)
        meta = self.data["META"]
        self.assertEqual((meta["id"], meta["type"], meta["sheet_id"]), ("ZERO-01", "auto_rifle", "ZA01"))
        self.assertEqual(len(self.ids), len(self.parts), "Teil-IDs doppelt")
        asms = {a["id"] for a in self.data["ASSEMBLIES"]}
        self.assertEqual(asms, {a["id"] for a in self.basic["ASSEMBLIES"]}, "Baugruppen wie die Familie")
        self.assertEqual({p["asm"] for p in self.parts} - asms, set())
        for p in self.parts:
            if p.get("parent_part"):
                self.assertIn(p["parent_part"], self.ids, p["id"])

    def test_sheet_id(self):
        """ZA01: Muster Z<Linie><NN>, Register = META, kein Zusammenstoß mit Waffen-, Roboter- und EXTENDED-Blättern."""
        import re
        from formgen import variants
        from formgen.robot import lines
        self.assertEqual(extended.sheet_id("z01"), "ZA01")
        self.assertEqual(extended.package("z01"), "zero")
        self.assertEqual(extended.package("e01"), "extended")
        self.assertRegex("ZA01", f"^{extended.SHEET_PATTERN}$")
        others = set(variants.sheets()) | set(lines.sheets()) | {v for k, v in extended.SHEETS.items() if k != "z01"}
        self.assertNotIn("ZA01", others)
        for bad in ("ZI01", "ZO01", "ZA1", "XA01", "BA01"):   # Gegenproben: gesperrte Buchstaben, Format, fremde Reihe
            self.assertIsNone(re.fullmatch(extended.SHEET_PATTERN, bad), bad)

    def test_anchors_points_actions(self):
        A = self.data["ANCHORS"]
        for name in ("Socket_Hand", "Socket_SupportHand", "Socket_Muzzle", "Socket_MagWell", "Socket_Charge", "Socket_Eye"):
            self.assertIn(name, A)
            self.assertIn(A[name]["part"], self.ids, name)
        self.assertEqual(tuple(A["Socket_Hand"]["at"]), (0, 0, 0))
        for k, v in self.data["ACTIONS"].items():
            for pid in v["keys"]:
                self.assertIn("move", self.ids[pid], f"{k}: {pid} ohne Bewegung")
        sys.path.insert(0, str(SNAP))
        try:
            variant = importlib.import_module("basic.variant")
            W = variant.as_module(copy.deepcopy(self.data))
            self.assertEqual(variant.problems(W), [])
        finally:
            sys.path.remove(str(SNAP))
            extended._purge()

    def test_family_interfaces(self):
        self.assertEqual((self.ids["grip"]["mat"], self.ids["grip"]["iface"]), ("rubber", "BGM-1"))
        self.assertEqual(self.ids["mag_well"]["iface"], "BMW-R")
        self.assertEqual(self.ids["muzzle"]["iface"], "BMZ-15")
        self.assertEqual(self.ids["rail"]["iface"], "BRI-22")
        self.assertEqual((self.ids["frame_top"]["mat"], self.ids["frame_low"]["mat"]), ("shell", "graphite"), "Creme über Graphit")

    def test_budgets(self):
        self.assertEqual(lights(self.parts), ["ammo_counter", "chamber", "sight_emitter"])   # ≤ 3 (Visieremitter zählt mit, wie EA01)
        self.assertEqual(accent_functions(self.parts), ["charging_handle", "mag_release", "selector"])
        self.assertEqual([p["id"] for p in self.parts if p["shape"] == "text"], ["text_r"])
        self.assertEqual(graphics(self.parts), ["chevron"])
        extra = self.parts + [dict(self.ids["ammo_counter"], id="x1"), dict(self.ids["ammo_counter"], id="x2")]
        self.assertGreater(len(lights(extra)), 3)   # Gegenprobe: die Schranke schlägt an

    def test_sight_line(self):
        bore = self.ids["barrel"]["c"][0]
        eye = self.data["ANCHORS"]["Socket_Eye"]["at"][1]
        self.assertEqual(bore, 106)
        self.assertTrue(SIGHT_RANGE[0] <= eye - bore <= SIGHT_RANGE[1], eye - bore)
        self.assertLessEqual(eye - bore, 74, "Familienband der Langwaffen (Kanon-Messblock)")

    def test_own_silhouette(self):
        """Seiten-IoU des Kanons (`kanon._side_iou` am ausgewerteten Netz, gemeinsamer Ursprung am Griff) < 0,85 gegen BASIC-01 und jede
        EXTENDED-Langwaffe (Kanon › 2); dazu die Näherung `extended.side_iou` wie bei EA01. Gegenproben: sich selbst 1,0, eine Linie ohne
        Mündung bleibt über der Schwelle."""
        from formgen import kanon
        for sid in ("BA01",) + tuple(f"EA{k[1:]}" for k in LONG):
            with self.subTest(sid):
                self.assertLess(kanon._side_iou(self.own, self.tris[sid]), IOU_MAX)
        self.assertGreaterEqual(kanon._side_iou(self.own, self.own), 0.99)
        self.assertLess(extended.side_iou(self.basic["PARTS"], self.parts), IOU_MAX)
        for key in LONG:
            with self.subTest(key):
                self.assertLess(extended.side_iou(extended.load(key, SNAP)["PARTS"], self.parts, **FRAME), IOU_MAX)
        trimmed = [p for p in self.parts if p["id"] not in ("muzzle", "muzzle_crown")]   # eine Linie bliebe über der Schwelle
        self.assertGreater(extended.side_iou(self.parts, trimmed), IOU_MAX)

    def test_no_floating_parts(self):
        self.assertEqual(extended.components(self.parts)[1:], [])
        moved = copy.deepcopy(self.parts)   # Gegenprobe: Kammersteg 70 mm nach außen → eigene Gruppe
        next(p for p in moved if p["id"] == "cross_web")["x"] = 70
        self.assertGreater(len(extended.components(moved)), 1)

    def test_zero_frame_is_open(self):
        """Leitmotiv: der Rahmen umschließt eine Lücke, durch die man quer hindurchsieht (Negativraum an der Silhouette, L:35).
        Gegenprobe: ohne Öffnungsschnitt ist der Rahmen ein Block."""
        cut = next(c for c in self.ids["frame_top"]["cuts"] if c.get("w") == 80)["pts"]
        box = (min(q[0] for q in cut), max(q[0] for q in cut), min(q[1] for q in cut), max(q[1] for q in cut))
        self.assertGreater(enclosed(extended.side_mask(self.parts), box), HOLE_MIN)
        closed = copy.deepcopy(self.parts)
        for p in closed:
            if p["id"] in ("frame_top", "frame_low"):
                p["cuts"] = [c for c in p["cuts"] if c.get("w") != 80]
        self.assertEqual(enclosed(extended.side_mask(closed), box), 0)

    def test_crosshair(self):
        """Fadenkreuz: Säule (unten) und Steg (oben) stehen auf derselben Achse wie die Kammerschelle; die Säule reicht von der Wanne bis
        unter die Schelle, der Steg von der Schelle bis an den Bügel; die Laufachse geht durch beide Pfosten. Gegenprobe: ein gekürzter
        Steg erreicht den Bügel nicht mehr."""
        clamp, web, column = self.ids["chamber_clamp"], self.ids["cross_web"], self.ids["feed_column"]
        opening = next(c for c in self.ids["frame_top"]["cuts"] if c.get("w") == 80)["pts"]
        o_f0, o_f1 = min(q[0] for q in opening), max(q[0] for q in opening)
        o_u0, o_u1 = min(q[1] for q in opening), max(q[1] for q in opening)
        mid, r = (clamp["a0"] + clamp["a1"]) / 2, clamp["r"]

        def spans(p, lo, hi):   # (f, u)-Hülle von p reicht von lo bis hi
            (f0, u0, _), (f1, u1, _) = extended.bounds(p)
            return u0 <= lo and u1 >= hi and f0 < mid < f1
        self.assertAlmostEqual((web["f0"] + web["f1"]) / 2, mid)
        top = [q[0] for q in column["pts"] if q[1] == max(u for _, u in column["pts"])]
        self.assertAlmostEqual(sum(top) / len(top), mid)
        self.assertTrue(spans(web, 106 + r - 1, o_u1))
        self.assertTrue(spans(column, o_u0, 106 - r + 1))
        self.assertTrue(o_f0 < mid < o_f1 and o_f0 < self.ids["chamber"]["a1"] <= o_f1 + 2)
        self.assertEqual({clamp["c"][0], self.ids["chamber"]["c"][0], self.ids["barrel"]["c"][0]}, {106})
        self.assertFalse(spans(dict(web, u1=web["u1"] - 6), 106 + r - 1, o_u1))

    def test_bolt_travel_inside_frame(self):
        """Der Verschluss läuft im Feuer sichtbar im Rahmen: der Kopf bleibt vor dem hinteren Pfosten, die Spannnase in der Öffnung,
        in Ruhe sitzt der Kopf an der Kammerschelle (Zuführstelle). Gegenprobe: 160 mm Hub verschwände im Pfosten."""
        bolt, head, lug, cap = (self.ids[k] for k in ("bolt_carrier", "bolt_head", "bolt_lug", "chamber_clamp"))
        rear = min(q[0] for q in next(c for c in self.ids["frame_top"]["cuts"] if c.get("w") == 80)["pts"])   # Öffnung hinten
        back = bolt["move"]["vector_mm"][0]
        self.assertEqual(head["a1"], cap["a0"])
        self.assertGreater(head["a0"] + back, rear)
        opening = next(c for c in self.ids["frame_top"]["cuts"] if c.get("w") == 80)["pts"]

        def free(lug):   # alle Ecken der Spannnase bei vollem Hub im Öffnungspolygon (samt 45°-Fasen, Richter R2)
            return all(inside((f + back, u), opening) for f in (lug["f0"], lug["f1"]) for u in (lug["u0"], lug["u1"]))
        self.assertTrue(free(lug))
        self.assertFalse(free(dict(lug, f0=20, f1=46)))   # Gegenprobe: alte Lage r4 stößt 3 mm in die hintere obere Fase
        self.assertLess(bolt["a0"], rear)   # der Träger steckt in Ruhe im hinteren Pfosten
        self.assertLess(head["a0"] - 160, rear)

    def test_magazine_before_guard(self):
        mag = max(q[0] for q in self.ids["trigger_guard"]["pts"])
        self.assertGreater(min(q[0] for q in self.ids["magazine"]["pts"]), mag)
        self.assertLess(min(q[0] for q in self.ids["grip"]["pts"]), mag)   # Gegenprobe: der Griff liegt hinter dem Bügelende

    def test_shaped_sections(self):
        """Keine Rechteck-Querschnitte (L:38): Rahmenbügel, Wanne, Haube (vor und hinter der Stufe), Schaftbalken und Fersenkeil mit 45°-Einzug
        ≥ R_MID 3 mm an beiden Kanten; die Unterteile je Seite schmaler als das Oberteil. Gegenprobe: ein Einzug unter R_MID fällt auf."""
        def depths(p):
            return [abs(c["pts"][1][1] - c["pts"][2][1]) - 2 for c in p["cuts"] if c.get("shape") == "xprof"]
        for pid, n in (("frame_top", 2), ("frame_low", 2), ("hg_top", 4), ("hg_low", 2), ("stock", 2), ("stock_heel", 2)):
            with self.subTest(pid):
                self.assertEqual(len(depths(self.ids[pid])), n)
                self.assertGreaterEqual(min(depths(self.ids[pid])), 3)
        self.assertLess(self.ids["frame_low"]["w"], self.ids["frame_top"]["w"])
        self.assertLess(self.ids["hg_low"]["w"], self.ids["hg_top"]["w"])
        self.assertLess(self.ids["stock_heel"]["w"], self.ids["stock"]["w"])
        plans = [c for pid in ("frame_top", "frame_low") for c in self.ids[pid]["cuts"] if c.get("shape") == "plan"]
        self.assertEqual(len(plans), 8, "45°-Ecken des Rahmens in der Draufsicht")
        for c in plans:   # im Uhrzeigersinn (Stilregel wie test_plan_winding)
            self.assertLess(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(c["pts"], c["pts"][1:] + c["pts"][:1])), 0)
        flat = dict(self.ids["hg_top"], cuts=[dict(c, pts=[c["pts"][0], c["pts"][1], (c["pts"][2][0], c["pts"][1][1] - 3)])
                                               for c in self.ids["hg_top"]["cuts"]])
        self.assertLess(min(depths(flat)), 3)

    def test_no_thin_sticks(self):
        self.assertEqual(sticks(self.parts), [])
        rod = dict(id="guide_rod", asm="mechanism", shape="cyl", mat="dark_metal", axis="f", c=(124, 0), a0=-66, a1=178, r=4.0)
        self.assertEqual(sticks(self.parts + [rod]), ["guide_rod"])   # Gegenprobe: Führungsstange Ø 8 durch den Rahmen

    def test_lettering_on_flat_face(self):
        """Schrift rechts auf der ebenen Haubenflanke: vor den Chevrons nach vorn, hinter der Haubenstufe, unter dem Kanten-Einzug."""
        t, hood = self.ids["text_r"], self.ids["hg_top"]
        step = max(f for f, u in hood["pts"] if u == max(v for _, v in hood["pts"]))   # Hinterkante der 45°-Stufe

        def problems(t):
            start, end = text_span(t)
            out = []
            if start < max(q[0] for i in self.ids["chevron"]["items"] for q in i["pts"]):
                out.append("über den Chevrons")
            if end > step:
                out.append("über der Haubenstufe")
            if not (104 + 2 <= t["u"] - t["size"] / 2 and t["u"] + t["size"] / 2 <= 134 - 6 - 1):
                out.append("über dem Einzug")
            if abs(abs(t["x"]) - hood["w"] / 2) > 0.2 or t["side"] != -1:
                out.append("nicht auf der rechten Flanke")
            return out
        self.assertEqual(problems(t), [])
        self.assertEqual(problems(dict(t, f=t["f"] - 30)), ["über den Chevrons"])     # Gegenproben
        self.assertEqual(problems(dict(t, f=step - 20)), ["über der Haubenstufe"])
        self.assertEqual(problems(dict(t, u=128)), ["über dem Einzug"])

    def test_profiles_simple(self):
        for p in self.parts:
            for q in (p["items"] if p["shape"] == "multi" else [p]):
                if q.get("shape", p["shape"]) == "prof":
                    self.assertIsNone(crossing(list(map(tuple, q["pts"]))), p["id"])

    def test_source_hash(self):
        a = extended.source("z01", SNAP)
        self.assertEqual(a, extended.source("z01", SNAP))
        self.assertIn("formgen/models/zero/z01_crosshair.py", a["files"])
        self.assertIn("basic/common.py", a["files"])
        self.assertNotIn("basic/pilot/w01_auto_rifle_v21.py", a["files"], "kein Umbau von BASIC-01")
        self.assertFalse([f for f in a["files"] if "e01_spearhead" in f], "kein Umbau von EXTENDED-01")
        self.assertIn("formgen/models/extended/e01_spearhead.py", extended.source("e01", SNAP)["files"])   # EA-Pfade unverändert

    def test_in_family_band(self):
        """Messzeile im Band der Langwaffen (Detaildichte, Klarheit, Proportionen; formgen.kanon.outside) – Stilprüfung Nr. 3. Das
        Referenzband ist nur die Familie (ohne ZA01). Gegenproben: zehn Platten (Detaildichte) und Ausreißer in Länge, Breite und Füllgrad."""
        from formgen import kanon
        row = kanon.measure_model(self.data, "ZA01", SNAP, family=(self.rows, self.tris))
        self.assertNotIn("ZA01", {r["id"] for r in self.rows})
        self.assertEqual(kanon.outside(row, self.rows), [])
        slabs = dict(row, parts=10, forms=10, round=0.0, boxy=0.9)   # Astra-Formstudie
        self.assertLessEqual({"parts", "forms", "round", "boxy"}, {k for k, *_ in kanon.outside(slabs, self.rows)})
        odd = dict(row, length=1300, width=150, fill=0.7)
        self.assertLessEqual({"length", "width", "fill"}, {k for k, *_ in kanon.outside(odd, self.rows)})


@unittest.skipIf(SNAP is None, REASON)
class TestFacet(unittest.TestCase):
    """ZERO-02 „Facet“ (Nutzerwahl W4): Facettenkeil – Sechskant-Querschnitte an Gehäuse, Haube und Schaft, steigender Keilschaft mit Schlitz."""

    @classmethod
    def setUpClass(cls):
        from formgen import kanon, variety, extended_lines
        cls.data = extended.load("z02", SNAP)
        cls.parts = cls.data["PARTS"]
        cls.ids = {p["id"]: p for p in cls.parts}
        cls.basic = extended.load_basic("01", SNAP)
        cls.rows, cls.tris = kanon._family(SNAP)
        cls.own = variety.triangles(extended_lines.author(cls.data, "ZA02")[0])
        cls.zero1 = variety.triangles(extended_lines.author(extended.load("z01", SNAP), "ZA01")[0])

    def test_fields_ids_and_sheet(self):
        import re
        meta = self.data["META"]
        self.assertEqual((meta["id"], meta["type"], meta["sheet_id"]), ("ZERO-02", "auto_rifle", "ZA02"))
        self.assertEqual((extended.sheet_id("z02"), extended.package("z02")), ("ZA02", "zero"))
        self.assertRegex("ZA02", f"^{extended.SHEET_PATTERN}$")
        self.assertEqual(len(self.ids), len(self.parts), "Teil-IDs doppelt")
        self.assertEqual({a["id"] for a in self.data["ASSEMBLIES"]}, {a["id"] for a in self.basic["ASSEMBLIES"]})
        self.assertEqual(len(set(extended.SHEETS.values())), len(extended.SHEETS), "Blatt-IDs doppelt")
        self.assertIsNone(re.fullmatch(extended.SHEET_PATTERN, "ZA2"))   # Gegenprobe

    def test_anchors_points_actions(self):
        A = self.data["ANCHORS"]
        for name in ("Socket_Hand", "Socket_SupportHand", "Socket_Muzzle", "Socket_MagWell", "Socket_Charge", "Socket_Eye"):
            self.assertIn(A[name]["part"], self.ids, name)
        for k, v in self.data["ACTIONS"].items():
            for pid in v["keys"]:
                self.assertIn("move", self.ids[pid], f"{k}: {pid} ohne Bewegung")
        sys.path.insert(0, str(SNAP))
        try:
            variant = importlib.import_module("basic.variant")
            self.assertEqual(variant.problems(variant.as_module(copy.deepcopy(self.data))), [])
        finally:
            sys.path.remove(str(SNAP))
            extended._purge()

    def test_family_and_budgets(self):
        self.assertEqual((self.ids["grip"]["iface"], self.ids["mag_well"]["iface"], self.ids["muzzle"]["iface"]), ("BGM-1", "BMW-R", "BMZ-15"))
        self.assertEqual((self.ids["upper"]["mat"], self.ids["lower"]["mat"]), ("shell", "graphite"))
        self.assertEqual(lights(self.parts), ["ammo_counter", "edge_glow", "sight_emitter"])
        self.assertEqual(accent_functions(self.parts), ["charging_handle", "mag_release", "selector"])
        self.assertEqual([p["id"] for p in self.parts if p["shape"] == "text"], ["text_r"])
        self.assertEqual(graphics(self.parts), ["chevron"])
        bore, eye = self.ids["barrel"]["c"][0], self.data["ANCHORS"]["Socket_Eye"]["at"][1]
        self.assertTrue(SIGHT_RANGE[0] <= eye - bore <= min(SIGHT_RANGE[1], 74), eye - bore)

    def test_own_silhouette(self):
        """Kanon-IoU < 0,85 gegen BASIC-01, jede EXTENDED-Langwaffe und ZERO-01 (Skizze W4 lag mit tiefem Keil bei 0,87 gegen EA01).
        Gegenprobe: ein tiefer Keil wie in der Skizze (Schaftfuß u 22) rückt näher an EA01 (die Messung reagiert auf den Treiber)."""
        from formgen import kanon, variety, extended_lines
        for sid in ("BA01",) + tuple(f"EA{k[1:]}" for k in LONG):
            with self.subTest(sid):
                self.assertLess(kanon._side_iou(self.own, self.tris[sid]), IOU_MAX)
        self.assertLess(kanon._side_iou(self.own, self.zero1), IOU_MAX)
        deep = copy.deepcopy(self.data)
        deep["PARTS"].append(dict(shape="prof", id="deep_wedge", asm="stock", mat="shell", pts=[(-108, 96), (-300, 22), (-300, 96)], w=40))
        t = variety.triangles(extended_lines.author(deep, "ZA02")[0])
        self.assertGreater(kanon._side_iou(t, self.tris["EA01"]), kanon._side_iou(self.own, self.tris["EA01"]))

    def test_no_floating_parts(self):
        self.assertEqual(extended.components(self.parts)[1:], [])
        moved = copy.deepcopy(self.parts)   # Gegenprobe: Haubenleiste 40 mm nach außen
        next(p for p in moved if p["id"] == "hg_cover")["x"] = 40
        self.assertGreater(len(extended.components(moved)), 1)

    def test_facet_sections(self):
        """Leitmotiv: Gehäuse, Haube und Schaft sind Sechskant-Querprofile (≥ 6 Ecken, Breite ändert sich über die Höhe um ≥ 3 mm, mit
        senkrechtem Mittelband); die Unterteile sind schmaler. Gegenprobe: ein Rechteck fällt durch."""
        def facetted(pts):
            us = [u for _, u in pts]
            widths = [width_at(pts, min(us) + (max(us) - min(us)) * t) for t in (0.05, 0.5, 0.95)]
            band = any(x0 == x1 and u0 != u1 for (x0, u0), (x1, u1) in zip(pts, pts[1:] + pts[:1]))
            return len(pts) >= 6 and max(widths) - min(widths) >= 3 and band
        for pid in ("upper", "hg_top", "stock"):
            with self.subTest(pid):
                self.assertEqual(self.ids[pid]["shape"], "xprof")
                self.assertTrue(facetted(self.ids[pid]["pts"]))
        self.assertFalse(facetted([(-20, 50), (20, 50), (20, 150), (-20, 150)]))
        self.assertLess(max(x for x, _ in self.ids["lower"]["pts"]), max(x for x, _ in self.ids["upper"]["pts"]))

    def test_wedge_stock_and_slot(self):
        """Keilschaft: Oberkante steigt über das Gehäuse (154 > 142), der Graphit-Keil fällt zur Kappe; der Schlitz ist ein abgeschlossener
        Negativraum an der Silhouette des ausgewerteten Netzes (kein Fachwerkdreieck: vier Ecken, Ober- und Unterkante parallel).
        Gegenprobe: ohne Schlitz fehlt genau diese Lücke."""
        stock = self.ids["stock"]
        self.assertGreater(max(u for _, u in stock["pts"]), 142)
        area = lambda q: abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(q, q[1:] + q[:1]))) / 2   # noqa: E731
        slot = min((c["pts"] for c in stock["cuts"] if len(c["pts"]) == 4 and c.get("w") == 80), key=area)
        slope = lambda a, b: (b[1] - a[1]) / (b[0] - a[0])   # noqa: E731
        self.assertAlmostEqual(slope(slot[0], slot[1]), slope(slot[3], slot[2]), places=3)
        closed = copy.deepcopy(self.data)
        cl = next(p for p in closed["PARTS"] if p["id"] == "stock")
        cl["cuts"] = [c for c in cl["cuts"] if c["pts"] != slot]
        self.assertGreater(holes(self.data, "ZA02") - holes(closed, "ZA02"), 1000)   # Schlitz ≈ 125 × 16 mm, abzüglich Kantenleiste

    def test_magazine_sticks_lettering_profiles(self):
        guard = max(q[0] for q in self.ids["trigger_guard"]["pts"])
        self.assertGreater(min(q[0] for q in self.ids["magazine"]["pts"]), guard)
        self.assertEqual(sticks(self.parts), [])
        t, up = self.ids["text_r"], self.ids["upper"]
        start, end = text_span(t)
        port = next(c for c in up["cuts"] if c.get("shape", "box") == "box" and c.get("x") == -26.0)
        band = [u for x, u in up["pts"] if x == -26.0]
        ok = lambda s, e, u: e < port["f0"] and s >= up["f0"] and min(band) + 1 <= u - 2.5 and u + 2.5 <= max(band) - 1   # noqa: E731
        self.assertTrue(ok(start, end, t["u"]))
        self.assertFalse(ok(start + 100, end + 100, t["u"]))   # Gegenprobe: auf dem Auswurffenster
        self.assertFalse(ok(start, end, 124))                  # Gegenprobe: über dem Mittelband
        for p in self.parts:
            for q in (p["items"] if p["shape"] == "multi" else [p]):
                if q.get("shape", p["shape"]) == "prof":
                    self.assertIsNone(crossing(list(map(tuple, q["pts"]))), p["id"])

    def test_source_and_band(self):
        from formgen import kanon
        a = extended.source("z02", SNAP)
        self.assertIn("formgen/models/zero/z02_facet.py", a["files"])
        self.assertFalse([f for f in a["files"] if "z01_" in f or "e01_" in f or "w01_auto_rifle" in f], "kein Umbau")
        row = kanon.measure_model(self.data, "ZA02", SNAP, family=(self.rows, self.tris))
        self.assertEqual(kanon.outside(row, self.rows), [])
        self.assertIn("parts", {k for k, *_ in kanon.outside(dict(row, parts=10), self.rows)})   # Gegenprobe


@unittest.skipIf(SNAP is None, REASON)
class TestRenderSubject(unittest.TestCase):
    """0.46: `tools/extended_render.py z01` baut ZERO-01 (vorher still EA01, weil die Blatt-ID über das EXTENDED-Linienregister lief)."""

    def test_subject(self):
        saved = list(sys.path)
        self.addCleanup(lambda: sys.path.__setitem__(slice(None), saved))
        sys.path.insert(0, str(extended.ROOT / "tools"))
        er = importlib.import_module("extended_render")
        data, skin, sid = er.subject("z01", argparse.Namespace(line=None, finish=None))
        self.assertEqual((data["META"]["id"], skin, sid), ("ZERO-01", "standard", "ZA01"))
        data, skin, sid = er.subject("e01", argparse.Namespace(line=None, finish=None))   # Gegenprobe: EXTENDED unverändert
        self.assertEqual((data["META"]["id"], sid), ("EXTENDED-01", "EA01"))
        with self.assertRaises(SystemExit):
            er.subject("z01", argparse.Namespace(line="B", finish=None))


if __name__ == "__main__":
    unittest.main()
