"""Variantenregister, Blatt-Spec v1 (Schema, Migration) und Stufen-Cache der Waffen-Pipeline (ohne Bilder)."""
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from formgen import ballon, pipeline, variants, wspec

ROOT = Path(__file__).resolve().parents[1]
try:
    SNAP = ballon.snapshot()
except ballon.BallonError as error:
    SNAP, REASON = None, str(error)
else:
    REASON = ""

ENTRY = {"letter": "A", "name": "Baseline", "idea": "Bezug", "since": "0.2", "skin": "standard", "params": {}}


class RegisterTests(unittest.TestCase):
    def test_registered_variants_follow_rule_and_ids(self):
        entries = variants.load()
        sheets = variants.sheets(entries)
        self.assertEqual(len(sheets), 17 * len(entries))
        self.assertIn("BA01", sheets); self.assertIn("BC17", sheets)
        self.assertEqual(variants.parse_sheet("BB07"), ("B", "07"))

    def test_rule_rejects_bad_entries(self):
        bad = [dict(ENTRY, name="glass fang"), dict(ENTRY, name="Very Long Name Here"), dict(ENTRY, name="One Two Three Four"),
               dict(ENTRY, letter="I"), dict(ENTRY, letter="O"), dict(ENTRY, letter="ab"),
               dict(ENTRY, params={"front": 2.0}), dict(ENTRY, params={"shiny": 1}), dict(ENTRY, idea=""),
               dict(ENTRY, types=["18"])]
        for entry in bad:
            with self.assertRaises(variants.VariantError, msg=entry):
                variants.check([entry])
        with self.assertRaises(variants.VariantError):
            variants.check([ENTRY, dict(ENTRY, letter="B")])           # Name doppelt
        with self.assertRaises(variants.VariantError):
            variants.check([ENTRY, dict(ENTRY, name="Other")])         # Buchstabe doppelt
        with self.assertRaises(variants.VariantError):
            variants.check([dict(ENTRY, skin="neon")], {"standard"})

    def test_new_appends_and_rejects_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "variants.toml"
            shutil.copy(variants.REGISTRY, path)
            variants.new("D", "Glass Fang", "Probe", "0.2", "kobalt", {"front": 1.1, "drop": ["vent_*"]}, path)
            self.assertEqual(variants.load(path)[-1]["params"], {"front": 1.1, "drop": ["vent_*"]})
            before = path.read_text()
            with self.assertRaises(variants.VariantError):
                variants.new("E", "Glass Fang", "doppelt", "0.2", path=path)
            self.assertEqual(path.read_text(), before)
        with self.assertRaises(variants.VariantError):
            variants.parse_sheet("BI01")

    def test_new_escapes_multiline_and_quotes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "variants.toml"
            shutil.copy(variants.REGISTRY, path)
            idea = 'Zeile eins\nZeile "zwei" \\ Ende\tTab'
            variants.new("D", "Glass Fang", idea, "0.2", path=path)
            self.assertEqual(variants.load(path)[-1]["idea"], idea)


@unittest.skipIf(SNAP is None, REASON)
class PipelineCacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out, self.cache = Path(self.tmp.name) / "out", Path(self.tmp.name) / "cache"

    def tearDown(self):
        self.tmp.cleanup()

    def run_stages(self, entries, ids, out=None):
        selection = {i: variants.sheets(entries)[i] for i in ids}
        results, timing = pipeline.run(selection, out or self.out, self.cache, ("geometry", "specs", "prompts"), log=lambda _: None)
        return {s: (v["built"], v["cached"]) for s, v in timing["stages"].items()}

    def test_second_run_only_hits_and_small_change_rebuilds_only_affected(self):
        entries = [dict(ENTRY), dict(ENTRY, letter="B", name="Long Reach", params={"front": 1.1})]
        ids = ["BA05", "BB05"]
        self.assertEqual(self.run_stages(entries, ids), {"geometry": (2, 0), "specs": (2, 0), "prompts": (2, 0)})
        self.assertEqual(self.run_stages(entries, ids), {"geometry": (0, 2), "specs": (0, 2), "prompts": (0, 2)})
        changed = copy.deepcopy(entries); changed[1]["params"]["front"] = 1.12
        self.assertEqual(self.run_stages(changed, ids), {"geometry": (1, 1), "specs": (1, 1), "prompts": (1, 1)})
        # anderer Ausgabeordner (zweiter Worktree), gleicher Cache: nur Treffer
        self.assertEqual(self.run_stages(changed, ids, Path(self.tmp.name) / "worktree2"),
                         {"geometry": (0, 2), "specs": (0, 2), "prompts": (0, 2)})

    def test_key_depends_on_ballon_source_hash_and_generator_code(self):
        entries = [dict(ENTRY)]
        sel = {"BA05": variants.sheets(entries)["BA05"]}
        commit = ballon.config()["commit"]
        key = pipeline.geometry_plan(sel, SNAP, commit)[0].key
        self.assertEqual(key, pipeline.geometry_plan(sel, SNAP, "0" * 40)[0].key)   # Commit allein ändert nichts
        with mock.patch.object(ballon, "source", lambda s, n: dict(ballon.closure(s, n) and {
                "basic_id": "BASIC-05", "files": {}, "source_sha256": "f" * 64, "spec_sha256": "missing"})):
            self.assertNotEqual(key, pipeline.geometry_plan(sel, SNAP, commit)[0].key)
        pipeline.code_hash.cache_clear()
        with mock.patch.object(pipeline, "code_hash", lambda rel: "0" * 64):
            self.assertNotEqual(key, pipeline.geometry_plan(sel, SNAP, commit)[0].key)

    def test_builder_files_are_part_of_every_stage_key(self):
        pipeline.code_hash.cache_clear()
        before = {stage: pipeline.code_hash(rel) for stage, rel in pipeline.CODE.items()}
        real = pipeline.file_hash
        fake = lambda path: "0" * 64 if Path(path).name == "build.py" else real(path)
        try:
            pipeline.code_hash.cache_clear()
            with mock.patch.object(pipeline, "file_hash", fake):
                after = {stage: pipeline.code_hash(rel) for stage, rel in pipeline.CODE.items()}
        finally:
            pipeline.code_hash.cache_clear()
        self.assertTrue(all(before[s] != after[s] for s in before), "build.py-Builder fehlen in einem Stufenschlüssel")

    def test_code_closure_covers_geometry_engine(self):
        files = pipeline.build.source_hashes(ROOT / pipeline.CODE["geometry"])
        names = {Path(f).name for f in files}
        self.assertTrue({"generator.py", "ballon.py", "geom.py", "model.py", "cache.py"} <= names, names)
        self.assertNotIn("raster.py", names)

    def test_spec_is_schema_valid_and_deterministic(self):
        self.run_stages([dict(ENTRY)], ["BA04"])
        doc = json.loads((self.out / "specs/BA04.spec.json").read_text())
        wspec.validate(doc)
        self.assertEqual(doc["ballon"]["commit"], ballon.config()["commit"])
        self.assertEqual(doc["ballon"]["source_sha256"], ballon.source(SNAP, "04")["source_sha256"])
        code = ("import sys,hashlib;from formgen import pipeline,variants;from pathlib import Path;"
                "e=[{'letter':'A','name':'Baseline','idea':'Bezug','since':'0.2','skin':'standard','params':{}}];"
                "o=Path(sys.argv[1]);pipeline.run({'BA04':variants.sheets(e)['BA04']},o,o/'c',('geometry','specs'),force=True,log=lambda _:0);"
                "print(hashlib.sha256((o/'specs/BA04.spec.json').read_bytes()).hexdigest())")
        values = [subprocess.check_output([sys.executable, "-c", code, str(Path(self.tmp.name) / seed)], cwd=ROOT,
                                          env={**os.environ, "PYTHONHASHSEED": seed}).strip() for seed in ("1", "42")]
        self.assertEqual(values[0], values[1])


class SpecMigrationTests(unittest.TestCase):
    def minimal(self):
        return {"format": wspec.FORMAT, "format_version": 1}

    def test_unknown_versions_and_foreign_formats_fail(self):
        for doc in ({"format": "x", "format_version": 1}, dict(self.minimal(), format_version=0),
                    dict(self.minimal(), format_version=2), dict(self.minimal(), format_version="1")):
            with self.assertRaises(wspec.SpecError):
                wspec.migrate(doc)

    def test_missing_migration_step_fails(self):
        with mock.patch.object(wspec, "FORMAT_VERSION", 2):
            with self.assertRaises(wspec.SpecError):
                wspec.migrate(self.minimal())

    def test_migration_chain_runs_in_order(self):
        calls = []
        def step(doc):
            calls.append(doc["format_version"]); return dict(doc, format_version=doc["format_version"] + 1)
        with mock.patch.object(wspec, "FORMAT_VERSION", 3), mock.patch.dict(wspec.MIGRATIONS, {1: step, 2: step}), \
                mock.patch.object(wspec, "validate", lambda d: None):
            self.assertEqual(wspec.migrate(self.minimal())["format_version"], 3)
        self.assertEqual(calls, [1, 2])

    def test_viewer_rejects_unknown_spec_version(self):
        from formgen import viewer
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            for d in ("sheets", "previews", "specs"):
                (out / d).mkdir()
            (out / "sheets/BA01.dc.html").write_text("x"); (out / "previews/BA01.webp").write_bytes(b"x")
            (out / "specs/BA01.spec.json").write_text(json.dumps({"format": wspec.FORMAT, "format_version": 9}))
            with self.assertRaises(wspec.SpecError):
                viewer.items(out)

    def test_schema_requires_ballon_hashes(self):
        schema = wspec.schema()
        self.assertIn("ballon", schema["required"])
        self.assertEqual(set(schema["properties"]["ballon"]["required"]),
                         {"commit", "basic_id", "source_sha256", "spec_sha256", "files"})


if __name__ == "__main__":
    unittest.main()
