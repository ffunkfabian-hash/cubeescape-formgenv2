"""0.38 Foundry: EXTENDED-Linien (Register, Bau, Vielfalt wie BASIC, Zusammenhalt), Finish und Rollentest."""
import copy
import hashlib
import importlib.util
import json
import tempfile
import tomllib
import unittest
from pathlib import Path

from formgen import ballon, extended, extended_lines as XL, generator, variants, variety
from formgen.cache import canonical

ROOT = Path(__file__).resolve().parents[1]
try:
    SNAP = ballon.snapshot()
except ballon.BallonError as error:   # z. B. Cloud ohne BALLON-Checkout
    SNAP, REASON = None, str(error)
else:
    REASON = ""
PAIR_LIMIT = 0.998       # Annahme (0.38): darüber sind zwei Linien desselben Modells in Seite und Draufsicht deckungsgleich
CONTRAST_MIN = 10.0      # Annahme (0.38): ΔE76 der zwei größten Rollen, darunter liest sich das mittelgraue Bild als eine Fläche
GLOW_MIN = 25.0          # Annahme (0.38): Leuchtrolle gegen Schale, damit der Blickfang (EXTENDED-Motivtabelle) sichtbar bleibt
ENERGY = ("energy", "charge_core", "pin_glow", "draw_light")


def _render_tool():
    spec = importlib.util.spec_from_file_location("extended_render", ROOT / "tools/extended_render.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RegisterTests(unittest.TestCase):
    def setUp(self):
        self.entries = XL.load()

    def test_twelve_lines_with_frozen_ids(self):
        self.assertEqual([e["letter"] for e in self.entries], list("BCDEFGHJKLMN"))
        self.assertEqual([e["name"] for e in self.entries][:3], ["Plumb Line", "Bracket", "Ironwork"])
        self.assertEqual(len(XL.sheets(self.entries)), 12 * 17)
        self.assertEqual(XL.parse_sheet("EB01"), ("B", "e01"))
        for sid in ("EA01", "EN17"):
            self.assertRegex(sid, extended.SHEET_PATTERN)
        for bad in ("EI01", "EO05", "EB18", "BB01"):
            with self.assertRaises(XL.LineError):
                XL.parse_sheet(bad)

    def test_only_silhouette_keeping_operations(self):
        for e in self.entries:
            self.assertLessEqual(set(e["params"]), set(XL.OPS), e["letter"])
            self.assertNotIn("series", e["params"])

    def test_names_differ_from_basic_lines(self):
        basic = {v["name"].lower() for v in variants.load()}
        self.assertTrue(basic.isdisjoint(e["name"].lower() for e in self.entries))

    def test_new_rejects_what_the_register_forbids(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lines.toml"
            path.write_text("schema = 1\n")
            XL.new("B", "Test Line", "x", "0.38", "titan", {"front": [1.0, 1.1]}, path)
            for args in (("A", "Base Form", "x", "0.38", "titan", {}),                  # A ist das Modell selbst
                         ("C", "Long Reach", "x", "0.38", "titan", {}),                 # Name einer BASIC-Linie
                         ("C", "Shell Coat", "x", "0.38", "titan", {"series": "flow"}),  # Verkleidung nicht erlaubt
                         ("C", "Shell Coat", "x", "0.38", "titan", {"stock": "S1"}),     # Schafttausch nicht erlaubt
                         ("C", "Shell Coat", "x", "0.38", "unbekannt", {}),
                         ("B", "Other Line", "x", "0.38", "titan", {})):                 # Buchstabe doppelt
                with self.assertRaises(XL.LineError, msg=args[:2]):
                    XL.new(*args, path=path)
            self.assertEqual(len(tomllib.loads(path.read_text())["lines"]), 1)

    def test_every_weapon_skin_is_used_by_a_line(self):
        used = {v["skin"] for v in variants.load()} | {e["skin"] for e in self.entries}
        self.assertEqual(used, set(variants._skins()))

    def test_seed_space_is_separate_from_basic(self):
        self.assertNotEqual(XL.seed("EB01"), variants.seed("BB01"))
        a, _ = XL.resolve({"front": [0.9, 1.1]}, "EB05")
        b, _ = XL.resolve({"front": [0.9, 1.1], "mag": [0.7, 1.4]}, "EB05")
        self.assertEqual(a["front"], b["front"])                  # neuer Parameter verschiebt keine andere Ziehung


@unittest.skipIf(SNAP is None, REASON)
class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = XL.load()
        cls.built, cls.tris = {}, {}
        for key in XL.KEYS:
            for letter in ["A"] + [e["letter"] for e in cls.entries]:
                sid = XL.sheet_id(letter, key)
                model, run = XL.vary(sid, SNAP, cls.entries)
                cls.built[sid] = (model, run)
                cls.tris[sid] = variety.triangles(XL.author(model, sid)[0])

    def test_line_a_is_the_extended_model(self):
        for key in XL.KEYS:
            self.assertEqual(self.built[XL.sheet_id("A", key)][0], extended.load(key, SNAP))

    def test_every_line_differs_visibly_from_its_extended_model(self):
        """Gleiches Maß wie BASIC (variety.THRESHOLD, kleinere IoU aus Seite und Draufsicht)."""
        weak = {}
        for sid, tris in self.tris.items():
            letter, key = XL.parse_sheet(sid)
            if letter != "A":
                views = variety.iou(self.tris[XL.sheet_id("A", key)], tris)
                if not variety.visible(views):
                    weak[sid] = views
        self.assertEqual(weak, {})

    def test_no_two_lines_share_a_silhouette(self):
        """Gegenprobe zur Lehre „formgleiche Linien, die nur die Farbe wechseln“: je Modell kein deckungsgleiches Linienpaar."""
        letters = [e["letter"] for e in self.entries]
        same = {}
        for key in XL.KEYS:
            for i, a in enumerate(letters):
                for b in letters[i + 1:]:
                    views = variety.iou(self.tris[XL.sheet_id(a, key)], self.tris[XL.sheet_id(b, key)])
                    if min(views["side"], views["top"]) > PAIR_LIMIT:
                        same[f"{key} {a}-{b}"] = views
        self.assertEqual(same, {})

    def test_no_line_breaks_a_model_apart(self):
        for sid, (model, run) in self.built.items():
            base = self.built[XL.sheet_id("A", XL.parse_sheet(sid)[1])][0]
            self.assertLessEqual(XL.pieces(model["PARTS"]), XL.pieces(base["PARTS"]), sid)
        withdrawn = {sid: run["withdrawn"] for sid, (_, run) in self.built.items() if run.get("withdrawn")}
        self.assertEqual(withdrawn, {}, "Rückzug ist Notbremse, keine Linie des Registers braucht sie")

    def test_withdrawal_catches_a_detached_part(self):
        """Gegenprobe: ohne Rohr-Regel riss die Frontstreckung an EA06 die Mündungskrone ab (EB06)."""
        model, _ = generator.adapt(extended.load("e06", SNAP))
        generator.stretch_front(model, 1.2)
        self.assertGreater(XL.pieces(model["PARTS"]), XL.pieces(extended.load("e06", SNAP)["PARTS"]))
        model, _ = generator.adapt(extended.load("e06", SNAP))
        op = XL.stretch_front(model, 1.2)
        self.assertIn("muzzle", op["tubes"])
        self.assertEqual(XL.pieces(model["PARTS"]), XL.pieces(extended.load("e06", SNAP)["PARTS"]))

    def test_parts_do_not_share_cut_bodies(self):
        """EA12 teilt Profilschnitte zwischen Schale und Unterschale; geteilt verschob der Generator sie je Teil erneut (Finne EH12)."""
        def shared(parts):
            owner, out = {}, set()
            for p in parts:
                for c in p.get("cuts") or ():
                    if owner.setdefault(id(c), p["id"]) != p["id"]:
                        out.add(p["id"])
            return out
        self.assertTrue(shared(extended.load("e12", SNAP)["PARTS"]), "Gegenprobe: Grundform teilt Schnitte")
        for sid, (model, _) in self.built.items():
            if not sid.startswith("EA"):
                self.assertEqual(shared(model["PARTS"]), set(), sid)

    def test_design_contract_holds(self):
        for sid, (_, run) in self.built.items():
            if "contract" not in run:
                continue
            base, mine = run["contract"]["base"], run["contract"]["line"]
            self.assertLessEqual(len(mine["accent_functions"]), max(generator.ACCENT_LIMIT, len(base["accent_functions"])), sid)
            for socket, role in mine["hand_roles"].items():
                self.assertTrue(role in generator.HAND_ROLES or role == base["hand_roles"].get(socket), (sid, socket, role))
            before, after = base["sight_line_mm"], mine["sight_line_mm"]
            if generator._in_band(before):
                self.assertTrue(generator._in_band(after), (sid, before, after))

    def test_build_is_deterministic(self):
        for sid in ("EB01", "EE12", "EN07", "EH17"):
            again, _ = XL.vary(sid, SNAP, self.entries)
            self.assertEqual(hashlib.sha256(canonical(again)).hexdigest(),
                             hashlib.sha256(canonical(self.built[sid][0])).hexdigest(), sid)


class RoleTests(unittest.TestCase):
    """Rollentest (0.38): ein Skin bleibt auf jedem EXTENDED-Modell lesbar."""

    @classmethod
    def setUpClass(cls):
        cls.shares = {key: XL.role_shares(extended.load(key, SNAP)["PARTS"]) for key in XL.KEYS} if SNAP else {}

    @unittest.skipIf(SNAP is None, REASON)
    def test_line_skins_keep_the_two_largest_roles_apart(self):
        weak = {}
        for key, shares in self.shares.items():
            top = sorted(shares, key=lambda r: -shares[r])[:2]
            for e in XL.load():
                de = XL.delta_e(XL.role_color(top[0], e["skin"]), XL.role_color(top[1], e["skin"]))
                if de < CONTRAST_MIN:
                    weak[f"{key} {e['letter']}"] = (top, de)
        self.assertEqual(weak, {})

    @unittest.skipIf(SNAP is None, REASON)
    def test_glow_stays_visible_in_every_finish(self):
        weak = {}
        for key, shares in self.shares.items():
            for role in (r for r in shares if r in ENERGY):
                for skin in XL.skins():
                    de = XL.delta_e(XL.role_color(role, skin), XL.role_color("shell", skin))
                    if de < GLOW_MIN:
                        weak[f"{key} {role} {skin}"] = de
        self.assertEqual(weak, {})

    def test_contrast_counterproof(self):
        """Gegenprobe: Frost (Schale #14171D, Graphit #0C0D10) fällt unter die Schwelle, der Test schlägt also an."""
        self.assertLess(XL.delta_e(XL.role_color("shell", "frost"), XL.role_color("graphite", "frost")), CONTRAST_MIN)
        self.assertGreater(XL.delta_e("#FFFFFF", "#000000"), 99)

    @unittest.skipIf(SNAP is None, REASON)
    def test_shares_add_up_and_follow_the_camera(self):
        for key, shares in self.shares.items():
            self.assertAlmostEqual(sum(shares.values()), 1.0, delta=0.01, msg=key)
        self.assertGreater(self.shares["e12"]["shell"], 0.6)   # EA12: großer glatter weißer Körper (Familienprüfung 0.28)


class FinishTests(unittest.TestCase):
    def test_finish_list_is_every_weapon_skin(self):
        self.assertEqual(set(XL.skins()), set(variants._skins()))
        self.assertTrue(all(not s.get("robot") for s in XL.skins().values()))

    def test_render_wrapper_unchanged_without_finish(self):
        """Stempel der vorhandenen AAA-Bilder EA01–EA17 bleiben gültig: ohne Skin ist der Wrapper bytegleich."""
        tool = _render_tool()
        data = {"PARTS": [{"mat": "shell"}]}
        self.assertEqual(tool.wrapper(data), tool.WRAPPER)
        text = tool.wrapper(data, "titan")
        self.assertIn("kit.SKIN['name'] = job['skin']", text)
        self.assertLess(text.index("kit.SKIN"), text.index("BB.main"))

    @unittest.skipIf(SNAP is None, REASON)
    def test_preview_follows_the_finish(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = XL.preview("EA05", "side_left", "standard", (240, 160), SNAP, Path(tmp))
            b = XL.preview("EA05", "side_left", "signalrot", (240, 160), SNAP, Path(tmp))
            self.assertEqual(a.size, b.size)
            self.assertNotEqual(a.tobytes(), b.tobytes())
            self.assertEqual(len(list(Path(tmp).glob("EA05_*.png"))), 2)
            again = XL.preview("EA05", "side_left", "signalrot", (240, 160), SNAP, Path(tmp))
            self.assertEqual(again.tobytes(), b.tobytes())


if __name__ == "__main__":
    unittest.main()
