"""Die freigegebene Serie ist über denselben Einstieg wie die Einzelblätter baubar."""
import unittest
from unittest.mock import patch

from formgen import model, pipeline


class VoltSeriesTests(unittest.TestCase):
    def test_series_selects_the_four_approved_sheets(self):
        for number in ("01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11"):
            series = "Volt-" + number
            with self.subTest(series=series), patch.object(pipeline, "run") as run:
                self.assertEqual(pipeline.main(["--series", series]), 0)
                ids = list(run.call_args.args[0])
                self.assertEqual(ids, [letter + number for letter in "KLMN"])
                for sid, name in zip(ids, ("Service", "Patrol", "Ranger", "Field")):
                    author = pipeline.AUTHORED[sid]
                    info = model.normalize(author.author(None))["info"]
                    self.assertEqual((info["id"], info["nick"]), (sid, f"{series} {name}"))
                    self.assertEqual(author.make(None)["META"]["id"], sid)
