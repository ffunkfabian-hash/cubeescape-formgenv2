"""Pure mesh validation, not a claim of visual Ortho acceptance."""
import json
import unittest
from collections import Counter

import numpy as np
from scipy.spatial import ConvexHull

from formgen import geom
from formgen.models.figures.r01_parts import upper_body as upper


class UpperBodyGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = geom.evaluate(dict(
            info=dict(id='UPPER', kind='figure', name_de='Oberkörper', provenance=upper.PROVENANCE),
            parts=upper.PARTS, assemblies=[dict(id='upper_body', de='Oberkörper')],
            anchors=upper.ANCHORS))

    def test_closed_positive_meshes_and_hollow_main_shells(self):
        json.dumps(self.document, allow_nan=False)
        self.assertFalse(self.document['warnings'])
        for part in self.document['parts']:
            mesh = part['mesh']
            edges = Counter(tuple(sorted((a, b))) for face in mesh['faces']
                            for a, b in zip(face, face[1:]+face[:1]))
            self.assertTrue(all(n == 2 for n in edges.values()), part['id'])
            volume = geom._volume(mesh['vertices'], mesh['faces'])
            self.assertGreater(volume, 0, part['id'])
            if any(name in part['id'] for name in ('breastplate', 'backplate', 'shoulder_cap')):
                envelope = ConvexHull(mesh['vertices']).volume
                self.assertLess(volume, envelope*.35, part['id'])

    def test_mirrored_shells_and_nonemissive_roles(self):
        parts = {part['id']: part for part in self.document['parts']}
        for key, part in parts.items():
            self.assertNotIn(part['role'], ('energy', 'glass'), key)
            if key.endswith('_r'):
                right = np.asarray(part['mesh']['vertices']).copy()
                left_part = parts[key[:-1]+'l']
                left = np.asarray(left_part['mesh']['vertices'])
                right[:, 0] *= -1
                self.assertEqual({tuple(v) for v in right}, {tuple(v) for v in left}, key)
                self.assertAlmostEqual(geom._volume(part['mesh']['vertices'], part['mesh']['faces']),
                                       geom._volume(left_part['mesh']['vertices'], left_part['mesh']['faces']), places=10)
        self.assertEqual(upper.ANCHORS['Socket_Neck']['at'], [35, 1690, 0])
        for side, sign in [('R', -1), ('L', 1)]:
            self.assertEqual(upper.ANCHORS['Socket_Shoulder_'+side]['at'], [-26, 1546, sign*281])

    def test_shoulder_caps_leave_joint_and_lower_opening_free(self):
        for part in upper.PARTS:
            if 'shoulder_cap' not in part['id']:
                continue
            vertices = np.asarray(part['vertices'])
            radial = np.linalg.norm(vertices[:, :2]-[-26, 1546], axis=1)
            # The outer white flange surrounds a 48mm open bearing. Neither
            # that flange nor the barrel may turn into a disk over the joint.
            self.assertAlmostEqual(radial.min(), 48)
            self.assertAlmostEqual(radial.max(), 99)
            self.assertGreater(vertices[:, 1].min(), 1470)
            self.assertEqual(part['wall_mm'], 6)

    def test_shoulder_coupling_bridges_shells_without_closing_bearing(self):
        parts = {p['id']: p for p in upper.PARTS}
        for suffix, sign in [('r', -1), ('l', 1)]:
            coupling = parts['upper_body_shoulder_coupling_'+suffix]
            self.assertEqual(coupling['c'], [-26, 1546])
            self.assertGreater(coupling['r_in'], 70)
            self.assertLess(coupling['r'], 99)
            vertices = np.asarray(parts['upper_body_shoulder_cap_'+suffix]['vertices'])
            # Front references show the cap overlapping the torso coupling;
            # the former x237 inner edge left a visible daylight gap.
            self.assertLessEqual((sign*vertices[:, 2]).min(), 185)
            self.assertLess(vertices[:, 1].max(), 1646)
