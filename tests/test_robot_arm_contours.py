"""Registered casing dimensions without changing source arms or their rig."""
import unittest
import numpy as np
from scipy.spatial import ConvexHull

from formgen.models.figures.r01_parts import arms


def section(points, height, sign=1):
    values=[]
    for i,a in enumerate(points):
        if abs(a[1]-height)<1e-9:
            values.append(sign*a[2])
        for b in points[i+1:]:
            if (a[1]-height)*(b[1]-height)<=0 and abs(b[1]-a[1])>1e-9:
                values.append(sign*(a[2]+(b[2]-a[2])*(height-a[1])/(b[1]-a[1])))
    return min(values),max(values)


class ArmContourTests(unittest.TestCase):
    def raw(self, pid, side):
        entry=next(p for p in arms.SOURCE.parts() if p[0]==pid)
        _,_,segment,kind,_,parameters=entry
        return arms.convert(kind,parameters,arms.SEGMENT_FRAMES[side+'_'+segment],
                            arms.LENGTH_SCALE[segment])['points']

    def authored(self,pid,side):
        return next(p['points'] for p in arms.PARTS if p['id']==f'arms_{pid}_{side}')

    def test_upper_width_matches_both_references_without_shifting_section_center(self):
        for side,sign in (('r',-1),('l',1)):
            before=[];after=[]
            for pid in ('upper_body','upper_shell'):
                raw=self.raw(pid,side)
                before.extend([[f,u,x-sign*arms.UPPER_CASING_MEDIAL_MM] for f,u,x in raw])
                points=self.authored(pid,side);after.extend(points)
                np.testing.assert_array_equal(np.asarray(points)[:len(raw),:2],np.asarray(raw)[:,:2])
                def projection_hull(values):
                    fu=np.unique(np.asarray(values)[:,:2],axis=0)
                    return set(map(tuple,fu[ConvexHull(fu).vertices]))
                self.assertEqual(projection_hull(points),projection_hull(raw))
            lo,hi=section(before,1450,sign);a,b=section(after,1450,sign)
            self.assertGreaterEqual(b-a,118)
            self.assertLessEqual(b-a,122)
            self.assertLess(abs((a+b-lo-hi)/2),2)

    def test_upper_cheek_adds_active_mirrored_supports_preserving_medial_edge(self):
        variants=[]
        for side,sign in (('r',-1),('l',1)):
            raw=self.raw('upper_shell',side)
            base=[[f,u,x-sign*arms.UPPER_CASING_MEDIAL_MM] for f,u,x in raw]
            base=arms._upper_casing_width(base,sign)
            points=self.authored('upper_shell',side)
            np.testing.assert_array_equal(points[:len(base)],base)
            self.assertEqual(len(points)-len(base),7)
            active=set(ConvexHull(points).vertices)
            self.assertTrue(set(range(len(base),len(points))).issubset(active))
            for height in range(1320,1511,10):
                lo,hi=section(base,height,sign);a,b=section(points,height,sign)
                self.assertAlmostEqual(a,lo,places=9)
                if height>=1450:self.assertAlmostEqual(b,hi,places=9)
            self.assertAlmostEqual(section(points,1350,sign)[1]-section(base,1350,sign)[1],8)
            variants.append(np.asarray(points)*[1,1,sign])
        np.testing.assert_allclose(*variants,atol=1e-9)

    def test_forearm_keeps_complete_original_core_and_side_projection(self):
        for side in ('r','l'):
            raw=self.raw('fore_body',side);points=self.authored('fore_body',side)
            self.assertTrue(set(map(tuple,raw)).issubset(set(map(tuple,points))))
            self.assertEqual({tuple(p[:2]) for p in raw},{tuple(p[:2]) for p in points})

    def test_forearm_medial_extension_preserves_outer_contour(self):
        for side,sign in (('r',-1),('l',1)):
            raw=self.raw('fore_body',side);points=self.authored('fore_body',side)
            for height in range(1100,1251,10):
                inner,outer=section(raw,height,sign);a,b=section(points,height,sign)
                self.assertAlmostEqual(outer,b,places=9)
                self.assertGreaterEqual(inner-a,-1e-9)
                self.assertLessEqual(inner-a,20+1e-9)
            self.assertGreater(section(raw,1220,sign)[0]-section(points,1220,sign)[0],10)
