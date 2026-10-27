"""Analytical open AUTO-Bezier centerline checks; no pixels or Blender."""
import unittest

import numpy as np

from formgen.curves import auto_bezier_points


class AutoBezierTests(unittest.TestCase):
    def test_straight_span_collinear_monotonic_and_exact_endpoints(self):
        samples=auto_bezier_points([[1,2,3],[11,22,33]])
        self.assertEqual(samples.shape,(13,3))
        np.testing.assert_array_equal(samples[[0,-1]],[[1,2,3],[11,22,33]])
        np.testing.assert_allclose(samples[6],[6,12,18],atol=1e-14)
        delta=samples-[1,2,3]
        np.testing.assert_allclose(delta[:,1],2*delta[:,0],atol=1e-14)
        np.testing.assert_allclose(delta[:,2],3*delta[:,0],atol=1e-14)
        self.assertTrue(np.all(np.diff(samples[:,0])>0))

    def test_curved_path_passes_every_knot_without_duplicate_spans(self):
        points=np.array([[0,0,0],[1,1,0],[2,0,1],[4,1,3]],float)
        before=points.copy()
        samples=auto_bezier_points(points,resolution=7)
        self.assertEqual(samples.shape,(22,3))
        np.testing.assert_array_equal(samples[::7],points)
        np.testing.assert_array_equal(points,before)
        self.assertTrue(np.all(np.linalg.norm(np.diff(samples,axis=0),axis=1)>0))
        np.testing.assert_array_equal(samples,auto_bezier_points(points,7))

    def test_unequal_chord_clamp_matches_analytical_midpoint(self):
        # Chord lengths100 and1: the incoming middle handle is limited to
        # 5/2.5614 along the diagonal tangent, rather than100/2.5614.
        samples=auto_bezier_points([[0,0,0],[100,0,0],[100,1,0]],resolution=2)
        h=5/(2.5614*np.sqrt(2))
        # Cubic at t=1/2 with first handle(100/2.5614,0),
        # second handle(100-h,-h), and endpoints(0,0)/(100,0).
        expected=[.375*(100/2.5614+100-h)+12.5,-.375*h,0]
        np.testing.assert_allclose(samples[1],expected,rtol=0,atol=1e-13)
        # Reversing an open path must reverse its samples, including clamp.
        reverse=auto_bezier_points([[100,1,0],[100,0,0],[0,0,0]],2)
        np.testing.assert_allclose(reverse[::-1],samples,rtol=0,atol=1e-13)

    def test_right_angle_auto_is_smooth_and_not_a_polyline(self):
        points=[[0,0,0],[1,0,0],[1,1,0]]
        samples=auto_bezier_points(points,2)
        diagonal=1/(2.5614*np.sqrt(2))
        np.testing.assert_allclose(samples[1],
            [.375*(1/2.5614+1-diagonal)+.125,-.375*diagonal,0],atol=1e-14)
        self.assertLess(samples[1,1],0)
        np.testing.assert_array_equal(samples[2],points[1])

    def test_reversal_collapses_middle_handles_without_nan(self):
        samples=auto_bezier_points([[0,0,0],[1,0,0],[0,0,0]])
        self.assertTrue(np.isfinite(samples).all())
        np.testing.assert_array_equal(samples[12],[1,0,0])
        self.assertTrue(np.all((samples[:,0]>=0)&(samples[:,0]<=1)))

    def test_resolution_one_and_invalid_inputs(self):
        points=[[0,0,0],[1,2,3],[2,1,4]]
        np.testing.assert_array_equal(auto_bezier_points(points,1),points)
        for resolution in (0,-1,2.5,True,'12'):
            with self.assertRaisesRegex(ValueError,'resolution'):
                auto_bezier_points(points,resolution)
        for points in ([],[[0,0,0]],[[0,0],[1,1]],
                       [[0,0,0],[0,0,0]],[[0,0,0],[np.nan,0,1]]):
            with self.assertRaises(ValueError):
                auto_bezier_points(points)
