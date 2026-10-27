import copy
import json
from pathlib import Path
import tomllib
import unittest

import jsonschema
from formgen import geo, geom, model, prompts, spec

ROOT = Path(__file__).resolve().parents[1]


class SpecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.w01 = geom.evaluate(model.load(ROOT / 'formgen/models/weapons/w01_auto_rifle.py'))
        cls.weapon = spec.build(cls.w01)

    def test_original_import_contracts_preserved(self):
        for name, kind in [('KG02', 'weapon'), ('VS02', 'sight')]:
            with self.subTest(name=name):
                d = geo.load(ROOT / f'tests/fixtures/{name}.geo.json')
                original = json.loads((ROOT / f'tests/fixtures/{name}.spec.json').read_text())
                result = spec.build(d)
                schema = json.loads((ROOT / f'docs/schemas/{kind}-spec.schema.json').read_text())
                jsonschema.Draft202012Validator(schema).validate(result)
                self.assertEqual(result, original)
                result['parts'][0]['label'] = 'independent copy'
                self.assertEqual(d['source_spec'], original)
                del d['source_spec']
                with self.assertRaisesRegex(ValueError, 'SHA-geprüfte'):
                    spec.build(d)

    def test_w01_schema_ids_and_measured_extent(self):
        schema = json.loads((ROOT / 'docs/schemas/weapon-spec.schema.json').read_text())
        jsonschema.Draft202012Validator(schema).validate(self.weapon)
        self.assertEqual(len(self.weapon['parts']), len(self.w01['parts']))
        for i, (author, exported) in enumerate(zip(self.w01['parts'], self.weapon['parts'])):
            self.assertEqual(exported['id'], f'p{i:02d}')
            self.assertEqual(self.weapon['part_id_map'][author['id']], exported['id'])
            self.assertEqual(exported['source_id'], author['id'])
            self.assertEqual(exported['bounds_m'], author['bounds_m'])
            self.assertGreater(exported['area_m2'], 0)
        self.assertAlmostEqual(self.weapon['dimensions_m']['with_sight']['length'], .915, places=6)
        self.assertEqual(self.weapon['units']['reference_length_m'], .934)
        self.assertEqual(self.weapon['anchors']['Socket_CenterOfMass']['position_m'], None)
        self.assertEqual(self.weapon['axes']['origin'], 'Socket_Hand')

    def test_nonzero_origin_and_analytic_surface(self):
        d = geom.evaluate(model.load(ROOT / 'formgen/models/mini.py'))
        before = copy.deepcopy(d)
        result = spec.build(d)
        self.assertEqual(d, before)
        self.assertEqual(result['anchors']['Socket_Hand']['position_m'], [0, 0, 0])
        self.assertEqual(result['axes']['origin_world_m'], [0, -.02, -.03])
        shell = result['parts'][0]
        for actual, expected in zip(shell['bounds_m'][0], [-.015, -.08, .03]):
            self.assertAlmostEqual(actual, expected)
        self.assertAlmostEqual(shell['area_m2'], 2*(.1*.04+.1*.03+.04*.03))
        self.assertIn('Testgriffs', result['anchors']['Socket_Hand']['source'])
        del d['anchors']['Socket_Hand']
        with self.assertRaisesRegex(ValueError, 'Socket_Hand'):
            spec.build(d)

    def test_actual_skin_colors_and_multiple_role_colors(self):
        with (ROOT / 'skins.toml').open('rb') as stream:
            skins = tomllib.load(stream)
        by_id = {p['id']: p for p in self.weapon['palette']}
        self.assertEqual(by_id['nacht']['channels']['MT_Primary'], skins['skins']['nacht']['roles']['shell'])
        self.assertEqual(by_id['arktis']['channels']['MT_Primary'], skins['skins']['polar']['roles']['shell'])
        self.assertEqual(by_id['standard']['channels']['MT_Primary'], skins['roles']['shell']['color'])
        self.assertTrue(by_id['standard']['other_colors'])
        for part in self.weapon['parts']:
            self.assertEqual(part['color'], skins['roles'][part['role']]['color'])

    def test_figure_has_geometry_hierarchy_and_provenance(self):
        d = model.load(ROOT / 'formgen/models/mini.py')
        d['info']['kind'] = 'figure'
        d['poses'] = {'neutral': {'source': 'Annahme: Schnittstellentest'}}
        d['parts'][1]['parent_part'] = 'shell'
        d = geom.evaluate(d)
        result = spec.build(d)
        self.assertEqual(result['format'], 'cubeescape-formgen/figure-spec')
        self.assertEqual(result['format_version'], 1)
        self.assertEqual(result['assemblies'], d['assemblies'])
        self.assertEqual(result['anchors'], d['anchors'])
        self.assertEqual(result['poses'], d['poses'])
        self.assertEqual(result['parts'][1]['parent_part'], 'shell')
        self.assertEqual(result['parts'][0]['provenance']['kind'], 'Annahme')
        self.assertAlmostEqual(result['dimensions_m']['height'], .1)
        self.assertIn('mesh.vertices', result['measurement_source'])
        json.dumps(result, allow_nan=False)

    def test_channel_palette_uses_surface_shares_in_spec2_format(self):
        document = model.load(ROOT / 'formgen/models/mini.py')
        small = dict(document['parts'][0], role='metal', f1=10, u1=10, w=10)
        large = dict(small, id='grip', role='trim', f1=20, u1=20, w=20)
        document['parts'] = [small, large]
        document = geom.evaluate(document)
        result = spec.build(document)
        base = result['palette'][0]
        with (ROOT / 'skins.toml').open('rb') as stream:
            colors = tomllib.load(stream)['roles']
        # Cubes with side lengths 10/20 mm have a surface ratio of 1:4.
        self.assertEqual(base['channels']['MT_Metal'], colors['trim']['color'].upper())
        self.assertEqual(base['other_colors']['MT_Metal'],
                         [dict(color=colors['metal']['color'].upper(), share=.2)])
        document['parts'].reverse()
        self.assertEqual(spec.build(document)['palette'], result['palette'])

    def test_invalid_palette_mapping_or_share_is_rejected(self):
        for colors in ({'p01': '#123456'}, [dict(color='#123456', share=1.1)],
                       [dict(color='p01', share=.1)], [dict(color='#123456', share=True)]):
            value = copy.deepcopy(self.weapon)
            value['palette'][0]['other_colors'] = {'MT_Metal': colors}
            with self.assertRaisesRegex(ValueError, 'other_colors'):
                spec.validate(value)

    def test_glass_is_only_a_fallback_for_an_empty_opaque_channel(self):
        document = model.load(ROOT / 'formgen/models/mini.py')
        small = dict(document['parts'][0], role='anodized', f1=10, u1=10, w=10)
        large = dict(small, id='grip', role='glass', f1=100, u1=100, w=100)
        document['parts'] = [large, small]
        with (ROOT / 'skins.toml').open('rb') as stream:
            colors = tomllib.load(stream)['roles']
        palette = spec.build(geom.evaluate(document))['palette'][0]
        self.assertEqual(palette['channels']['MT_Detail'], colors['anodized']['color'].upper())
        self.assertNotIn('MT_Detail', palette['other_colors'])
        document['parts'] = [large]
        palette = spec.build(geom.evaluate(document))['palette'][0]
        self.assertEqual(palette['channels']['MT_Detail'], colors['glass']['color'].upper())
        self.assertNotIn('MT_Detail', palette['other_colors'])

    def test_prompts_grounded_in_shared_geometry(self):
        before = copy.deepcopy(self.w01)
        result = prompts.build(self.w01)
        self.assertIn('Oberes Gehäuse', result['de'])
        self.assertIn('Upper receiver', result['en'])
        self.assertIn('0.915000', result['en'])
        self.assertIn('Darstellungsvorgaben', result['de'])
        self.assertIn('presentation instructions', result['en'])
        self.assertEqual(result['warnings'], self.w01['warnings'])
        self.assertEqual(self.w01, before)
        for name in ('KG02', 'VS02'):
            imported = prompts.build(geo.load(ROOT / f'tests/fixtures/{name}.geo.json'))
            self.assertIsInstance(imported['de'], str)
            self.assertIsInstance(imported['en'], str)

    def test_nonfinite_measurements_rejected(self):
        d = copy.deepcopy(self.w01)
        d['parts'][0]['mesh']['vertices'][0][0] = float('nan')
        with self.assertRaisesRegex(ValueError, 'Netzkoordinaten'):
            spec.build(d)


if __name__ == '__main__':
    unittest.main()
