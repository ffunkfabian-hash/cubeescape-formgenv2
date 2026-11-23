"""EXTENDED-10 „Bellmouth“ und EXTENDED-11 „Collimator“ (0.19 „Crucible“): eigenständige Fusionswaffen im BALLON-Kit-Vokabular.

Prüft die Datensätze ohne Blender: Felder und IDs, Weltpunkte (BALLONs `variant.problems` als Orakel), Familienschnittstellen, Budgets
des Stilhandbuchs (≤ 3 Leuchtfunktionen, genau ein Blickfang, ≤ 3 Akzent-Bedienfunktionen, eine Schrift, ein Grafikelement), Visierlinie,
Schrift auf ebener Fläche, Seiten-IoU < 0,85 gegen den eigenen BASIC-Typ und jedes vorhandene EXTENDED-Modell, die Gegensätze der beiden
Typen (gestreut/kurz gegen gebündelt/lang), Zusammenhang, Länge, Quellhash und den Rollen-Vorspann des Renderwerkzeugs. Jede Prüfung hat
eine Gegenprobe, die aus dem erwarteten Grund rot wird.
"""
import copy
import importlib
import sys
import unittest

from formgen import ballon, extended

try:
    SNAP = ballon.snapshot()
except ballon.BallonError as error:   # z. B. Cloud ohne BALLON-Checkout
    SNAP, REASON = None, str(error)
else:
    REASON = ""

IOU_MAX = 0.85                 # Annahme wie BALLON A1 und test_extended
SIGHT_RANGE = (60.0, 80.0)     # Vorgabe Visier-Standard
FRAME = dict(lo=(-460.0, -200.0), size=(1400, 520))   # A: Rahmen für Langwaffen (E11 bis f 800)
OWN = {"e10": ("10", "fusion_rifle", "EXTENDED-10", "EA10", "e10_bellmouth"),
       "e11": ("11", "linear_fusion_rifle", "EXTENDED-11", "EA11", "e11_collimator")}
LIGHT_MATS = ("energy", "charge_core")


def lights(parts):
    return sorted(p["id"] for p in parts if p["mat"] in LIGHT_MATS)


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


def flare(p):
    """Öffnungsverhältnis eines Kegels entlang f: > 1 öffnet nach vorn (Streuung), < 1 bündelt."""
    return p.get("r1", p["r"]) / p["r"]


def spacing_problems(fs):
    gaps = [b - a for a, b in zip(fs, fs[1:])]
    return [f"Abstand {g} nach {a} nicht kürzer" for a, g, h in zip(fs, gaps, gaps[1:]) if h >= g]


@unittest.skipIf(SNAP is None, REASON)
class TestFusionPair(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = {k: extended.load(k, SNAP) for k in OWN}
        cls.basic = {k: extended.load_basic(OWN[k][0], SNAP) for k in OWN}
        cls.others = {k: extended.load(k, SNAP)["PARTS"] for k in extended.MODELS if k not in OWN}
        cls.ids = {k: {p["id"]: p for p in d["PARTS"]} for k, d in cls.data.items()}

    def test_fields_and_ids(self):
        for k, (num, typ, wid, sid, mod) in OWN.items():
            with self.subTest(k):
                d, ids = self.data[k], self.ids[k]
                self.assertEqual(extended.MODELS[k], mod)
                self.assertEqual(d["META"]["id"], wid)
                self.assertEqual(d["META"]["type"], typ)
                self.assertEqual(d["META"]["type"], self.basic[k]["META"]["type"], "Typ wie BASIC-NN")
                self.assertEqual(len(ids), len(d["PARTS"]), "Teil-IDs doppelt")
                asms = {a["id"] for a in d["ASSEMBLIES"]}
                self.assertEqual(asms, {a["id"] for a in self.basic[k]["ASSEMBLIES"]}, "Baugruppen wie BASIC-NN")
                self.assertEqual({p["asm"] for p in d["PARTS"]} - asms, set())
                for p in d["PARTS"]:
                    if p.get("parent_part"):
                        self.assertIn(p["parent_part"], ids, p["id"])
                self.assertIsNone(d["EJECT"], "Energiewaffe ohne Hülsenauswurf")

    def test_sheet_ids(self):
        import re
        for k, (_, _, _, sid, _) in OWN.items():
            self.assertEqual(extended.sheet_id(k), sid)
            self.assertEqual(self.data[k]["META"]["sheet_id"], sid)
            self.assertRegex(sid, f"^{extended.SHEET_PATTERN}$")
        sids = list(extended.SHEETS.values())
        self.assertEqual(len(set(sids)), len(sids), "Blatt-IDs doppelt")
        self.assertIsNone(re.match(f"^{extended.SHEET_PATTERN}$", "EA100"))   # Gegenprobe: dreistellig ist kein Blatt

    def test_anchors_points_actions(self):
        sys.path.insert(0, str(SNAP))
        try:
            variant = importlib.import_module("basic.variant")
            for k, d in self.data.items():
                with self.subTest(k):
                    A, ids = d["ANCHORS"], self.ids[k]
                    self.assertEqual(set(A) - set(self.basic[k]["ANCHORS"]), set(), "Anker wie BASIC-NN")
                    self.assertEqual(set(self.basic[k]["ANCHORS"]) - set(A), set())
                    for name, a in A.items():
                        self.assertIn(a["part"], ids, name)
                    self.assertEqual(tuple(A["Socket_Hand"]["at"]), (0, 0, 0))
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
        for k, ids in self.ids.items():
            with self.subTest(k):
                self.assertEqual(ids["grip"]["iface"], "BGM-1")
                self.assertEqual(ids["grip"]["mat"], "rubber")
                self.assertEqual(ids["energy_cell"]["iface"], "BEC-1")
                self.assertEqual(ids["cell_lip"]["iface"], "BEC-1")
                self.assertIn("BMZ-15", {p.get("iface") for p in ids.values()})

    def test_budgets(self):
        for k, d in self.data.items():
            with self.subTest(k):
                P = d["PARTS"]
                self.assertLessEqual(len(lights(P)), 3, lights(P))
                self.assertEqual(len([p for p in P if p["mat"] == "charge_core"]), 1, "genau ein Blickfang (Ladekern)")
                self.assertLessEqual(len(accent_functions(P)), 3, accent_functions(P))
                self.assertEqual([p["id"] for p in P if p["shape"] == "text"], ["text_r"])
                self.assertEqual(len(graphics(P)), 1, graphics(P))
        core = next(p for p in self.data["e10"]["PARTS"] if p["mat"] == "charge_core")   # Gegenprobe: zweiter Ladekern
        two = self.data["e10"]["PARTS"] + [dict(core, id="core2")]
        self.assertEqual(len([p for p in two if p["mat"] == "charge_core"]), 2)
        self.assertGreater(len(lights(two + [dict(core, id="core3")])), 3)

    def test_sight_line(self):
        for k, d in self.data.items():
            with self.subTest(k):
                bore = d["ANCHORS"]["Socket_Muzzle"]["at"][1]
                eye = d["ANCHORS"]["Socket_Eye"]["at"][1]
                self.assertGreaterEqual(eye - bore, SIGHT_RANGE[0])
                self.assertLessEqual(eye - bore, SIGHT_RANGE[1])

    def test_lettering_on_flat_face(self):
        """E10: rechts auf dem Unteren Gehäuse vor dem Zellentrichter; E11: rechts auf dem Gehäuse zwischen Paneelmulde und Grundplatte."""
        t10, t11 = self.ids["e10"]["text_r"], self.ids["e11"]["text_r"]
        lower = self.ids["e10"]["lower"]
        a, b = text_span(t10)
        self.assertGreater(a, min(q[0] for q in lower["pts"]) + 5)                       # nicht über die Gehäusekante hinten
        self.assertLess(b, 86 - 14)                                                     # vor dem Zellentrichter (CELL f 86)
        self.assertAlmostEqual(abs(t10["x"]), lower["w"] / 2, delta=0.2)
        rec = self.ids["e11"]["receiver"]
        mulde = max(c["f1"] for c in rec["cuts"] if c.get("shape") == "box")
        a, b = text_span(t11)
        self.assertGreater(a, mulde)
        self.assertLess(b, rec["f1"] - 5)                                                # vor der Grundplatte
        self.assertAlmostEqual(abs(t11["x"]), max(x for x, _ in rec["pts"]), delta=0.2)
        a, b = text_span(dict(t10, f=50))                                                 # Gegenprobe: läuft in den Trichter
        self.assertGreaterEqual(b, 86 - 14)

    def test_own_silhouette(self):
        """Seiten-IoU < 0,85 gegen den eigenen BASIC-Typ, gegen jedes andere EXTENDED-Modell und gegeneinander."""
        for k, d in self.data.items():
            with self.subTest(k):
                self.assertLess(extended.side_iou(self.basic[k]["PARTS"], d["PARTS"], **FRAME), IOU_MAX)
                for o, parts in self.others.items():
                    self.assertLess(extended.side_iou(parts, d["PARTS"], **FRAME), IOU_MAX, o)
        self.assertLess(extended.side_iou(self.data["e10"]["PARTS"], self.data["e11"]["PARTS"], **FRAME), IOU_MAX)
        b11 = self.basic["e11"]["PARTS"]   # Gegenproben: gleiche Form 1,0; eine Parameterlinie bleibt über der Schwelle
        self.assertGreaterEqual(extended.side_iou(b11, b11, **FRAME), 0.99)
        trimmed = [p for p in b11 if p["id"] not in ("muzzle", "muzzle_crown")]
        self.assertGreater(extended.side_iou(b11, trimmed, **FRAME), IOU_MAX)
        with self.assertRaisesRegex(ValueError, "beschnitten"):   # Gegenprobe: E11 passt nicht in den Standardrahmen (bis f 780)
            extended.side_mask(self.data["e11"]["PARTS"])

    def test_scatter_versus_focus(self):
        """Die Typen setzen sich ab: E10 kurz mit sich öffnendem Trichter, E11 lang mit bündelndem Kegel und enger werdendem Plattentakt."""
        l10, l11 = length(self.data["e10"]["PARTS"]), length(self.data["e11"]["PARTS"])
        self.assertLess(l10, 650)
        self.assertGreater(l11, 1050)
        self.assertLess(l10, length(self.basic["e10"]["PARTS"]), "E10 kompakter als BASIC-10")
        self.assertGreater(l11, length(self.basic["e11"]["PARTS"]), "E11 länger als BASIC-11")
        self.assertGreater(flare(self.ids["e10"]["bell"]), 1.4, "Glocke öffnet nach vorn")
        self.assertLess(flare(self.ids["e11"]["muzzle"]), 0.7, "Fokuskegel bündelt")
        self.assertGreater(flare(dict(self.ids["e11"]["muzzle"], r1=20)), 1.0)            # Gegenprobe: umgedrehter Kegel streut
        plates = sorted(i["f0"] for i in self.ids["e11"]["plates"]["items"])
        fs = [self.ids["e11"]["base_plate"]["f0"]] + plates + [self.ids["e11"]["front_plate"]["f0"]]
        self.assertEqual(spacing_problems(fs), [], fs)
        self.assertTrue(spacing_problems([200, 300, 400, 500]))                           # Gegenprobe: gleicher Takt

    def test_cage_shows_core(self):
        """E11: in der Seitenansicht liegt der Kern frei zwischen den Stäben (mindestens 6 mm Luft je Seite)."""
        core = self.ids["e11"]["linear_core"]
        rods = self.ids["e11"]["rods"]["items"]

        def gap(rods):
            us = sorted({r["c"][0] for r in rods})
            return min(abs(u - core["c"][0]) - r["r"] - core["r"] for u in us for r in rods if r["c"][0] == u)
        self.assertGreaterEqual(gap(rods), 6.0)
        self.assertLess(gap([dict(r, c=(core["c"][0] + (6 if r["c"][0] > core["c"][0] else -6), r["c"][1])) for r in rods]), 6.0)

    def test_no_floating_parts(self):
        for k, d in self.data.items():
            with self.subTest(k):
                groups = extended.components(d["PARTS"])
                self.assertEqual(len(groups), 1, groups[1:])
        moved = copy.deepcopy(self.data["e10"]["PARTS"])   # Gegenprobe: Glocke 60 mm nach vorn → eigene Gruppe
        for p in moved:
            if p["id"] in ("bell", "bell_lip"):
                p["a0"] += 60
                p["a1"] += 60
        self.assertGreater(len(extended.components(moved)), 1)

    def test_proportions(self):
        for k, d in self.data.items():
            with self.subTest(k):
                self.assertAlmostEqual(length(d["PARTS"]) / 1000, d["META"]["reference_length_m"], delta=0.005)

    def test_source_hash(self):
        for k, (num, _, _, _, mod) in OWN.items():
            with self.subTest(k):
                a = extended.source(k, SNAP)
                self.assertEqual(a, extended.source(k, SNAP))
                self.assertIn(f"formgen/models/extended/{mod}.py", a["files"])
                self.assertIn("basic/pilot/energy_roles.py", a["files"])
                self.assertFalse([f for f in a["files"] if f.startswith(f"basic/pilot/w{num}_") or f.startswith(f"basic/weapons/w{num}_")],
                                 "kein Umbau von BASIC-NN")

    def test_snapshot_released(self):
        self.assertFalse(any(n == "basic" or n.startswith("basic.") for n in sys.modules))
        self.assertNotIn(str(SNAP), sys.path)


@unittest.skipIf(SNAP is None, REASON)
class TestRenderRoles(unittest.TestCase):
    """`tools/extended_render.py` registriert BALLONs Leuchtrollen nur für Datensätze, die sie nutzen; e01 behält Wrapper und Stempel."""

    def setUp(self):
        saved = list(sys.path)
        self.addCleanup(lambda: sys.path.__setitem__(slice(None), saved))
        sys.path.insert(0, str(extended.ROOT / "tools"))
        self.er = importlib.import_module("extended_render")

    def test_wrapper(self):
        e01 = extended.load("e01", SNAP)
        self.assertEqual(self.er.wrapper(e01), self.er.WRAPPER)
        for k in OWN:
            w = self.er.wrapper(extended.load(k, SNAP))
            self.assertIn("import basic.pilot.energy_roles\nimport tools.blender_build as BB", w)
            self.assertLess(w.index("sys.path.insert(0, job['snapshot'])"), w.index("energy_roles"))   # Snapshot steht schon auf dem Pfad
        marked = copy.deepcopy(e01)   # Gegenprobe: ein Ladekern im Gewehr verlangt die Rollen
        marked["PARTS"][0]["mat"] = "charge_core"
        self.assertNotEqual(self.er.wrapper(marked), self.er.WRAPPER)


if __name__ == "__main__":
    unittest.main()
