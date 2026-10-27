"""Post-Cut profile proof and real multi-contour bevel regressions."""
import copy
import unittest
from collections import Counter

import numpy as np

from formgen import geom, model
from formgen.models.weapons import w01_auto_rifle


@unittest.skipIf(geom._manifold is None, 'manifold3d optional')
class CutExtrusionBevelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = {p['id']:p for p in w01_auto_rifle.PARTS}
        doc = geom.evaluate(model.load(w01_auto_rifle.__file__), bevels=False)
        cls.parts = {p['id']:p for p in doc['parts']}

    def assertSolid(self, vertices, faces):
        v = np.asarray(vertices)
        t = np.asarray(geom._triangulate(v, faces))
        uses = Counter(tuple(sorted(e)) for tri in t for e in zip(tri,np.roll(tri,-1)))
        self.assertEqual(set(uses.values()), {2})
        area = np.linalg.norm(np.cross(v[t[:,1]]-v[t[:,0]],v[t[:,2]]-v[t[:,0]]),axis=1)
        self.assertGreater(area.min(),1e-14)
        solid = geom._as_manifold(v,t.tolist())
        self.assertGreater(solid.volume(),0)
        self.assertAlmostEqual(geom._volume(v,t.tolist()),solid.volume(),delta=1e-15)
        return solid

    def test_four_real_cut_extrusions_keep_holes_bounds_and_positive_volume(self):
        for name,holes in [('rail',0),('stock_spine',3),('stock',1),('butt_pad',0)]:
            with self.subTest(name=name):
                p = self.parts[name]; mesh = p['mesh']; source = self.source[name]
                section = geom._constant_x_cut_profile(mesh['vertices'],mesh['faces'])
                self.assertIsNotNone(section)
                self.assertEqual(sum(geom._area(q)<0 for q in section[0]),holes)
                v,f = geom._bevel(mesh['vertices'],mesh['faces'],source['bevel']/1000,2,part=source)
                solid = self.assertSolid(v,f)
                middle = solid.transform([[0,1,0,0],[0,0,1,0],[1,0,0,0]]).slice(0).to_polygons()
                self.assertEqual(sum(geom._area(q)<0 for q in middle),holes)
                bounds = np.array([np.min(v,axis=0),np.max(v,axis=0)])
                old = np.array(p['bounds_m'])
                np.testing.assert_allclose(bounds[:,0],old[:,0],atol=1e-14,rtol=0)
                self.assertTrue(np.all(bounds[0]>=old[0]-1e-13))
                self.assertTrue(np.all(bounds[1]<=old[1]+1e-13))
                self.assertLess(solid.volume(),geom._volume(mesh['vertices'],mesh['faces']))

    def test_butt_pad_real_nearly_equal_collapse_stations_have_no_null_faces(self):
        p = self.parts['butt_pad']; mesh = p['mesh']
        v,f = geom._bevel(mesh['vertices'],mesh['faces'],.003,2,part=self.source['butt_pad'])
        self.assertSolid(v,f)
        self.assertEqual((len(v),len(geom._triangulate(v,f))),(624,1244))

    def test_eight_variable_cut_parts_are_rejected(self):
        for name in ['upper','lower','top_shroud','bolt_carrier','magazine','handguard','barrel','muzzle']:
            with self.subTest(name=name):
                mesh = self.parts[name]['mesh']
                self.assertIsNone(geom._constant_x_cut_profile(mesh['vertices'],mesh['faces']))

    def test_unequal_contours_holes_and_separate_island_in_arbitrary_order(self):
        outer = np.array([[0,0],[50,0],[50,40],[0,40]])*.001
        hole1 = np.array([[5,5],[5,15],[15,5]])*.001
        hole2 = np.array([[25,5],[23,9],[25,13],[29,13],[29,5]])*.001
        angle = np.linspace(0,2*np.pi,8)[:-1]
        island = np.column_stack([65+8*np.cos(angle),20+8*np.sin(angle)])*.001
        for segments in [1,2,4]:
            with self.subTest(segments=segments):
                contours = [hole2,island,outer,hole1]
                v,f = geom._contour_extrusion_bevel(contours,np.zeros(3),np.array([1.,0.,0.]),
                    np.array([[0.,1.,0.],[0.,0.,1.]]),.022,.0004,segments)
                self.assertSolid(v,f)

    def test_changed_cut_mesh_cannot_be_replaced_by_cap_silhouettes(self):
        # Identical outer end silhouettes hide a wholly internal void.
        source = dict(shape='box',f0=0,f1=30,u0=0,u1=30,w=10)
        v,f = geom._shape(source,[])
        cutter = dict(shape='box',f0=10,f1=20,u0=10,u1=20,w=4)
        cv,cf = geom._shape(cutter,[])
        v,f = geom._from_manifold(geom._as_manifold(v,f)-geom._as_manifold(cv,cf))
        self.assertIsNone(geom._constant_x_cut_profile(v,f))

    def test_radius_below_construction_precision_rejects_instead_of_shifting_endcaps(self):
        square = np.array([[0,0],[.01,0],[.01,.01],[0,.01]])
        for radius in [1e-15,1e-13,1e-12]:
            with self.subTest(radius=radius), self.assertRaisesRegex(geom.GeometryError,'numerisch stabiler Clampbereich'):
                geom._contour_extrusion_bevel([square],np.zeros(3),np.array([1.,0.,0.]),
                    np.array([[0.,1.,0.],[0.,0.,1.]]),.01,radius,2)
