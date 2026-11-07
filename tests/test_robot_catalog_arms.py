"""0.14 Kitbash: Varianten Oberarm, Unterarm, Hände (catalog/arms.py) in RA01 und RA02; Grundform bytegleich, Vielfalt je Einzelteil."""
import copy
import hashlib
import json
import unittest

import numpy as np
from scipy.spatial import cKDTree

from formgen import geom, model
from formgen.models.robot import arm, catalog
from formgen.models.robot import roboterbasic_01 as basic1
from formgen.models.robot import roboterbasic_02 as basic2
from formgen.models.robot.catalog import arms
from formgen.robot import lines, variety

TYPES = ((1, 'RA01', basic1), (2, 'RA02', basic2))
OWN = ('upper_arms', 'forearms', 'hands')
# Teile der Einzelteile Oberarm, Unterarm, Hände der Grundform (PARAMS), JSON sortiert: gemessen am Stand d0837a9 (Schnittstelle, vor dem
# Heben der Konstanten); die zehn Blattdokumente waren vor und nach dem Heben bytegleich.
BASE_SHA = {1: '347d3efcdcc16e3f36f94da0ad1ae0a8202613d4d6b2b73a1e635708fca1dc56',
            2: '9b53fa13fe1074179d653023865b239cebe2394a1440e7c21def9c7a99e69665'}
ANCHORS_01 = [f'arm_{s}_{p}' for s in 'RL' for p in ('upper_core', 'elbow', 'palm')]
MARGIN = 50.0       # mm: kein Punkt einer Variante außerhalb der Grundfigur ± MARGIN
GEOMETRY = ('points', 'vertices', 'rings', 'items', 'faces', 'cuts', 'shape')


def points(p):
    out = [np.asarray(p[k], float).reshape(-1, 3) for k in ('points', 'vertices') if k in p]
    out += [np.asarray(r, float).reshape(-1, 3) for r in p.get('rings', [])]
    out += [points(c) for c in p.get('items', [])]
    return np.concatenate(out) if out else np.empty((0, 3))


def twin(pid):
    return pid.replace('arm_R_', 'arm_L_', 1) if pid.startswith('arm_R_') else None


def mirror_error(a, b):
    """Größter Abstand (mm) zwischen Punktmenge a und der an x (dritte Achse f/u/x) gespiegelten Menge b, beidseitig."""
    if not len(a) or not len(b):
        return 0.0 if len(a) == len(b) else float('inf')
    b = b * (1, 1, -1)
    return float(max(cKDTree(b).query(a)[0].max(), cKDTree(a).query(b)[0].max()))


def own_triangles(module, params, sid, assembly):
    """Dreiecke (m) nur der Teile eines Einzelteils, wie variety.by_assembly (Teile werden ohne Booleans unabhängig ausgewertet)."""
    doc = module.document(params, sheet_id=sid)
    doc['parts'] = [{k: v for k, v in p.items() if k != 'parent_part'} for p in doc['parts'] if p['assembly'] == assembly]
    ids = {p['id'] for p in doc['parts']}
    doc['anchors'] = {k: a for k, a in doc['anchors'].items() if a['part'] in ids}
    doc['assemblies'] = [a for a in doc['assemblies'] if a['id'] == assembly]
    tris = []
    for p in geom.evaluate(model.normalize(doc), booleans=False, bevels=False)['parts']:
        v = np.asarray(p['mesh']['vertices'], float)
        for face in p['mesh']['faces']:
            tris += [v[[face[0], face[i], face[i + 1]]] for i in range(1, len(face) - 1)]
    return np.array(tris).reshape(-1, 3, 3)


def chosen(module, v):
    params = copy.deepcopy(module.PARAMS)
    params['variants'][v.assembly] = v.letter
    return params


class BaseTest(unittest.TestCase):
    def test_constants_are_the_defaults_and_base_parts_are_unchanged(self):
        self.assertEqual(arm.parts(), arm.parts(arm.FOREARM, arm.HAND))
        self.assertEqual(arm.parts(), arm.parts({}, {}))
        self.assertEqual(vars(arm.dims()), vars(arm.dims({})))
        d = arm.dims(arm.HAND)
        for key in ('FINGER_X', 'FINGER_SCALE', 'FINGER_LINKS', 'KNUCKLE_Z', 'THUMB_BASE', 'THUMB_DIR', 'THUMB_LINKS'):
            self.assertEqual(list(np.ravel(getattr(d, key))), list(np.ravel(getattr(arm, key))), key)
        for num, _, module in TYPES:
            self.assertEqual((module.PARAMS['forearm'], module.PARAMS['hand']), (arm.FOREARM, arm.HAND), module.__name__)
            parts = [p for p in module.parts() if p['assembly'] in OWN]
            self.assertEqual(hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest(), BASE_SHA[num], module.__name__)

    def test_unknown_keys_are_errors(self):
        with self.assertRaisesRegex(ValueError, 'forearm: unbekannter Schlüssel shield'):
            arm.parts({'shield': 1})
        with self.assertRaisesRegex(ValueError, 'hand: unbekannter Schlüssel claw'):
            arm.parts(None, {'claw': 1})

    def test_catalog_rule_two_form_variants_each(self):
        kit = catalog.validate(arms.VARIANTS)
        for a in OWN:
            self.assertGreaterEqual(len(kit[a]) - 1, 2, a)
        for v in arms.VARIANTS:
            self.assertIn(v.assembly, OWN)
            self.assertEqual((v.since, v.ra02), ('0.14', 'field'), v.id)
            for over in (v.params, *v.types.values()):
                self.assertLessEqual(set(over), {'upper_arm', 'forearm', 'hand'}, v.id)


class VariantTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = {num: {p['id']: p for p in module.parts()} for num, _, module in TYPES}
        cls.built = {(num, v.id): {p['id']: p for p in module.parts(chosen(module, v))} for num, _, module in TYPES for v in arms.VARIANTS}

    def test_every_variant_builds_in_both_types_without_phantoms(self):
        for num, _, module in TYPES:
            base = self.base[num]
            box = np.concatenate([points(p) for p in base.values()])
            lo, hi = box.min(0) - MARGIN, box.max(0) + MARGIN
            for v in arms.VARIANTS:
                got = self.built[(num, v.id)]
                with self.subTest(type=num, variant=v.id):
                    new, gone = set(got) - set(base), set(base) - set(got)
                    changed = {i for i in set(got) & set(base)
                               if {k: got[i].get(k) for k in GEOMETRY} != {k: base[i].get(k) for k in GEOMETRY}}
                    self.assertTrue(new | changed, 'ohne Wirkung')
                    self.assertEqual({got[i]['assembly'] for i in new | changed} | {base[i]['assembly'] for i in gone}, {v.assembly})
                    # außerhalb des eigenen Einzelteils höchstens die Elternkette (RA02: entfernte Schale hängt den Unterarm um)
                    others = {i for i in set(got) & set(base) if got[i] != base[i] and got[i]['assembly'] != v.assembly}
                    self.assertEqual({k for i in others for k in got[i] if got[i][k] != base[i].get(k)} - {'parent_part'}, set())
                    pts = np.concatenate([points(got[i]) for i in new | changed])
                    self.assertFalse(((pts < lo) | (pts > hi)).any(), 'Punkt außerhalb der Figur ± 50 mm')
                    anchors = ANCHORS_01 if num == 1 else [a['part'] for a in module.anchors().values()]
                    self.assertLessEqual(set(anchors), set(got))

    def test_mirror_symmetry(self):
        """RA01: jedes neue oder geänderte Teil links = rechts an x gespiegelt. RA02: neue Teile ebenso auf 1 mm; geänderte gemessene Teile
        sind schon in der Grundform bis 4 mm unsymmetrisch und dürfen je Teil höchstens 1 mm schlechter werden. Vor der Spiegelkorrektur in
        roboterbasic_02_parameters._frame_for (0.14) lag der Bizepskolben links 103 mm daneben."""
        for num, _, _ in TYPES:
            base = self.base[num]
            for v in arms.VARIANTS:
                got = self.built[(num, v.id)]
                with self.subTest(type=num, variant=v.id):
                    touched = [i for i in got if twin(i) and (i not in base or got[i] != base[i])]
                    self.assertTrue(all(twin(i) in got for i in touched))
                    for i in touched:
                        limit = 1e-3 if num == 1 else (1.0 if i not in base else mirror_error(points(base[i]), points(base[twin(i)])) + 1.0)
                        self.assertLess(mirror_error(points(got[i]), points(got[twin(i)])), limit, i)

    def test_variety_each_variant_differs_in_its_own_part(self):
        """Wie variety.measure_parts: IoU der Masken des eigenen Einzelteils gegen die Grundform, kleinste Ansicht ≤ PART_THRESHOLD.
        Andere Einzelteile bleiben geometrisch gleich (test_every_variant_…), ihre IoU ist damit 1."""
        for num, sid, module in TYPES:
            base = {a: own_triangles(module, module.PARAMS, sid, a) for a in OWN}
            for v in arms.VARIANTS:
                with self.subTest(type=num, variant=v.id):
                    own = variety._part_iou(base[v.assembly], own_triangles(module, chosen(module, v), sid, v.assembly))
                    self.assertLessEqual(min(own.values()), variety.PART_THRESHOLD, own)

    def test_counter_probe_invisible_variant_is_reported_equal(self):
        """Gegenprobe über measure_parts selbst: Knöchelwelle 10 → 10,5 mm liegt in Handfläche und Knöchelschutz (RA01) bzw. ist in RA02
        nicht gebunden; die Variante muss als GLEICH gelten, und zwar weil ihr eigenes Einzelteil Hände IoU ≈ 1 hat."""
        probe = catalog.Variant('hands', 'Z', 'Hidden Knuckle', '0.14', 'Gegenprobe', dict(kind='Annahme', source='Test'),
                                params={'hand': {'knuckles': 10.5}})
        register = lines.load()
        register = dict(register, lines=[e for e in register['lines'] if e['letter'] == 'A'])
        result = variety.measure_parts(catalog=catalog.validate([probe]), register=register)
        rows = {sid: row for vid, sid, *row in variety.part_verdict(result) if vid == 'HN-Z'}
        self.assertEqual(set(rows), {'RA01', 'RA02'})
        for sid, (assembly, least, differs) in rows.items():
            self.assertEqual(assembly, 'hands', sid)
            self.assertFalse(differs, sid)
            self.assertGreater(least, 0.995, sid)
            self.assertEqual(result['variants'][sid]['HN-Z']['side_effect']['least'], 1.0, sid)
        self.assertEqual(result['variants']['RA02']['HN-Z']['least'], 1.0)


if __name__ == '__main__':
    unittest.main()
