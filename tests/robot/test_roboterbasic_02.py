"""Vertrag, Geometrie und Offline-Eigenschaften von RoboterBasic-02."""
from __future__ import annotations

import copy
import builtins
import io
import json
import math
import re
import socket
import tomllib
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

from formgen import geom, model
from formgen.models.robot import roboterbasic_01 as basic_01
from formgen.models.robot import roboterbasic_02 as basic_02
from formgen.robot import lines, spec

ROOT = Path(__file__).resolve().parents[2]
SOCKETS_01 = tuple(basic_01.ANCHORS)
MEASURED_MM = np.array([883.877873, 497.176960, 1848.919751])  # Breite X, Tiefe Y, Höhe Z
USER_SHOULDER_INSET_MM = 40.0  # Nutzerkorrektur: beide vorhandenen Schultern je 20 mm zur Mitte
EXPECTED_MODEL_MM = MEASURED_MM.copy()
EXPECTED_MODEL_MM[0] -= USER_SHOULDER_INSET_MM
DIMENSION_TOLERANCE_M = 0.00005
ANCHOR_BOUNDS_TOLERANCE_M = 0.00005  # maximal 0,05 mm Mess-/Rundungstoleranz am Bauteil-AABB


def _size_matches(bounds_m, dimensions_mm=MEASURED_MM):
    low, high = np.asarray(bounds_m, dtype=float)
    np.testing.assert_allclose((high - low) * 1000, dimensions_mm, atol=0.05, rtol=0)


def _check_source_text(text):
    posix_absolute = re.compile(r"(?<![A-Za-z0-9_.-])/(?:[A-Za-z0-9._~-]+/)+[A-Za-z0-9._~-]+")
    quoted_root = re.compile(r"(?P<quote>['\"])/[^'\"]+(?P=quote)")
    windows_absolute = re.compile(r"(?<![A-Za-z0-9_])(?:[A-Za-z]:\\|\\\\[^\\]+\\[^\\]+)")
    windows_text = text.replace('\\\\', '\\')  # escaped Python-/JSON-Strings mit prüfen
    if posix_absolute.search(text) or quoted_root.search(text) or windows_absolute.search(windows_text):
        raise AssertionError('absoluter Pfad im Modell oder Shapes-Datensatz')
    if re.search(r"#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?\b", text):
        raise AssertionError('Farbwert im Modell oder Shapes-Datensatz')


def _check_shape_data(data):
    forbidden = {'color', 'colour', 'rgba', 'rgb'}
    def visit(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if str(key).lower() in forbidden:
                    raise AssertionError(f'Farbfeld {key!r} im Shapes-Datensatz')
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(data)


def _collect_shape_points(shape):
    """Geometrische Kontrollpunkte in FUX-mm, rekursiv für Multi-Formen."""
    points = []
    for key in ('vertices', 'points', 'rings', 'path'):
        if key in shape:
            value = np.asarray(shape[key], dtype=float)
            if value.ndim == 2 and value.shape[1] == 3:
                points.extend(value)
            elif value.ndim == 3 and value.shape[2] == 3:
                points.extend(value.reshape(-1, 3))
    for key in ('items', 'cuts'):
        for child in shape.get(key, []):
            points.extend(_collect_shape_points(child))
    return np.asarray(points, dtype=float).reshape((-1, 3)) if points else np.empty((0, 3))


def _shape_payload(part):
    geometry_keys = {'shape', 'f0', 'f1', 'u0', 'u1', 'w', 'x', 'pts', 'points', 'vertices', 'faces',
                     'rings', 'items', 'cuts', 'path', 'r', 'r1', 'r_in', 'axis', 'c', 'segs'}
    return {k: v for k, v in part.items() if k in geometry_keys}


def _hausdorff_mm(left, right):
    if not len(left) or not len(right):
        raise AssertionError('leere Spiegelgeometrie')
    distances = np.linalg.norm(left[:, None, :] - right[None, :, :], axis=2)
    return max(float(distances.min(axis=1).max()), float(distances.min(axis=0).max()))


def _forearm_spans_fux(points, side='R', params=None):
    """Axial and cross-sectional spans in the parameterized forearm frame."""
    params = basic_02.PARAMS if params is None else params
    frame = basic_02._frames(params)[f'arm_{side}_fore'][0]
    axis_xyz = np.asarray(frame, dtype=float)[:, 2]
    axis = np.array([-axis_xyz[1], axis_xyz[2], axis_xyz[0]], dtype=float)
    axis /= np.linalg.norm(axis)
    seed = np.eye(3)[np.argmin(np.abs(axis))]
    across = np.cross(axis, seed)
    across /= np.linalg.norm(across)
    depth = np.cross(axis, across)
    return np.array([np.ptp(points @ direction) for direction in (axis, across, depth)])


def _assert_mirrors_match(parts, mirror_rows):
    for row in mirror_rows:
        left = _collect_shape_points(parts[row['id']])
        right = _collect_shape_points(parts[row['mirror_of']]).copy()
        right[:, 2] *= -1  # Spiegelung an der Roboter-Mittellinie in FUX (x)
        distance = _hausdorff_mm(left, right)
        if distance > 0.002:
            raise AssertionError(f"{row['id']} gegen {row['mirror_of']}: Hausdorff {distance:.6f} mm")


def _assert_shoulder_width_transport(base, changed, width_delta_mm):
    for side,sign in (('R',-1),('L',1)):
        for pid in (f'torso_{side}_shoulder_block',f'arm_{side}_upper_arm_core'):
            before = _collect_shape_points(base[pid])
            after = _collect_shape_points(changed[pid])
            expected = np.tile([0,0,sign*width_delta_mm/2],(len(before),1))
            np.testing.assert_allclose(after-before,expected,atol=0.002,rtol=0,err_msg=pid)


def _right_arm_donor_01(params):
    raw = model.normalize(basic_01.document(params))
    # Actual articulated chain only. The bespoke torso-mounted shoulder caps are
    # a separate swap target and are deliberately excluded from this contract.
    parts = [p for p in raw['parts'] if p['id'].startswith('arm_R_') and p.get('side') == 'R']
    ids = {p['id'] for p in parts}
    assembly_ids = {p['assembly'] for p in parts}
    donor = copy.deepcopy(raw)
    donor['parts'] = parts
    donor['assemblies'] = [a for a in raw['assemblies'] if a['id'] in assembly_ids]
    donor['anchors'] = {name: anchor for name, anchor in raw['anchors'].items() if anchor['part'] in ids}
    return geom.evaluate(donor)


def _placed_arm(donor, receiver):
    result = copy.deepcopy(donor)
    delta = (np.asarray(receiver['anchors']['Socket_Shoulder_R']['position_m'])
             - np.asarray(donor['anchors']['Socket_Shoulder_R']['position_m']))
    for part in result['parts']:
        vertices = np.asarray(part['mesh']['vertices'], dtype=float) + delta
        part['mesh']['vertices'] = vertices.tolist()
        part['bounds_m'] = [vertices.min(axis=0).tolist(), vertices.max(axis=0).tolist()]
    return result


def _aabb_overlap(left, right):
    return all(left['bounds_m'][0][axis] < right['bounds_m'][1][axis]
               and right['bounds_m'][0][axis] < left['bounds_m'][1][axis] for axis in range(3))


def _arm_swap_intersections(donor, receiver):
    """Return donor/receiver penetration volumes in m³; AABBs skip disjoint pairs."""
    # New contract separates shoulders into their own assembly, but these are
    # body-mounted 02 caps and remain collision targets. Exclude only 02 arm chain IDs.
    recipient_parts = [p for p in receiver['parts'] if not p['id'].startswith('arm_')]
    hits = []
    for donor_part in donor['parts']:
        donor_solid = geom._as_manifold(donor_part['mesh']['vertices'], donor_part['mesh']['faces'])
        for recipient in recipient_parts:
            if not _aabb_overlap(donor_part, recipient):
                continue
            recipient_solid = geom._as_manifold(recipient['mesh']['vertices'], recipient['mesh']['faces'])
            volume = (donor_solid ^ recipient_solid).volume()
            if volume > 1e-9:  # 1 mm³
                hits.append((volume, donor_part['id'], recipient['id']))
    return hits


class RobotBasic02Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = model.load(basic_02)
        cls.doc = geom.evaluate(cls.raw)
        cls.reference_doc = geom.evaluate(model.normalize(basic_02.document(basic_02.REFERENCE_PARAMS)))
        cls.arm_donor_01 = _right_arm_donor_01(basic_01.PARAMS)
        cls.arm_donor_01_reference = _right_arm_donor_01(basic_01.REFERENCE_PARAMS)

    def test_load_and_evaluate_without_blender_network_or_source_blend(self):
        """Laden und Auswerten blockiert Blender, Netzwerkimporte und Blend-Dateizugriffe."""
        real_import = builtins.__import__
        def guarded_import(name, *args, **kwargs):
            if name.split('.', 1)[0] in {'bpy', 'requests', 'urllib', 'http'}:
                raise AssertionError(f'verbotener Laufzeitimport: {name}')
            return real_import(name, *args, **kwargs)

        def allow_repo_path(path):
            resolved = Path(path).resolve()
            if not resolved.is_relative_to(ROOT.resolve()):
                raise AssertionError(f'Resource außerhalb des Repos gesperrt: {resolved}')

        real_path_open, real_io_open, real_builtin_open = Path.open, io.open, builtins.open
        def guarded_path_open(path, *args, **kwargs):
            allow_repo_path(path)
            return real_path_open(path, *args, **kwargs)
        def guarded_io_open(path, *args, **kwargs):
            allow_repo_path(path)
            return real_io_open(path, *args, **kwargs)
        def guarded_builtin_open(path, *args, **kwargs):
            allow_repo_path(path)
            return real_builtin_open(path, *args, **kwargs)
        def blocked_socket_connect(*_args, **_kwargs):
            raise AssertionError('Netzwerkverbindung gesperrt')

        with mock.patch('builtins.__import__', side_effect=guarded_import), \
                mock.patch.object(Path, 'open', guarded_path_open), \
                mock.patch.object(io, 'open', guarded_io_open), \
                mock.patch('builtins.open', side_effect=guarded_builtin_open), \
                mock.patch.object(socket.socket, 'connect', blocked_socket_connect):
            loaded = model.load(basic_02.__file__)
            evaluated = geom.evaluate(loaded)
            for opener in (lambda: Path('/tmp/forbidden.json').open('r'),
                           lambda: io.open('/tmp/forbidden.json', 'r'),
                           lambda: builtins.open('/tmp/forbidden.json', 'r')):
                with self.assertRaisesRegex(AssertionError, 'außerhalb des Repos'):
                    opener()
            sock = socket.socket()
            try:
                with self.assertRaisesRegex(AssertionError, 'Netzwerkverbindung'):
                    sock.connect(('127.0.0.1', 9))
            finally:
                sock.close()
        self.assertEqual(len(evaluated['parts']), 554)
        self.assertGreater(evaluated['counts']['triangles'], 0)
        # Neuer Stand: fünf zusätzliche A-Arm-Freiraumcuts; gedrehte CSG-Netze
        # zählen anders als die Referenz, siehe docs/robot/roboterbasic-02.md.
        self.assertEqual(evaluated['counts']['triangles'], 264549)
        self.assertEqual(self.reference_doc['counts']['triangles'], 260247)

        # Gegenprobe: ein verbotener Import wird vom selben Wächter sicher rot erkannt.
        with mock.patch('builtins.__import__', side_effect=guarded_import):
            with self.assertRaisesRegex(AssertionError, 'bpy'):
                __import__('bpy')
            with self.assertRaisesRegex(AssertionError, 'requests'):
                __import__('requests')

    def test_part_ids_are_unique_and_duplicate_mutation_is_rejected(self):
        ids = [p['id'] for p in self.raw['parts']]
        self.assertEqual(len(ids), len(set(ids)))
        bad = copy.deepcopy(self.raw)
        bad['parts'][1]['id'] = bad['parts'][0]['id']
        with self.assertRaisesRegex(model.ModelError, 'Teile.*eindeutige'):
            model.normalize(bad)
        bad = copy.deepcopy(self.raw)
        bad['assemblies'][1]['id'] = bad['assemblies'][0]['id']
        with self.assertRaisesRegex(model.ModelError, 'Baugruppen.*eindeutige'):
            model.normalize(bad)

    def test_all_roles_are_declared_in_skins_and_unknown_role_is_rejected(self):
        roles = set(tomllib.loads((ROOT / 'skins.toml').read_text())['roles'])
        used = {p['role'] for p in self.raw['parts']}
        self.assertTrue(used <= roles, sorted(used - roles))
        bad = copy.deepcopy(self.doc)
        bad['parts'][0]['role'] = 'role_not_in_skins'
        with self.assertRaisesRegex(ValueError, 'Rollen'):
            lines.check_document(bad)

    def test_assembly_and_socket_names_match_basic_01_contract(self):
        self.assertEqual(self.doc['info']['id'], 'RoboterBasic-02')
        expected = {a['id']: a for a in basic_01.ASSEMBLIES}
        self.assertEqual({a['id'] for a in self.doc['assemblies']}, set(expected))
        self.assertEqual(len(self.doc['assemblies']), 10)
        self.assertEqual({a['group'] for a in self.doc['assemblies']}, {'head', 'upper_body', 'arms', 'legs'})
        for assembly in self.doc['assemblies']:
            self.assertEqual(assembly['group'], expected[assembly['id']]['group'], assembly['id'])
            self.assertEqual(assembly['group_de'], expected[assembly['id']]['group_de'], assembly['id'])
        self.assertEqual(set(self.doc['anchors']), set(SOCKETS_01))
        self.assertEqual(len(self.doc['anchors']), 15)
        bad = copy.deepcopy(self.doc)
        bad['anchors'].pop(SOCKETS_01[-1])
        with self.assertRaisesRegex(ValueError, 'Anker fehlen'):
            lines.check_document(bad)
        bad = copy.deepcopy(self.doc)
        bad['assemblies'][0]['group'] = 'wrong'
        with self.assertRaisesRegex(ValueError, 'Baugruppe'):
            lines.check_document(bad)

    def test_reference_document_marks_measured_geometry_in_spec(self):
        _size_matches(self.reference_doc['bounds_m'], EXPECTED_MODEL_MM)
        entry = dict(line=dict(name='Basic'), type=dict(num=2, name_de='RoboterBasic-02'), skin='weiss_graphit')
        built = spec.build(self.reference_doc, entry)
        expected_measured = sorted(p['id'] for p in self.reference_doc['parts']
                                   if p.get('provenance', {}).get('kind') == 'gemessen')
        self.assertEqual(built['measured_parts'], expected_measured)
        self.assertTrue(built['measured_parts'])

    def test_default_is_a_pose_reference_is_measured_pose_and_shoulder_open_rotates_about_pivot(self):
        default_pose = basic_02.PARAMS['pose']
        reference_pose = basic_02.REFERENCE_PARAMS['pose']
        self.assertEqual(default_pose['origin'], 'Annahme')
        self.assertEqual(reference_pose['origin'], 'gemessen')
        self.assertAlmostEqual(reference_pose['shoulder_open'], 0.0, delta=1e-12)
        np.testing.assert_allclose(default_pose['upper'], basic_01.PARAMS['pose']['upper'], atol=1e-12, rtol=0)
        np.testing.assert_allclose(default_pose['fore'], basic_01.PARAMS['pose']['fore'], atol=1e-12, rtol=0)
        hang = math.degrees(math.atan(basic_02.REFERENCE_PARAMS['pose']['upper'][0]
                                      / basic_02.REFERENCE_PARAMS['pose']['upper'][2]))
        self.assertAlmostEqual(default_pose['shoulder_open'], basic_02.A_ANGLE - hang, delta=1e-12)

        base = {p['id']: p for p in basic_02.parts()}
        params = copy.deepcopy(basic_02.PARAMS)
        params['pose']['shoulder_open'] += 10.0
        opened = {p['id']: p for p in basic_02.parts(params)}
        shoulder_part = 'torso_R_shoulder_block'
        self.assertNotEqual(_shape_payload(base[shoulder_part]), _shape_payload(opened[shoulder_part]))
        self.assertEqual(_shape_payload(base['torso_chest']), _shape_payload(opened['torso_chest']))
        np.testing.assert_allclose(basic_02.anchors(params)['Socket_Shoulder_R']['at'],
                                   basic_02.anchors()['Socket_Shoulder_R']['at'], atol=0.01, rtol=0)
        bad_anchor = np.asarray(basic_02.anchors(params)['Socket_Shoulder_R']['at'], dtype=float) + [0, 1, 0]
        with self.assertRaises(AssertionError):
            np.testing.assert_allclose(bad_anchor, basic_02.anchors()['Socket_Shoulder_R']['at'], atol=0.01, rtol=0)

    def test_anchors_lie_on_their_physical_part_bounds(self):
        parts = {p['id']: p for p in self.doc['parts']}
        def assert_anchors_on_parts(document):
            for name, anchor in document['anchors'].items():
                self.assertIn(anchor['part'], parts, name)
                low, high = (np.asarray(v, dtype=float) for v in parts[anchor['part']]['bounds_m'])
                point = np.asarray(anchor['position_m'], dtype=float)
                gap = np.maximum(np.maximum(low - point, point - high), 0)
                self.assertLessEqual(float(np.linalg.norm(gap)), ANCHOR_BOUNDS_TOLERANCE_M, name)
        assert_anchors_on_parts(self.doc)
        bad = copy.deepcopy(self.doc)
        low, high = (np.asarray(v, dtype=float) for v in parts[bad['anchors']['Socket_Waist']['part']]['bounds_m'])
        bad['anchors']['Socket_Waist']['position_m'][0] = float(high[0] + ANCHOR_BOUNDS_TOLERANCE_M + 0.00001)
        with self.assertRaises(AssertionError):
            assert_anchors_on_parts(bad)

    def test_dimensions_keep_source_depth_height_and_user_corrected_width(self):
        _size_matches(self.reference_doc['bounds_m'], EXPECTED_MODEL_MM)
        bad_bounds = copy.deepcopy(self.reference_doc['bounds_m'])
        bad_bounds[1][0] += 0.0001  # 0.1 mm breiter als die Quelle
        with self.assertRaises(AssertionError):
            _size_matches(bad_bounds, EXPECTED_MODEL_MM)

    def test_model_and_shape_data_have_no_colors_or_absolute_paths(self):
        module_path = Path(basic_02.__file__)
        source_text = module_path.read_text()
        _check_source_text(source_text)
        self.assertEqual(len(basic_02.DATA_FILES), 2)
        for shapes_path in basic_02.DATA_FILES:
            shapes_text = Path(shapes_path).read_text()
            _check_source_text(shapes_text)
            self.assertLess(Path(shapes_path).stat().st_size, 5_000_000)
        _check_shape_data(basic_02._DATA)

        # Gezielte Gegenproben für allgemeine POSIX- und Windows-Absolutpfade.
        _check_source_text("SOURCE = 'robot_v2.blend SHA256 abcdef'")  # relativer Dateiname ist zulässig
        for absolute_path in ('/tmp/foo.json', '/var/cache/item', '/opt/data/source.json',
                              'C:\\temp\\foo.json', '\\\\server\\share\\foo.json'):
            with self.subTest(path=absolute_path), self.assertRaisesRegex(AssertionError, 'absoluter Pfad'):
                _check_source_text(source_text + f"\nSOURCE = {absolute_path!r}")
        with self.assertRaisesRegex(AssertionError, 'Farbwert'):
            _check_source_text(source_text + '\nCOLOR = "#123456"')
        with self.assertRaisesRegex(AssertionError, 'Farbfeld'):
            _check_shape_data({'parts': [{'color': [1, 0, 0]}]})

    def test_measured_mirror_templates_reflect_after_part_generation(self):
        parts = {p['id']: p for p in basic_02.parts()}
        mirror_rows = [row for row in basic_02._DATA['parts'] if 'mirror_of' in row]
        self.assertGreater(len(mirror_rows), 100)
        _assert_mirrors_match(parts, mirror_rows)
        bad = copy.deepcopy(parts)
        row = mirror_rows[0]
        cloud_key = next(k for k in ('vertices', 'points', 'rings') if k in bad[row['id']])
        bad[row['id']][cloud_key][0][2] += 0.01  # 0,01 mm seitlicher Spiegelversatz
        with self.assertRaisesRegex(AssertionError, 'Hausdorff'):
            _assert_mirrors_match(bad, mirror_rows)

    def test_right_arm_from_01_clears_the_02_body_after_shoulder_socket_alignment(self):
        self.assertEqual(len(self.arm_donor_01['parts']), 71)
        self.assertTrue(all(p['id'].startswith('arm_R_') for p in self.arm_donor_01['parts']))
        for donor, receiver, label in ((self.arm_donor_01, self.doc, 'A-Position'),
                                       (self.arm_donor_01_reference, self.reference_doc, 'Referenzhaltung')):
            with self.subTest(stance=label):
                placed = _placed_arm(donor, receiver)
                np.testing.assert_allclose(
                    np.asarray(donor['anchors']['Socket_Shoulder_R']['position_m'])
                    + (np.asarray(receiver['anchors']['Socket_Shoulder_R']['position_m'])
                       - np.asarray(donor['anchors']['Socket_Shoulder_R']['position_m'])),
                    receiver['anchors']['Socket_Shoulder_R']['position_m'], atol=1e-9)
                hits = _arm_swap_intersections(placed, receiver)
                self.assertEqual(hits, [], f'{label}: Armtausch-Penetrationen > 1 mm³: {hits[:8]}')

        # Gegenprobe: ohne die expliziten Freiraum-Cuts muss derselbe Tausch rot werden.
        raw_without_cuts = copy.deepcopy(self.raw)
        cut_parts = [p for p in raw_without_cuts['parts']
                     if p['id'].startswith('torso_R_shoulder_block') and p.get('cuts')]
        self.assertTrue(cut_parts, 'Schulter-Freiraum-Cuts fehlen als Gegenprobenziel')
        for part in cut_parts:
            part.pop('cuts')
        uncut = geom.evaluate(raw_without_cuts)
        uncut_placed = _placed_arm(self.arm_donor_01, uncut)
        self.assertTrue(_arm_swap_intersections(uncut_placed, uncut),
                        'Entfernte Schulter-Freiraum-Cuts müssen die Penetration zurückbringen')

    def test_existing_shoulder_caps_contact_chest_without_added_bridge_parts(self):
        for stance, document in (('Referenzhaltung', self.reference_doc), ('A-Position', self.doc)):
            parts = {p['id']: p for p in document['parts']}
            self.assertFalse(any('shoulder_bridge' in p['id'] for p in document['parts']))
            for side in 'RL':
                cap = parts[f'torso_{side}_shoulder_block']
                chest = parts['torso_chest']
                self.assertTrue(_aabb_overlap(cap, chest), (stance, cap['id'], chest['id']))
                volume_mm3 = (geom._as_manifold(cap['mesh']['vertices'], cap['mesh']['faces'])
                              ^ geom._as_manifold(chest['mesh']['vertices'], chest['mesh']['faces'])).volume() * 1e9
                self.assertGreater(volume_mm3, 100.0, (stance, cap['id'], chest['id'], volume_mm3))

                # Gegenprobe: in der gemessenen Referenzhaltung stellt 20 mm nach außen die Originallücke her.
                if stance == 'Referenzhaltung':
                    detached = copy.deepcopy(cap)
                    sign = -1 if side == 'R' else 1
                    vertices = np.asarray(detached['mesh']['vertices'], dtype=float) + np.array([sign * 0.020, 0.0, 0.0])
                    detached['mesh']['vertices'] = vertices.tolist()
                    detached['bounds_m'] = [vertices.min(axis=0).tolist(), vertices.max(axis=0).tolist()]
                    self.assertFalse(_aabb_overlap(detached, chest), detached['id'])

        # Schulterbreite verschiebt nur die vorhandenen Mounts; die Brustform bleibt gleich.
        params = copy.deepcopy(basic_02.PARAMS)
        params['dimensions']['shoulder_width'] += 40
        source_parts = {p['id']: p for p in basic_02.parts()}
        wider = {p['id']: p for p in basic_02.parts(params)}
        self.assertEqual(_shape_payload(source_parts['torso_chest']), _shape_payload(wider['torso_chest']))

    def test_shoulder_pivot_is_stable_and_width_moves_sockets_symmetrically(self):
        base = basic_02.anchors()
        for side, x in (('R', -0.280000042), ('L', 0.280000042)):
            self.assertAlmostEqual(base[f'Socket_Shoulder_{side}']['at'][2], x * 1000, delta=0.01)

        params = copy.deepcopy(basic_02.PARAMS)
        params['pose']['upper'] = list(params['pose']['upper'])
        params['pose']['upper'][0] += 0.12
        posed = basic_02.anchors(params)
        for name in ('Socket_Shoulder_R', 'Socket_Shoulder_L'):
            np.testing.assert_allclose(posed[name]['at'], base[name]['at'], atol=0.01, rtol=0)

        params = copy.deepcopy(basic_02.PARAMS)
        params['dimensions']['shoulder_width'] += 40
        wider = basic_02.anchors(params)
        self.assertAlmostEqual(wider['Socket_Shoulder_R']['at'][2] - base['Socket_Shoulder_R']['at'][2], -20.0, delta=0.01)
        self.assertAlmostEqual(wider['Socket_Shoulder_L']['at'][2] - base['Socket_Shoulder_L']['at'][2], 20.0, delta=0.01)

    def test_height_parameter_scales_head_about_ground(self):
        params = copy.deepcopy(basic_02.PARAMS)
        params['dimensions']['height'] += 40.0
        changed = geom.evaluate(model.normalize(basic_02.document(params)))
        base_head_top = max(p['bounds_m'][1][2] for p in self.doc['parts'] if p['assembly'] == 'head')
        changed_head_top = max(p['bounds_m'][1][2] for p in changed['parts'] if p['assembly'] == 'head')
        expected_top = base_head_top * (params['dimensions']['height'] / basic_02.PARAMS['dimensions']['height'])
        self.assertAlmostEqual(changed_head_top, expected_top, delta=0.00001)
        self.assertAlmostEqual(changed['bounds_m'][0][2], 0.0, delta=0.000001)
        self.assertEqual({p['id'] for p in changed['parts']}, {p['id'] for p in self.doc['parts']})
        with self.assertRaises(AssertionError):  # Gegenprobe: 1 mm Zusatzhub ist außerhalb der Messgleichung.
            self.assertAlmostEqual(changed_head_top + 0.001, expected_top, delta=0.00001)

    def test_arm_length_extends_forearm_without_scaling_its_thickness(self):
        base = {p['id']: p for p in basic_02.parts()}
        params = copy.deepcopy(basic_02.PARAMS)
        params['dimensions']['arm_length'] += 40.0
        longer = {p['id']: p for p in basic_02.parts(params)}
        base_spans = _forearm_spans_fux(_collect_shape_points(base['arm_R_forearm_core']), params=basic_02.PARAMS)
        longer_spans = _forearm_spans_fux(_collect_shape_points(longer['arm_R_forearm_core']), params=params)
        self.assertGreater(longer_spans[0], base_spans[0] + 20.0)
        np.testing.assert_allclose(longer_spans[1:], base_spans[1:], atol=0.05, rtol=0)
        bad = longer_spans.copy()
        bad[1] += 0.1
        with self.assertRaises(AssertionError):
            np.testing.assert_allclose(bad[1:], base_spans[1:], atol=0.05, rtol=0)

    def test_arm_bulk_only_changes_arm_parts_and_pose_changes_arm_frames(self):
        for module, fore_core, upper_core in (
            (basic_01, 'arm_R_fore_body', 'arm_R_upper_core'),
            (basic_02, 'arm_R_forearm_core', 'arm_R_upper_arm_core'),
        ):
            with self.subTest(module=module.__name__):
                base = {p['id']: p for p in module.parts()}
                params = copy.deepcopy(module.PARAMS)
                params['arm_bulk'] += 0.15
                bulk = {p['id']: p for p in module.parts(params)}
                changed_ids = {pid for pid in base if _shape_payload(base[pid]) != _shape_payload(bulk[pid])}
                expected_fore_ids = {pid for pid, part in base.items()
                                     if part.get('segment', '').endswith('_fore')
                                     or part.get('segment', '').startswith('forearm_')}
                self.assertEqual(changed_ids, expected_fore_ids)
                self.assertNotEqual(_shape_payload(base[fore_core]), _shape_payload(bulk[fore_core]))
                self.assertEqual(_shape_payload(base[upper_core]), _shape_payload(bulk[upper_core]))
                # Hände und alle Fingersegmente behalten ihre Geometrie.
                for pid, part in base.items():
                    segment = part.get('segment', '').lower()
                    if any(token in segment for token in ('hand', 'finger', 'thumb', 'fingertip', 'fingermid')):
                        self.assertEqual(_shape_payload(part), _shape_payload(bulk[pid]), pid)

        base = {p['id']: p for p in basic_02.parts()}
        params = copy.deepcopy(basic_02.PARAMS)
        params['pose']['upper'] = list(params['pose']['upper'])
        params['pose']['upper'][0] += 0.12
        posed = {p['id']: p for p in basic_02.parts(params)}
        self.assertNotEqual(_shape_payload(base['arm_R_upper_arm_core']), _shape_payload(posed['arm_R_upper_arm_core']))

    def test_shoulder_width_leg_length_and_head_neck_parameters_affect_their_parts(self):
        base = {p['id']: p for p in basic_02.parts()}
        params = copy.deepcopy(basic_02.PARAMS)
        params['dimensions']['shoulder_width'] += 40
        wider = {p['id']: p for p in basic_02.parts(params)}
        self.assertEqual(_shape_payload(base['torso_chest']), _shape_payload(wider['torso_chest']))
        _assert_shoulder_width_transport(base,wider,40)
        frozen = copy.deepcopy(wider)
        frozen['torso_R_shoulder_block'] = copy.deepcopy(base['torso_R_shoulder_block'])
        with self.assertRaises(AssertionError):  # Gegenprobe: fehlerhaft eingefrorene Kappe im geänderten Modell.
            _assert_shoulder_width_transport(base,frozen,40)

        params = copy.deepcopy(basic_02.PARAMS)
        params['dimensions']['leg_length'] += 40
        longer_legs = {p['id']: p for p in basic_02.parts(params)}
        legs = [pid for pid, p in base.items() if p['assembly'] in {'thighs', 'shins', 'feet'}]
        base_u = np.concatenate([_collect_shape_points(base[pid])[:, 1] for pid in legs])
        longer_u = np.concatenate([_collect_shape_points(longer_legs[pid])[:, 1] for pid in legs])
        self.assertGreater(np.ptp(longer_u), np.ptp(base_u))

        params = copy.deepcopy(basic_02.PARAMS)
        params['head']['neck'] += 8
        thicker_neck = {p['id']: p for p in basic_02.parts(params)}
        neck_ids = [pid for pid, p in base.items() if p['assembly'] == 'head' and 'neck' in pid.lower()]
        self.assertTrue(neck_ids)
        self.assertTrue(any(_shape_payload(base[pid]) != _shape_payload(thicker_neck[pid]) for pid in neck_ids),
                        'head.neck muss die gemessenen Halsbauteile beeinflussen')


if __name__ == '__main__':
    unittest.main()
