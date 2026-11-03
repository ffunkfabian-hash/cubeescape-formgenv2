"""Weltpunkte (BALLON 0.41 `POINTS`: Auswurf, Griffkontakte; Form wie ANCHORS) im Generator, 0.7 „Waypoint“.

Regel (BALLON docs/formgen-schnittstelle.md › 2): Punkte wie Anker behandeln – Dehnen/Stauchen, Spiegeln, Teiletausch, drop. Zwei
Orakel, beide unabhängig von der Punktlogik des Generators:
  - Prüfpunkte: jeder Anker bekommt einen Zwilling in POINTS (`probe.<Anker>`, gleiche Lage, gleiches Teil); nach jedem Eingriff muss
    der Zwilling genau dort stehen, wo der Generator den Anker hingelegt hat.
  - Teilbindung: ein echter Punkt behält den Versatz zum nächsten Eckpunkt seines Teils (Profilpunkt bzw. Rahmenecke in f/u).
Gegenprobe je Fall: derselbe Lauf mit festen Punkten (Verhalten 0.6, `_located` nur Anker) muss rot werden.
"""
import copy
import math
import unittest
from unittest import mock

from formgen import asset, ballon, generator, variants

try:
    SNAP = ballon.snapshot()
except ballon.BallonError as error:   # z. B. Cloud ohne BALLON-Checkout
    SNAP, REASON = None, str(error)
else:
    REASON = ""

TOL = 1e-6


def pilot(num):
    return ballon.load(SNAP, num, ballon.resolve_base(SNAP, num, "pilot"))


def vary(data, params, num):
    return generator.vary(data, {"letter": "X", "params": params}, num, SNAP)


def fixed_points():
    """Gegenprobe: Punkte bleiben stehen (0.6 kannte nur Anker)."""
    return mock.patch.object(generator, "_located", lambda model: list(model["ANCHORS"].values()))


def probed(data, names=None):
    d = copy.deepcopy(data)
    d.setdefault("POINTS", {})
    for n, a in d["ANCHORS"].items():
        if names is None or n in names:
            d["POINTS"][f"probe.{n}"] = {"at": tuple(a["at"]), "part": a["part"]}
    return d


def close(a, b, tol=TOL):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def probe_errors(model):
    """Prüfpunkte, die nicht auf ihrem Anker stehen (Anker ersetzt: kein Vergleich)."""
    return {n: (tuple(q["at"]), tuple(model["ANCHORS"][n[6:]]["at"])) for n, q in model["POINTS"].items()
            if n.startswith("probe.") and n[6:] in model["ANCHORS"] and not close(q["at"], model["ANCHORS"][n[6:]]["at"])}


def _verts(p):
    if p.get("shape") == "prof":
        return [tuple(q[:2]) for q in p["pts"]]
    (f0, f1), (u0, u1) = generator._extent(p, 0), generator._extent(p, 1)
    return [(f0, u0), (f0, u1), (f1, u0), (f1, u1)]


def binding_errors(before, after):
    """Echte Punkte, deren Versatz zum nächsten Eckpunkt ihres Teils sich geändert hat (Teil gleich geblieben)."""
    B, A = {p["id"]: p for p in before["PARTS"]}, {p["id"]: p for p in after["PARTS"]}
    bad = {}
    for n, q in after["POINTS"].items():
        q0 = before["POINTS"].get(n)
        if q0 is None or n.startswith("probe.") or q["part"] != q0["part"] or q["part"] not in A:
            continue
        v0, v1 = _verts(B[q0["part"]]), _verts(A[q["part"]])
        if len(v0) != len(v1):
            continue
        i = min(range(len(v0)), key=lambda k: math.dist(v0[k], q0["at"][:2]))
        want = (v1[i][0] + q0["at"][0] - v0[i][0], v1[i][1] + q0["at"][1] - v0[i][1], q0["at"][2])
        if not close(want, q["at"]):
            bad[n] = (tuple(q["at"]), want)
    return bad


@unittest.skipIf(SNAP is None, REASON)
class PointSourceTests(unittest.TestCase):
    def test_pilots_carry_points_on_existing_parts(self):
        for num in ballon.TYPES:
            with self.subTest(num=num):
                data = pilot(num)
                ids = {p["id"] for p in data["PARTS"]}
                self.assertEqual(bool(data["POINTS"]), num not in ("16", "17"))      # Formstudien ohne Piloten: keine Punkte
                self.assertTrue(all(q["part"] in ids and len(q["at"]) == 3 for q in data["POINTS"].values()))
                if data["POINTS"]:
                    self.assertIn("grip.grip", data["POINTS"])

    def test_line_a_keeps_ballons_points(self):
        for num in ballon.TYPES:
            with self.subTest(num=num):
                model, _, _ = asset.variant_model(variants.sheets()[f"BA{num}"], SNAP)
                self.assertEqual(model["POINTS"], pilot(num)["POINTS"])


@unittest.skipIf(SNAP is None, REASON)
class PointMoveTests(unittest.TestCase):
    def check(self, num, params, data=None, moved_min=1):
        """Lauf mit Prüfpunkten: alle stehen auf ihren Ankern, mindestens `moved_min` haben sich bewegt; Gegenprobe rot."""
        data = probed(data or pilot(num))
        model, run = vary(data, params, num)
        self.assertEqual(probe_errors(model), {})
        self.assertEqual(binding_errors(data, model), {})
        moved = [n for n, q in model["POINTS"].items() if n in data["POINTS"] and not close(q["at"], data["POINTS"][n]["at"])]
        self.assertGreaterEqual(len(moved), moved_min, run["ops"])
        with fixed_points():
            stuck, _ = vary(data, params, num)
        self.assertTrue(probe_errors(stuck) or binding_errors(data, stuck), "Gegenprobe: feste Punkte fallen nicht auf")
        return model, run, moved

    def test_front_stretch_and_compress(self):
        for factor in (1.3, 0.85):
            with self.subTest(factor=factor):
                _, run, moved = self.check("01", {"front": factor})
                self.assertIn("probe.Socket_Muzzle", moved)
                self.assertEqual(run["ops"][0]["points_moved"].keys(), set(moved))

    def test_rear_stretch_and_compress_mirror_back(self):
        # hinten wird gespiegelt geschnitten: Punkte am Schaft gehen hin und zurück durch _mirror
        data = pilot("09")
        data["POINTS"]["test.shoulder"] = {"at": (generator._extent(next(p for p in data["PARTS"] if p["id"] == "butt_pad"))[0],
                                                  80.0, 0.0), "part": "butt_pad"}
        for factor in (1.2, 0.85):
            with self.subTest(factor=factor):
                model, run = vary(probed(data), {"rear": factor}, "09")
                self.assertEqual(probe_errors(model), {})
                delta = run["ops"][0]["delta_mm"]
                self.assertNotEqual(delta, 0)
                self.assertAlmostEqual(model["POINTS"]["test.shoulder"]["at"][0], data["POINTS"]["test.shoulder"]["at"][0] - delta,
                                       places=3)                                    # delta_mm im Bericht auf µm gerundet
                with fixed_points():
                    stuck, _ = vary(probed(data), {"rear": factor}, "09")
                self.assertAlmostEqual(stuck["POINTS"]["test.shoulder"]["at"][0], data["POINTS"]["test.shoulder"]["at"][0])

    def test_mirror_is_symmetric(self):
        model = generator.adapt(pilot("01"))[0]
        start = copy.deepcopy(model["POINTS"])
        generator._mirror(model, 1)
        self.assertTrue(all(close(model["POINTS"][n]["at"], (q["at"][0], -q["at"][1], q["at"][2])) for n, q in start.items()))
        generator._mirror(model, 1)
        self.assertEqual({n: tuple(q["at"]) for n, q in model["POINTS"].items()}, {n: tuple(q["at"]) for n, q in start.items()})

    def test_bow_limbs_move_points_on_both_arms(self):
        # Wurfarme in u, unten über _mirror(ax=1). Nockpunkt (grip.nock, string_top bei u ≈ 0) liegt vor beiden Schnitten und bleibt
        # wie Socket_Nock; Punkte an den Rollen (verschoben) wandern oben +delta, unten −delta
        data = pilot("07")
        P = {p["id"]: p for p in data["PARTS"]}
        for cam in ("cam_top", "cam_bottom"):
            (f0, f1), (u0, u1) = generator._extent(P[cam], 0), generator._extent(P[cam], 1)
            data["POINTS"][f"test.{cam}"] = {"at": ((f0 + f1) / 2, (u0 + u1) / 2, 0.0), "part": cam}
        model, run, moved = self.check("07", {"limbs": 1.2}, data=data, moved_min=2)
        top, bottom = run["ops"][0]["sides"]
        self.assertEqual(set(moved), {"test.cam_top", "test.cam_bottom"})
        self.assertAlmostEqual(model["POINTS"]["test.cam_top"]["at"][1] - data["POINTS"]["test.cam_top"]["at"][1], top["delta_mm"], places=3)
        self.assertAlmostEqual(model["POINTS"]["test.cam_bottom"]["at"][1] - data["POINTS"]["test.cam_bottom"]["at"][1], -bottom["delta_mm"],
                               places=3)
        self.assertTrue(close(model["POINTS"]["grip.nock"]["at"], data["POINTS"]["grip.nock"]["at"]))

    def test_muzzle_length(self):
        _, run, moved = self.check("01", {"muzzle": 1.6})
        self.assertIn("probe.Socket_Muzzle", moved)

    def test_mag_moves_grip_contact_along_removal(self):
        data = pilot("02")                                                     # 01 hat kein Stangenmagazin mit Entnahme
        model, run = vary(data, {"mag": 0.8}, "02")
        op = run["ops"][0]
        d, delta = op["direction"], op["delta_mm"]
        at0, at1 = data["POINTS"]["grip.mag"]["at"], model["POINTS"]["grip.mag"]["at"]
        self.assertTrue(close(at1, (at0[0] + d[0] * delta, at0[1] + d[1] * delta, at0[2]), 1e-2), (at0, at1))   # Bericht gerundet
        self.assertEqual(op["points_moved"], {"grip.mag": [round(at1[i] - at0[i], 3) for i in range(3)]})
        self.assertEqual(binding_errors(data, model), {})
        with fixed_points():
            stuck, _ = vary(data, {"mag": 0.8}, "02")
        self.assertIn("grip.mag", binding_errors(data, stuck))

    def test_all_registered_sheets_keep_points_bound(self):
        moved = []
        for sid, entry in sorted(variants.sheets().items()):
            num = entry["num"]
            base = pilot(num)
            model, run, _ = asset.variant_model(entry, SNAP)
            with self.subTest(sid=sid):
                self.assertEqual(binding_errors(base, model), {})
                self.assertTrue(set(model["POINTS"]) == set(base["POINTS"]))
            if any(o.get("points_moved") for o in run["ops"]):
                moved.append(sid)
                with fixed_points():
                    stuck, _, _ = asset.variant_model(entry, SNAP)
                self.assertTrue(binding_errors(base, stuck), f"Gegenprobe {sid}")
        self.assertGreaterEqual(len(moved), 10, moved)          # Linien C, E, F, G, H mit Magazin: grip.mag


@unittest.skipIf(SNAP is None, REASON)
class PointSwapTests(unittest.TestCase):
    def test_sight_swap_hands_point_to_new_part(self):
        data = pilot("01")
        eye = data["ANCHORS"]["Socket_Eye"]
        data["POINTS"]["test.sight"] = {"at": tuple(eye["at"]), "part": eye["part"]}
        model, run = vary(data, {"sight": "holo_kasten"}, "01")
        op = run["ops"][0]
        self.assertNotIn("skipped", op)
        old, new = op["points_handed"]["test.sight"]
        self.assertEqual(old, eye["part"])
        self.assertIn(new, op["added"])                                     # Holo-Kasten führt sight_frame ebenfalls
        self.assertEqual(model["POINTS"]["test.sight"], {"at": tuple(eye["at"]), "part": new})

    def test_replace_hands_point_to_nearest_new_part(self):
        model = generator.adapt(pilot("01"))[0]
        P = {p["id"]: p for p in model["PARTS"]}
        at = model["POINTS"]["grip.charge"]["at"]
        near = dict(copy.deepcopy(P["charging_handle"]), id="new_near", parent_part=None)
        far = dict(copy.deepcopy(P["muzzle_crown"]), id="new_far", parent_part=None)
        removed, _, handed = generator._replace(model, ["charging_handle"], [far, near])
        self.assertEqual(handed, {"grip.charge": ["charging_handle", "new_near"]})
        self.assertEqual(model["POINTS"]["grip.charge"], {"at": at, "part": "new_near"})
        model = generator.adapt(pilot("01"))[0]                              # Gegenprobe: falsch zugeordnet fiele auf
        with mock.patch.object(generator, "_nearest", lambda parts, at: "new_far"):
            generator._replace(model, ["charging_handle"], [far, near])
        self.assertNotEqual(model["POINTS"]["grip.charge"]["part"], "new_near")

    def test_stock_swap_keeps_point_on_same_id_or_nearest(self):
        data = pilot("01")
        pad = next(p for p in data["PARTS"] if p["id"] == "butt_pad")
        data["POINTS"]["test.shoulder"] = {"at": (generator._extent(pad)[0], 90.0, 0.0), "part": "butt_pad"}
        model, run = vary(data, {"stock": "S2"}, "01")
        op = run["ops"][0]
        self.assertNotIn("skipped", op)
        self.assertEqual(op["points_handed"]["test.shoulder"][0], "butt_pad")
        self.assertIn(model["POINTS"]["test.shoulder"]["part"], op["added"])
        self.assertEqual(model["POINTS"]["test.shoulder"]["part"], "butt_pad")           # S2 führt ebenfalls butt_pad

    def test_grip_swap_on_study(self):
        data = ballon.load(SNAP, "01")                                                   # Formstudie: grip_rifle
        data["POINTS"] = {"test.grip": {"at": tuple(data["ANCHORS"]["Socket_Hand"]["at"]), "part": "grip"}}
        model, run = vary(data, {"grip": "v21"}, "01")
        op = run["ops"][0]
        self.assertNotIn("skipped", op)
        self.assertEqual(op["points_handed"], {"test.grip": ["grip", "grip"]})
        self.assertIn("grip", {p["id"] for p in model["PARTS"]})

    def test_replace_without_new_parts_is_an_error(self):
        model = generator.adapt(pilot("01"))[0]
        with self.assertRaises(generator.GeneratorError):
            generator._replace(model, ["magazine"], [])


@unittest.skipIf(SNAP is None, REASON)
class PointDropTests(unittest.TestCase):
    def test_drop_protects_point_parts(self):
        data = pilot("01")
        target = data["POINTS"]["grip.support"]["part"]
        model, run = vary(data, {"drop": [target]}, "01")
        op = run["ops"][0]
        self.assertEqual(op["dropped"], [])
        self.assertIn("Weltpunkt", op["protected_why"][target])
        self.assertIn(target, {p["id"] for p in model["PARTS"]})
        # Gegenprobe: ohne Schutz fiele das Teil weg, und der Punkt zeigte ins Leere (_finish bricht ab)
        bare = generator.adapt(data)[0]
        points = bare.pop("POINTS")
        generator.drop(bare, [target])
        bare["POINTS"] = points
        with self.assertRaises(ValueError):
            generator._finish(bare, [])


@unittest.skipIf(SNAP is None, REASON)
class KitModelPointTests(unittest.TestCase):
    def test_kit_model_carries_moved_points(self):
        model, run, _ = asset.variant_model(variants.sheets()["BC02"], SNAP)
        base = pilot("02")
        self.assertEqual(set(model["POINTS"]), set(base["POINTS"]))
        self.assertNotEqual(model["POINTS"]["grip.mag"], base["POINTS"]["grip.mag"])
        self.assertEqual({n: q for n, q in model["POINTS"].items() if n != "grip.mag"},
                         {n: q for n, q in base["POINTS"].items() if n != "grip.mag"})

    def test_ballon_accepts_points(self):
        """BALLONs eigene Prüfung (basic/variant.problems, as_module → resolve) auf allen Paket-Datensätzen."""
        import importlib
        import json
        import sys
        ballon._purge()
        sys.path.insert(0, str(SNAP))
        try:
            VA = importlib.import_module("basic.variant")
            for sid, entry in sorted(variants.sheets().items()):
                if entry["num"] in ("16", "17"):
                    continue
                model, _, base = asset.variant_model(entry, SNAP)
                model = json.loads(json.dumps(model))                    # wie im Paket: JSON (Tupel → Listen)
                module = ".".join(ballon.module_file(SNAP, entry["num"], base).relative_to(SNAP).with_suffix("").parts)
                W = VA.as_module(model, importlib.import_module(module), name=f"basic.variant.{sid}")
                with self.subTest(sid=sid):
                    self.assertEqual(VA.problems(W), [])
                    if "grip.mag" in model["POINTS"]:
                        grips = getattr(W, "EGO_GRIPS", None) or importlib.import_module("basic.arms.ego").GRIPS
                        self.assertTrue(close(grips["mag"]["contact"], model["POINTS"]["grip.mag"]["at"]))
        finally:
            sys.path.remove(str(SNAP))
            ballon._purge()


if __name__ == "__main__":
    unittest.main()
