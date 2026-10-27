"""Analytical imported surface contracts; no image production in this file."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

import numpy as np

from formgen import build, geo, legacy_surface

FIXTURES = Path(__file__).parent/'fixtures'
TOON = np.array([.72, .82, .92, 1.])


def kg02():
    document = geo.normalize(json.loads((FIXTURES/'KG02.geo.json').read_text()))
    document['source_spec'] = json.loads((FIXTURES/'KG02.spec.json').read_text())
    return document


class LegacySurfaceTests(unittest.TestCase):
    def setUp(self):
        self.document = kg02()
        self.surface = legacy_surface.resolve(self.document)

    def test_native_path_is_absent_and_resolved_hero_uses_original_base_palette(self):
        self.assertIsNone(legacy_surface.resolve({'parts': []}))
        self.assertEqual(self.surface.recipe['id'], 'glyphenband')
        color, finish = self.surface.slot('MT_Accent')
        np.testing.assert_array_equal(color, [232, 102, 28])
        self.assertEqual(finish, 'paint')
        self.assertEqual(legacy_surface.resolve(self.document, 'legacy:goldglyphe').recipe['id'], 'goldglyphe')
        with self.assertRaisesRegex(ValueError, 'Legacy-Skin'):
            legacy_surface.resolve(self.document, 'legacy:does-not-exist')

    def test_real_hero_has_63_imported_decals_and_44_resolved_glyphs_without_mutation(self):
        original = deepcopy(self.document)
        decorations = self.surface.decorations()
        self.assertEqual(len(decorations), 107)
        glyphs = [p for p in decorations if '/legacy-glyph/' in p['id']]
        self.assertEqual(len(glyphs), 44)
        self.assertTrue(all(p['emissive'] and p['color'] == '#6CF2FF' for p in glyphs))
        self.assertEqual({tuple(p['_decal_normal']) for p in glyphs}, {(1, 0, 0), (-1, 0, 0)})
        self.assertTrue(all(p['_surface_parent'] in self.surface.parts for p in decorations))
        self.assertEqual(self.document, original)

    def test_decal_depth_ownership_includes_previous_decals_but_not_other_parts(self):
        parts = self.surface.render_parts()
        parents = self.surface.parents(parts)
        decoration = parts[len(self.document['parts'])]
        owner = next(i for i, p in enumerate(parts) if p['id'] == decoration['_surface_parent'])
        other = next(i for i, p in enumerate(parts) if not p.get('_surface_parent') and i != owner)
        already_decorated = next(i for i, p in enumerate(parts) if p is decoration)
        visible = np.array([owner, other, -1, already_decorated])
        np.testing.assert_array_equal(self.surface.parent_visible(decoration, visible, parents, parts),
                                      [True, False, False, True])

    def test_detail_selection_drops_decorations_of_absent_parents_and_keeps_physical_scale(self):
        selected = build.select_document(self.document, 'detail_trigger')
        ids = {p['id'] for p in selected['parts']}
        self.assertLess(len(ids), len(self.document['parts']))
        for skin in ('standard', 'legacy:goldglyphe'):
            surface = legacy_surface.resolve(selected, skin)
            rendered = surface.render_parts()
            surface.parents(rendered)
            self.assertEqual(surface.height, self.surface.height)
            for decoration in rendered[len(selected['parts']):]:
                self.assertIn(decoration.get('_surface_parent') or decoration['_surface_attach'], ids)

    def test_real_orange_band_is_in_metres_and_restricted_to_resolved_parts(self):
        part = self.surface.parts['p09']
        points = np.array([[.03, -.1, .10], [.03, -.1, .15]])
        colors = self.surface.shade(part, [217, 203, 176], [1, 0, 0], points, 3, TOON)
        np.testing.assert_array_equal(colors[0], [232, 102, 28])
        self.assertFalse(np.array_equal(colors[1], colors[0]))
        wrong = deepcopy(part); wrong['id'] = 'unselected'
        other = self.surface.shade(wrong, [217, 203, 176], [1, 0, 0], points, 3, TOON)
        self.assertFalse(np.array_equal(colors[0], other[0]))

    def test_all_resolved_color_layer_families_at_known_world_points(self):
        part = self.surface.parts['p09']; part = dict(part, texture=None, toolgen_material=None)
        self.surface.colors = {'a': dict(color='#FF0000', finish='paint'),
                               'b': dict(color='#0000FF', finish='paint')}
        points = np.array([[0, .25, .25], [0, 1.25, .25], [0, 2.25, .25]])
        def sample(layer):
            self.surface.layers = [dict(parts=['p09'], **layer)]
            return self.surface.shade(part, [10, 10, 10], [1, 0, 0], points, 3, TOON)
        colors = sample(dict(type='side_block', slot='a', poly_yz_m=[[0, 0], [1, 0], [1, 1], [0, 1]]))
        np.testing.assert_array_equal(colors, [[255, 0, 0], [10, 10, 10], [10, 10, 10]])
        colors = sample(dict(type='bands', dir=[0, 1, 0], t0_m=0, width_m=.5, period_m=1, count=2, slots=['a', 'b']))
        np.testing.assert_array_equal(colors, [[255, 0, 0], [0, 0, 255], [10, 10, 10]])
        colors = sample(dict(type='gradient', dir=[0, 1, 0], t0_m=0, t1_m=2.5, steps=3, slots=['a', 'b']))
        np.testing.assert_array_equal(colors, [[255, 0, 0], [127.5, 0, 127.5], [0, 0, 255]])
        colors = sample(dict(type='rings', center_yz_m=[0, .25], r0_m=0, width_m=.5, gap_m=.5, count=2, slots=['a', 'b']))
        np.testing.assert_array_equal(colors, [[255, 0, 0], [0, 0, 255], [10, 10, 10]])

    def test_neon_is_unshaded_and_chrome_has_object_space_streak(self):
        points = np.array([[0, 0, 0], [0, 0, self.surface.height*.21]])
        for level in range(4):
            neon = self.surface.tones([108, 242, 255], 'neon', level, points, TOON)
            np.testing.assert_array_equal(neon, [[144.75, 245.25, 255]]*2)
        chrome = self.surface.tones([201, 210, 220], 'polished_chrome', 2, points, TOON)
        np.testing.assert_array_equal(chrome[0], [255, 255, 255])
        self.assertFalse(np.array_equal(chrome[0], chrome[1]))

    def test_imported_emissive_decal_preserves_unlit_color_without_skin_finish(self):
        part = dict(id='lamp-decal', _legacy_finish='paint', emissive=True)
        positions = np.array([[.01, .02, .03], [.02, .03, .04]])
        for level in range(4):
            actual = self.surface.shade(part,[123,145,167],[1,0,0],positions,level,TOON)
            np.testing.assert_array_equal(actual,[[123,145,167]]*2)

    def test_trim_spec_contains_renderable_prisms_without_model_construction(self):
        surface = legacy_surface.resolve(self.document, 'legacy:goldglyphe')
        trims = [p for p in surface.decorations() if '/legacy-trim/' in p['id']]
        self.assertEqual(len(trims), 3)
        for trim in trims:
            vertices = np.asarray(trim['mesh']['vertices'])
            self.assertEqual(len(vertices), 8)
            self.assertTrue(np.all(np.ptp(vertices, axis=0) > 0))
            self.assertEqual(len(trim['mesh']['faces']), 6)

    def test_wear_responds_to_geometry_edges_and_never_to_decal_edges(self):
        shape = (16, 16)
        colors = np.zeros((*shape, 3))
        positions = np.zeros((*shape, 3)); positions[..., 2] = np.arange(16)[:, None]*.002
        geometry = np.zeros(shape, int); geometry[:, 8:] = 1
        parts = np.zeros(shape, int)
        render_parts = [dict(id='body'), dict(id='decal', _surface_parent='body')]
        self.surface.layers = [dict(type='edge_wear', parts=['body'], width_mm=5, coverage=1., color='#9AA2AC')]
        worn = self.surface.wear(colors, geometry, parts, positions, np.zeros(shape, int), render_parts, 1000, TOON)
        self.assertTrue(np.any(worn > 0))
        parts[:, 8:] = 1
        decal_only = self.surface.wear(colors, geometry, parts, positions, np.zeros(shape, int), render_parts, 1000, TOON)
        np.testing.assert_array_equal(decal_only, colors)

    def test_material_patterns_have_physical_scale_and_part_axis(self):
        points = np.array([[0, 0, .001], [.002, -.003, .004]])
        part = dict(self.surface.parts['p09'], texture='brushed')
        a = self.surface._material_pattern(part, points, [1, 0, 0])
        axis = np.argmax(np.ptp(np.asarray(part['mesh']['vertices']), axis=0))
        shifted = points.copy(); shifted[:, axis] += .1
        np.testing.assert_allclose(a, self.surface._material_pattern(part, shifted, [1, 0, 0]))
        rubber = dict(part, texture='rubber')
        values = self.surface._material_pattern(rubber, np.array([[0, 0, 0], [0, .002, .002]]), [1, 0, 0])
        np.testing.assert_allclose(values, [.66, 1.], atol=1e-14)

    def test_brushed_transverse_phase_matches_original_axes_for_x_and_z_long_parts(self):
        points = np.array([[.001, .002, .003], [.004, -.005, .006]])
        p = next(p for p in self.surface._catalog['patterns'] if p['id']=='brushed')['params']
        for axis, across in [(0, points[:, 2]-points[:, 1]),
                             (2, points[:, 0]-points[:, 1])]:
            vertices = [[0, 0, 0], [1 if i==axis else .01 for i in range(3)]]
            part = dict(texture='brushed', mesh=dict(vertices=vertices))
            expected = 1+p['amplitude']*sum(w['weight']*np.sin(2*np.pi*1000*across/w['wavelength_mm']+w['phase']) for w in p['waves'])
            np.testing.assert_allclose(self.surface._material_pattern(part, points, [1, 0, 0]),expected,atol=1e-14)

    def test_knurl_matches_original_normal_axis_and_negative_length_coordinate(self):
        points = np.array([[.001, .002, .003], [.004, -.005, .006]])
        pattern = next(p for p in self.surface._catalog['patterns'] if p['id']=='knurl')
        original = [-points[:, 1]*1000, points[:, 2]*1000, points[:, 0]*1000]
        for normal, u, v in [([1, 0, 0], original[0], original[1]),
                             ([0, 1, 0], original[1], original[2]),
                             ([0, 0, 1], original[0], original[2])]:
            expected = 1-pattern['params']['darkening']*((np.floor((u+v)/pattern['size_mm'])%2==0)&(np.floor((u-v)/pattern['size_mm'])%2==0))
            actual = self.surface._material_pattern(dict(texture='rubber'),points,normal)
            np.testing.assert_allclose(actual,expected,atol=1e-14)

    def test_brushed_equal_extent_keeps_original_length_axis_priority(self):
        points = np.array([[.001, .002, .003], [.004, -.005, .006]])
        part = dict(texture='brushed', mesh=dict(vertices=[[0, 0, 0], [1, 1, 1]]))
        p = next(p for p in self.surface._catalog['patterns'] if p['id']=='brushed')['params']
        # v1 chooses its length (-worldY) before height (Z) and width (X).
        across = (points[:, 0]+points[:, 2])*1000
        expected = 1+p['amplitude']*sum(w['weight']*np.sin(2*np.pi*across/w['wavelength_mm']+w['phase']) for w in p['waves'])
        np.testing.assert_allclose(self.surface._material_pattern(part, points, [1, 0, 0]),expected,atol=1e-14)


if __name__ == '__main__':
    unittest.main()
