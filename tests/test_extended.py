"""EXTENDED-01 „Spearhead“ (0.15): eigenständiges Modell im BALLON-Kit-Vokabular.

Prüft den Datensatz ohne Blender: Felder und IDs, Anker/Weltpunkte auf vorhandenen Teilen (BALLONs `variant.problems` als Orakel), Budgets
des Stilhandbuchs (Leuchtfunktionen, Akzent-Bedienfunktionen, eine Schrift, ein Grafikelement), Visierlinie 60–80 mm über der
Laufachse, Eigenständigkeit gegen BASIC-01 in der Seitensilhouette und Zusammenhang aller Teile. Gegenproben: BA01 gegen sich selbst,
ein abgelöstes Teil, ein überzähliges Leuchtteil.
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

IOU_MAX = 0.85        # Annahme wie BALLON A1: eigene Form, nicht nur eine Linie (Linien liegen bei ≥ 0,95)
SIGHT_RANGE = (60.0, 80.0)   # Vorgabe Visier-Standard: Visierlinie über der Laufachse


def lights(parts):
    return sorted(p["id"] for p in parts if p["mat"] == "energy")


def accent_functions(parts):
    """Akzent-Bedienfunktionen außerhalb des Visiers; beidseitige Hebel zählen einmal (Suffix _r)."""
    return sorted({p["id"].removesuffix("_r") for p in parts if p["mat"] == "accent" and p.get("move") and p["asm"] != "sight"})


@unittest.skipIf(SNAP is None, REASON)
class TestSpearhead(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = extended.load("e01", SNAP)
        cls.parts = cls.data["PARTS"]
        cls.ids = {p["id"]: p for p in cls.parts}
        cls.basic = extended.load_basic("01", SNAP)

    def test_fields_and_ids(self):
        for k in ("META", "PARTS", "ASSEMBLIES", "ANCHORS", "POINTS", "ACTIONS"):
            self.assertIn(k, self.data)
        self.assertEqual(self.data["META"]["id"], "EXTENDED-01")
        self.assertEqual(self.data["META"]["type"], "auto_rifle")
        self.assertEqual(len(self.ids), len(self.parts), "Teil-IDs doppelt")
        asms = {a["id"] for a in self.data["ASSEMBLIES"]}
        self.assertEqual(asms, {a["id"] for a in self.basic["ASSEMBLIES"]}, "Baugruppen wie die Familie")
        self.assertEqual({p["asm"] for p in self.parts} - asms, set())
        for p in self.parts:
            if p.get("parent_part"):
                self.assertIn(p["parent_part"], self.ids, p["id"])

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
        self.assertEqual(self.ids["grip"]["mat"], "rubber")
        self.assertEqual(self.ids["grip"]["iface"], "BGM-1")
        self.assertEqual(self.ids["mag_well"]["iface"], "BMW-R")
        self.assertEqual(self.ids["muzzle"]["iface"], "BMZ-15")
        self.assertEqual(self.ids["handguard"]["mat"], "graphite")
        self.assertIn(self.ids["upper"]["mat"], ("shell",))

    def test_budgets(self):
        self.assertLessEqual(len(lights(self.parts)), 3, lights(self.parts))
        self.assertLessEqual(len(accent_functions(self.parts)), 3, accent_functions(self.parts))
        self.assertEqual([p["id"] for p in self.parts if p["shape"] == "text"], ["text_r"])
        graphics = [p["id"] for p in self.parts if p["mat"] == "accent" and not p.get("move") and p["asm"] != "sight"]
        self.assertEqual(graphics, ["chevron"])

    def test_budget_counterprobe(self):
        extra = self.parts + [dict(self.ids["ammo_counter"], id="extra_glow")]
        self.assertGreater(len(lights(extra)), len(lights(self.parts)))
        self.assertEqual(len(lights(extra + [dict(self.ids["ammo_counter"], id="x2")])), 5)

    def test_lettering_on_receiver(self):
        """Die Schrift (linksbündig, rechts läuft sie nach vorn) liegt ganz auf der ebenen Gehäusefläche vor der Klingenfuge.

        Länge ≈ 0,62 × Größe je Zeichen (Annahme, Barlow/Blender-Standardschrift großzügig); r2 lag bei f 184 und lief in die Chevrons."""
        t = self.ids["text_r"]
        upper = self.ids["upper"]
        f_join = max(q[0] for q in upper["pts"])
        end = t["f"] + 0.62 * t["size"] * len(t["text"]) if t["side"] == -1 else t["f"]
        start = t["f"] if t["side"] == -1 else t["f"] - 0.62 * t["size"] * len(t["text"])
        self.assertLess(end, f_join - 5, "Schrift läuft über die Fuge Gehäuse/Klinge")
        self.assertGreater(start, min(q[0] for q in upper["pts"]))
        self.assertAlmostEqual(abs(t["x"]), upper["w"] / 2, delta=0.2)
        port = next(c for c in upper["cuts"] if c.get("x") == -upper["w"] / 2 and c.get("f0") == 28)
        self.assertGreater(start, port["f1"], "Schrift auf dem Auswurffenster")

    def test_sight_line(self):
        bore = self.ids["barrel"]["c"][0]
        eye = self.data["ANCHORS"]["Socket_Eye"]["at"][1]
        self.assertGreaterEqual(eye - bore, SIGHT_RANGE[0])
        self.assertLessEqual(eye - bore, SIGHT_RANGE[1])
        self.assertEqual(bore, 106)

    def test_own_silhouette(self):
        own = extended.side_iou(self.basic["PARTS"], self.parts)
        self.assertLess(own, IOU_MAX)
        self.assertGreaterEqual(extended.side_iou(self.basic["PARTS"], self.basic["PARTS"]), 0.99)   # Gegenprobe
        # Gegenprobe: eine Parameterlinie (BA01 ohne Mündung) bleibt über der Schwelle – das Maß trennt Linie und eigene Form
        trimmed = [p for p in self.basic["PARTS"] if p["id"] not in ("muzzle", "muzzle_crown")]
        self.assertGreater(extended.side_iou(self.basic["PARTS"], trimmed), IOU_MAX)

    def test_no_floating_parts(self):
        groups = extended.components(self.parts)
        self.assertEqual(len(groups), 1, groups[1:])
        moved = copy.deepcopy(self.parts)   # Gegenprobe: Kernrahmen 40 mm nach außen → eigene Gruppe
        frame = next(p for p in moved if p["id"] == "core_frame")
        frame["x"] += 40
        self.assertGreater(len(extended.components(moved)), 1)

    def test_proportions(self):
        f = [b for p in self.parts if (b := extended.bounds(p))]
        length = max(b[1][0] for b in f) - min(b[0][0] for b in f)
        self.assertAlmostEqual(length / 1000, self.data["META"]["reference_length_m"], delta=0.005)
        self.assertGreater(length, 850)
        self.assertLess(length, 950)

    def test_source_hash(self):
        a, b = extended.source("e01", SNAP), extended.source("e01", SNAP)
        self.assertEqual(a, b)
        self.assertIn("formgen/models/extended/e01_spearhead.py", a["files"])
        self.assertIn("basic/common.py", a["files"])
        self.assertNotIn("basic/pilot/w01_auto_rifle_v21.py", a["files"], "kein Umbau von BASIC-01")

    def test_snapshot_released(self):
        self.assertFalse(any(n == "basic" or n.startswith("basic.") for n in sys.modules))
        self.assertNotIn(str(SNAP), sys.path)


if __name__ == "__main__":
    unittest.main()
