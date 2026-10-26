"""Pure raster contracts plus opt-in pixel tests (run under ce lock gpu)."""
import os
import json
import io
import unittest

import numpy as np
from PIL import Image

from formgen import raster


def panel(x=0., role='shell', **extra):
    return dict(id=f'panel-{x}', role=role,
                mesh={'vertices': [[x, -.4, -.4], [x, .4, -.4], [x, .4, .4], [x, -.4, .4]],
                      'faces': [[0, 1, 2], [0, 2, 3]], 'hard': [True, True]}, **extra)


def doc(*parts):
    return {'parts': list(parts)}


class CameraMaterialTests(unittest.TestCase):
    def test_orthonormal_camera_and_aliases(self):
        for view in raster.VIEWS:
            basis = raster.camera(view)
            np.testing.assert_allclose(basis @ basis.T, np.eye(3), atol=1e-14)
            self.assertAlmostEqual(np.linalg.det(basis), 1)
        np.testing.assert_array_equal(raster.camera('rear'), raster.camera('back'))
        with self.assertRaises(ValueError):
            raster.camera('perspective')

    def test_units_orientation_and_camera_depth(self):
        p = raster.project([[0, 0, 0], [0, -1, 0], [0, 0, 1], [1, 0, 0]],
                           width=400, height=300, scale=100)
        np.testing.assert_allclose(p, [[200, 150, 0], [100, 150, 0], [200, 50, 0], [200, 150, 1]])
        front = raster.project([[0, -1, 0]], 'front', scale=100)
        self.assertEqual(front[0, 2], 1)

    def test_top_bottom_keep_weapon_length_horizontal(self):
        for view in ('top', 'bottom'):
            points = raster.project([[0, 0, 0], [0, -1, 0]], view, 400, 300, 100)
            np.testing.assert_array_equal(points[:, :2], [[200, 150], [100, 150]])
        weapon = panel()
        weapon['mesh']['vertices'] = [[x*.1, y*2, z*.25] for x, y, z in weapon['mesh']['vertices']]
        frame = raster.framing(doc(weapon), raster.ORTHOS, 960, 640)
        self.assertAlmostEqual(frame['scale'], 960*.84/1.6)

    def test_feature_groups_remove_warped_diagonal_and_keep_folds(self):
        mesh = panel()['mesh']
        mesh['vertices'][2][0] = .05
        self.assertEqual(len(set(raster._face_groups(mesh))), 1)
        mesh['vertices'][2][0] = 1.
        self.assertEqual(len(set(raster._face_groups(mesh))), 2)
        # Same mildly warped mesh exported as a triangle soup, no shared indices.
        source = panel()['mesh']
        source['vertices'][2][0] = .05
        soup = {'vertices': [source['vertices'][i] for face in source['faces'] for i in face],
                'faces': [[0, 1, 2], [3, 4, 5]], 'hard': [True, True]}
        self.assertEqual(len(set(raster._face_groups(soup))), 1)

    def test_common_framing_fits_all_views(self):
        d = doc(panel())
        f = raster.framing(d, raster.VIEWS, width=400, height=300)
        for view in raster.VIEWS:
            p = raster.project(d['parts'][0]['mesh']['vertices'], view, 400, 300, **f)
            self.assertTrue(np.all(p[:, :2] >= [32-1e-8, 24-1e-8]))
            self.assertTrue(np.all(p[:, :2] <= [368+1e-8, 276+1e-8]))
        self.assertEqual(f['center'], [0., 0., 0.])
        with self.assertRaises(ValueError):
            raster.project([[0, 0, 0]], scale=0)
        with self.assertRaises(ValueError):
            raster.framing(doc({'id': 'raw'}))

    def test_material_toml_import_and_unlit(self):
        standard = raster.material({'role': 'shell'})
        night = raster.material({'role': 'shell'}, 'nacht')
        self.assertFalse(np.array_equal(standard['rgb'], night['rgb']))
        self.assertTrue(raster.material({'role': 'energy'})['unlit'])
        self.assertLess(raster.material({'role': 'glass'})['alpha'], 1)
        np.testing.assert_array_equal(raster.material({'role': 'v1', 'color': '#123456'})['rgb'], [18, 52, 86])
        with self.assertRaises(ValueError):
            raster.material({'role': 'typo'})

    def test_object_texture_is_camera_independent_and_energy_unshaded(self):
        positions = np.array([[.01, .03, .04], [.02, -.01, .13]])
        m = raster.material({'role': 'shell'}, 'tarnung')
        np.testing.assert_array_equal(raster._shade(m, [1, 0, 0], positions),
                                      raster._shade(m, [1, 0, 0], positions))
        energy = raster.material({'role': 'energy'})
        for normal in ([1, 0, 0], [0, 0, -1]):
            np.testing.assert_array_equal(raster._shade(energy, normal, positions),
                                          np.broadcast_to(energy['rgb'], positions.shape))

    def test_concave_face_preserves_area(self):
        vertices = np.array([[0, 0, 0], [0, 2, 0], [0, 2, 1], [0, 1, 1], [0, 1, 2], [0, 0, 2]])
        triangles = raster._triangles(vertices, list(range(6)))
        area = sum(np.linalg.norm(np.cross(vertices[t[1]]-vertices[t[0]], vertices[t[2]]-vertices[t[0]]))/2
                   for t in triangles)
        self.assertAlmostEqual(area, 3)


@unittest.skipUnless(os.environ.get('FORMGEN_RENDER_TESTS') == '1', 'Pixeltests nur mit FORMGEN_RENDER_TESTS=1 unter GPU-Lock')
class PixelTests(unittest.TestCase):
    def render(self, *parts, **kwargs):
        return raster.render(doc(*parts), width=80, height=80, scale=75, center=[0, 0, 0], **kwargs)

    def test_zbuffer_ignores_submission_order_and_shared_triangle_seam(self):
        far = panel(0, color='#FF0000', emissive=True)
        near = panel(.1, color='#00FF00', emissive=True)
        a = self.render(far, near)
        b = self.render(near, far)
        np.testing.assert_array_equal(a, b)
        # Diagonal between coplanar mesh triangles is not a drawn contour.
        np.testing.assert_array_equal(np.asarray(a)[40, 40], [0, 255, 0, 255])
        self.assertEqual(a.info['supersampling'], 2)
        self.assertEqual(a.info['framing']['scale'], 75)

    def test_warped_quad_does_not_draw_triangulation_diagonal(self):
        warped = panel(color='#D8CCB4', emissive=True)
        warped['mesh']['vertices'][2][0] = .05
        image = np.asarray(self.render(warped))
        np.testing.assert_array_equal(image[40, 40], [216, 204, 180, 255])
        sharp = panel(color='#D8CCB4', emissive=True)
        sharp['mesh']['vertices'][2][0] = 1.
        crease = np.asarray(self.render(sharp))
        # The crease x+y=80 straddles output pixels: [40,40] has only one
        # covered subpixel of four. Compare its actual antialiased profile to
        # the analytical two-sample boundary, rather than require every sample
        # near the diagonal to be darker than a fully covered line pixel.
        size = 80*raster.SS
        expected = np.broadcast_to(image[40, 40], (size, size, 4)).copy()
        yy, xx = np.indices((size, size))
        line = (xx+yy == size-1) | (xx+yy == size)
        expected[line, :3] = raster._rgb(raster.palette()['render']['outline'])
        expected = np.asarray(Image.fromarray(expected).resize((80, 80), Image.Resampling.LANCZOS))
        np.testing.assert_array_equal(crease[35:45, 35:45], expected[35:45, 35:45])
        self.assertLess(crease[40, 39, :3].mean(), image[40, 39, :3].mean()/2)
        np.testing.assert_array_equal(crease[30, 40], image[30, 40])

    def test_coverage_matches_samples_and_serializes_separately(self):
        part = panel(emissive=True)
        # Fractional screen boundary gives half-covered output pixels.
        part['mesh']['vertices'] = [[x, y+1/150, z] for x, y, z in part['mesh']['vertices']]
        image = self.render(part, bg='#D8CCB4')
        mask = image.coverage_mask
        self.assertEqual(mask.mode, 'L')
        self.assertEqual(mask.size, image.size)
        expected = np.zeros((80, 80), dtype=np.uint8)
        expected[10:70, 11:70] = 255
        expected[10:70, [10, 70]] = 128
        np.testing.assert_array_equal(mask, expected)
        # Background and glass opacity do not change geometric occupancy.
        glass = dict(part, role='glass', alpha=.1)
        transparent = self.render(glass, bg='transparent')
        np.testing.assert_array_equal(mask, transparent.coverage_mask)
        self.assertLess(np.asarray(transparent)[40, 40, 3], 255)
        hidden = panel(-.1, alpha=0.)
        np.testing.assert_array_equal(mask, self.render(hidden, part).coverage_mask)
        payload = io.BytesIO()
        mask.save(payload, format='PNG')
        payload.seek(0)
        np.testing.assert_array_equal(Image.open(payload), expected)
        payload = io.BytesIO()
        image.save(payload, format='PNG')
        json.dumps(image.info, sort_keys=True)

    def test_glass_blends_over_background_and_opaque_occludes_glass(self):
        glass = panel(.1, role='glass', color='#FFFFFF', alpha=.5, emissive=True)
        a = np.asarray(self.render(glass, bg='#000000'))
        np.testing.assert_allclose(a[40, 40, :3], [127, 127, 127], atol=1)
        opaque = panel(.2, color='#FF0000', emissive=True)
        b = np.asarray(self.render(opaque, glass))
        np.testing.assert_array_equal(b[40, 40], [255, 0, 0, 255])

    def test_transparency_order_and_no_bloom(self):
        red = panel(.1, role='glass', color='#FF0000', alpha=.5, emissive=True)
        green = panel(.2, role='glass', color='#00FF00', alpha=.5, emissive=True)
        a = self.render(red, green, bg='#000000')
        b = self.render(green, red, bg='#000000')
        np.testing.assert_array_equal(a, b)
        np.testing.assert_allclose(np.asarray(a)[40, 40, :3], [63, 127, 0], atol=1)
        lit = np.asarray(self.render(panel(role='energy'), bg='transparent'))
        unlit = np.asarray(self.render(panel(role='shell'), bg='transparent'))
        np.testing.assert_array_equal(lit[..., 3], unlit[..., 3])
        self.assertFalse(lit[:5, :, 3].any())

    def test_null_label_metadata_uses_id_and_serializes(self):
        image = self.render(panel(label=None))
        self.assertIn('panel-0.0', image.info['anchors'])
        self.assertIn('panel-0.0', image.info['boxes'])
        json.dumps(image.info, sort_keys=True)

    def test_dark_internal_contour_has_contrast_but_silhouette_stays_dark(self):
        base = panel(color='#202020', emissive=True)
        raised = panel(.1, color='#202020', emissive=True)
        raised['mesh']['vertices'] = [[x, y*.5, z*.5] for x, y, z in raised['mesh']['vertices']]
        a = np.asarray(self.render(base, raised))
        # Raised panel boundary around x=25 is lighter than the dark material;
        # the outer silhouette around x=10 remains darker than that boundary.
        self.assertGreater(a[40, 25, :3].mean(), a[40, 40, :3].mean())
        self.assertLess(a[40, 10, :3].mean(), a[40, 25, :3].mean())

    def test_label_anchor_lies_on_visible_part(self):
        image = self.render(panel(label='Schale'))
        x, y = image.info['anchors']['Schale']
        self.assertTrue(10 < x < 70 and 10 < y < 70)
        self.assertIn('Schale', image.info['boxes'])


if __name__ == '__main__':
    unittest.main()
