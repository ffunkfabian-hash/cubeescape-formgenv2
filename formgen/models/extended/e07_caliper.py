"""EXTENDED-07 „Caliper“ – eigenständiger Sci-Fi-Kampfbogen der BASIC-Familie (Formgen v2 0.28 „Quiver“).

Eigenes Modell im BALLON-Kit-Vokabular (reines Python, kein bpy). Keine Teile oder Umbauten von BASIC-07: aus `basic.common` kommen nur
genormte Familienschnittstellen (Pinvisier B1 auf Schiene BRI-22, Schraubenköpfe) und Hilfen (`band`, `cut_box`, `mirror`,
`side_mount`). Bogen-Regel der Familie (BALLON familienmasse.md): Griffstück statt BGM-1, kein Magazin, kein Auswurf. Geladen über
`formgen.extended`, gerendert mit BALLONs unverändertem `tools/blender_build.main` (`tools/extended_render.py`).

Formsprache (Stilhandbuch BALLON §3; Auswahl und Skizzen: docs/extended.md)
- Leitmerkmal Klammer: Ein kurzer, tief eingezogener Bügel (Deflex-Riser, die Griffstelle liegt hinten) trägt an seinen Enden zwei
  schwere Wurfarmtaschen; die Wurfarme laufen von dort fast parallel nach hinten (Past-Parallel) zu großen Rollen. Mit der Sehne
  schließt sich die Form zu einer Klammer ⊐ – kurz und tief statt der hohen Sichel von BASIC-07.
- Silhouette: Spanne 0,80 m (BASIC-07 1,02 m), Rollen hinter den Ecken; der Bügel krümmt sich zum Schützen, die Ecken stehen vorn.
- Querschnitt: Keilrippe – der Bügel hat eine schmale Vorderkante (zwei Fasen) und eine breite, flache Rückseite zum Schützen;
  die Flanken tragen ein Flankenfeld 2 mm tief.
- Negativraum: das Sichtfenster im Bügel (Pfeil und Blick frei, Fensterbogen links), zwei Rippenschlitze oben und unten im Bügel,
  die gegabelten Wurfarmenden mit der Rolle dazwischen und der Raum der Klammer.
- Blickfang (genau einer): das Spannlicht als liegender Halbmond links am Fensterbogen, leuchtet bei vollem Auszug.
- Zweiton: Creme-Bügel (`shell`) gegen Graphit-Wurfarme, eloxierte Taschen, Rollen `dark_metal`, Griffstück Gummi.
- Visierbefestigung: Höhenschlitten – eine Schelle umgreift die Vorderkante des Fensterbogens (zwei Klemmschrauben, Höhenskala darüber),
  ein Querarm trägt die Schiene über dem Pfeil (eigene Lösung; keine Konsole aus der Schale wie EA14).
- Sehne lesbar über Volumen: Sehne Ø 4,4 mm mit Mittelwicklung Ø 7 am Nockpunkt und Endwicklungen an den Rollen (begründete Ausnahme der
  Stiftprüfung: eine Sehne ist dünn).
- Grafik: ein oranger Streifen links an der oberen Wurfarmtasche; eine Schrift links unten am Bügel.
- Front mehrstufig: Pfeilspitze (dunkle Schneide, blanke Hülse) → Visierring → Schlitten → Bügel mit Fasen → Taschen.
- Ergonomie: Griffstück mit Handballenwölbung (R_SOFT) hinten am Bügel, Pfeilauflage direkt über der Hand im Fenster, Zughand am
  Nockpunkt. Akzent-Bedienfunktionen: Leitfeder (Pfeil) und Klemmhebel des Visiers (Baustein) – keine weiteren.

Herkunft der Zahlen: V = Vorgabe (Familie/Schnittstelle, BASIC-07 Pilot v2.1 bzw. `basic.common`), A = Annahme (Entwurf 0.28),
G = gemessen; Zahlen ohne Kennung sind A (Entwurf 0.28, an den Renders gesichtet).
Maße mm; f nach vorn, u nach oben, x nach links; Socket_Hand = (0, 0, 0). Der Bogen steht senkrecht (u = Spanne).
"""
import math

from basic.common import (part, prof, box, cyl, cut_box, screws, mirror, rail, band, pins, side_mount, PINS_SIZES, PINS_LINE,
                          R_BODY, R_MID, R_SMALL, R_FINE, R_SOFT)
from basic.reticles import SIGHT
from basic.variant import collect

META = dict(id='EXTENDED-07', num='E07', sheet_id='EA07', type='combat_bow', type_de='Bogen', type_en='Combat Bow',
            family='BASIC', name='Caliper', nick='Klammer', ammo='primary', fire='draw_release',
            reference_length_m=0.796, reference_axis='height_m',
            reference_length_source='G: Spanne (Höhe) des Datensatzes 0.28; BASIC-07 1,02 m (V) als Rahmen, bewusst kürzer',
            reference_note='Bogen: Bezug ist die größte Ausdehnung (Höhe), Länge = Pfeilrichtung',
            inspired_by='BASIC-07 Familie; Formgen v1 als Haltung (eine mutige Gesamtarchitektur)',
            summary='Kampfbogen als Klammer: tief eingezogener Bügel, fast parallele Wurfarme nach hinten zu großen Rollen, '
                    'Pinvisier B1 auf einem Höhenschlitten (EXTENDED-Reihe).')
ASSEMBLIES = [
    dict(id='riser', de='Mittelstück', en='Riser'),
    dict(id='limbs', de='Wurfarme', en='Limbs'),
    dict(id='string', de='Sehne', en='String'),
    dict(id='arrow', de='Pfeil', en='Arrow'),
    dict(id='sight', de='Visier', en='Sight'),
    dict(id='grip_controls', de='Griff und Bedienung', en='Grip and controls'),
]

ARROW_U = 46                 # V: Pfeilachse über der Griffachse wie BASIC-07 (Auflage direkt über der Hand)
BORE = ARROW_U               # V: Schussachse für die Visierhöhe
STRING_F = -150              # V: Standhöhe 150 mm hinter der Griffachse wie BASIC-07
DRAW = 420                   # V: Auszug wie BASIC-07 (Nockpunkt f −150 → −570)
EYE_BEHIND = 20              # V: Augenpunkt 20 mm hinter dem Nockpunkt bei vollem Auszug
CAM_R = 32.0                 # A: Rollenradius (BASIC-07 30, V); die Sehne läuft hinten tangential ab
AXLE = (STRING_F + CAM_R, 366)   # A: Rollenachse oben (unten gespiegelt); Sehne bei f −150 tangential
CAM_DEG = 90                 # V: Rollendrehung beim vollen Auszug wie BASIC-07 (≤ 90°, Stilhandbuch)
ARROW = (-150, 505)          # V: Pfeilschaft Nocke bis Spitzenhülse wie BASIC-07
TIP = ARROW[1] + 48          # V: Pfeilspitze
WIN = dict(x_in=28.0, x_out=44.0, u0=36.0, u1=176.0)   # V: Sichtfenster wie BASIC-07 (x_in 28: Sichtkegel über dem Pfeil braucht x ≥ 27)
W_RISER = 30.0               # V: Bügelbreite wie BASIC-07
SIGHT_X = 0                  # V: Visier direkt über dem Pfeil (BASIC-07 seit 0.35)
SIGHT_U = ARROW_U + SIGHT['height_mm'] + 3.5      # V: Visierlinie 69,5 mm über dem Pfeil wie BASIC-07
DECK = SIGHT_U - PINS_SIZES['M'] - PINS_LINE      # V: Schienenoberkante
RAIL = (40, 104)             # V: Schiene BRI-22 wie BASIC-07
POCKET_U = 302               # A: Unterkante der Wurfarmtasche oben (Bügelende); unten gespiegelt
SLOT_U = ((214, 288), (-286, -98))   # A: Rippenschlitze im Bügel oben, unten (u0 < u1)

# Bügel (Seitenprofil): Vorderkante und Rückseite als Catmull-Rom-Bogen, Ecken vorn (Deflex: Griffstelle hinten)
_FRONT = [(92, 318), (72, 214), (58, 120), (52, 40), (50, -40), (56, -120), (70, -214), (92, -318)]   # Runde 3: Bügel 6 mm tiefer
_BACK = [(46, -318), (28, -214), (13, -120), (5, -56), (5, 40), (11, 120), (26, 214), (46, 318)]



def cw(pts):
    """Draufsicht-Profil (f, x) im Uhrzeigersinn: BALLONs `mesh_plan` richtet die Normalen nicht selbst aus (anders als `mesh_xprof`);
    ein Profil gegen den Uhrzeigersinn ergibt einen umgestülpten Körper, als Schneidkörper schneidet er nicht (0.28, Runde 2)."""
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))
    return list(pts[::-1]) if area > 0 else list(pts)

def spline(pts, n=6):
    """Catmull-Rom durch pts (Endpunkte gedoppelt); n Zwischenpunkte je Abschnitt."""
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in range(2)))
    out.append(tuple(pts[-1]))
    return out


FRONT, BACK = spline(_FRONT), spline(_BACK)


def edge_f(line, u):
    """f einer Kante (Liste (f, u), u monoton) in Höhe u."""
    pts = sorted(line, key=lambda q: q[1])
    for (f0, u0), (f1, u1) in zip(pts, pts[1:]):
        if u0 <= u <= u1:
            return f0 + (f1 - f0) * (u - u0) / ((u1 - u0) or 1)
    return pts[0][0] if u < pts[0][1] else pts[-1][0]


def offset(line, d, u0, u1, n=24):
    """Kurve d mm hinter der Vorderkante (bzw. vor der Rückseite bei d < 0) zwischen u0 und u1."""
    return [(edge_f(line, u0 + (u1 - u0) * i / n) - d, u0 + (u1 - u0) * i / n) for i in range(n + 1)]


def slot(u0, u1, w=12.0):
    """Rippenschlitz: Stadion entlang der Bügelmitte (Runde 3: 12 statt 14 mm, Stege 17 mm)."""
    mid = lambda u: (edge_f(FRONT, u) + edge_f(BACK, u)) / 2   # noqa: E731
    n = 12
    us = [u0 + (u1 - u0) * i / n for i in range(n + 1)]
    right = [(mid(u) + w / 2, u) for u in us]
    left = [(mid(u) - w / 2, u) for u in us[::-1]]
    cap1 = [(mid(u1) + w / 2 * math.cos(math.radians(a)), u1 + w / 2 * math.sin(math.radians(a))) for a in range(30, 180, 30)]
    cap0 = [(mid(u0) - w / 2 * math.cos(math.radians(a)), u0 - w / 2 * math.sin(math.radians(a))) for a in range(30, 180, 30)]
    return right + cap1 + left + cap0


_RISER = FRONT + BACK
_rx = (WIN['x_out'] - W_RISER / 2) / 2           # Mitte der Bügelbreite mit Kröpfung (x −15 … 44)
_rw = W_RISER / 2 + WIN['x_out'] + 0.5
_flank = [dict(shape='prof', pts=offset(FRONT, 9, a, b) + offset(BACK, -9, a, b)[::-1], w=4.0, x=sx * (W_RISER / 2 + 0.5))
          for a, b in ((198, 300), (-300, -90)) for sx in (1, -1)]   # Flankenfeld 1,5 mm (Schichtung)
_chamfer = [dict(shape='prof', pts=[(edge_f(FRONT, u) - 8, u) for u in range(a, b + 1, 6)] + [(130, b), (130, a)],
                 w=8, x=sx * (W_RISER / 2 - 3.5 + 4)) for a, b in ((196, 330), (-330, 16)) for sx in (1, -1)]
# Keilrippe: die Vorderkante ist beidseitig 3,5 mm eingezogen (schmale Rippe vorn, breite Rückseite zum Schützen)
P = []
# ---------------------------------------------------------------- Bügel (Mittelstück) mit Sichtfenster, Griffstück, Auflage
P += [
    prof('riser', 'Bügel', 'Riser', 'riser', 'shell',
         'Tief eingezogener Bügel: trägt Wurfarmtaschen, Griffstück, Auflage und Visierschlitten; links gekröpft zum Fensterbogen',
         'Grundkörper', _RISER, _rw, x=_rx,
         cuts=[cut_box(-60, 120, WIN['u0'], WIN['u1'], WIN['x_in'] + W_RISER / 2 + 1, x=(WIN['x_in'] - W_RISER / 2 - 1) / 2),   # Fenster
               cut_box(-60, 120, 196, 340, 30, x=W_RISER / 2 + 15), cut_box(-60, 120, -340, 16, 30, x=W_RISER / 2 + 15),     # schlank
               dict(shape='prof', pts=slot(*SLOT_U[0]), w=60), dict(shape='prof', pts=slot(*SLOT_U[1]), w=60)]
         + _flank + _chamfer),
    prof('grip', 'Griffstück', 'Bow grip', 'grip_controls', 'rubber', 'Bogenhand umschließt den Bügel; trägt Socket_Hand',
         'hinten um den Bügel geschraubt',
         [(-24, -56), (4, -56), (11, -42), (12, -18), (8, -2), (12, 18), (10, 34), (-14, 40), (-30, 27), (-38, 2), (-36, -28),
          (-30, -48)], W_RISER + 4, bevel=R_SOFT),
    part('arrow_rest', 'Pfeilauflage', 'Arrow rest', 'riser', 'multi', 'anodized', 'Führt den Pfeil im Sichtfenster',
         'am Fensterbogen verschraubt (quer ins Fenster)', bevel=0.4,
         items=[dict(shape='box', f0=-4, f1=22, u0=ARROW_U - 10, u1=ARROW_U - 5, w=WIN['x_in'] + 3, x=WIN['x_in'] / 2 + 0.5),
                dict(shape='prof', pts=[(0, ARROW_U - 6), (16, ARROW_U - 6), (12, ARROW_U - 3.6), (4, ARROW_U - 3.6)], w=3, x=0)]),
]
# Wurfarmtaschen (eloxiert): schwere Ecken der Klammer, je zwei blanke Schrauben links und rechts
_POCKET = [(34, -2), (70, -4), (94, 0), (106, 10), (109, 22), (104, 36), (90, 45), (60, 48), (30, 46), (16, 38), (20, 20)]   # Runde 2: Keilnase statt Kasten
def pocket_x(f):
    """Linke Fläche der Wurfarmtasche (Draufsicht verjüngt 18,5 → 15 mm halbe Breite von f 120 nach f 10)."""
    return 15.0 + 3.5 * (f - 10) / 110


for s, pid, de, en in ((1, 'pocket_top', 'Wurfarmtasche oben', 'Upper limb pocket'), (-1, 'pocket_bottom', 'Wurfarmtasche unten', 'Lower limb pocket')):
    P.append(prof(pid, de, en, 'limbs', 'anodized', 'Klemmt den Wurfarm; Ecke der Klammer', 'auf das Bügelende geschraubt',
                  [(f, s * (POCKET_U - 4 + u)) for f, u in _POCKET][::s], W_RISER + 6, bevel=R_BODY,
                  cuts=[dict(shape='plan', pts=cw([(120, sx * 18.5), (10, sx * 15.0), (10, sx * 40), (120, sx * 40)]), u0=-500, u1=500)
                        for sx in (1, -1)]))   # Runde 2: verjüngt sich nach hinten in den Wurfarm
P += [part('pocket_screws', 'Taschenschrauben', 'Pocket screws', 'limbs', 'multi', 'trim', 'Spannen die Wurfarme in den Taschen',
           'seitlich in den Taschen', bevel=0.2,
           items=mirror(screws([(f, s * (POCKET_U + 22)) for f in (48, 84) for s in (1, -1)], W_RISER / 2 + 1.6, r=2.2, h=1.0)))]
# Spannlicht (Blickfang): liegender Halbmond links am Fensterbogen, leuchtet bei vollem Auszug
_LU = 138                     # A: Höhe der Mondmitte am Fensterbogen
_lf = (edge_f(FRONT, _LU) + edge_f(BACK, _LU)) / 2
_lx = WIN['x_out'] + 0.25     # linke Fläche des Fensterbogens


def crescent(r, n=16):
    """Halbmond, Spitzen nach hinten: Außenkreis r um die Mitte, Innenkreis 0,85 r um 0,45 r nach hinten versetzt; die Bögen enden
    im Schnittpunkt beider Kreise (außen ±122°, innen ±95,6°)."""
    outer = [(_lf + 4 + r * math.cos(math.radians(a)), _LU + r * math.sin(math.radians(a))) for a in
             [-122 + 244 * i / n for i in range(n + 1)]]
    inner = [(_lf + 4 - 0.45 * r + 0.85 * r * math.cos(math.radians(a)), _LU + 0.85 * r * math.sin(math.radians(a))) for a in
             [95.6 - 191.2 * i / n for i in range(1, n)]]
    return outer + inner


P[0]['cuts'].append(dict(shape='prof', pts=crescent(14.0), w=3.0, x=_lx))   # Mulde 1,5 mm
P += [
    part('draw_light', 'Spannlicht', 'Draw light', 'riser', 'prof', 'draw_light', 'Leuchtet bei vollem Auszug (Bogen bereit); Blickfang links',
         'in der Mulde links am Fensterbogen', bevel=0.2, pts=crescent(13.0), w=1.0, x=_lx - 1.0,
         move=dict(kind='glow', pivot=None, event='full_draw', max=0.7)),
    part('draw_light_rim', 'Mondkante', 'Light rim', 'riser', 'prof', 'trim', 'Blanke Kante um das Spannlicht', 'um die Mulde',
         bevel=0.3, pts=crescent(16.4), w=0.8, x=_lx + 0.1, cuts=[dict(shape='prof', pts=crescent(14.2), w=4, x=_lx)]),
]
# Grafik und Schrift
P += [
    part('band_side', 'Taschenstreifen', 'Pocket stripe', 'limbs', 'plan', 'accent', 'Lackierter Streifen (einziges Grafikelement)',
         'lackiert, links an der oberen Wurfarmtasche (folgt der Verjüngung)', bevel=0, u0=POCKET_U + 28, u1=POCKET_U + 33,
         pts=cw([(40, pocket_x(40) + 0.05), (92, pocket_x(92) + 0.05), (92, pocket_x(92) + 0.35), (40, pocket_x(40) + 0.35)])),
    part('text_l', 'Schriftzug', 'Lettering', 'riser', 'text', 'anodized', 'Kennung „BASIC  EX-07“ (einzige Schrift; dunkel auf Creme)',
         'aufgedruckt', bevel=0, text='BASIC  EX-07', size=4.0, f=edge_f(FRONT, -72) - 9, u=-74, x=W_RISER / 2 + 0.05, side=1, depth=0.12),
]
# ---------------------------------------------------------------- Höhenschlitten: Schelle um den Fensterbogen, Querarm zur Schiene
_cf = edge_f(FRONT, 72)       # Vorderkante des Fensterbogens in Höhe des Schlittens
SLED = (DECK - 26, DECK + 12)  # A: Schelle u0, u1 (Höhenschlitten)
P += [
    part('sight_sled', 'Visierschelle', 'Sight clamp', 'riser', 'plan', 'anodized',
         'Höhenschlitten: umgreift die Vorderkante des Fensterbogens, in der Höhe verstellbar', 'um den Fensterbogen geklemmt',
         bevel=R_SMALL, u0=SLED[0], u1=SLED[1],
         pts=cw([(_cf - 16, WIN['x_in'] - 4), (_cf + 10, WIN['x_in'] - 4), (_cf + 14, WIN['x_in'] + 2), (_cf + 14, WIN['x_out'] + 1),
                 (_cf + 8, WIN['x_out'] + 5), (_cf - 16, WIN['x_out'] + 5)]),
         cuts=[dict(shape='plan', pts=cw([(_cf - 40, WIN['x_in'] - 0.2), (_cf + 0.2, WIN['x_in'] - 0.2), (_cf + 0.2, WIN['x_out'] + 0.4),
                                          (_cf - 40, WIN['x_out'] + 0.4)]), u0=SLED[0] - 2, u1=SLED[1] + 2)]),
    part('sight_arm', 'Querarm', 'Sight cross arm', 'riser', 'prof', 'anodized', 'Trägt die Schiene über dem Pfeil auf ganzer Länge (aus der Schelle)',
         'an die Schelle angeformt', bevel=R_SMALL, pts=[(RAIL[0], DECK - 22), (RAIL[1] - 6, DECK - 22), (RAIL[1], DECK - 16), (RAIL[1], DECK - 7.5),
                                                         (RAIL[0], DECK - 7.5)], w=WIN['x_in'] + 12, x=(WIN['x_in'] - 12) / 2 + 0.0),
    part('clamp_screws', 'Klemmschrauben', 'Clamp screws', 'riser', 'multi', 'trim', 'Spannen die Schelle am Fensterbogen',
         'links in der Schelle', bevel=0.2, items=screws([(_cf - 8, SLED[0] + 9), (_cf - 8, SLED[1] - 9)], WIN['x_out'] + 5, r=2.2, h=1.0)),
    part('sight_scale', 'Höhenskala', 'Elevation scale', 'riser', 'multi', 'trim', 'Teilstriche der Visierhöhe über der Schelle',
         'graviert, blank ausgelegt', bevel=0,
         items=[dict(shape='prof', pts=[(edge_f(FRONT, u) - 9, u), (edge_f(FRONT, u) - 3, u), (edge_f(FRONT, u) - 3, u + 1.2),
                                        (edge_f(FRONT, u) - 9, u + 1.2)], w=0.4, x=WIN['x_out'] + 0.3) for u in range(int(SLED[1]) + 6, 150, 9)]),
]
P += [dict(p, asm='riser', iface='BRI-22', x=SIGHT_X, attach='auf dem Querarm des Höhenschlittens (fest)') for p in rail(RAIL[0], RAIL[1], DECK - 8)]
P[-1]['cuts'] = [cut_box(46 + 12 * i, 51 + 12 * i, DECK - 4, DECK + 1, 30, x=SIGHT_X) for i in range(5)]
_sight, SIGHT_ANCHORS = side_mount(*pins(56, DECK, eye_f=STRING_F - DRAW - EYE_BEHIND), SIGHT_X)
P += _sight
# ---------------------------------------------------------------- Wurfarme (fast parallel nach hinten, gegabelt), Rollen
_c = [(92, POCKET_U + 20), (40, POCKET_U + 28), (-20, POCKET_U + 40), (-76, POCKET_U + 52), (AXLE[0], AXLE[1]), (AXLE[0] - 16, AXLE[1] + 3)]
_th = [34, 32, 29, 25, 22, 22]   # Runde 4: Wurfarme kräftiger (r3 wirkten sie von vorn zart)


def _limb(pid, de, en, sgn):
    c = [(f, sgn * u) for f, u in _c]
    return prof(pid, de, en, 'limbs', 'graphite', 'Speichert die Zugenergie; fast parallel nach hinten, am Ende gegabelt (Rolle dazwischen)',
                'in der Wurfarmtasche geklemmt', band(c, _th), 36, bevel=R_MID,
                cuts=[dict(shape='prof', pts=band(c[3:] + [(AXLE[0] - 40, sgn * (AXLE[1] + 6))], [t + 8 for t in _th[3:]] + [24]), w=14)]
                + [dict(shape='plan', pts=cw([(120, sx * 18.0), (AXLE[0] - 30, sx * 15.0), (AXLE[0] - 30, sx * 40), (120, sx * 40)]),
                        u0=-500, u1=500) for sx in (1, -1)])   # verjüngt sich in der Draufsicht 36 → 30 mm (kein Rechteck von vorn)


def _cam(pid, de, en, sgn):
    a = (AXLE[0], sgn * AXLE[1])
    pts = [(a[0] + (CAM_R + 3 * math.cos(math.radians(d))) * math.cos(math.radians(d)) - 3,
            a[1] + CAM_R * math.sin(math.radians(d))) for d in range(0, 360, 10)]
    holes = [dict(shape='cyl', axis='x', c=(a[0] + 21 * math.cos(math.radians(d)), a[1] + 21 * math.sin(math.radians(d))),
                  a0=-7, a1=7, r=6.0, segs=24) for d in (30, 150, 270)]
    return prof(pid, de, en, 'limbs', 'dark_metal', 'Exzentrische Rolle; wickelt die Sehne ab und dreht beim Auszug',
                'auf der Achse zwischen den Zinken', pts, 12, bevel=R_FINE, cuts=holes,
                move=dict(kind='rotate', pivot=(a[0], a[1], 0), axis='x', range_deg=(0, -CAM_DEG * sgn), event='draw',
                          expect=((a[0] + CAM_R * math.cos(math.radians(45)), a[1] - sgn * CAM_R * math.sin(math.radians(45)), 0),
                                  (-1, 0, 0))))


P += [_limb('limb_top', 'Wurfarm oben', 'Upper limb', 1), _limb('limb_bottom', 'Wurfarm unten', 'Lower limb', -1),
      _cam('cam_top', 'Rolle oben', 'Upper cam', 1), _cam('cam_bottom', 'Rolle unten', 'Lower cam', -1),
      part('cam_hubs', 'Rollennaben', 'Cam hubs', 'limbs', 'multi', 'anodized', 'Naben der Rollen (Lager)', 'auf den Achsen',
           bevel=0.4, smooth=True, items=[dict(shape='cyl', axis='x', c=(AXLE[0], s * AXLE[1]), a0=-6.5, a1=6.5, r=13.0, segs=28)
                                          for s in (1, -1)]),
      part('cam_axles', 'Rollenachsen', 'Cam axles', 'limbs', 'multi', 'trim', 'Lagern die Rollen in den Zinken',
           'quer durch die Wurfarmenden', bevel=0.4, smooth=True,
           items=[dict(shape='cyl', axis='x', c=(AXLE[0], s * AXLE[1]), a0=-20, a1=20, r=5.0, segs=20) for s in (1, -1)])]
# ---------------------------------------------------------------- Sehne (zwei Hälften, folgen dem Nockpunkt), Wicklungen, Pfeil
STRING_R = 2.2                # A: Sehne Ø 4,4 (BASIC-07 Ø 3,2, V): auf Spielabstand lesbar
for s, pid, de, en in ((1, 'string_top', 'Sehne oben', 'Upper string'), (-1, 'string_bottom', 'Sehne unten', 'Lower string')):
    a = (STRING_F, s * AXLE[1])
    P.append(cyl(pid, de, en, 'string', 'string', f'{"Obere" if s > 0 else "Untere"} Sehnenhälfte; läuft hinten tangential von der Rolle, folgt dem Nockpunkt',
                 'zwischen Rolle und Nockpunkt', 'u', (STRING_F, 0), min(ARROW_U, a[1]), max(ARROW_U, a[1]), STRING_R, bevel=0, segs=10,
                 move=dict(kind='segment', pivot=(a[0], a[1], 0), tip=(a[0], a[1], 0), nock=(STRING_F, ARROW_U, 0),
                           vector_mm=(-DRAW, 0, 0), event='draw', expect=((STRING_F, ARROW_U, 0), (-1, 0, 0)))))
    u_mid = ARROW_U + s * 2
    P += [cyl(f'serving_{pid[7:]}', f'Mittelwicklung {"oben" if s > 0 else "unten"}', f'Center serving {"top" if s > 0 else "bottom"}',
              'string', 'anodized', 'Wicklung am Nockpunkt: schützt die Sehne, macht sie lesbar', 'auf die Sehne gewickelt', 'u',
              (STRING_F, 0), min(u_mid, u_mid + s * 34), max(u_mid, u_mid + s * 34), 3.5, bevel=0.3, segs=14, smooth=True, parent_part=pid),
          cyl(f'end_serving_{pid[7:]}', f'Endwicklung {"oben" if s > 0 else "unten"}', f'End serving {"top" if s > 0 else "bottom"}',
              'string', 'anodized', 'Wicklung am Ablauf der Rolle', 'auf die Sehne gewickelt', 'u', (STRING_F, 0),
              min(s * (AXLE[1] - 44), s * (AXLE[1] - 4)), max(s * (AXLE[1] - 44), s * (AXLE[1] - 4)), 3.0, bevel=0.3, segs=14, smooth=True,
              parent_part=pid)]
P += [
    part('nock_loop', 'Nockschlaufe', 'D-loop', 'string', 'multi', 'trim', 'Messingklemmen über und unter dem Nockpunkt (Lage der Nocke)',
         'auf der Mittelwicklung geklemmt', bevel=0.3, smooth=True, parent_part='string_top',
         items=[dict(shape='cyl', axis='u', c=(STRING_F, 0), a0=ARROW_U + 4.5, a1=ARROW_U + 8.5, r=4.2, segs=14)]),
    cyl('arrow_shaft', 'Pfeilschaft', 'Arrow shaft', 'arrow', 'graphite', 'Pfeil; wird mit der Sehne zurückgezogen',
        'auf der Auflage, Nocke an der Sehne', 'f', (ARROW_U, 0), ARROW[0], ARROW[1], 3.2, segs=12, removable=True,
        move=dict(kind='translate', pivot=(ARROW[0], ARROW_U, 0), vector_mm=(-DRAW, 0, 0), event='draw',
                  expect=((TIP, ARROW_U, 0), (-1, 0, 0)))),
    cyl('arrow_ferrule', 'Spitzenhülse', 'Ferrule', 'arrow', 'trim', 'Blanke Hülse; trägt die Spitze', 'vorn auf dem Schaft',
        'f', (ARROW_U, 0), ARROW[1] - 8, ARROW[1] + 4, 4.4, segs=16, bevel=0.4, parent_part='arrow_shaft'),
    cyl('arrow_head', 'Pfeilspitze', 'Arrow head', 'arrow', 'dark_metal', 'Schneide (dreikant)', 'auf der Hülse', 'f', (ARROW_U, 0),
        ARROW[1] + 3, TIP, 7.0, r1=0.6, segs=3, bevel=R_FINE, parent_part='arrow_shaft'),
    cyl('arrow_nock', 'Nocke', 'Nock', 'arrow', 'anodized', 'Rastet an der Sehne ein', 'Schaftende', 'f', (ARROW_U, 0),
        ARROW[0] - 8, ARROW[0] + 6, 3.4, segs=12, parent_part='arrow_shaft',
        cuts=[cut_box(ARROW[0] - 10, ARROW[0] + 1.5, ARROW_U - 1.4, ARROW_U + 1.4, 12)]),
    prof('fletch_top', 'Leitfeder', 'Cock vane', 'arrow', 'accent', 'Stabilisiert den Flug; zeigt die Nockrichtung', 'am Schaft',
         [(ARROW[0] + 16, ARROW_U), (ARROW[0] + 72, ARROW_U), (ARROW[0] + 64, ARROW_U + 11), (ARROW[0] + 30, ARROW_U + 11)], 1.2,
         bevel=0.3, parent_part='arrow_shaft'),
    part('fletch_l', 'Befiederung links', 'Left vane', 'arrow', 'plan', 'graphite', 'Stabilisiert den Flug', 'am Schaft',
         bevel=0.3, parent_part='arrow_shaft', u0=ARROW_U - 0.6, u1=ARROW_U + 0.6,
         pts=cw([(ARROW[0] + 16, 2), (ARROW[0] + 72, 2), (ARROW[0] + 64, 11), (ARROW[0] + 30, 12)])),
    part('fletch_r', 'Befiederung rechts', 'Right vane', 'arrow', 'plan', 'graphite', 'Stabilisiert den Flug', 'am Schaft',
         bevel=0.3, parent_part='arrow_shaft', u0=ARROW_U - 0.6, u1=ARROW_U + 0.6,
         pts=cw([(ARROW[0] + 16, -2), (ARROW[0] + 30, -12), (ARROW[0] + 64, -11), (ARROW[0] + 72, -2)])),
]
PARTS = P

# ---------------------------------------------------------------- Anker, Weltpunkte, Aktionen
ANCHORS = {
    'Socket_Hand': dict(at=(0, 0, 0), part='grip', note='Bogenhand im Griffstück (Griffachse)'),
    'Socket_SupportHand': dict(at=(STRING_F, ARROW_U, 0), part='string_top', note='Zughand am Nockpunkt in Ruhe'),
    'Socket_Nock': dict(at=(STRING_F, ARROW_U, 0), part='string_top', note='Nockpunkt in Ruhe (Toolgen-Name)'),
    'Socket_DrawFull': dict(at=(STRING_F - DRAW, ARROW_U, 0), part='string_top', note=f'Nockpunkt bei vollem Auszug ({DRAW} mm)'),
    'Socket_ArrowTip': dict(at=(TIP, ARROW_U, 0), part='arrow_head', note='Pfeilspitze in Ruhe (Toolgen-Name)'),
    'Socket_Muzzle': dict(at=(12, ARROW_U, 0), part='arrow_rest', note='Abgangspunkt des Pfeils an der Auflage'),
}
ANCHORS.update(SIGHT_ANCHORS)
_d = [(0, 0), (18, 1), (40, 1), (42, 0)]
_light = [(0, 0), (16, 0), (18, 1), (40, 1), (41, 0)]
ACTIONS = {
    'draw_hold_release': dict(de='Ausziehen, halten, lösen', frames=60, step=2, keys={
        'arrow_shaft': [(0, 0), (18, 1), (40, 1), (42, -0.4), (46, -4)], 'string_top': _d, 'string_bottom': _d,
        'cam_top': _d, 'cam_bottom': _d, 'draw_light': _light},
        events=[(0, 'nocked'), (18, 'full_draw'), (40, 'release'), (42, 'shot'), (46, 'arrow_gone')], view=(-0.95, 0.15, 0.3)),
    'let_down': dict(de='Entspannen ohne Schuss', frames=40, keys={
        'arrow_shaft': [(0, 0), (16, 1), (24, 1), (40, 0)], 'string_top': [(0, 0), (16, 1), (24, 1), (40, 0)],
        'string_bottom': [(0, 0), (16, 1), (24, 1), (40, 0)], 'cam_top': [(0, 0), (16, 1), (24, 1), (40, 0)],
        'cam_bottom': [(0, 0), (16, 1), (24, 1), (40, 0)], 'draw_light': [(0, 0), (14, 0), (16, 1), (24, 1), (26, 0)]},
        events=[(16, 'full_draw'), (40, 'relaxed')], view=(-0.95, 0.15, 0.3)),
}
EXPLODE = {'arrow': (0, 0, -90), 'string': (-40, 0, 0), 'limbs': (-30, 0, 0), 'sight': (60, 40, 0), 'grip_controls': (-60, 0, 0),
           'riser': (0, 0, 0)}
HERO = (0.92, -0.30, 0.22)   # A: Kamera wie BASIC-07, aber von links (Runde 3: Halbmond, Schlitten und Schrift zur Kamera)
SIGHT_ID = 'B1'
EGO_GRIPS = {
    'grip':    dict(contact=(-8, -26, 17.5), palm=(0.15, 0.0, -1.0), fingers=(1.0, -0.06, 0.0), fingers_pose='foregrip',
                    src='V: Bogenhand links am Griffstück wie BASIC-07 (Handmitte 26 mm unter der Griffachse)'),
    'support': dict(part='arrow_shaft', contact=(-158, 40, -8), palm=(0.0, 0.0, 1.0), fingers=(0.25, -0.97, 0.0), fingers_pose='pinch',
                    src='V: Zughand rechts am Nockpunkt wie BASIC-07; folgt dem Pfeil beim Auszug'),
    'nock':    dict(contact=(-578, 40, -8), palm=(0.0, 0.0, 1.0), fingers=(0.25, -0.97, 0.0), fingers_pose='pinch',
                    src='V: Nockpunkt bei vollem Auszug (Socket_DrawFull), fest an der Waffe – Ort des Lösens'),
}
EGO_LIVE = dict(trigger='', bolt='', port='')
EJECT = None       # Bogen: kein Magazin, kein Hülsenauswurf
POINTS = collect(EJECT, EGO_GRIPS, dict(grip='grip', nock='string_top'))
