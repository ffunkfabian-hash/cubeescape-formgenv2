"""BALLON-Grundlage (Quellhash, Snapshot) und Generator (Grundform = BALLON, Varianten nur über Parameter)."""
import copy
import shutil
import tempfile
import unittest
from pathlib import Path

from formgen import ballon, generator, geom, model, variants

try:
    SNAP = ballon.snapshot()
except ballon.BallonError as error:   # z. B. Cloud ohne BALLON-Checkout
    SNAP, REASON = None, str(error)
else:
    REASON = ""


def evaluated(author):
    return geom.evaluate(model.normalize(author), bevels=True)


def dims(doc):
    vs = [v for p in doc["parts"] for v in p["mesh"]["vertices"]]
    return {k: 1000 * (max(v[i] for v in vs) - min(v[i] for v in vs)) for k, i in (("length", 1), ("height", 2), ("width", 0))}


@unittest.skipIf(SNAP is None, REASON)
class BallonSourceTests(unittest.TestCase):
    def test_closure_covers_module_common_and_packages(self):
        files = ballon.closure(SNAP, "01")
        self.assertEqual(set(files), {"basic/__init__.py", "basic/weapons/__init__.py", "basic/common.py",
                                      "basic/weapons/w01_auto_rifle.py"})

    def test_all_seventeen_types_load_without_bpy(self):
        for num in ballon.TYPES:
            data = ballon.load(SNAP, num)
            self.assertEqual(data["META"]["id"], f"BASIC-{num}")
            self.assertTrue(data["PARTS"])

    def test_source_hash_is_content_only_and_type_local(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy_dir = Path(tmp) / "elsewhere"
            shutil.copytree(SNAP, copy_dir)
            self.assertEqual(ballon.source(copy_dir, "01"), ballon.source(SNAP, "01"))      # Pfad egal
            (copy_dir / "basic/weapons/w02_pulse_rifle.py").write_text("# andere Waffe geändert\n", encoding="utf-8")
            self.assertEqual(ballon.source(copy_dir, "01")["source_sha256"], ballon.source(SNAP, "01")["source_sha256"])
            common = copy_dir / "basic/common.py"
            common.write_text(common.read_text() + "\n# Änderung\n")
            self.assertNotEqual(ballon.source(copy_dir, "01")["source_sha256"], ballon.source(SNAP, "01")["source_sha256"])
            spec = copy_dir / "data/specs/BASIC-01.spec.json"
            spec.write_text(spec.read_text() + " ")
            self.assertNotEqual(ballon.source(copy_dir, "01")["spec_sha256"], ballon.source(SNAP, "01")["spec_sha256"])

    def test_snapshot_rejects_short_commit(self):
        with self.assertRaises(ballon.BallonError):
            ballon.snapshot("dcdda60")


@unittest.skipIf(SNAP is None, REASON)
class GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.variants = {v["letter"]: v for v in variants.load()}
        cls.base = {"letter": "A", "name": "Baseline", "idea": "x", "since": "0.2", "skin": "standard", "params": {}}

    def gen(self, num, **params):
        return generator.build(dict(self.base, params=params), num, SNAP)

    def test_baseline_is_ballon_shape_for_all_types(self):
        """Ohne Parameter ist die Grundform BALLONs exportiertes Modell (Maße aus BALLONs Spec, ±1 mm Fasen)."""
        for num in ballon.TYPES:
            author, report = self.gen(num)
            self.assertEqual(report["ops"], [])
            measured = dims(evaluated(author))
            spec = ballon.load_spec(SNAP, num)["dimensions"]
            # BALLONs umgestülpter Objektiv-Hohlkegel (adapt) ragt in BALLONs Messung um r_in·r1/r − r1 über den Außenradius
            raw = {p["id"]: p for p in ballon.load(SNAP, num)["PARTS"]}
            overhang = max([raw[n["part"]]["r_in"] * raw[n["part"]]["r1"] / raw[n["part"]]["r"] - raw[n["part"]]["r1"]
                            for n in report["adaptations"] if n.get("field") == "r_in"] or [0])
            for key in ("length", "height", "width"):
                expected = spec[f"{key}_m"] * 1000
                if overhang and key != "length":
                    self.assertTrue(expected - 2 * overhang - 1 <= measured[key] <= expected + 1.0, f"BASIC-{num} {key}")
                else:
                    self.assertAlmostEqual(measured[key], expected, delta=1.0, msg=f"BASIC-{num} {key}")

    def test_baseline_parts_identical_to_ballon(self):
        author, report = self.gen("01")
        raw = ballon.load(SNAP, "01")
        self.assertEqual([p["id"] for p in author["PARTS"]], [p["id"] for p in raw["PARTS"]])
        for mine, theirs in zip(author["PARTS"], raw["PARTS"]):
            for key in ("pts", "f0", "f1", "u0", "u1", "w", "x", "a0", "a1", "c", "r", "bevel", "mat", "asm"):
                if key in theirs:
                    self.assertEqual(mine[key], theirs[key], (mine["id"], key))

    def test_front_stretch_lengthens_by_reported_delta_and_keeps_short_parts(self):
        base, _ = self.gen("01")
        author, report = self.gen("01", front=1.15)
        op = report["ops"][0]
        self.assertFalse(op["limited"])
        self.assertAlmostEqual(op["delta_mm"], 0.15 * 606, places=6)   # Socket_Muzzle f=606 vor Socket_Hand
        self.assertAlmostEqual(dims(evaluated(author))["length"] - dims(evaluated(base))["length"], op["delta_mm"], delta=0.01)
        before = {p["id"]: generator._extent(p) for p in base["PARTS"]}
        for p in author["PARTS"]:
            lo, hi = generator._extent(p)
            if before[p["id"]][1] - before[p["id"]][0] < generator.SHORT_MM:
                self.assertAlmostEqual(hi - lo, before[p["id"]][1] - before[p["id"]][0], places=9, msg=p["id"])
        self.assertAlmostEqual(author["ANCHORS"]["Socket_Muzzle"]["at"][0], 606 + op["delta_mm"])
        self.assertEqual(author["ANCHORS"]["Socket_Hand"]["at"], base["ANCHORS"]["Socket_Hand"]["at"])

    def test_shortening_never_inverts_parts(self):
        for num in ballon.TYPES:
            author, report = self.gen(num, front=0.7, rear=0.7)
            doc = evaluated(author)
            for p in doc["parts"]:
                self.assertTrue(p["mesh"]["faces"], (num, p["id"]))
            for op in report["ops"]:
                if "delta_mm" in op and op["delta_mm"] < 0:
                    self.assertGreaterEqual(op["delta_mm"], op["wanted_mm"] - 1e-9)

    def test_rear_skips_types_without_stock(self):
        _, report = self.gen("05", rear=1.2)
        self.assertIn("skipped", report["ops"][0])

    def test_drop_protects_anchored_parts_and_keeps_assemblies_consistent(self):
        author, report = self.gen("01", drop=["vent_*", "grip", "charging_handle"])
        op = report["ops"][0]
        self.assertEqual(len(op["dropped"]), 8)
        self.assertEqual(sorted(op["protected"]), ["charging_handle", "grip"])
        model.normalize(author)

    def test_inverted_ballon_cone_wall_is_adapted_and_reported(self):
        author, report = self.gen("03")
        notes = {n["part"]: n for n in report["adaptations"] if "part" in n}
        self.assertIn("scope_objective", notes)
        part = next(p for p in author["PARTS"] if p["id"] == "scope_objective")
        self.assertLess(part["r_in"], min(part["r"], part["r1"]))
        self.assertEqual(notes["scope_objective"]["kind"], "Annahme")

    def test_generator_does_not_mutate_loaded_ballon_data(self):
        data = ballon.load(SNAP, "01")
        frozen = copy.deepcopy(data)
        generator.generate(data, dict(self.base, params={"front": 1.2, "rear": 0.9, "drop": ["vent_*"]}), "01",
                           ballon.source(SNAP, "01"))
        self.assertEqual(data, frozen)


if __name__ == "__main__":
    unittest.main()
