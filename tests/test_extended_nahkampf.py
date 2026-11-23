"""EXTENDED-16 „Sweepguard“ (Schwert) und EXTENDED-17 „Gorget“ (Glefe), 0.20 „Riftguard“: Nahkampf der EXTENDED-Familie.

Prüft die Datensätze ohne Blender: Felder und IDs, Anker wie der BASIC-Typ, Weltpunkte mit `basic.variant.problems` als Orakel,
Budgets des Stilhandbuchs, Zusammenhang, Seiten-IoU gegen den eigenen BASIC-Typ und jedes andere EXTENDED-Modell, die verlangte
Absetzung Schwert ↔ Glefe (Einhand/Klinge dominiert gegen Stange/Schaft dominiert, andere Querschnitte), Negativraum als echte Lücke
in der Seitensilhouette, Lage der Schrift und die Blatt-IDs. Jede Prüfung hat eine Gegenprobe, die aus dem erwarteten Grund anschlägt.

Visierlinie und Magazinschnittstelle entfallen: Nahkampfwaffen haben weder Visier noch Magazin (BASIC-16/17 ebenso, Formgen v1
`wtypes.MELEE`: „kein Visier und keine Visierschiene“). Geprüft wird stattdessen, dass kein Visier- und kein Magazinteil vorhanden ist.
"""
import copy
import importlib
import math
import re
import sys
import unittest

import numpy as np
from scipy import ndimage

from formgen import ballon, extended

try:
    SNAP = ballon.snapshot()
except ballon.BallonError as error:   # z. B. Cloud ohne BALLON-Checkout
    SNAP, REASON = None, str(error)
else:
    REASON = ""

IOU_MAX = 0.85                       # Annahme wie BALLON A1 und test_extended (Linien liegen bei ≥ 0,95)
FRAME = ((-700.0, -300.0), (2000, 700))   # Annahme: Rahmen für Langformen (Glefe 1,57 m); side_mask-Standard reicht nur bis f 780
HOLE_MIN = 150                       # Annahme: kleinste zählende Lücke in mm² (Rundungspixel an Fasen bleiben darunter)
KEYS = {"e16": "16", "e17": "17"}


def mask(parts):
    return extended.side_mask(parts, *FRAME)


def iou(a, b):
    ma, mb = mask(a), mask(b)
    return round(float((ma & mb).sum() / (ma | mb).sum()), 4)


def holes(parts):
    """Flächen (mm²) der vom Rand abgeschlossenen Hintergrundinseln der Seitensilhouette (Negativraum, der durchscheint)."""
    lab, n = ndimage.label(~mask(parts))
    border = set(lab[0]) | set(lab[-1]) | set(lab[:, 0]) | set(lab[:, -1])
    sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
    return sorted((int(s) for i, s in enumerate(sizes, 1) if i not in border and s >= HOLE_MIN), reverse=True)


def lights(parts):
    return sorted(p["id"] for p in parts if p["mat"] == "energy")


def accent_functions(parts):
    return sorted({p["id"] for p in parts if p["mat"] == "accent" and p.get("move")})


def graphics(parts):
    return sorted(p["id"] for p in parts if p["mat"] == "accent" and not p.get("move"))


def length(parts):
    b = [x for p in parts if (x := extended.bounds(p))]
    return max(q[1][0] for q in b) - min(q[0][0] for q in b)


def inside(pt, poly):
    """Punkt im Polygon (Strahlverfahren)."""
    f, u = pt
    hit = False
    for (f0, u0), (f1, u1) in zip(poly, poly[1:] + poly[:1]):
        if (u0 > u) != (u1 > u) and f < f0 + (u - u0) * (f1 - f0) / (u1 - u0):
            hit = not hit
    return hit


def outline(p):
    if p["shape"] == "prof":
        return [tuple(q) for q in p["pts"]]
    return [(p["f0"], p["u0"]), (p["f1"], p["u0"]), (p["f1"], p["u1"]), (p["f0"], p["u1"])]


def lettering_problems(t, carrier):
    """Schrift (linksbündig; rechts läuft sie nach vorn) ganz auf der ebenen Seitenfläche des Trägerteils.

    Länge ≈ 0,62 × Größe je Zeichen, Höhe = Größe (Annahme wie test_extended, großzügig)."""
    run = 0.62 * t["size"] * len(t["text"])
    f0, f1 = (t["f"], t["f"] + run) if t["side"] == -1 else (t["f"] - run, t["f"])
    corners = [(f0, t["u"]), (f1, t["u"]), (f1, t["u"] + t["size"]), (f0, t["u"] + t["size"])]
    out = []
    if not all(inside(c, outline(carrier)) for c in corners):
        out.append("über den Rand")
    face = abs(carrier.get("x", 0.0)) + carrier["w"] / 2
    if abs(abs(t["x"]) - face) > 0.2:
        out.append("nicht auf der Seitenfläche")
    return out


def melee_problems(data):
    """Nahkampf: kein Visier, keine Visierlinie, kein Magazin, kein Auswurf."""
    out = [f"Visierteil {p['id']}" for p in data["PARTS"] if p["asm"] == "sight"]
    out += [f"Anker {k}" for k in data["ANCHORS"] if k.startswith("Socket_Eye") or k == "Socket_MagWell"]
    out += [f"Magazinschnittstelle {p['id']}" for p in data["PARTS"] if p.get("iface") in ("BMW-R", "BRI-22")]
    if data.get("EJECT"):
        out.append("Auswurf")
    return out


@unittest.skipIf(SNAP is None, REASON)
class TestNahkampf(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = {k: extended.load(k, SNAP) for k in KEYS}
        cls.basic = {k: extended.load_basic(n, SNAP) for k, n in KEYS.items()}
        cls.ids = {k: {p["id"]: p for p in d["PARTS"]} for k, d in cls.data.items()}

    def test_fields_and_ids(self):
        for k, n in KEYS.items():
            with self.subTest(k):
                d, b = self.data[k], self.basic[k]
                for f in ("META", "PARTS", "ASSEMBLIES", "ANCHORS", "POINTS", "ACTIONS", "HERO"):
                    self.assertIn(f, d)
                self.assertEqual(d["META"]["id"], f"EXTENDED-{n}")
                self.assertEqual(d["META"]["type"], b["META"]["type"])
                self.assertEqual(len(self.ids[k]), len(d["PARTS"]), "Teil-IDs doppelt")
                asms = {a["id"] for a in d["ASSEMBLIES"]}
                self.assertEqual(asms, {a["id"] for a in b["ASSEMBLIES"]}, "Baugruppen wie BASIC")
                self.assertEqual({p["asm"] for p in d["PARTS"]} - asms, set())
                self.assertEqual(set(d["ANCHORS"]), set(b["ANCHORS"]), "Anker wie BASIC (Vertrag)")
                for name, a in d["ANCHORS"].items():
                    self.assertIn(a["part"], self.ids[k], name)
                self.assertEqual(tuple(d["ANCHORS"]["Socket_Hand"]["at"]), (0, 0, 0))
                self.assertEqual(set(d["ACTIONS"]) & set(b["ACTIONS"]), set(b["ACTIONS"]), "Aktionen von BASIC bleiben")
                for act, v in d["ACTIONS"].items():
                    for pid in v["keys"]:
                        self.assertIn("move", self.ids[k][pid], f"{act}: {pid} ohne Bewegung")

    def test_points_oracle(self):
        sys.path.insert(0, str(SNAP))
        try:
            variant = importlib.import_module("basic.variant")
            for k, d in self.data.items():
                with self.subTest(k):
                    self.assertEqual(variant.problems(variant.as_module(copy.deepcopy(d))), [])
            # Gegenprobe: ohne EGO_GRIPS fordert das Orakel die Gewehr-Griffpunkte der Familie – leere Ego-Griffe sind also Absicht
            bare = {f: v for f, v in copy.deepcopy(self.data["e16"]).items() if f != "EGO_GRIPS"}
            self.assertTrue(any("fehlt in POINTS" in m for m in variant.problems(variant.as_module(bare))))
        finally:
            sys.path.remove(str(SNAP))
            extended._purge()

    def test_melee_has_no_sight_or_magazine(self):
        for k, d in self.data.items():
            self.assertEqual(melee_problems(d), [], k)
        rifle = extended.load("e01", SNAP)   # Gegenprobe: das Gewehr hat Visier, Visierlinie, Magazin und Auswurf
        found = " ".join(melee_problems(rifle))
        for word in ("Visierteil", "Socket_Eye", "Socket_MagWell", "Magazinschnittstelle mag_well", "Auswurf"):
            self.assertIn(word, found)

    def test_budgets(self):
        want = {"e16": (["charge_arc"], ["charge_switch"], ["spine_band"]),
                "e17": (["emitter", "energy_cell_window"], ["cell_release", "shield_switch"], ["collar_stripe"])}
        for k, (li, acc, gfx) in want.items():
            with self.subTest(k):
                parts = self.data[k]["PARTS"]
                self.assertEqual(lights(parts), li)
                self.assertLessEqual(len(lights(parts)), 3)
                self.assertEqual(accent_functions(parts), acc)
                self.assertLessEqual(len(accent_functions(parts)), 3)
                self.assertEqual(graphics(parts), gfx, "genau ein Grafikelement")
                self.assertEqual([p["id"] for p in parts if p["shape"] == "text"], ["text_r"], "genau eine Schrift")
                # Blickfang: genau ein Leuchtteil ist als Blickfang beschrieben
                self.assertEqual(sum("Blickfang" in p["func"] for p in parts if p["mat"] == "energy"), 1)
                # Schrauben (trim) nur an Paneelen, Schuh, Halter: kein Schraubenteil ohne Trägerangabe
                self.assertTrue(all(p["attach"] for p in parts))
        extra = self.data["e17"]["PARTS"] + [dict(self.ids["e17"]["emitter"], id=f"x{i}") for i in range(2)]
        self.assertEqual(len(lights(extra)), 4)   # Gegenprobe: zwei zusätzliche Leuchtteile reißen die Schranke 3

    def test_no_floating_parts(self):
        for k, d in self.data.items():
            with self.subTest(k):
                self.assertEqual(len(extended.components(d["PARTS"])), 1, extended.components(d["PARTS"])[1:])
        for k, pid in (("e16", "pommel"), ("e17", "lantern")):   # Gegenprobe: ein um 60 mm versetztes Teil bildet eine eigene Gruppe
            moved = copy.deepcopy(self.data[k]["PARTS"])
            p = next(q for q in moved if q["id"] == pid)
            if p["shape"] == "cyl":   # Achse f: c = (u, x)
                p["c"] = (p["c"][0], p["c"][1] + 60)
            else:
                p["x"] = p.get("x", 0.0) + 60
            self.assertGreater(len(extended.components(moved)), 1, k)

    def test_own_silhouette(self):
        """Seiten-IoU < 0,85 gegen den eigenen BASIC-Typ und gegen jedes andere registrierte EXTENDED-Modell."""
        others = {k: extended.load(k, SNAP)["PARTS"] for k in extended.MODELS if k not in KEYS}
        for k, d in self.data.items():
            with self.subTest(k):
                self.assertLess(iou(self.basic[k]["PARTS"], d["PARTS"]), IOU_MAX)
                for o, parts in list(others.items()) + [(q, self.data[q]["PARTS"]) for q in KEYS if q != k]:
                    self.assertLess(iou(parts, d["PARTS"]), IOU_MAX, o)
        b16 = self.basic["e16"]["PARTS"]   # Gegenproben: gleich = 1,0; eine Linie (ohne Knauf) bleibt über der Schwelle
        self.assertGreaterEqual(iou(b16, b16), 0.99)
        self.assertGreater(iou(b16, [p for p in b16 if p["id"] != "pommel"]), IOU_MAX)
        with self.assertRaisesRegex(ValueError, "beschnitten"):   # Gegenprobe: zu lang für den Rahmen wird gemeldet
            mask(self.data["e17"]["PARTS"] + [dict(self.ids["e17"]["shaft"], id="long", a1=1400)])

    def test_sword_and_glaive_set_apart(self):
        """Schwert: Einhand, Klinge dominiert, geschichtete Klinge. Glefe: Stange, Schaft dominiert, Keilquerschnitt."""
        sw, gl = self.ids["e16"], self.ids["e17"]
        sw_len, gl_len = length(self.data["e16"]["PARTS"]), length(self.data["e17"]["PARTS"])
        blade = max(q[0] for q in sw["blade"]["pts"]) - extended.bounds(sw["guard"])[1][0]
        self.assertGreaterEqual(blade / sw_len, 0.70, "Schwert: Klinge ≥ 70 % der Länge")
        grip = extended.bounds(sw["grip"])
        self.assertLessEqual(grip[1][0] - grip[0][0], 130, "Schwert: Einhandgriff ≤ 130 mm")
        shaft = extended.bounds(gl["shaft"])
        self.assertGreaterEqual((shaft[1][0] - shaft[0][0]) / gl_len, 0.60, "Glefe: Schaft ≥ 60 % der Länge")
        head = gl_len - (extended.bounds(gl["head_collar"])[0][0] - min(b[0][0] for p in self.data["e17"]["PARTS"]
                                                                          if (b := extended.bounds(p))))
        self.assertLessEqual(head / gl_len, 0.35, "Glefe: kompakter Kopf")
        # Querschnitte: Schwert drei Stufen (Seitenprofile verschiedener Breite), Glefe Keil als Querprofil
        widths = sorted({sw[i]["w"] for i in ("spine_rail", "blade", "blade_edge")})
        self.assertEqual(len(widths), 3)
        self.assertTrue(all(b - a >= 3.9 for a, b in zip(widths, widths[1:])), "Stufen ≥ 2 mm je Seite")
        self.assertEqual({sw[i]["shape"] for i in ("spine_rail", "blade", "blade_edge")}, {"prof"})
        self.assertEqual(gl["blade"]["shape"], "xprof")
        pts = gl["blade"]["pts"]
        back = max(q[0] for q in pts if q[1] == 0) - min(q[0] for q in pts if q[1] == 0)
        top_u = max(q[1] for q in pts)
        tip = max(q[0] for q in pts if q[1] == top_u) - min(q[0] for q in pts if q[1] == top_u)
        self.assertGreaterEqual(back, 3 * tip, "Keil: Rückenfläche mindestens dreimal so breit wie oben")
        self.assertLess(iou(self.data["e16"]["PARTS"], self.data["e17"]["PARTS"]), 0.5)
        # Gegenproben: die Regeln trennen – die Glefe verfehlt die Klingenregel, das Schwert die Schaftregel, BASIC-16 (Zweihand)
        # die Einhandregel
        gl_blade = max(q[0] for q in extended.bounds(gl["blade"])[1:]) - extended.bounds(gl["blade"])[0][0]
        self.assertLess(gl_blade / gl_len, 0.70)
        self.assertLess((grip[1][0] - grip[0][0]) / sw_len, 0.60)
        b16_grip = next(p for p in self.basic["e16"]["PARTS"] if p["id"] == "grip")
        self.assertGreater(b16_grip["a1"] - b16_grip["a0"], 130)

    def test_negative_space(self):
        """Negativraum als echte Lücke der Seitensilhouette: Schwert Handraum im Bügel, Glefe Fenster der Laterne."""
        sword, glaive = holes(self.data["e16"]["PARTS"]), holes(self.data["e17"]["PARTS"])
        self.assertGreaterEqual(len(sword), 1)
        self.assertGreater(sword[0], 3000, "Handraum ≥ 30 cm² in der Seite")
        self.assertGreaterEqual(len(glaive), 2, "Fenster über und unter den Spulen")
        # Gegenproben: ohne Bügel kein Handraum; ohne Fensterschnitt keine Laternenlücke
        self.assertEqual(holes([p for p in self.data["e16"]["PARTS"] if p["id"] != "bow"])[:1], [])
        shut = copy.deepcopy(self.data["e17"]["PARTS"])
        for p in shut:
            if p["id"] in ("lantern", "shield_l", "shield_r"):
                p["cuts"] = [c for c in p.get("cuts", []) if c.get("shape") != "box"]
        self.assertLess(len(holes(shut)), len(glaive))
        self.assertEqual(holes(self.basic["e16"]["PARTS"]), [])   # BASIC-16 hat keinen Negativraum in der Seite

    def test_lettering(self):
        carriers = {"e16": "guard_panel_r", "e17": "housing_base"}
        for k, cid in carriers.items():
            with self.subTest(k):
                t, c = self.ids[k]["text_r"], self.ids[k][cid]
                self.assertEqual(t["side"], -1)
                self.assertEqual(lettering_problems(t, c), [])
                self.assertEqual(lettering_problems(dict(t, f=t["f"] + 200), c), ["über den Rand"])   # Gegenprobe
                self.assertEqual(lettering_problems(dict(t, x=t["x"] - 3), c), ["nicht auf der Seitenfläche"])

    def test_shield_wings_mirror(self):
        sl, sr = self.ids["e17"]["shield_l"], self.ids["e17"]["shield_r"]
        self.assertEqual(sl["x"], -sr["x"])
        self.assertEqual(sl["move"]["range_deg"], tuple(-a for a in sr["move"]["range_deg"]))
        self.assertGreater(sl["move"]["expect"][1][2], 0)   # links nach außen (x > 0)
        self.assertLess(sr["move"]["expect"][1][2], 0)
        # Fenster der Flügel deckt sich mit dem der Laterne (sonst schlösse ein Flügel den Negativraum)
        lw = next(c for c in self.ids["e17"]["lantern"]["cuts"] if c.get("shape") == "box")
        for s in (sl, sr):
            sw = s["cuts"][0]
            self.assertEqual((sw["f0"], sw["f1"], sw["u0"], sw["u1"]), (lw["f0"], lw["f1"], lw["u0"], lw["u1"]))

    def test_proportions(self):
        for k, d in self.data.items():
            with self.subTest(k):
                self.assertAlmostEqual(length(d["PARTS"]) / 1000, d["META"]["reference_length_m"], delta=0.005)
        self.assertLess(length(self.data["e16"]["PARTS"]), length(self.data["e17"]["PARTS"]) * 0.75)

    def test_sheet_ids(self):
        """Blatt-IDs EA16/EA17 (Schema E<Linie><NN>, Nutzerentscheid 23.11.2026): Register = META, eindeutig, kein Zusammenstoß."""
        from formgen import variants
        from formgen.robot import lines
        sids = list(extended.SHEETS.values())
        for k, n in KEYS.items():
            self.assertEqual(extended.sheet_id(k), f"EA{n}")
            self.assertEqual(self.data[k]["META"]["sheet_id"], f"EA{n}")
            self.assertRegex(extended.sheet_id(k), f"^{extended.SHEET_PATTERN}$")
        self.assertEqual(set(extended.SHEETS), set(extended.MODELS))
        self.assertEqual(len(set(sids)), len(sids), "Blatt-IDs doppelt")
        self.assertEqual((set(variants.sheets()) | set(lines.sheets())) & set(sids), set())
        self.assertIsNone(re.match(f"^{extended.SHEET_PATTERN}$", "EA160"))   # Gegenprobe: dreistellig abgelehnt

    def test_source_hash(self):
        for k, n in KEYS.items():
            with self.subTest(k):
                a = extended.source(k, SNAP)
                self.assertEqual(a, extended.source(k, SNAP))
                self.assertIn(f"formgen/models/extended/{extended.MODELS[k]}.py", a["files"])
                self.assertIn("basic/common.py", a["files"])
                self.assertFalse(any(f.startswith("basic/weapons/") or f.startswith("basic/pilot/") for f in a["files"]),
                                 "kein Umbau eines BASIC-Moduls")
        self.assertNotEqual(extended.source("e16", SNAP)["source_sha256"], extended.source("e17", SNAP)["source_sha256"])

    def test_sword_blade_geometry(self):
        """Schwung: Rücken steigt monoton bis zum Clip, Schneide liegt immer unter dem Rücken, Stufen laufen in die Spitze."""
        sw = self.ids["e16"]
        spine = sorted((q for q in sw["blade"]["pts"]), key=lambda q: q[0])
        top = {}
        for f, u in sw["blade"]["pts"]:
            top[f] = max(top.get(f, -1e9), u)
        fs = sorted(top)
        clip = max(f for f in fs if f <= 860)
        rising = [top[f] for f in fs if 130 <= f <= clip]
        self.assertTrue(all(b >= a for a, b in zip(rising, rising[1:])), "Rücken steigt")
        self.assertGreater(rising[-1] - rising[0], 40, "Stich ≥ 40 mm")
        tip = max(spine, key=lambda q: q[0])
        self.assertLess(tip[1], max(rising), "Clip: Spitze unter dem höchsten Rückenpunkt")
        self.assertTrue(math.isclose(max(q[0] for q in sw["blade_edge"]["pts"]), tip[0]), "Schneide läuft in die Spitze")


@unittest.skipIf(SNAP is None, REASON)
class TestRenderAdditions(unittest.TestCase):
    """0.20 additiv in `tools/extended_render.py`: Vergleich mit einer BASIC-Referenz (`--ref`) und Detailausschnitte für Langformen."""

    def setUp(self):
        import argparse
        import tempfile
        from pathlib import Path
        from PIL import Image
        saved = list(sys.path)
        self.addCleanup(lambda: sys.path.__setitem__(slice(None), saved))
        sys.path.insert(0, str(extended.ROOT / "tools"))
        self.er = importlib.import_module("extended_render")
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        self.ref, self.out = root / "B16", root / "e16"
        for d in (self.ref, self.out / "r1"):
            d.mkdir(parents=True)
            for v in ("hero", "side_left", "side", "front", "top"):
                Image.new("RGB", (160, 90), "#777").save(d / f"{v}.png")
        self.a = argparse.Namespace(out=self.out, tag="r1", ref=self.ref)

    def test_compare_and_details(self):
        from PIL import Image
        self.er.compare_ref("e16", self.a)
        cmp = Image.open(self.out / "r1" / "vergleich_B16.png")
        self.assertEqual(cmp.size[1], 4 * (450 + 34) + 16, "vier Ansichtspaare")
        self.er.details("e16", self.a)
        made = sorted(p.name for p in (self.out / "r1").glob("detail_*.png"))
        self.assertEqual(made, [f"detail_{i + 1}_{v}.png" for i, (v, _) in enumerate(self.er.DETAIL["e16"])])
        self.assertNotIn("e01", self.er.DETAIL, "e01 unverändert: keine Ausschnitte")
        # Gegenprobe: fehlt eine Ansicht in der Referenz, fällt nur dieses Paar weg
        (self.ref / "top.png").unlink()
        self.er.compare_ref("e16", self.a)
        self.assertEqual(Image.open(self.out / "r1" / "vergleich_B16.png").size[1], 3 * (450 + 34) + 16)

    def test_e01_defaults_unchanged(self):
        """Die 0.15-Vorgaben bleiben: Standardordner 0.15, Ansichten, Wrapper (Stempel von e01 gelten weiter)."""
        self.assertTrue(str(self.er.OUT).endswith("0.15/belege"))
        self.assertEqual(self.er.VIEWS, ("hero", "hero_p", "side_left", "side", "top", "front", "rear"))
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), self.assertRaises(SystemExit):
            self.er.main(["--help"])
        self.assertIn("--ref", buf.getvalue())
        self.assertIn("--out", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
