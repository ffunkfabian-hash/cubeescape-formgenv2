"""Analytical checks for the shared-scale side-profile correction; no renders."""
import unittest

import numpy as np

from formgen import geom
from formgen.models.figures.r01_parts import legs


class RobotLegProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = geom.evaluate(dict(
            info=dict(id='R01_LEG_PROFILES',kind='figure',name_de='Beinprofile'),
            parts=legs.PARTS,assemblies=[dict(id='legs',de='Beine')],
            anchors=legs.ANCHORS))
        edges = []
        for p in cls.document['parts']:
            if not p['id'].endswith('_l'):
                continue
            v = np.asarray(p['mesh']['vertices'])*1000
            e = sorted({tuple(sorted((a,b))) for face in p['mesh']['faces']
                        for a,b in zip(face,face[1:]+face[:1])})
            edges.extend(v[np.asarray(e)])
        cls.edges = np.asarray(edges)

    def plane_extent(self, u, axis):
        a,b = self.edges[:,0],self.edges[:,1]
        selected = ((np.minimum(a[:,2],b[:,2])<=u+1e-8)
                    & (np.maximum(a[:,2],b[:,2])>=u-1e-8))
        a,b = a[selected],b[selected]
        du = b[:,2]-a[:,2]
        flat = abs(du)<1e-8
        t = np.divide(u-a[:,2],du,out=np.zeros_like(du),where=~flat)
        values = np.concatenate((a[:,axis]+t*(b[:,axis]-a[:,axis]),b[flat,axis]))
        return np.array([values.min(),values.max()])

    def test_frozen_front_envelope_including_connection_heights(self):
        # Frozen before this change from the actual mesh projected into x/u.
        # Includes the sole, ring overhangs and the narrow gap above the shin.
        expected = {
            0:(177,339),30:(149.5,368.73333333),62:(150,366),
            80:(151.42105263,361.73684211),100:(153,357),
            120:(154.77777778,351.66666667),145:(157,345),178:(168,324),
            190:(175,305),205:(163,317),234:(159,321),275:(163,317),
            585:(106,290),600:(110.28571429,281.42857143),620:(116,270),
            625:(141,247),643:(138,250),660:(111,277),680:(107,281),
            710:(107,281),750:(107,281),766:(111,277),772:(112,266),
            805:(103,253),1072:(81,219),1080:(82,212),
        }
        for u,bounds in expected.items():
            with self.subTest(u=u):
                np.testing.assert_allclose(self.plane_extent(u,0),bounds,atol=1e-6,rtol=0)

    def test_soled_ground_and_all_joint_datums_are_frozen(self):
        for side,sign in (('r',-1),('l',1)):
            sole = next(p for p in legs.PARTS if p['id']=='legs_foot_sole_'+side)
            self.assertEqual(sole['side'],[[-123,0],[180,0],[188,18],[186,48],
                                           [167,66],[-113,66],[-129,39]])
            self.assertEqual(sole['front'],[[sign*x,u] for x,u in
                [(177,0),(339,0),(368,19),(370,49),(361,68),(155,68),(148,42),(151,18)]])
            for name,at in [('Hip',[45,1080,sign*142]),('Knee',[35,710,sign*194]),
                            ('Ankle',[-30,234,sign*240])]:
                self.assertEqual(legs.ANCHORS['Socket_'+name+'_'+side.upper()]['at'],at)

    def test_profiles_follow_both_registered_side_measurements(self):
        # Neither whole-view scale nor ground datum changes to improve this.
        provenance = legs.PROVENANCE['profile_refinement']
        foot = provenance['foot_samples_mm']
        for i,u in enumerate(foot['u']):
            actual = -self.plane_extent(u,1)[::-1]
            backs = [foot[k][i] for k in ('right_back','left_back')]
            fronts = [foot[k][i] for k in ('right_front','left_front')]
            self.assertLess(abs(actual[0]-np.mean(backs)),1.5,(u,actual))
            # Raised dark panel adds a real 3mm skin above the toe shell.
            self.assertLess(abs(actual[1]-np.mean(fronts)),3.5,(u,actual))
        knee = provenance['knee_back_samples_mm']
        for i,u in enumerate(knee['u']):
            rear = -self.plane_extent(u,1)[1]
            self.assertLess(abs(rear-(knee['right'][i]+knee['left'][i])/2),1.5,u)
        for u,f in ((625,132.2),(643,139.85)):
            self.assertAlmostEqual(-self.plane_extent(u,1)[0],f,delta=.5)

    def test_no_collapsed_faces_or_open_connection_shells(self):
        for p in self.document['parts']:
            v = np.asarray(p['mesh']['vertices']);f = np.asarray(p['mesh']['faces'])
            areas = np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]),axis=1)/2
            self.assertGreater(areas.min(),1e-14,p['id'])
            if 'knee_rear_shell' in p['id']:
                solid = geom._as_manifold(v,f.tolist())
                self.assertGreater(solid.volume(),0,p['id'])
                self.assertEqual(p['wall_mm'],5)


if __name__ == '__main__':
    unittest.main()
