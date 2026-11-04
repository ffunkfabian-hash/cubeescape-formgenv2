"""Design-Serien 0.8 „Hallmark“: eigene Formensprache außen auf dem Piloten, Funktion bleibt.

Orakel, unabhängig von der Schnittlogik in `series.Body.keepout`: je Blatt wird dieselbe Linie ohne `series` gebaut – alle vorhandenen Teile,
Anker, Weltpunkte müssen gleich bleiben; danach misst die Prüfung die fertigen Schalen in 3D gegen die Wege bewegter Teile, in der Seitenansicht
gegen Handkontakte und Auswurf und gegen die Sichtlinie. Gegenprobe: ohne Freizonen werden dieselben Prüfungen rot.
"""
import copy
import math
import unittest
from unittest import mock

import numpy as np

from formgen import asset, ballon, generator, series, variants, variety

try:
    SNAP = ballon.snapshot()
except ballon.BallonError as error:   # z. B. Cloud ohne BALLON-Checkout
    SNAP, REASON = None, str(error)
else:
    REASON = ""

LINES = "JKLM"
OVERLAP_MM2 = 1.0      # Rundungsrest bei der Flächenprüfung
HAND_MIN_MM = 12.0     # Schalen halten diesen Abstand zu Handkontakten (Annahme kleiner als HAND_R_MM: Prüfung, nicht Bauregel)


def entries():
    return [v for v in variants.load() if v["letter"] in LINES]


def pair(v, num):
    """(Modell mit Serie, Modell derselben Linie ohne Serie, Lauf)."""
    data = ballon.load(SNAP, num, ballon.resolve_base(SNAP, num, v.get("base", "standard")))
    drop = ("series", "sight") if num == "14" else ("series",)      # 14: Serien behalten das Seitenvisier, ohne Serie würde getauscht
    plain = dict(v, params={k: x for k, x in v["params"].items() if k not in drop})
    with_series, run = generator.vary(data, v, num, SNAP)
    without, _ = generator.vary(data, plain, num, SNAP)
    return with_series, without, run


def added(model, base):
    old = {p["id"] for p in base["PARTS"]}
    return [p for p in model["PARTS"] if p["id"] not in old]


def footprint(p):
    """Seitenansicht einer Schale mit ihren Durchbrüchen; Rahmen nur als Band (innen hohl)."""
    area = series.silhouette(p)
    for c in p.get("cuts", []):
        if c.get("shape") == "prof":
            area = area - series.silhouette(c)
    return area


def rim_boxes(p):
    """3D-Quader eines Rahmens (vier Stege) statt der vollen Außenkontur."""
    f0, f1, u0, u1, x0, x1 = series.bounds(p)
    t = (p["ow"] - p["iw"]) / 2
    return [(f0, f1, u0, u1, x0, x0 + t), (f0, f1, u0, u1, x1 - t, x1), (f0, f1, u0, u0 + t, x0, x1), (f0, f1, u1 - t, u1, x0, x1)]


def carried_hits(model, base):
    """Schalen eines bewegten Trägers über den ganzen Trägerweg gegen alles, was stehen bleibt (Grundform und feste Schalen): [(Schale, Teil)]."""
    parts = {p["id"]: p for p in model["PARTS"]}
    still = [p for p in model["PARTS"] if not p.get("parent_part") and not p.get("move") and p["asm"] != "sight"]
    still = [p for p in still if not any(q.get("id") == p.get("parent_part") for q in model["PARTS"])]
    hits = []
    for p in added(model, base):
        host = parts.get(p.get("parent_part"))
        if not host or (host.get("move") or {}).get("kind") != "translate":
            continue
        df, du = host["move"]["vector_mm"][:2]
        b, area = series.bounds(p), footprint(p)
        path = series.union([area.translate((df * k / 16, du * k / 16)) for k in range(17)])
        for q in still:
            c = series.bounds(q)
            if q is not host and b[4] < c[5] and b[5] > c[4] and (path ^ footprint(q)).area() > OVERLAP_MM2:
                hits.append((p["id"], q["id"]))
    return hits


def problems(model, base, num):
    """Fehlerliste einer Serie: Mechanik, Hände, Auswurf, Mündung, Sichtlinie (nur fertige Teile, keine Schnittlogik)."""
    bad = []
    parents = {p["id"]: p for p in base["PARTS"]}
    live = [p for p in base["PARTS"] if p.get("move") and p["move"].get("kind") in ("translate", "rotate")]
    live += [p for p in base["PARTS"] if p.get("parent_part") in {q["id"] for q in live}]
    new = added(model, base)
    A, P = base["ANCHORS"], base.get("POINTS", {})
    melee = num in ("16", "17")
    bow = any(p["asm"] == "limbs" for p in base["PARTS"])
    top = series.union([series.silhouette(p) for p in base["PARTS"] if p["asm"] != "sight" and not p.get("move")])
    body = series.Body(copy.deepcopy(base), num, None)
    for p in new:
        b = series.bounds(p)
        area = footprint(p)
        carried = p.get("parent_part")
        for q in live:
            if carried and (q["id"] == carried or q.get("parent_part") == carried):
                continue                         # Kind des bewegten Trägers läuft mit
            s = series.swept(q, parents)
            boxes = rim_boxes(p) if p["shape"] == "frame" else [b]
            for r in boxes:
                if r[4] < s[5] and r[5] > s[4]:
                    region = series.rect(r[0], r[1], r[2], r[3]) ^ area if p["shape"] == "frame" else area
                    if (region ^ series.rect(s[0], s[1], s[2], s[3])).area() > OVERLAP_MM2:
                        bad.append(f"{p['id']} im Weg von {q['id']}")
                        break
        for name, pt in P.items():
            f, u, x = pt["at"]
            if name.startswith("grip.") and (area ^ series.circle(f, u, HAND_MIN_MM)).area() > OVERLAP_MM2:
                bad.append(f"{p['id']} an Handkontakt {name}")
            if name.startswith("eject") and (x > 0) == (b[5] > 0 and b[4] >= 0) and b[4] * b[5] > 0 and \
                    (area ^ series.rect(f - 20, f + 20, u - 14, u + 14)).area() > OVERLAP_MM2:
                bad.append(f"{p['id']} vor Auswurf {name}")
        if "Socket_Muzzle" in A and not melee and not bow and b[1] > A["Socket_Muzzle"]["at"][0] - 1.0:
            bad.append(f"{p['id']} vor der Mündung")
        if "Socket_Eye" in A and abs(A["Socket_Eye"]["at"][2]) > series.SIDE_SIGHT_MM:      # BASIC-14: Blick neben dem Rohr
            ahead = [series.bounds(q) for q in base["PARTS"] if series.bounds(q)[1] > A["Socket_Eye"]["at"][0] and q["asm"] != "sight"]
            limit = max(max(abs(q[4]), abs(q[5])) for q in ahead if q[5] < A["Socket_Eye"]["at"][2] - 5) + series.TOP_MM
            if b[1] > A["Socket_Eye"]["at"][0] and max(abs(b[4]), abs(b[5])) > limit:
                bad.append(f"{p['id']} seitlich in der Sichtlinie ({max(abs(b[4]), abs(b[5])):.1f} > {limit:.1f})")
        elif "Socket_Eye" in A and not melee and not bow:
            eye = A["Socket_Eye"]["at"]
            for f in (b[0], b[1], (b[0] + b[1]) / 2):
                base_top = body.top(f, top)
                line = eye[1] - math.tan(math.radians(series.SIGHT_DEG)) * (f - eye[0]) if f > eye[0] else -1e9
                limit = max((base_top if base_top is not None else -1e9) + series.TOP_MM, line)
                here = body.top(f, area)
                if here is not None and here > limit + 0.6 and p["shape"] != "tube":
                    bad.append(f"{p['id']} über der Sichtgrenze bei f = {f:.0f} ({here:.1f} > {limit:.1f})")
    return bad


class RegisterTests(unittest.TestCase):
    def test_four_series_with_own_language_and_palette(self):
        lines = entries()
        self.assertEqual([v["letter"] for v in lines], list(LINES))
        self.assertEqual(sorted(v["params"]["series"] for v in lines), sorted(variants.SERIES))
        self.assertEqual(len({v["skin"] for v in lines}), 4)
        for v in lines:
            self.assertEqual(len(v["types"]), 17)
            self.assertEqual(v["base"], "pilot")

    def test_unknown_or_several_series_rejected(self):
        for value in ("neon", ["facet", "flow"]):
            with self.assertRaises(variants.VariantError, msg=value):
                variants.check([dict(letter="N", name="Other Line", idea="x", since="0.8", params={"series": value})])

    def test_series_languages_match_register(self):
        self.assertEqual(series.KINDS, variants.SERIES)
        self.assertEqual(set(series.LANGUAGES), set(series.KINDS))

    def test_own_skins_reach_the_bake(self):
        self.assertIsNone(asset.skin_def("kobalt"))             # BALLON-Skin: kennt der Kit selbst
        for v in entries():
            own = asset.skin_def(v["skin"])
            self.assertEqual(set(own) & {"de", "kind", "roles"}, {"de", "kind", "roles"})
            self.assertNotIn("formgen", own)
            self.assertIn("shell", own["roles"])
            self.assertIn("energy", own["roles"])                # Leuchtführung je Serie


class SweepTests(unittest.TestCase):
    """Wege gegen unabhängige Rechnung: Vollkreis analytisch, Teilbögen gegen dichte Abtastung (0,25°), beide Drehsinne."""

    def box(self, kind_range, axis="x"):
        return {"id": "t", "shape": "box", "f0": 100, "f1": 101, "u0": 50, "u1": 51, "w": 2, "x": 0,
                "move": {"kind": "rotate", "pivot": (0, 0, 0), "axis": axis, "range_deg": kind_range}}

    def test_full_turn_reaches_the_circle(self):
        r = math.hypot(101, 51)
        b = series.swept(self.box((0, 360)), {})
        for v in (b[1], b[3], -b[0], -b[2]):
            self.assertAlmostEqual(v, r, places=6)

    def test_partial_arc_matches_dense_sampling(self):
        for lo, hi in ((0, 90), (0, -12), (10, 200)):
            p = self.box((lo, hi))
            b = series.swept(p, {})
            pts = []
            for a in np.arange(min(lo, hi, -lo, -hi), max(lo, hi, -lo, -hi) + .25, .25):
                if not (min(lo, hi) <= a <= max(lo, hi) or min(-lo, -hi) <= a <= max(-lo, -hi)):
                    continue
                c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
                pts += [(f * c - u * s, f * s + u * c) for f in (100, 101) for u in (50, 51)]
            pts = np.asarray(pts)
            self.assertLessEqual(b[0], pts[:, 0].min() + 1e-9)
            self.assertGreaterEqual(b[1], pts[:, 0].max() - 1e-9)
            self.assertLessEqual(b[2], pts[:, 1].min() + 1e-9)
            self.assertGreaterEqual(b[3], pts[:, 1].max() - 1e-9)


    def test_chained_turns_reach_every_combination(self):
        """Kind dreht auf einem drehenden Eltern: Abtastung aller Winkelpaare (5°) muss in der Box liegen."""
        parent = {"id": "p", "shape": "box", "f0": 0, "f1": 1, "u0": 0, "u1": 1, "w": 1,
                  "move": {"kind": "rotate", "pivot": (0, 0, 0), "axis": "x", "range_deg": (0, 360)}}
        child = {"id": "c", "shape": "box", "f0": 30, "f1": 31, "u0": 0, "u1": 1, "w": 1, "parent_part": "p",
                 "move": {"kind": "rotate", "pivot": (20, 0, 0), "axis": "x", "range_deg": (0, 360)}}
        b = series.swept(child, {"p": parent})
        reach = 0.0
        for a1 in range(0, 360, 5):
            for a2 in range(0, 360, 5):
                for f, u in ((30, 0), (31, 0), (30, 1), (31, 1)):
                    c, s = math.cos(math.radians(a1)), math.sin(math.radians(a1))
                    q = (20 + (f - 20) * c - u * s, (f - 20) * s + u * c)
                    c, s = math.cos(math.radians(a2)), math.sin(math.radians(a2))
                    reach = max(reach, q[0] * c - q[1] * s)
        self.assertGreaterEqual(b[1], reach - 1e-9)


@unittest.skipIf(SNAP is None, REASON)
class ShellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.built = {(v["letter"], n): pair(v, n) for v in entries() for n in ballon.TYPES}

    def test_existing_parts_anchors_points_stay(self):
        for key, (model, base, run) in self.built.items():
            with self.subTest(key):
                old = {p["id"]: p for p in base["PARTS"]}
                now = {p["id"]: p for p in model["PARTS"]}
                self.assertTrue(all(now[i] == p or _only_recoloured(now[i], p) for i, p in old.items()), "vorhandenes Teil geändert")
                self.assertEqual(model["ANCHORS"], base["ANCHORS"])
                self.assertEqual(model["POINTS"], base["POINTS"])

    def test_shells_are_static_and_cover_every_type(self):
        for key, (model, base, run) in self.built.items():
            with self.subTest(key):
                new = added(model, base)
                self.assertGreaterEqual(len(new), 4, "Serie setzt zu wenig Form")
                self.assertTrue(all(not p.get("move") and not p.get("iface") for p in new))
                self.assertTrue(all(p["asm"] in {a["id"] for a in base["ASSEMBLIES"]} for p in new))
                self.assertEqual(len({p["id"] for p in model["PARTS"]}), len(model["PARTS"]))

    def test_function_stays_free(self):
        for key, (model, base, run) in self.built.items():
            with self.subTest(key):
                self.assertEqual(problems(model, base, key[1]), [])

    def test_counter_probe_without_keepouts_goes_red(self):
        v = entries()[0]
        with mock.patch.object(series.Body, "keepout", lambda *a, **k: series.CrossSection()):
            model, base, _ = pair(v, "01")
        self.assertTrue(any("im Weg" in b for b in problems(model, base, "01")))

    def test_carried_shells_clear_everything_that_stays(self):
        for v in entries():
            model, base, _ = self.built[v["letter"], "05"]
            self.assertTrue(any(p.get("parent_part") == "slide" for p in added(model, base)))
            self.assertEqual(carried_hits(model, base), [], v["letter"])

    def test_carried_shells_avoid_a_static_part_on_their_way(self):
        """Festes Teil vor der Schale, in Ruhe frei: Freizone über den Weg muss es aussparen; Gegenprobe ohne Freizonen trifft es."""
        v = entries()[0]
        data = ballon.load(SNAP, "05", ballon.resolve_base(SNAP, "05", "pilot"))
        data["PARTS"].append(dict(id="probe", de="Probe", en="Probe", asm="receiver", shape="box", mat="graphite", func="Test", attach="Test", bevel=0.5,
                                  f0=150, f1=156, u0=66, u1=76, w=6, x=16.5))
        plain = dict(v, params={k: x for k, x in v["params"].items() if k != "series"})
        base, _ = generator.vary(data, plain, "05", SNAP)
        model, _ = generator.vary(data, v, "05", SNAP)
        self.assertNotIn("probe", {h[1] for h in carried_hits(model, base)})
        with mock.patch.object(series.Body, "keepout", lambda *a, **k: series.CrossSection()):
            model, _ = generator.vary(data, v, "05", SNAP)
        self.assertIn("probe", {h[1] for h in carried_hits(model, base)})

    def test_shells_on_moving_host_follow_it(self):
        model, base, _ = self.built["J", "05"]
        carried = [p for p in added(model, base) if p.get("parent_part") == "slide"]
        self.assertTrue(carried)
        self.assertEqual(next(p for p in model["PARTS"] if p["id"] == "slide"), next(p for p in base["PARTS"] if p["id"] == "slide"))

    def test_side_sight_stays_on_rocket_launcher(self):
        for v in entries():
            model, base, run = self.built[v["letter"], "14"]
            self.assertEqual(model["ANCHORS"]["Socket_Eye"]["at"][2], 66.0, "Auge seitlich am Rohr vorbei")
            self.assertIn("skipped", next(o for o in run["ops"] if o["op"] == "sight"))

    def test_design_contract_keeps_controls(self):
        for key, (model, base, run) in self.built.items():
            with self.subTest(key):
                a, b = generator.contract(model), generator.contract(base)
                self.assertEqual(a["hand_roles"], b["hand_roles"])
                self.assertEqual(a["sight_line_mm"], b["sight_line_mm"])
                self.assertEqual(a["accent_functions"], b["accent_functions"], "Grafikblöcke zählen nicht als Bedienfunktion")

    def test_build_is_deterministic(self):
        v = entries()[3]
        self.assertEqual(pair(v, "09")[0], pair(v, "09")[0])

    def test_kit_model_keeps_points_for_ballon(self):
        v = entries()[1]
        model, run, _ = asset.variant_model({"variant": v, "num": "05"}, SNAP)
        self.assertTrue(model["POINTS"])
        self.assertTrue(any(p["id"].startswith("bench_") for p in model["PARTS"]))
        self.assertEqual(next(o for o in run["ops"] if o["op"] == "series")["kind"], "bench")


@unittest.skipIf(SNAP is None, REASON)
class VarietyTests(unittest.TestCase):
    def test_pairs_follow_the_selection(self):
        near = variety.pairs(snap=SNAP, types=("05",), letters=["J", "K"])
        self.assertEqual(list(near["05"]), ["J-K"])

    def test_each_series_clearly_differs_from_baseline(self):
        res = variety.measure(letters=list(LINES), snap=SNAP)
        self.assertEqual(len(res), 68)
        worst = max(min(r["side"], r["top"]) for r in res.values())
        self.assertLessEqual(worst, variety.SERIES_THRESHOLD)
        self.assertLess(variety.SERIES_THRESHOLD, 0.98)          # schärfer als die Schwelle aus 0.4

    def test_series_differ_from_each_other(self):
        near = variety.pairs(snap=SNAP)
        self.assertEqual(len(near), 17)
        self.assertLessEqual(max(v for row in near.values() for v in row.values()), variety.PAIR_THRESHOLD)


def _only_recoloured(new, old):
    """`_keep_accents` darf neue Baustein-Akzente entfärben; anderes nicht."""
    return {k: v for k, v in new.items() if k != "mat"} == {k: v for k, v in old.items() if k != "mat"}


if __name__ == "__main__":
    unittest.main()
