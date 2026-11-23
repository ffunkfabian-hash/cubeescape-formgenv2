"""EXTENDED-06 „Wishbone“ und EXTENDED-15 „Flywheel“ (0.22 „Torrent“): Maschinenpistole und Maschinengewehr als eigene Modelle.

Prüft die Datensätze ohne Blender: Felder und IDs, Blatt-IDs, Anker/Weltpunkte/Aktionen (BALLONs `variant.problems` als Orakel),
Familienschnittstellen, Budgets des Stilhandbuchs (genau ein Blickfang außerhalb des Visiers, ≤ 3 Akzent-Bedienfunktionen, eine Schrift,
ein Grafikelement), Visierlinie, Schrift auf ebener Fläche, Seiten-IoU < 0,85 gegen den eigenen BASIC-Typ, gegen jedes andere
EXTENDED-Modell und gegeneinander (Rahmen aus den Hüllen beider Modelle), die Leitmotive (Gabelbein: Schacht 24° gegen Griff 15°,
Kinnstirn und Λ-Fenster parallel, geschlossener Gabelzwickel; Schwungrad: Trommel quer mit offener Nabe, Kühlmantel mit vier Rippen),
die Absetzung der beiden Dauerfeuerwaffen, Zusammenhang, Länge und Quellhash. Jede Regelprüfung hat eine Gegenprobe, die aus dem
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
PAIR_MAX = 0.70                # Annahme wie 0.18: die beiden Typen einer Sitzung setzen sich deutlich ab
SIGHT_RANGE = (60.0, 80.0)     # Vorgabe Visier-Standard
FRAME_MARGIN = 20.0            # A: Rand um die gemeinsame Hülle (mm)
OWN = {"e06": dict(num="06", type="submachine_gun", id="EXTENDED-06", sheet="EA06", mod="e06_wishbone"),
       "e15": dict(num="15", type="machine_gun", id="EXTENDED-15", sheet="EA15", mod="e15_flywheel")}
# Projizierte Teile des Holovisiers H2 „Pille“: Kontur, Glas und Absehen stehen frei vor dem Emitter (BASIC-06 genauso, gemessen)
H2_FREE = {"sight_line", "sight_glass", "sight_reticle"}


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


def lean_deg(a, b):
    """Neigung der Strecke a→b gegen die Senkrechte in Grad; positiv, wenn sie nach unten nach vorn läuft."""
    (f0, u0), (f1, u1) = (a, b) if a[1] > b[1] else (b, a)
    return math.degrees(math.atan2(f1 - f0, u0 - u1))


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
class TestDauerfeuer(unittest.TestCase):
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
        self.assertEqual(bool(self.data["e15"]["EJECT"].get("links")), True, "MG wirft Gurtglieder aus wie BASIC-15")

    def test_sheet_ids(self):
        for k, o in OWN.items():
            self.assertEqual(extended.sheet_id(k), o["sheet"])
            self.assertEqual(self.data[k]["META"]["sheet_id"], o["sheet"])
            self.assertRegex(o["sheet"], f"^{extended.SHEET_PATTERN}$")
        sids = list(extended.SHEETS.values())
        self.assertEqual(len(set(sids)), len(sids), "Blatt-IDs doppelt")
        self.assertEqual(set(extended.SHEETS), set(extended.MODELS))
        self.assertIsNone(re.match(f"^{extended.SHEET_PATTERN}$", "EI06"))   # Gegenprobe: Linienbuchstabe I ist gesperrt

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
        want = {"e06": {"grip": "BGM-1", "magazine": "BMW-R", "well_lip": "BMW-R", "muzzle": "BMZ-15", "rail": "BRI-22"},
                "e15": {"grip": "BGM-1", "ammo_box": "BAB-1", "drum_hanger": "BAB-1", "muzzle": "BMZ-15", "rail": "BRI-22"}}

        def problems(ids, w):
            return [pid for pid, iface in w.items() if ids.get(pid, {}).get("iface") != iface]
        for k, ids in self.ids.items():
            with self.subTest(k):
                self.assertEqual(problems(ids, want[k]), [])
                self.assertEqual(ids["grip"]["mat"], "rubber")
        self.assertEqual(problems(self.ids["e06"], want["e15"]), ["ammo_box", "drum_hanger"])   # Gegenprobe: MP hat keine Trommel

    # ---------------------------------------------------------------- Budgets, Visier, Schrift
    def test_budgets(self):
        for k, d in self.data.items():
            with self.subTest(k):
                P = d["PARTS"]
                self.assertEqual(len(lights(P)), 1, f"genau ein Blickfang außerhalb des Visiers: {lights(P)}")
                glow = self.ids[k][lights(P)[0]]
                self.assertGreater(glow["x"], 0, "Blickfang links (Ego-Seite)")
                self.assertLessEqual(len(accent_functions(P)), 3, accent_functions(P))
                self.assertEqual([p["id"] for p in P if p["shape"] == "text"], ["text_r"])
                self.assertEqual(len(graphics(P)), 1, graphics(P))
        two = self.data["e06"]["PARTS"] + [dict(self.ids["e06"]["ammo_counter"], id="counter2")]   # Gegenprobe: zweiter Blickfang
        self.assertEqual(len(lights(two)), 2)
        more = self.data["e15"]["PARTS"] + [dict(self.ids["e15"]["cover_latch"], id="extra_lever")]   # Gegenprobe: vierte Bedienfunktion
        self.assertGreater(len(accent_functions(more)), 3)

    def test_sight_line(self):
        def height(d):
            return d["ANCHORS"]["Socket_Eye"]["at"][1] - d["ANCHORS"]["Socket_Muzzle"]["at"][1]
        for k, d in self.data.items():
            with self.subTest(k):
                self.assertTrue(SIGHT_RANGE[0] <= height(d) <= SIGHT_RANGE[1], height(d))
        raised = copy.deepcopy(self.data["e15"])   # Gegenprobe: Visier 20 mm höher liegt außerhalb des Vertrags
        raised["ANCHORS"]["Socket_Eye"]["at"] = tuple(v + (20 if i == 1 else 0) for i, v in enumerate(raised["ANCHORS"]["Socket_Eye"]["at"]))
        self.assertGreater(height(raised), SIGHT_RANGE[1])

    def test_lettering_on_flat_face(self):
        """E06: rechts am Deck zwischen Auswurffenster und Kinnstirn; E15: rechts am Gehäuse zwischen Auswurffenster und Mantelträger."""
        c6, c15 = self.consts["e06"], self.consts["e15"]

        def problems(k, t):
            ids, c = self.ids[k], self.consts[k]
            a, b = text_span(t)
            h = 0.75 * t["size"]
            if k == "e06":
                lo, hi, u0, u1, half = c["_port"][1] + 3, c["face"](t["u"] + h) - 3, c["SPLIT"] + 6, c["TOP"] - 3, c["HALF_D"]
            else:
                lo, hi, u0, u1, half = c["PORT"][1] + 3, c["REC1"] - 5, c["SPLIT"] + 2, c["TOP"] - 4, c["HALF"]
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
        self.assertIn("außerhalb der freien Fläche", problems("e06", dict(self.ids["e06"]["text_r"], f=c6["_port"][0])))   # im Fenster
        self.assertIn("außerhalb der freien Fläche", problems("e15", dict(self.ids["e15"]["text_r"], f=c15["REC1"] - 20)))  # über die Fuge
        self.assertIn("außerhalb der Höhe", problems("e15", dict(self.ids["e15"]["text_r"], u=c15["SPLIT"] - 4)))          # auf der Fuge

    # ---------------------------------------------------------------- Silhouette
    def test_own_silhouette(self):
        """Seiten-IoU < 0,85 gegen den eigenen BASIC-Typ, gegen jedes andere EXTENDED-Modell und gegeneinander (< 0,70)."""
        for k, d in self.data.items():
            with self.subTest(k):
                self.assertLess(iou(self.basic[k]["PARTS"], d["PARTS"]), IOU_MAX)
                for o, parts in self.others.items():
                    self.assertLess(iou(parts, d["PARTS"]), IOU_MAX, o)
        self.assertLess(iou(self.data["e06"]["PARTS"], self.data["e15"]["PARTS"]), PAIR_MAX)
        b15 = self.basic["e15"]["PARTS"]   # Gegenproben: gleiche Form 1,0; eine Parameterlinie bleibt über der Schwelle
        self.assertGreaterEqual(iou(b15, b15), 0.99)
        trimmed = [p for p in b15 if p["id"] not in ("muzzle", "muzzle_crown")]
        self.assertGreater(iou(b15, trimmed), IOU_MAX)
        # Gegenprobe: der Rahmen aus beiden Hüllen trägt auch die 1,6 m lange Glefe, die den Standardrahmen sprengt
        self.assertLess(iou(self.others["e17"], self.data["e15"]["PARTS"]), IOU_MAX)
        with self.assertRaisesRegex(ValueError, "beschnitten"):
            extended.side_mask(self.others["e17"])

    # ---------------------------------------------------------------- Leitmotiv Gabelbein (E06)
    def test_wishbone_spread(self):
        """Schacht 24° nach vorn, Griff 15° nach hinten (Λ); Magazin, Kinnstirn und Λ-Fenster folgen den beiden Schenkeln."""
        ids, c = self.ids["e06"], self.consts["e06"]

        def spread(ids):
            well = ids["mag_well"]["pts"]
            grip = ids["grip"]["pts"]
            return lean_deg(well[1], well[2]), lean_deg(grip[0], grip[1])
        well, grip = spread(ids)
        self.assertAlmostEqual(well, 24.0, delta=0.1)
        self.assertLess(grip, -10.0, "Griff läuft nach unten nach hinten")
        self.assertGreater(well - grip, 35.0, "Λ: die Schenkel spreizen sich um mehr als 35°")
        mag = next(p for p in self.data["e06"]["PARTS"] if p["id"] == "magazine")
        self.assertAlmostEqual(lean_deg(mag["pts"][1], mag["pts"][2]), 24.0, delta=0.1)
        self.assertAlmostEqual(lean_deg((c["face"](40), 40), (c["face"](116), 116)), 24.0, delta=0.1)
        tri = ids["ammo_counter"]["pts"]
        self.assertAlmostEqual(lean_deg(tri[1], tri[2]), 24.0, delta=0.1, msg="Vorderkante des Λ-Fensters wie der Schacht")
        self.assertAlmostEqual(lean_deg(tri[0], tri[2]), -15.0, delta=0.1, msg="Hinterkante wie der Griff")
        upright = dict(ids, mag_well=dict(ids["mag_well"], pts=[(84, 42), (132, 42), (132, -34), (84, -34)]))   # Gegenprobe: senkrecht
        self.assertLess(spread(upright)[0] - spread(upright)[1], 35.0)

    def test_wishbone_gap_closed(self):
        """Gabelzwickel: der Abzugsraum zwischen Griff, Schacht, Rumpf und Bügel ist in der Seite eine geschlossene Lücke."""
        P = self.data["e06"]["PARTS"]
        self.assertTrue(enclosed(P, 66, 28))
        self.assertFalse(enclosed(P, 66, -10), "unter dem Bügel öffnet sich das Λ")
        self.assertFalse(enclosed([p for p in P if p["id"] != "trigger_guard"], 66, 28))   # Gegenprobe: ohne Bügel offen

    def test_t_section(self):
        """T-Querschnitt: das Deck kragt je Seite mindestens 5 mm über den Rumpf."""
        ids = self.ids["e06"]

        def overhang(ids):
            return (ids["upper"]["w"] - ids["lower"]["w"]) / 2
        self.assertGreaterEqual(overhang(ids), 5.0)
        self.assertLess(overhang(dict(ids, upper=dict(ids["upper"], w=ids["lower"]["w"]))), 5.0)   # Gegenprobe: bündig

    # ---------------------------------------------------------------- Leitmotiv Schwungrad (E15)
    def test_flywheel_drum(self):
        """Trommel quer zur Laufachse, Ø ≥ 140, zwischen Griff und Stützhand, offene Nabe quer durch alle Trommelteile."""
        ids, c = self.ids["e15"], self.consts["e15"]
        drum = ids["ammo_box"]
        self.assertEqual(drum["axis"], "x")
        self.assertGreaterEqual(2 * drum["r"], 140)
        f_sup = self.data["e15"]["ANCHORS"]["Socket_SupportHand"]["at"][0]
        self.assertTrue(0 < drum["c"][0] - drum["r"] and drum["c"][0] + drum["r"] < f_sup, "Rad zwischen Griff und Stützhand")

        def hub_problems(parts):
            """Trommelteile haben die Nabe als durchgehenden Schnitt; kein anderes Teil ragt in der Seite in den Nabenkreis."""
            out = []
            hub, drum_ids = c["HUB_R"], ("ammo_box", "drum_face_l", "drum_face_r")
            for p in parts:
                if p["id"] in drum_ids:
                    holes = [q for q in p.get("cuts") or () if q.get("axis") == "x" and q["r"] >= hub
                             and min(q["a0"], q["a1"]) <= min(p["a0"], p["a1"]) and max(q["a0"], q["a1"]) >= max(p["a0"], p["a1"])]
                    if not holes:
                        out.append(f"{p['id']}: Nabe nicht durchgehend")
            rest = [p for p in parts if p["id"] not in drum_ids + ("hub_sleeve", "hub_rings") and extended.bounds(p)]
            fr = frame(rest + [drum])
            rows, cols = fr["size"][1], fr["size"][0]
            uu, ff = np.mgrid[0:rows, 0:cols]
            inside = np.hypot(ff + fr["lo"][0] - drum["c"][0], rows - 1 - uu + fr["lo"][1] - drum["c"][1]) < hub - 0.5
            for p in rest:
                if (extended.side_mask([p], **fr) & inside).any():
                    out.append(f"{p['id']} in der Nabe")
            return out
        self.assertEqual(hub_problems(self.data["e15"]["PARTS"]), [])
        spindle = dict(drum, id="spindle", r=8, cuts=[], a0=-40, a1=40, mat="metal")   # Gegenprobe: Achse in der Nabe
        self.assertEqual(hub_problems(self.data["e15"]["PARTS"] + [spindle]), ["spindle in der Nabe"])
        blind = dict(drum, cuts=[dict(q, a0=drum["a0"] + 4) for q in drum["cuts"]])   # Gegenprobe: Sackloch
        self.assertIn("ammo_box: Nabe nicht durchgehend", hub_problems([blind]))

    def test_cross_jacket(self):
        """Kreuz-Querschnitt: vier Rippen oben, unten, links, rechts um den runden Kern, mindestens 8 mm dick."""
        c = self.consts["e15"]
        fins = self.ids["e15"]["jacket_fins"]["items"] + self.ids["e15"]["jacket_fins_side"]["items"]

        def directions(fins):
            out = set()
            for q in fins:
                b = extended.bounds(q)
                (f0, u0, x0), (f1, u1, x1) = b
                if q["shape"] == "prof" and q["w"] >= 8:
                    out.add("oben" if u0 > c["BORE"] else "unten")
                if q["shape"] == "plan" and u1 - u0 >= 8:
                    out.add("links" if x0 > 0 else "rechts")
            return out
        self.assertEqual(directions(fins), {"oben", "unten", "links", "rechts"})
        self.assertEqual(directions([dict(q, w=4) if q["shape"] == "prof" else q for q in fins]), {"links", "rechts"})   # Gegenprobe: zart

    # ---------------------------------------------------------------- Absetzung, Zusammenhang, Länge, Quellhash
    def test_compact_versus_heavy(self):
        """MP kompakt mit Magazin im Schachtgriff, MG lang und schwer mit großer Trommel."""
        l6, l15 = length(self.data["e06"]["PARTS"]), length(self.data["e15"]["PARTS"])
        self.assertLess(l6, 480)
        self.assertGreater(l15, 950)
        self.assertLess(l6, length(self.basic["e06"]["PARTS"]), "E06 kompakter als BASIC-06")
        self.assertIn("magazine", self.ids["e06"])
        self.assertNotIn("magazine", self.ids["e15"])
        self.assertEqual(self.ids["e15"]["ammo_box"]["shape"], "cyl")
        self.assertGreater(l15 / l6, 2.0)

    def test_no_floating_parts(self):
        for k, d in self.data.items():
            with self.subTest(k):
                groups = extended.components(d["PARTS"])
                self.assertEqual([g for g in groups[1:] if set(g) - H2_FREE], [], groups[1:])
        b06 = extended.components(self.basic["e06"]["PARTS"])   # Beleg: dieselbe freie Gruppe beim Piloten BASIC-06
        self.assertEqual({frozenset(g) for g in b06[1:]}, {frozenset(H2_FREE)})
        moved = copy.deepcopy(self.data["e15"]["PARTS"])   # Gegenprobe: Mündung 60 mm nach vorn → eigene Gruppe
        for p in moved:
            if p["id"] in ("muzzle", "muzzle_crown"):
                p["a0"] += 60
                p["a1"] += 60
        self.assertGreater(len(extended.components(moved)), 1)

    def test_proportions(self):
        for k, d in self.data.items():
            with self.subTest(k):
                self.assertAlmostEqual(length(d["PARTS"]) / 1000, d["META"]["reference_length_m"], delta=0.005)
        longer = self.data["e06"]["PARTS"] + [dict(self.ids["e06"]["muzzle_crown"], id="probe", a0=300, a1=310)]   # Gegenprobe
        self.assertGreater(abs(length(longer) / 1000 - self.data["e06"]["META"]["reference_length_m"]), 0.005)

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
