"""Parametervertrag fuer gemessene 02-Teile, rein numerisch und ohne Blender.

Die Referenzwerte sind Vorgabe01 (BALLON 14bd78d); sie sind KEINE
Messbehauptung ueber 02. Die individuelle 02-Grundform und ihre Profilmasse
kommen ausschliesslich aus den Kontrollpunkten der gemessenen Quellrows.
Eine Profilzuordnung kalibriert die Referenzform auf diese Messung; Aenderungen
werden als Verschiebungsfeld in mm uebertragen. Damit ist der Default exakt
identisch und keine gemeinsame Skelett-, Pose- oder Bulk-Skalierung doppelt.
Neue konstruktive Features verwenden denselben body/arm-Baukasten wie 01.
Die Zuordnung ist eine explizite Entwurfsannahme, keine Quellenmessung.
"""
from __future__ import annotations

from copy import deepcopy

import numpy as np

from formgen import geom
from . import arm, body, catalog, kit

PROVENANCE = {
    'reference': 'Vorgabe01: BALLON 14bd78d; Parameter und Einheiten aus RoboterBasic-01',
    'calibration': 'gemessen: lokale Kontrollpunkte jeder 02-Quellteilfamilie, roboterbasic_02_shapes.json und _shapes_2.json',
    'association': 'Annahme: deklarative Zuordnung semantisch gleicher Teile und lokal interpolierter Verschiebungstransport',
}

_REFERENCE = {'arm_drop': ('upper_body', 'upper_shell'),
 'upper_arm': {'rows': [(10, 62, 60, 0), (150, 70, 68, 2), (290, 56, 54, 0)],
               'ball': 60,
               'shell': (-110, 110),
               'ch': 20},
 'torso': {'core': [(30, 112, 88, -2),
                    (120, 150, 106, 0),
                    (230, 192, 122, -4),
                    (280, 204, 118, -6),
                    (330, 176, 106, -8),
                    (380, 120, 88, -10)],
           'core_ch': 44,
           'waist': (86, 68),
           'abdomen': 'plates',
           'waist_pistons': True,
           'lights': True,
           'gorget': (372, 140, 108, 12),
           'bridges': (176, 352, 190, 14),
           'collar': [(360, 132, 98, -10), (410, 104, 86, -8), (428, 92, 80, -8)],
           'chest': {'a': (-74, 74),
                     'full': 170,
                     'tip': 118,
                     'mid': (240, 300),
                     'top': 352,
                     't': 12,
                     'plate': 226,
                     'stripe': 280,
                     'emblem': True,
                     'vents': (306, 318, 330)},
           'back': {'kind': 'pack',
                    'z': (150, 220, 350),
                    'y': -150,
                    'nozzle_x': 66,
                    'rows': [(150, 112, 52, 0), (200, 132, 62, -6), (300, 136, 64, -8), (360, 110, 50, -4)]},
           'SX': 276,
           'SZ': 300,
           'joint_r': 58,
           'pauldron': {'rows': [(250, 104, 124, -6, 40),
                                 (290, 120, 134, -6, 30),
                                 (340, 118, 130, -6, 12),
                                 (375, 98, 112, -6, -4),
                                 (392, 60, 76, -6, -14)],
                        'flare': [(180, 116, 132, -6, 50), (256, 100, 116, -6, 40)],
                        'flare2': [(120, 104, 120, -6, 56), (196, 92, 108, -6, 48)],
                        'flare_span': 112,
                        'band': 260,
                        'med': (272, 26),
                        'stripes': True,
                        'tilt': 16,
                        'ch': 34,
                        'grooves': (312, 326, 340)}},
 'pelvis': {'pel': [(-30, 140, 94, -2), (50, 154, 100, -2), (130, 124, 86, -2), (190, 100, 76, -2)],
            'belt': (118, 146, 128, 90),
            'front': {'full': 20, 'tip': -90, 'a': 30},
            'side': {'rows': [(-110, 236, 118, -4), (-20, 200, 108, -4), (110, 168, 100, -4)],
                     'span': 32,
                     'layer': True,
                     'center': 80},
            'hip_x': 120,
            'hip_z': 40,
            'hip_r': 50,
            'butt': True,
            'belt_boxes': True,
            'pel_ch': 34},
 'legs': {'LT': 395,
          'LS': 385,
          'foot_h': 112,
          'thigh_ch': 26,
          'shin_ch': 24,
          'knee_ch': 20,
          'thigh': [(-12, 76, 82, 0), (110, 94, 100, 2), (280, 84, 88, 0), (395, 66, 70, 0)],
          'thigh_shell': (-112, 34),
          'thigh_seams': (200,),
          'knee_r': 56,
          'kneecap': [(-64, 54, 60), (-20, 64, 70), (36, 66, 72), (80, 60, 66)],
          'shin': [(30, 72, 76, 0), (140, 82, 88, -4), (280, 68, 72, -2), (385, 58, 60, 0)],
          'shin_shell': (-96, 96),
          'calf': True,
          'ankle_pistons': True,
          'lights': True,
          'ankle_r': 40,
          'foot': [(-100, 64, 44, -66),
                   (-30, 70, 56, -56),
                   (70, 72, 48, -64),
                   (160, 66, 34, -78),
                   (222, 54, 22, -88)]}}


def extras():
    """01-Schluessel, Referenzmasse in mm/Grad; 02-Schalter nach vorhandenen Teilen.

    Fehlende Features starten ausgeschaltet und werden bei Aktivierung gebaut.
    Die Profilzahlen sind deklarierte Referenzkoordinaten, keine erfundenen
    02-Messwerte. ``measurements`` liefert die tatsaechlichen 02-Profilgrenzen.
    """
    out = catalog.options(deepcopy(_REFERENCE))
    out.update(forearm=deepcopy(arm.FOREARM), hand=deepcopy(arm.HAND))     # 0.14: Unterarm- und Handmaße wie RA01 (arm.py)
    out['torso'].update(waist_pistons=False, gorget=None, bridges=None)
    out['torso']['pauldron'].update(flare=None, flare2=None, stripes=False, grooves=())
    out['pelvis']['belt_boxes'] = False
    out['pelvis']['side']['layer'] = False
    out['legs']['lights'] = False
    return out


# First matching prefix wins. The targets are actual body.py/arm.py part IDs,
# rather than a second list of parameter interpretations. Decorations travel
# with the same parent profile, preserving the source assembly and role.
# A trailing {s} is the lowercase anatomical side in body.py IDs.
ASSOCIATIONS = (
    ('UpperArmCore', 'upper_core'), ('UpperArm', 'upper_shell_r'),
    ('ElbowCable', 'upper_core'), ('ElbowInnerRing', 'elbow_ring'),
    ('ElbowInnerCap', 'elbow_disc'), ('ElbowMed', 'elbow_hub'), ('Elbow_', 'elbow'),
    ('ForearmCore', 'fore_body'), ('ForearmInnerPlate', 'fore_top'),
    ('ForearmPlate', 'fore_top'), ('ForearmBolt1', 'fore_bolt_a'), ('ForearmBolt2', 'fore_bolt_b'),
    ('Forearm', 'fore_shell'), ('WristCuff', 'fore_cuff'), ('Palm', 'palm'),
    ('HandPlate', 'back_plate'),
    ('ShoulderBlockLower', 'pauldron_{s}_band'), ('ShoulderBlockCore', 'shoulder_{s}_axle'),
    ('ShoulderBlock', 'pauldron_{s}'), ('ShoulderBolt', 'pauldron_{s}'),
    ('ShoulderMed', 'shoulder_{s}_med_disc'), ('ShoulderJoint', 'shoulder_ball'),
    ('Backpack', 'backpack'), ('RefBackMount', 'backpack_shell'), ('RefBackPanel', 'backpack_shell'),
    # 0.14: alle Back*-Teile außer Backpack sitzen gemessen auf dem Rückenmodul (f −302…−177 mm, Rumpfrücken bei −130), nicht auf einer
    # Rückenplatte; an `back` gebunden blieben sie bei Linien ohne Rückenmodul 160 mm hinter dem Rumpf in der Luft stehen.
    ('BackSpine', 'backpack_shell'), ('Back', 'backpack_shell'), ('Hose', 'pack_cable_{s}'),
    ('R5_SensorLightRing', 'chest_light_r_lamp'),
    ('R5_Sensor', 'emblem_disc'), ('Sensor', 'emblem_disc'),
    ('ChestVent', 'chest'), ('ChestSeam', 'chest'), ('ChestBand', 'chest_stripe_a'),
    ('ChestChevron', 'solar'), ('Chest', 'chest'), ('RibStripe', 'solar'), ('RibPlate', 'rib_r'),
    ('TorsoCore', 'torso_core'), ('Collar', 'collar'), ('AbPlate_Lower', 'abs_a'), ('AbPlate_Upper', 'abs_b'),
    ('SpineRing', 'waist_core'), ('Waist', 'waist_core'),
    ('PelvisCore', 'pelvis_core'), ('BeltBuckle', 'buckle'), ('BuckleSlot', 'buckle_inset'),
    ('BuckleTongue', 'buckle'), ('BeltBolt', 'belt'), ('Belt', 'belt'),
    ('CodGroove', 'tasset'), ('Codpiece', 'tasset'), ('Seat', 'butt'),
    ('HipJoint', 'hip_{s}_axle'), ('HipMed', 'hip_{s}_disc'),
    ('ThighCore', 'thigh_core'), ('ThighPlate', 'thigh_seam_0'),
    ('ThighHatch', 'thigh_shell'), ('ThighBolt', 'thigh_shell'),
    ('ThighTrim', 'thigh_cuff_trim'), ('Thigh_', 'thigh_shell'),
    ('KneePiston', 'knee_axle'), ('KneeCable', 'thigh_core'),
    ('KneeGroove', 'knee_cap'), ('KneeBolt', 'knee_cap'), ('Knee_', 'knee_cap'),
    ('KneeCore', 'knee_axle'), ('KneeJoint', 'knee_axle'), ('KneeMed', 'knee_disc'),
    ('CalfInsert', 'calf'), ('ShinChevron', 'shin_plate'), ('ShinBolt', 'shin_bolt_a'),
    ('Shin_', 'shin_shell'), ('AnkleCore', 'ankle_axle'), ('AnkleInsert', 'boot_cuff'),
    ('AnklePistonRod', 'ankle_piston_a_rod'), ('AnklePiston', 'ankle_piston_a_cyl'),
    ('BootSole', 'sole'), ('BootHeel', 'heel_cap'), ('BootToe', 'toe_cap'),
    ('BootAnkle', 'foot_core'), ('BootBolt', 'toe_cap'), ('ToeSeam', 'toe_cap'),
    ('R4_ToeBumper', 'toe_cap'),
)


PACK_DETAILS = ('OrangeDetail_6',)      # gemessen f −298…−292 mm: Akzent auf dem Rückenmodul, nicht auf der Brust (0.14)


def warnings(params, defaults):
    """Visible inherited 01 contract gaps; the protected 01 is not reinterpreted."""
    return [f'01-Parameter torso.chest.{key} aktuell ohne Formwirkung; geschuetztes 01 unveraendert'
            for key in ('tip', 'plate')
            if params['torso']['chest'][key] != defaults['torso']['chest'][key]]


def _side(row):
    return 'L' if row['bone'].endswith('_L') else 'R'


def binding(row):
    """Return (constructor family, semantic part), or None for head/finger data.

    Head and finger geometry already follows head/pose/skeleton in the caller;
    it must not receive a second deformation here.
    """
    if row.get('profile_binding'):
        return tuple(row['profile_binding'])
    name = row['source_object']
    if name in PACK_DETAILS:
        return ('torso', 'backpack_shell')
    if name.startswith('OrangeDetail'):
        return ('pelvis', 'tasset_stripe_a') if row['assembly'] == 'lower_body' else ('torso', 'chest_stripe_a')
    for prefix, target in ASSOCIATIONS:
        if name.startswith(prefix):
            pid = target.format(s=_side(row).lower())
            if prefix.startswith(('UpperArm', 'ElbowCable', 'ShoulderJoint')):
                family = 'upper_arm'
            elif target in {'fore_body', 'fore_top', 'fore_bolt_a', 'fore_bolt_b', 'fore_shell',
                            'fore_cuff', 'palm', 'back_plate', 'elbow_ring', 'elbow_disc', 'elbow_hub', 'elbow'}:
                family = 'arm'
            elif row['assembly'] == 'upper_body' or name.startswith(('AbPlate', 'SpineRing', 'Waist', 'Collar', 'Shoulder')):
                family = 'torso'
            elif name.startswith(('HipJoint', 'HipMed')) or row['assembly'] == 'lower_body':
                family = 'pelvis'
            else:
                family = 'legs'
            return family, pid
    return None


# Only the structural owner receives new boolean cuts. Bolts, vent inserts,
# seams and other decorations follow its field without being cut a second time.
CUT_OWNERS = {
    ('torso', 'chest'): ('Chest',),
    ('torso', 'pauldron_r'): ('ShoulderBlock_R',),
    ('torso', 'pauldron_l'): ('ShoulderBlock_L',),
}


# Source cutters are measured BEFORE boolean evaluation. Named groups replace
# only the corresponding editable feature; unrelated source pockets survive.
BOOLEAN_GROUPS = {
    ('torso', 'chest'): dict(group='vents', source_prefixes=('CUT_ChestSlots_L', 'CUT_ChestSlots_R')),
    ('torso', 'pauldron_r'): dict(group='grooves', source_prefixes=()),
    ('torso', 'pauldron_l'): dict(group='grooves', source_prefixes=()),
}
_GEOMETRY = ('shape', 'points', 'vertices', 'faces', 'rings', 'items', 'cuts')


def _cut_layout_changed(key, params, defaults):
    if key == ('torso', 'chest'):
        return params['torso']['chest']['vents'] != defaults['torso']['chest']['vents']
    if key in (('torso', 'pauldron_r'), ('torso', 'pauldron_l')):
        return params['torso']['pauldron']['grooves'] != defaults['torso']['pauldron']['grooves']
    return False


def _geometry_replaced(row, shape):
    out = {key: deepcopy(value) for key, value in row.items() if key not in _GEOMETRY}
    out.update({key: deepcopy(value) for key, value in shape.items() if key in _GEOMETRY})
    return out


def _rebuild_boolean_owner(row, key, new, params, deform, measured):
    if 'pre_boolean_shape' not in row or 'source_boolean_cuts' not in row:
        raise ValueError(f"{row['id']}: geaenderte Schnittgeometrie braucht gemessene pre_boolean_shape und source_boolean_cuts")
    group = BOOLEAN_GROUPS[key]
    base = _map(_geometry_replaced(row, row['pre_boolean_shape']), deform)
    preserved = []
    replaced_names = []
    for cut in row['source_boolean_cuts']:
        name = cut.get('source_object', '')
        belongs = cut.get('parameter_group') == group['group'] or any(name.startswith(prefix) for prefix in group['source_prefixes'])
        if belongs:
            replaced_names.append(name)
        else:
            preserved.append(_map({k: v for k, v in cut.items() if k in _GEOMETRY}, deform))
    # Constructive socket pockets are independent of editable decoration cuts.
    # Keep these data-marked pockets when rebuilding a source owner for grooves.
    preserved.extend(_map(cut, deform) for cut in row.get('cuts', [])
                     if cut.get('interface_clearance'))
    cuts = new.get('cuts', [])
    if key == ('torso', 'chest'):
        # body.torso emits right/left vent slots first, then its own notch/seam.
        # The measured source notch/seam are retained instead of being doubled.
        cuts = cuts[:2 * len(params['torso']['chest']['vents'])]
    base['cuts'] = preserved + [_map(cut, measured) for cut in cuts]
    base['parameter_boolean_rebuild'] = dict(group=group['group'], replaced_source_cutters=replaced_names)
    return base


def associate(rows):
    """Attach unbound accessories to measured owners in the same source bone.

    An explicit measured parent wins. Otherwise distance between source AABBs
    and then their centers selects the nearest declared profile owner; ID is the
    deterministic tie breaker. Head and finger rows remain in their own pose
    path. No source coordinates, IDs, roles or assemblies change.
    """
    by_id = {row['id']: row for row in rows}
    candidates = {}
    boxes = {}
    for row in rows:
        if binding(row) is not None:
            candidates.setdefault(row['bone'], []).append(row)
            cloud = _cloud(row)
            boxes[row['id']] = (cloud.min(axis=0), cloud.max(axis=0))
    out = []
    for row in rows:
        if binding(row) is not None or row['bone'] in ('head', 'neck') or row['bone'].startswith(('finger', 'thumb')):
            out.append(row)
            continue
        owners = candidates.get(row['bone'], [])
        if not owners:
            raise ValueError('Keine Profilzuordnung fuer Quellbone ' + row['bone'])
        parent, visited = row.get('parent_part'), set()
        chosen = None
        while parent and parent not in visited:
            visited.add(parent)
            candidate = by_id.get(parent)
            if candidate is None or candidate['bone'] != row['bone']:
                break
            if binding(candidate) is not None:
                chosen = candidate
                break
            parent = candidate.get('parent_part')
        if chosen is None:
            cloud = _cloud(row)
            low, high = cloud.min(axis=0), cloud.max(axis=0)
            center = (low + high) / 2
            def distance(candidate):
                a, b = boxes[candidate['id']]
                separation = np.maximum(np.maximum(a - high, low - b), 0)
                return (float(separation @ separation), float(np.linalg.norm(center - (a + b) / 2)), candidate['id'])
            chosen = min(owners, key=distance)
        updated = dict(row, profile_binding=binding(chosen), profile_owner=chosen['id'])
        out.append(updated)
    return out


def _xyz(points):
    a = np.asarray(points, float)
    return a[..., [2, 0, 1]] * [1, -1, 1]


def _fux(points):
    a = np.asarray(points, float)
    return np.round(a[..., [1, 2, 0]] * [-1, 1, 1], 6).tolist()


def _cloud(shape, *, cuts=False):
    values = []
    for key in ('points', 'vertices', 'rings'):
        if key in shape:
            values.append(_xyz(shape[key]).reshape(-1, 3))
    for item in shape.get('items', []):
        values.append(_cloud(item, cuts=cuts))
    if cuts:
        for item in shape.get('cuts', []):
            values.append(_cloud(item, cuts=True))
    return np.concatenate(values) if values else np.empty((0, 3))


def _map(shape, operation):
    out = deepcopy(shape)
    for key in ('points', 'vertices', 'rings'):
        if key in out:
            value = _xyz(out[key])
            out[key] = _fux(operation(value.reshape(-1, 3)).reshape(value.shape))
    for key in ('items', 'cuts'):
        if key in out:
            out[key] = [_map(child, operation) for child in out[key]]
    return out


def _segment(row):
    bone = row['bone']
    if bone in ('head', 'neck'):
        return 'head'
    if bone in ('hips', 'spine'):
        return 'pelvis'
    if bone == 'chest' or bone.startswith(('shoulder', 'pauldron')):
        return 'torso'
    if bone.startswith('upperarm_'):
        return 'arm_' + bone[-1] + '_upper'
    if bone.startswith('forearm_'):
        return 'arm_' + bone[-1] + '_fore'
    if bone.startswith('hand_'):
        return 'arm_' + bone[-1] + '_hand'
    if bone.startswith('kneecap_'):
        return 'shin_' + bone[-1]
    return bone


def _canonical(params):
    """Construct exactly the 01 parameter semantics, without its document import."""
    out = {}
    for family, function in (('upper_arm', body.upper_arm), ('torso', body.torso),
                             ('pelvis', body.pelvis), ('legs', body.legs)):
        for row in function(params[family]):
            out[(family, row[0])] = row
    for row in arm.parts(params['forearm'], params['hand']):
        if row[0] not in params['arm_drop']:
            out[('arm', row[0])] = row
    return out


def _shape(row):
    pid, label, segment, form, role, options = row
    part = kit.part(pid, label, segment, form, role, options, (np.eye(3), np.zeros(3)), 1, '', 'R')
    if 'faces' in part:
        # Triangulate in canonical coordinates before an anisotropic measured
        # calibration. It preserves the constructor's intended diagonal even
        # when a nonplanar strip projects poorly after rotation.
        part['faces'] = geom._triangulate(np.asarray(part['vertices'], float), part['faces'])
    return part


def _same(a, b):
    return a == b


def _frame_for(row, base_frames):
    R, origin, _, _ = base_frames[_segment(row)]
    # body.legs mirrors the left leg. 0.14: Arme ebenso – Konstruktorteile sind rechts beschrieben, kit.part spiegelt links an X; ohne
    # Spiegel lagen neue Armteile und Feldänderungen links ungespiegelt (Bizepskolben 103 mm daneben, Bericht 0.14).
    left_arm = _segment(row).startswith('arm_L_')
    mirror = np.array([-1, 1, 1]) if _side(row) == 'L' and (row['assembly'] == 'legs' or left_arm) else np.ones(3)
    return R, origin, mirror


def measurements(rows, base_frames):
    """Measured profile bounds per association, XYZ mm in each source bone frame.

    These values are derived from repository measurements every time, never from
    a workstation path. They are useful evidence for the default calibration.
    """
    grouped = {}
    for row in rows:
        key = binding(row)
        if key is None or row.get('profile_owner'):
            continue
        R, origin, mirror = _frame_for(row, base_frames)
        grouped.setdefault((key, _segment(row)), []).append((_cloud(row) - origin) @ R * mirror)
    return {key: (np.min(np.concatenate(v), axis=0), np.max(np.concatenate(v), axis=0))
            for key, v in grouped.items()}


def _resample(points, count):
    if len(points) == count:
        return points
    # Different profile-row counts retain a deterministic control correspondence.
    t = np.linspace(0, len(points) - 1, count)
    return np.column_stack([np.interp(t, np.arange(len(points)), points[:, i]) for i in range(3)])


def _field(points, reference, changed):
    """Interpolated control displacements in mm; exact identity when unchanged.

    Eight nearest reference controls give a local interpolated deformation rather
    than a bounding-box scale: a changed middle profile row remains local.
    """
    delta = _resample(changed, len(reference)) - reference
    if not np.any(delta):
        return points
    out = []
    for chunk in np.array_split(points, max(1, (len(points) + 63) // 64)):
        distance = np.sum((chunk[:, None, :] - reference[None, :, :]) ** 2, axis=2)
        count = min(8, len(reference))
        index = np.argpartition(distance, count - 1, axis=1)[:, :count]
        weights = 1 / np.maximum(np.take_along_axis(distance, index, axis=1), 1e-12)
        weights /= weights.sum(axis=1, keepdims=True)
        out.append(chunk + np.sum(delta[index] * weights[..., None], axis=1))
    return np.concatenate(out)


def _centered(row, R, origin, mirror, tolerance=1.0):
    """Mittelteil: die gemessene Hülle liegt im Segmentrahmen symmetrisch zu x = 0 (Annahme: Toleranz 1 mm), z. B. Codpiece, TorsoCore."""
    if _side(row) == 'L' or row['bone'].endswith(('_R', '_L')):
        return False
    local = (_cloud(row) - origin) @ R * mirror
    return bool(len(local)) and abs(local[:, 0].min() + local[:, 0].max()) / 2 < tolerance


def _calibration(bounds, reference):
    low, high = bounds
    rlow, rhigh = reference.min(axis=0), reference.max(axis=0)
    size = np.maximum(high - low, 1e-6)
    rsize = np.maximum(rhigh - rlow, 1e-6)
    return low, size, rlow, rsize


def templates(params, defaults, rows, base_frames):
    """Return predeformed measured rows, then feed the caller's normal rig mapper.

    Profiles, thicknesses, angular extents, offsets, chamfers and cuts are built
    by the SAME constructors as 01. Source surfaces retain their topology;
    new feature switches add actual kit geometry, removed features drop their
    associated source parts. All lengths remain mm and all angles degrees.
    """
    keys = ('upper_arm', 'torso', 'pelvis', 'legs', 'arm_drop', 'forearm', 'hand', 'replace')
    if all(_same(params[k], defaults[k]) for k in keys):
        return rows
    plan, replaced = None, []
    if params['replace']:
        # 0.14 Ersatzmodus: erst die gemessenen Teile der Einzelteile in params['replace'] gegen eingepasste Konstruktorteile tauschen
        # (roboterbasic_02_replace); die übrigen Teile gehen danach unverändert den Feldweg unten (Varianten, Proportionen).
        from . import roboterbasic_02_replace as replacement
        rows, replaced, plan = replacement.build(params, defaults, rows, base_frames)
    rows = associate(rows)
    before, after = _canonical(defaults), _canonical(params)
    bounds = measurements(rows, base_frames)
    shapes_before, shapes_after = {}, {}
    assigned = {binding(row) for row in rows}
    out = []
    for row in rows:
        key = binding(row)
        if (row['source_object'].startswith('ChestVent')
                and params['torso']['chest']['vents'] != defaults['torso']['chest']['vents']):
            # Source inserts belong to the old measured vent layout. The new
            # negative slots use the same constructive semantics as 01.
            continue
        if key is None:
            out.append(row)
            continue
        if key in before and key not in after:
            continue
        if key not in before or key not in after or before[key] == after[key]:
            out.append(row)
            continue
        if key not in shapes_before:
            shapes_before[key] = _shape(before[key])
            shapes_after[key] = _shape(after[key])
        old, new = shapes_before[key], shapes_after[key]
        reference, changed = _cloud(old), _cloud(new)
        R, origin, mirror = _frame_for(row, base_frames)
        low, size, rlow, rsize = _calibration(bounds[(key, _segment(row))], reference)
        center = _centered(row, R, origin, mirror)

        def deform(points, center=center):
            local = (points - origin) @ R * mirror
            refpoints = rlow + (local - low) / size * rsize
            displacement = _field(refpoints, reference, changed) - refpoints
            if center:
                # 0.14: Mittelteile bleiben spiegelgleich. Ändert eine Variante die Punktzahl des Konstruktorteils, ordnet _resample die
                # Kontrollpunkte nach Index zu, nicht nach Lage; das Feld wird schief (Mitte von Codpiece bei PV-C 5,8 mm daneben, Brustband in RC02 28 mm, Richter 0.14).
                # Mittel aus dem Feld am Punkt und dem gespiegelten Feld am Spiegelpunkt.
                flip = np.array([-1.0, 1.0, 1.0])
                mirrored = rlow + (local * flip - low) / size * rsize
                displacement = (displacement + (_field(mirrored, reference, changed) - mirrored) * flip) / 2
            return (local + displacement) * mirror @ R.T + origin

        updated = _map(row, deform)
        # Explicit editable layouts rebuild the measured owner before CSG.
        # Profile-only changes transport existing baked holes with the material;
        # a changed derived cut dictionary alone does not replace source details.
        if _cut_layout_changed(key, params, defaults) and row['source_object'] in CUT_OWNERS.get(key, ()):
            def measured(points):
                return ((low + (points - rlow) / rsize * size) * mirror) @ R.T + origin
            updated = _rebuild_boolean_owner(row, key, new, params, deform, measured)
        out.append(updated)
    # New constructive features use the measured profile calibration of the
    # nearest sibling in the SAME constructor family and anatomical segment.
    for key, new in after.items():
        if key in assigned or key in before:      # nur Merkmale, die der Standard nicht kennt; ein Konstruktorteil ohne gemessenes Gegenstück (shin_core, brief) ist kein Merkmal
            continue
        if plan is not None and plan.owner(key) in plan.replace:      # Ersatzmodus baut das Merkmal schon mit seinem Einzelteil
            continue
        family, pid = key
        _, label, segment, _, role, _ = new
        sides = ('R', 'L') if segment in ('upper', 'fore', 'hand', 'thigh', 'shin', 'foot') else ('C',)
        for side in sides:
            target = (f'arm_{side}_{segment}' if family in ('upper_arm', 'arm') else
                      f'{segment}_{side}' if side != 'C' else segment)
            candidates = [(r, binding(r)) for r in rows if binding(r) is not None
                          and binding(r)[0] == family and _segment(r) == target and binding(r) in before]
            if not candidates:
                continue
            # Preserve the semantic anatomical family before comparing spatial
            # neighbors: a left pauldron rim must not select a chest stripe just
            # because their canonical centers happen to be close.
            ancestors = [association[1] for _, association in candidates
                         if pid.startswith(association[1] + '_')]
            if ancestors:
                ancestor = max(ancestors, key=len)
                candidates = [candidate for candidate in candidates if candidate[1][1] == ancestor]
            new_cloud = _cloud(_shape(new))
            new_low, new_high = new_cloud.min(axis=0), new_cloud.max(axis=0)
            new_center = (new_low + new_high) / 2
            def rank(candidate):
                source, association = candidate
                if association not in shapes_before:
                    shapes_before[association] = _shape(before[association])
                reference = _cloud(shapes_before[association])
                low, high = reference.min(axis=0), reference.max(axis=0)
                center_distance = np.linalg.norm(new_center - (low + high) / 2)
                # Same canonical center: prefer the structural measured owner,
                # rather than a screw carrying the same semantic association.
                extent = np.ptp(_cloud(source), axis=0)
                return (float(center_distance), -float(np.prod(extent)), source['id'])
            sample, sibling = min(candidates, key=rank)
            if sibling not in shapes_before:
                shapes_before[sibling] = _shape(before[sibling])
            oldshape = shapes_before[sibling]
            ref = _cloud(oldshape)
            low, size, rlow, rsize = _calibration(bounds[(sibling, target)], ref)
            R, origin, mirror = _frame_for(sample, base_frames)
            def measured(points):
                return ((low + (points - rlow) / rsize * size) * mirror) @ R.T + origin
            part = _map(_shape(new), measured)
            if np.prod(mirror) < 0 and 'faces' in part:
                part['faces'] = [list(reversed(face)) for face in part['faces']]
            part.update(id=f'{target}_profile_{pid}', source_object=f'Parameter_{pid}_{side}',
                        bone=sample['bone'], assembly=sample['assembly'], label=label, role=role,
                        parameter_feature=f'{family}.{pid}',
                        profile_calibration_source=sample['source_object'],
                        profile_reference=f'{sibling[0]}.{sibling[1]}',
                        provenance=dict(kind='Annahme', source=PROVENANCE['association']))
            # Calibration and the generated part share one measured placement.
            # In particular, pauldron additions must inherit the current shoulder
            # mount translation instead of remaining at the source shoulder.
            for field in ('frame', 'mount_frame', 'length_scale', 'parent_part'):
                if field in sample:
                    part[field] = deepcopy(sample[field])
            if family == 'arm' and segment == 'upper':
                # 01 applies arm_bulk to the restored arm-v3 upper parts, while
                # body.upper_arm replacement profiles have their own dimensions.
                part['apply_arm_bulk'] = True
            out.append(part)
    return out + replaced
