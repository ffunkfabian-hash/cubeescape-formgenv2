"""EXTENDED-04 „Sledge“ und EXTENDED-05 „Duplex“ (0.18 „Holster“): Handkanone und Seitenwaffe als eigene Modelle.

Prüft die Datensätze ohne Blender, je Modell: Felder und IDs, Blatt-ID, Anker/Weltpunkte (BALLONs `variant.problems` als Orakel),
Budgets des Stilhandbuchs (genau ein Blickfang außerhalb des Visiers, ≤ 3 Leuchtfunktionen, ≤ 3 Akzent-Bedienfunktionen, eine Schrift,
ein Grafikelement), freie Visierlinie, Schrift auf ebener Fläche, Eigenständigkeit in der Seitensilhouette gegen den eigenen BASIC-Typ
und jedes EXTENDED-Modell gleicher Größenklasse, Zusammenhang aller Teile, Länge, Quellhash ohne BASIC-Piloten und die Leitmotive
(Hammerkopf mit offener Kehle, Doppeldeck mit freiem Schlitz). Zu jeder Schranke eine Gegenprobe, die aus dem erwarteten Grund anschlägt.
"""
import copy
import importlib
import math
import re
import sys
import unittest

from formgen import ballon, extended

try:
    SNAP = ballon.snapshot()
except ballon.BallonError as error:   # z. B. Cloud ohne BALLON-Checkout
    SNAP, REASON = None, str(error)
else:
    REASON = ""

IOU_MAX = 0.85          # Annahme wie BALLON A1 und tests/test_extended.py: eigene Form, keine Linie
PAIR_MAX = 0.70         # Annahme 0.18: Handkanone und Seitenwaffe derselben Sitzung setzen sich deutlich ab
HANDGUN_M = 0.40        # Annahme: Größenklasse Faustwaffe bis 0,40 m Länge
LINE_RANGE = (30.0, 50.0)   # Annahme 0.18: Visierlinie über der Laufachse bei Kimme/Korn (BASIC-04 32, BASIC-05 29; tiefe Achse E05)
MODELS = {"e04": dict(num="04", type="hand_cannon", file="e04_sledge.py", text_on="neck"),
          "e05": dict(num="05", type="sidearm", file="e05_duplex.py", text_on="slide")}


def lights(parts):
    return sorted(p["id"] for p in parts if p["mat"] == "energy")


def accent_functions(parts):
    return sorted({p["id"].removesuffix("_r") for p in parts if p["mat"] == "accent" and p.get("move") and p["asm"] != "sight"})


def length(parts):
    b = [x for p in parts if (x := extended.bounds(p))]
    return max(q[1][0] for q in b) - min(q[0][0] for q in b)


def occupants(parts, f0, f1, u0, u1, skip=()):
    """Teile, deren Seitensilhouette den Raum f0..f1 × u0..u1 trifft (quer ganz offen) – für freie Zonen (Kehle, Schlitz, Visierlinie).
    Raster wie `extended.side_mask` (1 mm je Pixel ab (−420, −200), Bildzeile 0 oben)."""
    lo, rows = (-420, -200), 520
    r0, r1 = math.ceil(rows - 1 - (u1 - lo[1])), math.floor(rows - 1 - (u0 - lo[1]))   # nur Pixel ganz im Raum
    c0, c1 = math.ceil(f0 - lo[0]), math.floor(f1 - lo[0])
    out = []
    for p in parts:
        if p["id"] not in skip and extended.bounds(p) and extended.side_mask([p])[r0:r1 + 1, c0:c1 + 1].any():
            out.append(p["id"])
    return sorted(out)


def lettering_problems(t, face, f_free, half):
    """Schrift (linksbündig; rechts läuft sie nach vorn) liegt ganz auf der Seitenfläche `face` (halbe Breite `half` an dieser Stelle) im
    freien Bereich f_free und in der Höhe des Teils. Länge ≈ 0,62 × Größe je Zeichen (Annahme wie tests/test_extended.py), Höhe ≈ 0,75 × Größe."""
    n = 0.62 * t["size"] * len(t["text"])
    start, end = (t["f"], t["f"] + n) if t["side"] == -1 else (t["f"] - n, t["f"])
    (lo, hi) = extended.bounds(face)[0], extended.bounds(face)[1]
    out = []
    if start < f_free[0] or end > f_free[1]:
        out.append("außerhalb der freien Fläche")
    if t["u"] < lo[1] + 1 or t["u"] + 0.75 * t["size"] > hi[1] - 1:
        out.append("außerhalb der Höhe")
    if abs(abs(t["x"]) - half) > 0.2:
        out.append("nicht auf der Seitenfläche")
    return out


@unittest.skipIf(SNAP is None, REASON)
class TestHandguns(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = {k: extended.load(k, SNAP) for k in MODELS}
        cls.basic = {k: extended.load_basic(m["num"], SNAP) for k, m in MODELS.items()}
        cls.others = {k: extended.load(k, SNAP) for k in extended.MODELS if k not in MODELS}

    def parts(self, key):
        return self.data[key]["PARTS"]

    def ids(self, key):
        return {p["id"]: p for p in self.parts(key)}

    def test_fields_and_ids(self):
        for key, m in MODELS.items():
            with self.subTest(key):
                d = self.data[key]
                for k in ("META", "PARTS", "ASSEMBLIES", "ANCHORS", "POINTS", "ACTIONS", "EJECT", "EGO_GRIPS", "HERO"):
                    self.assertIn(k, d)
                self.assertEqual(d["META"]["id"], f"EXTENDED-{m['num']}")
                self.assertEqual(d["META"]["type"], m["type"])
                self.assertEqual(d["META"]["type"], self.basic[key]["META"]["type"], "Typ wie BASIC-NN")
                self.assertEqual(len(self.ids(key)), len(self.parts(key)), "Teil-IDs doppelt")
                asms = {a["id"] for a in d["ASSEMBLIES"]}
                self.assertEqual(asms, {a["id"] for a in self.basic[key]["ASSEMBLIES"]}, "Baugruppen wie BASIC-NN")
                self.assertEqual({p["asm"] for p in self.parts(key)} - asms, set())
                for p in self.parts(key):
                    if p.get("parent_part"):
                        self.assertIn(p["parent_part"], self.ids(key), p["id"])

    def test_sheet_ids(self):
        """EA04/EA05 nach dem Schema E<Linie><NN> (Nutzerentscheid 23.11.2026): Register = META, NN = EXTENDED-Nummer."""
        for key, m in MODELS.items():
            sid = extended.sheet_id(key)
            self.assertEqual(sid, f"EA{m['num']}")
            self.assertEqual(self.data[key]["META"]["sheet_id"], sid)
            self.assertRegex(sid, f"^{extended.SHEET_PATTERN}$")
            self.assertEqual(extended.MODELS[key], m["file"].removesuffix(".py"))
        self.assertEqual(len(set(extended.SHEETS.values())), len(extended.SHEETS), "Blatt-IDs doppelt")

    def test_anchors_points_actions(self):
        for key in MODELS:
            with self.subTest(key):
                A, ids = self.data[key]["ANCHORS"], self.ids(key)
                for name in ("Socket_Hand", "Socket_SupportHand", "Socket_Muzzle", "Socket_MagWell", "Socket_Sight", "Socket_Eye"):
                    self.assertIn(name, A)
                    self.assertIn(A[name]["part"], ids, name)
                self.assertEqual(tuple(A["Socket_Hand"]["at"]), (0, 0, 0))
                for k, v in self.data[key]["ACTIONS"].items():
                    for pid in v["keys"]:
                        self.assertIn("move", ids[pid], f"{k}: {pid} ohne Bewegung")
                sys.path.insert(0, str(SNAP))
                try:
                    variant = importlib.import_module("basic.variant")
                    self.assertEqual(variant.problems(variant.as_module(copy.deepcopy(self.data[key]))), [])
                    broken = copy.deepcopy(self.data[key])   # Gegenprobe: Weltpunkt auf ein fehlendes Teil
                    broken["POINTS"]["grip.grip"]["part"] = "kein_teil"
                    self.assertTrue(any("kein_teil" in s for s in variant.problems(variant.as_module(broken))))
                finally:
                    sys.path.remove(str(SNAP))
                    extended._purge()

    def test_family_interfaces(self):
        for key in MODELS:
            ids = self.ids(key)
            self.assertEqual(ids["grip"]["mat"], "rubber")
            self.assertEqual(ids["grip"]["iface"], "BGM-1")
            for pid in ("sight_rear", "sight_front", "sight_status", "sight_glass"):   # Kimme/Korn K1 „Klammer“
                self.assertIn(pid, ids)
        self.assertEqual(self.ids("e04")["cylinder"]["mat"], "dark_metal")      # Revolver: Trommel
        self.assertEqual(self.ids("e05")["slide"]["move"]["kind"], "translate")  # Schlittenpistole
        self.assertTrue(self.ids("e05")["magazine"]["move"].get("removable"))

    def test_budgets(self):
        for key in MODELS:
            with self.subTest(key):
                parts = self.parts(key)
                self.assertLessEqual(len(lights(parts)), 3, lights(parts))
                focal = [p["id"] for p in parts if p["mat"] == "energy" and p["asm"] != "sight"]
                self.assertEqual(len(focal), 1, f"genau ein Blickfang außerhalb des Visiers: {focal}")
                self.assertLessEqual(len(accent_functions(parts)), 3, accent_functions(parts))
                self.assertEqual([p["id"] for p in parts if p["shape"] == "text"], ["text_r"])
                graphics = [p["id"] for p in parts if p["mat"] == "accent" and not p.get("move") and p["asm"] != "sight"]
                self.assertEqual(graphics, ["chevron"])
        extra = self.parts("e04") + [dict(self.ids("e04")["eye_glow"], id="zweites_auge")]   # Gegenprobe: zweiter Blickfang
        self.assertEqual(len([p for p in extra if p["mat"] == "energy" and p["asm"] != "sight"]), 2)
        self.assertGreater(len(lights(extra)), 3)

    def test_sight_line(self):
        """Visierlinie (Kimme/Korn, Linie Träger + 11 mm) frei: zwischen Kimme und Korn ragt kein Teil über die Linie."""
        for key in MODELS:
            with self.subTest(key):
                A, ids = self.data[key]["ANCHORS"], self.ids(key)
                bore = A["Socket_Muzzle"]["at"][1]
                line = A["Socket_Eye"]["at"][1]
                self.assertEqual(line, A["Socket_Sight"]["at"][1])
                self.assertGreaterEqual(line - bore, LINE_RANGE[0])
                self.assertLessEqual(line - bore, LINE_RANGE[1])
                rear, front = extended.bounds(ids["sight_rear"]), extended.bounds(ids["sight_front"])
                sight = {p["id"] for p in self.parts(key) if p["asm"] == "sight"}
                self.assertEqual(occupants(self.parts(key), rear[1][0], front[0][0], line - 2, line + 30, sight), [])
        # Gegenprobe: ein Kopf, der bis über die Linie ragt, wird gefunden
        head = copy.deepcopy(self.ids("e04")["head"])
        head["pts"] = [(f, u + 14 if u > 90 else u) for f, u in head["pts"]]
        line = self.data["e04"]["ANCHORS"]["Socket_Eye"]["at"][1]
        self.assertEqual(occupants([head], 100, 230, line - 2, line + 30), ["head"])

    def test_lettering(self):
        e04, e05 = self.ids("e04"), self.ids("e05")
        cases = {"e04": (e04["neck"], (e04["frame"]["pts"][3][0] + 2, e04["head"]["pts"][0][0] - 2), e04["neck"]["w"] / 2),   # Bug bis Kopf
                 "e05": (e05["slide"], (60 + 2, min(i["pts"][0][0] for i in e05["chevron"]["items"]) - 2),            # Block bis Chevrons
                         e05["slide"]["w"] / 2 - 2)}                                                    # Oberdeck je Seite 2 mm eingezogen
        for key, case in cases.items():
            with self.subTest(key):
                self.assertEqual(lettering_problems(self.ids(key)["text_r"], *case), [])
        self.assertIn("außerhalb der freien Fläche", lettering_problems(dict(e04["text_r"], f=170), *cases["e04"]))   # in den Kopf
        self.assertIn("außerhalb der freien Fläche", lettering_problems(dict(e05["text_r"], f=120), *cases["e05"]))   # in die Chevrons
        self.assertIn("außerhalb der Höhe", lettering_problems(dict(e04["text_r"], u=84), *cases["e04"]))

    def test_own_silhouette(self):
        """Seiten-IoU < 0,85 gegen den eigenen BASIC-Typ und jedes EXTENDED-Modell gleicher Größenklasse; das Paar setzt sich ab."""
        for key, m in MODELS.items():
            with self.subTest(key):
                self.assertLess(extended.side_iou(self.basic[key]["PARTS"], self.parts(key)), IOU_MAX)
                for other, d in {**self.others, **{k: v for k, v in self.data.items() if k != key}}.items():
                    if length(d["PARTS"]) / 1000 <= HANDGUN_M:
                        self.assertLess(extended.side_iou(d["PARTS"], self.parts(key)), IOU_MAX, other)
        self.assertLess(extended.side_iou(self.parts("e04"), self.parts("e05")), PAIR_MAX)
        # Gegenproben: BASIC-04 gegen sich selbst 1,0; BASIC-04 ohne Visier bleibt über der Schwelle (Linie, keine eigene Form)
        b04 = self.basic["e04"]["PARTS"]
        self.assertGreaterEqual(extended.side_iou(b04, b04), 0.99)
        self.assertGreater(extended.side_iou(b04, [p for p in b04 if p["asm"] != "sight"]), IOU_MAX)
        self.assertGreater(extended.side_iou(self.parts("e04"), self.parts("e04")[:-3]), PAIR_MAX)   # Paarschranke trennt

    def test_leitmotiv_sledge(self):
        """Hammerkopf: Kopf breiter als Brücke und Hals (Draufsicht), höher als der Hals; offene Kehle unter dem Hals."""
        ids = self.ids("e04")
        w = {k: ids[k]["w"] for k in ("head", "strap", "neck")}
        self.assertGreater(w["head"], w["strap"])
        self.assertGreater(w["strap"], w["neck"])
        head, neck = extended.bounds(ids["head"]), extended.bounds(ids["neck"])
        self.assertGreater((head[1][1] - head[0][1]) / (neck[1][1] - neck[0][1]), 2.0)
        throat = (ids["frame"]["pts"][3][0] + 1, ids["head"]["pts"][0][0] - 1, 34.0, neck[0][1] - 1)   # Bug oben bis Kopf oben
        self.assertEqual(occupants(self.parts("e04"), *throat), [])
        self.assertGreater(throat[1] - throat[0], 50)
        plug = dict(ids["neck"], id="unterlauf", pts=[(110, 40), (180, 40), (180, 58), (110, 58)])   # Gegenprobe: Unterlauf füllt sie
        self.assertEqual(occupants(self.parts("e04") + [plug], *throat), ["unterlauf"])

    def test_leitmotiv_duplex(self):
        """Doppeldeck: zwischen Laufrohr und Schlitten bleibt vorn ein freier Schlitz ≥ 5 mm hinter der Laufbuchse bis zur Stirn."""
        ids = self.ids("e05")
        tube, slide_u = extended.bounds(ids["tube"]), min(u for f, u in ids["slide"]["pts"] if f > 60)
        slot = (ids["bushing"]["a1"] + 1, ids["slide"]["pts"][5][0] - 4, tube[1][1] + 0.5, slide_u - 0.5)
        self.assertGreaterEqual(slide_u - tube[1][1], 5.0)
        self.assertEqual(occupants(self.parts("e05"), *slot, skip=("barrel", "muzzle_crown")), [])
        self.assertGreater(slot[1] - slot[0], 55)
        self.assertLess(extended.bounds(ids["tube"])[0][1], extended.bounds(ids["frame"])[1][1], "Rohr sitzt im Rahmen")
        plug = dict(ids["barrel_hood"], id="steg", f0=100, f1=110, u0=40, u1=62)   # Gegenprobe: ein Steg schließt den Schlitz
        self.assertEqual(occupants(self.parts("e05") + [plug], *slot, skip=("barrel", "muzzle_crown")), ["steg"])

    def test_no_floating_parts(self):
        for key, moved_id in (("e04", "eye_ring"), ("e05", "bushing")):
            with self.subTest(key):
                groups = extended.components(self.parts(key))
                self.assertEqual(len(groups), 1, groups[1:])
                moved = copy.deepcopy(self.parts(key))   # Gegenprobe: ein Teil 40 mm nach außen → eigene Gruppe
                part = next(p for p in moved if p["id"] == moved_id)
                for q in part.get("items") or [part]:   # Querrichtung x: Achse x über a0/a1, Achse f über c = (u, x)
                    if q["axis"] == "x":
                        q["a0"], q["a1"] = q["a0"] + 40, q["a1"] + 40
                    else:
                        q["c"] = (q["c"][0], q["c"][1] + 40)
                self.assertGreater(len(extended.components(moved)), 1)

    def test_proportions(self):
        """Länge = META; Handkanone deutlich länger und schwerer als die Seitenwaffe (Kontrast des Paars)."""
        lens = {k: length(self.parts(k)) for k in MODELS}
        for key in MODELS:
            self.assertAlmostEqual(lens[key] / 1000, self.data[key]["META"]["reference_length_m"], delta=0.005)
            self.assertLess(lens[key] / 1000, HANDGUN_M)
        self.assertGreater(lens["e04"] - lens["e05"], 60)
        self.assertLess(lens["e05"], length(self.basic["e05"]["PARTS"]), "Seitenwaffe kompakter als BASIC-05")

    def test_source_hash(self):
        for key, m in MODELS.items():
            a, b = extended.source(key, SNAP), extended.source(key, SNAP)
            self.assertEqual(a, b)
            self.assertIn(f"formgen/models/extended/{m['file']}", a["files"])
            self.assertIn("basic/common.py", a["files"])
            self.assertFalse([f for f in a["files"] if re.match(rf"basic/(pilot|weapons)/w{m['num']}_", f)], "kein Umbau von BASIC-NN")

    def test_snapshot_released(self):
        self.assertFalse(any(n == "basic" or n.startswith("basic.") for n in sys.modules))
        self.assertNotIn(str(SNAP), sys.path)


if __name__ == "__main__":
    unittest.main()
