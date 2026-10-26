"""R01 Ego-Arme: unveränderte Quelldaten, dokumentierte Ortho-Montage in mm.

Keine bpy-Abhängigkeit und kein Import aus dem Schwesterrepo. source_robot_arm
ist eine bytegleiche Kopie; die Umrechnung unten ist editierbare kit-Geometrie.
Frontgelenke haben Vorrang vor den alten Längenvorgaben 320/300 mm. Ausschließlich
Ober-/Unterarmhüllen werden längs angepasst; Gelenkradien und Hände bleiben 1:1.
"""
import copy
import math

from . import source_robot_arm as SOURCE

SOURCE_SHA256 = 'd713339efd85b3f2b24304133129094c550f55e62725dd9c72b1be0864ce29f5'
K = 1924 / 3653
SHOULDER_R = [-26, 1546, -281]
ELBOW_R = [-36, 1275, -371]
WRIST_R = [53, 1028, -478]
PROVENANCE = {
    'kind': 'gemessen',
    'source': 'robot-ortho-front/side-right/side-left.png; 4096²; 26.10.2026. Ego-Armformen aus ballon basic/arms/robot_arm.py, lokale bytegleiche Kopie source_robot_arm.py.',
    'source_sha256': SOURCE_SHA256,
    'joint_height_comparison_mm': {
        'front_elbow': (3876-(1435.1+1477.1+1431.9+1474.8)/4)*K,
        'front_wrist': (3876-1925)*K,
        'side_right_elbow': 1924-(1491.1-216)*K,
        'side_left_elbow': 1924-(1489.9-218)*K,
        'side_right_wrist': 1924-(1970-216)*K,
        'side_left_wrist': 1924-(1970-218)*K,
        'selected_elbow': 1275, 'selected_wrist': 1028,
        'kind': 'gemessen',
        'source': 'Front aus Mittelwert beider Ringscheiben beider Arme; Seiten an jeweiliger Helmoberkante registriert. Wrist visuell abgelesen, Frontwerte verbindlich.'},
    'bevel_difference': {'kind': 'Annahme',
        'source': 'Kit wertet Quell-Fasenbreiten als echte planare Kantenfase aus; ballons Zweisegment-Rundung wird nicht nachgebildet. Geometrieausgabe meldet diese Abweichung je Teil.'},
    'scale': {'kind': 'Vorgabe', 'height_mm': 1924, 'mm_per_pixel': K,
              'source': 'massfigur-v2 Entwurfshöhe; einheitlich Front y223..3876; keine Einzelbild-Höhennormalisierung'},
    'front_landmarks_px': {'kind': 'gemessen',
        'elbow_ring_centers_r': [[1227.8, 1435.1], [1460.0, 1477.1]],
        'elbow_ring_centers_l': [[2864.3, 1431.9], [2636.3, 1474.8]],
        'wrist_axis_r': [1140, 1925], 'wrist_axis_l': [2956, 1925],
        'source': 'Ellbogen: Flächenschwerpunkte der sichtbaren Cyan-Messmarker gemittelt, Material nicht übernommen. Handgelenk: Mitte des dunklen Übergangs Stulpe/Hand, visuell gerundet; x-Mitte2048.'},
    'side_landmarks_px': {'kind': 'gemessen', 'elbow_ring_right': [2217.8, 1491.1],
        'elbow_ring_left': [1876.5, 1489.9], 'wrist_axis_right': [2050, 1970],
        'wrist_axis_left': [2046, 1970],
        'source': 'Rechts f0=2150, links1946; Helmoberkanten216/218 an Front223 registriert. Ellbogen f≈−36, Handgelenk f≈53. Seitenhöhen Ellbogen≈1252/1254 und Hand≈1000/1001 stimmen nicht mit Front1275/1028 überein; Front verbindlich.'},
    'construction': {'kind': 'Annahme',
        'source': 'Gelenke symmetrisch gerundet; Schulter verbindlich (−26,1546,±281). Handrücken nach außen mit kleiner Vorwärtskomponente0.35; entspannte Fingerwinkel unverändert aus Quelle. Innenlager Schulter70mm Radius; keine Kappe/äußeren Ringe (upper_body). 20 Segmente Ego-Gelenke,24 Innenlager.'},
    'length_change': {'kind': 'gemessen',
        'source': 'Neue Front-Gelenklagen ersetzen 320/300mm Entwurfslängen. Explizite axiale Anpassung der Armhüllen, z-Positionen von Bolzen/Stulpen; Gelenkdurchmesser und alle Hand-/Fingermaße bleiben original. Keine globale Skalierung.',
        'source_upper_mm': SOURCE.UPPER_MM, 'source_fore_mm': SOURCE.FORE_MM},
}
PARTS = []
ANCHORS = {}
SEGMENT_FRAMES = {}


def _add(a, b):
    return [a[i]+b[i] for i in range(3)]


def _mul(v, s):
    return [x*s for x in v]


def _sub(a, b):
    return _add(a, _mul(b, -1))


def _dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def _norm(v):
    return math.sqrt(_dot(v, v))


def _unit(v):
    return _mul(v, 1/_norm(v))


def _cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def _frame(at, direction, y_hint):
    """Right-handed in physical xyz; author f,u,x has opposite orientation."""
    z = _unit(direction)
    y = _unit(_sub(y_hint, _mul(z, _dot(y_hint, z))))
    x = _mul(_cross(y, z), -1)
    return {'at': list(at), 'basis': [x, y, z]}


def _vector(frame, v):
    return [sum(frame['basis'][j][i]*v[j] for j in range(3)) for i in range(3)]


def _point(frame, v):
    return _add(frame['at'], _vector(frame, v))


def _rotate_x(frame, degrees):
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return {'at': frame['at'][:], 'basis': [_vector(frame, v) for v in ([1,0,0], [0,c,s], [0,-s,c])]}


def _advance(frame, v):
    return {'at': _point(frame, v), 'basis': copy.deepcopy(frame['basis'])}


def _reflect(frame):
    return {'at': [*frame['at'][:2], -frame['at'][2]],
            'basis': [[*v[:2], -v[2]] for v in frame['basis']]}


UPPER_MM = _norm(_sub(ELBOW_R, SHOULDER_R))
FORE_MM = _norm(_sub(WRIST_R, ELBOW_R))
LENGTH_SCALE = {'upper': UPPER_MM/SOURCE.UPPER_MM, 'fore': FORE_MM/SOURCE.FORE_MM}
PROVENANCE['length_change'].update(upper_mm=UPPER_MM, fore_mm=FORE_MM, axial_scale=LENGTH_SCALE)

# Full local-to-author basis; consumers can pose each group without guessing a
# pivot from its bounds. Finger frames include all preceding bends/translations.
frames = {
    'upper': _frame(SHOULDER_R, _sub(ELBOW_R, SHOULDER_R), [.35, 0, -1]),
    'fore': _frame(ELBOW_R, _sub(WRIST_R, ELBOW_R), [.35, 0, -1]),
    'hand': _frame(WRIST_R, _sub(WRIST_R, ELBOW_R), [.35, 0, -1]),
}
pose = SOURCE.FINGER_POSES['relaxed']
for i, x in enumerate(SOURCE.FINGER_X):
    finger = _advance(frames['hand'], [x, 0, SOURCE.KNUCKLE_Z])
    for j, length in enumerate(SOURCE.FINGER_LINKS):
        finger = _rotate_x(finger, pose['f'][i][j])
        frames[f'f{i}_{j}'] = finger
        finger = _advance(finger, [0, 0, length*SOURCE.FINGER_SCALE[i]])
# Source thumb frame in its original xyz coordinates, then compose with hand.
z = _unit(SOURCE.THUMB_DIR)
y = _unit(_sub([0,1,0], _mul(z, _dot([0,1,0], z))))
x = _cross(y, z)
thumb = {'at': _point(frames['hand'], SOURCE.THUMB_BASE),
         'basis': [_vector(frames['hand'], v) for v in (x, y, z)]}
# relaxed out=30 equals the source's neutral thumb abduction; no extra Y turn.
for j, length in enumerate(SOURCE.THUMB_LINKS):
    thumb = _rotate_x(thumb, [pose['t'][0], pose['t'][2]*.6, pose['t'][2]][j])
    frames[f't_{j}'] = thumb
    thumb = _advance(thumb, [0, 0, length])
for suffix in ('r', 'l'):
    for segment, frame in frames.items():
        SEGMENT_FRAMES[suffix+'_'+segment] = frame if suffix == 'r' else _reflect(frame)


def _plate_points(p):
    """Same faceted plate points as ego_geometrie.plate_verts, without bpy."""
    z0, z1 = p['z']; w0, w1 = p['w']; r0, r1 = p['r']
    def radius(z):
        return r0+(r1-r0)*(z-z0)/(z1-z0)
    points = [(p.get('u',0)+sign*w/2, radius(z)+dy, z)
              for z,w in ((z0,w0),(z1,w1)) for sign in (-1,1) for dy in (0,p['t'])]
    if p['ridge'] > 0:
        points += [(p.get('u',0),radius(z)+p['t']+p['ridge'],z)
                   for z in (z0+p['hip'][0],z1-p['hip'][1])]
    c, s = math.cos(math.radians(p.get('phi',0))), math.sin(math.radians(p.get('phi',0)))
    return [[x*c-y*s,x*s+y*c,z] for x,y,z in points]


def convert(kind, p, frame, axial_scale=1):
    """Local source primitive → one world kit primitive; no latent transforms."""
    def point(v):
        return _point(frame, [v[0], v[1], v[2]*axial_scale])
    center = p.get('c', [0,0,0])
    if kind == 'cyl':
        axis = 'xyz'.index(p['axis'])
        radial = [i for i in range(3) if i != axis]
        rings = []
        for end in (-1,1):
            ring = []
            for i in range(20):
                t = 2*math.pi*i/20
                v = [0.,0.,0.]; v[axis] = end*p['len']/2
                v[radial[0]],v[radial[1]] = p['r']*math.cos(t),p['r']*math.sin(t)
                # Preserve circular bearings: move their center axially only.
                ring.append(_add(point(center), _vector(frame,v)))
            rings.append(ring)
        return {'shape':'loft','rings':rings,'smooth':True}
    if kind == 'hull':
        points = p['pts']
    elif kind == 'plate':
        points = _plate_points(p)
    elif kind == 'box':
        points = [_add(center,[sx*p['d'][0]/2,sy*p['d'][1]/2,sz*p['d'][2]/2])
                  for sx in (-1,1) for sy in (-1,1) for sz in (-1,1)]
    elif kind == 'prism':
        points = [_add(center,[r*math.cos(2*math.pi*i/8+math.pi/8),r*math.sin(2*math.pi*i/8+math.pi/8),z])
                  for r,z in ((p['r0'],-p['len']/2),(p['r1'],p['len']/2)) for i in range(8)]
    else:
        raise ValueError('Unbekannte Ego-Form: '+kind)
    return {'shape':'hull','points':[point(v) for v in points]}


for suffix, sign in [('r',-1),('l',1)]:
    for pid, label, segment, kind, role, parameters in SOURCE.parts():
        group = suffix+'_'+segment
        PARTS.append(dict(id='arms_'+pid+'_'+suffix, assembly='arms', label=label,
            role=role, segment=segment, group=group, arm_side=suffix,
            source_id=pid, source_shape=kind, source_parameters=copy.deepcopy(parameters),
            source_sha256=SOURCE_SHA256,
            bevel=parameters.get('bevel', {'cyl':.8,'prism':1.6,'plate':1,'hull':1.6}.get(kind,0)),
            provenance={'kind':'Vorgabe','source':'ballon robot_arm.py '+SOURCE_SHA256+'; unveränderte Quelldaten. Montage und axiale Ortho-Anpassung siehe PROVENANCE.length_change.'},
            **convert(kind, parameters, SEGMENT_FRAMES[group], LENGTH_SCALE.get(segment,1))))
    # Shoulder armor and external ring are owned by upper_body. These two
    # inner-bearing pieces stay fully inside its open 95–108mm radial shell.
    for name, radius, halfwidth, role in [('shoulder_inner',70,44,'dark_metal'),('shoulder_axle',37,47,'anodized')]:
        PARTS.append(dict(id='arms_'+name+'_'+suffix, assembly='arms', role=role,
            segment='upper', group=suffix+'_upper', arm_side=suffix,
            shape='cyl', axis='x', c=SHOULDER_R[:2],
            a0=sign*281-halfwidth, a1=sign*281+halfwidth, r=radius, segs=24, bevel=0,
            provenance={'kind':'Annahme','source':'Innenlager an gemeinsamem Shoulder-Socket; 70/37mm Radien, 88/94mm Breite; keine Schulterkappe und kein äußerer Ring.'}))
    for name, pos, part in [('Elbow', ELBOW_R, 'elbow'),('Wrist', WRIST_R,'wrist_block'),('Hand',WRIST_R,'palm')]:
        at = [pos[0],pos[1],-sign*pos[2]]
        ANCHORS['Socket_'+name+'_'+suffix.upper()] = dict(at=at,part='arms_'+part+'_'+suffix,
            source='Gemessen/abgeleitet: Frontgelenke und Seitentiefe, einheitlich1924/3653; gerundet. Hand-Socket ist Kardanursprung, siehe SEGMENT_FRAMES.' )
