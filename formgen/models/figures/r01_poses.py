"""Rigid R01 ready pose; neutral geometry and all source dimensions stay intact.

Author coordinates are mm (f,u,x); emitted rigid matrices operate on world xyz
metres. The one-handed, forward low-ready arrangement is an explicit design
assumption, not a measurement of the neutral orthographic references.
"""
from copy import deepcopy
import math

from .r01_parts import arms

SOURCE = arms.SOURCE
GRIP_IN_HAND = [10, -37, 55]
READY_WEAPON_SOCKET = [500, 1320, -320]
# Hand +X follows grip height, +Y points outwards, +Z towards the muzzle.
READY_HAND_BASIS = [[0, 1, 0], [0, 0, -1], [1, 0, 0]]


def _xyz(point):
    return [point[2]/1000, -point[0]/1000, point[1]/1000]


def _frame_matrix(old, new):
    """Map one equal-handed orthonormal frame onto another, without scaling."""
    old_basis = [_xyz(v) for v in old['basis']]
    new_basis = [_xyz(v) for v in new['basis']]
    rotation = [[sum(new_basis[k][i]*old_basis[k][j]*1e6 for k in range(3))
                 for j in range(3)] for i in range(3)]
    origin, target = _xyz(old['at']), _xyz(new['at'])
    return [rotation[i]+[target[i]-sum(rotation[i][j]*origin[j] for j in range(3))]
            for i in range(3)] + [[0., 0., 0., 1.]]


def transform_point(matrix, point):
    return [sum(matrix[i][j]*point[j] for j in range(3))+matrix[i][3] for i in range(3)]


def hand_socket():
    """Actual grip datum, distinct from the existing wrist/Kardan datum."""
    return dict(at=arms._point(arms.SEGMENT_FRAMES['r_hand'], GRIP_IN_HAND),
                part='arms_palm_r',
                provenance=dict(kind='Annahme', source='Griffdatum lokal [10,-37,55]mm in unveränderter rechter Hand: Palmenseite an W01-Griff (30mm Breite), Fingerreihen entlang Griffhöhe; siehe docs/robot-pose.md'))


def _elbow(shoulder, wrist):
    delta = arms._sub(wrist, shoulder)
    distance = arms._norm(delta)
    a, b = arms.UPPER_MM, arms.FORE_MM
    if not abs(a-b) < distance < a+b:
        raise ValueError('Ready-Hand außerhalb der unveränderten Armreichweite')
    direction = arms._unit(delta)
    along = (a*a-b*b+distance*distance)/(2*distance)
    pole = [0, -.35, -1]
    pole = arms._unit(arms._sub(pole, arms._mul(direction, arms._dot(pole, direction))))
    return arms._add(shoulder, arms._add(arms._mul(direction, along),
                         arms._mul(pole, math.sqrt(a*a-along*along))))


def ready_frames():
    hand = dict(at=[0, 0, 0], basis=deepcopy(READY_HAND_BASIS))
    hand['at'] = arms._sub(READY_WEAPON_SOCKET, arms._vector(hand, GRIP_IN_HAND))
    elbow = _elbow(arms.SHOULDER_R, hand['at'])
    frames = dict(r_hand=hand,
        r_upper=arms._frame(arms.SHOULDER_R, arms._sub(elbow, arms.SHOULDER_R), [0,0,-1]),
        r_fore=arms._frame(elbow, arms._sub(hand['at'], elbow), [0,0,-1]))
    grip = SOURCE.FINGER_POSES['grip']
    for i, x in enumerate(SOURCE.FINGER_X):
        finger = arms._advance(hand, [x, 0, SOURCE.KNUCKLE_Z])
        for j, length in enumerate(SOURCE.FINGER_LINKS):
            finger = arms._rotate_x(finger, grip['f'][i][j])
            frames[f'r_f{i}_{j}'] = finger
            finger = arms._advance(finger, [0, 0, length*SOURCE.FINGER_SCALE[i]])
    z = arms._unit(SOURCE.THUMB_DIR)
    y = arms._unit(arms._sub([0,1,0], arms._mul(z, arms._dot([0,1,0], z))))
    x = arms._cross(y,z)
    thumb = dict(at=arms._point(hand, SOURCE.THUMB_BASE),
                 basis=[arms._vector(hand,v) for v in (x,y,z)])
    # Source thumb neutral abduction is 30 degrees. Apply grip's 12 degrees
    # relative to that frame, then its three source flexion values.
    angle = math.radians(grip['t'][1]-30)
    c, s = math.cos(angle), math.sin(angle)
    thumb['basis'] = [arms._vector(thumb,v) for v in ([c,0,-s],[0,1,0],[s,0,c])]
    for j, length in enumerate(SOURCE.THUMB_LINKS):
        thumb = arms._rotate_x(thumb, [grip['t'][0],grip['t'][2]*.6,grip['t'][2]][j])
        frames[f'r_t_{j}'] = thumb
        thumb = arms._advance(thumb, [0,0,length])
    return frames


def build_poses(parts, anchors):
    """No mutation: caller installs hand_socket() as Socket_Hand_R first."""
    if anchors.get('Socket_Hand_R', {}).get('at') != hand_socket()['at']:
        raise ValueError('Ready benötigt das explizite Griffdatum aus hand_socket()')
    frames = ready_frames()
    matrices = {name:_frame_matrix(arms.SEGMENT_FRAMES[name], frame)
                for name,frame in frames.items()}
    return dict(idle=dict(label='Neutraler Stand',part_transforms={},
                 provenance=dict(kind='Vorgabe',source='Unveränderte Neutralstellung der vier Orthos')),
        ready=dict(label='W01 in rechter Hand – Ready-Entwurf',
            status='draft_not_accepted',
            part_transforms={part['id']:matrices[part['group']] for part in parts
                             if part.get('group') in matrices},
            joints_mm=dict(shoulder=arms.SHOULDER_R[:], elbow=frames['r_fore']['at'],
                           wrist=frames['r_hand']['at'], grip=READY_WEAPON_SOCKET[:]),
            attachments=[dict(model='W01',source_anchor='Socket_Hand',target_anchor='Socket_Hand_R',
                              rotation=[[1,0,0],[0,1,0],[0,0,1]])],
            provenance=dict(kind='Annahme',source='Einhand-Low-Ready; W01-Griff [500,1320,-320]mm, Lauf nach +f, IK mit Quell-Armlängen; SOURCE.grip, separate Griff- und Wrist-Daten. Bildabnahme offen; docs/robot-pose.md')))


def evaluated_attachment(weapon_document, robot_document, pose='ready'):
    """Place evaluated weapon meshes at the posed robot grip; inputs unchanged.

Return the transformed weapon document. The caller prefixes part/assembly IDs
before combining it with the robot. No imports, reconstruction or rendering.
"""
    definition = robot_document['poses'][pose]
    matching = [entry for entry in definition.get('attachments', [])
                if entry['model'] == weapon_document['info']['id']]
    if len(matching) != 1:
        raise ValueError('Pose benötigt genau eine passende Waffenreferenz')
    entry = matching[0]
    source = weapon_document['anchors'][entry['source_anchor']]['position_m']
    target = robot_document['anchors'][entry['target_anchor']]
    point = target['position_m']
    if target.get('part') in definition['part_transforms']:
        point = transform_point(definition['part_transforms'][target['part']], point)
    rotation = entry['rotation']
    matrix = [list(rotation[i])+[point[i]-sum(rotation[i][j]*source[j] for j in range(3))]
              for i in range(3)] + [[0,0,0,1]]
    result = deepcopy(weapon_document)
    for part in result['parts']:
        part['mesh']['vertices'] = [transform_point(matrix,p) for p in part['mesh']['vertices']]
        vertices = part['mesh']['vertices']
        part['bounds_m'] = [[min(p[i] for p in vertices) for i in range(3)],
                            [max(p[i] for p in vertices) for i in range(3)]]
    for anchor in result['anchors'].values():
        anchor['position_m'] = transform_point(matrix,anchor['position_m'])
    result['bounds_m'] = [[min(p['bounds_m'][0][i] for p in result['parts']) for i in range(3)],
                          [max(p['bounds_m'][1][i] for p in result['parts']) for i in range(3)]]
    result['attachment_transform_m'] = matrix
    return result
