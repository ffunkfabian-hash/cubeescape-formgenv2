"""EXTENDED-02 „Cadence“ und EXTENDED-03 „Meridian“ (0.17 „Outrider“): eigenständige Gewehre im BALLON-Kit-Vokabular.

Prüft die Datensätze ohne Blender, je mit Gegenprobe: Felder, IDs und Blatt-IDs, Funktion des eigenen BASIC-Typs (Feuerart, Baugruppen,
Schnittstellen), Weltpunkte mit `basic.variant.problems` als Orakel, Budgets (Leuchtfunktionen, Akzent-Bedienfunktionen, eine Schrift,
ein Grafikelement), Visierlinie, Seiten-IoU < 0,85 gegen den eigenen BASIC-Typ und gegen jedes vorhandene EXTENDED-Modell der
Langwaffenklasse, Zusammenhang, Lage der Schrift, die Leitmerkmale (02: eine Neigung für Kolben, Stirn, Schlitze, Fuge und Magazin;
03: alle Rohrteile auf der Laufachse) und das Vergleichsrendern mit `--basic` (Blender wird nie gestartet).
"""
import argparse
import copy
import importlib
import json
import math
from pathlib import Path
import sys
import unittest

from formgen import ballon, extended

try:
    SNAP = ballon.snapshot()
except ballon.BallonError as error:   # z. B. Cloud ohne BALLON-Checkout
    SNAP, REASON = None, str(error)
else:
    REASON = ""

IOU_MAX = 0.85               # Annahme wie BALLON A1 und tests/test_extended.py: eigene Form, nicht nur eine Linie
PAIR_MAX = 0.70              # Annahme 0.17: die beiden Gewehre dieser Sitzung setzen sich deutlich voneinander ab
SIGHT_RANGE = (60.0, 80.0)   # Vorgabe Visier-Standard: Visierlinie über der Laufachse
LONG_M = 0.6                 # Annahme: Langwaffenklasse (Vergleich der Seiten-IoU) ab 0,6 m Bezugslänge
CHAR = 0.62                  # Annahme wie tests/test_extended.py: Zeichenbreite ≈ 0,62 × Schriftgröße (großzügig)


def light_functions(parts):
    """Leuchtfunktionen: Teile aus `energy`; die Salvenanzeigen burst_1 … burst_3 sind eine Funktion."""
    return sorted({"burst" if p["id"].startswith("burst_") else p["id"] for p in parts if p["mat"] == "energy"})


def accent_functions(parts):
    """Akzent-Bedienfunktionen außerhalb des Visiers; beidseitige Hebel zählen einmal (Suffix _r)."""
    return sorted({p["id"].removesuffix("_r") for p in parts if p["mat"] == "accent" and p.get("move") and p["asm"] != "sight"})


def graphics(parts):
    return [p["id"] for p in parts if p["mat"] == "accent" and not p.get("move") and p["asm"] != "sight"]


def text_span(t):
    """f-Bereich der Schrift: linksbündig, rechts (side −1) läuft sie nach vorn, links nach hinten."""
    length = CHAR * t["size"] * len(t["text"])
    return (t["f"], t["f"] + length) if t["side"] == -1 else (t["f"] - length, t["f"])


def angle(p0, p1):
    """Neigung einer Kante gegen die Senkrechte in Grad (positiv = oben weiter vorn)."""
    return math.degrees(math.atan2(p1[0] - p0[0], p1[1] - p0[1]))


def pair_iou(a, b, margin=20.0):
    """Seiten-IoU mit einem Rahmen aus den Hüllen beider Teillisten (1 mm je Pixel, gemeinsamer Ursprung Socket_Hand).

    Der Standardrahmen von `extended.side_mask` (f −420 … 780, u −200 … 320) beschneidet längere Modelle wie Schwert und Glefe
    (EXTENDED-16/17) mit `ValueError`; je Paar gemessen bleibt der Vergleich mit jedem EXTENDED-Modell möglich (Koordination 0.17)."""
    boxes = [x for p in list(a) + list(b) if (x := extended.bounds(p))]
    f0, u0 = min(q[0][0] for q in boxes) - margin, min(q[0][1] for q in boxes) - margin
    f1, u1 = max(q[1][0] for q in boxes) + margin, max(q[1][1] for q in boxes) + margin
    frame = dict(lo=(math.floor(f0), math.floor(u0)), size=(math.ceil(f1 - f0) + 1, math.ceil(u1 - u0) + 1))
    ma, mb = extended.side_mask(a, **frame), extended.side_mask(b, **frame)
    return round(float((ma & mb).sum() / (ma | mb).sum()), 4)


def length(parts):
    b = [x for p in parts if (x := extended.bounds(p))]
    return max(q[1][0] for q in b) - min(q[0][0] for q in b)


class Common:
    """Gemeinsame Prüfungen; KEY und NUM setzen die Unterklassen."""
    KEY = NUM = None

    @classmethod
    def setUpClass(cls):
        cls.data = extended.load(cls.KEY, SNAP)
        cls.parts = cls.data["PARTS"]
        cls.ids = {p["id"]: p for p in cls.parts}
        cls.basic = extended.load_basic(cls.NUM, SNAP)

    def test_fields_and_ids(self):
        for k in ("META", "PARTS", "ASSEMBLIES", "ANCHORS", "POINTS", "ACTIONS", "EJECT", "EGO_GRIPS", "HERO"):
            self.assertIn(k, self.data)
        meta = self.data["META"]
        self.assertEqual(meta["id"], f"EXTENDED-{self.NUM}")
        self.assertEqual(meta["type"], self.basic["META"]["type"], "Typ wie BASIC-NN")
        self.assertEqual(meta["sheet_id"], f"EA{self.NUM}")
        self.assertEqual(extended.sheet_id(self.KEY), meta["sheet_id"])
        self.assertEqual(len(self.ids), len(self.parts), "Teil-IDs doppelt")
        asms = {a["id"] for a in self.data["ASSEMBLIES"]}
        self.assertEqual(asms, {a["id"] for a in self.basic["ASSEMBLIES"]}, "Baugruppen wie BASIC-NN")
        self.assertEqual({p["asm"] for p in self.parts} - asms, set())
        for p in self.parts:
            if p.get("parent_part"):
                self.assertIn(p["parent_part"], self.ids, p["id"])

    def test_function_of_type(self):
        """Funktionsprinzip bleibt: dieselben Aktionen wie der BASIC-Pilot (Feuerart, Nachladen), Abzug und Magazin bewegen sich."""
        self.assertEqual(set(self.data["ACTIONS"]), set(self.basic["ACTIONS"]))
        for k, v in self.data["ACTIONS"].items():
            for pid in v["keys"]:
                self.assertIn("move", self.ids[pid], f"{k}: {pid} ohne Bewegung")
        fire = next(k for k in self.data["ACTIONS"] if k.startswith("fire"))
        shots = [e for e in self.data["ACTIONS"][fire]["events"] if e[1] == "shot"]
        self.assertEqual(len(shots), len([e for e in self.basic["ACTIONS"][fire]["events"] if e[1] == "shot"]))

    def test_anchors_and_points(self):
        A = self.data["ANCHORS"]
        for name in ("Socket_Hand", "Socket_SupportHand", "Socket_Muzzle", "Socket_MagWell", "Socket_Charge", "Socket_Eye"):
            self.assertIn(name, A)
            self.assertIn(A[name]["part"], self.ids, name)
        self.assertEqual(tuple(A["Socket_Hand"]["at"]), (0, 0, 0))
        sys.path.insert(0, str(SNAP))
        try:
            variant = importlib.import_module("basic.variant")
            self.assertEqual(variant.problems(variant.as_module(copy.deepcopy(self.data))), [])
            bad = copy.deepcopy(self.data)   # Gegenprobe: ein Weltpunkt auf einem fehlenden Teil
            next(iter(bad["POINTS"].values()))["part"] = "gibt_es_nicht"
            self.assertTrue(any("fehlt" in m for m in variant.problems(variant.as_module(bad))))
        finally:
            sys.path.remove(str(SNAP))
            extended._purge()

    def test_family_interfaces(self):
        self.assertEqual(self.ids["grip"]["iface"], "BGM-1")
        self.assertEqual(self.ids["mag_well"]["iface"], "BMW-R")
        self.assertEqual(self.ids["muzzle"]["iface"], "BMZ-15")
        self.assertIn("BRI-22", {p.get("iface") for p in self.parts})
        self.assertEqual(self.ids["handguard"]["mat"], "graphite")

    def test_budgets(self):
        self.assertLessEqual(len(light_functions(self.parts)), 3, light_functions(self.parts))
        self.assertLessEqual(len(accent_functions(self.parts)), 3, accent_functions(self.parts))
        self.assertEqual([p["id"] for p in self.parts if p["shape"] == "text"], ["text_r"])
        self.assertEqual(len(graphics(self.parts)), 1, graphics(self.parts))
        # Gegenproben: ein weiteres Leuchtteil und ein weiterer Akzenthebel überschreiten die Schranken
        glow = next(p for p in self.parts if p["mat"] == "energy" and p["asm"] != "sight")
        extra = self.parts + [dict(glow, id=f"extra_{i}") for i in range(3)]
        self.assertGreater(len(light_functions(extra)), 3)
        lever = dict(self.ids["selector"], id="extra_lever")
        self.assertGreater(len(accent_functions(self.parts + [lever])), 3)

    def test_sight_line(self):
        bore = self.ids["barrel"]["c"][0]
        eye = self.data["ANCHORS"]["Socket_Eye"]["at"][1]
        self.assertGreaterEqual(eye - bore, SIGHT_RANGE[0])
        self.assertLessEqual(eye - bore, SIGHT_RANGE[1])
        self.assertEqual(bore, self.basic_bore())

    def basic_bore(self):
        return next(p for p in self.basic["PARTS"] if p["id"] == "barrel")["c"][0]

    def test_own_silhouette(self):
        """Seiten-IoU < 0,85 gegen BASIC-NN und jedes vorhandene EXTENDED-Modell der Langwaffenklasse."""
        self.assertLess(pair_iou(self.basic["PARTS"], self.parts), IOU_MAX)
        self.assertAlmostEqual(pair_iou(self.basic["PARTS"], self.parts), extended.side_iou(self.basic["PARTS"], self.parts),
                               delta=1e-4, msg="Paarrahmen misst wie der Standardrahmen, wenn beide hineinpassen")
        others = 0
        for key in extended.MODELS:
            if key == self.KEY:
                continue
            other = extended.load(key, SNAP)
            if other["META"]["reference_length_m"] >= LONG_M:
                others += 1
                self.assertLess(pair_iou(other["PARTS"], self.parts), IOU_MAX, key)
        self.assertGreaterEqual(others, 2, "mindestens EXTENDED-01 und das Schwestergewehr")
        # Gegenprobe: das Maß erkennt eine Kopie (IoU 1) und eine Linie (BASIC ohne Mündung bleibt über der Schwelle)
        self.assertGreaterEqual(pair_iou(self.parts, copy.deepcopy(self.parts)), 0.99)
        trimmed = [p for p in self.basic["PARTS"] if not p["id"].startswith("muzzle")]
        self.assertGreater(pair_iou(self.basic["PARTS"], trimmed), IOU_MAX)
        # Gegenprobe: ein Modell über 1,2 m (Lauf bis f 1400, Kolben bis f −500) bricht den Standardrahmen ab, den Paarrahmen nicht
        long = copy.deepcopy(self.parts) + [dict(shape="cyl", axis="f", c=(100, 0), a0=-500, a1=1400, r=12, id="long", mat="metal")]
        self.assertGreater(length(long), 1200)
        with self.assertRaisesRegex(ValueError, "beschnitten"):
            extended.side_iou(long, self.parts)
        self.assertLess(pair_iou(long, self.parts), 1.0)

    def test_no_floating_parts(self):
        groups = extended.components(self.parts)
        self.assertEqual(len(groups), 1, groups[1:])
        moved = copy.deepcopy(self.parts)   # Gegenprobe: das Mündungsteil 40 mm nach vorn → eigene Gruppe
        for p in moved:
            if p["id"] in ("muzzle", "muzzle_tip", "muzzle_crown"):
                p["a0"] += 60
                p["a1"] += 60
        self.assertGreater(len(extended.components(moved)), 1)

    def test_length(self):
        self.assertAlmostEqual(length(self.parts) / 1000, self.data["META"]["reference_length_m"], delta=0.005)

    def test_source_hash(self):
        a = extended.source(self.KEY, SNAP)
        self.assertEqual(a, extended.source(self.KEY, SNAP))
        self.assertIn(f"formgen/models/extended/{extended.MODELS[self.KEY]}.py", a["files"])
        self.assertIn("basic/common.py", a["files"])
        self.assertFalse([f for f in a["files"] if f.startswith(f"basic/pilot/w{self.NUM}_")], "kein Umbau von BASIC-NN")
        self.assertFalse([f for f in a["files"] if f.startswith(f"basic/weapons/w{self.NUM}_")], "kein Umbau von BASIC-NN")


@unittest.skipIf(SNAP is None, REASON)
class TestCadence(Common, unittest.TestCase):
    KEY, NUM = "e02", "02"

    def test_bullpup(self):
        """Bullpup: Magazin und Verschluss hinter dem Griff, Laufachse wie BASIC-02, deutlich kürzer als BASIC-02."""
        A = self.data["ANCHORS"]
        self.assertLess(A["Socket_MagWell"]["at"][0], -100)
        self.assertLess(self.data["EJECT"]["at"][0], -60)
        self.assertLess(length(self.parts), 0.9 * length(self.basic["PARTS"]))
        basic_mag = next(a for a in self.basic["ANCHORS"].values() if a["part"] == "mag_well")
        self.assertGreater(basic_mag["at"][0], 0, "Gegenprobe: BASIC-02 ist konventionell")

    def lean_edges(self, parts):
        ids = {p["id"]: p for p in parts}
        up, ch, lo = ids["upper"]["pts"], ids["chamber"]["pts"], ids["lower"]["pts"]
        edges = {"Kolbenende": (up[0], up[5]), "Fuge Kolben/Fahrgestell": (up[1], up[2]), "Fuge Kolben/Haube": (up[3], up[4]),
                 "Stirn": (ch[1], ch[2])}
        for i, c in enumerate(ids["chamber"]["cuts"]):
            if c["shape"] == "prof" and c.get("w") == 80:
                edges[f"Taktschlitz {i}"] = (c["pts"][0], c["pts"][3])
        for b in ("burst_1", "burst_2", "burst_3"):
            edges[b] = (ids[b]["pts"][0], ids[b]["pts"][3])
        return edges, ids

    def test_one_lean(self):
        """Leitmerkmal Parallelogramm: Kolbenende, Stirn, beide schrägen Fugen, die drei Taktschlitze, die Leuchtbalken und das Magazin
        neigen sich um denselben Winkel wie der Griff BGM-1 (15°). Gegenprobe: ein senkrechter Schlitz fällt auf."""
        edges, ids = self.lean_edges(self.parts)
        self.assertEqual(sum(k.startswith("Taktschlitz") for k in edges), 3)
        for name, (a, b) in edges.items():
            self.assertAlmostEqual(angle(a, b), 15.0, delta=0.3, msg=name)
        mag = ids["magazine"]["pts"]                     # Magazinvorderkante oben → unten: unten weiter hinten
        self.assertAlmostEqual(angle(mag[2], mag[1]), 15.0, delta=0.3)
        grip = ids["grip"]["pts"]
        self.assertAlmostEqual(angle(grip[5], grip[3]), 15.0, delta=0.3, msg="Griffachse BGM-1 (Vorgabe, Punkte mit gleichem Versatz)")
        bad = copy.deepcopy(self.parts)
        cut = next(c for c in next(p for p in bad if p["id"] == "chamber")["cuts"] if c["shape"] == "prof" and c.get("w") == 80)
        cut["pts"][3] = (cut["pts"][0][0], cut["pts"][3][1])
        edges, _ = self.lean_edges(bad)
        self.assertTrue([k for k, (a, b) in edges.items() if abs(angle(a, b) - 15.0) > 0.3])

    def test_slots_see_through(self):
        """Negativraum: jeder Taktschlitz geht quer ganz durch Haube und Vorderschaft und hat eine Spule auf der Laufachse;
        die Seitensilhouette zeigt den Durchblick über der Spule."""
        hood, guard = self.ids["chamber"], self.ids["handguard"]
        slots = [c for c in hood["cuts"] if c["shape"] == "prof" and c.get("w") == 80]
        coils = self.ids["pulse_coils"]["items"]
        self.assertEqual(len(slots), 3)
        self.assertEqual(len(coils), 3)
        mask = extended.side_mask(self.parts)
        for s, c in zip(slots, coils):
            self.assertIn(s, guard["cuts"])
            self.assertGreaterEqual(s["w"] / 2, hood["w"] / 2)
            fs = [q[0] for q in s["pts"]]
            self.assertTrue(min(fs) < c["a0"] and c["a1"] < max(fs), "Spule im Schlitz")
            top_u = c["c"][0] + c["r"] + 2             # 2 mm über der Spule, Schlitzmitte
            f_mid = (c["a0"] + c["a1"]) / 2 + (top_u - c["c"][0]) * math.tan(math.radians(15))
            j, i = round(f_mid + 420), round(519 - (top_u + 200))
            self.assertFalse(mask[i, j], f"kein Durchblick bei f {f_mid:.0f}")
        # Gegenprobe: ohne Schlitze ist dort Schale
        closed = copy.deepcopy(self.parts)
        for p in closed:
            if p["id"] in ("chamber", "handguard"):
                p["cuts"] = [c for c in p["cuts"] if not (c["shape"] == "prof" and c.get("w") == 80)]
        self.assertTrue(extended.side_mask(closed)[i, j])

    def test_window_bars_visible(self):
        """Blickfang: die drei Leuchtbalken liegen im offenen Fensterschacht zwischen Fenstergrund und Glas (Runde 1 lagen sie
        im Muldenboden der Schale und waren unsichtbar). Gegenprobe: ohne Fensterschacht liegen sie im Vollmaterial."""
        def problems(parts):
            ids = {p["id"]: p for p in parts}
            up = ids["upper"]
            wells = [c for c in up["cuts"] if c["shape"] == "prof" and c.get("x", 0) > 0 and c["x"] - c["w"] / 2 <= 17]
            out = []
            for b in ("burst_1", "burst_2", "burst_3"):
                bar = ids[b]
                x0, x1 = bar["x"] - bar["w"] / 2, bar["x"] + bar["w"] / 2
                if not (ids["window_back"]["x"] + ids["window_back"]["w"] / 2 <= x0 and x1 <= ids["window_lens"]["x"] - 0.3):
                    out.append(f"{b}: nicht zwischen Grund und Glas")
                fs, us = [q[0] for q in bar["pts"]], [q[1] for q in bar["pts"]]
                inside = [w for w in wells if min(q[0] for q in w["pts"]) <= min(fs) and max(fs) <= max(q[0] for q in w["pts"])
                          and min(q[1] for q in w["pts"]) <= min(us) and max(us) <= max(q[1] for q in w["pts"])
                          and w["x"] - w["w"] / 2 <= x0]
                if not inside:
                    out.append(f"{b}: im Vollmaterial der Schale")
            return out
        self.assertEqual(problems(self.parts), [])
        r1 = copy.deepcopy(self.parts)
        up = next(p for p in r1 if p["id"] == "upper")
        up["cuts"] = [c for c in up["cuts"] if not (c["shape"] == "prof" and c.get("w") == 14)]
        self.assertEqual(len(problems(r1)), 3)

    def test_lettering(self):
        """Schrift rechts auf der Kammerhaube zwischen schräger Fuge und erstem Taktschlitz, unter der Schulterfase, über der Fuge."""
        t, hood = self.ids["text_r"], self.ids["chamber"]
        f0, f1 = text_span(t)
        self.assertGreater(f0, hood["pts"][0][0] + 3)
        slot = next(c for c in hood["cuts"] if c["shape"] == "prof" and c.get("w") == 80)
        self.assertLess(f1, min(q[0] for q in slot["pts"]) - 3)
        self.assertGreater(t["u"], hood["pts"][0][1] + 2)
        self.assertLess(t["u"] + t["size"], hood["pts"][2][1] - 10)          # unter der Schulterfase (10 mm)
        self.assertAlmostEqual(abs(t["x"]), hood["w"] / 2, delta=0.1)
        self.assertGreater(text_span(dict(t, f=170))[1], min(q[0] for q in slot["pts"]) - 3)   # Gegenprobe: läuft in den Schlitz


@unittest.skipIf(SNAP is None, REASON)
class TestMeridian(Common, unittest.TestCase):
    KEY, NUM = "e03", "03"

    AXIAL = ("drum", "drum_cap", "coupling", "tube", "handguard", "band", "face_cap", "crown", "barrel", "muzzle", "stock_tube",
             "stock_ring")

    def test_coaxial(self):
        """Leitmerkmal: Rohrschaft, Trommel, Vorderrohr, Handschale, Stirn und Mündung sind Zylinder auf der Laufachse; Ober- und
        Unterlinie des Rohrzugs sind gerade (Trommel 4 mm über dem Rohr). Gegenprobe: ein versetztes Rohr fällt auf."""
        bore = self.ids["barrel"]["c"][0]

        def off(parts):
            ids = {p["id"]: p for p in parts}
            return [k for k in self.AXIAL if ids[k]["shape"] != "cyl" or ids[k]["axis"] != "f" or tuple(ids[k]["c"]) != (bore, 0)]
        self.assertEqual(off(self.parts), [])
        self.assertEqual(self.ids["drum"]["r"] - self.ids["tube"]["r"], 4.0)
        self.assertGreater(self.ids["handguard"]["r"], self.ids["tube"]["r"])
        tube = self.ids["tube"]
        self.assertGreater(tube["a1"] - tube["a0"], 350, "langes Vorderrohr")
        bad = copy.deepcopy(self.parts)
        next(p for p in bad if p["id"] == "tube")["c"] = (bore + 6, 0)
        self.assertEqual(off(bad), ["tube"])

    def test_round_section(self):
        """Querschnitt Kreis: Vorderrohr mit Rillen oben, Trommel mit Seitenflächen; Rillen links oben tragen die Meridianlinie."""
        tube, drum, line = self.ids["tube"], self.ids["drum"], self.ids["meridian"]
        flutes = [c for c in tube["cuts"] if c["shape"] == "xprof"]
        self.assertEqual(len(flutes), 4)
        for c in flutes:
            self.assertTrue(all(q[1] > tube["c"][0] for q in c["pts"]), "Rillen nur in der oberen Hälfte")
        bore = tube["c"][0]
        mx, mu = (sum(q[0] for q in line["pts"]) / 4, sum(q[1] for q in line["pts"]) / 4 - bore)
        ang = math.degrees(math.atan2(mu, mx))
        self.assertTrue(any(abs(ang - math.degrees(math.atan2(sum(q[1] - bore for q in c["pts"]), sum(q[0] for q in c["pts"])))) < 1
                            for c in flutes), "Meridianlinie in einer Rille")
        self.assertLess(math.hypot(mx, mu), tube["r"], "im Rillengrund, unter der Rohroberfläche")
        self.assertGreater(mx, 0, "Meridianlinie links (Ego-Seite)")
        self.assertTrue(flutes[0]["f0"] <= line["f0"] and line["f1"] <= flutes[0]["f1"])
        self.assertEqual(sum(1 for c in drum["cuts"] if c.get("w") == 2 * drum["r"]), 2, "zwei Seitenflächen")

    def test_cheek_bridge_window(self):
        """Negativraum: das Fenster der Wangenbrücke geht quer durch und liegt über dem Rohrschaft; die Seitensilhouette ist dort offen.
        Gegenprobe: ohne Fensterschnitt ist die Brücke geschlossen."""
        bridge, tube = self.ids["cheek_bridge"], self.ids["stock_tube"]
        win = bridge["cuts"][0]
        self.assertGreaterEqual(win["w"], bridge["w"])
        us = [q[1] for q in win["pts"]]
        self.assertGreater(min(us), tube["c"][0] + tube["r"], "über dem Rohrschaft")
        fs = [q[0] for q in win["pts"]]
        j, i = round((min(fs) + max(fs)) / 2 + 420), round(519 - ((min(us) + max(us)) / 2 + 200))
        self.assertFalse(extended.side_mask(self.parts)[i, j])
        closed = copy.deepcopy(self.parts)
        next(p for p in closed if p["id"] == "cheek_bridge")["cuts"] = []
        self.assertTrue(extended.side_mask(closed)[i, j])

    def test_lettering(self):
        """Schrift rechts auf der Trommelfläche vor dem Auswurffenster, innerhalb der Flächenhöhe."""
        t, drum = self.ids["text_r"], self.ids["drum"]
        half = next(c for c in drum["cuts"] if c.get("w") == 2 * drum["r"])["x"]
        flat = abs(half) - drum["r"]
        chord = math.sqrt(drum["r"] ** 2 - flat ** 2)
        bore = drum["c"][0]
        port = next(c for c in drum["cuts"] if c.get("x") == -flat and c.get("w") == 8)

        def problems(t):
            f0, f1 = text_span(t)
            out = []
            if f0 < port["f1"] + 3 and f1 > port["f0"] - 3:
                out.append("auf dem Auswurffenster")
            if f1 > drum["a1"] - 10:
                out.append("über der Kupplung")
            if t["u"] < bore - chord + 1 or t["u"] + t["size"] > bore + chord - 1:
                out.append("außerhalb der Fläche")
            if abs(abs(t["x"]) - flat) > 0.1:
                out.append("nicht auf der Fläche")
            return out
        self.assertEqual(problems(t), [])
        self.assertEqual(problems(dict(t, f=40)), ["auf dem Auswurffenster"])       # Gegenproben
        self.assertEqual(problems(dict(t, u=114)), ["außerhalb der Fläche"])


@unittest.skipIf(SNAP is None, REASON)
class TestPair(unittest.TestCase):
    """Die beiden Gewehre der Sitzung setzen sich deutlich voneinander ab: Silhouette, Architektur, Querschnitt."""

    @classmethod
    def setUpClass(cls):
        cls.a, cls.b = extended.load("e02", SNAP), extended.load("e03", SNAP)

    def test_distinct(self):
        self.assertLess(extended.side_iou(self.a["PARTS"], self.b["PARTS"]), PAIR_MAX)
        # Architektur: Bullpup (Magazin hinter dem Griff) gegen konventionell (davor)
        self.assertLess(self.a["ANCHORS"]["Socket_MagWell"]["at"][0], 0)
        self.assertGreater(self.b["ANCHORS"]["Socket_MagWell"]["at"][0], 0)
        # Querschnitt: Trapez aus Schulterfasen (xprof-Schnitte an der Haube) gegen Rundrohr (Zylinder)
        hood = next(p for p in self.a["PARTS"] if p["id"] == "chamber")
        self.assertEqual(hood["shape"], "prof")
        self.assertEqual(sum(c["shape"] == "xprof" for c in hood["cuts"]), 2)
        self.assertEqual(next(p for p in self.b["PARTS"] if p["id"] == "tube")["shape"], "cyl")
        # Gegenprobe: dieselbe Silhouette gegen sich selbst überschreitet die Paarschranke
        self.assertGreater(extended.side_iou(self.a["PARTS"], self.a["PARTS"]), PAIR_MAX)


@unittest.skipIf(SNAP is None, REASON)
class TestRenderRef(unittest.TestCase):
    """`tools/extended_render.py --basic NN` (0.17): BASIC-NN im selben AAA-Weg; nur Fehlendes oder Veraltetes; Blender wird nie gestartet."""

    def setUp(self):
        import tempfile
        from unittest import mock
        saved = list(sys.path)
        self.addCleanup(lambda: sys.path.__setitem__(slice(None), saved))
        sys.path.insert(0, str(extended.ROOT / "tools"))
        self.er = importlib.import_module("extended_render")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.a = argparse.Namespace(out=Path(self.tmp.name), tag="t", samples=96, res=1600, gpu=False, extra=False, force=False,
                                    basic="02", sheets=False)
        self.run = mock.patch.object(self.er.subprocess, "run", side_effect=self.fake).start()
        self.addCleanup(mock.patch.stopall)
        self.calls = []

    def fake(self, cmd, **kw):
        job = json.loads(Path(cmd[-1]).read_text())
        self.calls.append(job)
        out = Path(job["out"]) / "BASIC-02-v2.1" / "views"
        out.mkdir(parents=True)
        for v in job["only"].split(","):
            (out / f"{v}.png").write_bytes(b"png")
        return argparse.Namespace(returncode=0, stdout="", stderr="")

    def test_renders_once_with_pilot_base(self):
        self.assertTrue(self.er.render_ref("02", self.a))
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0]["base"], "basic.pilot.w02_pulse_rifle_v21")
        self.assertEqual(self.calls[0]["model"]["META"]["id"], "BASIC-02")
        self.assertEqual(sorted(p.name for p in (self.a.out / "BA02").glob("*.png")), ["hero.png", "side_left.png"])
        self.assertFalse(self.er.render_ref("02", self.a))          # aktuell: kein zweiter Lauf
        self.assertEqual(len(self.calls), 1)
        # Gegenproben: andere Auflösung, --force und ein fehlendes Bild rendern neu
        for change in (dict(res=800), dict(force=True), {}):
            a = copy.copy(self.a)
            vars(a).update(change)
            if not change:
                (self.a.out / "BA02" / "hero.png").unlink()
            self.assertTrue(self.er.render_ref("02", a))
        self.assertEqual(len(self.calls), 4)

    def test_missing_view_leaves_no_stamp(self):
        def partial(cmd, **kw):
            job = json.loads(Path(cmd[-1]).read_text())
            out = Path(job["out"]) / "BASIC-02-v2.1" / "views"
            out.mkdir(parents=True)
            (out / "hero.png").write_bytes(b"png")
            return argparse.Namespace(returncode=0, stdout="", stderr="")
        self.run.side_effect = partial
        with self.assertRaises(RuntimeError):
            self.er.render_ref("02", self.a)
        self.assertFalse((self.a.out / "BA02" / "render.json").exists())


if __name__ == "__main__":
    unittest.main()
