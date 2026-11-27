"""Patch basic-schnitte: geteilte Schnittkörper werden je Teil kopiert (BASIC-02, Laufkanal von pulse_chamber und handguard)."""
import copy
import unittest

from formgen import ballon, generator, variants

try:
    SNAP = ballon.snapshot()
except ballon.BallonError as error:   # z. B. Cloud ohne BALLON-Checkout
    SNAP, REASON = None, str(error)
else:
    REASON = ""


def shared(parts):
    """IDs der Teile, die ein Schnitt-Dict mit einem früheren Teil teilen."""
    owner, out = {}, set()
    for p in parts:
        for c in p.get("cuts") or ():
            if owner.setdefault(id(c), p["id"]) != p["id"]:
                out.add(p["id"])
    return out


def bore(author, pid):
    """Der zylindrische Schnitt entlang f im Teil pid (der Laufkanal)."""
    part = next(p for p in author["PARTS"] if p["id"] == pid)
    return next(c for c in part["cuts"] if c.get("shape") == "cyl" and c.get("axis") == "f")


@unittest.skipIf(SNAP is None, REASON)
class SharedCutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = ballon.load(SNAP, "02", ballon.resolve_base(SNAP, "02", "pilot"))

    def test_counterproof_a_joint_deepcopy_keeps_the_sharing(self):
        self.assertEqual(shared(copy.deepcopy(self.data["PARTS"])), {"handguard"})

    def test_adapt_copies_every_part_on_its_own(self):
        model, _ = generator.adapt(self.data)
        self.assertEqual(shared(model["PARTS"]), set())
        self.assertEqual(model["PARTS"], self.data["PARTS"])   # gleiche Werte, nur keine geteilten Objekte

    def test_bore_keeps_its_length_in_every_line(self):
        """Vorher: BC02/BE02/BG02 mit negativer Kanallänge, BB02 77 mm zu weit vorn (Schnitt je Teil erneut verschoben)."""
        ref = bore(self.data, "pulse_chamber")
        length = ref["a1"] - ref["a0"]
        for v in variants.load():
            if v["params"].get("architecture"):   # eigene Außenform (Linie T, 0.24): kein BASIC-02-Laufkanal, eigener Test unten
                continue
            author, _ = generator.build(v, "02", SNAP)
            a, b = bore(author, "pulse_chamber"), bore(author, "handguard")
            self.assertAlmostEqual(a["a1"] - a["a0"], length, places=6, msg=v["letter"])
            self.assertEqual((a["a0"], a["a1"]), (b["a0"], b["a1"]), v["letter"])

    def test_only_own_architectures_skip_the_bore(self):
        """Gegenprobe zum Ausschluss oben: übersprungen werden nur Linien, deren Typ 02 wirklich ohne BASIC-02-Laufkanal gebaut wird."""
        for v in variants.load():
            if v["params"].get("architecture") and "02" in v.get("types", ("02",)):
                author, _ = generator.build(v, "02", SNAP)
                self.assertNotIn("pulse_chamber", {p["id"] for p in author["PARTS"]}, v["letter"])


if __name__ == "__main__":
    unittest.main()
