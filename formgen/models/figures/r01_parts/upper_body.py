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
    'shoulder_revision_1': {
        'kind': 'gemessen',
        'source': 'Frontmaske unverändert: y770 x1497..1672, y800 x1458..1712; y850..1060 zusammenhängender Schulter/Rumpfrand. Seitenoriginal: breite weiße Ringfläche um freie dunkle Gelenkmitte. Ein begründeter Korrekturdurchgang, kein Maskenfit.',
        'construction': {'kind': 'Annahme',
            'source': 'Konturstützpunkte auf gemeinsames k1924/3653 gerundet: axiale Schale185..333mm, Radius94..99mm, äußere Seitenblende48mm freie Mitte und6mm axiale Wand. Oberer Außenrand um0.35 des radialen Höhenanteils nach innen geneigt. Graphit-Anschlusskragen x173..237, Radien72/92; keine Änderung der Schulterachse.'}},
    'surface_revision_2': {
        'kind': 'gemessen',
        'source': 'Gemeinsam registrierte Front-/Rückenorthos: Schulteraußenkante bei u1550 etwa x±356mm; Front u1500/1525/1575/1600 etwa x±342/355/351/328mm. Taille: zentrale Kontur bei u1220 Front±126mm, Rücken−116..125mm; u1245 etwa±112mm, u1300 etwa±127mm. Keine Änderung der Gelenke oder der Seitenregistrierung.',
        'construction': {'kind': 'Annahme',
            'source': 'Ein gemeinsamer räumlicher Kappenkranz mit 24mm parabolischer axialer Wölbung um die feste Achshöhe1546; Formhalbhöhe54mm und Aufwärtsneigung0.3, oberhalb der Wölbung keine Verengung der bestehenden Krone. Innerer Anschluss x185 bleibt fest, f/u-Radien und freie48mm Lageröffnung unverändert. Bauchweite119/126/112/127/123mm bei u1190/1220/1245/1306/1344; Front-/Rücktiefe bleibt erhalten, neu interpolierte Zwischenzeile f133/−52mm.'}},
    'carrier_roof_revision_3': {
        'kind': 'gemessen',
        'source': 'Unveränderte registrierte Front-/Rückenmasken, GEOM4/RASTER5: bei x80mm obere Kontur u1641/1639, x100 u1643/1645, x110 u1645/1643; Modell zuvor1624/1631/1635mm. Bei x−170 Referenzen1603/1605, Modell1633mm. Gespiegelter Rücken, gemeinsamer Maßstab; keine Kamera-/Maskenanpassung.',
        'construction': {'kind': 'Annahme',
            'source': 'Gerundetes gemeinsames Trägerdach: medialer bestehender Punkt x65/f88 von u1617 auf1640, lateraler Punkt x176/f48 von u1632 auf1615. Gerade Dachsegmente zum unveränderten x125/u1640 und x210/u1582. Alle f/x-Werte, drei unteren Punkte, 5mm-Wand, Kappen, Kragen und Anker unverändert; neue Bildabnahme separat erforderlich.'}},
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

ABDOMEN_ROWS = [(1190, 119, 126, -48), (1220, 126, 133, -52),
                (1245, 112, 139, -56), (1306, 127, 145, -64),
                (1344, 123, 150, -65)]
abdomen = _part('abdomen_core', 'graphite',
                'Gemessen: Front/Rücken schwarze Bauchzone und gemeinsame Konturstützen PROVENANCE.surface_revision_2. Annahme: breiterer Innenkörper um festen Waist(45,1190,0), unveränderte Seitentiefe und 6mm Plattenfugen.',
                **_body(ABDOMEN_ROWS))
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

def _cap_axial_crown(x, radial_height):
    """A rounded axial crown around the fixed shoulder, not a wider joint."""
    # The old straight sloping rim was narrow at the axis yet too flared below.
    # One smooth 3D crown adds the measured middle width and returns inward at
    # the lower lip; the original upper crown and inner coupling stay intact.
    bulge = 24 * (1 - (radial_height / 54)**2) + .3 * radial_height
    if radial_height > 0:
        bulge = max(0, bulge)
    return x - .35 * radial_height * max(0, (x - 185) / 148) + bulge * max(0, (x - 185) / 148)


# Wide beams connect the chest to the open shoulder cups. Actual shoulder
# bearings and ring faces belong to arms; this assembly supplies the shells.
for suffix, sign in [('r', -1), ('l', 1)]:
    _part('shoulder_carrier_'+suffix, 'graphite',
          'Gemessen: Front/Rücken dunkle breite Träger über Brust; gemeinsame Dachkontur PROVENANCE.carrier_roof_revision_3. Annahme: gefalteter Hohlträger, 5mm Wand; unveränderte Anbindung und Achsanschluss x281.',
          **_plate([[88, 1640, sign*65], [68, 1640, sign*125],
                    [48, 1615, sign*176], [45, 1582, sign*210],
                    [89, 1555, sign*175], [103, 1596, sign*102]],
                   [[0, 1, 2, 5], [2, 3, 4, 5]]))

    _part('shoulder_coupling_'+suffix, 'graphite',
          'Gemessen: Front/Rücken y850..1060 ohne weiße Lücke zwischen Thorax und Schulter. Annahme: hohler Anschlusskragen x173..237, Radien72/92, 24 Segmente; trägt keine Gelenkscheibe und lässt den inneren Lagerraum frei.',
          shape='cyl', axis='x', c=[-26, 1546],
          a0=sign*205-32, a1=sign*205+32, r=92, r_in=72, segs=24)

    # Sweep a closed shell section around the shoulder axis. Its outer flange
    # remains open at the bearing and below; it is a broad white ring in side
    # view, rather than the six-millimetre line of a bare barrel edge.
    angles = [math.radians(-129 + i*258/24) for i in range(25)]
    section = [(185, 94), (210, 99), (286, 99), (315, 87),
               (333, 78), (333, 48), (327, 48), (327, 74),
               (309, 82), (286, 93), (210, 93), (185, 88)]
    vertices = [[-26+r*math.sin(t), 1546+r*math.cos(t),
                 sign*_cap_axial_crown(x, r*math.cos(t))]
                for x, r in section for t in angles]
    row = len(angles)
    faces = [[j*row+i, j*row+i+1, ((j+1)%len(section))*row+i+1,
              ((j+1)%len(section))*row+i]
             for j in range(len(section)) for i in range(row-1)]
    for i in (0, row-1):
        # Pair the outer/inner wall explicitly. A triangle fan over this
        # concave section would cross the empty bearing opening.
        for quad in ([0, 1, 10, 11], [1, 2, 9, 10], [2, 3, 8, 9],
                     [3, 4, 7, 8], [4, 5, 6, 7]):
            faces.append([j*row+i for j in quad])
    shell = _part('shoulder_cap_'+suffix, 'shell',
                  'Gemessen: Front Kappenoberkante y≈755..770; Seite breite weiße Ringfläche um Gelenk, Frontachse y≈940. Annahme: unten offene258°-Kappe, max99mm Radius,6mm Schalenwand,48mm freie Ringmitte, geneigter Außenrand; Stützpunkte und axiale Kranzwölbung siehe PROVENANCE.shoulder_revision_1/surface_revision_2.',
                  **_closed(vertices, faces), wall_mm=6)
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
