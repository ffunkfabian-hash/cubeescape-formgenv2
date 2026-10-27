"""Actual post-Cut face/edge/corner geometry; no Blender parity assertion."""
import copy
import json
import math
import unittest
from collections import Counter

import numpy as np

from formgen import geom, model
from formgen.models.weapons import w01_auto_rifle
from formgen.polybevel import bevel, _self_intersects


NAMES = ['upper','lower','top_shroud','magazine','handguard','barrel','muzzle']


def ray_x(vertices,faces,y,z):
    v=np.asarray(vertices);t=np.asarray(geom._triangulate(v,faces));tri=v[t]
    origin=np.array([-.1,y,z]);direction=np.array([1.,0.,0.])
    e1,e2=tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]
    h=np.cross(direction,e2);det=np.sum(e1*h,axis=1)
    good=np.abs(det)>1e-16;inv=np.zeros(len(det));inv[good]=1/det[good]
    shift=origin-tri[:,0];u=inv*np.sum(shift*h,axis=1);q=np.cross(shift,e1)
    w=inv*np.sum(direction*q,axis=1);distance=inv*np.sum(e2*q,axis=1)
    keep=good&(u>=-1e-10)&(w>=-1e-10)&(u+w<=1+1e-10)&(distance>=0)
    return sorted(set(np.round(distance[keep]-.1,12)))


@unittest.skipIf(geom._manifold is None,'manifold3d optional')
class PolyhedralBevelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.definition=model.load(w01_auto_rifle.__file__)
        cls.source=geom.evaluate(cls.definition,bevels=False)
        cls.source_parts={p['id']:p for p in cls.source['parts']}
        cls.result=geom.evaluate(cls.definition)
        cls.parts={p['id']:p for p in cls.result['parts']}

    def solid(self,part):
        v=np.asarray(part['mesh']['vertices']);t=np.asarray(part['mesh']['faces']);tri=v[t]
        area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)
        self.assertGreater(area.min(),1e-14)
        uses=Counter((a,b) for f in t for a,b in zip(f,np.roll(f,-1)))
        self.assertTrue(all(uses[a,b]==uses[b,a]==1 for a,b in uses))
        self.assertEqual(set(t.ravel()),set(range(len(v))))
        solid=geom._as_manifold(v,t.tolist());self.assertGreater(solid.volume(),0)
        return solid

    def test_all_seven_actual_postcut_nets_have_closed_nonempty_patch_geometry(self):
        expected={'upper':(576,1148),'lower':(294,584),'top_shroud':(294,584),
                  'magazine':(444,884),'handguard':(336,672),'barrel':(384,764),'muzzle':(1320,2648)}
        for name in NAMES:
            with self.subTest(name=name):
                p=self.parts[name];self.solid(p)
                self.assertEqual(p['bevel_status'],'segmented_polyhedral_bevel')
                self.assertEqual((len(p['mesh']['vertices']),len(p['mesh']['faces'])),expected[name])
                old=np.asarray(self.source_parts[name]['bounds_m']);new=np.asarray(p['bounds_m'])
                self.assertTrue(np.all(new[0]>=old[0]-1e-12))
                self.assertTrue(np.all(new[1]<=old[1]+1e-12))
                d=p['bevel_diagnostics'];self.assertEqual(d['self_intersections'],0)
                self.assertGreater(d['minimum_setback_m'],0)
                self.assertLessEqual(d['maximum_setback_m'],p['bevel']/1000+1e-12)
        json.dumps(self.result,allow_nan=False)

    def test_lower_both_pairs_of_real_blind_floors_and_cavity_centers_remain(self):
        p=self.parts['lower'];v,f=p['mesh']['vertices'],p['mesh']['faces']
        for y,z in [(.087,.073),(-.160,.077),(.087,.079),(-.160,.081)]:
            with self.subTest(y=y,z=z):
                np.testing.assert_allclose(ray_x(v,f,y,z),[-.0195,.0195],atol=1e-11,rtol=0)
        d=p['bevel_diagnostics']
        self.assertEqual(p['bevel'],5)
        self.assertAlmostEqual(d['minimum_setback_m'],.00036,places=14)
        self.assertAlmostEqual(d['maximum_setback_m'],.005,places=14)
        warning=' '.join(w for w in self.result['warnings'] if w.startswith('lower:'))
        self.assertIn('0.36..5 mm',warning)
        self.assertIn('keine Blender',warning)
        self.assertIn('Clampparitaet',warning)

    def test_lower_convex_mouth_and_concave_floor_have_true_circle_midpoints(self):
        # The source pocket at X+ has its upper wall at Z80, floor X19.5.
        # Actual depth1.5mm gives the explicit24% local setback0.36mm.
        r=.00036;a=1-1/math.sqrt(2);v=np.asarray(self.parts['lower']['mesh']['vertices'])
        for target in [[.021-r*a,.080+r*a],[.0195+r*a,.080-r*a]]:
            self.assertLess(np.linalg.norm(v[:,[0,2]]-target,axis=1).min(),1e-14)

    def test_plane_patch_has_real_slope_and_preserves_handguard_through_opening(self):
        p=self.parts['handguard'];v=np.asarray(p['mesh']['vertices']);t=np.asarray(p['mesh']['faces']);tri=v[t]
        n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.linalg.norm(n,axis=1)[:,None]
        self.assertTrue(np.any((np.abs(n[:,1])>.1)&(np.abs(n[:,2])>.1)))
        # A known large central opening survives the actual post-Cut source.
        source=self.source_parts['handguard'];sv=source['mesh']['vertices'];st=source['mesh']['faces']
        for y,z in [(-.32,.100),(-.33,.100)]:
            np.testing.assert_allclose(ray_x(v,t,y,z),ray_x(sv,st,y,z),atol=1e-11,rtol=0)

    def test_translation_rotation_and_one_segment_are_geometric_not_id_exceptions(self):
        p=self.source_parts['lower'];v=np.asarray(p['mesh']['vertices']);f=p['mesh']['faces']
        angle=.371;rotation=np.array([[math.cos(angle),-math.sin(angle),0],
                                     [math.sin(angle),math.cos(angle),0],[0,0,1]])
        offset=np.array([.37,-.23,.41]);a,b,diag=bevel((v@rotation.T+offset).tolist(),f,.005,1)
        original,_,original_diag=bevel(v,f,.005,1)
        self.assertAlmostEqual(diag['volume_m3'],original_diag['volume_m3'],places=13)
        # Compare point sets in source coordinates; triangulation diagonals may change.
        restored=(np.asarray(a)-offset)@rotation
        for point in original:self.assertLess(np.linalg.norm(restored-point,axis=1).min(),1e-11)

    def test_incompatible_higher_segment_corner_is_explicitly_unsupported(self):
        d=copy.deepcopy(self.definition);d['parts']=[p for p in d['parts'] if p['id']=='upper'];d['parts'][0]['segs_bevel']=4;d['assemblies']=[a for a in d['assemblies'] if a['id']=='receiver'];d['anchors']={};d.pop('poses',None)
        p=geom.evaluate(d)['parts'][0]
        self.assertEqual(p['bevel_status'],'unsupported')
        self.assertNotIn('bevel_diagnostics',p)

    def test_real_crossing_and_coplanar_overlap_gates_and_valid_shared_edge(self):
        v=np.array([[0,0,0],[2,0,0],[0,2,0],[.25,.25,0],[1.5,.25,0],[.25,1.5,0]],float)
        self.assertTrue(_self_intersects(v,np.array([[0,1,2],[3,4,5]])))
        v[3:]=[[.5,.5,-1],[.5,.5,1],[1.5,.5,0]]
        self.assertTrue(_self_intersects(v,np.array([[0,1,2],[3,4,5]])))
        v=np.array([[0,0,0],[2,0,0],[0,2,0],[1,1,-1],[1,1,1]],float)
        self.assertTrue(_self_intersects(v,np.array([[0,1,2],[0,3,4]])))
        v=np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0]],float)
        self.assertFalse(_self_intersects(v,np.array([[0,1,2],[0,2,3]])))

    def test_invalid_width_segment_count_and_enclosed_disconnected_void_are_rejected(self):
        p=self.source_parts['lower'];v,f=p['mesh']['vertices'],p['mesh']['faces']
        for width,segs in [(0,2),(float('nan'),2),(.005,0),(.005,True)]:
            with self.assertRaises(geom.GeometryError):bevel(v,f,width,segs)
        with self.assertRaises(geom.GeometryError):bevel(v,[face[::-1] for face in f],.005,2)
        outer=geom._manifold.Manifold.cube([.03,.03,.03]);inner=geom._manifold.Manifold.cube([.01,.01,.01]).translate([.01,.01,.01])
        vv,ff=geom._from_manifold(outer-inner)
        with self.assertRaises(geom.GeometryError):bevel(vv,ff,.001,2)
