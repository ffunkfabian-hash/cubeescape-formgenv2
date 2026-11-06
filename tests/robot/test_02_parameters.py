"""Isolated semantic-profile hooks: no Blender or source workstation needed."""
from copy import deepcopy
import unittest

import numpy as np

from formgen import geom
from formgen.models.robot import roboterbasic_01 as one
from formgen.models.robot import roboterbasic_02 as two
from formgen.models.robot import roboterbasic_02_parameters as profiles
from formgen.robot import lines


class ParameterProfilesTests(unittest.TestCase):
    def setUp(self):
        self.defaults = dict(two.PARAMS, **profiles.extras())

    def changed(self, path, value):
        params = deepcopy(self.defaults)
        target = params
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        return profiles.templates(params, self.defaults, two._TEMPLATES, two._BASE_FRAMES)

    def test_default_is_exact_identity_and_every_01_key_merges(self):
        self.assertIs(profiles.templates(self.defaults, self.defaults, two._TEMPLATES, two._BASE_FRAMES),
                      two._TEMPLATES)
        # This traverses every dict key and therefore exercises merge's strict
        # existing-key contract, including complete nested profiles.
        merged = lines.merge(self.defaults, one.PARAMS)
        for key in one.PARAMS:
            self.assertEqual(merged[key], one.PARAMS[key])

    def test_associations_are_resolvable_and_have_measured_nonempty_profiles(self):
        canonical = profiles._canonical(self.defaults)
        measured = profiles.measurements(two._TEMPLATES, two._BASE_FRAMES)
        for row in two._TEMPLATES:
            key = profiles.binding(row)
            if key:
                self.assertIn(key, canonical)
                low, high = measured[(key, profiles._segment(row))]
                self.assertTrue(np.all(high > low))
                self.assertTrue(np.isfinite(low).all())

    def test_middle_profile_changes_source_surface_locally(self):
        rows = deepcopy(self.defaults['torso']['core'])
        rows[2] = tuple(v + (16 if i == 1 else 0) for i, v in enumerate(rows[2]))
        result = self.changed(('torso', 'core'), rows)
        old = next(r for r in two._TEMPLATES if r['source_object'] == 'TorsoCore')
        new = next(r for r in result if r['source_object'] == 'TorsoCore')
        a, b = profiles._cloud(old), profiles._cloud(new)
        self.assertEqual(a.shape, b.shape)
        self.assertGreater(float(np.linalg.norm(a - b, axis=1).max()), 1)
        displacement = np.linalg.norm(a - b, axis=1)
        self.assertGreater(float(np.ptp(displacement)), 0.01)

    def test_shell_thickness_and_slots_change_measured_chest(self):
        for path, value in [(('torso', 'chest', 't'), 20),
                            (('torso', 'chest', 'vents'), (290, 310, 330))]:
            with self.subTest(path=path):
                result = self.changed(path, value)
                new = next(r for r in result if r['source_object'] == 'Chest')
                old = next(r for r in two._TEMPLATES if r['source_object'] == 'Chest')
                self.assertNotEqual(new, old)
                if path[-1] == 'vents':
                    self.assertGreater(len(new['cuts']), 0)

    def test_switches_remove_source_and_build_absent_features(self):
        without_calf = self.changed(('legs', 'calf'), False)
        self.assertFalse(any(r['source_object'].startswith('CalfInsert') for r in without_calf))
        with_lights = self.changed(('legs', 'lights'), True)
        lamps = [r for r in with_lights if r.get('parameter_feature', '').startswith('legs.shin_light')]
        self.assertEqual(len(lamps), 4)
        self.assertEqual(sum(r['role'] == 'energy' for r in lamps), 2)
        self.assertTrue(all(len(profiles._cloud(r)) > 0 for r in lamps))
        with_arm = self.changed(('arm_drop',), ())
        self.assertEqual(len([r for r in with_arm if r.get('parameter_feature', '').startswith('arm.upper_')]), 4)

    def test_accessories_inherit_same_bone_profile_and_follow_foot(self):
        associated = profiles.associate(two._TEMPLATES)
        for row in associated:
            if row['bone'] not in ('head', 'neck') and not row['bone'].startswith(('finger', 'thumb')):
                self.assertIsNotNone(profiles.binding(row))
        accessory = next(r for r in associated if r['source_object'] == 'R2_AnkleBearing_R')
        self.assertIn('profile_owner', accessory)
        owner = next(r for r in associated if r['id'] == accessory['profile_owner'])
        self.assertEqual(owner['bone'], accessory['bone'])
        foot = deepcopy(self.defaults['legs']['foot'])
        foot = [(z, a + 16, b + 12, offset) for z, a, b, offset in foot]
        changed = self.changed(('legs', 'foot'), foot)
        result = next(r for r in changed if r['id'] == accessory['id'])
        self.assertGreater(float(np.linalg.norm(profiles._cloud(result) - profiles._cloud(accessory))), 0.1)

    def test_changed_profile_shapes_and_cuts_really_evaluate(self):
        core = [(z, a + 8, b + 5, offset) for z, a, b, offset in self.defaults['torso']['core']]
        upper = [(z, a + 10, b + 6, offset) for z, a, b, offset in self.defaults['upper_arm']['rows']]
        source = {r['id']: r for r in two._TEMPLATES}
        cases = [(('torso', 'core'), core), (('upper_arm', 'rows'), upper),
                 (('torso', 'chest', 'vents'), (290, 310, 330)), (('legs', 'lights'), True)]
        for path, value in cases:
            with self.subTest(path=path):
                changed = [deepcopy(r) for r in self.changed(path, value)
                           if r['id'] not in source or profiles._cloud(r).tolist() != profiles._cloud(source[r['id']]).tolist()
                           or r.get('cuts') != source[r['id']].get('cuts')]
                self.assertGreater(len(changed), 0)
                for row in changed:
                    row.pop('parent_part', None)  # isolated shapes have no assembly ancestors
                    row.update(bevel=0, provenance=dict(kind='Annahme', source='Isolierte Profil-Geometriepruefung'))
                document = dict(info=dict(id='profile-check', kind='figure'), parts=changed,
                                assemblies=[dict(id=a) for a in sorted({r['assembly'] for r in changed})])
                evaluated = geom.evaluate(document)
                self.assertEqual(evaluated['counts']['parts'], len(changed))
                self.assertGreater(evaluated['counts']['triangles'], 0)
                self.assertEqual(evaluated['warnings'], [])
                for part in evaluated['parts']:
                    self.assertGreater(part['counts']['vertices'], 3)
                    self.assertGreater(part['counts']['triangles'], 3)

    def test_removing_vents_restores_real_source_chest_material(self):
        measured = next(r for r in two._TEMPLATES if r['source_object'] == 'Chest')
        self.assertIn('pre_boolean_shape', measured)
        self.assertIn('source_boolean_cuts', measured)
        rows = self.changed(('torso', 'chest', 'vents'), ())
        restored = next(r for r in rows if r['source_object'] == 'Chest')
        self.assertFalse(any(r['source_object'].startswith('ChestVent') for r in rows))
        replaced = restored['parameter_boolean_rebuild']['replaced_source_cutters']
        self.assertIn('CUT_ChestSlots_L', replaced)
        self.assertIn('CUT_ChestSlots_R', replaced)
        self.assertGreater(len(restored.get('cuts', [])), 0)  # source seam/pockets remain
        def volume(source):
            part = deepcopy(source)
            part.pop('parent_part', None)
            part.update(bevel=0, provenance=dict(kind='Annahme', source='Gemessene Ventil-Volumenpruefung'))
            evaluated = geom.evaluate(dict(info=dict(id='vent-volume', kind='figure'),
                                           parts=[part], assemblies=[dict(id=part['assembly'])]))
            self.assertEqual(evaluated['warnings'], [])
            mesh = evaluated['parts'][0]['mesh']
            return geom._as_manifold(mesh['vertices'], mesh['faces']).volume()
        before, after = volume(measured), volume(restored)
        self.assertGreater(after - before, 1e-9)  # m^3, actual material regained

    def test_new_shoulder_grooves_cut_material_and_preserve_source_pockets(self):
        self.assertEqual(self.defaults['torso']['pauldron']['grooves'], ())
        result = self.changed(('torso', 'pauldron', 'grooves'), (312, 326, 340))
        untagged_templates = deepcopy(two._TEMPLATES)
        for owner in untagged_templates:
            if owner['source_object'] in ('ShoulderBlock_R', 'ShoulderBlock_L'):
                for cut in owner.get('cuts', []):
                    cut.pop('interface_clearance', None)
        params = deepcopy(self.defaults)
        params['torso']['pauldron']['grooves'] = (312, 326, 340)
        untagged_result = profiles.templates(params, self.defaults, untagged_templates, two._BASE_FRAMES)
        for name in ('ShoulderBlock_R', 'ShoulderBlock_L'):
            with self.subTest(owner=name):
                measured = next(r for r in two._TEMPLATES if r['source_object'] == name)
                changed = next(r for r in result if r['source_object'] == name)
                untagged = next(r for r in untagged_result if r['source_object'] == name)
                self.assertEqual(changed['parameter_boolean_rebuild']['replaced_source_cutters'], [])
                source_interfaces = [c for c in measured.get('cuts', []) if c.get('interface_clearance')]
                rebuilt_interfaces = [c for c in changed['cuts'] if c.get('interface_clearance')]
                self.assertEqual(len(source_interfaces), 1)
                self.assertEqual(len(rebuilt_interfaces), 1)
                self.assertEqual(len(changed['cuts']), len(measured['source_boolean_cuts']) + 3 + len(source_interfaces))
                self.assertEqual(len(untagged['cuts']), len(changed['cuts']) - 1)
                self.assertFalse(any(c.get('interface_clearance') for c in untagged['cuts']))
                volumes = []
                for source in (measured, changed):
                    part = deepcopy(source)
                    part.pop('parent_part', None)
                    part.update(bevel=0, provenance=dict(kind='Annahme', source='Gemessene Fugen-Volumenpruefung'))
                    evaluated = geom.evaluate(dict(info=dict(id='groove-volume', kind='figure'),
                                                   parts=[part], assemblies=[dict(id=part['assembly'])]))
                    self.assertEqual(evaluated['warnings'], [])
                    mesh = evaluated['parts'][0]['mesh']
                    volumes.append(geom._as_manifold(mesh['vertices'], mesh['faces']).volume())
                self.assertGreater(volumes[0] - volumes[1], 1e-9)

    def test_existing_shoulder_ball_changes_without_adding_parts(self):
        result = self.changed(('upper_arm', 'ball'), 66)
        self.assertEqual(len(result), len(two._TEMPLATES))
        before = {r['source_object']: r for r in two._TEMPLATES}
        for row in result:
            if row['source_object'].startswith('ShoulderJoint'):
                self.assertNotEqual(profiles._cloud(row).tolist(), profiles._cloud(before[row['source_object']]).tolist())

    def test_new_shoulder_flares_calibrate_at_the_measured_shoulders(self):
        flare = deepcopy(profiles._REFERENCE['torso']['pauldron']['flare'])
        result = self.changed(('torso', 'pauldron', 'flare'), flare)
        added = [r for r in result if r.get('parameter_feature', '').startswith('torso.pauldron')]
        self.assertEqual(len(added), 8)
        for row in added:
            self.assertTrue(row['id'].startswith('torso_profile_pauldron_'))
            self.assertTrue(row['profile_calibration_source'].startswith('ShoulderBlock_'))
            shoulder = next(r for r in two._TEMPLATES if r['source_object'] == row['profile_calibration_source'])
            shoulder_center = profiles._cloud(shoulder).mean(axis=0)
            feature_center = profiles._cloud(row).mean(axis=0)
            self.assertLess(float(np.linalg.norm(feature_center - shoulder_center)), 250)
            self.assertEqual(row['bone'], shoulder['bone'])

    def test_new_flares_follow_current_shoulder_mount_and_width(self):
        params = deepcopy(two.PARAMS)
        params['torso']['pauldron']['flare'] = deepcopy(profiles._REFERENCE['torso']['pauldron']['flare'])
        templates = profiles.templates(params, two.PARAMS, two._TEMPLATES, two._BASE_FRAMES)
        additions = [r for r in templates if r.get('parameter_feature', '').startswith('torso.pauldron')]
        before = {r['id']: r for r in two.parts(params)}
        wider = deepcopy(params)
        wider['dimensions']['shoulder_width'] += 40
        after = {r['id']: r for r in two.parts(wider)}
        measured = {r['source_object']: r for r in two._TEMPLATES}
        self.assertEqual(len(additions), 8)
        for row in additions:
            with self.subTest(feature=row['id']):
                owner = measured[row['profile_calibration_source']]
                self.assertEqual(row['mount_frame'], owner['mount_frame'])
                self.assertEqual(row.get('frame'), owner.get('frame'))
                self.assertEqual(row.get('length_scale'), owner.get('length_scale'))
                self.assertEqual(row.get('parent_part'), owner.get('parent_part'))
                def center(part):
                    return profiles._cloud(part).mean(axis=0)
                old_relative = center(before[row['id']]) - center(before[owner['id']])
                new_relative = center(after[row['id']]) - center(after[owner['id']])
                np.testing.assert_allclose(new_relative, old_relative, atol=2e-6, rtol=0)
                self.assertGreater(float(np.linalg.norm(center(after[owner['id']]) - center(before[owner['id']]))), 15)

    def test_reactivated_upper_arm_bulk_matches_01_without_scaling_replacements_or_hands(self):
        # Both Basic types apply bulk to restored arm-v3 upper parts. Their
        # body.upper_arm replacements and hands retain their independent sizes.
        for module in (one, two):
            with self.subTest(model=module.__name__):
                params = deepcopy(module.PARAMS)
                params.update(arm_drop=(), arm_bulk=1.0)
                enlarged = deepcopy(params)
                enlarged['arm_bulk'] = 1.5
                base = {r['id']: r for r in module.parts(params)}
                bulky = {r['id']: r for r in module.parts(enlarged)}
                frames = one.rig_of(params)[1] if module is one else two._frames(params)
                for side in 'RL':
                    R = frames[f'arm_{side}_upper'][0]
                    names = ((f'arm_{side}_upper_body', f'arm_{side}_upper_shell') if module is one else
                             (f'arm_{side}_upper_profile_upper_body', f'arm_{side}_upper_profile_upper_shell'))
                    for name in names:
                        before = np.ptp(profiles._cloud(base[name]) @ R[:, :2], axis=0)
                        after = np.ptp(profiles._cloud(bulky[name]) @ R[:, :2], axis=0)
                        np.testing.assert_allclose(after / before, [1.5, 1.5], atol=3e-6, rtol=0)
                stable = ([f'arm_{side}_{part}' for side in 'RL' for part in ('upper_core', 'upper_shell_r', 'palm')]
                          if module is one else
                          [r['id'] for r in base.values() if r['source_object'] in
                           ('UpperArmCore_R', 'UpperArmCore_L', 'UpperArm_R', 'UpperArm_L', 'Palm_R', 'Palm_L')])
                self.assertGreaterEqual(len(stable), 6)
                for name in stable:
                    np.testing.assert_array_equal(profiles._cloud(base[name]), profiles._cloud(bulky[name]))

    def test_legacy_inert_01_fields_are_visible_diagnostics(self):
        changed = deepcopy(self.defaults)
        changed['torso']['chest']['tip'] += 10
        changed['torso']['chest']['plate'] += 10
        self.assertEqual(len(profiles.warnings(changed, self.defaults)), 2)
        self.assertEqual(profiles.warnings(self.defaults, self.defaults), [])

    def test_numeric_changes_keep_ids_deterministic_and_finite(self):
        for path, value in [(('upper_arm', 'ball'), 75), (('pelvis', 'hip_r'), 65),
                            (('legs', 'knee_ch'), 12), (('torso', 'pauldron', 'tilt'), 24)]:
            with self.subTest(path=path):
                first, second = self.changed(path, value), self.changed(path, value)
                self.assertEqual(first, second)
                self.assertEqual(len({r['id'] for r in first}), len(first))
                for row in first:
                    self.assertTrue(np.isfinite(profiles._cloud(row)).all())


if __name__ == '__main__':
    unittest.main()
