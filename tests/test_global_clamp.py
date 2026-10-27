"""A short asymmetric notch limits remote bevels without identity-specific data."""
import math
import unittest
import numpy as np
from formgen import geom
from formgen.polybevel import bevel, planar_brep


@unittest.skipIf(geom._manifold is None, 'manifold3d optional')
class GlobalClampTests(unittest.TestCase):
    def source(self):
        # 3 mm notch width limits a distant 100 mm lower edge; 40 mm extrusion.
        part=dict(shape='prof',pts=[(0,0),(100,0),(100,60),(55,60),
            (55,52),(52,52),(52,60),(0,60)],w=40)
        return geom._shape(part,[])

    def test_short_notch_sets_one_common_width_for_remote_edges(self):
        vertices,faces=self.source();before=np.array(vertices,copy=True)
        v,t,d=bevel(vertices,faces,.005,2)
        np.testing.assert_array_equal(vertices,before)
        self.assertAlmostEqual(d['global_conservative_setback_m'],.00072,places=14)
        np.testing.assert_allclose([e['width'] for e in d['edges']],.00072,atol=1e-14,rtol=0)
        remote=[e for e in d['edges'] if np.max(before[list(e['edge']),2])<.001]
        self.assertTrue(remote)
        self.assertTrue(all(e['requested']==.005 for e in remote))
        self.assertGreater(d['volume_m3'],0)
        self.assertEqual(d['shallow_reduced_edges'],0)

    def test_global_clamp_commutes_with_rotation_translation_and_scaling(self):
        vertices,faces=self.source();vertices=np.asarray(vertices)
        base,_,diag=bevel(vertices,faces,.005,2);base=np.asarray(base)
        a,b=.371,-.213
        rz=np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]])
        ry=np.array([[math.cos(b),0,math.sin(b)],[0,1,0],[-math.sin(b),0,math.cos(b)]])
        rotation=rz@ry;shift=np.array([.37,-.23,.41])
        for scale in [.5,2.]:
            with self.subTest(scale=scale):
                vv,tt,dd=bevel(scale*vertices@rotation.T+shift,faces,.005*scale,2)
                self.assertAlmostEqual(dd['global_conservative_setback_m'],scale*.00072,places=13)
                # Rotated Delaunay caps may select the other nonplanar diagonal;
                # set back and point-set invariance below remain exact.
                self.assertLess(abs(dd['volume_m3']/(diag['volume_m3']*scale**3)-1),1e-7)
                restored=(np.asarray(vv)-shift)@rotation/scale
                self.assertEqual(len(restored),len(base))
                self.assertLess(np.linalg.norm(restored[:,None,:]-base[None,:,:],axis=2).min(axis=1).max(),1e-11)
