"""Head contracts and shell geometry; visual Ortho acceptance is separate."""
import json
import unittest
from collections import Counter

import numpy as np
from scipy.spatial import ConvexHull

from formgen import geom
from formgen.models.figures.r01_parts import head


class RobotHeadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = geom.evaluate(dict(
            info=dict(id='HEAD',kind='figure',name_de='Kopf',provenance=head.PROVENANCE),
            parts=head.PARTS,assemblies=[dict(id='head',de='Kopf')],anchors=head.ANCHORS))
        cls.parts = {p['id']: p for p in cls.document['parts']}

    def test_closed_positive_finite_meshes(self):
        json.dumps(self.document,allow_nan=False)
        self.assertFalse(self.document['warnings'])
        for name, part in self.parts.items():
            mesh = part['mesh']
            edges = Counter(tuple(sorted((a,b))) for face in mesh['faces']
                            for a,b in zip(face,face[1:]+face[:1]))
            self.assertTrue(all(n==2 for n in edges.values()),name)
            self.assertGreater(geom._volume(mesh['vertices'],mesh['faces']),0,name)

    def test_dimensions_shared_anchor_and_collar_overlap(self):
        lo,hi = np.asarray(self.document['bounds_m'])*1000
        self.assertAlmostEqual(hi[2],1924)
        self.assertAlmostEqual(lo[2],1598)
        self.assertAlmostEqual(hi[0]-lo[0],274)
        self.assertLessEqual(hi[1]-lo[1],275)
        self.assertEqual(head.ANCHORS['Socket_Neck']['at'],[35,1690,0])
        neck = np.asarray(self.parts['head_neck_core']['mesh']['vertices'])*1000
        self.assertLessEqual(neck[:,2].min(),1598)
        self.assertGreater(neck[:,2].max(),1690)
        self.assertGreaterEqual(neck[:,0].max(),60)

    def test_real_shells_and_separate_face(self):
        for name in ['head_face_mask','head_rear_housing','head_crown_shell_l',
                     'head_crown_shell_r','head_ear_shell_l','head_ear_shell_r']:
            part = self.parts[name]
            mesh = part['mesh']
            volume = geom._volume(mesh['vertices'],mesh['faces'])
            envelope = ConvexHull(mesh['vertices']).volume
            self.assertLess(volume,envelope*.45,name)
            self.assertEqual(part['wall_mm'],4)
        self.assertEqual(self.parts['head_face_mask']['role'],'graphite')
        self.assertEqual(self.parts['head_occipital_shell']['role'],'shell')

    def test_symmetry_and_single_emitter(self):
        self.assertEqual([p['id'] for p in head.PARTS if p['role']=='energy'],['head_visor'])
        for name, part in self.parts.items():
            if not name.endswith('_l'):
                continue
            left = np.asarray(part['mesh']['vertices']).copy()
            left[:,0] *= -1
            right = np.asarray(self.parts[name[:-1]+'r']['mesh']['vertices'])
            self.assertEqual({tuple(np.round(v,10)) for v in left},
                             {tuple(np.round(v,10)) for v in right},name)
            if 'ear_joint' in name or 'ear_hub' in name or 'neck_strut' in name:
                self.assertIn(part['role'],['dark_metal','anodized'])


if __name__ == '__main__':
    unittest.main()
