"""Foot construction regressions; visual acceptance remains a separate gate."""
import json
import unittest
from collections import Counter

import numpy as np

from formgen import geom
from formgen.models.figures.r01_parts import legs


def _coplanar_triangle_overlap_mm2(a, b):
    """Intersect actual coplanar triangles; shared edges have zero area."""
    na, nb = np.cross(a[1]-a[0],a[2]-a[0]), np.cross(b[1]-b[0],b[2]-b[0])
    na, nb = na/np.linalg.norm(na), nb/np.linalg.norm(nb)
    if abs(float(na@nb)) < 1-1e-10 or np.max(abs((b-a[0])@na)) > 1e-8:
        return 0.0
    axis = int(np.argmax(abs(na)))
    polygon, clip = np.delete(a,axis,axis=1).tolist(), np.delete(b,axis,axis=1).tolist()
    def cross(a,b,c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    orientation = 1 if cross(*clip)>0 else -1
    for p,q in zip(clip,clip[1:]+clip[:1]):
        result = []
        for x,y in zip(polygon,polygon[1:]+polygon[:1]):
            dx, dy = orientation*cross(p,q,x), orientation*cross(p,q,y)
            if dx>=-1e-10:
                result.append(x)
            if (dx < -1e-10)!=(dy < -1e-10):
                t = dx/(dx-dy)
                result.append([u+t*(v-u) for u,v in zip(x,y)])
        polygon = result
        if len(polygon)<3:
            return 0.0
    projected = abs(sum(x[0]*y[1]-x[1]*y[0]
                        for x,y in zip(polygon,polygon[1:]+polygon[:1])))/2
    return projected/abs(na[axis])


class RobotFootGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = {p['id']: p for p in legs.PARTS}
        document = geom.evaluate(dict(
            info=dict(id='R01_FEET', kind='figure', name_de='Füße'),
            parts=[p for p in legs.PARTS if '_foot_' in p['id']],
            assemblies=[dict(id='legs', de='Beine')]))
        # Reconstruct from the exact serialized artifact, rather than checking
        # a native CSG result whose exported/reimported triangles can differ.
        cls.parts = {p['id']: p for p in json.loads(json.dumps(document))['parts']}

    def test_actual_three_piece_armor_replaces_the_old_dark_overlay(self):
        for side in ('r', 'l'):
            self.assertNotIn('legs_foot_instep_'+side, self.source)
            core = self.source['legs_foot_core_'+side]
            self.assertEqual(core['shape'], 'surface')
            self.assertNotIn('cuts', core)
            for name in ('toe', 'heel', 'instep'):
                part = self.source['legs_foot_'+name+'_shell_'+side]
                self.assertEqual(part['wall_mm'], 5)
                vertices = np.array(part['vertices'])
                outer, inner = np.split(vertices, 2)
                expected = np.array([5 if name=='heel' else -5, 0, 0])
                np.testing.assert_allclose(inner-outer, np.tile(expected,(len(outer),1)))
                envelope = geom._shape(part, [])
                self.assertGreater(geom._volume(*envelope), 0)

    def test_mirroring_preserves_the_actual_canonical_triangle_surfaces(self):
        for name in ('core', 'toe_shell', 'heel_shell', 'instep_shell'):
            def triangles(side):
                mesh = self.parts['legs_foot_'+name+'_'+side]['mesh']
                vertices = np.array(mesh['vertices'])
                if side=='r':
                    vertices[:,0] *= -1
                return {tuple(sorted(tuple(np.round(vertices[i],12)) for i in face))
                        for face in mesh['faces']}
            self.assertEqual(triangles('r'), triangles('l'), name)

    def test_heel_union_has_no_coplanar_overlaps_or_internal_u145_caps(self):
        for side in ('r','l'):
            part = self.source['legs_foot_heel_shell_'+side]
            vertices = np.asarray(part['vertices'])
            triangles = vertices[part['faces']]
            overlaps = []
            for i,a in enumerate(triangles):
                for j in range(i+1,len(triangles)):
                    b = triangles[j]
                    if np.any(a.max(axis=0)<b.min(axis=0)-1e-8) or np.any(b.max(axis=0)<a.min(axis=0)-1e-8):
                        continue
                    area = _coplanar_triangle_overlap_mm2(a,b)
                    if area>1e-7:
                        overlaps.append((i,j,area))
            self.assertEqual(overlaps,[],side)
            seam = triangles[np.all(abs(triangles[:,:,1]-145)<1e-8,axis=1)]
            self.assertGreater(len(seam),0,side)
            # Only the real central window roof needs a cap at this height.
            # Neighboring upper/lower armor fields share an uninterrupted wall.
            x = abs(seam[:,:,2])
            self.assertGreaterEqual(float(x.min()),202-1e-8,side)
            self.assertLessEqual(float(x.max()),300+1e-8,side)
            area = np.linalg.norm(np.cross(seam[:,1]-seam[:,0],
                                           seam[:,2]-seam[:,0]),axis=1).sum()/2
            self.assertAlmostEqual(float(area),98*5,places=6,msg=side)

    @unittest.skipIf(geom._manifold is None, 'manifold3d optional')
    def test_all_three_exported_panels_clear_the_positive_core(self):
        for side in ('r', 'l'):
            solids = {}
            for name in ('core', 'toe_shell', 'heel_shell', 'instep_shell'):
                mesh = self.parts['legs_foot_'+name+'_'+side]['mesh']
                vertices = np.array(mesh['vertices'])
                triangles = vertices[geom._triangulate(vertices,mesh['faces'])]
                area = np.linalg.norm(np.cross(triangles[:,1]-triangles[:,0],
                                               triangles[:,2]-triangles[:,0]),axis=1)/2
                self.assertGreater(float(area.min()), 1e-14, name)
                edges = Counter(tuple(sorted((a,b))) for face in mesh['faces']
                                for a,b in zip(face,face[1:]+face[:1]))
                self.assertTrue(all(count==2 for count in edges.values()), name)
                solid = geom._as_manifold(mesh['vertices'],mesh['faces'])
                self.assertEqual(str(solid.status()), 'Error.NoError', name)
                self.assertGreater(solid.volume(), 0, name)
                # A second independent export/import must retain validity and
                # volume; the former instep regression appeared at this boundary.
                rebuilt = geom._as_manifold(*geom._from_manifold(solid))
                self.assertAlmostEqual(rebuilt.volume(),solid.volume(),places=13)
                solids[name] = rebuilt
            for name in ('toe_shell', 'heel_shell', 'instep_shell'):
                self.assertLess(abs((solids['core'] ^ solids[name]).volume()),
                                1e-12, side+'/'+name)
            for a,b in (('toe_shell','heel_shell'),('toe_shell','instep_shell'),
                        ('heel_shell','instep_shell')):
                self.assertLess(abs((solids[a] ^ solids[b]).volume()),1e-12,side+'/'+a+'/'+b)


if __name__ == '__main__':
    unittest.main()
