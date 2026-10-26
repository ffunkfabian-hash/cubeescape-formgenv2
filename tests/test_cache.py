"""Cache acceptance without images: real files, subprocesses and deliberately bad bytes."""
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import unittest

from formgen.build import ROOT, DUMMY, Stage, plan, summary
from formgen.cache import run_artifacts, valid_entry


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="formgen-cache-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.out = self.root / "out"
        self.cache = self.root / "cache"
        self.sources = {}
        for model_id in ("A", "B"):
            path = self.root / f"{model_id}.py"
            path.write_text(f"INFO = {{'id': '{model_id}'}}\n", encoding="utf-8")
            self.sources[model_id] = path

    def run_build(self, artifacts=None, **kwargs):
        return run_artifacts(plan(self.sources) if artifacts is None else artifacts,
                             self.out, self.cache, **kwargs)

    def test_two_real_disk_builds(self):
        first = self.run_build()
        second = self.run_build()
        self.assertEqual(summary(first), "2 gebaut · 0 aus dem Cache")
        self.assertEqual(summary(second), "0 gebaut · 2 aus dem Cache")
        self.assertEqual(json.loads((self.out / "dummy/A.json").read_text())["model"], "A")
        manifest = json.loads((self.out / "manifest.json").read_text())
        self.assertEqual(len(manifest["artifacts"]), 2)
        self.assertEqual(manifest["artifacts"]["dummy/A.json"]["reason"], "cache_hit")

    def test_source_change_isolates_model(self):
        self.run_build()
        with self.sources["A"].open("a") as stream:
            stream.write("# changed geometry\n")
        results = self.run_build()
        self.assertEqual([result.built for result in results], [True, False])

    def test_missing_and_corrupt_outputs_restore_without_build(self):
        self.run_build()
        expected = {name: (self.out / f"dummy/{name}.json").read_bytes() for name in self.sources}
        (self.out / "dummy/A.json").unlink()
        (self.out / "dummy/B.json").write_bytes(b"bad output")
        results = self.run_build()
        self.assertEqual([result.built for result in results], [False, False])
        self.assertEqual([result.reason for result in results],
                         ["restored_missing_output", "restored_corrupt_output"])
        for name, content in expected.items():
            self.assertEqual((self.out / f"dummy/{name}.json").read_bytes(), content)

    def test_corrupt_cache_rebuilds_only_affected_entry(self):
        first = self.run_build()
        (self.cache / first[0].key / "artifact").write_bytes(b"damaged cache")
        self.assertFalse(valid_entry(self.cache / first[0].key, first[0].key))
        second = self.run_build()
        self.assertEqual([result.built for result in second], [True, False])
        self.assertEqual(second[0].reason, "corrupt_cache")
        self.assertTrue(valid_entry(self.cache / first[0].key, first[0].key))

    def test_missing_and_invalid_cache_manifests_rebuild(self):
        first = self.run_build()
        (self.cache / first[0].key / "entry.json").unlink()
        (self.cache / first[1].key / "entry.json").write_text("[]")
        self.assertTrue(all(result.built for result in self.run_build()))

    def test_cache_directory_replaced_by_file_is_repaired(self):
        first = self.run_build()
        entry = self.cache / first[0].key
        shutil.rmtree(entry)
        entry.write_bytes(b"not a cache directory")
        second = self.run_build()
        self.assertEqual([result.built for result in second], [True, False])
        self.assertTrue(valid_entry(entry, first[0].key))

    def test_source_move_keeps_content_key(self):
        self.run_build()
        moved = self.root / "moved.py"
        self.sources["A"].rename(moved)
        self.sources["A"] = moved
        self.assertFalse(any(result.built for result in self.run_build()))

    def test_failed_force_preserves_previous_cache_and_output(self):
        artifact = plan(self.sources)[0]
        self.run_build([artifact])
        expected = (self.out / artifact.output).read_bytes()
        with self.assertRaises(ModuleNotFoundError):
            self.run_build([replace(artifact, builder="missing_formgen_builder:build")], force=True)
        self.assertEqual((self.out / artifact.output).read_bytes(), expected)
        self.assertTrue(valid_entry(self.cache / artifact.key, artifact.key))

    def test_force_is_selective_by_kind(self):
        stages = [Stage(kind, DUMMY.builder, (version,), kind, ".json")
                  for kind, version in (("views", "RASTER"), ("sheets", "SHEET"), ("specs", "SPEC"))]
        artifacts = plan({"A": self.sources["A"]}, stages)
        self.run_build(artifacts)
        for selected in ("views", "sheets"):
            results = self.run_build(artifacts, force_kinds={selected})
            self.assertEqual([result.built for result in results],
                             [artifact.kind == selected for artifact in artifacts])
        self.assertTrue(all(result.built for result in self.run_build(artifacts, force=True)))

    def test_renderer_version_only_invalidates_views(self):
        stages = [Stage(kind, DUMMY.builder, (version,), kind, ".json")
                  for kind, version in (("views", "RASTER"), ("sheets", "SHEET"), ("specs", "SPEC"))]
        artifacts = plan({"A": self.sources["A"]}, stages)
        self.run_build(artifacts)
        artifacts[0] = replace(artifacts[0], versions={"RASTER": 999})
        results = self.run_build(artifacts)
        self.assertEqual([result.built for result in results], [True, False, False])

    def test_parameters_change_key_but_mapping_order_does_not(self):
        artifact = plan(self.sources)[0]
        first = replace(artifact, params={"width": 100, "height": 80})
        reordered = replace(artifact, params={"height": 80, "width": 100})
        changed = replace(artifact, params={"width": 101, "height": 80})
        self.assertEqual(first.key, reordered.key)
        self.assertNotEqual(first.key, changed.key)
        self.run_build([first])
        self.assertFalse(self.run_build([reordered])[0].built)
        self.assertTrue(self.run_build([changed])[0].built)

    def test_source_changed_after_planning_does_not_publish(self):
        artifact = plan(self.sources)[0]
        self.sources["A"].write_text("changed after plan")
        with self.assertRaisesRegex(RuntimeError, "während des Baus"):
            self.run_build([artifact])
        self.assertFalse((self.cache / artifact.key).exists())
        self.assertFalse((self.out / artifact.output).exists())

    def test_process_workers_merge_manifest(self):
        first = self.run_build(jobs=2)
        self.assertEqual(summary(first), "2 gebaut · 0 aus dem Cache")
        manifest = json.loads((self.out / "manifest.json").read_text())
        self.assertEqual(set(manifest["artifacts"]), {"dummy/A.json", "dummy/B.json"})
        self.assertEqual(summary(self.run_build(jobs=2)), "0 gebaut · 2 aus dem Cache")

    def command(self, *flags):
        return [sys.executable, "-m", "formgen.build", "--dummy", "--out", str(self.out),
                "--cache", str(self.cache), *flags]

    def test_cli_runs_twice_and_supports_force_flags(self):
        for flags, expected in [((), "1 gebaut · 0 aus dem Cache"),
                                (("MINI", "--jobs", "2"), "0 gebaut · 1 aus dem Cache"),
                                (("--force-views", "--force-sheets"), "0 gebaut · 1 aus dem Cache"),
                                (("--force",), "1 gebaut · 0 aus dem Cache")]:
            result = subprocess.run(self.command(*flags), cwd=ROOT, text=True,
                                    capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), expected)

    def test_concurrent_cli_builders_publish_once(self):
        processes = [subprocess.Popen(self.command(), cwd=ROOT, text=True,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(3)]
        outputs = []
        try:
            for process in processes:
                stdout, stderr = process.communicate(timeout=30)
                self.assertEqual(process.returncode, 0, stderr)
                outputs.append(stdout.strip())
        finally:
            for process in processes:
                if process.poll() is None:
                    process.kill()
                    process.wait()
        self.assertEqual(outputs.count("1 gebaut · 0 aus dem Cache"), 1)
        self.assertEqual(outputs.count("0 gebaut · 1 aus dem Cache"), 2)
        manifest = json.loads((self.out / "manifest.json").read_text())
        key = manifest["artifacts"]["dummy/MINI.json"]["key"]
        self.assertTrue(valid_entry(self.cache / key, key))

    def test_bad_cli_selection_and_jobs_fail_without_output(self):
        for flags in (("UNKNOWN",), ("--jobs", "0"), ("--jobs", "-2")):
            result = subprocess.run(self.command(*flags), cwd=ROOT, text=True,
                                    capture_output=True, timeout=30)
            self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.out.exists())

    def test_build_imports_no_image_or_geometry_module(self):
        code = ("import formgen.build, sys; "
                "assert not {'formgen.raster', 'formgen.geom', 'PIL', 'numpy'} & set(sys.modules)")
        result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, text=True,
                                capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_duplicate_and_escaping_paths_rejected(self):
        artifact = plan(self.sources)[0]
        for output in ("../outside", "/outside", "manifest.json", ".locks/key", "a//b", "a/./b"):
            with self.assertRaises(ValueError):
                self.run_build([replace(artifact, output=output)])
        with self.assertRaises(ValueError):
            self.run_build([artifact, artifact])
        self.out.mkdir()
        (self.out / "escape").symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.run_build([replace(artifact, output="escape/outside")])


if __name__ == "__main__":
    unittest.main()
