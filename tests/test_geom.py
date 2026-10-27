import json
import math
import unittest
from collections import Counter
from unittest.mock import patch
import numpy as np

from formgen import geom,model


def document(shape):
    return dict(info=dict(id='TEST',kind='figure',name_de='Test',provenance=dict(kind='Annahme',source='Analytischer Geometrietest')),parts=[dict(id='body',assembly='body',role='shell',bevel=0,**shape)],assemblies=[dict(id='body',de='Körper')],anchors={})


def evaluate(shape,**kw):
    return geom.evaluate(document(shape),**kw)


def volume(part):
    return geom._volume(part['mesh']['vertices'],part['mesh']['faces'])


class GeometryTests(unittest.TestCase):
    def assertSolid(self,part,expected=None):
        mesh=part['mesh']
        edge=Counter()
        directed=Counter()
        for face in mesh['faces']:
            for a,b in zip(face,face[1:]+face[:1]):
                edge[tuple(sorted((a,b)))]+=1
                directed[a,b]+=1
        self.assertTrue(all(n==2 for n in edge.values()))
        self.assertTrue(all(directed[a,b]==directed[b,a] for a,b in directed))
        self.assertGreater(volume(part),0)
        if expected is not None:
            self.assertAlmostEqual(volume(part),expected,delta=expected*1e-5)

    def test_mini_axes_and_contract(self):
        d=geom.evaluate(model.load('formgen/models/mini.py'))
        self.assertEqual(d['counts'],dict(parts=2,vertices=16,faces=24,triangles=24))
        np.testing.assert_allclose(d['anchors']['Socket_Hand']['position_m'],[0,-.02,-.03])
        self.assertEqual(len(d['parts'][0]['mesh']['hard']),12)
        self.assertSolid(d['parts'][0],.1*.04*.03)
        json.dumps(d,allow_nan=False)

    def test_concave_profile_real_cap(self):
        pts=[[0,0],[30,0],[30,10],[10,10],[10,30],[0,30]]
        d=evaluate(dict(shape='prof',pts=pts,w=10))
        self.assertSolid(d['parts'][0],500*10/1e9)
        d=evaluate(dict(shape='plan',pts=pts,u0=0,u1=10))
        self.assertSolid(d['parts'][0],500*10/1e9)

    def test_cylinder_axes_hollow_taper_and_phase(self):
        n=24
        for axis in ('f','u','x'):
            d=evaluate(dict(shape='cyl',axis=axis,c=[0,0],a0=0,a1=100,r=10,r1=20,r_in=5,segs=n))
            area=n/2*math.sin(2*math.pi/n)
            expected=area*(100+200+400-25-50-100)*100/3/1e9
            self.assertSolid(d['parts'][0],expected)
        p=evaluate(dict(shape='cyl',axis='f',c=[0,0],a0=0,a1=100,r=10,segs=4))['parts'][0]
        np.testing.assert_allclose(p['bounds_m'][1][[0,2]] if isinstance(p['bounds_m'][1],np.ndarray) else [p['bounds_m'][1][0],p['bounds_m'][1][2]],[math.sqrt(.00005)]*2)

    def test_frame_tube_multi_and_text_explicit(self):
        for shape in (dict(shape='frame',f0=0,f1=10,cu=0,ow=40,oh=50,iw=30,ih=40,r_out=4,r_in=2),dict(shape='tube',path=[[0,0,0],[10,0,0],[20,10,0]],r=2),dict(shape='xbox',f0=0,f1=5,cu=10,ww=20,hh=20)):
            self.assertSolid(evaluate(shape)['parts'][0])
        d=evaluate(dict(shape='text',text='TEST',size=10,f=0,u=0))
        self.assertSolid(d['parts'][0])
        self.assertGreater(len(d['parts'][0]['mesh']['faces']),12)
        self.assertFalse(any('Ersatz' in w for w in d['warnings']))

    def test_hull_loft_and_solid_surface(self):
        points=[[f,u,x] for f in (0,100) for u in (0,100) for x in (0,100)]
        self.assertSolid(evaluate(dict(shape='hull',points=points))['parts'][0],.001)
        rings=[[[f,u,x] for f,x in ((0,0),(100,0),(100,100),(0,100))] for u in (0,100)]
        self.assertSolid(evaluate(dict(shape='loft',rings=rings))['parts'][0],.001)
        # Closed shell: outer cube stays fixed, cavity is 80 mm cubed.
        self.assertSolid(evaluate(dict(shape='loft',rings=rings,thickness=10))['parts'][0],.001-.08**3)
        # Explicit outward winding +Z; inward is down by 10 mm.
        p=evaluate(dict(shape='surface',vertices=[[0,0,0],[0,0,100],[-100,0,100],[-100,0,0]],faces=[[0,1,2,3]],thickness=10))['parts'][0]
        self.assertSolid(p,.1*.1*.01)
        np.testing.assert_allclose(p['bounds_m'][0],[0,0,-.01])

    def test_collapsed_wall_is_rejected(self):
        rings=[[[f,u,x] for f,x in ((0,0),(100,0),(100,100),(0,100))] for u in (0,100)]
        with self.assertRaisesRegex(geom.GeometryError,'Wandstärke'):
            evaluate(dict(shape='loft',rings=rings,thickness=60))

    @unittest.skipIf(geom._manifold is None,'manifold3d optional')
    def test_prism2_exact_intersection_and_boolean(self):
        d=evaluate(dict(shape='prism2',side=[[0,0],[100,0],[100,100],[0,100]],front=[[-20,0],[20,0],[20,100],[-20,100]]))
        self.assertSolid(d['parts'][0],.1*.1*.04)
        d=evaluate(dict(shape='box',f0=0,f1=100,u0=0,u1=100,w=100,cuts=[dict(shape='box',f0=25,f1=75,u0=25,u1=75,w=120)]))
        self.assertSolid(d['parts'][0],.001-.05*.05*.1)

    def test_missing_boolean_emits_marker_and_warning(self):
        with patch.object(geom,'_manifold',None):
            d=evaluate(dict(shape='box',f0=0,f1=100,u0=0,u1=100,w=100,cuts=[dict(shape='box',f0=25,f1=75,u0=25,u1=75,w=120)]))
        self.assertIn('Decal',d['warnings'][0])
        self.assertEqual(len(d['parts'][0]['decal_meshes']),1)
        self.assertAlmostEqual(volume(d['parts'][0]),.001)

    @unittest.skipIf(geom._manifold is None,'manifold3d optional')
    def test_true_chamfer_changes_volume_not_bounds(self):
        d=document(dict(shape='box',f0=0,f1=100,u0=0,u1=100,w=100))
        d['parts'][0]['bevel']=5
        p=geom.evaluate(d)['parts'][0]
        self.assertEqual(p['bevel_status'],'segmented_bevel')
        self.assertSolid(p)
        self.assertLess(volume(p),.001)
        self.assertGreater(p['counts']['triangles'],12)
        np.testing.assert_allclose(p['bounds_m'],[[-.05,-.1,0],[.05,0,.1]],atol=1e-8)

    @unittest.skipIf(geom._manifold is None,'manifold3d optional')
    def test_segmented_bevel_retains_circular_midpoint(self):
        d=document(dict(shape='box',f0=0,f1=100,u0=0,u1=100,w=100))
        d['parts'][0].update(bevel=5, segs_bevel=2)
        p=geom.evaluate(d)['parts'][0]
        self.assertSolid(p)
        verts=np.asarray(p['mesh']['vertices'])
        # Middle of a long 90-degree edge: circle radius5mm, center(-5,95).
        midpoint=np.array([.05-.005+.005/math.sqrt(2), -.005+.005/math.sqrt(2)])
        self.assertTrue(np.any(np.linalg.norm(verts[:,:2]-midpoint,axis=1)<1e-10))
        d['parts'][0]['segs_bevel']=1
        chamfer=geom.evaluate(d)['parts'][0]
        self.assertEqual(chamfer['bevel_status'],'planar_chamfer')
        self.assertLess(volume(chamfer),volume(p))

    @unittest.skipIf(geom._manifold is None,'manifold3d optional')
    def test_disconnected_bevel_preserves_parts_and_gap(self):
        boxes=[dict(shape='box',f0=f,f1=f+20,u0=0,u1=20,w=20) for f in (0,60)]
        d=document(dict(shape='multi',items=boxes));d['parts'][0]['bevel']=2
        p=geom.evaluate(d)['parts'][0]
        self.assertEqual(p['bevel_status'],'segmented_bevel')
        self.assertSolid(p)
        components=list(geom._mesh_components(p['mesh']['vertices'],p['mesh']['faces']))
        self.assertEqual(len(components),2)
        self.assertTrue(all(geom._volume(v,f)>0 for v,f in components))
        self.assertFalse(any(-.06<y<-.02 for _,y,_ in p['mesh']['vertices']))

    @unittest.skipIf(geom._manifold is None,'manifold3d optional')
    def test_bevel_clamp_preserves_thin_box(self):
        d=document(dict(shape='box',f0=0,f1=20,u0=0,u1=20,w=1))
        d['parts'][0]['bevel']=10
        p=geom.evaluate(d)['parts'][0]
        self.assertSolid(p)
        self.assertGreater(volume(p),.02*.02*.001*.1)
        self.assertEqual(p['bevel_status'],'segmented_bevel')

    @unittest.skipIf(geom._manifold is None,'manifold3d optional')
    def test_concave_bevel_remains_explicitly_unsupported(self):
        d=document(dict(shape='box',f0=0,f1=30,u0=0,u1=30,w=10,
                        cuts=[dict(shape='box',f0=10,f1=40,u0=10,u1=40,w=20)]))
        d['parts'][0]['bevel']=1
        p=geom.evaluate(d)['parts'][0]
        self.assertEqual(p['bevel_status'],'unsupported')
        self.assertSolid(p,500*10/1e9)

    def test_pilot_every_part_evaluates(self):
        d=geom.evaluate(model.load('formgen/models/weapons/w01_auto_rifle.py'))
        self.assertEqual(d['counts']['parts'],72)
        self.assertGreater(d['counts']['triangles'],1000)
        for p in d['parts']:
            self.assertEqual(len(p['mesh']['hard']),len(p['mesh']['faces']))
            self.assertTrue(np.isfinite(p['mesh']['vertices']).all())
            vertices=np.asarray(p['mesh']['vertices'])
            faces=np.asarray(p['mesh']['faces'])
            areas2=np.linalg.norm(np.cross(vertices[faces[:,1]]-vertices[faces[:,0]],
                                          vertices[faces[:,2]]-vertices[faces[:,0]]),axis=1)
            self.assertTrue(np.all(areas2>1e-16),p['id'])
            self.assertSolid(p)
        json.dumps(d,allow_nan=False)
