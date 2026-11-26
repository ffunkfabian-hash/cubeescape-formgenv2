"""0.42 Canon: Design-Kanon (Messblock aktuell, Klassen vollständig, Beispielpaket, Füllgrad mit Gegenprobe); Patch kanon-detail: Detaildichte."""
import copy
import tempfile
import unittest
from pathlib import Path

import numpy as np

from formgen import ballon, kanon

try:
    SNAP = ballon.snapshot()
except ballon.BallonError as error:   # z. B. Cloud ohne BALLON-Checkout
    SNAP, REASON = None, str(error)
else:
    REASON = ""


def _box(w, h, hole=0.0):
    """Dreiecke eines Rechtecks in der Seitenebene (Meter), optional mit Fenster (als Rahmen aus vier Streifen)."""
    def quad(y0, z0, y1, z1):
        a, b, c, d = (0, y0, z0), (0, y1, z0), (0, y1, z1), (0, y0, z1)
        return [(a, b, c), (a, c, d)]
    if not hole:
        return np.asarray(quad(0, 0, w, h), float)
    t = hole
    return np.asarray(quad(0, 0, w, t) + quad(0, h - t, w, h) + quad(0, 0, t, h) + quad(w - t, 0, w, h), float)


class KanonStaticTests(unittest.TestCase):
    def test_classes_cover_every_type_once(self):
        nums = [n for group in kanon.CLASSES.values() for n in group]
        self.assertEqual(sorted(nums), list(ballon.TYPES))

    def test_examples_exist(self):
        for name in kanon.EXAMPLES:
            self.assertTrue((kanon.ROOT / "formgen/models/extended" / f"{name}.py").is_file(), name)

    def test_doc_has_the_measurement_markers(self):
        text = kanon.DOC.read_text(encoding="utf-8")
        self.assertEqual(text.count(kanon.BEGIN), 1)
        self.assertEqual(text.count(kanon.END), 1)

    def test_fill_tells_block_from_frame(self):
        """Gegenprobe zum Füllgrad: ein volles Rechteck ist ≈ 1, derselbe Umriss als Rahmen deutlich weniger."""
        full, frame = kanon._fill(_box(0.4, 0.2)), kanon._fill(_box(0.4, 0.2, hole=0.03))
        self.assertGreater(full, 0.95)
        self.assertLess(frame, 0.6)

    def test_fill_counts_the_gap_between_separate_parts(self):
        """Richter 0.42 R1: zwei getrennte Rechtecke füllen ihr umschließendes Rechteck nur zu zwei Dritteln (Lücke im Nenner); die alte Zählung ergab ≈ 1."""
        a = _box(0.2, 0.2)
        b = a + np.array([0.0, 0.4, 0.0])
        self.assertAlmostEqual(kanon._fill(np.concatenate([a, b])), 0.2 * 0.2 * 2 / (0.6 * 0.2), delta=0.05)

    def test_detail_counts_every_element_of_a_multi(self):
        parts = [{"id": "body", "shape": "box", "mat": "shell"},
                 {"id": "screws", "shape": "multi", "mat": "trim", "items": [{"shape": "cyl"}] * 3},
                 {"id": "barrel", "shape": "cyl", "mat": "metal"}]
        self.assertEqual(kanon.detail(parts), {"parts": 3, "forms": 5, "round": 0.8, "boxy": 0.2, "mats": 3, "trim": 1})

    def test_class_follows_the_type_number(self):
        self.assertEqual([kanon.klasse(s) for s in ("BA01", "EA13", "HA04", "EA16")], ["Langwaffe", "Werfer", "Kompakt", "Nahkampf"])

    def test_pack_bundles_canon_prompt_and_examples(self):
        with tempfile.TemporaryDirectory() as tmp:
            files = kanon.pack(Path(tmp) / "paket")
            names = {f.name for f in files}
            self.assertTrue({"design-kanon.md", "kanon-stilpruefung.md", "modellsprache.md", "skins.toml"} <= names)
            self.assertEqual({f.stem for f in files if f.suffix == ".py"}, set(kanon.EXAMPLES))


@unittest.skipIf(SNAP is None, REASON)
class KanonMeasureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = kanon.measure(SNAP)

    def test_one_row_per_model(self):
        self.assertEqual([r["id"] for r in self.rows], [f"BA{n}" for n in ballon.TYPES] + [f"EA{n}" for n in ballon.TYPES])

    def test_doc_block_is_current(self):
        """Der Kanon veraltet nicht still: Ändert sich ein Modell, muss `python -m formgen.kanon messen` laufen."""
        self.assertEqual(kanon.block(kanon.DOC.read_text(encoding="utf-8")), kanon.table(self.rows).strip())

    def test_single_model_row_matches_the_family_row(self):
        """Stilprüfung misst eine neue Waffe mit measure_model; am Bestandsmodell EA06 muss das dieselbe Zeile geben (Richter 0.42 R3)."""
        from formgen import extended
        row = kanon.measure_model(extended.load("e06", SNAP), "EA06", SNAP)
        self.assertEqual(row, next(r for r in self.rows if r["id"] == "EA06"))

    def test_family_model_lies_in_its_detail_band(self):
        """Positivprobe: EA01 gegen die übrigen Langwaffen hat keinen Detailwert auf der blockigen Seite."""
        row = next(r for r in self.rows if r["id"] == "EA01")
        self.assertEqual([k for k, *_ in kanon.outside(row, self.rows) if k in kanon.ONLY], [])

    def test_counterproof_ten_slabs_fall_below_the_band(self):
        """Gegenprobe mit dem erwarteten Grund: zehn Platten aus zwei Rollen (wie die Astra-Formstudie) bei EA01-Proportionen melden
        alle sechs Detailwerte, aber keine Proportion."""
        row = dict(next(r for r in self.rows if r["id"] == "EA01"), id="HA01")
        row.update(kanon.detail([{"id": f"slab{i}", "shape": "box", "mat": ("shell", "graphite")[i % 2]} for i in range(10)]))
        keys = {k for k, *_ in kanon.outside(row, self.rows)}
        self.assertEqual(keys, set(kanon.ONLY))

    def test_counterproof_a_changed_model_is_detected(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["length"] += 1
        self.assertNotEqual(kanon.block(kanon.DOC.read_text(encoding="utf-8")), kanon.table(rows).strip())


if __name__ == "__main__":
    unittest.main()
