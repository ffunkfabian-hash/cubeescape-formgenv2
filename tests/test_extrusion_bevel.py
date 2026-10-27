"""Analytic concave extrusion checks, separate from Blender parity claims."""
import copy
import math
import unittest
from collections import Counter

import numpy as np

from formgen import geom
from formgen.models.weapons import w01_auto_rifle


L_PROFILE = [[0, 0], [30, 0], [30, 10], [10, 10], [10, 30], [0, 30]]


def mesh(part):
    vertices, faces = geom._shape(part, [])
    return geom._bevel(vertices, faces, part.get('bevel', 1)/1000,
                       part.get('segs_bevel', 2), part=part)


def intersections(vertices, faces, f, u):
    """Independent triangle-ray test across the extrusion's width axis."""
    origin = np.array([-.1, -f/1000, u/1000])
    direction = np.array([1., 0., 0.])
    hits = []
    for face in geom._triangulate(vertices, faces):
        a, b, c = np.asarray(vertices)[face]
        matrix = np.column_stack([b-a, c-a, -direction])
        if abs(np.linalg.det(matrix)) < 1e-15:
            continue
        s, t, distance = np.linalg.solve(matrix, origin-a)
        if s >= -1e-10 and t >= -1e-10 and s+t <= 1+1e-10 and distance > 0:
            hits.append(distance)
    return sorted(set(np.round(hits, 10)))


@unittest.skipIf(geom._manifold is None, 'manifold3d optional')
class ExtrusionBevelTests(unittest.TestCase):
    def solid(self, vertices, faces):
        edges = Counter((a, b) for face in faces for a, b in zip(face, face[1:]+face[:1]))
        self.assertTrue(all(edges[a, b] == 1 and edges[b, a] == 1 for a, b in edges))
        tris = np.asarray(vertices)[geom._triangulate(vertices, faces)]
        areas = np.linalg.norm(np.cross(tris[:, 1]-tris[:, 0], tris[:, 2]-tris[:, 0]), axis=1)
        self.assertTrue(np.all(areas > 1e-16))
        self.assertGreater(geom._volume(vertices, faces), 0)
        self.assertEqual(str(geom._as_manifold(vertices, faces).status()), 'Error.NoError')

    def test_reentrant_fillet_adds_material_without_filling_notch(self):
        p = dict(shape='prof', pts=L_PROFILE, w=10, bevel=1)
        v, f = mesh(p)
        self.solid(v, f)
        self.assertEqual(len(intersections(v, f, 10.1, 10.1)), 2)
        self.assertEqual(intersections(v, f, 20, 20), [])
        self.assertEqual(intersections(v, f, 29.9, .1), [])
        # Both convex and re-entrant long edges contain the requested 2-segment
        # circular-profile midpoint. World axes here are (x, -f, u).
        d = 1-1/math.sqrt(2)
        for point in ((10+d, 10+d), (30-d, d)):
            projected = np.asarray(v)[:, [1, 2]]*[-1000, 1000]
            self.assertLess(np.linalg.norm(projected-point, axis=1).min(), 1e-9)

    def test_middle_section_has_analytic_segmented_fillet_area(self):
        p = dict(shape='prof', pts=L_PROFILE, w=10, bevel=1)
        v, _ = mesh(p); v = np.asarray(v)
        ring = v[np.abs(v[:, 0]+.004) < 1e-12][:, [1, 2]]*[-1000, 1000]
        # Five convex 90-degree corners lose area, one concave corner gains it.
        expected = 500-4*(1-math.sqrt(2)/2)
        self.assertAlmostEqual(abs(geom._area(ring)), expected, places=9)

    def test_cap_arc_collapse_has_real_topology_instead_of_null_faces(self):
        for segments in (1, 2, 3):
            p = dict(shape='prof', pts=L_PROFILE, w=10, bevel=1, segs_bevel=segments)
            v, f = mesh(p)
            self.solid(v, f)
            v = np.asarray(v)
            cap = v[np.abs(v[:, 0]+.005) < 1e-12]
            self.assertEqual(len(cap), len(np.unique(cap, axis=0)))
            self.assertTrue(np.any(np.linalg.norm(cap[:, [1, 2]]-[-.001, .001], axis=1) < 1e-12))

    def test_angle_filter_preserves_shallow_longitudinal_notch(self):
        profile = [[0, 0], [40, 0], [40, 40], [20, 40], [10, 38], [0, 40]]
        p = dict(shape='prof', pts=profile, w=10, bevel=1)
        v, f = mesh(p); self.solid(v, f)
        middle = np.asarray(v)[np.abs(np.asarray(v)[:, 0]+.004) < 1e-12]
        self.assertTrue(np.any(np.linalg.norm(middle[:, [1, 2]]-[-.01, .038], axis=1) < 1e-12))

    def test_winding_and_plan_rotation_have_identical_volume(self):
        variants = [dict(shape='prof', pts=L_PROFILE, w=10, bevel=1),
                    dict(shape='prof', pts=L_PROFILE[::-1], w=10, bevel=1),
                    dict(shape='plan', pts=L_PROFILE, u0=0, u1=10, bevel=1)]
        volumes = []
        for p in variants:
            v, f = mesh(p); self.solid(v, f)
            volumes.append(geom._volume(v, f))
        np.testing.assert_allclose(volumes, volumes[0], atol=1e-15)

    def test_oversize_clamp_preserves_thin_concave_shape_and_notch(self):
        profile = [[0, 0], [30, 0], [30, 2], [2, 2], [2, 30], [0, 30]]
        p = dict(shape='prof', pts=profile, w=1, bevel=20)
        v, f = mesh(p); self.solid(v, f)
        self.assertEqual(intersections(v, f, 20, 20), [])
        self.assertGreater(geom._volume(v, f), 116/1e9*.1)

    def test_four_w01_profiles_are_valid_without_mutating_source(self):
        names = ('sight_body', 'grip', 'trigger', 'trigger_guard')
        for source in w01_auto_rifle.PARTS:
            if source['id'] not in names:
                continue
            with self.subTest(part=source['id']):
                p = copy.deepcopy(source); before = copy.deepcopy(p)
                self.assertTrue(geom._concave_extrusion(p))
                v, f = mesh(p); self.solid(v, f)
                self.assertEqual(p, before)
                original, original_faces = geom._shape(p, [])
                self.assertLess(geom._volume(v, f), geom._volume(original, original_faces))
                self.assertGreater(geom._volume(v, f), .8*geom._volume(original, original_faces))

    def test_cut_or_nonextrusion_never_uses_uncut_profile_path(self):
        p = dict(shape='prof', pts=L_PROFILE, w=10)
        self.assertFalse(geom._concave_extrusion(dict(p, cuts=[{}])))
        self.assertFalse(geom._concave_extrusion(dict(p, shape='surface')))
        self.assertFalse(geom._concave_extrusion(dict(p, pts=[[0, 0], [1, 0], [1, 1], [0, 1]])))


if __name__ == '__main__':
    unittest.main()
