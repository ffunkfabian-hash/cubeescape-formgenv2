"""Pose kinematics and coarse solid clearance; no raster/image acceptance."""
from copy import deepcopy
import json
import unittest

import numpy as np

from formgen import geom, model
from formgen.models.figures import r01_basic_robot as robot, r01_poses as pose
from formgen.models.figures.r01_parts import arms
from formgen.models.weapons import w01_auto_rifle as weapon


def posed(document):
    result = deepcopy(document)
    transforms = document['poses']['ready']['part_transforms']
    for part in result['parts']:
        if part['id'] in transforms:
            matrix = transforms[part['id']]
            vertices = [pose.transform_point(matrix,p) for p in part['mesh']['vertices']]
            part['mesh']['vertices'] = vertices
            part['bounds_m'] = np.asarray(vertices).min(axis=0).tolist(),np.asarray(vertices).max(axis=0).tolist()
    return result


def overlap(a,b):
    return all(a['bounds_m'][0][i] < b['bounds_m'][1][i]
               and b['bounds_m'][0][i] < a['bounds_m'][1][i] for i in range(3))


def intersection(a,b):
    if not overlap(a,b):
        return 0.
    return (geom._as_manifold(a['mesh']['vertices'],a['mesh']['faces'])
            ^ geom._as_manifold(b['mesh']['vertices'],b['mesh']['faces'])).volume()


class RobotPoseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = model.normalize(robot)
        source['anchors']['Socket_Hand_R'] = pose.hand_socket()
        source['poses'] = pose.build_poses(source['parts'],source['anchors'])
        cls.document = geom.evaluate(source,bevels=False)
        cls.ready = posed(cls.document)
        cls.weapon = geom.evaluate(model.normalize(weapon),bevels=False)
        cls.placed = pose.evaluated_attachment(cls.weapon,cls.document)

    def test_idle_identity_and_only_right_arm_changes_rigidly(self):
        definition = self.document['poses']
        self.assertEqual(definition['idle']['part_transforms'],{})
        transforms = definition['ready']['part_transforms']
        expected = {p['id'] for p in arms.PARTS if p['arm_side']=='r'}
        self.assertEqual(set(transforms),expected)
        for matrix in transforms.values():
            rotation = np.asarray(matrix)[:3,:3]
            np.testing.assert_allclose(rotation.T@rotation,np.eye(3),atol=1e-12)
            self.assertAlmostEqual(np.linalg.det(rotation),1.)
        by_id = {p['id']:p for p in self.ready['parts']}
        for part in self.document['parts']:
            if part['id'] not in transforms:
                self.assertEqual(part['mesh'],by_id[part['id']]['mesh'])
        self.assertNotEqual(self.document['parts'],self.ready['parts'])
        json.dumps(definition,allow_nan=False)

    def test_all_joints_remain_connected_with_source_lengths(self):
        frames = pose.ready_frames()
        for group,length,next_group in [('r_upper',arms.UPPER_MM,'r_fore'),
                                        ('r_fore',arms.FORE_MM,'r_hand')]:
            frame = frames[group]
            endpoint = np.asarray(frame['at'])+np.asarray(frame['basis'][2])*length
            np.testing.assert_allclose(endpoint,frames[next_group]['at'],atol=1e-10)
        for i in range(4):
            for j in range(2):
                frame=frames[f'r_f{i}_{j}']
                endpoint=np.asarray(frame['at'])+np.asarray(frame['basis'][2])*arms.SOURCE.FINGER_LINKS[j]*arms.SOURCE.FINGER_SCALE[i]*arms.HAND_SCALE
                np.testing.assert_allclose(endpoint,frames[f'r_f{i}_{j+1}']['at'],atol=1e-10)
        for j in range(2):
            frame=frames[f'r_t_{j}']
            endpoint=np.asarray(frame['at'])+np.asarray(frame['basis'][2])*arms.SOURCE.THUMB_LINKS[j]*arms.HAND_SCALE
            np.testing.assert_allclose(endpoint,frames[f'r_t_{j+1}']['at'],atol=1e-10)
        np.testing.assert_allclose(frames['r_upper']['at'],arms.SHOULDER_R)

    def test_socket_colocation_and_attachment_is_pure(self):
        anchor = self.document['anchors']['Socket_Hand_R']
        matrix = self.document['poses']['ready']['part_transforms'][anchor['part']]
        target = pose.transform_point(matrix,anchor['position_m'])
        np.testing.assert_allclose(target,self.placed['anchors']['Socket_Hand']['position_m'],atol=1e-12)
        np.testing.assert_allclose(target,pose._xyz(pose.READY_WEAPON_SOCKET),atol=1e-12)
        self.assertNotEqual(anchor['at'],arms.WRIST_R)
        before = deepcopy(self.weapon)
        pose.evaluated_attachment(self.weapon,self.document)
        self.assertEqual(self.weapon,before)
        muzzle=self.placed['anchors']['Socket_Muzzle']['position_m']
        self.assertLess(muzzle[1],target[1]-.6)

    @unittest.skipIf(geom._manifold is None,'solid contact checks require manifold3d')
    def test_grip_thumb_and_index_really_reach_weapon(self):
        parts = {p['id']:p for p in self.ready['parts']}
        weapon_parts = {p['id']:p for p in self.placed['parts']}
        for hand_part,weapon_part in [('arms_palm_r','grip'),('arms_f1_2_core_r','grip'),
                                      ('arms_t_1_core_r','grip'),('arms_f0_1_core_r','trigger')]:
            self.assertGreater(intersection(parts[hand_part],weapon_parts[weapon_part]),1e-10,
                               (hand_part,weapon_part))

    @unittest.skipIf(geom._manifold is None,'solid clearance checks require manifold3d')
    def test_weapon_clear_of_torso_head_and_arm_shells(self):
        protected = [p for p in self.ready['parts']
                     if p['assembly'] in ('upper_body','lower_body','head')
                     or p.get('group') in ('r_upper','r_fore')]
        for weapon_part in self.placed['parts']:
            for robot_part in protected:
                self.assertLessEqual(intersection(weapon_part,robot_part),1e-10,
                                     (weapon_part['id'],robot_part['id']))
        # A surface touch is fragile even if the intersection volume is zero.
        # The revised upper-arm roll needs an actual millimetre of clearance.
        upper=next(p for p in self.ready['parts'] if p['id']=='arms_upper_body_r')
        stock=next(p for p in self.placed['parts'] if p['id']=='butt_pad')
        a=geom._as_manifold(upper['mesh']['vertices'],upper['mesh']['faces'])
        b=geom._as_manifold(stock['mesh']['vertices'],stock['mesh']['faces'])
        self.assertGreater(a.min_gap(b,.01),.001)

    def test_missing_grip_datum_fails_instead_of_using_wrist(self):
        with self.assertRaisesRegex(ValueError,'Griffdatum'):
            pose.build_poses(arms.PARTS,arms.ANCHORS)
        with self.assertRaisesRegex(ValueError,'Waffenreferenz'):
            pose.evaluated_attachment(dict(info=dict(id='OTHER')),self.document)


if __name__ == '__main__':
    unittest.main()
