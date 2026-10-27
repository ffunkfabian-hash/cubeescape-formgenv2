"""Pure geometry checks for the leg assembly; no visual acceptance claim."""
import json
import unittest
from collections import Counter

import numpy as np
from scipy.spatial import ConvexHull

from formgen import geom
from formgen.models.figures.r01_parts import legs


class RobotLegGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = geom.evaluate(dict(
            info=dict(id='R01_LEGS',kind='figure',name_de='Beine',provenance=legs.PROVENANCE),
            parts=legs.PARTS,assemblies=[dict(id='legs',de='Beine')],anchors=legs.ANCHORS))

    def test_closed_positive_shells_and_export(self):
        json.dumps(self.document,allow_nan=False)
        self.assertFalse(self.document['warnings'])
        for p in self.document['parts']:
            mesh=p['mesh']
            edge=Counter(tuple(sorted((a,b))) for face in mesh['faces']
                         for a,b in zip(face,face[1:]+face[:1]))
            self.assertTrue(all(n==2 for n in edge.values()),p['id'])
            v=geom._volume(mesh['vertices'],mesh['faces'])
            self.assertGreater(v,0,p['id'])
            if 'wall_mm' in p:
                # A shell must leave substantial interior volume; a solid
                # loft painted cream does not satisfy the shell contract.
                envelope=ConvexHull(np.array(mesh['vertices'])).volume
                self.assertLess(v,envelope*.35,p['id'])

    def test_symmetry_ground_and_nonemissive_joints(self):
        parts={p['id']:p for p in self.document['parts']}
        for key,p in parts.items():
            if key.endswith('_r'):
                r=np.array(p['mesh']['vertices']); l=np.array(parts[key[:-1]+'l']['mesh']['vertices'])
                r[:,0]*=-1
                # Boolean triangulation may reorder vertices.
                self.assertEqual({tuple(np.round(v,9)) for v in r},
                                 {tuple(np.round(v,9)) for v in l},key)
            if 'ring' in key or 'disc' in key:
                self.assertIn(p['role'],('dark_metal','anodized'))
        self.assertAlmostEqual(self.document['bounds_m'][0][2],0)
        for side in ('R','L'):
            self.assertEqual(legs.ANCHORS['Socket_Knee_'+side]['at'][1],710)
            self.assertEqual(legs.ANCHORS['Socket_Ankle_'+side]['at'][1],234)

    def test_hip_housing_keeps_bearing_anchor_and_side_circle(self):
        parts = {p['id']: p for p in legs.PARTS}
        for side, sign in (('r', -1), ('l', 1)):
            axis = parts['legs_hip_axis_'+side]
            rings = np.asarray(axis['rings'])
            # The medial cylinder and complete f/u bearing circle survive;
            # only the outer housing shoulder is sloped toward its cap.
            self.assertEqual(sign*rings[0, 0, 2], 82)
            np.testing.assert_allclose(rings[0, :, :2], rings[1, :, :2])
            np.testing.assert_allclose(np.linalg.norm(rings[0, :, :2]-[45,1080], axis=1), 72)
            np.testing.assert_allclose(np.linalg.norm(rings[2, :, :2]-[45,1080], axis=1), 20)
            self.assertEqual(sign*rings[2, 0, 2], 212)
            self.assertEqual(legs.ANCHORS['Socket_Hip_'+side.upper()]['at'], [45,1080,sign*142])

    def test_upper_hip_projection_approaches_both_measured_contours(self):
        parts = {p['id']: p for p in self.document['parts']}
        # Each tuple contains both sides of the Front/Back source masks.
        # These are improvement checks, not a new acceptance tolerance.
        samples = ((1120, (198.6,200.1,189.6,199.1), 212),
                   (1130, (179.1,180.7,169.6,178.5), 212),
                   (1140, (168.5,169.1,160.6,168.5), 212),
                   (1150, (157,157,154.8,161.7), 202))
        for side in ('r', 'l'):
            for height, reference, previous in samples:
                crossings = []
                for key in ('hip_axis', 'hip_socket'):
                    mesh = parts['legs_'+key+'_'+side]['mesh']
                    vertices = np.asarray(mesh['vertices'])*1000
                    for face in mesh['faces']:
                        for ia, ib in zip(face, face[1:]+face[:1]):
                            a, b = vertices[ia], vertices[ib]
                            if min(a[2], b[2]) <= height <= max(a[2], b[2]) and abs(a[2]-b[2]) > 1e-10:
                                t = (height-a[2])/(b[2]-a[2])
                                crossings.append(abs(a[0]+t*(b[0]-a[0])))
                width = max(crossings)
                for target in reference:
                    self.assertLess(abs(width-target), abs(previous-target))

    @unittest.skipIf(geom._manifold is None, 'manifold3d optional')
    def test_hip_socket_is_thick_open_and_physically_seated(self):
        source = {p['id']: p for p in legs.PARTS}
        meshes = {p['id']: p['mesh'] for p in self.document['parts']}
        def solid(key):
            mesh = meshes[key]
            return geom._as_manifold(mesh['vertices'], mesh['faces'])
        for side in ('r', 'l'):
            part = source['legs_hip_socket_'+side]
            points = np.asarray(part['vertices'])
            n = len(points)//4
            radial = np.linalg.norm(points[:, :2]-[45,1080], axis=1)
            self.assertAlmostEqual(float(radial.min()), 45)
            self.assertAlmostEqual(float(radial.max()), 68)
            normal = np.cross(points[1]-points[0], points[n]-points[0])
            normal /= np.linalg.norm(normal)
            self.assertAlmostEqual(abs(float(np.dot(points[0]-points[3*n], normal))), 8)
            socket = solid('legs_hip_socket_'+side)
            axis = solid('legs_hip_axis_'+side)
            self.assertGreater((socket ^ axis).volume(), 1e-8)
            self.assertGreater((socket-axis).volume(), 1e-8)
            self.assertGreater((axis ^ solid('legs_thigh_core_'+side)).volume(), 1e-8)
            # A true central bore remains in the ring part, rather than a
            # painted annulus over a full disk or a disconnected decoration.
            sign = -1 if side == 'r' else 1
            bore = dict(shape='cyl', axis='x', c=[45,1080],
                        a0=sign*140, a1=sign*205, r=40, segs=32)
            self.assertLess(abs((socket ^ geom._as_manifold(*geom._shape(bore, []))).volume()), 1e-12)
            for key in ('legs_hip_axis_'+side, 'legs_hip_socket_'+side):
                mesh = meshes[key]
                vertices = np.asarray(mesh['vertices'])
                triangles = vertices[geom._triangulate(vertices, mesh['faces'])]
                area2 = np.linalg.norm(np.cross(triangles[:, 1]-triangles[:, 0],
                                                triangles[:, 2]-triangles[:, 0]), axis=1)
                self.assertTrue(np.all(area2 > 1e-16), key)
                self.assertEqual(str(solid(key).status()), 'Error.NoError')

    def test_hidden_cores_do_not_pierce_shell_walls(self):
        # The former independent octagons cut 118,000..281,000 mm³ out
        # of each thigh wall and made dark stripes across the cream skin.
        # Check real mesh intersection, including the foot and link ends;
        # matching only profile extrema misses the folded cheek surfaces.
        meshes={p['id']:p['mesh'] for p in self.document['parts']}
        def solid(key):
            mesh=meshes['legs_'+key]
            return geom._as_manifold(mesh['vertices'],mesh['faces'])
        for side in ('r','l'):
            for limb, panels in (('thigh',('front','rear')),
                                 ('shin',('front','rear')),
                                 ('foot',('toe','heel'))):
                for panel in panels:
                    name=f'{limb}_{panel}_shell_{side}'
                    overlap=solid(f'{limb}_core_{side}') ^ solid(name)
                    # Manifold uses float32 metre coordinates. At foot
                    # folds its residual is <0.05 mm³; permit 1 mm³.
                    self.assertLess(abs(overlap.volume()),1e-9,name)
            for link, limb, panels in (('knee_lower_link','shin',('front','rear')),
                                       ('ankle_link','foot',('toe','heel'))):
                for panel in panels:
                    overlap=solid(f'{link}_{side}') ^ solid(f'{limb}_{panel}_shell_{side}')
                    self.assertLess(abs(overlap.volume()),1e-9,f'{link}_{side}/{panel}')
