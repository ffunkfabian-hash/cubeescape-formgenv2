"""R01 Oberkörper: Frontgelenke, Seitentiefe, Rückenschale, echte Schalen.

Alle Maße mm im gemeinsamen (f,u,x)-Rahmen. Keine Render-Abnahme hier.
Vorgabe 1924mm ist die angenommene physische Gesamthöhe; Pixelmessungen
werden mit EINEM Maßstab 1924/3653 übertragen. Geometrie bleibt editierbar.
"""
import math

K = 1924 / 3653
PROVENANCE = {
    'kind': 'gemessen',
    'source': 'Vier robot-ortho-{front,back,side-right,side-left}.png, 4096²; 26.10.2026, visuell abgelesene gerundete Pixelanteile',
    'scale': {'kind': 'Vorgabe', 'height_mm': 1924, 'mm_per_pixel': K,
              'source': 'massfigur-v2 Entwurfshöhe; Front y223..3876; x-Mitte2048'},
    'registration': {'kind': 'Annahme', 'front_x_center_px': 2048,
                     'side_right_f0_px': 2150, 'side_right_top_px': 216,
                     'side_left_f0_px': 1946, 'side_left_top_px': 218,
                     'source': 'Gemeinsame Registrierung docs/robot-contract.md; f=(2150-x)*K rechts, keine unabhängige Höhennormierung'},
    'front_landmarks_px': {'kind': 'gemessen', 'shoulder_axis_y': 940,
                           'shoulder_centers_x': [1515, 2581],
                           'neck_head_join_y': 665, 'collar_y': 810,
                           'chest_top_y': 822, 'chest_bottom_y': 1295,
                           'abdomen_bottom_y': 1617,
                           'source': 'Front: sichtbare Kappenmitten statt äußerer Ringscheiben; verdeckte Achsmitte ist abgeleitete Annahme'},
    'side_landmarks_px': {'kind': 'gemessen', 'shoulder_axis_x': 2200,
                          'chest_front_x': 1742, 'back_extreme_x': 2390,
                          'source': 'side-right Ringzentrum und Schalenprofil; Gegenansicht side-left visuell gegengeprüft'},
    'construction': {'kind': 'Annahme',
                     'source': 'Gerundete Konturstützpunkte und verdeckte Verbindungsteile; 5mm f-Wand Brust/Rücken, 6mm radial Schulter, 6mm Fugen; 24 Schultersegmente. B nur Facettierung, massfigur-v2 nur Schalenprinzip.'},
    'waist': {'kind': 'Vorgabe', 'at': [45, 1190, 0],
              'source': 'Gemeinsamer unterer Rumpfanschluss docs/robot-contract.md; Socket_Waist wird vom Unterkörper exportiert'},
}
PARTS = []
ANCHORS = {}


def _part(name, role, source, **geometry):
    p = dict(id='upper_body_' + name, assembly='upper_body', role=role,
             bevel=0, provenance={'kind': 'Annahme', 'source': source}, **geometry)
    PARTS.append(p)
    return p['id']


def _closed(vertices, faces):
    """Positive world-volume winding, including mirrored author coordinates."""
    # Explicit triangles keep mirrored folded quads on the same diagonal.
    faces = [[face[0], face[i], face[i+1]]
             for face in faces for i in range(1, len(face)-1)]
    def det(a, b, c):
        return (a[0]*(b[1]*c[2]-b[2]*c[1]) - a[1]*(b[0]*c[2]-b[2]*c[0])
                + a[2]*(b[0]*c[1]-b[1]*c[0]))
    volume = sum(det(vertices[face[0]], vertices[face[i]], vertices[face[i+1]])
                 for face in faces for i in range(1, len(face)-1))
    # Author f,u,x -> world x,-f,u reverses orientation.
    if volume > 0:
        faces = [list(reversed(face)) for face in faces]
    return dict(shape='surface', vertices=vertices, faces=faces)


def _plate(vertices, faces, wall=5, rear=False):
    """Explicit inner skin and boundary rims; nominal wall measured along f."""
    n = len(vertices)
    inner = [[f + (wall if rear else -wall), u, x] for f, u, x in vertices]
    uses = {}
    for face in faces:
        for a, b in zip(face, face[1:] + face[:1]):
            key = tuple(sorted((a, b)))
            uses.setdefault(key, []).append((a, b))
    closed = faces + [[n+i for i in reversed(face)] for face in faces]
    for pair in uses.values():
        if len(pair) == 1:
            a, b = pair[0]
            closed.append([b, a, n+a, n+b])
    return dict(**_closed(vertices+inner, closed), wall_mm=wall)


def _body(rows):
    """Octagonal horizontal rings (u, halfwidth, front, back)."""
    rings = []
    for u, w, front, back in rows:
        depth = front-back
        rings.append([[f, u, x] for f, x in (
            (front, -.68*w), (front, .68*w), (front-.18*depth, w),
            (back+.18*depth, w), (back, .68*w), (back, -.68*w),
            (back+.18*depth, -w), (front-.18*depth, -w))])
    return dict(shape='loft', rings=rings)


# Black load-bearing enclosure follows the white panel perimeter with a
# deliberate visible border; the breastplate itself remains hollow.
CORE_ROWS = [(1300, 124, 142, -62), (1360, 172, 170, -88),
             (1478, 197, 185, -103), (1588, 169, 105, -88),
             (1612, 131, 91, -78)]
core = _part('thorax_core', 'graphite',
             'Gemessen: Front Rumpfrand x≈1674..2422, y≈810..1408; Seitenprofil unter der Schale. Annahme: verdeckte achteckige Querschnitte.',
             **_body(CORE_ROWS))

# Separate left/right breastplates: raised central fold, faceted cheek and
# low outer corner. The central seam stays physically open (4 mm).
CHEST_VERTICES = [
    [124, 1600, 2], [118, 1600, 62], [96, 1610, 132], [102, 1588, 177],
    [152, 1478, 189], [152, 1359, 108], [180, 1380, 77], [195, 1380, 2],
    [218, 1510, 2], [203, 1517, 162],
]
CHEST_FACES = [[0, 1, 2, 9, 8], [2, 3, 9], [3, 4, 9],
               [8, 9, 6, 7], [9, 4, 5, 6]]
for suffix, sign in [('r', -1), ('l', 1)]:
    _part('breastplate_'+suffix, 'shell',
          'Gemessen: Front helle Brust y822..1295, x≈1690..2406; Seite Frontmaximum x≈1742→f215. Annahme: 5mm Innenhaut, 4mm Mittelfuge und gefaltete Interpolation (B).',
          **_plate([[f, u, sign*x] for f, u, x in CHEST_VERTICES], CHEST_FACES))

# Back reference has broad paired wing panels, plus a narrow spine module.
BACK_VERTICES = [[-91, 1601, 30], [-87, 1610, 124], [-93, 1588, 174],
                 [-116, 1482, 188], [-101, 1358, 110], [-112, 1378, 73],
                 [-125, 1378, 30], [-128, 1510, 30], [-119, 1517, 158]]
BACK_FACES = [[0, 1, 8, 7], [1, 2, 8], [2, 3, 8], [7, 8, 5, 6], [8, 3, 4, 5]]
for suffix, sign in [('r', -1), ('l', 1)]:
    _part('backplate_'+suffix, 'shell',
          'Gemessen: robot-ortho-back breite helle Schulterblattflächen, y≈820..1295; Seite Rückenmaximum x≈2390→f−126. Annahme: gleiche 5mm Wand und 6mm Fuge zum schmalen Wirbelsäulenmodul.',
          **_plate([[f, u, sign*x] for f, u, x in BACK_VERTICES], BACK_FACES, rear=True))
spine = [[-91, 1600, -25], [-91, 1600, 25], [-129, 1510, 25],
         [-126, 1378, 25], [-126, 1378, -25], [-129, 1510, -25]]
_part('back_spine_cover', 'shell',
      'Gemessen: Rücken zentrale schmale Abdeckung. Annahme: 50mm Breite, 5mm Wand und längs gefaltetes Profil.',
      **_plate(spine, [[0, 1, 2, 5], [5, 2, 3, 4]], rear=True))

abdomen = _part('abdomen_core', 'graphite',
                'Gemessen: Front schwarze Bauchzone y≈1400..1617; Annahme: um Waist(45,1190,0) liegender Innenkörper und 6mm Plattenfugen.',
                **_body([(1190, 82, 126, -48), (1245, 96, 139, -56),
                         (1306, 111, 145, -64), (1344, 123, 150, -65)]))
for i, (u0, u1, width, front, back) in enumerate([
        (1195, 1232, 72, 139, -62), (1239, 1276, 83, 149, -70),
        (1283, 1323, 93, 156, -76)]):
    for rear in (False, True):
        f = back if rear else front
        vertices = [[f, u0, -width*.78], [f, u0, width*.78],
                    [f, u0+8, width], [f, u1-8, width],
                    [f, u1, width*.78], [f, u1, -width*.78],
                    [f, u1-8, -width], [f, u0+8, -width]]
        _part(('abdominal_back_' if rear else 'abdominal_front_')+str(i+1), 'graphite',
              'Gemessen: drei gerippte Bauchsegmente in Front/Rücken. Annahme: gerundete Höhen/Weiten aus Rumpfzone, 5mm Wand, 7mm Gelenkfuge.',
              **_plate(vertices, [list(range(8))], rear=rear))

# Collar and short neck socket: head owns the visible neck above the collar.
collar = _part('neck_collar', 'graphite',
               'Gemessen: Front Kragenbasis y≈810→u1615; Seite Halsfuß f≈35. Annahme: 78mm Außenradius und 53mm freie Öffnung, 20 Segmente.',
               shape='cyl', axis='u', c=[35, 0], a0=1598, a1=1630,
               r=78, r_in=53, segs=20)

# Wide beams connect the chest to the open shoulder cups. Actual shoulder
# bearings and ring faces belong to arms; this assembly supplies the shells.
for suffix, sign in [('r', -1), ('l', 1)]:
    _part('shoulder_carrier_'+suffix, 'graphite',
          'Gemessen: Front dunkle breite Träger über Brust, y≈755..940. Annahme: gefalteter Hohlträger, 5mm Wand; Achsanschluss x281.',
          **_plate([[88, 1617, sign*65], [68, 1640, sign*125],
                    [48, 1632, sign*176], [45, 1582, sign*210],
                    [89, 1555, sign*175], [103, 1596, sign*102]],
                   [[0, 1, 2, 5], [2, 3, 4, 5]]))

    # Five partial annular rings make a cap open below and at both axial ends.
    # Radial wall does not close the visible center; arms may install its disc.
    angles = [math.radians(-129 + i*258/24) for i in range(25)]
    rings = [(237, 95), (250, 107), (306, 108), (333, 96)]
    outer = [[-26+r*math.sin(t), 1546+r*math.cos(t), sign*x]
             for x, r in rings for t in angles]
    inner = [[-26+(r-6)*math.sin(t), 1546+(r-6)*math.cos(t), sign*x]
             for x, r in rings for t in angles]
    n, row = len(outer), len(angles)
    faces = [[j*row+i, j*row+i+1, (j+1)*row+i+1, (j+1)*row+i]
             for j in range(len(rings)-1) for i in range(row-1)]
    faces += [[n+i for i in reversed(face)] for face in faces[:]]
    boundary = list(range(row)) + [j*row+row-1 for j in range(1,len(rings))]
    boundary += list(range(n-2,n-row-1,-1)) + [j*row for j in range(len(rings)-2,0,-1)]
    for a, b in zip(boundary, boundary[1:]+boundary[:1]):
        faces.append([b, a, n+a, n+b])
    shell = _part('shoulder_cap_'+suffix, 'shell',
                  'Gemessen: Front Kappenhöhe y≈755..1110; Seite Schulterringzentrum x≈2200, Front y≈940. Annahme: offene258°-Kappe, Radien95..108, 6mm echte radiale Wand, 24 Segmente, axial x237..333.',
                  **_closed(outer+inner, faces), wall_mm=6)
    ANCHORS['Socket_Shoulder_'+suffix.upper()] = {
        'at': [-26, 1546, sign*281], 'part': shell,
        'source': 'Gemessen/abgeleitet: Front y940 und Kappenmitten x1515/2581, k1924/3653; Seite Ring-x2200 ergibt f−26. Gerundete verdeckte Gelenkachse.'}

# Chest puck is intentionally non-emissive: cyan is a reference marker only.
_part('sternum_mount', 'dark_metal',
      'Gemessen: Front kreisförmige Brustfassung Mittelpunkt x2048,y≈1010; Annahme: Radius47, 32 Segmente, 8mm Ringwand, sitzt vor gefalteter Schale.',
      shape='cyl', axis='f', c=[1509, 0], a0=216, a1=227, r=47, r_in=39, segs=32)
_part('sternum_sensor', 'anodized',
      'Gemessen: innere Frontscheibe der Brustfassung. Annahme: Radius34, Tiefe8; ausdrücklich dunkles Metall ohne Emission.',
      shape='cyl', axis='f', c=[1509, 0], a0=218, a1=226, r=34, segs=32)
ANCHORS['Socket_Neck'] = {'at': [35, 1690, 0], 'part': collar,
                          'source': 'Gemessen/abgeleitet: Front Kopf-Halsübergang y≈665→u1691; Seite f≈35. Gerundete Verbindung; sichtbaren Hals oberhalb Kragen baut head.'}
