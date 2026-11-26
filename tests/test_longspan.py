"""VA01: unabhängiger Autorenentwurf und Familienanschlüsse."""
from pathlib import Path
from unittest import mock
import json
import tempfile
import unittest

from formgen import ballon, build, extended, kanon, model, pipeline
from formgen.models.weapons import va01_longspan


class LongspanRegisterTests(unittest.TestCase):
    def test_id_and_basic_selection(self):
        self.assertIs(pipeline.AUTHORED["VA01"], va01_longspan)
        self.assertEqual(kanon.klasse("VA01"), "Langwaffe")
        self.assertNotIn("VA01", extended.SHEETS.values())
        self.assertEqual(list(pipeline.select(["BA01", "VA01"])), ["BA01", "VA01"])
        self.assertNotIn("VA01", pipeline.select(letters=["A"]))

    def test_canonical_edge_weights(self):
        outline = dict(shape="prof", pts=[(0,0),(40,0),(40,30)])
        self.assertEqual(kanon.clarity([outline]), {"axis": .58, "dirs": 1.0})


class LongspanModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.snap = ballon.snapshot()
        except ballon.BallonError as error:
            raise unittest.SkipTest(str(error)) from error
        cls.raw = va01_longspan.make(cls.snap)

    def test_detail_and_clarity(self):
        parts = self.raw["PARTS"]
        detail = kanon.detail(parts)
        self.assertGreaterEqual(detail["parts"], 57)
        self.assertGreaterEqual(detail["forms"], 94)
        self.assertGreaterEqual(detail["round"], .22)
        self.assertLessEqual(detail["boxy"], .37)
        self.assertGreaterEqual(detail["mats"], 11)
        self.assertGreaterEqual(detail["trim"], 1)
        clarity = kanon.clarity(parts)
        self.assertGreaterEqual(clarity["axis"], .74)
        self.assertGreaterEqual(clarity["dirs"], .90)

    def test_build_document_retains_identity_and_functions(self):
        doc = model.normalize(va01_longspan.author(self.snap))
        self.assertEqual(doc["info"]["id"], "VA01")
        self.assertTrue(all(p["func"] and p["role"] and "bevel" in p for p in doc["parts"]))
        self.assertEqual(len(extended.components(self.raw["PARTS"])), 1)
        self.assertEqual(doc["anchors"]["Socket_SupportHand"]["part"], "palm")
        self.assertEqual(doc["anchors"]["Socket_Hand"]["part"], "grip")


    def test_pipeline_builds_and_reuses_the_native_spec(self):
        selected = pipeline.select(["VA01"])
        with tempfile.TemporaryDirectory() as tmp:
            out, cache = Path(tmp) / "out", Path(tmp) / "cache"
            args = dict(stages=["geometry", "specs"], snap=self.snap, log=lambda _: None)
            pipeline.run(selected, out, cache, **args)
            spec = json.loads((out / "specs/VA01.spec.json").read_text())
            self.assertEqual(spec["sheet"]["id"], "VA01")
            self.assertEqual(spec["weapon"]["toolgen_id"], "assault_rifle")
            self.assertEqual(spec["source"]["ballon_commit"], ballon.config()["commit"])
            self.assertEqual(spec["sheet"]["nick"], "Longspan")
            _, reuse = pipeline.run(selected, out, cache, **args)
            self.assertEqual(reuse["built"], 0)

    def test_default_raster_build_and_mixed_catalog(self):
        # Normaler Stufenweg mit kleinen echten Rasterbildern für die Quick-Suite.
        parameters = build.view_parameters

        def small_view(doc, name, **options):
            return parameters(doc, name, **{**options, "width": 96, "height": 64})

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(build, "view_parameters", small_view):
            out, cache = Path(tmp) / "out", Path(tmp) / "cache"
            basic = pipeline.select(["BA01"])
            pipeline.run(basic, out, cache, stages=["specs", "sheets", "previews"], snap=self.snap)
            self.assertEqual(pipeline.main(["VA01", "--out", str(out), "--cache", str(cache), "--jobs", "1"]), 0)
            for name in ("side_left", "top", "front", "back"):
                self.assertTrue((out / "views" / "VA01" / (name + ".png")).is_file())
            for path in ("index.html", "previews/VA01.webp", "sheets/VA01.dc.html", "prompts/VA01.prompts.json"):
                self.assertGreater((out / path).stat().st_size, 0)
            weapons = (out / "waffen.html").read_text()
            self.assertIn('href="sheets/VA01.dc.html"', weapons)
            self.assertIn('href="sheets/BA01.dc.html"', weapons)
            self.assertIn('<option value="A">A · Baseline</option>', weapons)
            self.assertIn('<option value="VA01">VA01 · Longspan</option>', weapons)
