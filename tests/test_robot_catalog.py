"""0.14 Kitbash: Schnittstelle des Varianten-Baukastens je Einzelteil (Katalog, Register v2, Spec-Feld `variants`, beide Typen)."""
import copy
import tomllib
import unittest
from unittest import mock

from formgen.models.robot import catalog
from formgen.models.robot import roboterbasic_01 as basic1
from formgen.models.robot import roboterbasic_02 as basic2
from formgen.robot import lines, spec

ORIGIN = dict(kind='Annahme', source='Test')


def variant(**kw):
    base = dict(assembly='feet', letter='Z', name='Test Boot', since='0.14', idea='Test', origin=ORIGIN, params={'legs': {'foot_ch': 20}})
    return catalog.Variant(**dict(base, **kw))


class CatalogTest(unittest.TestCase):
    def test_every_assembly_has_its_base_and_ids_follow_the_rule(self):
        kit = catalog.load()
        self.assertEqual(tuple(kit), catalog.ASSEMBLIES)
        self.assertEqual(sorted(catalog.ASSEMBLIES), sorted(lines.ASSEMBLIES))
        self.assertEqual(len(set(catalog.CODES.values())), len(catalog.ASSEMBLIES))
        for a, variants in kit.items():
            self.assertEqual(variants[catalog.BASE].name, 'Basic', a)
            for letter, v in variants.items():
                self.assertEqual(v.id, f'{catalog.CODES[a]}-{letter}')
                self.assertEqual(catalog.parse(a, v.id, kit), v)

    def test_rule_rejects_bad_letters_names_doubles_and_locked_keys(self):
        catalog.validate([variant()])
        for bad, reason in [(dict(letter='I'), 'Kennbuchstabe'), (dict(letter='A'), 'Kennbuchstabe'), (dict(name='four words are here'), 'Name'),
                            (dict(name='Averyveryverylongname'), 'Name'), (dict(origin=dict(kind='geraten', source='x')), 'Herkunft'),
                            (dict(params={'skeleton': {}}), 'gehören dem Typ'), (dict(params={'proportion': {}}), 'gehören dem Typ'),
                            (dict(params={}), 'ohne Wirkung'), (dict(ra02='blend'), 'ra02'), (dict(assembly='tail'), 'unbekannt')]:
            with self.assertRaisesRegex(ValueError, reason, msg=bad):
                catalog.validate([variant(**bad)])
        with self.assertRaisesRegex(ValueError, 'doppelt'):
            catalog.validate([variant(), variant(letter='Y')])          # gleicher Name
        with self.assertRaisesRegex(ValueError, 'doppelt'):
            catalog.validate([variant(), variant(name='Other Boot')])    # gleicher Buchstabe

    def test_parse_rejects_wrong_code_and_unknown_letters(self):
        for assembly, vid in [('feet', 'SH-A'), ('feet', 'FT-Q'), ('feet', 'FT_A'), ('tail', 'FT-A')]:
            with self.assertRaises(ValueError, msg=vid):
                catalog.parse(assembly, vid)

    def test_options_change_nothing_against_the_constructors_without_them(self):
        """Richter 0.14: Werte gegen body.py prüfen, nicht nur Schlüssel – ohne die OPTIONS-Schlüssel bauen die Konstruktoren dasselbe."""
        from formgen.models.robot import body

        def strip(params, table):
            out = copy.deepcopy(params)
            for key, value in table.items():
                if isinstance(value, dict):
                    out[key] = strip(out[key], value)
                else:
                    out.pop(key, None)
            return out
        for module in (basic1, basic2):
            for family, build in (('torso', body.torso), ('pelvis', body.pelvis), ('legs', body.legs), ('upper_arm', body.upper_arm)):
                bare = strip(module.PARAMS[family], catalog.OPTIONS[family])
                self.assertNotEqual(bare, module.PARAMS[family])
                self.assertEqual(build(bare), build(module.PARAMS[family]), f'{module.__name__} {family}')

    def test_options_match_the_constructor_defaults(self):
        """Die OPTIONS-Schlüssel stehen in PARAMS beider Typen; ein Wert, den body.py ohne Schlüssel nähme, ändert nichts (Grundform bytegleich)."""
        for module in (basic1, basic2):
            for family, table in catalog.OPTIONS.items():
                self.assertEqual(catalog.options(module.PARAMS[family], table), module.PARAMS[family], module.__name__)


class ApplyTest(unittest.TestCase):
    def test_all_base_returns_the_same_object(self):
        for num, module in ((1, basic1), (2, basic2)):
            self.assertEqual(module.PARAMS['variants'], catalog.BASIC['variants'])
            self.assertIs(catalog.apply(module.PARAMS, num=num, measured=num == 2), module.PARAMS)

    def test_variant_merges_strictly_and_per_type(self):
        kit = catalog.validate([variant(types={2: {'legs': {'ankle_len': 130}}}), variant(assembly='hands', letter='Y', name='Big Hand',
                                                                                           params={}, ra02='replace')])
        params = copy.deepcopy(basic2.PARAMS)
        params['variants'].update(feet='Z', hands='Y')
        out = catalog.apply(params, num=2, measured=True, catalog=kit)
        self.assertEqual((out['legs']['foot_ch'], out['legs']['ankle_len'], out['replace']), (20, 130, ['hands']))
        one = catalog.apply(dict(basic1.PARAMS, variants=params['variants']), num=1, catalog=kit)
        self.assertEqual((one['legs']['foot_ch'], one['legs']['ankle_len']), (20, basic1.PARAMS['legs']['ankle_len']))
        self.assertNotIn('replace', one)
        self.assertEqual(basic2.PARAMS['legs']['foot_ch'], 14)          # Eingabe unverändert
        typo = catalog.validate([variant(params={'legs': {'foot_chh': 20}})])
        with self.assertRaisesRegex(ValueError, 'FT-Z: unbekannter Parameter legs.foot_chh'):
            catalog.apply(dict(params, variants=dict(params['variants'], hands='A')), num=1, catalog=typo)
        with self.assertRaisesRegex(ValueError, 'variants'):
            catalog.apply(dict(params, variants={'feet': 'A'}), num=1)

    def test_both_types_build_a_field_variant(self):
        kit = catalog.validate([variant()])
        for num, module in ((1, basic1), (2, basic2)):
            params = copy.deepcopy(module.PARAMS)
            params['variants']['feet'] = 'Z'
            with mock.patch.object(catalog, 'load', return_value=kit):        # parts() wendet die Wahl selbst an
                changed = {p['id']: p for p in module.parts(params)}
            base = {p['id']: p for p in module.parts()}
            self.assertEqual(set(changed), set(base), module.__name__)
            moved = {base[i]['assembly'] for i in base if base[i] != changed[i]}
            self.assertEqual(moved, {'feet'}, module.__name__)


class RegisterTest(unittest.TestCase):
    def test_register_is_version_2_and_v1_migrates_to_base(self):
        text = lines.REGISTER.read_text()
        self.assertEqual(tomllib.loads(text)['version'], lines.VERSION)
        v1 = tomllib.loads(text)
        v1.pop('version')
        for e in v1['lines']:
            e.pop('parts', None)
        migrated = lines.migrate(v1)
        self.assertEqual(migrated['version'], 2)
        self.assertFalse(any('parts' in e for e in migrated['lines']))
        with self.assertRaisesRegex(ValueError, 'Version 2'):
            lines.migrate(dict(v1, lines=[dict(v1['lines'][0], parts={'feet': 'FT-A'})]))
        with self.assertRaisesRegex(ValueError, 'Version 3'):
            lines.migrate(dict(v1, version=3))

    def test_parts_are_validated_and_reach_entry_and_params(self):
        reg = lines.load()
        bad = [dict(reg['lines'][0], parts={'feet': 'SH-A'})]
        with self.assertRaisesRegex(ValueError, 'Linie A: feet'):
            lines.validate(reg['types'], bad)
        for key in ('variants', 'replace', 'helmet'):          # Richter 0.14: Teilewahl nie an der Variantenregel vorbei
            with self.assertRaisesRegex(ValueError, 'nur über'):
                lines.validate(reg['types'], [dict(reg['lines'][0], params={'1': {key: {}}})])
        good = lines.validate(reg['types'], [dict(reg['lines'][0], parts={'feet': 'FT-A'})])
        entry = lines.sheets(good)['RA01']
        self.assertEqual(entry['parts'], {'feet': 'FT-A'})
        self.assertEqual(lines.params_of(entry)['variants'], catalog.BASIC['variants'])
        self.assertEqual([v['letter'] for v in lines.variants_of(entry)], ['A'] * 10)
        self.assertNotIn('parts', lines.sheets()['RA01'])               # ohne Wahl wie in Version 1: Spec und Schlüssel von A bleiben


class KitTest(unittest.TestCase):
    def test_every_assembly_has_at_least_two_shape_variants_and_lines_b_to_e_use_the_kit(self):
        kit = catalog.load()
        for a, variants in kit.items():
            self.assertGreaterEqual(len(variants) - 1, 2, a)
        chosen = {}
        for sid, entry in lines.sheets().items():
            parts = entry.get('parts', {})
            if entry['line']['letter'] == 'A':
                self.assertEqual(parts, {}, sid)
                continue
            self.assertGreaterEqual(len(parts), 9, sid)                  # jede Linie ist ein eigener Roboter, nicht nur eine Farbe
            chosen.setdefault(entry['line']['letter'], tuple(sorted(parts.items())))
        self.assertEqual(len(set(chosen.values())), 4, 'B–E: je Linie eine eigene Kombination')
        used = {vid for combo in chosen.values() for _, vid in combo}
        for a, variants in kit.items():
            self.assertTrue({v.id for k, v in variants.items() if k != 'A'} & used, f'{a}: keine Linie nutzt eine Variante')


class PackDetailTest(unittest.TestCase):
    def test_ra02_without_backpack_drops_its_measured_details(self):
        """Regression 0.14: Die Back*-Details von RA02 sitzen auf dem Rückenmodul; an `back` gebunden blieben sie bei UB-B 160 mm hinter dem Rumpf
        stehen. Gegenprobe: mit Rückenmodul liegen Teile so weit hinten."""
        import numpy as np

        def depth(params):
            out = []
            for p in basic2.parts(params):
                if p['assembly'] == 'upper_body':
                    for key in ('points', 'vertices', 'rings'):
                        if key in p:
                            out.append(np.asarray(p[key], float).reshape(-1, 3)[:, 0].min())
            return min(out)
        params = copy.deepcopy(basic2.PARAMS)
        params['variants']['upper_body'] = 'B'
        self.assertGreater(depth(params), -150)
        self.assertLess(depth(basic2.PARAMS), -290)


class CenterMirrorTest(unittest.TestCase):
    def test_ra02_center_parts_stay_mirror_symmetric_under_field_variants(self):
        """Richter 0.14: Mittelteile von RA02 (gemessen symmetrisch zu x = 0, z. B. Codpiece) wurden im Feldweg schief, wenn eine Variante die
        Punktzahl des Konstruktorteils änderte (Mitte von Codpiece bei PV-C 5,8 mm, Brustband in RC02 28 mm). Gefordert: Mitte der Hülle höchstens 1 mm neben der Grundform."""
        import numpy as np

        from formgen.models.robot import roboterbasic_02_parameters as profiles

        def centers(params):
            out = {}
            for p in basic2.parts(params):
                x = profiles._cloud(p)[:, 0]          # Weltmaß x (rechte Körperseite), auch aus `items`
                if p['source_object'][-2:] not in ('_L', '_R') and len(x):
                    out[p['id']] = (x.min() + x.max()) / 2
            return out
        base = {k: v for k, v in centers(basic2.PARAMS).items() if abs(v) < 1.0}
        self.assertIn('pelvis_codpiece', base)
        kit = catalog.load()
        cases = []
        for a in ('upper_body', 'pelvis'):
            for letter, v in kit[a].items():
                if letter != 'A' and v.ra02 == 'field':
                    params = copy.deepcopy(basic2.PARAMS)
                    params['variants'][a] = letter
                    cases.append((v.id, params))
        cases += [(sid, lines.params_of(e)) for sid, e in lines.sheets().items() if e['type']['num'] == 2 and e['line']['letter'] != 'A']
        for name, params in cases:
            got = centers(params)
            with self.subTest(case=name):
                off = {k: round(got[k], 2) for k in base if k in got and abs(got[k]) > 1.0}
                self.assertEqual(off, {})
        with mock.patch.object(profiles, '_centered', return_value=False):          # Gegenprobe: ohne Mittelung liegt eine Mitte daneben
            got = centers(dict(cases[-3][1]))                                         # RC02
            self.assertTrue(any(abs(got[k]) > 1.0 for k in base if k in got))


class SpecTest(unittest.TestCase):
    def test_spec_key_follows_catalog_text(self):
        """Richter 0.14: spec.build schreibt Name und Idee der Varianten; eine geänderte Idee muss den Schlüssel der Spec-Stufe ändern."""
        from formgen.robot import pipeline
        entry = lines.sheets()['RB01']
        self.assertNotIn('variants', pipeline.spec_params(lines.sheets()['RA01']))      # A wie vor 0.14
        before = pipeline.spec_params(entry)
        kit = catalog.load()
        v = kit['head'][entry['parts']['head'].split('-')[1]]
        kit['head'][v.letter] = catalog.Variant(**dict(vars(v), idea=v.idea + ' (neu)'))
        with mock.patch.object(catalog, 'load', return_value=kit):
            self.assertNotEqual(pipeline.spec_params(entry), before)

    def test_variants_field_only_with_a_choice_and_migrate_fills_base(self):
        doc = dict(bounds_m=[[0, 0, 0], [1, 1, 1]], parts=[dict(id='p', assembly='feet', role='shell', shape='hull')], counts=dict(triangles=1),
                   assemblies=[dict(id=a, de=a, group='g', group_de='G') for a in ['feet']], info=dict(id='RA01', name_de='x', provenance={}))
        entry = copy.deepcopy(lines.sheets()['RA01'])
        plain = spec.build(doc, entry)
        self.assertNotIn('variants', plain)
        self.assertEqual([v['id'] for v in spec.migrate(plain)['variants']], [f'{c}-A' for c in catalog.CODES.values()])
        entry['parts'] = {'feet': 'FT-A'}
        chosen = spec.build(doc, entry)
        self.assertEqual(len(chosen['variants']), 10)
        self.assertEqual(spec.migrate(chosen)['variants'], chosen['variants'])


if __name__ == '__main__':
    unittest.main()
