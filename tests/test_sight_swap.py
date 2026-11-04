"""Visiertausch 0.8.1: Sitz auf dem Rohr statt im Rohr, Leuchtbewegung bleibt."""
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
    def test_sight_rests_on_tube(self):
        for sid in ("BE14", "BF14", "BG14", "BH14"):
            with self.subTest(sid):
                model, parts, op = build(sid)
                tube, eye = parts["tube"], model["ANCHORS"]["Socket_Eye"]["at"]
                self.assertEqual(op["seat"], {"part": "tube", "u_mm": 158.0})
                self.assertGreater(math.hypot(eye[1] - tube["c"][0], eye[2]), tube["r"])     # 0.8: Auge im Rohr
                self.assertTrue(generator._in_band(op["sight_line_mm"]["after"]))
                self.assertFalse({"rail", "sight_arm"} & set(parts))
                self.assertIn("sight_collar", parts)

    def test_series_keep_side_sight(self):
        for sid in ("BJ14", "BK14", "BL14", "BM14"):
            model, _, op = build(sid)
            self.assertIn("skipped", op, sid)
            self.assertEqual(model["ANCHORS"]["Socket_Eye"]["at"][2], 66.0, sid)

    def test_seat_is_tube_not_clamp(self):
        """Gegenprobe: ohne Rohr wäre die kürzere Schelle der Sitz, die Auswahl hängt also an der Länge."""
        model = build("BA14")[0]
        self.assertEqual(generator._tube_top(model, 20), ("tube", 158.0))
        model["PARTS"] = [p for p in model["PARTS"] if p["id"] != "tube"]
        self.assertEqual(generator._tube_top(model, 20), ("sight_collar", 161.0))

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
