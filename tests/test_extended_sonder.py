"""EXTENDED-07 „Caliper“ und EXTENDED-12 „Shuttle“ (0.28 „Quiver“): Kampfbogen und Spurgewehr als eigene Modelle.

Prüft die Datensätze ohne Blender: Felder und IDs, Blatt-IDs, Anker/Weltpunkte/Aktionen (BALLONs `variant.problems` als Orakel),
Familienschnittstellen, Budgets des Stilhandbuchs (genau ein Blickfang, ≤ 3 Akzent-Bedienfunktionen, eine Schrift, ein Grafikelement),
Visierlinie (B1 69,5 mm über dem Pfeil wie BASIC-07, H3 66 ± 4 mm über der Strahlachse), Sichtkegel des Bogens, Seiten-IoU < 0,85 gegen
BASIC-NN und jedes andere EXTENDED-Modell und < 0,70 im Paar (Rahmen aus den Hüllen beider Modelle; Standardmaß und genaues Maß mit den
Seitenschnitten der Querprofile), die Leitmotive (Klammer: Deflex-Bügel mit fast parallelen Wurfarmen; Weberschiffchen: Spindel mit
Auge und Spule auf der Strahlachse), Visierbefestigung, keine dünnen Stifte (begründete Ausnahme: die Sehne), gestaltete Querschnitte,
Detaildichte, die Absetzung der beiden Typen, Zusammenhang, Größe und Quellhash. Jede Regelprüfung hat eine Gegenprobe, die aus dem
erwarteten Grund rot wird; Felder, Quellhash und Snapshot-Freigabe sind Bestandsprüfungen.
"""
import copy
import importlib
import math
import re
import sys
import unittest

from formgen import ballon, extended
from tests.test_extended_schulter import as_side, crossing, forms, frame, iou, iou_exact, length, width_at

try:
    SNAP = ballon.snapshot()
except ballon.BallonError as error:   # z. B. Cloud ohne BALLON-Checkout
    SNAP, REASON = None, str(error)
else:
    REASON = ""

IOU_MAX = 0.85                 # Annahme wie BALLON A1 und test_extended
PAIR_MAX = 0.70                # Annahme wie 0.18–0.25: die beiden Typen einer Sitzung setzen sich deutlich ab
SIGHT_H = (62.0, 70.0)         # Vorgabe Visier-Standard: Visierhöhe 66 ± 4 mm
STICK_D = 12.0                 # Vorgabe Nutzer 0.25: Funktionsteile unter Ø 12 mm lesen sich als Fremdkörper
LIGHT_MATS = ("energy", "draw_light")
OWN = {"e07": dict(num="07", type="combat_bow", id="EXTENDED-07", sheet="EA07", mod="e07_caliper"),
       "e12": dict(num="12", type="trace_rifle", id="EXTENDED-12", sheet="EA12", mod="e12_shuttle")}


def lights(parts):
    return sorted(p["id"] for p in parts if p["mat"] in LIGHT_MATS and p["asm"] != "sight")


def accent_functions(parts):
    return sorted({p["id"] for p in parts if p["mat"] == "accent" and p.get("move") and p["asm"] != "sight"})


def graphics(parts):
    return [p["id"] for p in parts if p["mat"] == "accent" and not p.get("move") and p["asm"] not in ("sight", "arrow")]


def height(parts):
    bs = [b for p in parts if (b := extended.bounds(p))]
    return max(b[1][1] for b in bs) - min(b[0][1] for b in bs)


def sticks(parts, exempt=("sight", "string", "arrow")):
    """Sichtbare Stifte: Zylinder oder Leitungen unter Ø 12 mm, länger als das Vierfache ihres Durchmessers; Schrauben, Bolzen und
    Achsen (blank/Metall, höchstens 45 mm) zählen nicht. Begründete Ausnahme: Sehne (eine Sehne ist dünn), Pfeil und Visierbaustein."""
    out = []
    for p in parts:
        if p["asm"] in exempt:
            continue
        for q in p["items"] if p["shape"] == "multi" else [p]:
            k = q.get("shape", p["shape"])
            if k == "cyl":
                d, L = 2 * max(q["r"], q.get("r1", q["r"])), abs(q["a1"] - q["a0"])
            elif k == "tube":
                d = 2 * q["r"]
                L = sum(math.dist(a, b) for a, b in zip(q["path"], q["path"][1:]))
            else:
                continue
            if p["mat"] in ("trim", "metal") and L <= 45:
                continue
            if d < STICK_D and L > 4 * d:
                out.append(p["id"])
    return sorted(set(out))


@unittest.skipIf(SNAP is None, REASON)
class TestSonder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = {k: extended.load(k, SNAP) for k in OWN}
        cls.basic = {k: extended.load_basic(OWN[k]["num"], SNAP) for k in OWN}
        cls.others = {k: extended.load(k, SNAP)["PARTS"] for k in extended.MODELS if k not in OWN}
        cls.ids = {k: {p["id"]: p for p in d["PARTS"]} for k, d in cls.data.items()}
        sys.path.insert(0, str(SNAP))
        try:
            cls.mods = {k: importlib.import_module(extended.module_name(k)) for k in OWN}
            cls.consts = {k: {n: getattr(m, n) for n in dir(m) if not n.startswith('__')} for k, m in cls.mods.items()}
        finally:
            sys.path.remove(str(SNAP))
            extended._purge(tuple(extended.module_name(k) for k in OWN))

    # ---------------------------------------------------------------- Felder, IDs, Anker
    def test_fields_and_ids(self):
        for k, o in OWN.items():
            with self.subTest(k):
                d, ids = self.data[k], self.ids[k]
                self.assertEqual(extended.MODELS[k], o["mod"])
                self.assertEqual(d["META"]["id"], o["id"])
                self.assertEqual(d["META"]["type"], o["type"])
                self.assertEqual(d["META"]["type"], self.basic[k]["META"]["type"], "Typ wie BASIC-NN")
                self.assertEqual(d["META"]["fire"], self.basic[k]["META"]["fire"], "Feuerart wie BASIC-NN")
                self.assertEqual(len(ids), len(d["PARTS"]), "Teil-IDs doppelt")
                asms = {a["id"] for a in d["ASSEMBLIES"]}
                self.assertEqual(asms, {a["id"] for a in self.basic[k]["ASSEMBLIES"]}, "Baugruppen wie BASIC-NN")
                self.assertEqual({p["asm"] for p in d["PARTS"]} - asms, set())
                for p in d["PARTS"]:
                    if p.get("parent_part"):
                        self.assertIn(p["parent_part"], ids, p["id"])
                self.assertIsNone(d["EJECT"], "Bogen und Energiewaffe ohne Auswurf wie BASIC-NN")
        dup = self.data["e07"]["PARTS"] + [dict(self.ids["e07"]["sight_sled"], id="sight_clamp")]   # Gegenprobe: Stand vor der Umbenennung
        self.assertLess(len({p["id"] for p in dup}), len(dup))

    def test_sheet_ids(self):
        for k, o in OWN.items():
            self.assertEqual(extended.sheet_id(k), o["sheet"])
            self.assertEqual(self.data[k]["META"]["sheet_id"], o["sheet"])
            self.assertRegex(o["sheet"], f"^{extended.SHEET_PATTERN}$")
        sids = list(extended.SHEETS.values())
        self.assertEqual(len(set(sids)), len(sids), "Blatt-IDs doppelt")
        self.assertEqual(set(extended.SHEETS), set(extended.MODELS))
        self.assertIsNone(re.match(f"^{extended.SHEET_PATTERN}$", "EO07"))   # Gegenprobe: Linienbuchstabe O ist gesperrt

    def test_anchors_points_actions(self):
        sys.path.insert(0, str(SNAP))
        try:
            variant = importlib.import_module("basic.variant")
            for k, d in self.data.items():
                with self.subTest(k):
                    A, ids = d["ANCHORS"], self.ids[k]
                    self.assertEqual(set(A), set(self.basic[k]["ANCHORS"]), "Anker wie BASIC-NN")
                    for name, a in A.items():
                        self.assertIn(a["part"], ids, name)
                    self.assertEqual(tuple(A["Socket_Hand"]["at"]), (0, 0, 0))
                    self.assertEqual(set(d["POINTS"]), set(self.basic[k]["POINTS"]), "Weltpunkte wie BASIC-NN")
                    self.assertEqual(set(d["ACTIONS"]), set(self.basic[k]["ACTIONS"]), "Aktionen wie BASIC-NN")
                    for name, act in d["ACTIONS"].items():
                        for pid in act["keys"]:
                            self.assertIn("move", ids[pid], f"{name}: {pid} ohne Bewegung")
                    self.assertEqual(variant.problems(variant.as_module(copy.deepcopy(d))), [])
                    bad = copy.deepcopy(d)   # Gegenprobe: Griffpunkt auf ein fehlendes Teil
                    bad["POINTS"]["grip.grip"]["part"] = "kein_teil"
                    self.assertTrue(any("kein_teil" in m for m in variant.problems(variant.as_module(bad))))
        finally:
            sys.path.remove(str(SNAP))
            extended._purge()

    def test_family_interfaces(self):
        want = {"e07": {"rail": "BRI-22"}, "e12": {"grip": "BGM-1", "rail": "BRI-22", "energy_cell": "BEC-1", "shell": "BST-T"}}

        def problems(ids, w):
            return [pid for pid, iface in w.items() if ids.get(pid, {}).get("iface") != iface]
        for k, ids in self.ids.items():
            with self.subTest(k):
                self.assertEqual(problems(ids, want[k]), [])
                self.assertEqual(ids["grip"]["mat"], "rubber")
                self.assertEqual(ids["grip"]["bevel"], self.consts[k]["R_SOFT"] if k == "e07" else ids["grip"]["bevel"])
        self.assertIn("grip", problems(self.ids["e07"], want["e12"]))   # Gegenprobe: der Bogen hat Griffstück statt BGM-1
        self.assertIn("sight_pin_rail", self.ids["e07"], "B1 „Pins“ wie BASIC-07")
        self.assertEqual(self.data["e12"]["ANCHORS"]["Socket_Eye"]["part"], self.basic["e12"]["ANCHORS"]["Socket_Eye"]["part"], "H3 wie BASIC-12")

    # ---------------------------------------------------------------- Budgets, Visier, Sichtkegel
    def test_budgets(self):
        for k, d in self.data.items():
            with self.subTest(k):
                P = d["PARTS"]
                self.assertEqual(len(lights(P)), 1, f"genau ein Blickfang außerhalb des Visiers: {lights(P)}")
                self.assertLessEqual(len(accent_functions(P)), 3, accent_functions(P))
                self.assertEqual(len([p for p in P if p["shape"] == "text"]), 1)
                self.assertEqual(len(graphics(P)), 1, graphics(P))
        light = self.ids["e07"]["draw_light"]
        self.assertGreater(extended.bounds(light)[0][2], self.consts["e07"]["WIN"]["x_in"], "Spannlicht links am Fensterbogen")
        two = self.data["e12"]["PARTS"] + [dict(self.ids["e12"]["focus_lens"], mat="energy")]   # Gegenprobe: leuchtende Linse wie BASIC-12
        self.assertEqual(len(lights(two)), 2)
        more = self.data["e12"]["PARTS"] + [dict(self.ids["e12"]["cell_release"], id=f"k{i}") for i in range(3)]
        self.assertGreater(len(accent_functions(more)), 3)   # Gegenprobe: vier Bedienfunktionen

    def test_sight_line(self):
        """B1 69,5 mm über dem Pfeil wie BASIC-07 (Visier direkt über dem Pfeil, seit 0.35); H3 66 ± 4 mm über der Strahlachse."""
        def offset(d, k):
            eye = d["ANCHORS"]["Socket_Eye"]["at"]
            axis = self.consts[k]["BORE"]
            return eye[1] - axis, (eye[2] if len(eye) > 2 else 0.0)
        b = offset(self.basic["e07"], "e07")
        self.assertEqual(offset(self.data["e07"], "e07"), b, "Visierlinie wie BASIC-07")
        du, dx = offset(self.data["e12"], "e12")
        self.assertTrue(SIGHT_H[0] <= du <= SIGHT_H[1] and dx == 0, (du, dx))
        raised = copy.deepcopy(self.data["e12"])   # Gegenprobe: Visier 20 mm höher
        raised["ANCHORS"]["Socket_Eye"]["at"] = tuple(v + (20 if i == 1 else 0) for i, v in enumerate(raised["ANCHORS"]["Socket_Eye"]["at"]))
        self.assertGreater(offset(raised, "e12")[0], SIGHT_H[1])

    def test_bow_sight_cone(self):
        """Vom Auge (Ankerpunkt bei vollem Auszug) durch den Pinring bleibt der Sichtkegel frei: das Fenster im Bügel ist links tiefer
        als der Kegel breit, und kein anderes Teil außer dem Visier ragt hinein (Stilhandbuch: Pinvisier über dem Pfeil, BASIC-07)."""
        c, d = self.consts["e07"], self.data["e07"]
        eye = d["ANCHORS"]["Socket_Eye"]["at"]
        ring = self.ids["e07"]["sight_frame"]
        rf, rr = extended.bounds(ring)[0][0], c["PINS_SIZES"]["M"] + 1.8

        def half(f):
            return rr * (f - eye[0]) / (rf - eye[0])

        def problems(parts, win):
            out = []
            riser_front = max(c["edge_f"](c["FRONT"], u) for u in (c["SIGHT_U"] - rr, c["SIGHT_U"] + rr))
            if win["x_in"] < half(riser_front) or win["u0"] > c["SIGHT_U"] - half(riser_front) or win["u1"] < c["SIGHT_U"] + half(riser_front):
                out.append("Fenster zu klein")
            for p in parts:
                if p["asm"] in ("sight", "string", "arrow") or p["id"] in ("riser", "grip"):
                    continue   # Sehne und Pfeil liegen im Zielen am Ankerpunkt vor dem Auge (Auszug), wie bei BASIC-07
                for q in p["items"] if p["shape"] == "multi" else [p]:
                    b = extended.bounds(dict(q, shape=q.get("shape", "box")))
                    if not b:
                        continue
                    (f0, u0, x0), (f1, u1, x1) = b
                    if f1 < eye[0] or f0 > rf:
                        continue
                    h = half(min(f1, rf))
                    du = max(u0 - c["SIGHT_U"], 0, c["SIGHT_U"] - u1)   # nächster Punkt des Hüllquaders zur Visierlinie
                    dx = max(x0, 0, -x1)
                    if math.hypot(du, dx) < h:
                        out.append(p["id"])
            return sorted(set(out))
        self.assertEqual(problems(d["PARTS"], c["WIN"]), [])
        self.assertIn("Fenster zu klein", problems(d["PARTS"], dict(c["WIN"], x_in=16.0)))   # Gegenprobe: Fenster wie BASIC-07 bis 0.34
        post = dict(id="pfosten", asm="riser", shape="box", f0=20, f1=30, u0=90, u1=130, w=8, x=0)
        self.assertEqual(problems(d["PARTS"] + [post], c["WIN"]), ["pfosten"])               # Gegenprobe: Pfosten im Kegel

    def test_trace_view_clear(self):
        """Vor dem Visier steht nichts außer dem Visier höher als 24 mm unter der Visierlinie (wie die Haube von BASIC-12)."""
        c, d = self.consts["e12"], self.data["e12"]
        eye_u = d["ANCHORS"]["Socket_Eye"]["at"][1]

        def problems(parts):
            return [p["id"] for p in parts if (b := extended.bounds(p)) and p["asm"] != "sight"
                    and p["id"] not in ("rail", "shell", "lower") and b[1][0] > -12 and b[1][1] > eye_u - 24 + 0.5]
        self.assertEqual(problems(d["PARTS"]), [])
        hump = dict(id="buckel", asm="receiver", shape="box", f0=150, f1=200, u0=100, u1=140, w=30)
        self.assertEqual(problems(d["PARTS"] + [hump]), ["buckel"])   # Gegenprobe: Buckel vor dem Visier
        self.assertLessEqual(max(u for _, u in c["TOP_LINE"]), c["HOOD_MAX"] + 0.5)

    # ---------------------------------------------------------------- Silhouette
    def test_own_silhouette(self):
        """Seiten-IoU < 0,85 gegen BASIC-NN und jedes andere EXTENDED-Modell, < 0,70 im Paar – im Standardmaß und im genauen Maß."""
        for k, d in self.data.items():
            for measure in (iou, iou_exact):
                with self.subTest(k=k, measure=measure.__name__):
                    self.assertLess(measure(self.basic[k]["PARTS"], d["PARTS"]), IOU_MAX)
                    for o, parts in self.others.items():
                        self.assertLess(measure(parts, d["PARTS"]), IOU_MAX, o)
        for measure in (iou, iou_exact):
            self.assertLess(measure(self.data["e07"]["PARTS"], self.data["e12"]["PARTS"]), PAIR_MAX)
        b12 = self.basic["e12"]["PARTS"]   # Gegenproben: gleiche Form 1,0; eine Parameterlinie bleibt über der Schwelle
        self.assertGreaterEqual(iou(b12, b12), 0.99)
        self.assertGreater(iou(b12, [p for p in b12 if p["id"] not in ("focus_crown", "focus_lens")]), IOU_MAX)
        # Gegenprobe: das genaue Maß sieht das Auge im Querprofil, das Standardmaß zeichnet die Oberschale als volles Rechteck
        P = self.data["e12"]["PARTS"]
        self.assertGreater(extended.side_mask(P, **frame(P)).sum(), extended.side_mask([as_side(p) for p in P], **frame(P)).sum())

    # ---------------------------------------------------------------- Leitmotiv Klammer (E07)
    def test_caliper_bracket(self):
        """Klammer: Die Wurfarme laufen fast parallel nach hinten (≤ 15° gegen die Waagerechte, BASIC-07 schwingt steil), die Ecken
        (Taschen) stehen ≥ 40 mm vor der Griffstelle (Deflex), die Spanne ist kürzer als bei BASIC-07 und die Rollen liegen hinter den Ecken."""
        c, ids = self.consts["e07"], self.ids["e07"]

        def problems(center, front, axle):
            out = []
            (f0, u0), (f1, u1) = center[0], center[-2]
            if abs(math.degrees(math.atan2(u1 - u0, f0 - f1))) > 15:
                out.append("Wurfarme steil")
            if front[0][0] - min(f for f, u in front if abs(u) < 60) < 40:
                out.append("kein Deflex")
            if axle[0] > center[0][0] - 150:
                out.append("Rollen nicht hinter den Ecken")
            return out
        self.assertEqual(problems(c["_c"], c["FRONT"], c["AXLE"]), [])
        sickle = [(16, 218), (14, 290), (0, 360), (-30, 418), (-80, 460), (-150, 478), (-162, 479)]   # Gegenprobe: BASIC-07 Sichel
        self.assertIn("Wurfarme steil", problems(sickle, c["FRONT"], c["AXLE"]))
        straight = [(46, u) for _, u in c["FRONT"]]
        self.assertIn("kein Deflex", problems(c["_c"], straight, c["AXLE"]))   # Gegenprobe: gerader Bügel
        span = height([p for p in self.data["e07"]["PARTS"] if p["asm"] != "arrow"])
        self.assertLess(span, 0.85 * height([p for p in self.basic["e07"]["PARTS"] if p["asm"] != "arrow"]))
        self.assertEqual(ids["limb_top"]["mat"], "graphite")
        self.assertEqual(ids["riser"]["mat"], "shell")

    def test_caliper_riser_section(self):
        """Keilrippe: die Vorderkante des Bügels ist beidseitig eingezogen (schmale Rippe vorn), die Flanken tragen ein Flankenfeld, der
        Bügel hat zwei Rippenschlitze; die Wurfarme verjüngen sich in der Draufsicht (Front und Rückansicht keine Rechtecke)."""
        ids = self.ids["e07"]

        def problems(p, limb):
            out = []
            cuts = p.get("cuts") or ()
            rib = [q for q in cuts if q.get("shape") == "prof" and 8 <= abs(q.get("x", 0)) <= 25 and q.get("w", 99) <= 10]
            if len({math.copysign(1, q["x"]) for q in rib}) < 2:
                out.append("keine Keilrippe")
            if sum(1 for q in cuts if q.get("shape") == "prof" and q.get("w", 0) >= 60) < 2:
                out.append("keine Rippenschlitze")
            if not any(q.get("shape") == "plan" for q in limb.get("cuts") or ()):
                out.append("Wurfarm ohne Verjüngung")
            return out
        self.assertEqual(problems(ids["riser"], ids["limb_top"]), [])
        plain = dict(ids["riser"], cuts=[q for q in ids["riser"]["cuts"] if q.get("w", 0) > 20])
        self.assertEqual(problems(plain, ids["limb_top"]), ["keine Keilrippe"])   # Gegenprobe: glatter Kasten
        self.assertIn("Wurfarm ohne Verjüngung", problems(ids["riser"], dict(ids["limb_top"], cuts=[])))

    def test_caliper_string_readable(self):
        """Die Sehne ist die begründete Ausnahme der Stiftprüfung: Ø ≥ 4 mm, Mittelwicklung Ø ≥ 6,5 mm am Nockpunkt (je Hälfte auf ihrer
        Seite des Nockpunkts) und Endwicklungen an den Rollen machen sie auf Spielabstand lesbar; sie läuft hinten tangential von der Rolle
        ab und folgt dem Nockpunkt."""
        c, ids = self.consts["e07"], self.ids["e07"]

        def problems(s, serving, side):
            out = []
            if 2 * s["r"] < 4.0:
                out.append("Sehne zu dünn")
            at = c["ARROW_U"] + side * 2.5     # 2,5 mm über bzw. unter dem Nockpunkt (Lage der Nocke, Richter R1)
            if 2 * serving["r"] < 6.5 or not serving["a0"] <= at <= serving["a1"]:
                out.append("keine Mittelwicklung am Nockpunkt")
            if abs(s["c"][0] - (c["AXLE"][0] - c["CAM_R"])) > 0.5:
                out.append("nicht tangential")
            return out
        for s, side in (("top", 1), ("bottom", -1)):
            with self.subTest(s):
                self.assertEqual(problems(ids[f"string_{s}"], ids[f"serving_{s}"], side), [])
                self.assertEqual(ids[f"serving_{s}"]["parent_part"], f"string_{s}")
                self.assertEqual(ids[f"end_serving_{s}"]["parent_part"], f"string_{s}")
        self.assertEqual(problems(dict(ids["string_top"], r=1.6), ids["serving_top"], 1), ["Sehne zu dünn"])   # Gegenprobe: BASIC-07 Ø 3,2
        self.assertIn("keine Mittelwicklung am Nockpunkt", problems(ids["string_top"], dict(ids["serving_top"], a0=200, a1=230), 1))
        shifted = dict(ids["serving_bottom"], a0=-200, a1=-170)   # Gegenprobe (Richter R1): untere Wicklung verschoben
        self.assertIn("keine Mittelwicklung am Nockpunkt", problems(ids["string_bottom"], shifted, -1))

    def test_no_thin_sticks(self):
        """Keine Stifte unter Ø 12 mm (Nutzer 0.25); Ausnahme nur Sehne, Pfeil und Visierbaustein. Gegenprobe: Einbeinstift wie E09 r1–4."""
        for k, d in self.data.items():
            with self.subTest(k):
                self.assertEqual(sticks(d["PARTS"]), [])
        pin = dict(id="stopper", asm="riser", shape="cyl", mat="graphite", axis="f", c=(-60, 0), a0=-140, a1=0, r=4.0)
        self.assertEqual(sticks(self.data["e07"]["PARTS"] + [pin]), ["stopper"])          # Gegenprobe: Sehnenstopperstab Ø 8
        self.assertEqual(sticks(self.data["e07"]["PARTS"], exempt=("sight", "arrow")),
                         ["end_serving_bottom", "end_serving_top", "serving_bottom", "serving_top", "string_bottom", "string_top"])

    def test_caliper_sight_sled(self):
        """Visierbefestigung (Hinweis 0.25): Die Schelle umgreift die Vorderkante des Fensterbogens (Innenschnitt ≥ Bogenbreite), zwei
        blanke Klemmschrauben, der Querarm (≥ 400 mm² Querschnitt) trägt die Schiene über ihre ganze Länge; alles hängt mit dem Bügel zusammen."""
        c, ids, P = self.consts["e07"], self.ids["e07"], self.data["e07"]["PARTS"]
        win = c["WIN"]

        def problems(sled, arm):
            out = []
            inner = sled["cuts"][0]["pts"]
            xs = [x for _, x in inner]
            if min(xs) > win["x_in"] or max(xs) < win["x_out"] or max(f for f, _ in inner) < c["_cf"]:
                out.append("umgreift den Bogen nicht")
            us = [u for _, u in arm["pts"]]
            if (max(us) - min(us)) * arm["w"] < 400:
                out.append("Arm zu dünn")
            fs = [f for f, _ in arm["pts"]]
            if min(fs) > ids["rail"]["f0"] or max(fs) < ids["rail"]["f1"] or max(us) < ids["rail"]["u0"]:
                out.append("Schiene nicht getragen")
            if arm["x"] + arm["w"] / 2 < win["x_in"] - 0.5:
                out.append("Arm nicht an der Schelle")
            return out
        self.assertEqual(problems(ids["sight_sled"], ids["sight_arm"]), [])
        self.assertEqual(len(ids["clamp_screws"]["items"]), 2)
        self.assertEqual(ids["clamp_screws"]["mat"], "trim")
        group = next(g for g in extended.components(P) if "sight_sled" in g)
        self.assertTrue({"riser", "sight_arm", "rail", "sight_mount"} <= set(group))
        thin = dict(ids["sight_arm"], pts=[(40, 66), (104, 66), (104, 70), (40, 70)], w=22)
        self.assertIn("Arm zu dünn", problems(ids["sight_sled"], thin))                         # Gegenprobe: Blechwinkel
        short = dict(ids["sight_arm"], pts=[(40, 56), (60, 56), (60, 70), (40, 70)])
        self.assertIn("Schiene nicht getragen", problems(ids["sight_sled"], short))             # Gegenprobe: Stand r1 (Arm 22 mm)
        loose = dict(ids["sight_sled"], cuts=[dict(ids["sight_sled"]["cuts"][0], pts=[(f, x + 20) for f, x in ids["sight_sled"]["cuts"][0]["pts"]])])
        self.assertIn("umgreift den Bogen nicht", problems(loose, ids["sight_arm"]))           # Gegenprobe: stumpf angesetzt

    # ---------------------------------------------------------------- Leitmotiv Weberschiffchen (E12)
    def test_shuttle_spindle(self):
        """Spindel: Der Körper ist in der Mitte am höchsten und breitesten und läuft zu beiden Enden zusammen (Seite und Draufsicht); vorn
        tritt das freie runde Fokusrohr mit dem Kegel aus (Leitmerkmal BASIC-12)."""
        c, ids = self.consts["e12"], self.ids["e12"]

        def problems(top, bottom, plan):
            out = []
            h = lambda f: c["line_u"](top, f) - c["line_u"](bottom, f)   # noqa: E731
            hmax = max(h(f) for f in range(c["F0"], c["F1"], 4))
            if h(c["F1"] - 4) > 0.4 * hmax or h(c["F0"] + 4) > 0.75 * hmax:
                out.append("keine Spindel")
            w = dict(plan)
            if max(w.values()) - c["line_u"](plan, c["F1"]) < 8 or max(w.values()) - c["line_u"](plan, c["F0"]) < 4:
                out.append("Draufsicht gerade")
            return out
        self.assertEqual(problems(c["TOP_LINE"], c["BOTTOM_LINE"], c["PLAN_HW"]), [])
        block_top = [(f, 130) for f, _ in c["TOP_LINE"]]
        block_bot = [(f, 20) for f, _ in c["BOTTOM_LINE"]]
        self.assertIn("keine Spindel", problems(block_top, block_bot, c["PLAN_HW"]))            # Gegenprobe: Kasten
        self.assertIn("Draufsicht gerade", problems(c["TOP_LINE"], c["BOTTOM_LINE"], [(f, 30) for f, _ in c["PLAN_HW"]]))
        tube, cone = ids["focus_tube"], ids["focus_cone"]
        self.assertEqual((tube["axis"], tube["c"][0]), ("f", c["BORE"]))
        self.assertGreater(tube["a1"] - c["F1"], 100, "Fokusrohr frei vor der Spindel")
        self.assertGreater(cone["r"], cone["r1"], "Kegel verjüngt sich zur Linse (kein Trichter)")

    def test_shuttle_eye_and_spool(self):
        """Auge: quer offen durch beide Schalen; die Spule sitzt auf der Strahlachse im Auge mit Luft rundum (≥ 3 mm zur Laibung), ihre
        Achse ist in der Laibung gelagert, die Wicklung (Blickfang) liegt im Auge."""
        c, ids = self.consts["e12"], self.ids["e12"]

        def problems(flanges, axle, glow):
            out = []
            for q in flanges["items"]:
                for f in (q["a0"], q["a1"]):
                    if q["r"] > c["eye_h"](f, -6.0) + 1e-6:   # Laibung 3 mm stark, dazu 3 mm Luft (Richter R2)
                        out.append("Spule streift das Auge")
                        break
            if axle["a0"] > c["EYE"][0] or axle["a1"] < c["EYE"][1]:
                out.append("Achse nicht gelagert")
            if glow["a0"] < c["EYE"][0] or glow["a1"] > c["EYE"][1] or glow["r"] >= c["eye_h"]((glow["a0"] + glow["a1"]) / 2):
                out.append("Wicklung nicht im Auge")
            return out
        self.assertEqual(problems(ids["spool_flanges"], ids["spool_axle"], ids["spool_glow"]), [])
        big = dict(ids["spool_flanges"], items=[dict(q, r=28) for q in ids["spool_flanges"]["items"]])
        self.assertIn("Spule streift das Auge", problems(big, ids["spool_axle"], ids["spool_glow"]))      # Gegenprobe
        short = dict(ids["spool_axle"], a0=c["SPOOL"][0], a1=c["SPOOL"][1])
        self.assertIn("Achse nicht gelagert", problems(ids["spool_flanges"], short, ids["spool_glow"]))   # Gegenprobe: schwebende Spule
        eye = [q for q in ids["shell"]["cuts"] if q.get("shape") == "prof" and q["pts"] == c["eye_pts"]()]
        self.assertEqual(len(eye), 1)
        self.assertGreaterEqual(eye[0]["w"], 2 * c["OVAL"][0], "Auge quer durch den ganzen Körper")
        self.assertEqual(lights(self.data["e12"]["PARTS"]), ["spool_glow"])

    def test_shuttle_cell_in_belly(self):
        """Die Zelle ist der Bauch: ihr Boden folgt der Unterlinie (± 1 mm), sie sitzt vor dem Abzugsbügel und geht nach unten heraus."""
        c, ids = self.consts["e12"], self.ids["e12"]
        guard = extended.bounds(ids["trigger_guard"])

        def problems(cell):
            out = []
            bottom = [(f, u) for f, u in cell["pts"] if u < c["SEAM"]]
            if any(abs(u - c["line_u"](c["BOTTOM_LINE"], f)) > 1.0 for f, u in bottom):
                out.append("Zelle nicht bündig")
            if min(f for f, _ in cell["pts"]) < guard[1][0] + 2:
                out.append("Zelle im Abzugsbügel")
            return out
        self.assertEqual(problems(ids["energy_cell"]), [])
        self.assertEqual(ids["energy_cell"]["move"]["vector_mm"], (0, -110, 0))
        box = dict(ids["energy_cell"], pts=[(c["CELL"][0], 52), (c["CELL"][1], 52), (c["CELL"][1], -30), (c["CELL"][0], -30)])
        self.assertIn("Zelle nicht bündig", problems(box))                                       # Gegenprobe: Magazin wie BASIC-12
        early = dict(ids["energy_cell"], pts=[(f - 30, u) for f, u in ids["energy_cell"]["pts"]])
        self.assertIn("Zelle im Abzugsbügel", problems(early))

    def test_shuttle_rail_saddle(self):
        """Visierbefestigung: Die Schiene liegt über ihre ganze Länge auf dem ebenen Schienensattel der Oberschale (keine Stelzen)."""
        c, ids = self.consts["e12"], self.ids["e12"]

        def problems(r):
            gaps = [r["u0"] - c["line_u"](c["TOP_LINE"], f) for f in range(int(r["f0"]), int(r["f1"]) + 1, 4)]
            return ["Schiene schwebt"] if max(gaps) > 0.5 or min(gaps) < -1.5 else []
        self.assertEqual(problems(ids["rail"]), [])
        self.assertEqual(problems(dict(ids["rail"], u0=ids["rail"]["u0"] + 6)), ["Schiene schwebt"])   # Gegenprobe

    # ---------------------------------------------------------------- Querschnitte, Dichte, Profile
    def test_shaped_sections(self):
        """Hauptkörper mit gestalteten Querschnitten (Breite ändert sich über die Höhe um ≥ 1,5 mm) – Front, Rückansicht und Schaft sind
        keine Rechtecke (Nutzer 0.23). E12: Oval in Ober-, Unterschale und Schaftkappe."""
        def boxy(p):
            us = [u for _, u in p["pts"]]
            lo, hi = min(us), max(us)
            widths = [width_at(p["pts"], lo + (hi - lo) * t) for t in (0.08, 0.5, 0.92)]
            return max(widths) - min(widths) < 1.5
        ids = self.ids["e12"]
        self.assertEqual([pid for pid in ("shell", "lower", "butt_pad") if boxy(ids[pid])], [])
        self.assertTrue(boxy(dict(ids["lower"], pts=[(30, 50), (30, 0), (-30, 0), (-30, 50)])))   # Gegenprobe: Rechteck-Querschnitt
        self.assertTrue(all(q.get("shape") == "plan" for q in ids["shell"]["cuts"] if q.get("u0") == -60))

    def test_detail_density(self):
        """Detaildichte mindestens wie BASIC: Einzelformen ≥ 90 % des Piloten, blanke Teile mindestens so viele wie der Pilot."""
        for k, d in self.data.items():
            with self.subTest(k):
                b = self.basic[k]["PARTS"]
                self.assertGreaterEqual(forms(d["PARTS"]), 0.9 * forms(b))
                self.assertGreaterEqual(forms(d["PARTS"], "trim"), forms(b, "trim"))
        bare = [p for p in self.data["e12"]["PARTS"] if p["mat"] != "trim"]   # Gegenprobe: ohne blanke Teile unter BASIC-12
        self.assertLess(forms(bare, "trim"), forms(self.basic["e12"]["PARTS"], "trim"))

    def test_profiles_simple(self):
        """Kein Seiten- oder Querprofil schneidet sich selbst (auch Schnittprofile)."""
        def problems(parts):
            out = []
            for p in parts:
                for q in (p["items"] if p.get("shape") == "multi" else [p]) + list(p.get("cuts") or ()):
                    if q.get("shape") in ("prof", "xprof", "plan") and crossing([tuple(v) for v in q["pts"]]):
                        out.append(p["id"])
            return sorted(set(out))
        for k, d in self.data.items():
            with self.subTest(k):
                self.assertEqual(problems([p for p in d["PARTS"] if p["asm"] != "sight"]), [])
        bad = dict(self.ids["e07"]["riser"], pts=self.ids["e07"]["riser"]["pts"][:3] + self.ids["e07"]["riser"]["pts"][3:][::-1], cuts=[])
        self.assertEqual(problems([bad]), ["riser"])   # Gegenprobe: zweite Hälfte umgekehrt

    def test_plan_winding(self):
        """Runde 2: BALLONs `mesh_plan` richtet Normalen nicht aus – ein Draufsicht-Profil gegen den Uhrzeigersinn ergibt einen umgestülpten
        Körper und als Schneidkörper keinen Schnitt (die Spindel blieb in r1/r2 von oben gerade). Alle Draufsicht-Profile im Uhrzeigersinn."""
        def problems(parts):
            out = []
            for p in parts:
                for q in (p["items"] if p.get("shape") == "multi" else [p]) + list(p.get("cuts") or ()):
                    if q.get("shape") == "plan":
                        pts = q["pts"]
                        if sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1])) > 0:
                            out.append(p["id"])
            return sorted(set(out))
        for k, d in self.data.items():
            with self.subTest(k):
                self.assertEqual(problems([p for p in d["PARTS"] if p["asm"] != "sight"]), [])
        shell = self.ids["e12"]["shell"]
        ccw = dict(shell, cuts=[dict(q, pts=q["pts"][::-1]) if q.get("shape") == "plan" else q for q in shell["cuts"]])
        self.assertEqual(problems([ccw]), ["shell"])   # Gegenprobe: Stand r1/r2

    # ---------------------------------------------------------------- Absetzung, Zusammenhang, Größe, Quellhash
    def test_bow_versus_trace(self):
        """Bogen hoch und tief (Spanne > 1,5 × Pfeilrichtung ohne Pfeil), Spurgewehr lang und flach (Länge > 2,5 × Höhe)."""
        bow = [p for p in self.data["e07"]["PARTS"] if p["asm"] != "arrow"]
        self.assertGreater(height(bow), 1.5 * length(bow))
        tr = self.data["e12"]["PARTS"]
        self.assertGreater(length(tr), 2.5 * height(tr))
        self.assertIn("string_top", self.ids["e07"])
        self.assertIn("energy_cell", self.ids["e12"])

    def test_no_floating_parts(self):
        for k, d in self.data.items():
            with self.subTest(k):
                self.assertEqual(extended.components(d["PARTS"])[1:], [])
        moved = copy.deepcopy(self.data["e12"]["PARTS"])   # Gegenprobe: Spule samt Achse 900 mm nach vorn → eigene Gruppe
        for p in moved:
            if p["id"].startswith("spool"):
                for q in [p] + p.get("items", []):
                    for key in ("a0", "a1"):
                        if key in q:
                            q[key] += 900
        self.assertGreater(len(extended.components(moved)), 1)

    def test_proportions(self):
        bow = self.data["e07"]
        self.assertAlmostEqual(height(bow["PARTS"]) / 1000, bow["META"]["reference_length_m"], delta=0.005)
        self.assertEqual(bow["META"]["reference_axis"], "height_m")
        tr = self.data["e12"]
        self.assertAlmostEqual(length(tr["PARTS"]) / 1000, tr["META"]["reference_length_m"], delta=0.005)
        longer = tr["PARTS"] + [dict(self.ids["e12"]["focus_crown"], id="probe", a0=600, a1=610)]   # Gegenprobe
        self.assertGreater(abs(length(longer) / 1000 - tr["META"]["reference_length_m"]), 0.005)

    def test_source_hash(self):
        for k, o in OWN.items():
            with self.subTest(k):
                a = extended.source(k, SNAP)
                self.assertEqual(a, extended.source(k, SNAP))
                self.assertIn(f"formgen/models/extended/{o['mod']}.py", a["files"])
                self.assertFalse([f for f in a["files"] if f.startswith(f"basic/pilot/w{o['num']}_")
                                  or f.startswith(f"basic/weapons/w{o['num']}_")], "kein Umbau von BASIC-NN")

    def test_snapshot_released(self):
        self.assertFalse(any(n == "basic" or n.startswith("basic.") for n in sys.modules))
        self.assertNotIn(str(SNAP), sys.path)


if __name__ == "__main__":
    unittest.main()
