"""Ersatzmodus von RoboterBasic-02 (0.14 Kitbash): gemessene Einzelteile gegen eingepasste Konstruktorteile tauschen.

Eigener Katalog (unittest.mock) mit Varianten `ra02 = 'replace'` je Einzelteil; Prüfungen laut Auftrag: keine Messteile mehr,
Ersatzteile nur im Einzelteil, Hülle ±15 % je Achse, Anker und Gelenke unverändert, Spiegelgleichheit, übrige Einzelteile
unverändert, keine Ausreißer, Auswertung läuft. Gegenprobe: ohne Einpassung (rohe 01-Maße) fällt die Hülle durch.
"""
from copy import deepcopy
import unittest
from unittest import mock

import numpy as np
from scipy.spatial import cKDTree

from formgen import geom, model
from formgen.models.robot import catalog
from formgen.models.robot import roboterbasic_02 as two
from formgen.models.robot import roboterbasic_02_parameters as profiles
from formgen.models.robot import roboterbasic_02_replace as replacement

NINE = replacement.ALLOWED
HULL = 0.15          # Vorgabe Auftrag: Hülle des Einzelteils je Achse ±15 % der gemessenen Ausdehnung
JOINT = 0.01         # mm
MIRROR = 0.5         # mm
OUTLIER = 50.0       # mm um die Figurhülle
ORIGIN = dict(kind='Annahme', source='Test des Ersatzmodus')


def _variants():
    out = [catalog.Variant(a, 'B', 'Kit Test', '0.14', 'Ersatz ohne Parameteränderung', ORIGIN, ra02='replace') for a in NINE]
    out += [catalog.Variant('feet', 'C', 'Kit Chamfer', '0.14', 'Ersatz mit kantigerem Fuß', ORIGIN,
                            params=dict(legs=dict(foot_ch=20)), ra02='replace'),
            catalog.Variant('thighs', 'C', 'Field Test', '0.14', 'Feldvariante daneben', ORIGIN, params=dict(legs=dict(thigh_ch=34))),
            catalog.Variant('head', 'B', 'Kit Head', '0.14', 'Kopf im Ersatzmodus (noch nicht eingepasst)', ORIGIN, ra02='replace')]
    return catalog.validate(out)


KIT = _variants()


def _params(choice, proportion=None):
    params = deepcopy(two.PARAMS)
    params['variants'].update(choice)
    if proportion:
        params['proportion'].update(proportion)
    return params


def _document(params):
    with mock.patch.object(catalog, 'load', return_value=KIT):
        return two.document(params)


def _cloud(parts):
    return np.concatenate([profiles._cloud(p) for p in parts])


def _twin(pid):
    for a, b in (('_R_', '_L_'), ('_r_', '_l_')):
        if a in pid:
            return pid.replace(a, b, 1)
    return pid[:-2] + '_l' if pid.endswith('_r') else None


def _distance(a, b):
    return max(float(cKDTree(b).query(a)[0].max()), float(cKDTree(a).query(b)[0].max()))


def _deviation(measured, kit):
    a, b = _cloud(measured), _cloud(kit)
    low, high = a.min(axis=0), a.max(axis=0)
    return np.maximum(np.abs(b.min(axis=0) - low), np.abs(b.max(axis=0) - high)) / (high - low)


class ReplaceModeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = _document(_params({}))
        cls.docs = {X: _document(_params({X: 'B'})) for X in NINE}

    def parts(self, doc, assembly):
        return [p for p in doc['parts'] if p['assembly'] == assembly]

    def test_grundform_is_unchanged_and_catalog_feeds_replace(self):
        self.assertEqual(self.base, two.document())
        self.assertIs(profiles.templates(two.PARAMS, two.PARAMS, two._TEMPLATES, two._BASE_FRAMES), two._TEMPLATES)
        with mock.patch.object(catalog, 'load', return_value=KIT):
            applied = catalog.apply(_params({'feet': 'B', 'shins': 'B'}), num=2, measured=True)
        self.assertEqual(applied['replace'], ['shins', 'feet'])

    def test_each_part_is_replaced_only_inside_its_assembly(self):
        for X, doc in self.docs.items():
            with self.subTest(assembly=X):
                measured = {p['id'] for p in self.parts(self.base, X)}
                mine = self.parts(doc, X)
                kit = [p for p in doc['parts'] if '_kit_' in p['id']]
                self.assertTrue(mine)
                self.assertFalse(measured & {p['id'] for p in doc['parts']})
                self.assertEqual({p['id'] for p in mine}, {p['id'] for p in kit})
                self.assertEqual(len({p['id'] for p in doc['parts']}), len(doc['parts']))
                for p in kit:
                    self.assertTrue(p['source_object'].startswith('Kit_'))
                    self.assertEqual(p['provenance']['kind'], 'Annahme')
                    self.assertIn('Ersatzmodus, eingepasst in gemessene Maße', p['provenance']['source'])

    def test_hull_of_each_assembly_matches_measured_within_tolerance(self):
        for X, doc in self.docs.items():
            with self.subTest(assembly=X):
                deviation = _deviation(self.parts(self.base, X), self.parts(doc, X))
                self.assertLessEqual(float(deviation.max()), HULL, f'{X}: {np.round(deviation * 100, 1)} %')

    def test_anchors_and_joints_stay_and_point_to_existing_parts(self):
        for X, doc in self.docs.items():
            with self.subTest(assembly=X):
                ids = {p['id'] for p in doc['parts']}
                for name, anchor in doc['anchors'].items():
                    self.assertIn(anchor['part'], ids, name)
                    self.assertLessEqual(float(np.abs(np.subtract(anchor['at'], self.base['anchors'][name]['at'])).max()), JOINT)
                self.assertEqual(len(doc['info']['joints']), len(self.base['info']['joints']))
                for new, old in zip(doc['info']['joints'], self.base['info']['joints']):
                    self.assertIn(new['part'], ids)
                    self.assertLessEqual(float(np.abs(np.subtract(new['pivot'], old['pivot'])).max()), JOINT)
                    if old['part'] in {p['id'] for p in self.parts(self.base, X)}:
                        self.assertIn('_kit_', new['part'])
                    else:
                        self.assertEqual(new['part'], old['part'])

    def test_left_is_mirror_of_right(self):
        mirror = np.array([-1.0, 1.0, 1.0])
        for X, doc in self.docs.items():
            with self.subTest(assembly=X):
                kit = {p['id']: p for p in self.parts(doc, X)}
                right = [pid for pid in kit if _twin(pid) in kit]
                self.assertTrue(right)
                # Paare je Teil an den Gliedern; Rumpf-/Beckenränder (rim_a/rim_b) tauschen im Konstruktor links die Kante: dort als Menge.
                single = [pid for pid in right if not pid.startswith(('torso_', 'pelvis_')) or '_kit_shoulder_' in pid or '_kit_hip_' in pid]
                for pid in single:
                    self.assertLessEqual(_distance(profiles._cloud(kit[pid]) * mirror, profiles._cloud(kit[_twin(pid)])), MIRROR, pid)
                rest = [pid for pid in right if pid not in single]
                if rest:
                    a = _cloud([kit[pid] for pid in rest]) * mirror
                    b = _cloud([kit[_twin(pid)] for pid in rest])
                    self.assertLessEqual(_distance(a, b), MIRROR)

    def test_other_assemblies_stay_byte_identical(self):
        for X, doc in self.docs.items():
            with self.subTest(assembly=X):
                replaced = {p['id'] for p in self.parts(self.base, X)}
                new = {p['id']: p for p in doc['parts']}
                for old in self.base['parts']:
                    if old['assembly'] == X:
                        continue
                    part = new[old['id']]
                    if old.get('parent_part') in replaced:
                        self.assertIn('_kit_', part['parent_part'])
                        self.assertEqual(new[part['parent_part']]['assembly'], X)
                        part = dict(part, parent_part=old['parent_part'])
                    self.assertEqual(part, old)

    def test_no_outliers_and_parents_resolve(self):
        every = _cloud(self.base['parts'])
        low, high = every.min(axis=0) - OUTLIER, every.max(axis=0) + OUTLIER
        for X, doc in self.docs.items():
            with self.subTest(assembly=X):
                cloud = _cloud(self.parts(doc, X))
                self.assertTrue(np.all(cloud >= low) and np.all(cloud <= high))
                model.normalize(doc)          # parent_part bekannt und azyklisch

    def test_all_nine_together_evaluate(self):
        doc = _document(_params({X: 'B' for X in NINE}))
        self.assertEqual({p['assembly'] for p in doc['parts'] if '_kit_' not in p['id']}, {'head'})
        for X in NINE:
            self.assertLessEqual(float(_deviation(self.parts(self.base, X), self.parts(doc, X)).max()), HULL, X)
        ids = {p['id'] for p in doc['parts']}
        self.assertTrue(all(a['part'] in ids for a in doc['anchors'].values()))
        result = geom.evaluate(model.normalize(doc))
        self.assertEqual(len(result['parts']), len(doc['parts']))

    def test_variant_parameters_act_on_replacement_and_neighbours_stay(self):
        plain, chamfer = self.docs['feet'], _document(_params({'feet': 'C'}))
        self.assertNotEqual(self.parts(plain, 'feet'), self.parts(chamfer, 'feet'))
        self.assertLessEqual(float(_deviation(self.parts(self.base, 'feet'), self.parts(chamfer, 'feet')).max()), HULL)
        # Feldvariante am Oberschenkel und Proportion neben dem Ersatz: Oberschenkel wie ohne Ersatz, Unterschenkel-Ersatz wächst mit.
        field = _document(_params({'thighs': 'C'}, dict(legs=1.2)))
        both = _document(_params({'thighs': 'C', 'shins': 'B'}, dict(legs=1.2)))
        self.assertEqual(self.parts(both, 'thighs'), self.parts(field, 'thighs'))
        self.assertNotEqual(self.parts(field, 'thighs'), self.parts(self.base, 'thighs'))
        thin, thick = _cloud(self.parts(self.docs['shins'], 'shins')), _cloud(self.parts(both, 'shins'))
        growth = np.ptp(thick, axis=0) / np.ptp(thin, axis=0)
        self.assertGreater(float(growth[0]), 1.05)          # Querschnitt (Weltbreite x) folgt legs = 1,2
        self.assertLess(float(growth[2]), 1.05)             # Höhe: Proportion skaliert keine z, nur der Knieradius knee_r wächst mit
        self.assertLess(float(growth[2]), float(growth[0]))
        for name, anchor in both['anchors'].items():
            self.assertLessEqual(float(np.abs(np.subtract(anchor['at'], field['anchors'][name]['at'])).max()), JOINT)

    def test_head_is_not_in_replace_mode_yet(self):
        with self.assertRaisesRegex(ValueError, 'ohne Ersatzmodus'):
            _document(_params({'head': 'B'}))

    def test_counter_check_without_fit_breaks_the_hull(self):
        with mock.patch.object(replacement, 'FIT', False):
            raw = {X: _document(_params({X: 'B'})) for X in ('upper_body', 'pelvis', 'shoulders', 'thighs', 'shins', 'feet', 'forearms')}
        for X, doc in raw.items():
            with self.subTest(assembly=X):
                deviation = _deviation(self.parts(self.base, X), self.parts(doc, X))
                self.assertGreater(float(deviation.max()), HULL, f'{X}: {np.round(deviation * 100, 1)} %')


if __name__ == '__main__':
    unittest.main()
