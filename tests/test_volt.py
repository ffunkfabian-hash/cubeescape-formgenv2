"""Die freigegebene Serie ist über denselben Einstieg wie die Einzelblätter baubar."""
import unittest
from unittest.mock import patch

from formgen import model, pipeline


class VoltSeriesTests(unittest.TestCase):
    def test_series_selects_the_four_approved_sheets(self):
        with patch.object(pipeline, "run") as run:
            self.assertEqual(pipeline.main(["--series", "Volt-01"]), 0)
        ids = list(run.call_args.args[0])
        self.assertEqual(ids, ["K01", "L01", "M01", "N01"])
        for sid, name in zip(ids, ("Service", "Patrol", "Ranger", "Field")):
            with self.subTest(sid=sid):
                author = pipeline.AUTHORED[sid]
                info = model.normalize(author.author(None))["info"]
                self.assertEqual((info["id"], info["nick"]), (sid, "Volt-01 " + name))
                self.assertEqual(author.make(None)["META"]["id"], sid)
