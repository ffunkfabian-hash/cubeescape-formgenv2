"""Analytical draft tests; no rendering or repository writes."""
import copy
import math
from collections import Counter
import unittest
import numpy as np
from formgen import geom
from formgen.models.weapons import w01_auto_rifle

def beveled(part, radius=None, segments=None):
    v,f=geom._shape(part,[])
    return geom._bevel(v,f,part.get('bevel',1)/1000 if radius is None else radius,
                       part.get('segs_bevel',2) if segments is None else segments,part=part)


CANDIDATES = ('shroud_bracket', 'core_ring', 'sight_frame_trim', 'handguard_cap')
PARTS = {p['id']: p for p in w01_auto_rifle.PARTS}


def edge_counts(faces):
    return Counter(tuple(sorted((a, b))) for f in faces for a, b in zip(f, f[1:]+f[:1]))


def ray_hits(vertices, faces, origin, direction):
    hits = []
    for tri in geom._triangulate(vertices, faces):
        a, b, c = np.asarray(vertices)[tri]
        matrix = np.column_stack([b-a, c-a, -direction])
        if abs(np.linalg.det(matrix)) < 1e-15:
            continue
        u, v, t = np.linalg.solve(matrix, origin-a)
        if u >= -1e-10 and v >= -1e-10 and u+v <= 1+1e-10:
            hits.append(t)
    return sorted(set(np.round(hits, 10)))


class RingBevelTests(unittest.TestCase):
    def solid(self, v, f):
        self.assertTrue(all(n == 2 for n in edge_counts(f).values()))
        direct = Counter((a, b) for face in f for a, b in zip(face, face[1:]+face[:1]))
        self.assertTrue(all(direct[a, b] == direct[b, a] for a, b in direct))
        self.assertGreater(geom._volume(v, f), 0)
        tris = np.asarray(v)[geom._triangulate(v, f)]
        area2 = np.linalg.norm(np.cross(tris[:, 1]-tris[:, 0], tris[:, 2]-tris[:, 0]), axis=1)
        self.assertTrue(np.all(area2 > 1e-16), float(area2.min()))
        solid = geom._as_manifold(v, f)
        self.assertEqual(str(solid.status()), 'Error.NoError')
        self.assertFalse(solid.is_empty())
        return solid

    def test_four_real_candidates_closed_positive_valid_nonzero_bounds_volume(self):
        for name in CANDIDATES:
            with self.subTest(name=name):
                p = PARTS[name]
                old, oldfaces = geom._shape(p, [])
                v, f = beveled(p)
                self.solid(v, f)
                self.assertLess(geom._volume(v, f), geom._volume(old, oldfaces))
                np.testing.assert_allclose([np.min(v, axis=0), np.max(v, axis=0)],
                                           [np.min(old, axis=0), np.max(old, axis=0)], atol=1e-12, rtol=0)

    def test_four_real_candidates_open_hole_and_middle_unchanged(self):
        for name in CANDIDATES:
            with self.subTest(name=name):
                p = PARTS[name]
                old, _ = geom._shape(p, [])
                old = np.asarray(old); n = len(old)//4
                delta = old[n]-old[0]; length = np.linalg.norm(delta); axis = delta/length
                v, f = beveled(p); v = np.asarray(v)
                center = old[2*n:3*n].mean(axis=0)
                self.assertEqual(ray_hits(v, f, center-axis*length, axis), [])
                # Rings at b and L-b are the unchanged source profiles. Their
                # connecting faces are straight, hence the entire middle is too.
                b = p['bevel']/1000
                for station in (b, length-b):
                    at = v[np.abs((v-old[0])@axis-station) < 1e-12]
                    expected = np.vstack([old[:n], old[2*n:3*n]])+axis*station
                    self.assertEqual(len(at), len(expected))
                    distance = np.linalg.norm(at[:, None]-expected[None, :], axis=2)
                    self.assertLess(float(distance.min(axis=1).max()), 1e-12)

    def test_quarter_circle_midpoints_both_rims_and_chamfer(self):
        p = dict(shape='cyl', axis='u', c=[0, 0], a0=0, a1=100, r=30, r_in=20, segs=24, bevel=2)
        v, f = beveled(p); v = np.asarray(v)
        b = .002; z = b*(1-1/math.sqrt(2))
        at = v[np.abs(v[:, 2]-z) < 1e-12]
        radii = np.linalg.norm(at[:, :2], axis=1)
        offset = z/math.cos(math.pi/24)
        np.testing.assert_allclose(np.sort(radii), [(.02+offset)]*24+[(.03-offset)]*24, atol=1e-12)
        self.assertEqual(len(v[np.abs(v[:, 2]-(.1-z)) < 1e-12]), 48)
        linear, lf = beveled(p, segments=1)
        self.solid(linear, lf)
        self.assertLess(geom._volume(linear, lf), geom._volume(v, f))

    def test_rotation_equivalence_f_x_u(self):
        results = []
        for axis in ('f', 'x', 'u'):
            p = dict(shape='cyl', axis=axis, c=[0, 0], a0=0, a1=100, r=30, r_in=20, segs=24, bevel=2)
            v, f = beveled(p)
            self.solid(v, f)
            results.append((len(v), len(f), geom._volume(v, f)))
        for result in results[1:]:
            np.testing.assert_allclose(result, results[0], atol=1e-12)

    def test_oversize_width_clamps_both_wall_and_length_without_closing_hole(self):
        for height in (1, 100):
            p = dict(shape='cyl', axis='u', c=[0, 0], a0=0, a1=height, r=10, r_in=9, segs=24, bevel=20)
            v, f = beveled(p)
            self.solid(v, f)
            self.assertEqual(ray_hits(v, f, np.array([0., 0., -.1]), np.array([0., 0., 1.])), [])
            self.assertGreater(geom._volume(v, f), 0)

    def test_does_not_mutate_part_or_source_mesh(self):
        p = copy.deepcopy(PARTS['shroud_bracket']); before = copy.deepcopy(p)
        v, f = geom._shape(p, []); oldv, oldf = copy.deepcopy(v), copy.deepcopy(f)
        geom._ring_bevel(v, f, .0015, 2)
        self.assertEqual(p, before); self.assertEqual(v, oldv); self.assertEqual(f, oldf)

    def test_octagonal_muzzle_and_sharp_frame_receive_longitudinal_fillet(self):
        frame = dict(shape='frame', f0=0, f1=10, cu=0, ow=40, oh=40, iw=20, ih=20, r_out=0, r_in=0, bevel=1)
        for p in (PARTS['muzzle_crown'], frame):
            with self.subTest(shape=p['shape']):
                v, f = beveled(p)
                self.solid(v, f)
                original, original_faces = geom._shape(p, [])
                self.assertTrue(geom._sharp_ring_edges(original))
                self.assertLess(geom._volume(v, f), geom._volume(original, original_faces))
                self.assertEqual(ray_hits(v, f, np.array([0., 1., p.get('c', [0])[0]/1000]), np.array([0., -1., 0.])), [])

    def test_octagonal_long_edge_uses_requested_offset_on_outer_and_inner(self):
        p = PARTS['muzzle_crown']; v, f = beveled(p); v = np.asarray(v)
        self.solid(v, f)
        # At the middle's start, radial corner midpoint has the analytic
        # 45-degree rolling-circle setback; the bore's corner gains material.
        b = p['bevel']/1000
        rolling = b/math.tan(math.pi/8)
        decrease = rolling*(1/math.cos(math.pi/8)-1)
        middle = v[np.abs(v[:, 1]+(p['a0']/1000+b)) < 1e-12]
        radii = np.linalg.norm(middle[:, [0, 2]]-[0, p['c'][0]/1000], axis=1)
        for radius in (p['r']/1000-decrease, p['r_in']/1000-decrease):
            self.assertLess(np.abs(radii-radius).min(), 1e-12)

    def test_sharp_ring_large_width_clamps_and_keeps_bore_open(self):
        p = dict(shape='cyl', axis='u', c=[0, 0], a0=0, a1=1, r=10, r_in=9, segs=8, bevel=20)
        v, f = beveled(p)
        self.solid(v, f)
        self.assertEqual(ray_hits(v, f, np.array([0., 0., -.1]), np.array([0., 0., 1.])), [])

    def test_cuts_taper_solid_and_invalid_segments_rejected(self):
        base = dict(shape='cyl', axis='f', c=[0, 0], a0=0, a1=100, r=30, r_in=20, segs=24, bevel=2)
        for extra in (dict(cuts=[dict(shape='box')]), dict(r1=31), dict(r_in=0)):
            self.assertFalse(geom._constant_ring(dict(base, **extra)))
        for segments in (0, -1, 1.5, True):
            with self.assertRaises(geom.GeometryError):
                beveled(base, segments=segments)

    def test_degenerate_and_nonconstant_source_mesh_rejected(self):
        p = PARTS['core_ring']
        v, f = geom._shape(p, []); n = len(v)//4
        v[n][2] += .0001
        with self.assertRaisesRegex(geom.GeometryError, 'Taperprofile'):
            geom._ring_bevel(v, f, .0006, 2)


if __name__ == '__main__':
    unittest.main()
