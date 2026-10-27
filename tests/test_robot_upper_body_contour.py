"""Shared front/back contour correction; analytical geometry, no image claim."""
from collections import Counter
import unittest

import numpy as np

from formgen import geom
from formgen.models.figures.r01_parts import upper_body as upper


def section_halfwidth(part, height):
    mesh = np.asarray(part['vertices'], float)
    values = []
    for face in part['faces']:
        for ia, ib in zip(face, face[1:]+face[:1]):
            a, b = mesh[ia], mesh[ib]
            if min(a[1], b[1]) <= height <= max(a[1], b[1]) and abs(b[1]-a[1]) > 1e-10:
                t = (height-a[1])/(b[1]-a[1])
                values.append(abs(a[2]+t*(b[2]-a[2])))
    return max(values)


class UpperBodyContourTests(unittest.TestCase):
    def test_shared_shoulder_crown_widens_middle_without_lower_lip_flare(self):
        for suffix in ('r', 'l'):
            cap = next(p for p in upper.PARTS if p['id'] == 'upper_body_shoulder_cap_'+suffix)
            # Common measured silhouette support, rounded in mm. These bounds
            # do not claim a rendered IoU or compensate with camera changes.
            self.assertTrue(338 <= section_halfwidth(cap, 1500) <= 346)
            self.assertTrue(352 <= section_halfwidth(cap, 1525) <= 359)
            self.assertTrue(353 <= section_halfwidth(cap, 1550) <= 360)
            self.assertTrue(325 <= section_halfwidth(cap, 1600) <= 334)
            v = np.asarray(cap['vertices'])
            radial = np.linalg.norm(v[:, :2]-[-26, 1546], axis=1)
            self.assertAlmostEqual(float(radial.min()), 48)
            self.assertAlmostEqual(float(radial.max()), 99)
            self.assertLessEqual(float(np.abs(v[:, 2]).min()), 185)
        self.assertEqual(upper.ANCHORS['Socket_Shoulder_R']['at'], [-26, 1546, -281])
        self.assertEqual(upper.ANCHORS['Socket_Shoulder_L']['at'], [-26, 1546, 281])
        self.assertEqual(upper.ANCHORS['Socket_Neck']['at'], [35, 1690, 0])

    def test_carrier_roof_follows_shared_contour_without_moving_attachment(self):
        for suffix in ('r', 'l'):
            carrier = next(p for p in upper.PARTS
                           if p['id'] == 'upper_body_shoulder_carrier_'+suffix)
            vertices = np.asarray(carrier['vertices'], float)
            # Fixed measured stations distinguish a raised medial roof and a
            # falling lateral roof from a translation of the whole carrier.
            for width, limits in ((80, (1638, 1645)), (110, (1640, 1646)),
                                  (170, (1615, 1622))):
                crossings = []
                for face in carrier['faces']:
                    for ia, ib in zip(face, face[1:]+face[:1]):
                        a, b = vertices[ia], vertices[ib]
                        xa, xb = abs(a[2]), abs(b[2])
                        if min(xa, xb) <= width <= max(xa, xb) and abs(xa-xb) > 1e-10:
                            t = (width-xa)/(xb-xa)
                            crossings.append(a[1]+t*(b[1]-a[1]))
                self.assertTrue(limits[0] <= max(crossings) <= limits[1])
            # The carrier still reaches its original lower connections and
            # has the same nominal f-wall, rather than gaining a solid fill.
            outer, inner = vertices[:6], vertices[6:]
            self.assertEqual(outer[:, 0].tolist(), [88, 68, 48, 45, 89, 103])
            self.assertEqual(np.abs(outer[:, 2]).tolist(), [65, 125, 176, 210, 175, 102])
            self.assertEqual(outer[3:, 1].tolist(), [1582, 1555, 1596])
            np.testing.assert_allclose(outer-inner, [[5, 0, 0]]*6)

    def test_abdomen_width_follows_common_contour_with_existing_side_depth(self):
        abdomen = next(p for p in upper.PARTS if p['id'] == 'upper_body_abdomen_core')
        for ring, expected in zip(abdomen['rings'], upper.ABDOMEN_ROWS):
            u, width, front, back = expected
            points = np.asarray(ring)
            self.assertTrue(np.all(points[:, 1] == u))
            self.assertAlmostEqual(float(np.abs(points[:, 2]).max()), width)
            self.assertAlmostEqual(float(points[:, 0].max()), front)
            self.assertAlmostEqual(float(points[:, 0].min()), back)
        self.assertEqual(upper.ABDOMEN_ROWS[0], (1190, 119, 126, -48))
        self.assertEqual(upper.ABDOMEN_ROWS[1], (1220, 126, 133, -52))
        # Existing side-profile stations stay unchanged; only width changes.
        self.assertEqual([tuple((u, front, back)) for u, _, front, back in upper.ABDOMEN_ROWS if u != 1220],
                         [(1190, 126, -48), (1245, 139, -56), (1306, 145, -64), (1344, 150, -65)])

    @unittest.skipIf(geom._manifold is None, 'manifold3d optional')
    def test_corrected_meshes_remain_closed_positive_manifold_with_no_null_faces(self):
        selected = [p for p in upper.PARTS if 'shoulder_cap_' in p['id'] or 'shoulder_carrier_' in p['id']
                    or p['id'] == 'upper_body_abdomen_core']
        for part in selected:
            v, f = geom._shape(part, [])
            triangles = geom._triangulate(v, f)
            edges = Counter(tuple(sorted((a, b))) for face in triangles
                            for a, b in zip(face, face[1:]+face[:1]))
            self.assertTrue(all(n == 2 for n in edges.values()), part['id'])
            array = np.asarray(v)[triangles]
            area2 = np.linalg.norm(np.cross(array[:, 1]-array[:, 0], array[:, 2]-array[:, 0]), axis=1)
            self.assertTrue(np.all(area2 > 1e-16), part['id'])
            self.assertGreater(geom._volume(v, f), 0, part['id'])
            self.assertEqual(str(geom._as_manifold(v, f).status()), 'Error.NoError', part['id'])
