"""R01 head: measured Ortho envelope, separate face and hollow helmet panels.

Author coordinates (f,u,x), mm. Only the front height provides scale;
side-right y216 and side-left y218 are aligned without rescaling. The
1924mm stature is a design input, not a photographed real-world dimension.
"""
import math

K = 1924 / 3653
PROVENANCE = {
    'kind': 'gemessen',
    'source': 'robot-ortho-front/back/side-right/side-left.png, 4096², 26.10.2026; head crops visually checked',
    'scale': {'kind': 'Vorgabe', 'height_mm': 1924, 'mm_per_pixel': K,
              'source': 'massfigur-v2 design height; FRONT y223..3876 provides one scale for all four views'},
    'registration': {'kind': 'Annahme', 'front_center_x_px': 2048,
                     'front_top_px': 223, 'side_right_top_px': 216,
                     'side_left_top_px': 218, 'side_right_f0_px': 2150,
                     'side_left_f0_px': 1946,
                     'source': 'docs/robot-contract.md; f=(2150-x)*K right, f=(x-1946)*K left'},
    'front_pixels': {'kind': 'gemessen', 'helmet_width_px': [507, 520],
                     'width_samples_y_px': {240: 205, 280: 324, 330: 399, 400: 459, 500: 520, 600: 455, 630: 427},
                     'source': '4096² front mask and visual image: outline includes ear disks; rounded and symmetric in design'},
    'side_pixels': {'kind': 'gemessen', 'outline_x_at_y450_px': [1793, 2301],
                    'ear_center_px': [2115, 487],
                    'source': 'side-right silhouette/profile; opposite view checked at same scale'},
    'construction': {'kind': 'Annahme',
                     'source': 'Rounded profile interpolation; 4mm shell radial/f/x wall offsets, 2° face seam; 24 angular facets. Hidden neck/hinge geometry; dark joint roles override cyan image markers. B supplies only shell language; massfigur-v2 only separated shell principles.'},
    'nape_profile_revision_1': {
        'kind': 'gemessen',
        'source': 'Beide unveränderten4096px-Farborthos zeigen die dunkle gefaltete Nackenbasis zwischen Helm und Schulterring; k1924/3653, nur Helmregistrierung. Seitenmasken: u1630 R(y774,x2313)/L(y776,x1783), f−85.85/−85.85; u1640 R(755,2291)/L(757,1804), f−74.26/−74.79; u1650 R(736,2279)/L(738,1818), f−67.94/−67.42; u1660 R(717,2227)/L(719,1870), f−40.56/−40.03mm.',
        'construction': {'kind': 'Annahme',
            'source': 'Vorhandener zusammenhängender Nackenkern statt Zusatzwand: gerundetes Rückprofil u1630/−85,1640/−75,1650/−68,1660/−40. Front und x-Halbbereite werden exakt zwischen ursprünglichen Halsringen interpoliert. Basis1598, oberer Anschluss1704, Halsanker und alle Helmteile unverändert. Gemeinsame Seitenkontur bei1630/1640 enthält auch Schultermasse; Zuordnung als enge Nackenbasis aus beiden Farboriginalen, keine Behauptung bestandener Bildabnahme.'}},
    'neck': {'kind': 'Vorgabe', 'at': [35, 1690, 0], 'collar_overlap_u_mm': [1598, 1630],
             'source': 'Shared upper_body Socket_Neck and collar contract, 26.10.2026'},
}
PARTS = []
ANCHORS = {}


def _part(name, role, source, **shape):
    p = dict(id='head_' + name, assembly='head', role=role, bevel=0,
             provenance={'kind': 'Annahme', 'source': source}, **shape)
    PARTS.append(p)
    return p['id']


def _closed(vertices, faces):
    faces = [[face[0], face[i], face[i+1]]
             for face in faces for i in range(1, len(face)-1)]
    def det(a, b, c):
        return (a[0]*(b[1]*c[2]-b[2]*c[1])
                - a[1]*(b[0]*c[2]-b[2]*c[0])
                + a[2]*(b[0]*c[1]-b[1]*c[0]))
    if sum(det(vertices[a], vertices[b], vertices[c]) for a, b, c in faces) > 0:
        faces = [list(reversed(face)) for face in faces]
    return dict(shape='surface', vertices=vertices, faces=faces)


def _wall(outer, inner, faces, wall=4):
    """Explicit interior and boundary rims; no solid proxy for a shell."""
    n = len(outer)
    uses = {}
    for face in faces:
        for a, b in zip(face, face[1:] + face[:1]):
            uses.setdefault(tuple(sorted((a, b))), []).append((a, b))
    closed = faces + [[n+i for i in reversed(face)] for face in faces]
    for pair in uses.values():
        if len(pair) == 1:
            a, b = pair[0]
            closed.append([b, a, n+a, n+b])
    return dict(**_closed(outer+inner, closed), wall_mm=wall)


def _ring_point(row, angle, inset=0):
    u, w, front, back = row
    middle = (front+back)/2
    return [middle+((front-back)/2-inset)*math.cos(angle), u,
            (w-inset)*math.sin(angle)]


def _strip(rows, angle_rows, wall=4):
    n = len(angle_rows[0])
    outer = [_ring_point(row, a) for row, angles in zip(rows, angle_rows) for a in angles]
    inner = [_ring_point(row, a, wall) for row, angles in zip(rows, angle_rows) for a in angles]
    faces = [[j*n+i, j*n+i+1, (j+1)*n+i+1, (j+1)*n+i]
             for j in range(len(rows)-1) for i in range(n-1)]
    return _wall(outer, inner, faces, wall)


# Pixel outlines rounded to mm. Side controls f extent; front controls widths/u.
LOW_ROWS = [(1680, 43, 166, 41), (1695, 77, 174, -29),
            (1710, 111, 179, -31), (1726, 119, 182, -45),
            (1752, 122, 188, -60), (1778, 123, 189, -76),
            (1804, 120, 188, -79), (1831, 119, 182, -74),
            (1852, 110, 175, -66), (1868, 103, 165, -57)]
face_angles = [math.radians(-74+i*148/12) for i in range(13)]
rear_angles = [math.radians(76+i*208/18) for i in range(19)]
mask = _part('face_mask', 'graphite',
             'Gemessen: Front schwarze Gesichtsflaeche y330..650; side-right gewoelbtes Profil x1791..1831. Annahme: separate 4mm Maske, seitlich 2° Fuge.',
             **_strip(LOW_ROWS, [face_angles]*len(LOW_ROWS)))
_part('rear_housing', 'graphite',
      'Gemessen: eigene rueckwaertige Helmkontur und dunkle untere Rueckenschale. Annahme: 4mm Wand und verdeckter Innenraum.',
      **_strip(LOW_ROWS, [rear_angles]*len(LOW_ROWS)))

CROWN_ROWS = [(1868, 103, 165, -57), (1884, 94, 152, -46),
              (1894, 85, 142, -36), (1905, 72, 127, -21),
              (1915, 54, 107, -4), (1921, 34, 87, 16),
              (1924, 15, 64, 43)]
full_angles = [i*math.tau/24 for i in range(25)]
_part('crown_base', 'graphite',
      'Gemessen: Front y223..330 und Seitenprofil Helmkuppel. Annahme: 4mm tragende Schale mit dunklem Mittelstreifen.',
      **_strip([(u,w-4,front-4,back+4) for u,w,front,back in CROWN_ROWS],
               [full_angles]*len(CROWN_ROWS)))
# Top closure is a real four-millimetre plate at exactly u1924.
top = [_ring_point(CROWN_ROWS[-1], i*math.tau/24) for i in range(24)]
_part('crown_top', 'graphite', 'Annahme: verdeckter Deckel unter der schmalen oberen Mittelkuppe, 4mm Wand.',
      **_wall(top, [[f,u-4,x] for f,u,x in top], [list(range(24))]))
for suffix, sign in [('l', 1), ('r', -1)]:
    angles = []
    for _, width, _, _ in CROWN_ROWS:
        edge = math.asin(min(30, width*.52)/width)
        angles.append([sign*(edge+i*(math.pi-2*edge)/12) for i in range(13)])
    _part('crown_shell_'+suffix, 'shell',
          'Gemessen: helle Kronenhaelfte beidseits des Graphitstreifens. Annahme: echte 4mm Radialwand, feine Facetten und offene Trennfuge.',
          **_strip(CROWN_ROWS, angles))

# Independent ear bowl: a faceted elliptical plate, shallow raised rim.
for suffix, sign in [('l', 1), ('r', -1)]:
    outer, inner = [], []
    for fraction, x in [(1, 119), (.88, 127), (.45, 128)]:
        for i in range(24):
            t = i*math.tau/24
            falloff = (14 if math.sin(t)>0 else 29)*(fraction*math.sin(t))**2
            outer.append([21+80*fraction*math.cos(t), 1784+85*fraction*math.sin(t), sign*(x-falloff)])
            inner.append([21+80*fraction*math.cos(t), 1784+85*fraction*math.sin(t), sign*(x-falloff-4)])
    faces = [[j*24+i,j*24+(i+1)%24,(j+1)*24+(i+1)%24,(j+1)*24+i]
             for j in range(2) for i in range(24)]
    faces.append(list(range(48,72)))
    _part('ear_shell_'+suffix, 'shell',
          'Gemessen: side-right Ohrschale etwa x1960..2240/y306..634; Front Seitenschalen. Annahme: leicht elliptische Schale mit 4mm x-Wand.',
          **_wall(outer, inner, faces))
    _part('ear_joint_'+suffix, 'dark_metal',
          'Gemessen: side-right Ringscheibe Mitte x2115/y487, r≈76px. Annahme: Radius41mm und axiale Tiefe10mm, nicht leuchtend.',
          shape='cyl', axis='x', c=[21, 1784], a0=sign*127, a1=sign*137,
          r=41, r_in=24, segs=32)
    _part('ear_hub_'+suffix, 'anodized',
          'Annahme: geschlossene Nabenabdeckung der Ohrscheibe, Radius23mm, keine Cyan-Funktion.',
          shape='cyl', axis='x', c=[21, 1784], a0=sign*127, a1=sign*135,
          r=23, segs=32)

# Cheek/chin shell stays distinct from the black face mask.
for suffix, sign in [('l', 1), ('r', -1)]:
    outer = [[164,1687,sign*43], [161,1699,sign*72], [157,1727,sign*88],
             [177,1722,sign*45], [177,1701,sign*39]]
    _part('chin_shell_'+suffix, 'shell',
          'Gemessen: helle Kinnwangen Front y585..680, schwarze Mitte; side-right untere Frontwange. Annahme: 4mm f-Wand und f-Interpolation.',
          **_wall(outer, [[f-4,u,x] for f,u,x in outer], [[0,1,2,3,4]]))

# Rear reference has one broad shell above its dark nape cut-out.
rear = [[-60,1847,-83],[-69,1847,0],[-60,1847,83],
        [-75,1800,-86],[-82,1794,0],[-75,1800,86],
        [-60,1781,-68],[-70,1788,0],[-60,1781,68]]
_part('occipital_shell', 'shell',
      'Gemessen: Back breite helle Hinterkopfplatte y365..512 mit nach innen gefalteter Unterkante. Annahme: f-Tiefen aus beiden Seiten; 4mm Wand.',
      **_wall(rear, [[f+4,u,x] for f,u,x in rear],
              [[0,1,4,3],[1,2,5,4],[3,4,7,6],[4,5,8,7]]))

# The single emissive head feature follows the round black face, not ear joints.
visor_outer = []
for u in [1783, 1805]:
    for x in [-73,-67,-48,-24,0,24,48,67,73]:
        visor_outer.append([190-22*(abs(x)/73)**2,u,x])
# Narrow bevelled ends are geometry, not text or a painted decal.
visor_outer[0][1] += 5
visor_outer[8][1] += 5
visor_outer[9][1] -= 5
visor_outer[17][1] -= 5
_part('visor', 'energy',
      'Gemessen: Front horizontaler Lichtschlitz x≈1908..2188/y449..493; 148x23mm gerundet. Annahme: folgt Gesichtskruemmung; einzig leuchtendes Kopfteil.',
      **_wall(visor_outer, [[f-3,u,x] for f,u,x in visor_outer],
              [[i,i+1,10+i,9+i] for i in range(8)], wall=3))

# Neck enters the upper-body collar at1598 and overlaps the helmet below1690.
neck = _part('neck_core', 'graphite',
             'Vorgabe: Socket_Neck f35/u1690/x0 und Kragen1598..1630. Gemessen: Hals Front x≈1905..2195 und gemeinsame hintere Nackenbasis PROVENANCE.nape_profile_revision_1. Annahme: bestehender Lastkern mit gerundetem Rückprofil, unveränderte Front-/Breiteninterpolation.',
             shape='loft', rings=[[[f,u,x] for f,x in
                 [(front,-.7*w),(front,.7*w),(front-12,w),(back+12,w),
                  (back,.7*w),(back,-.7*w),(back+12,-w),(front-12,-w)]]
                 for u,w,front,back in [(1598,61,75,-30),(1630,64,79,-85),
                                         (1640,64+3*10/35,79+6*10/35,-75),
                                         (1650,64+3*20/35,79+6*20/35,-68),
                                         (1660,64+3*30/35,79+6*30/35,-40),
                                         (1665,67,85,-33),(1704,60,83,-29)]])
for suffix, sign in [('l', 1), ('r', -1)]:
    _part('neck_strut_'+suffix, 'dark_metal',
          'Gemessen: seitliche Halsstreben bis unter Kinn. Annahme: Radius10mm, keine leuchtenden Streben.',
          shape='loft', rings=[[[f+10*math.cos(i*math.tau/12),u,
                                 sign*(x+10*math.sin(i*math.tau/12))] for i in range(12)]
                               for f,u,x in [(65,1610,52),(57,1653,64),(30,1713,64)]])
_part('neck_bellows', 'dark_metal',
      'Gemessen: dunkle horizontale Halsfalten. Annahme: vier getrennte 5mm Lamellen vor dem Kern, gemeinsam ein logisches Bauteil.',
      shape='multi', items=[dict(shape='box', f0=78, f1=86, u0=u, u1=u+5,
                                w=77, x=0) for u in [1638,1652,1666,1680]])
ANCHORS = {
    'Socket_Neck': {'at': [35,1690,0], 'part': neck,
                    'source': 'Vorgabe: gemeinsamer upper_body/head Anschluss; Hals ab1598 in Kragen integriert'},
    'Socket_Head': {'at': [35,1690,0], 'part': mask,
                    'source': 'Annahme: Kopfdrehpunkt koaxial zum gemeinsamen Socket_Neck'},
}
