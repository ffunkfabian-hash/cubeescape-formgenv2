"""Variantenbaukasten 0.4: gesteuerter Zufall, Bausteine aus BALLON, v2.1-Grundform, Vielfalt und Designvertrag; 0.6 Pilot-Grundform."""
import hashlib
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

import numpy as np

from formgen import ballon, generator, geom, model, variants, variety
from formgen.cache import canonical

ROOT = Path(__file__).resolve().parents[1]
try:
    SNAP = ballon.snapshot()
except ballon.BallonError as error:   # z. B. Cloud ohne BALLON-Checkout
    SNAP, REASON = None, str(error)
else:
    REASON = ""
BASE = {"letter": "A", "name": "Baseline", "idea": "x", "since": "0.2", "skin": "standard", "params": {}}


class SeedTests(unittest.TestCase):
    def test_seed_depends_only_on_sheet_and_line(self):
        self.assertRegex(variants.seed("BE01"), r"^[0-9a-f]{16}$")
        self.assertEqual(variants.seed("BE01"), variants.seed("BE01"))
        self.assertNotEqual(variants.seed("BE01"), variants.seed("BF01"))
        self.assertNotEqual(variants.seed("BE01"), variants.seed("BE02"))

    def test_draws_stay_in_range_and_follow_precision_rule(self):
        params = {"front": [0.9, 1.1], "glow": [0, 2], "sight": list(variants.HOLO + variants.SCOPES), "stock": "S2"}
        seen = set()
        for num in ballon.TYPES:
            values, draws = variants.resolve(params, f"BJ{num}")
            self.assertTrue(0.9 <= values["front"] <= 1.1 and values["glow"] in (0, 1, 2))
            self.assertEqual(values["stock"], "S2"); self.assertNotIn("stock", draws)   # fester Wert ist keine Ziehung
            self.assertIn(values["sight"], variants.SCOPES if num in variants.PRECISION else variants.HOLO)
            seen.add(values["sight"])
        self.assertGreater(len(seen), 4, "Auswahl streut über die Bausteine")
        values, _ = variants.resolve({"sight": ["lang"]}, "BJ01")
        self.assertIsNone(values["sight"])                   # Zielfernrohr nur 03/09/11: Schritt entfällt

    def test_new_parameter_does_not_shift_other_draws(self):
        a, _ = variants.resolve({"front": [0.8, 1.2]}, "BJ05")
        b, _ = variants.resolve({"front": [0.8, 1.2], "mag": [0.7, 1.4]}, "BJ05")
        self.assertEqual(a["front"], b["front"])

    @unittest.skipIf(SNAP is None, REASON)
    def test_generated_models_are_bit_identical_across_hash_seeds(self):
        """Seed im Spec, Ergebnis bitgleich mit PYTHONHASHSEED 1 und 42 (alle Linien × Typen, Autorenmodell und Bericht)."""
        code = ("import hashlib;from formgen import ballon,generator,variants;from formgen.cache import canonical;"
                "s=ballon.snapshot();h=hashlib.sha256()\n"
                "for v in variants.load():\n"
                " for n in v['types']:h.update(canonical(generator.build(v,n,s)))\n"
                "print(h.hexdigest())")
        values = [subprocess.check_output([sys.executable, "-c", code], cwd=ROOT, env={**os.environ, "PYTHONHASHSEED": seed})
                  for seed in ("1", "42")]
        self.assertEqual(values[0], values[1])


@unittest.skipIf(SNAP is None, REASON)
class KitTests(unittest.TestCase):
    def test_trestle_h0_sits_on_bri22_above_flat_crown_and_is_shown(self):
        from formgen.build import select_document
        entry = variants.sheets()["BT01"]
        author, _ = generator.build(entry["variant"], entry["num"], SNAP)
        document = geom.evaluate(model.normalize(author))
        parts = document["parts"]
        crown = next(part for part in parts if part["id"] == "crown")
        lo, hi = np.array(crown["bounds_m"])
        # Scheitel bleibt eben; BRI-22 und H0 stehen gemäß Variante A darüber.
        self.assertAlmostEqual(hi[2], 0.132)
        body = [part for part in parts if part["id"] != "rail" and not part["id"].startswith("sight_")]
        self.assertAlmostEqual(max(part["bounds_m"][1][2] for part in body), hi[2])
        rail = next(part for part in parts if part["id"] == "rail")
        self.assertAlmostEqual(rail["bounds_m"][0][2], 0.1315)
        self.assertAlmostEqual(rail["bounds_m"][1][2], 0.140)
        self.assertLessEqual(rail["bounds_m"][0][2], hi[2])
        self.assertGreater(rail["bounds_m"][1][2], hi[2])
        foot = next(part for part in parts if part["id"] == "sight_mount")
        self.assertAlmostEqual(foot["bounds_m"][0][2] - rail["bounds_m"][1][2], 0.0005)
        self.assertGreater(foot["bounds_m"][1][2], rail["bounds_m"][1][2])
        hero = {p["id"] for p in select_document(document, "hero")["parts"]}
        self.assertTrue({"rail", "sight_mount", "sight_glass", "sight_frame"} <= hero)
        self.assertFalse(any(key.startswith("optic_") for key in hero))
        face = next(part for part in parts if part["id"] == "face")["mesh"]
        front = geom._as_manifold(face["vertices"], face["faces"])
        self.assertTrue(front.ray_cast((0, -0.44, 0.061), (0, -0.40, 0.061)),
                        "Variante A behält die geschlossene Front auf Laufachse u84")
        mesh = crown["mesh"]
        surface = geom._as_manifold(mesh["vertices"], mesh["faces"])
        for fx in (0.1, 0.5, 0.9):
            for fy in (0.15, 0.5, 0.85):
                x, y = lo[:2] + (hi[:2] - lo[:2]) * [fx, fy]
                hits = surface.ray_cast((x, y, hi[2] + 0.01), (x, y, lo[2] - 0.01))
                self.assertTrue(hits, (x, y))
                self.assertAlmostEqual(hits[0].position[2], hi[2])

    def test_trestle_width_matches_basic_01_including_kit(self):
        entry = variants.sheets()["BT01"]
        author, _ = generator.build(entry["variant"], entry["num"], SNAP)
        parts = geom.evaluate(model.normalize(author))["parts"]
        bounds = np.asarray([part["bounds_m"] for part in parts])
        extent_mm = 1000 * (bounds[:, 1].max(axis=0) - bounds[:, 0].min(axis=0))
        # BA01-Spec: 52,2 mm über alle Teile. Länge und Höhe vom freigegebenen BT01.
        np.testing.assert_allclose(extent_mm, [52.2, 704.24, 260.65], rtol=0, atol=0.1)

    def test_vesper_width_matches_basic_02_and_front_steps_inward(self):
        entry = variants.sheets()["BT02"]
        author, _ = generator.build(entry["variant"], entry["num"], SNAP)
        parts = geom.evaluate(model.normalize(author))["parts"]
        bounds = {p["id"]: np.asarray(p["bounds_m"]) * 1000 for p in parts}
        # Quelle: Gesamtbreite BA02 am GLB. Beide Außenkanten zählen einschließlich Beschriftung.
        all_bounds = np.array(list(bounds.values()))
        np.testing.assert_allclose([all_bounds[:, 0, 0].min(), all_bounds[:, 1, 0].max()],
                                   [-25.5, 25.5], atol=0.05, rtol=0)
        # In den zwei Fugen zwischen den drei Deckschalen bleibt der schmalere Kern sichtbar.
        segments = ["pulse_mantle", "pulse_middle", "pulse_front"]
        for rear, front in zip(segments, segments[1:]):
            gap = bounds[rear][0, 1] - bounds[front][1, 1]
            self.assertGreaterEqual(gap, 9.0)
        core_width = np.ptp(bounds["well_floor"][:, 0])
        self.assertAlmostEqual(core_width, 34.0, delta=0.1)
        for key in segments:
            self.assertAlmostEqual(np.ptp(bounds[key][:, 0]), 48.0, delta=0.1)
        front_widths = [np.ptp(bounds[key][:, 0]) for key in ("front_gasket", "front_mask", "front_glaze")]
        np.testing.assert_allclose(front_widths, [40, 34, 27], atol=0.1, rtol=0)

    def test_heron_total_width_matches_basic_03_including_the_scope(self):
        entry = variants.sheets()["BT03"]
        author, _ = generator.build(entry["variant"], entry["num"], SNAP)
        meshes = geom.evaluate(model.normalize(author))["parts"]
        bounds = np.asarray([p["bounds_m"] for p in meshes]) * 1000
        # Die beidseitigen Keilfelder bestimmen das Außenmaß. Auch Schrift und Z1 zählen mit.
        np.testing.assert_allclose([bounds[:, 0, 0].min(), bounds[:, 1, 0].max()], [-23.5, 23.5],
                                   rtol=0, atol=0.01)
        self.assertEqual({p["id"] for p in meshes if max(abs(v[0]) for v in p["bounds_m"]) >= 0.02349},
                         {"fore_chevron_l", "fore_chevron_r"})

    def test_cairn_width_matches_basic_04_across_both_medallions(self):
        widths = {}
        for sid in ("BA04", "BT04"):
            entry = variants.sheets()[sid]
            author, _ = generator.build(entry["variant"], entry["num"], SNAP)
            meshes = geom.evaluate(model.normalize(author))["parts"]
            bounds = np.asarray([part["bounds_m"] for part in meshes]) * 1000
            widths[sid] = bounds[:, 1, 0].max() - bounds[:, 0, 0].min()
            if sid == "BT04":
                self.assertEqual({p["id"] for p in meshes
                                  if max(abs(v[0]) for v in p["bounds_m"]) >= 0.02241},
                                 {"coin_l", "coin_r"})
        self.assertAlmostEqual(widths["BT04"], 44.83, delta=0.005)
        self.assertAlmostEqual(widths["BA04"], widths["BT04"], delta=0.005)

    def test_swift_width_matches_basic_05_across_the_grip_inlays(self):
        widths = {}
        for sid in ("BA05", "BT05"):
            entry = variants.sheets()[sid]
            author, _ = generator.build(entry["variant"], entry["num"], SNAP)
            parts = geom.evaluate(model.normalize(author))["parts"]
            bounds = np.asarray([p["bounds_m"] for p in parts]) * 1000
            widths[sid] = bounds[:, 1, 0].max() - bounds[:, 0, 0].min()
            if sid == "BT05":
                self.assertEqual({p["id"] for p in parts if max(abs(v[0]) for v in p["bounds_m"]) >= .01674},
                                 {"palm_wing_l", "palm_wing_r"})
        self.assertAlmostEqual(widths["BT05"], 33.50, delta=.005)
        self.assertAlmostEqual(widths["BT05"], widths["BA05"], delta=.005)

    def test_skiff_and_basic_08_have_the_same_full_width(self):
        for sid in ("BA08", "BT08"):
            with self.subTest(sid=sid):
                entry = variants.sheets()[sid]
                author, _ = generator.build(entry["variant"], entry["num"], SNAP)
                parts = geom.evaluate(model.normalize(author))["parts"]
                bounds = np.array([p["bounds_m"] for p in parts]) * 1000
                np.testing.assert_allclose([bounds[:, 0, 0].min(), bounds[:, 1, 0].max()],
                                           [-26, 26], rtol=0, atol=.005)
                if sid == "BT08":
                    outer = {p["id"] for p in parts if max(abs(v[0]) for v in p["bounds_m"]) >= .02599}
                    self.assertEqual(outer, {"cheek_l", "cheek_r"})

    def test_lark_preserves_the_asymmetric_basic_07_width_including_the_b1(self):
        for sid in ("BA07", "BT07"):
            with self.subTest(sid=sid):
                entry = variants.sheets()[sid]
                author, _ = generator.build(entry["variant"], entry["num"], SNAP)
                parts = geom.evaluate(model.normalize(author))["parts"]
                low, left_part = min((p["bounds_m"][0][0], p["id"]) for p in parts)
                high, right_part = max((p["bounds_m"][1][0], p["id"]) for p in parts)
                height = max(p["bounds_m"][1][2] for p in parts) - min(p["bounds_m"][0][2] for p in parts)
                self.assertAlmostEqual(height * 1000, {"BA07": 1015.67, "BT07": 904.72}[sid], delta=.01)
                self.assertEqual((left_part, right_part), ("sight_pin_screws", "riser"))
                np.testing.assert_allclose([low * 1000, high * 1000], [-24.52, 44.25], rtol=0, atol=.005)

    def test_tern_total_width_matches_basic_06(self):
        for sid in ("BA06", "BT06"):
            with self.subTest(sid=sid):
                entry = variants.sheets()[sid]
                author, _ = generator.build(entry["variant"], entry["num"], SNAP)
                parts = geom.evaluate(model.normalize(author))["parts"]
                bounds = np.asarray([p["bounds_m"] for p in parts]) * 1000
                self.assertAlmostEqual(bounds[:, 1, 0].max() - bounds[:, 0, 0].min(), 47., delta=.005)
                if sid == "BT06":
                    outer = {p["id"] for p in parts if max(abs(v[0]) for v in p["bounds_m"]) >= .02349}
                    self.assertEqual(outer, {"shoulder_l", "shoulder_r"})

    def test_trestle_front_window_and_nameplate_have_depth(self):
        entry = variants.sheets()["BT01"]
        author, _ = generator.build(entry["variant"], entry["num"], SNAP)
        parts = {p["id"]: p for p in geom.evaluate(model.normalize(author))["parts"]}
        for case, inset, through in (("fore_cuff", "louvre_2", True), ("flank", "badge", False)):
            mesh = parts[case]["mesh"]
            shell = geom._as_manifold(mesh["vertices"], mesh["faces"])
            for side, suffix in ((1, "l"), (-1, "r")):
                lo, hi = np.array(parts[inset + "_" + suffix]["bounds_m"])
                _, y, z = (lo + hi) / 2
                outer = max(side * lo[0], side * hi[0])
                self.assertLess(outer, parts[case]["bounds_m"][1][0])
                hits = shell.ray_cast((side * 0.05, y, z), (-side * 0.05, y, z))
                if through:
                    self.assertFalse(hits, "Die Lamelle muss durch das Schalenfenster sichtbar sein")
                else:
                    self.assertTrue(hits, "Die Tasche des Typenschilds braucht einen Boden")
                    self.assertLess(side * hits[0].position[0], outer)

    def gen(self, num, base="standard", **params):
        return generator.build(dict(BASE, letter="J", name="Probe", base=base, params=params), num, SNAP)

    def test_sight_swap_uses_ballon_block_and_replaces_anchors(self):
        author, report = self.gen("02", sight="zinken")
        op = report["ops"][0]
        self.assertNotIn("skipped", op)
        ids = {p["id"] for p in author["PARTS"]}
        self.assertTrue(set(op["added"]) <= ids and not set(op["removed"]) - set(op["added"]) & ids)
        ref, _ = ballon.call(SNAP, "zinken", op["f_mm"], 141 + 8 - 8, size="M", weapon_type="pulse_rifle")   # Schiene u1 = 141
        self.assertEqual([p["id"] for p in ref], op["added"])
        eye = author["ANCHORS"]["Socket_Eye"]
        self.assertIn(eye["part"], ids)
        self.assertTrue(60 <= eye["at"][1] - author["ANCHORS"]["Socket_Muzzle"]["at"][1] <= 80)
        mount = next(p for p in author["PARTS"] if p["id"] == "sight_mount")
        rail = next(p for p in author["PARTS"] if p["id"] == "rail")
        self.assertEqual(mount["iface"] if "iface" in mount else "BRI-22", "BRI-22")
        lo, hi = generator._extent(mount)
        self.assertTrue(rail["f0"] <= lo and hi <= rail["f1"], "Klemmfuß sitzt auf der Schiene")

    def test_scope_only_on_precision_types(self):
        _, report = self.gen("03", sight="scope_tropfen")
        self.assertNotIn("skipped", report["ops"][0])
        self.assertEqual(report["contract"]["variant"]["sight_line_mm"], generator.SCOPE_LINE_MM)
        with self.assertRaises(variants.VariantError):
            variants.check([dict(BASE, params={"sight": "fernrohr"})])
        values, _ = variants.resolve({"sight": "scope_tropfen"}, "BJ01")
        self.assertIsNone(values["sight"])

    def test_stock_swap_keeps_interface_point(self):
        author, report = self.gen("01", stock="S2", stock_scale=1.1)
        op = report["ops"][0]
        self.assertEqual((op["from"], op["kind"]), ("S1", "S2"))
        stock = next(p for p in author["PARTS"] if p["id"] == "stock")
        self.assertEqual(stock["mat"], "graphite")                                     # S2: einteilige Graphit-Schulterstütze
        self.assertEqual(tuple(stock["pts"][0]), (op["receiver_rear_f_mm"] + 2, op["bore_u_mm"] - 40))
        self.assertEqual((op["receiver_rear_f_mm"], op["bore_u_mm"]), (-120, 106))   # BASIC-01: stock_s1(-120, BORE=106)
        back, report2 = self.gen("01", stock="S1", stock_scale=1.0)
        raw = {p["id"]: p for p in ballon.load(SNAP, "01")["PARTS"]}
        for p in back["PARTS"]:
            if p["asm"] == "stock":
                self.assertEqual(p["pts" if "pts" in p else "f0"], raw[p["id"]]["pts" if "pts" in p else "f0"], p["id"])

    def test_grip_swap_only_for_plain_grip_rifle(self):
        author, report = self.gen("01", grip="v21")
        self.assertIn("grip_cap", report["ops"][0]["added"])
        self.assertEqual(next(p for p in author["PARTS"] if p["id"] == "grip")["mat"], "rubber")
        self.assertIn("skipped", self.gen("06", grip="v21")[1]["ops"][0])   # geneigter Griff (TILT) ist kein grip_rifle(top)

    def test_mag_stretch_along_removal_direction(self):
        base, _ = self.gen("01")
        author, report = self.gen("01", mag=1.3)
        op = report["ops"][0]
        d = np.array(op["direction"])
        old = {p["id"]: np.array(p["pts"], float) for p in base["PARTS"] if p["id"].startswith("magazine") and "pts" in p}
        for p in author["PARTS"]:
            if p["id"] in old:
                moved = np.array(p["pts"], float) - old[p["id"]]
                for m in moved:
                    self.assertTrue(np.allclose(m, 0) or np.allclose(m, d * op["delta_mm"], atol=1e-3), p["id"])
        self.assertAlmostEqual(op["delta_mm"], 0.3 * op["length_mm"], places=2)
        self.assertEqual(author["ANCHORS"]["Socket_MagWell"], base["ANCHORS"]["Socket_MagWell"])

    def test_muzzle_moves_socket_by_delta(self):
        base, _ = self.gen("01")
        author, report = self.gen("01", muzzle=1.6, muzzle_r=1.2)
        op = report["ops"][0]
        self.assertAlmostEqual(op["delta_mm"], 0.6 * 50)                                # barrel(…, muzzle_len=50)
        self.assertAlmostEqual(author["ANCHORS"]["Socket_Muzzle"]["at"][0], base["ANCHORS"]["Socket_Muzzle"]["at"][0] + op["delta_mm"])
        self.assertAlmostEqual(next(p for p in author["PARTS"] if p["id"] == "muzzle")["r"], 15 * 1.2)

    def test_limbs_lengthen_bow_symmetrically(self):
        base, _ = self.gen("07")
        author, report = self.gen("07", limbs=1.2)
        sides = report["ops"][0]["sides"]
        self.assertEqual([s["side"] for s in sides], ["oben", "unten"])
        self.assertAlmostEqual(sides[0]["delta_mm"], sides[1]["delta_mm"])
        tip = lambda a: {p["id"]: p for p in a["PARTS"]}["cam_top"]["c"][1]  # noqa: E731
        self.assertAlmostEqual(tip(author) - tip(base), sides[0]["delta_mm"], places=2)
        string = {p["id"]: p for p in author["PARTS"]}["string_top"]["move"]
        self.assertAlmostEqual(string["tip"][1] - 505, sides[0]["delta_mm"], places=2)            # TIP_U = 505 in w07
        self.assertEqual(string["nock"][1], 46)                                          # Nockpunkt am Pfeil bleibt

    def test_glow_lines_are_energy_parts_on_a_free_side(self):
        author, report = self.gen("02", glow=2)
        op = report["ops"][0]
        self.assertEqual(len(op["added"]), 2)
        for p in author["PARTS"]:
            if p["id"] in op["added"]:
                self.assertEqual((p["mat"], p["parent_part"]), ("energy", op["on"]))

    def test_v21_base_loads_pilot_and_falls_back_for_melee(self):
        author, report = self.gen("10", base="v21")
        self.assertEqual(report["base"], "v21")
        self.assertIn("basic/pilot/w10_fusion_rifle_v21.py", report["ballon"]["files"])
        _, report16 = self.gen("16", base="v21")
        self.assertEqual(report16["base"], "standard")
        self.assertTrue(any(a.get("field") == "base" for a in report16["adaptations"]))

    def test_pilot_base_takes_newest_version_and_marks_form_study(self):
        # 0.6 (Nutzerentscheid 242): `pilot` = neueste Fassung; BASIC-01 hat v2 und v21 → v21
        self.assertEqual(ballon.pilots(SNAP, "01"), ["v2", "v21"])
        author, report = self.gen("01", base="pilot")
        self.assertEqual((report["base"], report["variant"]["base"]), ("v21", "pilot"))
        self.assertFalse(any(a.get("field") == "base" for a in report["adaptations"]))
        self.assertIn(["Grundform", "BASIC-01 „Formstudie 01 v2.1“ · v2.1"], author["INFO"]["facts"])
        author16, report16 = self.gen("16", base="pilot")
        self.assertEqual(report16["base"], "standard")
        self.assertTrue(any(a.get("field") == "base" for a in report16["adaptations"]))
        self.assertTrue(any(k == "Grundform" and v.endswith("· Formstudie – kein Pilot") for k, v in author16["INFO"]["facts"]))

    def test_resolve_base_compares_versions_as_digit_tuples(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            pilot = Path(tmp) / "basic/pilot"
            pilot.mkdir(parents=True)
            for name in ("w01_auto_rifle_v2.py", "w01_auto_rifle_v21.py", "w01_auto_rifle_v3.py", "w02_pulse_rifle_v21.py",
                         "w01_auto_rifle_old.py"):
                (pilot / name).write_text("")
            self.assertEqual(ballon.pilots(tmp, "01"), ["v2", "v21", "v3"])
            self.assertEqual(ballon.resolve_base(tmp, "01", "pilot"), "v3")
            self.assertEqual(ballon.resolve_base(tmp, "01", "v21"), "v21")
            self.assertEqual(ballon.resolve_base(tmp, "03", "pilot"), "standard")
            self.assertEqual(ballon.spec_path(tmp, "01", "v3").name, "BASIC-01-v3.spec.json")
            with self.assertRaises(ballon.BallonError):
                ballon.resolve_base(tmp, "01", "v9x")

    def test_accent_limit_recolours_added_blocks(self):
        _, report = self.gen("01", sight="holo_kasten")          # BASIC-01 hat schon drei Akzent-Bedienfunktionen
        self.assertLessEqual(len(report["contract"]["variant"]["accent_functions"]), 3)
        self.assertTrue(any(a.get("part") == "sight_clamp" and a["v2"] == "sight_anod" for a in report["adaptations"]))


@unittest.skipIf(SNAP is None, REASON)
class RegisterVarietyTests(unittest.TestCase):
    """Über das ganze Register: jede Nicht-Baseline-Linie weicht je Typ sichtbar ab, der Designvertrag hält."""

    @classmethod
    def setUpClass(cls):
        cls.entries = variants.load()
        cls.built = {variants.sheet_id(v["letter"], n): generator.build(v, n, SNAP) for v in cls.entries for n in v["types"]}

    def test_every_line_stands_on_the_newest_pilot(self):
        # Grundform je Linie: 01–15 neuester Pilot (heute v2.1), 16/17 Formstudie mit Kennzeichnung im Blatt
        for v in self.entries:
            self.assertEqual(v["base"], "pilot", v["letter"])
        for sid, (author, report) in self.built.items():
            num = variants.parse_sheet(sid)[1]
            shape = dict(author["INFO"]["facts"])["Grundform"]
            if num in ("16", "17"):
                self.assertEqual(report["base"], "standard", sid)
                self.assertTrue(shape.endswith("· Formstudie – kein Pilot"), sid)
            else:
                self.assertEqual(report["base"], ballon.pilots(SNAP, num)[-1], sid)
                self.assertTrue(shape.endswith("· v2.1"), sid)

    def test_lines_with_frozen_ids(self):
        letters = [v["letter"] for v in self.entries]
        self.assertEqual(letters, list("ABCDEFGHJKLMT"))
        self.assertEqual(letters[:3], ["A", "B", "C"])
        self.assertEqual([v["name"] for v in self.entries[:3]], ["Baseline", "Long Reach", "Close Quarters"])
        self.assertEqual({v["skin"] for v in self.entries}, set(variants._skins()), "alle Skins im Einsatz")

    def test_every_line_differs_visibly_from_baseline(self):
        tris = {sid: variety.triangles(author) for sid, (author, _) in self.built.items()}
        weak = {}
        for sid in tris:
            letter, num = variants.parse_sheet(sid)
            if letter != "A":
                views = variety.iou(tris[f"BA{num}"], tris[sid])
                if not variety.visible(views):
                    weak[sid] = views
        self.assertEqual(weak, {}, f"Silhouetten-IoU (min Seite/oben) > {variety.THRESHOLD}")

    def test_design_contract_holds(self):
        for sid, (_, report) in self.built.items():
            base, mine = report["contract"]["base"], report["contract"]["variant"]
            self.assertLessEqual(len(mine["accent_functions"]), max(generator.ACCENT_LIMIT, len(base["accent_functions"])), sid)
            for socket, role in mine["hand_roles"].items():
                self.assertTrue(role in generator.HAND_ROLES or role == base["hand_roles"].get(socket), (sid, socket, role))
            before, after = base["sight_line_mm"], mine["sight_line_mm"]
            if sid == "BT01":
                # Nutzerentscheid Variante A (24.11.2026): H0 auf der Scheitelleiste,
                # Front unverändert. Nur diese Blatt-ID hat die feste Höhe 105 mm.
                self.assertEqual(after, 105.0, sid)
            elif generator._in_band(before):
                self.assertTrue(generator._in_band(after), (sid, before, after))
            elif after is not None and before is not None:
                self.assertLessEqual(abs(after - 70), abs(before - 70) + 1e-9, (sid, before, after))

    def test_spec_records_seed_and_draws(self):
        for sid, (_, report) in self.built.items():
            self.assertEqual(report["variation"]["seed"], variants.seed(sid))
            ranged = {k for k, v in report["variant"]["params"].items() if isinstance(v, list) and k != "drop"}
            self.assertTrue(set(report["variation"]["draws"]) <= ranged, sid)


class XprofTests(unittest.TestCase):
    def test_xprof_rectangle_matches_box(self):
        info = {"id": "X", "kind": "sight", "provenance": {"kind": "Annahme", "source": "Test"}}
        rect = [(-5, -2), (5, -2), (5, 2), (-5, 2)]
        parts = [{"id": "x", "asm": "a", "mat": "shell", "shape": "xprof", "f0": 0, "f1": 20, "cu": 30, "pts": rect, "bevel": 0},
                 {"id": "b", "asm": "a", "mat": "shell", "shape": "box", "f0": 0, "f1": 20, "u0": 28, "u1": 32, "w": 10, "bevel": 0}]
        doc = geom.evaluate(model.normalize({"INFO": info, "PARTS": parts, "ASSEMBLIES": [{"id": "a"}]}))
        x, b = doc["parts"]
        self.assertTrue(np.allclose(sorted(map(tuple, x["mesh"]["vertices"])), sorted(map(tuple, b["mesh"]["vertices"]))))

    def test_xprof_needs_fields(self):
        with self.assertRaises(model.ModelError):
            model._shape({"shape": "xprof", "f0": 0, "f1": 1, "pts": [(0, 0), (1, 0), (0, 1)]})

    @unittest.skipIf(SNAP is None, REASON)
    def test_all_v21_pilots_evaluate_with_xprof(self):
        used = 0
        for num in ballon.TYPES:
            if not ballon.has_base(SNAP, num, "v21"):
                continue
            author, _ = generator.build(dict(BASE, base="v21"), num, SNAP)
            used += sum(1 for p in author["PARTS"] for q in [p] + p.get("items", []) + p.get("cuts", []) if q.get("shape") == "xprof")
            doc = geom.evaluate(model.normalize(author), booleans=False, bevels=False)
            self.assertTrue(all(p["mesh"]["faces"] for p in doc["parts"]), num)
        self.assertGreater(used, 40)


if __name__ == "__main__":
    unittest.main()
