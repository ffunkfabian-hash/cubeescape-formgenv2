"""Serie DaVinci, DaVinci-01 „Linea“ (0.52 „Atelier“): eigenes Modell im BALLON-Kit-Vokabular mit Signature-Skin „Sfumato“.

Prüft ohne Blender: Felder, IDs und eigenes Blattpräfix; Anker/Weltpunkte (BALLONs `variant.problems` als Orakel); Budgets; Visierlinie;
eigene Silhouette gegen BASIC-01 und alle EXTENDED; Zusammenhang; die beiden Leitmerkmale (Linea mit genau einem Schrägwinkel,
Vesica-Schlossplatte mit Kern an der Spitze statt in der Mitte); geschlossener Negativraum im Daumenlochschaft; gestaltete Querschnitte;
Magazin vor dem Bügel; Detaildichte und Klarheit im Band der Langwaffen (Kanon-Messblock 0.42.2); Rollenanteile und Kontraste des Skins;
Exportstempel ohne Blender. Jede Regel mit Gegenprobe, die aus dem erwarteten Grund anschlägt.
"""
import copy
import importlib
import json
import math
from pathlib import Path
import sys
import tempfile
import tomllib
import unittest

import numpy as np
from scipy import ndimage

from formgen import ballon, davinci, extended, extended_lines, kanon

try:
    SNAP = ballon.snapshot()
except ballon.BallonError as error:   # z. B. Cloud ohne BALLON-Checkout
    SNAP, REASON = None, str(error)
else:
    REASON = ""

IOU_MAX = 0.85                 # Vorgabe Kanon › 2: Seiten-IoU < 0,85 gegen BASIC-NN und jedes EA gleicher Größenklasse
SIGHT_RANGE = (60.0, 80.0)     # Vorgabe Visier-Standard
FRAME = dict(lo=(-420.0, -200.0), size=(1700, 600))   # A: Rahmen für Langwaffen bis f 1280 (EA09, EA11)
SLOPE_DEG = 18.0               # A: der eine Schrägwinkel der Linea
# Kanon-Messblock 0.42.2, Klasse Langwaffe: Grenze Achsen (unteres Quartil), Minimum Richtungen, Teile, Formen, Rundkörper, Rollen, Quader max
BAND = dict(axis=0.66, dirs=0.67, parts=36, forms=41, round=0.22, mats=11, boxy=0.37)


def lights(parts):
    return sorted(p["id"] for p in parts if p["mat"] == "energy")


def accent_functions(parts):
    return sorted({p["id"].removesuffix("_r") for p in parts if p["mat"] == "accent" and p.get("move") and p["asm"] != "sight"})


def graphics(parts):
    """Grafikbänder: Aufdrucke (decal) ohne Schrift und Akzentteile ohne Bewegung außerhalb des Visiers."""
    return sorted(p["id"] for p in parts if p["shape"] != "text" and p["asm"] != "sight"
                  and (p["mat"] == "decal" or (p["mat"] == "accent" and not p.get("move"))))


def slant_angles(parts, longer=40.0):
    """Winkel aller langen Seitenkanten (≥ 40 mm, die Leitlinien; Fasen und Griffrücken BGM-1 sind kürzer), die weder waagerecht noch
    senkrecht sind (Toleranz wie kanon.clarity); gerundet auf 1°."""
    return {round(a) for a, n in kanon._edges(parts) if n >= longer and min(a % 90, 90 - a % 90) >= kanon.AXIS_DEG}


def boxy(p):
    """Wie test_extended_streuung.test_shaped_sections: Querprofil mit < 1,5 mm Breitenänderung oder Seitenprofil ohne Fasen-/Einzugs-
    schnitt (xprof/plan) bzw. mit Radius < R_MID gilt als Quader."""
    shaped = [q for q in p.get("cuts") or () if q.get("shape") in ("xprof", "plan")]
    return not shaped or p.get("bevel", 0) < 3.0


@unittest.skipIf(SNAP is None, REASON)
class TestDaVinci01(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = davinci.load("d01", SNAP)
        cls.parts = cls.data["PARTS"]
        cls.ids = {p["id"]: p for p in cls.parts}
        cls.basic = extended.load_basic("01", SNAP)
        sys.path.insert(0, str(SNAP))
        try:
            cls.mod = importlib.import_module(davinci.module_name("d01"))
            cls.c = {k: getattr(cls.mod, k) for k in ("TOP", "SPLIT", "SLOPE", "VES", "CORE_C", "CORE_R", "HALF", "HOLE", "F_REAR")}
        finally:
            sys.path.remove(str(SNAP))
            extended._purge((davinci.module_name("d01"),))

    # ---------------------------------------------------------------- Felder, IDs, Serie
    def test_fields_and_ids(self):
        for k in ("META", "PARTS", "ASSEMBLIES", "ANCHORS", "POINTS", "ACTIONS"):
            self.assertIn(k, self.data)
        meta = self.data["META"]
        self.assertEqual((meta["id"], meta["series"], meta["type"]), ("DAVINCI-01", "DaVinci", "auto_rifle"))
        self.assertEqual(len(self.ids), len(self.parts), "Teil-IDs doppelt")
        asms = {a["id"] for a in self.data["ASSEMBLIES"]}
        self.assertEqual(asms, {a["id"] for a in self.basic["ASSEMBLIES"]}, "Baugruppen wie die Familie")
        self.assertEqual({p["asm"] for p in self.parts} - asms, set())
        for p in self.parts:
            if p.get("parent_part"):
                self.assertIn(p["parent_part"], self.ids, p["id"])

    def test_own_series_and_sheet_id(self):
        """Nutzerentscheid 27.11.2026: eigene Serie. Präfix D, kein Zusammenstoß mit BASIC (B…), EXTENDED (E…) und Robotern (R…)."""
        import re
        from formgen import variants
        self.assertEqual(davinci.sheet_id("d01"), "DA01")
        self.assertEqual(self.data["META"]["sheet_id"], "DA01")
        self.assertEqual(set(davinci.SHEETS), set(davinci.MODELS))
        self.assertEqual(set(davinci.SKINS), set(davinci.MODELS))
        self.assertTrue(all(re.fullmatch(davinci.SHEET_PATTERN, s) for s in davinci.SHEETS.values()))
        self.assertFalse(set(davinci.MODELS) & set(extended.MODELS), "nicht im EXTENDED-Register")
        others = set(extended.SHEETS.values()) | set(variants.sheets())
        self.assertFalse(set(davinci.SHEETS.values()) & others)
        self.assertFalse(re.fullmatch(davinci.SHEET_PATTERN, "EA01"))   # Gegenprobe: EXTENDED-Blatt passt nicht ins Muster
        self.assertEqual(kanon.klasse("DA01"), "Langwaffe")

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
            self.assertEqual(variant.problems(variant.as_module(copy.deepcopy(self.data))), [])
        finally:
            sys.path.remove(str(SNAP))
            extended._purge()

    def test_family_interfaces(self):
        self.assertEqual((self.ids["grip"]["mat"], self.ids["grip"]["iface"]), ("rubber", "BGM-1"))
        self.assertEqual(self.ids["mag_well"]["iface"], "BMW-R")
        self.assertEqual(self.ids["muzzle"]["iface"], "BMZ-15")
        self.assertEqual(self.ids["rail"]["iface"], "BRI-22")
        self.assertEqual(self.ids["handguard"]["mat"], "graphite")
        self.assertEqual(self.ids["upper"]["mat"], "shell")

    # ---------------------------------------------------------------- Budgets, Visier, Silhouette, Zusammenhang
    def test_budgets(self):
        self.assertLessEqual(len(lights(self.parts)), 3, lights(self.parts))
        self.assertLessEqual(len(accent_functions(self.parts)), 3, accent_functions(self.parts))
        self.assertEqual([p["id"] for p in self.parts if p["shape"] == "text"], ["text_r"])
        self.assertEqual(graphics(self.parts), ["linea_band"])
        extra = self.parts + [dict(self.ids["linea_band"], id="chevron", mat="accent")]   # Gegenprobe: zweites Grafikelement
        self.assertEqual(graphics(extra), ["chevron", "linea_band"])

    def test_sight_line(self):
        bore = self.ids["barrel"]["c"][0]
        eye = self.data["ANCHORS"]["Socket_Eye"]["at"][1]
        self.assertTrue(SIGHT_RANGE[0] <= eye - bore <= SIGHT_RANGE[1], eye - bore)
        self.assertEqual(bore, 106)

    def test_own_silhouette(self):
        """Eigene Form gegen BASIC-01 und alle EXTENDED (Kanon › 2); Gegenprobe: BA01 gegen sich selbst."""
        own = {"BA01": extended.side_iou(self.basic["PARTS"], self.parts)}
        for key in extended.MODELS:   # gleiche Größenklasse (Kanon › 2); Nahkampfwaffen sprengen den Messrahmen
            if kanon.klasse(extended.sheet_id(key)) == "Langwaffe":
                own[extended.sheet_id(key)] = extended.side_iou(extended.load(key, SNAP)["PARTS"], self.parts, **FRAME)
        self.assertLess(max(own.values()), IOU_MAX, max(own.items(), key=lambda kv: kv[1]))
        self.assertGreaterEqual(extended.side_iou(self.basic["PARTS"], self.basic["PARTS"]), 0.99)

    def test_no_floating_parts(self):
        self.assertEqual(len(extended.components(self.parts)), 1, extended.components(self.parts)[1:])
        moved = copy.deepcopy(self.parts)   # Gegenprobe: Kernrahmen 40 mm nach außen → eigene Gruppe
        next(p for p in moved if p["id"] == "core_frame").update(a0=60, a1=63)
        self.assertGreater(len(extended.components(moved)), 1)

    def test_proportions(self):
        f = [b for p in self.parts if (b := extended.bounds(p))]
        length = max(b[1][0] for b in f) - min(b[0][0] for b in f)
        self.assertAlmostEqual(length / 1000, self.data["META"]["reference_length_m"], delta=0.005)

    # ---------------------------------------------------------------- Leitmerkmale
    def test_linea(self):
        """Eine gerade Oberlinie: Schale, Schaft und Nasenkappe enden oben auf TOP; genau ein Schrägwinkel (18°) in allen Seitenkanten
        der tragenden Körper, gespiegelt um den Griff. Gegenprobe: ein zweiter Winkel (Schaftrücken fällt um 10 mm) wird gemeldet."""
        top = self.c["TOP"]
        for pid in ("upper", "stock", "nose_cap"):
            self.assertEqual(max(u for _, u in self.ids[pid]["pts"]), top, pid)
        main = [self.ids[pid] for pid in ("upper", "lower", "handguard", "nose_cap", "stock")]
        angles = slant_angles(main)
        self.assertEqual(angles, {round(SLOPE_DEG), round(180 - SLOPE_DEG)})   # Nase steigt nach vorn, Strebe nach hinten, gespiegelt
        self.assertAlmostEqual(math.degrees(math.atan(self.c["SLOPE"])), SLOPE_DEG)
        bent = copy.deepcopy(main)
        stock = bent[-1]
        stock["pts"] = [(f, u - 10 if f == min(q[0] for q in stock["pts"]) and u == top else u) for f, u in stock["pts"]]
        self.assertNotEqual(slant_angles(bent) - slant_angles(main), set())

    def test_vesica_and_core(self):
        """Schlossplatte ist ein Spitzoval (spitze Enden, symmetrisch); der Kern sitzt an der vorderen Spitze, nicht in der Mitte (Runde 1:
        mittig las es sich als Auge). Gegenprobe: Kern in die Mitte gesetzt."""
        v, core = self.c["VES"], self.c["CORE_C"]
        pts = self.ids["plate_l"]["pts"]
        fs = [f for f, _ in pts]
        self.assertAlmostEqual(min(fs), v["fc"] - v["length"] / 2, delta=0.01)
        self.assertAlmostEqual(max(fs), v["fc"] + v["length"] / 2, delta=0.01)
        self.assertAlmostEqual(max(u for _, u in pts) - v["uc"], v["uc"] - min(u for _, u in pts), delta=0.01)

        def eye_like(c):
            return abs(c[0] - v["fc"]) < 0.3 * v["length"]
        self.assertFalse(eye_like(core))
        self.assertTrue(eye_like((v["fc"], v["uc"])))
        self.assertLess(abs(core[0] - (v["fc"] + v["length"] / 2)), self.c["CORE_R"] + 3, "Plattenspitze unter dem Rahmen")
        self.assertEqual(lights([self.ids["core_glow"]]), ["core_glow"])
        self.assertGreater(self.ids["core_glow"]["a1"], 0, "Kern links (Blickfang zur Hero-Kamera)")

    def test_thumbhole_closed(self):
        """Negativraum: der Durchbruch im Schaft ist ringsum geschlossen (Schleife), mindestens 8 000 mm². Gegenprobe: Strebe weg."""
        def enclosed(parts):
            mask = extended.side_mask(parts)
            labels, n = ndimage.label(~mask)
            border = set(labels[0]) | set(labels[-1]) | set(labels[:, 0]) | set(labels[:, -1])
            return max([int((labels == i).sum()) for i in range(1, n + 1) if i not in border] or [0])
        self.assertGreater(enclosed(self.parts), 8000)
        open_stock = copy.deepcopy(self.parts)
        s = next(p for p in open_stock if p["id"] == "stock")
        s["pts"] = [(f, max(u, 40)) for f, u in s["pts"]]   # Strebe gekappt: Schleife unten offen
        self.assertLess(enclosed(open_stock), 8000)

    def test_shaped_sections(self):
        ids = ("upper", "lower", "handguard", "nose_cap", "stock")
        self.assertEqual([pid for pid in ids if boxy(self.ids[pid])], [])
        self.assertTrue(boxy(dict(self.ids["upper"], cuts=[])))   # Gegenprobe: Schale ohne Fasen/Verjüngung

    def test_magazine_ahead_of_guard(self):
        guard = max(f for f, _ in self.ids["trigger_guard"]["pts"])
        mag = min(f for f, _ in self.ids["magazine"]["pts"])
        self.assertGreater(mag, guard)

    def test_detail_and_clarity_in_band(self):
        row = {**kanon.detail(self.parts), **kanon.clarity(self.parts)}
        problems = [k for k in ("axis", "dirs", "parts", "forms", "round", "mats") if row[k] < BAND[k]]
        problems += ["boxy"] if row["boxy"] > BAND["boxy"] else []
        self.assertEqual(problems, [], row)
        slabs = [dict(self.ids["upper"], id=f"slab{i}", shape="box", f0=0, f1=10, u0=0, u1=10, w=10) for i in range(80)]
        self.assertGreater(kanon.detail(self.parts + slabs)["boxy"], BAND["boxy"])   # Gegenprobe: Plattenhaufen

    def test_source_hash(self):
        a = davinci.source("d01", SNAP)
        self.assertEqual(a, davinci.source("d01", SNAP))
        self.assertIn("formgen/models/davinci/d01_davinci.py", a["files"])
        self.assertIn("basic/common.py", a["files"])
        self.assertNotIn("basic/pilot/w01_auto_rifle_v21.py", a["files"], "kein Umbau von BASIC-01")
        self.assertFalse(any("models/extended" in f for f in a["files"]), "kein Umbau von EXTENDED-01")

    def test_snapshot_released(self):
        self.assertFalse(any(n == "basic" or n.startswith("basic.") for n in sys.modules))
        self.assertNotIn(str(SNAP), sys.path)


@unittest.skipIf(SNAP is None, REASON)
class TestSfumato(unittest.TestCase):
    """Signature-Skin: Hauptfarbe dominiert, Sekundärfarbe deutlich, Akzent sparsam, Leuchte hebt sich ab (Kanon › 5: zwei größte Rollen
    ≥ ΔE 10, Leuchtrolle ≥ ΔE 25 zur Schale)."""

    @classmethod
    def setUpClass(cls):
        cls.parts = davinci.load("d01", SNAP)["PARTS"]
        with (davinci.ROOT / "skins.toml").open("rb") as stream:
            cls.skins = tomllib.load(stream)["skins"]
        cls.style = cls.skins["sfumato"]

    def test_declared(self):
        self.assertEqual(davinci.SKINS["d01"], "sfumato")
        self.assertTrue(self.style["formgen"])
        self.assertIn("sfumato", extended_lines.skins(), "auch als Finish frei wählbar")

    def test_shares_and_contrast(self):
        shares = extended_lines.role_shares(self.parts)
        ranked = sorted(shares, key=shares.get, reverse=True)
        self.assertEqual(ranked[0], "shell")
        self.assertGreaterEqual(shares["shell"], 0.5, "Hauptfarbe dominiert")
        self.assertGreaterEqual(shares["graphite"] + shares.get("anodized", 0), 0.15, "Sekundärfarbe Elfenbein deutlich")
        self.assertLessEqual(shares.get("accent", 0) + shares.get("trim", 0), 0.05, "Akzent sparsam")
        r = self.style["roles"]
        self.assertGreaterEqual(extended_lines.delta_e(r["shell"], r["graphite"]), 10)
        self.assertGreaterEqual(extended_lines.delta_e(r["energy"], r["shell"]), 25)
        ivory = [dict(p, mat="graphite") if p["id"] == "stock" else p for p in self.parts]   # Gegenprobe: Elfenbein-Schaft (Runde 2)
        self.assertLess(extended_lines.role_shares(ivory)["shell"], 0.5)

    def test_finish(self):
        s = davinci.skin("sfumato")
        self.assertEqual(s["anodized"], {"color": "#E4D9C3", "rough": 0.38, "metal": 0.0})
        self.assertEqual(s["shell"]["color"], self.style["roles"]["shell"])
        self.assertGreater(s["trim"]["metal"], 0.9)
        self.assertLess(s["trim"]["rough"], s["shell"]["rough"], "gebürsteter Champagner glänzt mehr als die Beschichtung")
        std = davinci.skin("standard")
        self.assertEqual(std["anodized"]["metal"], 0.6, "ohne finish gilt die Rolle")


@unittest.skipIf(SNAP is None, REASON)
class TestExportStamp(unittest.TestCase):
    """Export nur bei fehlenden oder veralteten Dateien (Projektregel); Blender wird hier nie gestartet."""

    def test_current(self):
        from formgen import ballon_kit
        data = davinci.load("d01", SNAP)
        want = davinci.stamp("d01", data, ballon_kit.snapshot())
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            files = davinci.outputs("d01", data, target)
            self.assertFalse(davinci.current(target, want, files))
            for f in files:
                f.write_bytes(b"x")
            (target / "export.json").write_text(json.dumps(want))
            self.assertTrue(davinci.current(target, want, files))
            self.assertFalse(davinci.current(target, dict(want, skin_sha256="0"), files))   # Gegenprobe: Skin geändert
            (target / "export.json").write_text(json.dumps(want)[:20])                     # Richter R4: abgeschnittener Stempel
            self.assertFalse(davinci.current(target, want, files))
            (target / "export.json").write_text("")
            self.assertFalse(davinci.current(target, want, files))
            davinci.write_stamp(target / "export.json", want)                              # atomar geschrieben, wieder gültig
            self.assertTrue(davinci.current(target, want, files))
            self.assertEqual([p.name for p in target.iterdir() if p.name.startswith(".export.json")], [], "keine Restdatei")
            files[0].unlink()
            self.assertFalse(davinci.current(target, want, files))                          # Gegenprobe: Datei fehlt


@unittest.skipIf(SNAP is None, REASON)
class TestPreviewStamp(unittest.TestCase):
    """Vorschau nur bei fehlenden oder veralteten Bildern (Richter 0.52, Befund 7); gerendert wird hier nicht."""

    def test_current(self):
        from unittest import mock
        want = davinci.preview_stamp("d01", (40, 20), ("side_left",), SNAP)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            files = davinci.preview_files("d01", out, ("side_left",))
            for f in files:
                f.write_bytes(b"x")
            (out / "preview.json").write_text(json.dumps(want))
            with mock.patch.object(davinci, "evaluate", side_effect=AssertionError("kein Rendern bei passendem Stempel")):
                self.assertEqual(davinci.preview("d01", out, (40, 20), ("side_left",), SNAP), files)
            self.assertFalse(davinci.current(out, dict(want, skin="0"), files, name="preview.json"))   # Gegenprobe: Skin geändert
            self.assertFalse(davinci.current(out, dict(want, size=[80, 40]), files, name="preview.json"))   # Gegenprobe: Größe
            import hashlib   # Richter R6: der Vorschaucode (Clay-Farbe, Bogen) steht im Stempel; geändert → ungültig
            self.assertEqual(want["preview_code"], hashlib.sha256(Path(davinci.__file__).read_bytes()).hexdigest())
            changed = dict(want, preview_code=hashlib.sha256(b"anderer Vorschaucode").hexdigest())
            self.assertFalse(davinci.current(out, changed, files, name="preview.json"))
            with mock.patch.object(davinci, "evaluate", side_effect=RuntimeError("gerendert")):   # Gegenprobe: force rendert
                with self.assertRaisesRegex(RuntimeError, "gerendert"):
                    davinci.preview("d01", out, (40, 20), ("side_left",), SNAP, force=True)

    def test_only_missing_views(self):
        """Richter R5: passt der Stempel und fehlt nur eine Ansicht, wird genau diese gerendert; Gegenprobe: veralteter Stempel → alle."""
        from unittest import mock
        from PIL import Image
        from formgen import raster
        views = ("side_left", "top")
        want = davinci.preview_stamp("d01", (40, 20), views, SNAP)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            files = davinci.preview_files("d01", out, views)
            for f in files:
                Image.new("RGB", (40, 20)).save(f)
            davinci.write_stamp(out / "preview.json", want)
            files[1].unlink()
            calls = []
            fake = lambda ev, view, w, h, skin, **kw: calls.append((skin, view)) or Image.new("RGB", (w, h))   # noqa: E731
            with mock.patch.object(davinci, "evaluate", return_value={"parts": []}), \
                    mock.patch.object(raster, "framing", return_value={"scale": 1.0, "center": [0, 0, 0]}), \
                    mock.patch.object(raster, "render", side_effect=fake):
                davinci.preview("d01", out, (40, 20), views, SNAP)
                self.assertEqual(calls, [("clay", "top")])
                self.assertTrue(davinci.current(out, want, files, name="preview.json"))
                calls.clear()
                davinci.write_stamp(out / "preview.json", dict(want, skin="0"))   # Gegenprobe: veralteter Stempel
                davinci.preview("d01", out, (40, 20), views, SNAP)
                self.assertEqual(len(calls), 4)


if __name__ == "__main__":
    unittest.main()
