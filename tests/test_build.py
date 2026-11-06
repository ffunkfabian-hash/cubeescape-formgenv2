"""Stage wiring and real geometry cache acceptance; no renderer execution."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from formgen import versions
from formgen.build import (ROOT, ORTHOS, SKINS, downstream_plan, geometry_plan,
                           select_document, source_hashes, view_names, view_parameters)
from formgen.cache import file_hash, run_artifacts


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="formgen-stages-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.out, self.cache = self.root / "out", self.root / "cache"

    def mini_geometry(self):
        artifacts = geometry_plan({"MINI": ROOT / "formgen/models/mini.py"})
        return run_artifacts(artifacts, self.out, self.cache)

    def test_real_geometry_two_runs_and_restore(self):
        first = self.mini_geometry()
        document = json.loads((self.out / "geometry/MINI.json").read_text())
        self.assertEqual(document["info"]["id"], "MINI")
        self.assertEqual(len(document["parts"]), 2)
        self.assertTrue(document["parts"][0]["mesh"]["vertices"])
        self.assertTrue(first[0].built)
        self.assertFalse(self.mini_geometry()[0].built)
        (self.out / "geometry/MINI.json").unlink()
        self.assertEqual(self.mini_geometry()[0].reason, "restored_missing_output")

    def test_geometry_cli_builds_registry_without_pixels(self):
        command = [sys.executable, "-m", "formgen.build", "--stages", "geometry",
                   "--out", str(self.out), "--cache", str(self.cache), "--jobs", "2"]
        for expected in ("4 gebaut · 0 aus dem Cache", "0 gebaut · 4 aus dem Cache"):
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), expected)
        self.assertFalse((self.out / "views").exists())
        for model_id in ("W01", "KG02", "VS02", "R01"):
            document = json.loads((self.out / "geometry" / f"{model_id}.json").read_text())
            self.assertEqual(document["info"]["id"], model_id)
            self.assertGreater(len(document["parts"]), 1)

    def test_renderer_version_and_params_isolate_view_keys(self):
        self.mini_geometry()
        stages = ("views", "specs", "prompts", "sheets")
        before = {kind: downstream_plan(["MINI"], self.out, kind, views=["side_left"])[0].key
                  for kind in stages}
        with patch.object(versions, "RASTER", versions.RASTER + 1):
            after = {kind: downstream_plan(["MINI"], self.out, kind, views=["side_left"])[0].key
                     for kind in stages}
        self.assertEqual([kind for kind in stages if before[kind] != after[kind]], ["views"])
        resized = {kind: downstream_plan(["MINI"], self.out, kind, views=["side_left"], width=512)[0].key
                   for kind in stages}
        self.assertEqual([kind for kind in stages if before[kind] != resized[kind]], ["views"])

    def test_sheet_key_tracks_layout_metadata_but_not_pixel_bytes(self):
        self.mini_geometry()
        with patch("formgen.build.Path.is_file", return_value=True):
            with patch("formgen.build.view_metadata", return_value={"front":{"width":100,"height":80,"labels":[]}}):
                first=downstream_plan(["MINI"],self.out,"sheets",views=["front"])[0]
                with patch.object(versions,"RASTER",versions.RASTER+1):
                    recolored=downstream_plan(["MINI"],self.out,"sheets",views=["front"])[0]
                self.assertEqual(first.key,recolored.key)
            with patch("formgen.build.view_metadata", return_value={"front":{"width":200,"height":160,"labels":[]}}):
                resized=downstream_plan(["MINI"],self.out,"sheets",views=["front"])[0]
            self.assertNotEqual(first.key,resized.key)

    def test_legacy_catalog_changes_only_imported_view_keys(self):
        self.mini_geometry()
        path=self.out/'geometry/MINI.json'
        native=json.loads(path.read_text())
        def keys():
            return {kind:downstream_plan(['MINI'],self.out,kind,views=['front'])[0].key
                    for kind in ('views','previews','specs','prompts')}
        real_hash=file_hash
        def hashes(catalog):
            return lambda p:catalog if Path(p).name=='catalog.json' else real_hash(p)
        with patch('formgen.build.file_hash',side_effect=hashes('a'*64)):
            before=keys()
        with patch('formgen.build.file_hash',side_effect=hashes('b'*64)):
            self.assertEqual(keys(),before)
        legacy=copy.deepcopy(native)
        # Legacy sights have no skin block, but still use catalog materials.
        legacy['source_geo']={'format':'cubeescape-design/geometry-spec'}
        path.write_text(json.dumps(legacy))
        with patch('formgen.build.file_hash',side_effect=hashes('a'*64)):
            before=keys()
        with patch('formgen.build.file_hash',side_effect=hashes('b'*64)):
            after=keys()
        self.assertNotEqual(before['views'],after['views'])
        self.assertNotEqual(before['previews'],after['previews'])
        self.assertEqual(before['specs'],after['specs'])
        self.assertEqual(before['prompts'],after['prompts'])

    def test_view_artifacts_are_separate_and_sheet_paths_stable(self):
        self.mini_geometry()
        views = downstream_plan(["MINI"], self.out, "views", views=["front", "side_left"])
        self.assertNotEqual(views[0].key, views[1].key)
        self.assertEqual([artifact.output for artifact in views],
                         ["views/MINI/front.png", "views/MINI/side_left.png"])
        sheet = downstream_plan(["MINI"], self.out, "sheets", views=["front"])[0]
        self.assertEqual(sheet.params["views"], {"front": "../views/MINI/front.png"})
        self.assertEqual(set(sheet.versions), {"SHEET", "SPEC", "PROMPTS"})

    def test_local_python_dependency_invalidation(self):
        model = self.root / "model.py"
        helper = self.root / "helper.py"
        model.write_text("from helper import PARTS\n")
        helper.write_text("PARTS = []\n")
        first = source_hashes(model, self.root)
        helper.write_text("PARTS = [1]\n")
        second = source_hashes(model, self.root)
        self.assertEqual(first[str(model)], second[str(model)])
        self.assertNotEqual(first[str(helper)], second[str(helper)])

    def test_invalid_stage_and_view_do_not_build_geometry(self):
        for flags in (("--stages", "unknown"), ("--views", "unknown"),
                      ("--width", "0"), ("--dummy", "--stages", "geometry")):
            command = [sys.executable, "-m", "formgen.build", "--out", str(self.out),
                       "--cache", str(self.cache), *flags]
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=30)
            self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.out.exists())

    def sample_document(self):
        def part(name, assembly, offset):
            return {"id": name, "assembly": assembly, "label": name,
                    "mesh": {"vertices": [[offset, 0., 0.], [offset + .02, 0., 0.],
                                          [offset, -.02, .02]], "faces": [[0, 1, 2]], "hard": [1]}}
        return {"info": {"id": "TEST", "kind": "weapon"},
                "parts": [part("trigger", "body", 0.), part("sight_lens", "sight", .2)],
                "assemblies": [{"id": "body", "explode": [0, 100, 0]}, {"id": "sight"}],
                "anchors": {"Socket_Hand": {"part": "trigger", "position_m": [0., 0., 0.]}}, "poses": {}}

    def test_weapon_subsets_preserve_source_and_focus_requested_parts(self):
        document = self.sample_document()
        original = copy.deepcopy(document)
        self.assertEqual([p["id"] for p in select_document(document, "hero")["parts"]], ["trigger"])
        self.assertEqual([p["id"] for p in select_document(document, "sight_side")["parts"]], ["sight_lens"])
        detail = select_document(document, "detail_trigger")
        self.assertEqual([p["id"] for p in detail["parts"]], ["trigger"])
        self.assertEqual(detail["view_crop"]["span_m"], .15)
        self.assertEqual(document, original)

    def test_full_weapon_views_dimensions_and_shared_orthos(self):
        document = self.sample_document()
        expected = {"hero", *ORTHOS, "detail_trigger", "sight_iso", "sight_side",
                    *(f"skin_{skin}" for skin in SKINS)}
        self.assertEqual(set(view_names(document)), expected)
        hero = view_parameters(document, "hero")
        self.assertEqual((hero["width"], hero["height"]), (1440, 960))
        for view in ORTHOS:
            params = view_parameters(document, view)
            self.assertEqual(params["framing_views"], list(ORTHOS))
            self.assertEqual((params["width"], params["height"]), (960, 480))
        self.assertEqual(view_parameters(document, "skin_kobalt")["skin"], "kobalt")
        document["info"]["kind"] = "sight"
        self.assertIn("iso", view_names(document))
        self.assertNotIn("hero", view_names(document))

    def test_views_of_a_line_include_its_main_skin(self):
        document = {**self.sample_document(), "generator": {"variant": {"skin": "wueste"}}}
        names = view_names(document)
        self.assertEqual([n for n in names if n.startswith("skin_")], ["skin_wueste", *(f"skin_{skin}" for skin in SKINS)])
        params = view_parameters(document, "skin_wueste")
        self.assertEqual((params["skin"], params["width"], params["height"]), ("wueste", 960, 640))

    def test_figure_explode_assembly_and_explicit_pose(self):
        document = self.sample_document()
        document["info"]["kind"] = "figure"
        document["poses"]["ready"] = {"part_transforms": {"trigger":
            [[1, 0, 0, .1], [0, 1, 0, 0], [0, 0, 1, .2], [0, 0, 0, 1]]}}
        exploded = select_document(document, "exploded")
        self.assertEqual(exploded["anchors"]["Socket_Hand"]["position_m"], [0., 0., .1])
        self.assertEqual(len(select_document(document, "assembly_sight")["parts"]), 1)
        posed = select_document(document, "ready")
        self.assertEqual(posed["anchors"]["Socket_Hand"]["position_m"], [.1, 0., .2])
        self.assertIn("ready", view_names(document))
        with self.assertRaisesRegex(ValueError, "part_transforms"):
            select_document(document, "idle")

    def test_spec_skin_and_prompt_spec_dependency_keys(self):
        self.mini_geometry()
        before = {kind: downstream_plan(["MINI"], self.out, kind)[0].key
                  for kind in ("specs", "prompts", "previews")}
        with patch("formgen.build.file_hash", side_effect=lambda path:
                   "changed-skin-sha" if Path(path).name == "skins.toml" else file_hash(path)):
            self.assertNotEqual(before["specs"], downstream_plan(["MINI"], self.out, "specs")[0].key)
            self.assertNotEqual(before["previews"], downstream_plan(["MINI"], self.out, "previews")[0].key)
            self.assertEqual(before["prompts"], downstream_plan(["MINI"], self.out, "prompts")[0].key)
        with patch.object(versions, "SPEC", versions.SPEC + 1):
            self.assertNotEqual(before["prompts"], downstream_plan(["MINI"], self.out, "prompts")[0].key)
            self.assertEqual(before["previews"], downstream_plan(["MINI"], self.out, "previews")[0].key)

    def test_geo_referenced_spec_is_part_of_source_key(self):
        source = self.root / "TEST.geo.json"
        source.write_text(json.dumps({"source": {"weapon_spec": {"file": "TEST.spec.json"}}}))
        absent = geometry_plan({"TEST": source})[0]
        spec = self.root / "TEST.spec.json"
        spec.write_text("{}")
        present = geometry_plan({"TEST": source})[0]
        spec.write_text('{"changed": true}')
        changed = geometry_plan({"TEST": source})[0]
        self.assertNotEqual(absent.key, present.key)
        self.assertNotEqual(present.key, changed.key)

    def test_specs_and_prompts_build_without_pixels(self):
        command = [sys.executable, "-m", "formgen.build", "--stages", "specs,prompts",
                   "--out", str(self.out), "--cache", str(self.cache), "--jobs", "2"]
        for expected in ("12 gebaut · 0 aus dem Cache", "0 gebaut · 12 aus dem Cache"):
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), expected)
        self.assertFalse((self.out / "views").exists())
        self.assertTrue((self.out / "specs/W01.spec.json").exists())
        self.assertTrue((self.out / "prompts/VS02.prompts.json").exists())
        for sid in ("KG02","VS02"):
            self.assertEqual((self.out/"specs"/f"{sid}.spec.json").read_bytes(),
                             (ROOT/"tests/fixtures"/f"{sid}.spec.json").read_bytes())
        native=json.loads((self.out/"specs/W01.spec.json").read_bytes())
        self.assertFalse(Path(native["source"]["path"]).is_absolute())


if __name__ == "__main__":
    unittest.main()
