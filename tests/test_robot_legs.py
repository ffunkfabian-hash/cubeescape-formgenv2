"""Pure geometry checks for the leg assembly; no visual acceptance claim."""
import json
import unittest
from collections import Counter

import numpy as np
from scipy.spatial import ConvexHull

from formgen import geom
from formgen.models.figures.r01_parts import legs


class RobotLegGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = geom.evaluate(dict(
            info=dict(id='R01_LEGS',kind='figure',name_de='Beine',provenance=legs.PROVENANCE),
            parts=legs.PARTS,assemblies=[dict(id='legs',de='Beine')],anchors=legs.ANCHORS))

    def test_closed_positive_shells_and_export(self):
        json.dumps(self.document,allow_nan=False)
        self.assertFalse(self.document['warnings'])
        for p in self.document['parts']:
            mesh=p['mesh']
            edge=Counter(tuple(sorted((a,b))) for face in mesh['faces']
                         for a,b in zip(face,face[1:]+face[:1]))
            self.assertTrue(all(n==2 for n in edge.values()),p['id'])
            v=geom._volume(mesh['vertices'],mesh['faces'])
            self.assertGreater(v,0,p['id'])
            if 'wall_mm' in p:
                # A shell must leave substantial interior volume; a solid
                # loft painted cream does not satisfy the shell contract.
                envelope=ConvexHull(np.array(mesh['vertices'])).volume
                self.assertLess(v,envelope*.35,p['id'])

    def test_symmetry_ground_and_nonemissive_joints(self):
        parts={p['id']:p for p in self.document['parts']}
        for key,p in parts.items():
            if key.endswith('_r'):
                r=np.array(p['mesh']['vertices']); l=np.array(parts[key[:-1]+'l']['mesh']['vertices'])
                r[:,0]*=-1
                # Boolean triangulation may reorder vertices.
                self.assertEqual({tuple(np.round(v,9)) for v in r},
                                 {tuple(np.round(v,9)) for v in l},key)
            if 'ring' in key or 'disc' in key:
                self.assertIn(p['role'],('dark_metal','anodized'))
        self.assertAlmostEqual(self.document['bounds_m'][0][2],0)
        for side in ('R','L'):
            self.assertEqual(legs.ANCHORS['Socket_Knee_'+side]['at'][1],710)
            self.assertEqual(legs.ANCHORS['Socket_Ankle_'+side]['at'][1],234)

    def test_hidden_cores_do_not_pierce_shell_walls(self):
        # The former independent octagons cut 118,000..281,000 mm³ out
        # of each thigh wall and made dark stripes across the cream skin.
        # Check real mesh intersection, including the foot and link ends;
        # matching only profile extrema misses the folded cheek surfaces.
        meshes={p['id']:p['mesh'] for p in self.document['parts']}
        def solid(key):
            mesh=meshes['legs_'+key]
            return geom._as_manifold(mesh['vertices'],mesh['faces'])
        for side in ('r','l'):
            for limb, panels in (('thigh',('front','rear')),
                                 ('shin',('front','rear')),
                                 ('foot',('toe','heel'))):
                for panel in panels:
                    name=f'{limb}_{panel}_shell_{side}'
                    overlap=solid(f'{limb}_core_{side}') ^ solid(name)
                    # Manifold uses float32 metre coordinates. At foot
                    # folds its residual is <0.05 mm³; permit 1 mm³.
                    self.assertLess(abs(overlap.volume()),1e-9,name)
            for link, limb, panels in (('knee_lower_link','shin',('front','rear')),
                                       ('ankle_link','foot',('toe','heel'))):
                for panel in panels:
                    overlap=solid(f'{link}_{side}') ^ solid(f'{limb}_{panel}_shell_{side}')
                    self.assertLess(abs(overlap.volume()),1e-9,f'{link}_{side}/{panel}')
