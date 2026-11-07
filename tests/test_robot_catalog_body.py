"""0.14 Kitbash: Kataloge der sechs Körper-Einzelteile (Oberkörper, Becken, Schulter, Oberschenkel, Unterschenkel, Füße) in beiden Typen.

Kataloge: formgen/models/robot/catalog/{torso,pelvis,shoulders,legs}.py. Geprüft: Grundform bytegleich, jede Variante baut, keine
Phantomteile, Spiegelsymmetrie (RA01), Anker, Vielfalt je Einzelteil (formgen.robot.variety.measure_parts) samt Gegenproben.
Varianten mit `ra02 = 'replace'` baut RA02 im Ersatzmodus (roboterbasic_02_replace), sie werden hier in beiden Typen geprüft.
Laufzeit einige Minuten: jede Variante wird je Typ einmal voll ausgewertet (Booleans, Fasen) und einmal für das Vielfaltsmaß gemessen.
"""
import copy
import json
import re
import unittest
from unittest import mock

import numpy as np
from scipy.spatial import cKDTree

from formgen import geom, model
from formgen.models.robot import catalog
from formgen.models.robot import roboterbasic_01 as basic1
from formgen.models.robot import roboterbasic_02 as basic2
from formgen.models.robot.catalog import legs, pelvis, shoulders, torso
from formgen.robot import bevel, lines, variety

BODY = ('upper_body', 'pelvis', 'shoulders', 'thighs', 'shins', 'feet')
OWNERS = {torso: ('upper_body',), pelvis: ('pelvis',), shoulders: ('shoulders',), legs: ('thighs', 'shins', 'feet')}
MINE = [v for module in OWNERS for v in module.VARIANTS]
MODULES = {1: basic1, 2: basic2}
ENVELOPE_M = 0.050          # Annahme: Figurhülle der Grundform ± 50 mm (die Fußvarianten reichen bis 39 mm über die Zehe hinaus)
SIDE_EFFECT_02 = 0.98       # Annahme: in RA02 trägt das Verschiebungsfeld Nachbarteile mit, höchstens 2 % Fläche (gemessen 0,9905)
# Gelenk- und Längenmaße hängen am Skelett des Typs; eine Variante setzt sie nie (bei RA02 träfen sie gemessene Nachbarteile)
JOINT_KEYS = dict(torso=('SX', 'SZ', 'joint_r'), pelvis=('hip_x', 'hip_z', 'hip_r', 'hip_len'),
                  legs=('LT', 'LS', 'foot_h', 'knee_r', 'knee_len', 'ankle_r', 'ankle_len'))
ANCHORS_01 = ('waist_core', 'thigh_R_hip_ball', 'thigh_L_hip_ball', 'thigh_R_thigh_core', 'thigh_L_thigh_core', 'foot_R_foot_core',
              'foot_L_foot_core')
ORIGIN = dict(kind='Annahme', source='Gegenprobe im Test')


def params_of(module, v):
    params = copy.deepcopy(module.PARAMS)
    params['variants'][v.assembly] = v.letter
    return params


def document(num, v, kit=None):
    module = MODULES[num]
    with mock.patch.object(catalog, 'load', return_value=kit or catalog.load()):
        return module.document(params_of(module, v), sheet_id=f'RA{num:02d}')


def builds(num):
    """Varianten, die Typ num baut: seit dem Ersatzmodus (0.14) alle, in beiden Typen."""
    return list(MINE)          # seit dem Ersatzmodus (0.14) baut RA02 auch die replace-Varianten


def phantoms(v, base, doc):
    """Neue oder entfallene Teile außerhalb des eigenen Einzelteils."""
    before = {p['id']: p['assembly'] for p in base['parts']}
    after = {p['id']: p['assembly'] for p in doc['parts']}
    return sorted([f'+{i} ({a})' for i, a in after.items() if i not in before and a != v.assembly]
                  + [f'-{i} ({a})' for i, a in before.items() if i not in after and a != v.assembly])


def mirror_gaps(parts, cuts):
    """Spiegelpaare (rechts/links) und Mittelteile an x gespiegelt, wie test_robot_basic; liefert Verstöße (Teil, Abstand mm)."""
    pairs = [(i, re.sub(r'(^|_)L_', r'\1R_', i, count=1)) for i in parts if re.search(r'(^|_)L_', i)]
    pairs += [(i, re.sub(r'(^|_)l(_|$)', r'\1r\2', i, count=1)) for i in parts if re.search(r'(^|_)l(_|$)', i)]
    paired = {i for pair in pairs for i in pair}
    center = sorted(set(parts) - paired - {'chest_stripe_a', 'chest_stripe_b'})      # Bruststreifen: nur eine Seite, schon in BALLON
    swap = lambda i: re.sub(r'_([ab])(?=$|_)', lambda m: '_' + 'ba'['ab'.index(m[1])], i)
    bad = []
    for left, right in pairs + [(i, i) for i in center]:
        names = [n for n in {right, swap(right)} if n in parts]
        if not names:
            bad.append((left, 'ohne Gegenstück'))
            continue
        mirrored = parts[left] * (-1, 1, 1)
        gap = min(max(cKDTree(parts[n]).query(mirrored)[0].max(), cKDTree(mirrored).query(parts[n])[0].max()) for n in names)
        if gap > (.005 if left in cuts else .001):
            bad.append((left, round(gap * 1000, 2)))
    return bad


class CatalogRuleTest(unittest.TestCase):
    def test_six_parts_with_variants_that_work_in_both_types(self):
        kit = catalog.load()
        for module, owned in OWNERS.items():
            self.assertTrue(module.VARIANTS, module.__name__)
            self.assertTrue(all(v.assembly in owned for v in module.VARIANTS), module.__name__)
        for a in BODY:
            mine = [v for v in MINE if v.assembly == a]
            self.assertEqual([kit[a][v.letter] for v in mine], mine, a)
            self.assertGreaterEqual(len([v for v in mine if v.ra02 == 'field']), 2, f'{a}: zwei Varianten, die RA02 heute schon baut')
            self.assertGreaterEqual(len(mine), 3, a)

    def test_params_are_strict_and_leave_joints_and_lengths_to_the_type(self):
        for v in MINE:
            self.assertEqual(v.since, '0.14', v.id)
            if v.origin['kind'] == 'Vorgabe':
                self.assertIn('BALLON 14bd78d', v.origin['source'], v.id)
            for num, module in MODULES.items():
                merged = catalog.merge(catalog.merge(module.PARAMS, v.params, what=v.id), v.types.get(num, {}), what=v.id)  # unbekannt → Fehler
                for family, keys in JOINT_KEYS.items():
                    for key in keys:
                        self.assertEqual(merged[family].get(key), module.PARAMS[family].get(key), f'{v.id} {family}.{key}')


class BaseTest(unittest.TestCase):
    def test_all_ten_sheets_are_bytes_identical_without_these_catalogs(self):
        """Die Kataloge ändern keine Linie, die sie nicht wählt: Dokument je Blatt mit und ohne die sechs Kataloge gleich."""
        full = catalog.load()
        rest = catalog.validate([v for m in catalog._modules() for v in m.VARIANTS if v not in MINE])
        sheets = lines.sheets()
        self.assertEqual(len(sheets), 10)
        compared = []
        for sid, entry in sheets.items():
            params = lines.params_of(entry)
            if any(params['variants'][a] != catalog.BASE for a in BODY):
                continue                        # die Linie wählt eine dieser Varianten: gewollte Änderung
            module = lines.module_of(entry)
            docs = []
            for kit in (full, rest):
                with mock.patch.object(catalog, 'load', return_value=kit):
                    docs.append(json.dumps(module.document(copy.deepcopy(params), sheet_id=sid), sort_keys=True, default=str))
            self.assertEqual(docs[0], docs[1], sid)
            compared.append(sid)
        self.assertTrue({'RA01', 'RA02'} <= set(compared), compared)

    def test_basic_params_stay_the_same_object(self):
        for num, module in MODULES.items():
            self.assertIs(catalog.apply(module.PARAMS, num=num, measured=num == 2), module.PARAMS)


class BuildTest(unittest.TestCase):
    """Jede Variante einmal je Typ: Dokument, volle Auswertung mit geom.evaluate (Booleans, Fasen der Waffen) und der Auswertungsweg
    des Roboters (bevel.evaluate: Booleans in geom, Fasen nach den Fugen). Symmetrie und Hülle am Roboterweg: geom fast Zylinder links
    und rechts verschieden (Gelenkachsen bis 4,9 mm schon an der Grundform), bevel.evaluate spiegelt exakt (test_robot_basic)."""

    @classmethod
    def setUpClass(cls):
        cls.base, cls.built, cls.full = {}, {}, {}
        for num, module in MODULES.items():
            doc = module.document(module.PARAMS, sheet_id=f'RA{num:02d}')
            cls.base[num] = (doc, bevel.evaluate(doc))
            for v in builds(num):
                doc = document(num, v)
                full = geom.evaluate(model.normalize(doc))
                cls.full[num, v.id] = (len(full['parts']), all(len(p['mesh']['faces']) for p in full['parts']))
                cls.built[num, v.id] = (v, doc, bevel.evaluate(doc))

    def test_every_variant_builds_and_changes_its_part(self):
        for (num, vid), (v, doc, ev) in self.built.items():
            with self.subTest(sheet=f'RA0{num}', variant=vid):
                self.assertEqual(self.full[num, vid], (len(doc['parts']), True))
                self.assertEqual(len(ev['parts']), len(doc['parts']))
                self.assertTrue(all(len(p['mesh']['faces']) for p in ev['parts']))
                base = {p['id']: p for p in self.base[num][0]['parts'] if p['assembly'] == v.assembly}
                own = {p['id']: p for p in doc['parts'] if p['assembly'] == v.assembly}
                self.assertNotEqual(own, base, 'Variante ohne Wirkung auf ihr Einzelteil')

    def test_no_phantom_parts_and_nothing_outside_the_figure(self):
        for (num, vid), (v, doc, ev) in self.built.items():
            with self.subTest(sheet=f'RA0{num}', variant=vid):
                self.assertEqual(phantoms(v, self.base[num][0], doc), [])
                lo, hi = np.array(self.base[num][1]['bounds_m'])
                points = np.concatenate([np.asarray(p['mesh']['vertices']) for p in ev['parts']])
                self.assertTrue(np.all(points.min(0) >= lo - ENVELOPE_M), (points.min(0) - lo) * 1000)
                self.assertTrue(np.all(points.max(0) <= hi + ENVELOPE_M), (points.max(0) - hi) * 1000)

    def test_ra01_changes_nothing_outside_its_part(self):
        base = {p['id']: p for p in self.base[1][0]['parts']}
        for (num, vid), (v, doc, _) in self.built.items():
            if num == 1:
                other = {p['id']: p for p in doc['parts'] if p['assembly'] != v.assembly}
                self.assertEqual(other, {i: p for i, p in base.items() if p['assembly'] != v.assembly}, vid)

    def test_ra01_variants_mirror(self):
        """Seitenpaare und Mittelteile des eigenen Einzelteils spiegeln an x (die übrigen Teile sind die der Grundform)."""
        for (num, vid), (v, doc, ev) in self.built.items():
            if num != 1:
                continue
            with self.subTest(variant=vid):
                parts = {p['id']: np.array(p['mesh']['vertices']) for p in ev['parts'] if p['assembly'] == v.assembly}
                cuts = {p['id'] for p in doc['parts'] if p.get('cuts')}
                self.assertEqual(mirror_gaps(parts, cuts), [])

    def test_mirror_check_sees_a_one_sided_part(self):
        """Gegenprobe: ein nur rechts verschobenes Teil wird gemeldet, über der Toleranz für Fugenteile (5 mm)."""
        v, doc, ev = self.built[1, 'SH-C']
        parts = {p['id']: np.array(p['mesh']['vertices']) for p in ev['parts'] if p['assembly'] == 'shoulders'}
        cuts = {p['id'] for p in doc['parts'] if p.get('cuts')}
        self.assertEqual(mirror_gaps(parts, cuts), [])
        parts['pauldron_r'] = parts['pauldron_r'] + (0, 0, .008)
        self.assertEqual([b[0] for b in mirror_gaps(parts, cuts)], ['pauldron_l'])

    def test_anchor_parts_remain(self):
        for (num, vid), (v, doc, _) in self.built.items():
            ids = {p['id'] for p in doc['parts']}
            with self.subTest(sheet=f'RA0{num}', variant=vid):
                self.assertTrue({a['part'] for a in doc['anchors'].values()} <= ids)
                if num == 2 and v.ra02 == 'replace':      # Ersatzmodus: gleiche Lage, das Teil darf das Ersatzteil desselben Einzelteils sein
                    base = self.base[num][0]['anchors']
                    self.assertEqual({k: a['at'] for k, a in doc['anchors'].items()}, {k: a['at'] for k, a in base.items()})
                else:
                    self.assertEqual(doc['anchors'], self.base[num][0]['anchors'])
                if num == 1:
                    self.assertTrue(set(ANCHORS_01) <= ids, set(ANCHORS_01) - ids)

    def test_phantom_check_sees_a_part_in_the_wrong_assembly(self):
        """Gegenprobe: Schulterkolben entstehen in body.torso, gehören aber zur Schulter; als Oberkörper-Variante gemeldet."""
        wrong = catalog.Variant('upper_body', 'Z', 'Shoulder Piston', '0.14', 'Gegenprobe', ORIGIN, {'torso': {'shoulder_pistons': True}})
        kit = catalog.validate([wrong])
        found = phantoms(wrong, self.base[1][0], document(1, wrong, kit))
        self.assertEqual(len(found), 6, found)
        self.assertTrue(all(f.startswith('+shoulder_piston_') and f.endswith('(shoulders)') for f in found), found)


class VarietyTest(unittest.TestCase):
    """Vielfalt je Einzelteil mit measure_parts: jede Variante ≤ PART_THRESHOLD in der kleinsten Ansicht ihres Einzelteils."""

    @classmethod
    def setUpClass(cls):
        register = lines.load()
        cls.register = dict(register, lines=[e for e in register['lines'] if e['letter'] == 'A'])   # nur Varianten, keine Linien
        cls.result = {}
        for num in MODULES:
            kit = catalog.validate(builds(num))
            cls.result.update(variety.measure_parts(catalog=kit, types=[num], register=cls.register)['variants'])

    def test_every_variant_differs_in_its_own_part(self):
        self.assertEqual(sorted(self.result), ['RA01', 'RA02'])
        for num in MODULES:
            rows = self.result[f'RA{num:02d}']
            self.assertEqual(sorted(rows), sorted(v.id for v in builds(num)))
            for vid, row in rows.items():
                with self.subTest(sheet=f'RA0{num}', variant=vid):
                    self.assertLessEqual(row['least'], variety.PART_THRESHOLD, row['iou'])

    def test_side_effects(self):
        """RA01: kein anderes Einzelteil ändert sich (IoU 1). RA02: das Feld trägt Nachbarn höchstens wenig mit."""
        for sid, rows in self.result.items():
            for vid, row in rows.items():
                limit = 1.0 if sid == 'RA01' else SIDE_EFFECT_02
                self.assertGreaterEqual(row['side_effect']['least'], limit, f'{sid} {vid} {row["side_effect"]}')

    def test_invisible_variant_is_reported_equal_for_the_right_reason(self):
        """Gegenprobe: ohne Brustlichter fallen Teile weg, die Silhouette des Oberkörpers bleibt; gemeldet als GLEICH, weil die IoU im
        eigenen, nichtleeren Einzelteil die Schwelle erreicht (nicht weil die Maske leer ist)."""
        dark = catalog.Variant('upper_body', 'Z', 'Lights Off', '0.14', 'Gegenprobe', ORIGIN, {'torso': {'lights': False}})
        visible = next(v for v in MINE if v.id == 'UB-B')
        kit = catalog.validate([dark, visible])
        result = variety.measure_parts(catalog=kit, types=[1], register=self.register)
        verdict = {vid: ok for vid, _, _, _, ok in variety.part_verdict(result)}
        self.assertEqual(verdict, {'UB-Z': False, 'UB-B': True})
        row = result['variants']['RA01']['UB-Z']
        self.assertTrue(all(x >= variety.PART_THRESHOLD for x in row['iou'].values()), row)
        removed = {p['id'] for p in basic1.PARTS} - {p['id'] for p in document(1, dark, kit)['parts']}
        self.assertTrue(removed and all(i.startswith('chest_light_') for i in removed), removed)
        self.assertTrue(len(variety.by_assembly(basic1, basic1.PARAMS)['upper_body']))


if __name__ == '__main__':
    unittest.main()
