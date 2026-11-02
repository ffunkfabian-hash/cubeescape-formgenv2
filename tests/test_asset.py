"""0.3 „Forge“: Waffen-Assets über BALLONs Blender-Kit (Machbarkeitsnachweis).

Ohne Blender: Rückführung des Generators auf BALLONs Datensatz, Schlüssel, Kit-Schnappschuss, GLB-Index.
Mit vorhandenen Ergebnissen (Mac, nach `python -m formgen.asset BA01 …`): BA01 dreiecks- und materialgleich zu BALLONs GLB.
"""
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from formgen import asset, ballon, ballon_kit, generator, variants
from formgen.cache import canonical

try:
    SNAP, KIT = ballon.snapshot(), ballon_kit.snapshot()
except ballon.BallonError as error:   # z. B. Cloud ohne BALLON-Checkout
    SNAP, KIT, REASON = None, None, str(error)
else:
    REASON = ""
OUT = asset.ROOT / "out"
BALLON_GLB = Path.home() / "Library/Caches/CubeEscapeBallon/out/BASIC-01/BASIC-01.glb"


def kit_model(sid):
    entry = variants.sheets()[sid]
    data = ballon.load(SNAP, entry["num"])
    author, report = generator.generate(data, entry["variant"], entry["num"], ballon.source(SNAP, entry["num"]))
    return data, asset.kit_model(data, author, report)


@unittest.skipIf(SNAP is None, REASON)
class KitModelTests(unittest.TestCase):
    def test_baseline_is_ballons_dataset_for_all_types(self):
        # Baseline = BALLONs Modul bit für bit (inkl. r_in der Zielfernrohre und leerer Baugruppe support)
        for num in ballon.TYPES:
            with self.subTest(num=num):
                data, model = kit_model(f"BA{num}")
                for key in ("META", "PARTS", "ASSEMBLIES", "ANCHORS", "ACTIONS"):
                    self.assertEqual(canonical(model[key]), canonical(data[key] or {}), key)

    def test_variant_keeps_metadata_and_filters_actions(self):
        data, model = kit_model("BC01")
        ids = {p["id"] for p in model["PARTS"]}
        self.assertFalse(any(i.startswith("vent_") for i in ids))
        self.assertEqual(len(ids), len(data["PARTS"]) - 8)
        original = {p["id"]: p for p in data["PARTS"]}
        for p in model["PARTS"]:
            self.assertNotIn("name_en", p)
            for key in ("de", "en", "func", "attach", "mat", "asm"):
                self.assertEqual(p.get(key), original[p["id"]].get(key))
        for action in model["ACTIONS"].values():
            self.assertLessEqual(set(action["keys"]), ids)
        self.assertEqual(model["ASSEMBLIES"], data["ASSEMBLIES"])

    def test_variant_changes_geometry(self):
        _, a = kit_model("BA01")
        _, b = kit_model("BB01")
        self.assertNotEqual(canonical(a["PARTS"]), canonical(b["PARTS"]))
        self.assertGreater(b["ANCHORS"]["Socket_Muzzle"]["at"][0], a["ANCHORS"]["Socket_Muzzle"]["at"][0])


@unittest.skipIf(SNAP is None, REASON)
class PlanTests(unittest.TestCase):
    def plan(self, ids, **cfg):
        with mock.patch.object(asset, "blender_version", lambda binary: "Blender 5.2.2 LTS"):
            return asset.plan(ids, KIT, SNAP, {**asset.DEFAULTS, **cfg})

    def test_keys_are_stable_and_per_sheet(self):
        a, b = self.plan(["BA01", "BB01"]), self.plan(["BA01", "BB01"])
        self.assertEqual([x.key for x in a], [x.key for x in b])
        self.assertNotEqual(a[0].key, a[1].key)
        self.assertEqual([x.output for x in a], ["assets/BA01.glb", "assets/BB01.glb"])
        self.assertEqual(a[0].inputs["module"], "basic.weapons.w01_auto_rifle")

    def test_key_follows_blender_version_and_code(self):
        base = self.plan(["BA01"])[0]
        with mock.patch.object(asset, "blender_version", lambda binary: "Blender 5.3.0"):
            other = asset.plan(["BA01"], KIT, SNAP, dict(asset.DEFAULTS))[0]
        self.assertNotEqual(base.key, other.key)
        self.assertEqual(base.source, other.source)
        asset.code_hash.cache_clear()
        with mock.patch.object(asset, "file_hash", lambda path: "x" if path.name == "asset_build.py" else "y"):
            changed = self.plan(["BA01"])[0]
        asset.code_hash.cache_clear()
        self.assertNotEqual(base.key, changed.key)

    def test_backend_hash_is_content_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy_dir = Path(tmp) / "kit"
            shutil.copytree(KIT / "basic", copy_dir / "basic")
            shutil.copytree(KIT / "tools", copy_dir / "tools")
            self.assertEqual(ballon_kit.backend_hash(copy_dir), ballon_kit.backend_hash(KIT))
            files = ballon_kit.closure_files(copy_dir, [copy_dir / f for f in ballon_kit.BACKEND])
            self.assertIn("basic/kit.py", files)
            self.assertIn("tools/bake_unity.py", files)
            with (copy_dir / "basic/kit.py").open("a") as stream:
                stream.write("\n# geändert\n")
            self.assertNotEqual(ballon_kit.backend_hash(copy_dir), ballon_kit.backend_hash(KIT))

    def test_newest_pilot(self):
        self.assertEqual(ballon_kit.pilot_file(KIT, "01").name, "w01_auto_rifle_v21.py")   # v21 vor v2
        self.assertIsNone(ballon_kit.pilot_file(KIT, "16"))                                 # Schwert ohne Pilot


@unittest.skipUnless((OUT / "assets/BA01.glb").is_file() and BALLON_GLB.is_file(),
                     "Ergebnisse fehlen (Mac: ce lock blender -- python -m formgen.asset BA01 BB01 BC01)")
class BuiltAssetTests(unittest.TestCase):
    def test_ba01_triangle_and_material_equal_to_ballon(self):
        import sys
        sys.path.insert(0, str(asset.ROOT / "tools"))
        import ballon_compare
        r = ballon_compare.compare_asset(OUT / "assets/BA01.glb", BALLON_GLB)
        self.assertTrue(r["equal"], r)
        self.assertEqual(r["triangles"]["asset"], r["triangles"]["ballon"])

    def test_index_matches_files(self):
        index = json.loads((OUT / "assets/index.json").read_text())
        for sid, entry in index["assets"].items():
            glb = OUT / "assets" / entry["glb"]
            self.assertEqual(asset.file_hash(glb), entry["sha256"], sid)
            self.assertEqual(asset.glb_info(glb)["triangles"], entry["triangles"], sid)


if __name__ == "__main__":
    unittest.main()
