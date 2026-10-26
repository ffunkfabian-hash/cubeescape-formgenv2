"""BASIC-Roboterarm v2 (Stil v2.1): eigene Datenquelle für Ober-/Unterarm, Kardan-Handgelenk, Hand mit vier Fingern und Daumen.

Getrennt von Toolgen (Entscheidung des Nutzers 24.10.2026: „so wie die Waffen, möglichst separat halten“). Längen, Gelenkgrenzen und
Fingerteilung sind **Startwerte aus Toolgen** `data/ego_arms.json` (Rig-Version 2) und `data/viewmodels.json › arm` – übernommen mit
Quelle, nicht verlinkt. Querschnitte, Panzer und Handvolumen sind v2-Entwurf (v1 wirkte drahtig, siehe robot_arm_v1.py).

v2-Formprinzipien (Inspiration aus Nutzerbildern Q-D2-ARM, nur Prinzipien): Panzer umschließt das Glied statt als Brett aufzuliegen,
Unterarm verjüngt sich zum Handgelenk, flache Facetten mit Grat (Walmdach), großes Ellbogengelenk, Stulpe überlappt die Hand,
höchstens eine Akzentlinie je Glied. Schlicht: keine Stacheln, kein Leuchten.

Segmentrahmen (mm, rechtshändig): Ursprung im Gelenk am Segmentanfang, +Z entlang des Segments, +Y Außen-/Rückseite
(Panzerseite, Handrücken), −Y Innen-/Handflächenseite, +X Daumenseite der rechten Hand (linke Hand: Daumen auf −X).
Jedes Teil: (id, de, Segment, Form, Rolle, Parameter). Formen: box (d, c), cyl (axis, r, len, c), prism (Achteck entlang Z: r0, r1,
len, c), plate (Facettenplatte: z, w, r, t, ridge, hip, phi, u – siehe tools/ego_build.plate_verts).
"""

SOURCE = 'Toolgen data/ego_arms.json (rig v2) und data/viewmodels.json › arm, gelesen 24.10.2026; Längen als Startwerte übernommen'
RIG_VERSION = 3

HAND_SCALE = 0.65 * 1.4          # viewmodels.arm.hand_scale × ego_arms.rig.scale (Handeinheiten → Meter im Bild)
HAND_BULK = 1.20                 # v2/v3: Handfläche und Finger kräftiger (entworfen; v2 1,12)
ARM_BULK = 1.15                  # v3: Querschnitt Ober-/Unterarm und Ellbogen (Nutzer: „etwas massiver“, entworfen)
UPPER_MM, FORE_MM = 320.0, 300.0  # viewmodels.arm.upper_length_m / forearm_length_m
# Kameraraum (Blender: rechts −X, vorn −Y, oben +Z). L = Toolgen-Startwert (weit vorn, damit die Stützhand den Handschutz erreicht);
# R entworfen (Toolgen-Wert −0,10/−0,30/−0,40 knickte den Arm an der BASIC-Hüfte zu stark)
SHOULDER = {'R': (-0.20, -0.05, -0.45), 'L': (0.06, -0.48, -0.48)}
ELBOW_POLE = (-0.5, 0.2, -1.0)   # rechter Ellbogen nach unten außen (links gespiegelt); Toolgen-Start (0,2/0/−1)
WRIST_LIMIT_DEG = 55        # Toolgen ego_arms.limits_degrees.wrist_limit
WRIST_TARGET_DEG = 45       # Toolgen wrist_target
FOREARM_PREF = (-0.30, 0.55, -0.78)   # Handgelenk → Ellbogen, rechter Arm (links gespiegelt): hinten, unten, außen (E)

_s = HAND_SCALE * 1000            # Handeinheiten (m) → mm im Bild
PALM_START, PALM_LEN = 0.014 * _s, 0.082 * _s
PALM_W, PALM_T = 0.086 * _s * HAND_BULK, 0.042 * _s * HAND_BULK
KNUCKLE_Z = 0.096 * _s
FINGER_X = [30.5, 10.2, -10.2, -30.5]         # v2: vier Finger (Zeige-, Mittel-, Ring-, kleiner Finger), Teilung 20,3 mm (entworfen)
FINGER_SCALE = [1.0, 1.06, 1.0, 0.84]       # Länge je Finger relativ zu FINGER_LINKS
FINGER_LINKS = [0.034 * _s, 0.027 * _s, 0.022 * _s]
FINGER_W, FINGER_D = 18.2, 0.020 * _s * HAND_BULK
THUMB_BASE = (0.046 * _s * HAND_BULK, 0.002 * _s, 0.030 * _s)
THUMB_DIR = (0.55, -0.35, 0.75)
THUMB_LINKS = [0.036 * _s, 0.028 * _s, 0.022 * _s]

# Fingerstellungen (Grad je Glied; Daumen: Beugung, Abspreizung, Spitze). Startwerte aus ego_arms.finger_poses, wo fest
# angegeben (open, regrip); Werte für wrap-Posen hier am Griff der Pilotwaffe eingestellt (entworfen).
FINGER_POSES = {
    'open':     dict(f=[[4, 4, 3]] * 4, t=[6, 34, 4]),
    'relaxed':  dict(f=[[14, 18, 12], [18, 22, 14], [22, 26, 16], [26, 30, 18]], t=[12, 30, 8]),
    'grip':     dict(f=[[62, 74, 48]] * 4, t=[38, 12, 30]),
    'trigger':  dict(f=[[20, 30, 18], [62, 74, 48], [64, 76, 50], [66, 78, 52]], t=[38, 12, 30]),
    'underhand': dict(f=[[52, 66, 44]] * 4, t=[20, 10, 16]),
    'mag_hold': dict(f=[[36, 46, 30]] * 4, t=[30, 24, 20]),
    'pinch':    dict(f=[[46, 56, 36], [70, 80, 56], [74, 82, 58], [76, 84, 60]], t=[46, 18, 34]),
}

APOTHEM = 0.924   # Achteck: Abstand Fläche/Achse = 0,924 × Eckradius


def plate(z, w, r, t, ridge, hip, phi=0.0, u=0.0):
    return dict(z=z, w=w, r=r, t=t, ridge=ridge, hip=hip, phi=phi, u=u)


def ridge_line(p, width=3.2, depth=1.6):
    """Akzentlinie auf dem Grat einer Facettenplatte (gleiche Neigung wie die Grundfläche)."""
    (z0, z1), (r0, r1) = p['z'], p['r']
    za, zb = z0 + p['hip'][0], z1 - p['hip'][1]

    def r(z):
        return r0 + (r1 - r0) * (z - z0) / (z1 - z0) + p['t'] + p['ridge'] - depth * 0.6
    return plate((za, zb), (width, width), (r(za), r(zb)), depth, 0.0, (0.0, 0.0), p['phi'], p['u'])


def section(w, y0, y1, ch, z):
    """Gefaster Rechteckquerschnitt (8 Punkte, mm) bei z: Breite w, von y0 (innen) bis y1 (außen), Fase ch."""
    return [(sx * w / 2, y, z) for sx in (-1, 1) for y in (y0 + ch, y1 - ch)] + \
           [(sx * (w / 2 - ch), y, z) for sx in (-1, 1) for y in (y0, y1)]


def section_top(w, y0, y1, ch, z, z_top=None):
    """Obere Hälfte eines gefasten Querschnitts (Schale): Seiten bei z, Deckfläche bei z_top (Pfeilschnitt, wenn verschieden)."""
    zt = z if z_top is None else z_top
    return [(sx * w / 2, y0, z) for sx in (-1, 1)] + [(sx * w / 2, y1 - ch, z) for sx in (-1, 1)] + \
           [(sx * (w / 2 - ch), y1, zt) for sx in (-1, 1)]


def _bulk(P, k):
    """Querschnitt (X/Y) der Teile von Ober- und Unterarm um k skalieren; Längen (Z) bleiben."""
    out = []
    for pid, de, seg, kind, role, p in P:
        if seg in ('upper', 'fore'):
            p = dict(p)
            if 'pts' in p:
                p['pts'] = [(x * k, y * k, z) for x, y, z in p['pts']]
            if 'c' in p:
                p['c'] = (p['c'][0] * k, p['c'][1] * k, p['c'][2])
            if kind == 'cyl':
                p['r'] = p['r'] * k
                if p['axis'] != 'z':
                    p['len'] = p['len'] * k
        out.append((pid, de, seg, kind, role, p))
    return out


def parts():
    """Teile je Segment: (id, de, segment, form, rolle, params). Maße in mm im Segmentrahmen."""
    P = []
    # Oberarm (meist außerhalb des Bildes): Graphitkörper, Cremeschale mit Pfeilschnitt zum Ellbogen
    P += [('upper_body', 'Oberarmkörper', 'upper', 'hull', 'graphite',
           dict(pts=section(104, -48, 44, 18, 20) + section(112, -50, 48, 18, 150) + section(92, -42, 38, 16, 300))),
          ('upper_shell', 'Oberarmschale', 'upper', 'hull', 'shell',
           dict(pts=section_top(112, -20, 54, 22, 40) + section_top(120, -22, 58, 22, 150) + section_top(100, -16, 48, 20, 276, z_top=300)))]
    # Ellbogen: großes Gelenk, seitlich Scheibe mit blankem Ring (Medaillon)
    P += [('elbow', 'Ellbogengelenk', 'fore', 'cyl', 'dark_metal', dict(axis='x', r=40, len=92, c=(0, 0, 0))),
          ('elbow_disc', 'Ellbogenscheibe', 'fore', 'cyl', 'graphite', dict(axis='x', r=36, len=98, c=(0, 0, 0))),
          ('elbow_ring', 'Ellbogenring', 'fore', 'cyl', 'trim', dict(axis='x', r=27, len=102, c=(0, 0, 0))),
          ('elbow_hub', 'Ellbogennabe', 'fore', 'cyl', 'graphite', dict(axis='x', r=19, len=104, c=(0, 0, 0)))]
    # Unterarm: Graphitkörper mit Wölbung (104 mm bei z 100) → 60 mm am Handgelenk, glatte Cremeschale mit Pfeilschnitt, zweite dunkle Lage am Handgelenk mit zwei Bolzen,
    # eine Akzentlinie, Stulpe mit blanker Kante
    sh0, shm, sh1 = (104, -18, 48, 20, 58, 34), (112, -20, 52, 22, 100, 100), (68, -10, 32, 13, 250, 250)   # w, y0, y1, Fase, z Seiten, z Mitte
    def shell_top(z):           # Deckfläche der Schale (stückweise linear über die drei Querschnitte)
        a, b = (sh0, shm) if z <= shm[5] else (shm, sh1)
        return a[2] + (b[2] - a[2]) * (z - a[5]) / (b[5] - a[5])
    P += [('fore_body', 'Unterarmkörper', 'fore', 'hull', 'graphite',
           dict(pts=section(92, -42, 36, 16, 24) + section(104, -48, 42, 18, 100) + section(60, -27, 23, 10, 262))),
          ('fore_shell', 'Unterarmschale', 'fore', 'hull', 'shell',
           dict(pts=section_top(*sh0[:5], z_top=sh0[5]) + section_top(*shm[:5], z_top=shm[5]) + section_top(*sh1[:5], z_top=sh1[5]))),
          ('fore_inset', 'Akzentlinie', 'fore', 'hull', 'accent',
           dict(pts=[(sx_, shell_top(z) + dy, z) for z in (52, 132) for sx_ in (-1.6, 1.6) for dy in (-0.8, 0.9)])),
          ('fore_top', 'Handgelenkplatte', 'fore', 'hull', 'anodized',
           dict(pts=[(x, shell_top(z) + dy, z) for z, w in ((176, 56), (260, 42)) for x in (-w / 2, w / 2) for dy in (-3, 7)]
                + [(0, shell_top(z) + dy, z) for z in (140,) for dy in (-3, 7)])),
          ('fore_bolt_a', 'Bolzen', 'fore', 'cyl', 'trim', dict(axis='y', r=4.2, len=4, c=(-14, shell_top(230) + 8, 230))),
          ('fore_bolt_b', 'Bolzen', 'fore', 'cyl', 'trim', dict(axis='y', r=4.2, len=4, c=(14, shell_top(230) + 8, 230))),
          ('fore_cuff', 'Stulpe', 'fore', 'hull', 'dark_metal', dict(pts=section(72, -32, 36, 16, 264) + section(76, -34, 38, 17, 296))),
          ('fore_cuff_trim', 'Stulpenkante', 'fore', 'hull', 'trim', dict(pts=section(75, -33.5, 37.5, 16.5, 262) + section(75, -33.5, 37.5, 16.5, 266)))]
    # Hand: Kardanblock (in der Stulpe), Handfläche, Handrückenschale mit Grat, Knöchelschutz, Daumensockel
    back = plate((-4, KNUCKLE_Z - 14), (66, PALM_W - 6), (PALM_T / 2 - 1, PALM_T / 2 - 1), 5, 9, (22, 14))
    P += [('wrist_block', 'Kardanblock', 'hand', 'box', 'dark_metal', dict(d=(36, 32, 24), c=(0, 0, 2), bevel=3)),
          ('wrist_pin', 'Kardanbolzen', 'hand', 'cyl', 'trim', dict(axis='x', r=8, len=42, c=(0, 0, 2))),
          ('palm', 'Handfläche', 'hand', 'box', 'graphite',
           dict(d=(PALM_W, PALM_T, PALM_START + PALM_LEN - 6), c=(0, 0, (PALM_START + PALM_LEN + 6) / 2), bevel=6)),
          ('back_plate', 'Handrückenschale', 'hand', 'plate', 'shell', back),
          ('back_inset', 'Handrücken-Akzentlinie', 'hand', 'plate', 'accent', ridge_line(back, 2.8, 1.4)),
          ('knuckles', 'Knöchelwelle', 'hand', 'cyl', 'dark_metal', dict(axis='x', r=10, len=PALM_W - 4, c=(0, 2, KNUCKLE_Z - 4))),
          ('knuckle_guard', 'Knöchelschutz', 'hand', 'plate', 'dark_metal',
           plate((KNUCKLE_Z - 16, KNUCKLE_Z + 2), (PALM_W + 2, PALM_W + 2), (PALM_T / 2, PALM_T / 2), 5, 4, (5, 5))),
          ('thumb_mount', 'Daumensockel', 'hand', 'box', 'graphite',
           dict(d=(22, 30, 34), c=(THUMB_BASE[0] - 7, THUMB_BASE[1], THUMB_BASE[2]), bevel=5))]
    # Finger: je Glied Kern, Facettenplatte, Gelenk (vier Finger)
    for i in range(len(FINGER_X)):
        for j, L0 in enumerate(FINGER_LINKS):
            L = L0 * FINGER_SCALE[i]
            seg = f'f{i}_{j}'
            P += [(f'{seg}_core', f'Finger {i + 1} Glied {j + 1}', seg, 'box', 'graphite',
                   dict(d=(FINGER_W - 2, FINGER_D - 2, L - 4), c=(0, 0, L / 2), bevel=2.5)),
                  (f'{seg}_plate', f'Finger {i + 1} Glied {j + 1} Platte', seg, 'plate', 'shell',
                   plate((2, L - 2), (FINGER_W - 3, FINGER_W - 4), (FINGER_D / 2 - 2, FINGER_D / 2 - 2), 3, 3, (L * 0.3, L * 0.25))),
                  (f'{seg}_joint', f'Finger {i + 1} Gelenk {j + 1}', seg, 'cyl', 'dark_metal',
                   dict(axis='x', r=7, len=FINGER_W, c=(0, 0, 0)))]
    for j, L in enumerate(THUMB_LINKS):
        seg = f't_{j}'
        P += [(f'{seg}_core', f'Daumen Glied {j + 1}', seg, 'box', 'graphite',
               dict(d=(FINGER_W + 2, FINGER_D + 1, L - 4), c=(0, 0, L / 2), bevel=2.5)),
              (f'{seg}_plate', f'Daumen Glied {j + 1} Platte', seg, 'plate', 'shell',
               plate((2, L - 2), (FINGER_W - 2, FINGER_W - 3), (FINGER_D / 2 - 1.5, FINGER_D / 2 - 1.5), 3, 3, (L * 0.3, L * 0.25))),
              (f'{seg}_joint', f'Daumengelenk {j + 1}', seg, 'cyl', 'dark_metal', dict(axis='x', r=7.6, len=FINGER_W + 3, c=(0, 0, 0)))]
    return _bulk(P, ARM_BULK)


SEGMENTS = (['upper', 'fore', 'hand'] + [f'f{i}_{j}' for i in range(len(FINGER_X)) for j in range(3)] + [f't_{j}' for j in range(3)])
