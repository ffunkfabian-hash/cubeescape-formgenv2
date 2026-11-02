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

    def test_only_r_in_adaptations_are_reverted(self):
        data = ballon.load(SNAP, "01")
        author = {"PARTS": [dict(p) for p in data["PARTS"]], "ANCHORS": data["ANCHORS"]}
        part = data["PARTS"][0]["id"]
        author["PARTS"][0]["mat"] = "sight_anod"                                             # Gestaltung der Variante (0.4)
        report = {"adaptations": [{"part": part, "kind": "Annahme", "field": "mat", "ballon": data["PARTS"][0]["mat"],
                                   "v2": "sight_anod"},
                                  {"kind": "Annahme", "field": "base", "ballon": "v21", "v2": "standard"}]}
        model = asset.kit_model(data, author, report)
        self.assertEqual(model["PARTS"][0]["mat"], "sight_anod")

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


class ToolSafetyTests(unittest.TestCase):
    def test_pilot_check_verdict_fails_on_any_gap(self):
        import sys
        sys.path.insert(0, str(asset.ROOT / "tools"))
        import kit_pilot_check as K
        good = {"built": True, "equal": True}
        self.assertEqual(K.verdict({"pilots": {"A": good, "B": good}}), 0)
        self.assertEqual(K.verdict({"pilots": {}}), 1)                                       # leere Auswahl
        self.assertEqual(K.verdict({"pilots": {"A": good, "B": {"built": True, "equal": False}}}), 1)
        self.assertEqual(K.verdict({"pilots": {"A": good, "B": {"built": True, "ego_json": "keine Referenz"}}}), 1)
        self.assertEqual(K.verdict({"pilots": {"A": {"built": False, "error": "x"}}}), 1)

    def test_package_refuses_foreign_folder_and_keeps_old_on_failure(self):
        art = mock.Mock(model_id="BX01", inputs={"snapshot": "", "module": "", "model": {}, "skin": "standard", "blender": "b"})
        cfg = dict(asset.DEFAULTS)
        with tempfile.TemporaryDirectory() as tmp:
            foreign = Path(tmp) / "BX01"
            foreign.mkdir()
            (foreign / "notiz.txt").write_text("fremd")
            with mock.patch.object(asset, "run_blender") as run:
                with self.assertRaises(RuntimeError):
                    asset.build_package(art, Path(tmp), cfg)
                run.assert_not_called()
            self.assertTrue((foreign / "notiz.txt").is_file())
            (foreign / "notiz.txt").unlink()
            (foreign / "BX01.package.json").write_text("{}")                                   # eigenes altes Paket
            with mock.patch.object(asset, "run_blender", side_effect=RuntimeError("Blender")):
                with self.assertRaises(RuntimeError):
                    asset.build_package(art, Path(tmp), cfg)
            self.assertTrue((foreign / "BX01.package.json").is_file())                       # bleibt bei Fehlschlag
            def fake(job, blender):
                Path(job["out"], "BX01.package.json").write_text('{"neu": 1}')
            with mock.patch.object(asset, "run_blender", side_effect=fake):
                asset.build_package(art, Path(tmp), cfg)
            self.assertEqual(json.loads((foreign / "BX01.package.json").read_text()), {"neu": 1})
            self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()), ["BX01"])          # kein Temp-Rest


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

    def test_moved_anchor_is_detected(self):
        import struct
        import sys
        sys.path.insert(0, str(asset.ROOT / "tools"))
        import ballon_compare
        data = (OUT / "assets/BA01.glb").read_bytes()
        n = struct.unpack_from("<I", data, 12)[0]
        g = json.loads(data[20:20 + n])
        node = next(x for x in g["nodes"] if x.get("name") == "Socket_Muzzle")
        node["translation"] = [v + (0.002 if i == 1 else 0.0) for i, v in enumerate(node.get("translation", [0, 0, 0]))]
        chunk = json.dumps(g).encode()
        chunk += b" " * (-len(chunk) % 4)
        rest = data[20 + n:]
        body = struct.pack("<II", len(chunk), 0x4E4F534A) + chunk + rest
        with tempfile.TemporaryDirectory() as tmp:
            moved = Path(tmp) / "moved.glb"
            moved.write_bytes(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)
            r = ballon_compare.compare_asset(moved, OUT / "assets/BA01.glb")
        self.assertTrue(r["meshes_equal"] and r["positions_equal"])
        self.assertFalse(r["nodes_equal"])
        self.assertEqual(r["nodes_differing"], ["Socket_Muzzle"])
        self.assertFalse(r["equal"])

    def test_swapped_mesh_geometry_is_detected(self):
        # zwei Netze gleicher Dreieckszahl und gleichen Materials tauschen ihre Geometrie: global gleich, je Netz nicht
        import struct
        import sys
        sys.path.insert(0, str(asset.ROOT / "tools"))
        import ballon_compare
        data = (OUT / "assets/BA01.glb").read_bytes()
        n = struct.unpack_from("<I", data, 12)[0]
        g = json.loads(data[20:20 + n])
        nodes = {x["name"]: x for x in g["nodes"] if "mesh" in x}
        info = asset.glb_info(OUT / "assets/BA01.glb")["meshes"]
        pairs = {}
        for name, prims in info.items():
            pairs.setdefault((prims[0]["triangles"], prims[0]["material"], len(prims)), []).append(name)
        a, b = next(v for v in pairs.values() if len(v) >= 2)[:2]
        a_mesh, a_tr = nodes[a]["mesh"], {k: nodes[a].get(k) for k in ("translation", "rotation", "scale")}
        nodes[a]["mesh"], nodes[b]["mesh"] = nodes[b]["mesh"], a_mesh
        for k in ("translation", "rotation", "scale"):
            nodes[a][k], nodes[b][k] = nodes[b].get(k), a_tr[k]
            for x in (nodes[a], nodes[b]):
                if x[k] is None:
                    del x[k]
        chunk = json.dumps(g).encode()
        chunk += b" " * (-len(chunk) % 4)
        body = struct.pack("<II", len(chunk), 0x4E4F534A) + chunk + data[20 + n:]
        with tempfile.TemporaryDirectory() as tmp:
            swapped = Path(tmp) / "swapped.glb"
            swapped.write_bytes(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)
            r = ballon_compare.compare_asset(swapped, OUT / "assets/BA01.glb")
        self.assertTrue(r["meshes_equal"], (a, b))
        self.assertFalse(r["positions_equal"])
        self.assertFalse(r["equal"])

    def test_asset_reference_follows_glb_dir(self):
        import sys
        sys.path.insert(0, str(asset.ROOT / "tools"))
        import ballon_compare
        with tempfile.TemporaryDirectory() as tmp:
            ref = Path(tmp) / "BASIC-01"
            ref.mkdir()
            shutil.copyfile(OUT / "assets/BA01.glb", ref / "BASIC-01.glb")
            report = Path(tmp) / "r.json"
            code = ballon_compare.main(["--asset", "BA01", "--glb-dir", tmp, "--out", str(report)])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(report.read_text())["BA01"]["ballon_glb"], str(ref / "BASIC-01.glb"))

    def test_index_matches_files(self):
        index = json.loads((OUT / "assets/index.json").read_text())
        for sid, entry in index["assets"].items():
            glb = OUT / "assets" / entry["glb"]
            self.assertEqual(asset.file_hash(glb), entry["sha256"], sid)
            self.assertEqual(asset.glb_info(glb)["triangles"], entry["triangles"], sid)


if __name__ == "__main__":
    unittest.main()
