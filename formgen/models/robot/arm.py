# Einmalig übertragen aus BALLON Commit 14bd78d (basic/arms/robot_arm.py); BALLON bleibt Lesereferenz, keine Laufzeitabhängigkeit.
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

# 0.14 Kitbash: Maße von Unterarm und Hand als Parameter (PARAMS['forearm'], PARAMS['hand'] beider Typen); Standard = genau die Zahlen,
# die parts() bis 0.13 fest trug (Grundform bytegleich). Schnittstelle: parts(fore, hand) baut die Teile, dims(hand) liefert die Maße für
# rig.arm_segments (Finger, Daumen, Längen). Herkunft wie im Modulkopf: Handmaße und Fingerteilung Toolgen-Startwerte (× HAND_SCALE,
# HAND_BULK), Querschnitte, Panzer und Ellbogen v2-Entwurf. Alle mm im Segmentrahmen, vor ARM_BULK und arm_bulk der Typen.
# Zusatzformen (Varianten, catalog/arms.py) sind None = aus; ihre Zahlen stehen mit Herkunft im Katalog.
FOREARM: dict = dict(
    elbow=((40, 92), (36, 98), (27, 102), (19, 104)),     # (r, Länge X) Gelenk, Scheibe, blanker Ring, Nabe (v2-Entwurf)
    body=((92, -42, 36, 16, 24), (104, -48, 42, 18, 100), (60, -27, 23, 10, 262)),   # section(w, y0, y1, Fase, z): Wölbung → Handgelenk
    shell=((104, -18, 48, 20, 58, 34), (112, -20, 52, 22, 100, 100), (68, -10, 32, 13, 250, 250)),   # w, y0, y1, Fase, z Seiten, z Mitte
    inset=(52, 132),                      # Akzentlinie von z bis z auf dem Schalengrat
    top=((176, 56), (260, 42)), top_tip=140, top_t=(-3, 7),    # Handgelenkplatte: (z, Breite), Spitze bei z, Lage über der Schale
    bolts=dict(z=230, dx=14, r=4.2, lift=8),
    cuff=((72, -32, 36, 16, 264), (76, -34, 38, 17, 296)),     # Stulpe section(w, y0, y1, Fase, z)
    cuff_trim=(75, -33.5, 37.5, 16.5, 262, 266),               # blanke Stulpenkante: Querschnitt, von z bis z
    girth=1.0,                            # Querschnittsfaktor X/Y nur der Unterarmteile fore_* (Ellbogen bleibt); 1,0 = Grundform
    guard=None,                           # Armschild über der Schale: dict(z, w, lift, t, ridge, hip)
    ram=None,                             # Stellzylinder an der Innenseite: dict(z, r, y, rod_z, rod_r)
)
HAND: dict = dict(
    palm_start=PALM_START, palm_len=PALM_LEN, palm_w=PALM_W, palm_t=PALM_T, knuckle_z=KNUCKLE_Z,
    finger_x=tuple(FINGER_X), finger_scale=tuple(FINGER_SCALE), finger_links=tuple(FINGER_LINKS), finger_w=FINGER_W, finger_d=FINGER_D,
    thumb_base=THUMB_BASE, thumb_dir=THUMB_DIR, thumb_links=tuple(THUMB_LINKS),
    wrist_block=(36, 32, 24), wrist_pin=(8, 42),                # Kardanblock d, Kardanbolzen (r, Länge)
    back=dict(w0=66, inset=6, z0=-4, end=14, t=5, ridge=9, hip=(22, 14)),     # Handrückenschale: Breite am Gelenk, PALM_W − inset vorn, z bis KNUCKLE_Z − end
    knuckles=10,                                                # Radius der Knöchelwelle
    guard=dict(z=(-16, 2), grow=2, t=5, ridge=4, hip=(5, 5)),   # Knöchelschutz um KNUCKLE_Z, PALM_W + grow breit
    thumb_mount=(22, 30, 34),
    armor=None,                           # Panzerhand: dict(z, w, lift, t, ridge, hip, cheek) großer Knöchelpanzer, Seitenwangen
    claws=None,                           # Krallenaufsatz: dict(x, base, reach, w, t, drop) je Kralle auf dem Handrücken
)

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


def dims(hand=None):
    """Maße der Armkette für rig.arm_segments: Konstanten dieses Moduls, überschrieben durch PARAMS['hand'] (0.14)."""
    from types import SimpleNamespace
    out = SimpleNamespace(**{k: v for k, v in globals().items() if k.isupper()})
    for key, value in (hand or {}).items():
        if key.upper() in vars(out):
            setattr(out, key.upper(), value)
    return out


def parts(fore=None, hand=None):
    """Teile je Segment: (id, de, segment, form, rolle, params). Maße in mm im Segmentrahmen; fore/hand: PARAMS['forearm'], PARAMS['hand']."""
    P = []
    # Oberarm (meist außerhalb des Bildes): Graphitkörper, Cremeschale mit Pfeilschnitt zum Ellbogen
    P += [('upper_body', 'Oberarmkörper', 'upper', 'hull', 'graphite',
           dict(pts=section(104, -48, 44, 18, 20) + section(112, -50, 48, 18, 150) + section(92, -42, 38, 16, 300))),
          ('upper_shell', 'Oberarmschale', 'upper', 'hull', 'shell',
           dict(pts=section_top(112, -20, 54, 22, 40) + section_top(120, -22, 58, 22, 150) + section_top(100, -16, 48, 20, 276, z_top=300)))]
    F, H = _merged(FOREARM, fore, 'forearm'), _merged(HAND, hand, 'hand')
    P += _forearm(F) + _hand(H)
    return _bulk(P, ARM_BULK)


def _merged(base, over, what):
    """Standardmaße mit Überschreibung (eine Ebene tief bei Unter-Dicts); ein unbekannter Schlüssel ist ein Fehler."""
    out = dict(base)
    for key, value in (over or {}).items():
        if key not in out:
            raise ValueError(f'arm.{what}: unbekannter Schlüssel {key}')
        out[key] = dict(out[key], **value) if isinstance(out[key], dict) and isinstance(value, dict) else value
    return out


def _plate_hull(p):
    """Facettenplatte (kit._plate_points, ohne phi/u) als Punktwolke einer Hülle: Ober- und Unterarmteile müssen als pts vorliegen,
    sonst skalieren _bulk und arm_bulk sie nicht mit (Platten im Segment fore lagen in RA01 sonst unter der Schale)."""
    (z0, z1), (w0, w1), (r0, r1), (h0, h1) = p['z'], p['w'], p['r'], p['hip']

    def r(z):
        return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    pts = [(s * w / 2, r(z) + dy, z) for z, w in ((z0, w0), (z1, w1)) for s in (-1, 1) for dy in (0, p['t'])]
    if p['ridge'] > 0:
        pts += [(0, r(z) + p['t'] + p['ridge'], z) for z in (z0 + h0, z1 - h1)]
    return pts


def _girth(P, k):
    """Querschnitt (X/Y) der Unterarmteile fore_* um k skalieren, Längen (Z) und Ellbogen bleiben (Variante, FOREARM['girth']).
    Bolzen behalten ihre Teilung in X und wandern nur mit der Schale nach außen: Eine Verschiebung in X überträgt RA02 heute links
    ungespiegelt (roboterbasic_02_parameters._frame_for spiegelt nur Beine)."""
    if k == 1.0:
        return P
    out = []
    for pid, de, seg, kind, role, p in P:
        if pid.startswith('fore_'):
            p = dict(p)
            if 'pts' in p:
                p['pts'] = [(x * k, y * k, z) for x, y, z in p['pts']]
            if 'c' in p:
                p['c'] = (p['c'][0], p['c'][1] * k, p['c'][2])
            if kind == 'cyl':
                p['r'] = p['r'] * k
        out.append((pid, de, seg, kind, role, p))
    return out


def _forearm(F):
    # Ellbogen: großes Gelenk, seitlich Scheibe mit blankem Ring (Medaillon)
    (er, el), (dr, dl), (rr, rl), (hr, hl) = F['elbow']
    P = [('elbow', 'Ellbogengelenk', 'fore', 'cyl', 'dark_metal', dict(axis='x', r=er, len=el, c=(0, 0, 0))),
         ('elbow_disc', 'Ellbogenscheibe', 'fore', 'cyl', 'graphite', dict(axis='x', r=dr, len=dl, c=(0, 0, 0))),
         ('elbow_ring', 'Ellbogenring', 'fore', 'cyl', 'trim', dict(axis='x', r=rr, len=rl, c=(0, 0, 0))),
         ('elbow_hub', 'Ellbogennabe', 'fore', 'cyl', 'graphite', dict(axis='x', r=hr, len=hl, c=(0, 0, 0)))]
    # Unterarm: Graphitkörper mit Wölbung (104 mm bei z 100) → 60 mm am Handgelenk, glatte Cremeschale mit Pfeilschnitt, zweite dunkle Lage am Handgelenk mit zwei Bolzen,
    # eine Akzentlinie, Stulpe mit blanker Kante
    sh0, shm, sh1 = F['shell']   # w, y0, y1, Fase, z Seiten, z Mitte

    def shell_top(z):           # Deckfläche der Schale (stückweise linear über die drei Querschnitte)
        a, b = (sh0, shm) if z <= shm[5] else (shm, sh1)
        return a[2] + (b[2] - a[2]) * (z - a[5]) / (b[5] - a[5])
    B = F['bolts']
    t0, t1 = F['top_t']
    ct = F['cuff_trim']
    fore = [('fore_body', 'Unterarmkörper', 'fore', 'hull', 'graphite', dict(pts=[q for s in F['body'] for q in section(*s)])),
            ('fore_shell', 'Unterarmschale', 'fore', 'hull', 'shell',
             dict(pts=[q for s in (sh0, shm, sh1) for q in section_top(*s[:5], z_top=s[5])])),
            ('fore_inset', 'Akzentlinie', 'fore', 'hull', 'accent',
             dict(pts=[(sx_, shell_top(z) + dy, z) for z in F['inset'] for sx_ in (-1.6, 1.6) for dy in (-0.8, 0.9)])),
            ('fore_top', 'Handgelenkplatte', 'fore', 'hull', 'anodized',
             dict(pts=[(x, shell_top(z) + dy, z) for z, w in F['top'] for x in (-w / 2, w / 2) for dy in (t0, t1)]
                  + [(0, shell_top(z) + dy, z) for z in (F['top_tip'],) for dy in (t0, t1)])),
            ('fore_bolt_a', 'Bolzen', 'fore', 'cyl', 'trim', dict(axis='y', r=B['r'], len=4, c=(-B['dx'], shell_top(B['z']) + B['lift'], B['z']))),
            ('fore_bolt_b', 'Bolzen', 'fore', 'cyl', 'trim', dict(axis='y', r=B['r'], len=4, c=(B['dx'], shell_top(B['z']) + B['lift'], B['z']))),
            ('fore_cuff', 'Stulpe', 'fore', 'hull', 'dark_metal', dict(pts=[q for s in F['cuff'] for q in section(*s)])),
            ('fore_cuff_trim', 'Stulpenkante', 'fore', 'hull', 'trim', dict(pts=section(*ct[:4], ct[4]) + section(*ct[:4], ct[5])))]
    if F['guard']:              # Armschild: Facettenplatte über der Schale, breiter als sie, mit Grat (Variante)
        g = F['guard']
        z0, z1 = g['z']
        shield = plate((z0, z1), g['w'], (shell_top(z0) + g['lift'], shell_top(z1) + g['lift']), g['t'], g['ridge'], g['hip'])
        fore += [('fore_guard', 'Armschild', 'fore', 'hull', 'shell', dict(pts=_plate_hull(shield))),
                 ('fore_guard_line', 'Armschild-Akzentlinie', 'fore', 'hull', 'accent', dict(pts=_plate_hull(ridge_line(shield, 3.2, 1.6))))]
    if F['ram']:                # Stellzylinder mit blanker Kolbenstange an der Innenseite (−Y), mittig in X (Variante)
        r = F['ram']
        (z0, z1), (q0, q1) = r['z'], r['rod_z']
        fore += [('fore_ram', 'Stellzylinder', 'fore', 'cyl', 'dark_metal', dict(axis='z', r=r['r'], len=z1 - z0, c=(0, r['y'], (z0 + z1) / 2))),
                 ('fore_ram_rod', 'Kolbenstange', 'fore', 'cyl', 'trim', dict(axis='z', r=r['rod_r'], len=q1 - q0, c=(0, r['y'], (q0 + q1) / 2))),
                 ('fore_ram_mount', 'Zylinderlager', 'fore', 'hull', 'graphite',
                  dict(pts=[(sx_ * (r['r'] + 4), r['y'] + dy, z0 + dz) for sx_ in (-1, 1) for dy in (-r['r'] / 2, r['r'] + 6) for dz in (0, 16)]))]
    return P + _girth(fore, F['girth'])


def _hand(H):
    # Hand: Kardanblock (in der Stulpe), Handfläche, Handrückenschale mit Grat, Knöchelschutz, Daumensockel
    PW, PT, KZ, PS, PL = H['palm_w'], H['palm_t'], H['knuckle_z'], H['palm_start'], H['palm_len']
    FW, FD, TB = H['finger_w'], H['finger_d'], H['thumb_base']
    bk, gd = H['back'], H['guard']
    back = plate((bk['z0'], KZ - bk['end']), (bk['w0'], PW - bk['inset']), (PT / 2 - 1, PT / 2 - 1), bk['t'], bk['ridge'], bk['hip'])
    P = [('wrist_block', 'Kardanblock', 'hand', 'box', 'dark_metal', dict(d=H['wrist_block'], c=(0, 0, 2), bevel=3)),
         ('wrist_pin', 'Kardanbolzen', 'hand', 'cyl', 'trim', dict(axis='x', r=H['wrist_pin'][0], len=H['wrist_pin'][1], c=(0, 0, 2))),
         ('palm', 'Handfläche', 'hand', 'box', 'graphite',
          dict(d=(PW, PT, PS + PL - 6), c=(0, 0, (PS + PL + 6) / 2), bevel=6)),
         ('back_plate', 'Handrückenschale', 'hand', 'plate', 'shell', back),
         ('back_inset', 'Handrücken-Akzentlinie', 'hand', 'plate', 'accent', ridge_line(back, 2.8, 1.4)),
         ('knuckles', 'Knöchelwelle', 'hand', 'cyl', 'dark_metal', dict(axis='x', r=H['knuckles'], len=PW - 4, c=(0, 2, KZ - 4))),
         ('knuckle_guard', 'Knöchelschutz', 'hand', 'plate', 'dark_metal',
          plate((KZ + gd['z'][0], KZ + gd['z'][1]), (PW + gd['grow'], PW + gd['grow']), (PT / 2, PT / 2), gd['t'], gd['ridge'], gd['hip'])),
         ('thumb_mount', 'Daumensockel', 'hand', 'box', 'graphite',
          dict(d=H['thumb_mount'], c=(TB[0] - 7, TB[1], TB[2]), bevel=5))]
    if H['armor']:              # Panzerhand: großer Knöchelpanzer über Knöchel und Fingerwurzeln, Seitenwangen an der Handfläche (Variante)
        a = H['armor']
        z0, z1 = a['z']
        fist = plate((KZ + z0, KZ + z1), (PW + a['w'][0], PW + a['w'][1]), (PT / 2 + a['lift'], PT / 2 + a['lift']), a['t'], a['ridge'], a['hip'])
        cw, cz0, cz1 = a['cheek']
        P += [('fist_guard', 'Knöchelpanzer', 'hand', 'plate', 'dark_metal', fist),
              ('fist_guard_line', 'Knöchelpanzer-Akzentlinie', 'hand', 'plate', 'accent', ridge_line(fist, 3.0, 1.5))]
        P += [(f'fist_cheek_{k}', 'Handwange', 'hand', 'box', 'shell',
               dict(d=(cw, PT + 6, cz1 - cz0), c=(sx_ * (PW + cw) / 2, 0, (cz0 + cz1) / 2), bevel=4)) for k, sx_ in (('a', -1), ('b', 1))]
    if H['claws']:              # Krallenaufsatz: Klingen vom Handrücken über die Finger hinaus, an der Spitze zur Handfläche gebogen (Variante)
        c = H['claws']
        y0 = PT / 2 + bk['t'] - 2           # auf der Handrückenschale
        for k, x in enumerate(c['x']):
            w, t = c['w'], c['t']
            zb0, zb1 = c['base']
            tip = (x, y0 - c['drop'], KZ + c['reach'])
            pts = [(x + sx_ * w / 2, y0 + dy, z) for sx_ in (-1, 1) for dy in (0, t) for z in (zb0, zb1)]
            pts += [(x + sx_ * w / 4, y0 + t * 0.6 - c['drop'] * 0.55, KZ + c['reach'] * 0.7) for sx_ in (-1, 1)] + [tip]
            P += [(f'claw_{k}', 'Kralle', 'hand', 'hull', 'trim', dict(pts=pts)),
                  (f'claw_{k}_mount', 'Krallenfuß', 'hand', 'box', 'dark_metal',
                   dict(d=(w + 6, t + 4, zb1 - zb0 + 8), c=(x, y0 + t / 2, (zb0 + zb1) / 2), bevel=3))]
    # Finger: je Glied Kern, Facettenplatte, Gelenk (vier Finger)
    for i in range(len(H['finger_x'])):
        for j, L0 in enumerate(H['finger_links']):
            L = L0 * H['finger_scale'][i]
            seg = f'f{i}_{j}'
            P += [(f'{seg}_core', f'Finger {i + 1} Glied {j + 1}', seg, 'box', 'graphite',
                   dict(d=(FW - 2, FD - 2, L - 4), c=(0, 0, L / 2), bevel=2.5)),
                  (f'{seg}_plate', f'Finger {i + 1} Glied {j + 1} Platte', seg, 'plate', 'shell',
                   plate((2, L - 2), (FW - 3, FW - 4), (FD / 2 - 2, FD / 2 - 2), 3, 3, (L * 0.3, L * 0.25))),
                  (f'{seg}_joint', f'Finger {i + 1} Gelenk {j + 1}', seg, 'cyl', 'dark_metal',
                   dict(axis='x', r=7, len=FW, c=(0, 0, 0)))]
    for j, L in enumerate(H['thumb_links']):
        seg = f't_{j}'
        P += [(f'{seg}_core', f'Daumen Glied {j + 1}', seg, 'box', 'graphite',
               dict(d=(FW + 2, FD + 1, L - 4), c=(0, 0, L / 2), bevel=2.5)),
              (f'{seg}_plate', f'Daumen Glied {j + 1} Platte', seg, 'plate', 'shell',
               plate((2, L - 2), (FW - 2, FW - 3), (FD / 2 - 1.5, FD / 2 - 1.5), 3, 3, (L * 0.3, L * 0.25))),
              (f'{seg}_joint', f'Daumengelenk {j + 1}', seg, 'cyl', 'dark_metal', dict(axis='x', r=7.6, len=FW + 3, c=(0, 0, 0)))]
    return P


SEGMENTS = (['upper', 'fore', 'hand'] + [f'f{i}_{j}' for i in range(len(FINGER_X)) for j in range(3)] + [f't_{j}' for j in range(3)])
