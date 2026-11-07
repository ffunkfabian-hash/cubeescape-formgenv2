"""0.13 Gantry: Bauteilproportionen der Roboterlinien (Faktoren auf Profile, Vielfaltsmaß, RA02-Übertragung)."""
import copy
import unittest

from formgen.models.robot import proportion
from formgen.models.robot import roboterbasic_01 as basic1
from formgen.models.robot import roboterbasic_02 as basic2
from formgen.robot import lines, variety


def merged(module, **factors):
    return lines.merge(module.PARAMS, {'proportion': factors})


class ApplyTest(unittest.TestCase):
    def test_neutral_returns_the_same_object(self):
        for module in (basic1, basic2):
            self.assertIs(proportion.apply(module.PARAMS), module.PARAMS)
            self.assertEqual(module.PARAMS['proportion'], proportion.NEUTRAL)
            self.assertEqual(module.REFERENCE_PARAMS['proportion'], proportion.NEUTRAL)       # Abnahmehaltung bleibt unberührt

    def test_each_factor_changes_only_its_group(self):
        base = basic1.PARAMS
        groups = dict(shoulders=[('torso', 'pauldron')], torso=[('torso', 'core'), ('torso', 'collar'), ('torso', 'waist'), ('torso', 'gorget')],
                      legs=[('legs', 'thigh'), ('legs', 'shin'), ('legs', 'kneecap'), ('legs', 'knee_r')], pack=[('torso', 'back')])
        for name, touched in groups.items():
            out = proportion.apply(merged(basic1, **{name: 1.2}))
            changed = {(a, b) for a in ('torso', 'legs', 'pelvis', 'upper_arm') for b in out[a] if out[a][b] != base[a][b]}
            self.assertEqual(changed, set(touched), name)
            self.assertEqual({k for k in out if k not in ('torso', 'legs') and out[k] != base[k]}, {'proportion'}, name)

    def test_only_cross_sections_scale_heights_stay(self):
        out = proportion.apply(merged(basic1, legs=1.25, shoulders=0.8))
        for new, old in zip(out['legs']['thigh'], basic1.PARAMS['legs']['thigh']):
            self.assertEqual((new[0], new[3]), (old[0], old[3]))            # z und Versatz bleiben
            self.assertAlmostEqual(new[1] / old[1], 1.25)
            self.assertAlmostEqual(new[2] / old[2], 1.25)
        for new, old in zip(out['torso']['pauldron']['rows'], basic1.PARAMS['torso']['pauldron']['rows']):
            self.assertEqual((new[0], new[3], new[4]), (old[0], old[3], old[4]))
            self.assertAlmostEqual(new[1] / old[1], 0.8)

    def test_input_is_never_modified(self):
        before = copy.deepcopy(basic1.PARAMS)
        proportion.apply(merged(basic1, shoulders=1.3, torso=0.9, legs=1.1, pack=0.8))
        self.assertEqual(basic1.PARAMS, before)

    def test_rejects_unknown_keys_and_values_out_of_range(self):
        with self.assertRaisesRegex(ValueError, 'erwartet'):
            proportion.check(dict(proportion.NEUTRAL, head=1.0))
        with self.assertRaisesRegex(ValueError, 'proportion.legs'):
            proportion.apply(merged(basic1, legs=1.5))
        with self.assertRaisesRegex(ValueError, 'proportion.pack'):
            proportion.apply(merged(basic1, pack=0.5))
        with self.assertRaisesRegex(ValueError, 'proportion.nope'):
            lines.merge(basic1.PARAMS, {'proportion': {'nope': 1.0}})


class ModelTest(unittest.TestCase):
    def test_both_types_keep_ids_and_counts_with_proportions(self):
        """Der Fehler vor 0.13: RA02 hängte bei jeder Profiländerung Konstruktorteile ohne gemessenes Gegenstück an (30 bei den Beinen)."""
        for module in (basic1, basic2):
            base = [p['id'] for p in module.parts()]
            other = [p['id'] for p in module.parts(merged(module, shoulders=1.3, torso=1.1, legs=1.2, pack=0.8))]
            self.assertEqual(sorted(base), sorted(other), module.__name__)

    def test_geometry_grows_with_the_factor(self):
        for module in (basic1, basic2):
            wide = {p['id']: p for p in module.parts(merged(module, legs=1.3))}
            base = {p['id']: p for p in module.parts()}
            self.assertEqual(set(wide), set(base))
            moved = [i for i in base if base[i] != wide[i]]
            self.assertTrue(moved, module.__name__)
            self.assertTrue(all(base[i]['assembly'] in ('thighs', 'shins', 'feet', 'pelvis') for i in moved), module.__name__)

    def test_ra02_still_adds_a_switched_on_feature(self):
        params = copy.deepcopy(basic2.PARAMS)
        params['torso']['waist_pistons'] = True
        ids = {p['id'] for p in basic2.parts(params)} - {p['id'] for p in basic2.parts()}
        self.assertTrue(ids and all('_profile_' in i for i in ids), ids)


class RegisterTest(unittest.TestCase):
    def test_every_coloured_line_has_its_own_proportions(self):
        reg = lines.sheets()
        seen = set()
        for sid, entry in reg.items():
            module = lines.module_of(entry)
            full = lines.merge(module.PARAMS, entry['params'])['proportion']
            proportion.check(full)
            if entry['line']['letter'] == 'A':
                self.assertEqual(full, proportion.NEUTRAL, sid)
            else:
                self.assertNotEqual(full, proportion.NEUTRAL, sid)
                seen.add(tuple(sorted(full.items())))
        self.assertEqual(len(seen), 4, 'B–E: je Linie eigene Faktoren')


class VarietyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = variety.measure()

    def test_every_line_differs_from_a_and_from_each_other(self):
        rows = variety.verdict(self.result)
        self.assertEqual(len(self.result['against_a']), 8)
        self.assertEqual(len(self.result['pairs']), 12)
        gleich = [(k, least) for k, _, least, ok in rows if not ok]
        self.assertEqual(gleich, [])

    def test_counterproof_a_line_without_proportions_is_flagged_for_the_right_reason(self):
        reg = lines.load()
        one = dict(types=reg['types'][:1], lines=[dict(reg['lines'][0], types=[1]), dict(reg['lines'][1], types=[1], params={})])
        result = variety.measure(lines.validate(one['types'], one['lines']))
        (key, views, least, ok), = variety.verdict(result)
        self.assertEqual(key, 'RB01')
        self.assertFalse(ok)
        self.assertEqual(least, 1.0)           # identische Form, nur der Skin unterscheidet: die Silhouette ist dieselbe


if __name__ == '__main__':
    unittest.main()
