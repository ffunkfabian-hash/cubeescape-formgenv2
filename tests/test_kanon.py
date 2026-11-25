"""0.42 Canon: Design-Kanon (Messblock aktuell, Klassen vollständig, Beispielpaket, Füllgrad mit Gegenprobe)."""
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

    def test_counterproof_a_changed_model_is_detected(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["length"] += 1
        self.assertNotEqual(kanon.block(kanon.DOC.read_text(encoding="utf-8")), kanon.table(rows).strip())


if __name__ == "__main__":
    unittest.main()
