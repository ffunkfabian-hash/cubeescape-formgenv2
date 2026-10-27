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

    def test_nape_profile_preserves_front_width_and_original_collar_entry(self):
        neck = next(p for p in head.PARTS if p['id'] == 'head_neck_core')
        original = np.asarray([(1598,61,75,-30), (1630,64,79,-28),
                               (1665,67,85,-33), (1704,60,83,-29)], float)
        rows = np.asarray([[ring[0][1], max(abs(p[2]) for p in ring),
                            max(p[0] for p in ring), min(p[0] for p in ring)]
                           for ring in neck['rings']])
        for column in (1, 2):
            np.testing.assert_allclose(rows[:, column],
                                       np.interp(rows[:, 0], original[:, 0], original[:, column]),
                                       rtol=0, atol=1e-12)
        np.testing.assert_array_equal(rows[0], original[0])
        np.testing.assert_array_equal(rows[-1], original[-1])
        # Independently digitized rear contour of both color references,
        # rounded to author millimetres; no free widening of the neck.
        for height, bounds in ((1630, (-87, -84)), (1640, (-76, -73)),
                               (1650, (-70, -66)), (1660, (-42, -39))):
            back = rows[rows[:, 0] == height, 3].item()
            self.assertTrue(bounds[0] <= back <= bounds[1])
        self.assertEqual(head.ANCHORS['Socket_Neck']['at'], [35,1690,0])
        self.assertEqual(head.ANCHORS['Socket_Head']['at'], [35,1690,0])

    @unittest.skipIf(geom._manifold is None, 'manifold3d optional')
    def test_nape_remains_closed_and_physically_connected_to_collar(self):
        from formgen.models.figures.r01_parts import upper_body
        neck = next(p for p in head.PARTS if p['id'] == 'head_neck_core')
        collar = next(p for p in upper_body.PARTS if p['id'] == 'upper_body_neck_collar')
        nv, nf = geom._shape(neck, [])
        cv, cf = geom._shape(collar, [])
        solid = geom._as_manifold(nv, nf)
        self.assertEqual(str(solid.status()), 'Error.NoError')
        self.assertGreater(solid.volume(), 0)
        overlap = solid ^ geom._as_manifold(cv, cf)
        self.assertGreater(overlap.volume(), 1e-10)
        triangles = np.asarray(nv)[geom._triangulate(nv, nf)]
        area2 = np.linalg.norm(np.cross(triangles[:, 1]-triangles[:, 0],
                                        triangles[:, 2]-triangles[:, 0]), axis=1)
        self.assertTrue(np.all(area2 > 1e-16))

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

    @unittest.skipIf(geom._manifold is None, 'manifold3d optional')
    def test_occipital_plate_clears_carrier_and_is_visible_over_its_full_footprint(self):
        plate=self.parts['head_occipital_shell']['mesh']
        carrier=self.parts['head_rear_housing']['mesh']
        a=geom._as_manifold(plate['vertices'],plate['faces'])
        b=geom._as_manifold(carrier['vertices'],carrier['faces'])
        self.assertLess(abs((a^b).volume()),1e-15)
        # Independent orthographic back rays through both old black-island
        # regions and the entire panel, using actual triangles, no raster.
        def back_depth(mesh,x,u):
            tri=np.asarray(mesh['vertices'])[mesh['faces']]
            p=tri[:,:,[0,2]];point=np.array([x,u])
            e,f=p[:,1]-p[:,0],p[:,2]-p[:,0];q=point-p[:,0]
            cross=lambda a,b:a[:,0]*b[:,1]-a[:,1]*b[:,0]
            det=cross(e,f);good=abs(det)>1e-18
            v=np.divide(cross(q,f),det,out=np.zeros_like(det),where=good)
            w=np.divide(cross(e,q),det,out=np.zeros_like(det),where=good)
            good&=(v>=-1e-9)&(w>=-1e-9)&(v+w<=1+1e-9)
            depth=tri[:,0,1]+v*(tri[:,1,1]-tri[:,0,1])+w*(tri[:,2,1]-tri[:,0,1])
            return depth[good].max() if good.any() else None
        checked=0
        for x in range(-80,81,4):
            for u in range(1782,1847,2):
                front=back_depth(plate,x/1000,u/1000)
                behind=back_depth(carrier,x/1000,u/1000)
                # On the exact panel outline a ray may also graze the uncut
                # neighboring carrier; require a half-mm interior footprint.
                interior=all(back_depth(plate,(x+dx)/1000,(u+du)/1000) is not None
                             for dx,du in ((-.5,0),(.5,0),(0,-.5),(0,.5)))
                if interior and front is not None and behind is not None:
                    self.assertGreaterEqual(front-behind,.004-1e-10,(x,u))
                    checked+=1
        self.assertGreater(checked,500)

    def test_occipital_wall_has_corresponding_symmetric_four_mm_triangles(self):
        p=next(p for p in head.PARTS if p['id']=='head_occipital_shell')
        outer=np.asarray(p['vertices'][:9]);inner=np.asarray(p['vertices'][9:])
        np.testing.assert_allclose(inner-outer,np.tile([4,0,0],(9,1)),atol=1e-12)
        faces=p['faces'];self.assertEqual(len(faces),32)
        self.assertEqual({tuple(f) for f in faces[8:16]},
                         {tuple(9+i for i in reversed(f)) for f in faces[:8]})
        mirrored=outer*[1,1,-1]
        self.assertEqual(set(map(tuple,outer)),set(map(tuple,mirrored)))
        mirror={i:next(j for j,v in enumerate(outer) if np.array_equal(v,mirrored[i])) for i in range(9)}
        self.assertEqual({tuple(sorted(f)) for f in faces[:8]},
                         {tuple(sorted(mirror[i] for i in f)) for f in faces[:8]})

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
