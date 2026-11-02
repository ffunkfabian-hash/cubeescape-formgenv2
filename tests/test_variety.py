"""Variantenbaukasten 0.4: gesteuerter Zufall, Bausteine aus BALLON, v2.1-Grundform, Vielfalt und Designvertrag."""
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

    def test_six_to_eight_lines_with_frozen_ids(self):
        letters = [v["letter"] for v in self.entries]
        self.assertTrue(6 <= len(letters) <= 8, letters)
        self.assertEqual(letters[:3], ["A", "B", "C"])
        self.assertEqual([v["name"] for v in self.entries[:3]], ["Baseline", "Long Reach", "Close Quarters"])
        self.assertEqual({v["skin"] for v in self.entries}, set(variants._skins()), "alle BALLON-Skins im Einsatz")

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
            if generator._in_band(before):
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
