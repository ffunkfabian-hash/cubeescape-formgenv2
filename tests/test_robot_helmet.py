"""0.14 Kitbash: Kopfvarianten (helmet.py, catalog/head.py) in beiden Basic-Typen – Grundform unverändert, Gruppen, Feld, Aufsätze, Vielfalt."""
import copy
import re
import unittest
from unittest import mock

import numpy as np

from formgen import geom, model
from formgen.models.robot import catalog, helmet
from formgen.models.robot import roboterbasic_01 as basic1
from formgen.models.robot import roboterbasic_02 as basic2
from formgen.models.robot.catalog import head as head_catalog
from formgen.robot import lines, variety

TYPES = ((1, basic1), (2, basic2))
LETTERS = [v.letter for v in head_catalog.VARIANTS]


def with_head(module, letter):
    params = copy.deepcopy(module.PARAMS)
    params['variants']['head'] = letter
    return params


def points(part):
    return helmet._points(part)


def head_inputs(num):
    """Kopfteile, wie sie ra01/ra02 bekommen, und der Kopfrahmen."""
    if num == 1:
        _, frames = basic1.rig_of(basic1.PARAMS)
        return basic1._helmet(frames), frames
    return [p for p in basic2.PARTS if p['assembly'] == 'head'], basic2._frames(basic2.PARAMS)


class Built:
    """Dokumente je Typ und Kopfvariante, einmal gebaut."""
    docs = {}

    @classmethod
    def doc(cls, num, letter):
        if (num, letter) not in cls.docs:
            module = dict(TYPES)[num]
            cls.docs[num, letter] = module.document(with_head(module, letter), sheet_id=f'RA{num:02d}')
        return cls.docs[num, letter]


class NeutralTest(unittest.TestCase):
    def test_params_carry_neutral_and_neutral_returns_the_same_list(self):
        for num, module in TYPES:
            self.assertEqual(module.PARAMS['helmet'], helmet.NEUTRAL)
            parts, frames = head_inputs(num)
            params = dict(module.PARAMS, helmet=copy.deepcopy(helmet.NEUTRAL))     # gleicher Wert, anderes Objekt
            call = helmet.ra01 if num == 1 else helmet.ra02
            self.assertIs(call(parts, params, frames), parts)

    def test_base_documents_unchanged_by_the_catalog(self):
        """Grundform A: parts() liefert dieselben Teile wie vor dem Katalog (helmet.ra0x gibt die Liste zurück)."""
        for num, module in TYPES:
            self.assertEqual(module.parts(with_head(module, 'A')), module.PARTS)

    def test_check_rejects_values_outside_the_limits_and_unknown_keys(self):
        helmet.check(copy.deepcopy(helmet.NEUTRAL))
        for path, value in ((('dome', 'height'), 1.5), (('jaw', 'forward'), 40.0), (('crest',), 80.0), (('ears',), -1.0)):
            P = copy.deepcopy(helmet.NEUTRAL)
            target = P
            for k in path[:-1]:
                target = target[k]
            target[path[-1]] = value
            with self.assertRaisesRegex(ValueError, 'außerhalb'):
                helmet.check(P)
        with self.assertRaisesRegex(ValueError, 'Schlüssel'):
            helmet.check(dict(helmet.NEUTRAL, horns=1.0))


class GroupTest(unittest.TestCase):
    def test_groups_cover_every_head_part_of_both_types_exactly_once(self):
        keys = {1: [p['id'] for p in basic1.PARTS if p['assembly'] == 'head'],
                2: [p['source_object'] for p in basic2.PARTS if p['assembly'] == 'head']}
        self.assertEqual((len(keys[1]), len(keys[2])), (61, 31))        # Helm H 80 (58) + Hals aus body.head (3); RA02 31 gemessene Teile
        for num, names in keys.items():
            listed = [k for group in helmet.GROUPS[num].values() for k in group]
            self.assertEqual(len(listed), len(set(listed)), num)
            self.assertEqual(sorted(listed), sorted(names), num)
            self.assertEqual(set(helmet.GROUPS[num]), set(helmet.FIELD_GROUPS) | {helmet.FIXED}, num)
            self.assertTrue(all(k in names for k in helmet.EYES[num]))
        with self.assertRaisesRegex(ValueError, 'keiner Helmgruppe'):
            helmet.group_of(1, 'helmet_horn')

    def test_field_is_mirror_symmetric_and_does_not_fold(self):
        """Jacobi-Determinante des Felds an allen Punkten der verformten Teile > 0,25 (Annahme: keine Faltung, keine gekippten Flächen);
        Spiegelprobe: d(spiegel p) = spiegel d(p)."""
        rng = np.random.default_rng(14)
        for num, _ in TYPES:
            parts, frames = head_inputs(num)
            R, o, _, _ = frames['head']
            key = (lambda p: p['id']) if num == 1 else (lambda p: p['source_object'])
            local = {key(p): helmet._local(R, o, points(p)) for p in parts}
            L = helmet.landmarks(num, local)
            for v in head_catalog.VARIANTS:
                P = catalog.merge(helmet.NEUTRAL, v.params['helmet'])
                for group in set(helmet.FIELD_GROUPS) - set(helmet.ISOLATED[num]):
                    d = helmet.displacement(num, group, P, L)
                    p = np.concatenate([q for k, q in local.items() if helmet.group_of(num, k) == group] or [np.empty((0, 3))])
                    if not len(p):
                        continue
                    J = np.stack([(d(p + e) - d(p - e)) / 1.0 for e in np.eye(3) * 0.5], axis=2) + np.eye(3)
                    self.assertGreater(np.linalg.det(J).min(), 0.25, (num, v.id, group))
                    q = rng.uniform(p.min(0), p.max(0), (200, 3))
                    np.testing.assert_allclose(d(q * (-1, 1, 1)), d(q) * (-1, 1, 1), atol=1e-9, err_msg=f'{num} {v.id}')
            # Gegenprobe: weit außerhalb LIMITS (Hinterkopf 150 mm nach vorn gezogen) faltet das Feld, die Prüfung schlägt an
            P = catalog.merge(helmet.NEUTRAL, dict(back=dict(out=-150.0)))
            d = helmet.displacement(num, 'dome', P, L)
            p = np.concatenate([q for k, q in local.items() if helmet.group_of(num, k) not in helmet.ISOLATED[num]])
            J = np.stack([(d(p + e) - d(p - e)) / 1.0 for e in np.eye(3) * 0.5], axis=2) + np.eye(3)
            self.assertLess(np.linalg.det(J).min(), 0, num)
            with self.assertRaisesRegex(ValueError, 'außerhalb'):
                helmet.check(P)


class VariantTest(unittest.TestCase):
    def test_catalog_has_three_real_head_variants(self):
        kit = catalog.load()['head']
        self.assertEqual(sorted(kit), ['A', 'B', 'C', 'D'])
        for v in head_catalog.VARIANTS:
            self.assertEqual((v.assembly, v.ra02, set(v.params), v.types), ('head', 'field', {'helmet'}, {}))
            P = catalog.merge(helmet.NEUTRAL, v.params['helmet'])
            helmet.check(P)
            self.assertTrue(any(P[k] for k in helmet.ATTACHMENTS), v.id)       # jede Variante trägt Aufsätze
            self.assertTrue(any(P[g] != helmet.NEUTRAL[g] for g in helmet.FIELD_GROUPS), v.id)      # und verformt

    def test_every_variant_builds_in_both_types_and_only_the_head_changes(self):
        for num, module in TYPES:
            base = Built.doc(num, 'A')
            before = {p['id']: p for p in base['parts']}
            head_box = np.concatenate([points(p) for p in base['parts'] if p['assembly'] == 'head'])
            lo, hi = head_box.min(0) - 150, head_box.max(0) + 150
            for letter in LETTERS:
                doc = Built.doc(num, letter)
                model.normalize(doc)
                lines.check_document(doc)
                now = {p['id']: p for p in doc['parts']}
                self.assertEqual(len(now), len(doc['parts']))
                self.assertLessEqual(set(before), set(now), (num, letter))                       # Teile-IDs der Grundform bleiben
                self.assertEqual(doc['anchors'], base['anchors'])                               # Halsanker, Skelett, Haltung
                for pid, p in before.items():
                    if p['assembly'] != 'head' or helmet.group_of(num, p['id'] if num == 1 else p['source_object']) == helmet.FIXED:
                        self.assertEqual(now[pid], p, (num, letter, pid))
                new = [now[i] for i in set(now) - set(before)]
                self.assertTrue(new)
                for p in new:
                    self.assertRegex(p['id'], r'^head_')
                    self.assertEqual((p['assembly'], p['segment']), ('head', 'head'))
                    self.assertIn(p['provenance']['kind'], ('Vorgabe', 'Annahme'))
                for p in doc['parts']:
                    if p['assembly'] == 'head':
                        q = points(p)
                        self.assertTrue(np.isfinite(q).all() and (q >= lo).all() and (q <= hi).all(), (num, letter, p['id']))

    def test_attachment_pairs_mirror(self):
        """Paare rechts/links spiegelgleich zur Mittelebene x = 0 (beide Kopfrahmen liegen in der A-Position auf ihr)."""
        for num, module in TYPES:
            frames = basic1.rig_of(basic1.PARAMS)[1] if num == 1 else basic2._frames(basic2.PARAMS)
            R, o, _, _ = frames['head']
            self.assertAlmostEqual(o[0], 0)
            np.testing.assert_allclose(np.abs(R[:, 0]), (1, 0, 0), atol=1e-12)
            for letter in LETTERS:
                parts = {p['id']: p for p in Built.doc(num, letter)['parts'] if p['id'].startswith('head_')}
                right = [i for i in parts if re.search(r'_r(_|$)', i)]
                self.assertEqual(len(right), len([i for i in parts if re.search(r'_l(_|$)', i)]), (num, letter))
                for i in right:
                    j = re.sub(r'_r(_|$)', r'_l\1', i, count=1)
                    a, b = points(parts[i]), points(parts[j]) * (1, 1, -1)
                    self.assertEqual({tuple(np.round(q, 3)) for q in a}, {tuple(np.round(q, 3)) for q in b}, (num, letter, i))
                    self.assertEqual((parts[i]['side'], parts[j]['side'], parts[i]['role']), ('R', 'L', parts[j]['role']))


class VarietyTest(unittest.TestCase):
    """Vielfalt des Einzelteils Kopf gegen die Grundform (variety.PART_THRESHOLD, kleinste Ansicht), wie variety.measure_parts: Masken
    nur der Kopfteile, ohne Booleans und Fasen. Dass die übrigen Einzelteile gleich bleiben, prüft VariantTest Teil für Teil."""

    @staticmethod
    def head_triangles(doc):
        parts = [p for p in doc['parts'] if p['assembly'] == 'head']
        ids = {p['id'] for p in parts}
        parts = [p if p.get('parent_part') in ids | {None} else {k: v for k, v in p.items() if k != 'parent_part'} for p in parts]
        head = dict(doc, parts=parts, assemblies=[a for a in doc['assemblies'] if a['id'] == 'head'],
                    anchors={k: a for k, a in doc['anchors'].items() if a['part'] in ids})
        tris = []
        for p in geom.evaluate(model.normalize(head), booleans=False, bevels=False)['parts']:
            v = np.asarray(p['mesh']['vertices'], float)
            tris += [v[[f[0], f[i], f[i + 1]]] for f in p['mesh']['faces'] for i in range(1, len(f) - 1)]
        return np.array(tris).reshape(-1, 3, 3)

    def test_every_head_variant_deviates_in_both_types(self):
        for num, _ in TYPES:
            base = self.head_triangles(Built.doc(num, 'A'))
            for letter in LETTERS:
                iou = variety._part_iou(base, self.head_triangles(Built.doc(num, letter)))
                self.assertLessEqual(min(iou.values()), variety.PART_THRESHOLD, (num, letter, iou))

    def test_counter_check_variant_without_effect_is_equal_for_the_right_reason(self):
        """Gegenprobe: Eine Variante, die nur NEUTRAL-Werte setzt, besteht die Variantenregel, wirkt aber nicht: ra0x bekommt NEUTRAL und
        gibt dieselbe Liste zurück (der Grund), das Maß meldet für den Kopf 1,0 in allen Ansichten (GLEICH)."""
        idle = catalog.Variant(assembly='head', letter='Z', name='Idle Head', since='0.14', idea='Gegenprobe',
                               origin=dict(kind='Annahme', source='Test'), params={'helmet': dict(crest=0.0, dome=dict(height=1.0))})
        kit = catalog.validate([*head_catalog.VARIANTS, idle])
        for num, module in TYPES:
            call = 'ra01' if num == 1 else 'ra02'
            with mock.patch.object(catalog, 'load', return_value=kit), \
                    mock.patch.object(helmet, call, wraps=getattr(helmet, call)) as spy:
                doc = module.document(with_head(module, 'Z'), sheet_id=f'RA{num:02d}')
            (args, _), = spy.call_args_list
            self.assertEqual(args[1]['helmet'], helmet.NEUTRAL)
            self.assertIs(getattr(helmet, call)(*args), args[0])
            self.assertEqual(doc['parts'], module.PARTS)
            iou = variety._part_iou(self.head_triangles(Built.doc(num, 'A')), self.head_triangles(doc))
            self.assertEqual(iou, {view: 1.0 for view in variety.VIEWS})
            self.assertFalse(min(iou.values()) <= variety.PART_THRESHOLD)


if __name__ == '__main__':
    unittest.main()
