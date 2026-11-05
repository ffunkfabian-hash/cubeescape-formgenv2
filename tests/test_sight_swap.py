"""Visiertausch 0.8.1: Sitz auf der Seitenschiene statt im Rohr, Leuchtbewegung bleibt."""
import math
import unittest

from formgen import ballon, generator, raster, variants


def build(sid):
    snap = ballon.snapshot()
    entry = variants.sheets()[sid]
    data = ballon.load(snap, entry["num"], ballon.resolve_base(snap, entry["num"], "pilot"))
    model, run = generator.vary(data, entry["variant"], entry["num"], snap)
    return model, {p["id"]: p for p in model["PARTS"]}, next((o for o in run["ops"] if o["op"] == "sight"), None)


class SightSwap(unittest.TestCase):
    def test_sight_sits_on_side_rail_like_pilot(self):
        pilot = build("BA14")[0]["ANCHORS"]["Socket_Eye"]["at"]
        for sid in ("BE14", "BF14", "BG14", "BH14"):
            with self.subTest(sid):
                model, parts, op = build(sid)
                tube, eye = parts["tube"], model["ANCHORS"]["Socket_Eye"]["at"]
                self.assertEqual(op["side_mm"], 66.0)
                self.assertEqual(tuple(eye[1:]), tuple(pilot[1:]))
                self.assertGreater(math.hypot(eye[1] - tube["c"][0], eye[2]), tube["r"])     # 0.8: Auge im Rohr
                self.assertTrue({"rail", "sight_arm", "sight_collar"} <= set(parts))

    def test_no_side_shift_on_centre_rail(self):
        """Gegenprobe: an einer Mittelschiene bleibt der Baustein auf der Mittelebene."""
        model, _, op = build("BE01")
        self.assertNotIn("side_mm", op)
        self.assertEqual(model["ANCHORS"]["Socket_Eye"]["at"][2], 0)

    def test_series_keep_side_sight(self):
        for sid in ("BJ14", "BK14", "BL14", "BM14"):
            model, _, op = build(sid)
            self.assertIn("skipped", op, sid)
            self.assertEqual(model["ANCHORS"]["Socket_Eye"]["at"][2], 66.0, sid)

    def test_emitter_keeps_charge_glow(self):
        glow = build("BA10")[1]["sight_emitter"]["move"]
        self.assertEqual(glow["kind"], "glow")
        for sid in ("BE10", "BF10", "BG10", "BH10", "BJ10", "BK10", "BL10"):
            _, parts, op = build(sid)
            self.assertEqual(parts["sight_emitter"]["move"], glow, sid)
            self.assertEqual(op["glow_kept"], ["sight_emitter"], sid)
        self.assertNotIn("glow_kept", build("BM10")[2])          # Bögen bringt die Bewegung selbst mit

    def test_drum_exception_names_a_real_part(self):
        self.assertTrue(set(raster.NO_EDGE_LIFT) <= set(build("BA04")[1]))
