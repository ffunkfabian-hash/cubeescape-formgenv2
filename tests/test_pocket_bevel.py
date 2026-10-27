"""Actual blind-pocket fillets and closed convex/concave corner patches."""
import math
import unittest
from collections import Counter

import numpy as np

from formgen import geom, model
from formgen.models.weapons import w01_auto_rifle


def fixture():
    return dict(info=dict(id='TEST',kind='figure',name_de='Pocket',provenance=dict(kind='Annahme',source='Analytischer Taschentest')),
        parts=[dict(id='pocket',assembly='body',role='shell',shape='box',f0=-40,f1=40,u0=0,u1=30,w=20,bevel=2,
                    cuts=[dict(shape='box',f0=-20,f1=20,u0=10,u1=20,w=8,x=-10)])],
        assemblies=[dict(id='body',de='Körper')],anchors={})


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
class PocketBevelTests(unittest.TestCase):
    def solid(self,mesh):
        v=np.asarray(mesh['vertices']);t=np.asarray(mesh['faces']);xyz=v[t]
        area=np.linalg.norm(np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]),axis=1)
        self.assertGreater(area.min(),1e-14)
        uses=Counter((a,b) for f in t for a,b in zip(f,np.roll(f,-1)))
        self.assertTrue(all(uses[a,b]==uses[b,a]==1 for a,b in uses))
        self.assertEqual(set(t.ravel()),set(range(len(v))))
        self.assertEqual(len(v)-len(uses)//2+len(t),2)
        solid=geom._as_manifold(v,t.tolist())
        self.assertGreater(solid.volume(),0)
        return solid

    def test_real_bolt_carrier_gets_closed_pocket_fillet_and_truthful_warning(self):
        d=geom.evaluate(model.load(w01_auto_rifle.__file__))
        p=next(p for p in d['parts'] if p['id']=='bolt_carrier')
        self.assertEqual(p['bevel_status'],'segmented_pocket_bevel')
        solid=self.solid(p['mesh'])
        self.assertAlmostEqual(solid.volume()*1e9,68608.8877428624,places=6)
        np.testing.assert_allclose(p['bounds_m'],[[-.013,-.082,.097],[.013,.040,.119]],atol=1e-14,rtol=0)
        np.testing.assert_allclose(ray_x(**{k:p['mesh'][k] for k in ['vertices','faces']},y=-.053,z=.108),[-.011,.013],atol=1e-11,rtol=0)
        warning=' '.join(w for w in d['warnings'] if w.startswith('bolt_carrier:'))
        self.assertIn('Blindtasche',warning)
        self.assertIn('Wand- und Bodenkanten',warning)
        self.assertIn('keine Blender',warning)
        self.assertNotIn('komponentenweise konvex',warning)

    def test_generic_pocket_preserves_blind_floor_instead_of_becoming_through_hole(self):
        for segments in [1,2,4]:
            with self.subTest(segments=segments):
                d=fixture();d['parts'][0]['segs_bevel']=segments
                p=geom.evaluate(d)['parts'][0];self.solid(p['mesh'])
                self.assertEqual(p['bevel_status'],'planar_pocket_chamfer' if segments==1 else 'segmented_pocket_bevel')
                np.testing.assert_allclose(ray_x(p['mesh']['vertices'],p['mesh']['faces'],0,.015),[-.006,.01],atol=1e-11,rtol=0)

    def test_mouth_wall_floor_and_three_way_corner_have_actual_analytic_midpoints(self):
        p=geom.evaluate(fixture())['parts'][0];v=np.asarray(p['mesh']['vertices'])
        r=.00196;a=1-1/math.sqrt(2);y0,z0=-.020,.010;z1=.020
        targets=[[-.010+r*a,y0+r,z1+r*a],[-.006-r*a,y0+r,z1-r*a],
                 [-.010+r,y0+r*a,z0+r*a],[-.006-r*a,y0+r/2,z0+r/2]]
        for point in targets:self.assertLess(np.linalg.norm(v-point,axis=1).min(),1e-14)

    def test_other_seven_variable_parts_stay_explicitly_unsupported(self):
        d=geom.evaluate(model.load(w01_auto_rifle.__file__));parts={p['id']:p for p in d['parts']}
        for name in ['upper','lower','top_shroud','magazine','handguard','barrel','muzzle']:
            with self.subTest(name=name):self.assertEqual(parts[name]['bevel_status'],'unsupported')

    def test_fully_enclosed_void_cannot_be_mistaken_for_open_blind_pocket(self):
        d=fixture();d['parts'][0]['cuts'][0].update(w=4,x=0)
        p=geom.evaluate(d)['parts'][0]
        self.assertEqual(p['bevel_status'],'unsupported')
