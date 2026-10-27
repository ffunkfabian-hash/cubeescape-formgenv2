"""Imported surface pixel contracts; opt in under the shared GPU lock."""
from copy import deepcopy
import os
import unittest

import numpy as np

from formgen import raster


def panel(name='body', x=0., color='#909090', extent=.4):
    return dict(id=name, role='shell', color=color, mesh=dict(
        vertices=[[x, -.4, -extent], [x, .4, -extent],
                  [x, .4, extent], [x, -.4, extent]], faces=[[0, 1, 2, 3]], hard=True))


def decal(parent='body', x=.001, normal=(1, 0, 0), color='#FF0000', extent=.2):
    return dict(part=parent, polygon_m=[[x, -extent, -extent], [x, extent, -extent],
                                      [x, extent, extent], [x, -extent, extent]],
                normal=list(normal), color=color, emissive=True)


def document(*parts, decals=(), layers=(), colors=None):
    return dict(parts=list(parts or [panel()]), decals=list(decals),
                source_geo=dict(format='cubeescape-design/geometry-spec'),
                source_spec=dict(skin=dict(hero='test', items=[dict(
                    id='test', layers=list(layers), colors=dict(base=colors or {}))])))


@unittest.skipUnless(os.environ.get('FORMGEN_RENDER_TESTS') == '1',
                     'Pixeltests nur unter GPU-Lock mit FORMGEN_RENDER_TESTS=1')
class LegacyRasterTests(unittest.TestCase):
    def render(self, value, **kwargs):
        return raster.render(value, width=80, height=80, scale=75,
                             center=[0, 0, 0], **kwargs)

    def test_resolved_orange_band_on_both_sides(self):
        layer = dict(type='bands', parts=['body'], dir=[0, 0, 1], t0_m=-.1,
                     width_m=.2, period_m=1, count=1, slots=['accent'])
        d = document(layers=[layer], colors=dict(accent=dict(color='#E8661C', finish='paint')))
        plain = document()
        for view in ('side_left', 'side_right'):
            actual = self.render(d, view=view)
            baseline = self.render(plain, view=view)
            center = np.asarray(actual)[40, 40, :3]
            self.assertGreater(int(center[0]), int(center[1])*2)
            self.assertGreater(int(center[1]), int(center[2])*2)
            np.testing.assert_array_equal(actual.coverage_mask, baseline.coverage_mask)
            np.testing.assert_array_equal(np.asarray(actual)[20, 40], np.asarray(baseline)[20, 40])

    def test_decal_preserves_coverage_boxes_and_has_no_geometry_outline(self):
        original = document()
        value = document(decals=[decal(extent=.6)])
        before = deepcopy(value)
        plain, decorated = self.render(original), self.render(value)
        np.testing.assert_array_equal(plain.coverage_mask, decorated.coverage_mask)
        self.assertEqual(plain.info['boxes'], decorated.info['boxes'])
        self.assertIn('body', decorated.info['anchors'])
        np.testing.assert_array_equal(np.asarray(decorated)[40, 40], [255, 0, 0, 255])
        self.assertEqual(value, before)
        smaller = self.render(document(decals=[decal()]))
        # An interior decal edge has red on one side and parent tone on the
        # other; it must not acquire the renderer's near-black geometry line.
        pixels = np.asarray(smaller)[40, 23:57, :3]
        self.assertTrue(np.all(np.max(pixels, axis=1) > 50))

    def test_parent_ownership_rejects_other_foreground_in_either_order(self):
        body, cover = panel(), panel('cover', x=.1, color='#00FF00')
        for parts in ((body, cover), (cover, body)):
            plain = self.render(document(*parts))
            actual = self.render(document(*parts, decals=[decal(x=.2)]))
            np.testing.assert_array_equal(actual, plain)

    def test_parent_depth_rejects_buried_decal(self):
        plain = self.render(document())
        buried = self.render(document(decals=[decal(x=-.01)]))
        np.testing.assert_array_equal(buried, plain)

    def test_normals_reject_backside_and_unrelated_parent_face(self):
        plain = self.render(document())
        backwards = self.render(document(decals=[decal(normal=(-1, 0, 0))]))
        np.testing.assert_array_equal(backwards, plain)
        # Positive camera dot alone is insufficient: this normal points
        # almost along the parent, rather than out of its visible surface.
        tangent = self.render(document(decals=[decal(normal=(.1, 0, .995))]))
        np.testing.assert_array_equal(tangent, plain)
        oblique = self.render(document(decals=[decal(normal=(.6, 0, .8))]))
        np.testing.assert_array_equal(np.asarray(oblique)[40, 40], [255, 0, 0, 255])

    def test_ordered_overlays_can_cover_previous_decal_of_same_parent(self):
        value = document(decals=[decal(color='#FF0000'), decal(color='#0000FF')])
        actual = self.render(value)
        np.testing.assert_array_equal(np.asarray(actual)[40, 40], [0, 0, 255, 255])

    def test_glyph_surface_normal_selects_each_side_and_explicit_skin(self):
        parts = [panel(x=.05), panel('backface', x=-.05)]
        colors = dict(left=dict(color='#6CF2FF', finish='neon'),
                      right=dict(color='#FF4060', finish='neon'))
        left = decal(x=.05004)['polygon_m']
        right = decal(x=-.05004)['polygon_m']
        layers = [dict(type='glyphs', part='body', decals=[dict(
            surface='left', points_m=left, slot='left')]),
            dict(type='glyphs', part='backface', decals=[dict(
                surface='right', points_m=right, slot='right')])]
        value = document(*parts, layers=layers, colors=colors)
        for view in ('side_left', 'side_right'):
            actual = self.render(value, view=view, skin='legacy:test')
            center = np.asarray(actual)[40, 40, :3]
            if view == 'side_left':
                self.assertGreater(int(center[1]), 240)
                self.assertEqual(int(center[2]), 255)
                self.assertLess(int(center[0]), 180)
            else:
                self.assertEqual(int(center[0]), 255)
                self.assertLess(int(center[1]), 150)
                self.assertLess(int(center[2]), 180)
        self.assertEqual(value['parts'], parts)

    def test_wear_does_not_turn_flat_decal_boundary_into_metal(self):
        value = document(decals=[decal()])
        plain = self.render(value)
        value['source_spec']['skin']['items'][0]['layers'] = [dict(
            type='edge_wear', parts=['body'], width_mm=20, coverage=1, color='#FFFFFF')]
        worn = self.render(value)
        # The real outer rim is 15 output pixels farther away. Only the
        # interior decal boundary is present in this central comparison.
        np.testing.assert_array_equal(np.asarray(worn)[25:55, 25:55],
                                      np.asarray(plain)[25:55, 25:55])
