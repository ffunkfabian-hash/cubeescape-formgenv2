"""Geometry/provenance checks only; image acceptance remains an integration job."""
import hashlib
import json
from pathlib import Path
import unittest
from collections import Counter

import numpy as np

from formgen import geom
from formgen.models.figures.r01_parts import arms


class RobotArmTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = geom.evaluate(dict(
            info=dict(id='ARMS',kind='figure',provenance=arms.PROVENANCE),
            parts=arms.PARTS,assemblies=[dict(id='arms',de='Arme')],
            anchors=arms.ANCHORS))
        cls.parts = {p['id']:p for p in cls.document['parts']}

    def test_original_source_and_all_source_parts_preserved(self):
        path = Path(arms.SOURCE.__file__)
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), arms.SOURCE_SHA256)
        source = arms.SOURCE.parts()
        self.assertEqual(len(source), 67)
        for side in ('r','l'):
            for pid, _, segment, kind, role, params in source:
                p = self.parts['arms_'+pid+'_'+side]
                self.assertEqual(p['source_parameters'],json.loads(json.dumps(params)))
                self.assertEqual((p['source_shape'],p['segment'],p['role']),(kind,segment,role))
                self.assertEqual(p['group'], side+'_'+segment)
                self.assertIn(p['group'],arms.SEGMENT_FRAMES)
        self.assertEqual(len(self.parts),138)

    def test_closed_positive_meshes_and_valid_json(self):
        json.dumps(self.document,allow_nan=False)
        json.dumps(arms.SEGMENT_FRAMES,allow_nan=False)
        self.assertEqual(len(self.document['warnings']),134)
        self.assertTrue(all(w.endswith('Fase: echte planare Kantenfase; ballons Zweisegment-Rundung wird nicht nachgebildet') for w in self.document['warnings']))
        for part in self.parts.values():
            mesh = part['mesh']
            edges = Counter(tuple(sorted((a,b))) for face in mesh['faces']
                            for a,b in zip(face,face[1:]+face[:1]))
            self.assertTrue(all(n == 2 for n in edges.values()),part['id'])
            self.assertGreater(geom._volume(mesh['vertices'],mesh['faces']),0,part['id'])
            self.assertNotIn(part['role'],('energy','glass'))

    def test_symmetric_geometry_and_four_fingers_plus_thumb(self):
        # Compare the authored solids before the generic bevel triangulator.
        # The default evaluated meshes are checked separately for closure.
        uncut = geom.evaluate(dict(
            info=dict(id='ARMS',kind='figure',provenance=arms.PROVENANCE),
            parts=arms.PARTS,assemblies=[dict(id='arms',de='Arme')],
            anchors=arms.ANCHORS),bevels=False)
        symmetric_parts={p['id']:p for p in uncut['parts']}
        for pid,part in symmetric_parts.items():
            if not pid.endswith('_r'):
                continue
            r = np.array(part['mesh']['vertices']); r[:,0] *= -1
            l = np.array(symmetric_parts[pid[:-1]+'l']['mesh']['vertices'])
            self.assertEqual({tuple(np.round(v,7)) for v in r},
                             {tuple(np.round(v,7)) for v in l},pid)
        for side in ('r','l'):
            for segment in [f'f{i}_{j}' for i in range(4) for j in range(3)]+[f't_{j}' for j in range(3)]:
                self.assertEqual(sum(p['group']==side+'_'+segment for p in self.parts.values()),3)

    def test_front_anchors_and_explicit_source_length_deviation(self):
        self.assertEqual(arms.ANCHORS['Socket_Elbow_R']['at'],[-36,1275,-371])
        self.assertEqual(arms.ANCHORS['Socket_Wrist_R']['at'],[53,1028,-478])
        self.assertAlmostEqual(arms.UPPER_MM,285.7288924838)
        self.assertAlmostEqual(arms.FORE_MM,283.5119045120)
        self.assertAlmostEqual(arms.UPPER_MM/320,arms.LENGTH_SCALE['upper'])
        self.assertAlmostEqual(arms.FORE_MM/300,arms.LENGTH_SCALE['fore'])
        for side in ('r','l'):
            for seg,length,dest in [('upper',arms.UPPER_MM,'Elbow'),('fore',arms.FORE_MM,'Wrist')]:
                f=arms.SEGMENT_FRAMES[side+'_'+seg]
                end=np.asarray(f['at'])+np.asarray(f['basis'][2])*length
                np.testing.assert_allclose(end,arms.ANCHORS['Socket_'+dest+'_'+side.upper()]['at'])

    def test_bearings_stay_round_and_hand_unscaled(self):
        for side in ('r','l'):
            frame=arms.SEGMENT_FRAMES[side+'_fore']
            axis=np.asarray(frame['basis'][0]); center=np.asarray(frame['at'])
            part=next(p for p in arms.PARTS if p['id']=='arms_elbow_'+side)
            for ring in part['rings']:
                delta=np.asarray(ring)-center
                radial=delta-np.outer(delta@axis,axis)
                np.testing.assert_allclose(np.linalg.norm(radial,axis=1),40*arms.SOURCE.ARM_BULK)
            f0=arms.SEGMENT_FRAMES[side+'_f0_0']; f1=arms.SEGMENT_FRAMES[side+'_f0_1']
            self.assertAlmostEqual(np.linalg.norm(np.asarray(f1['at'])-f0['at']),arms.SOURCE.FINGER_LINKS[0])


if __name__ == '__main__':
    unittest.main()
