"""EXTENDED-12 „Shuttle“ – eigenständiges Sci-Fi-Spurgewehr der BASIC-Familie (Formgen v2 0.28 „Quiver“).

Eigenes Modell im BALLON-Kit-Vokabular (reines Python, kein bpy). Keine Teile oder Umbauten von BASIC-12: aus `basic.common` kommen nur
genormte Familienschnittstellen (Griffmodul BGM-1, Visier H3 „Zinken“ auf Schiene BRI-22, Schraubenköpfe) und Hilfen (`cut_box`,
`mirror`). Geladen über `formgen.extended`, gerendert mit BALLONs unverändertem `tools/blender_build.main` (`tools/extended_render.py`).

Formsprache (Stilhandbuch BALLON §3; Auswahl und Skizzen: docs/extended.md)
- Leitmerkmal Weberschiffchen: Der Einteilkörper ist eine Spindel – vom Schaftende bis zur Stirn ein Körper, in der Seite und von
  oben spitz zulaufend, unten ein Bauch für die Zelle. Durch seine Mitte geht ein linsenförmiges Auge; darin sitzt auf der Strahlachse
  die Fokusspule wie die Garnspule im Schiffchen (der Strahl ist der Faden, der „Spur“ zieht). Vorn tritt das freie runde Fokusrohr mit
  dem Kegel aus der Spitze (Leitmerkmal BASIC-12: rundes Fokusrohr mit Kegel, Einteilkörper).
- Silhouette: 0,80 m, Linse mit dem höchsten Punkt vor dem Visier, der Bauch hängt vor dem Abzugsbügel; vorn das schlanke Rohr.
- Querschnitt: stehendes Oval (oben schmal für die Schiene, unten zum Bauch eingezogen), Draufsicht ebenfalls spitz zulaufend.
- Negativraum: das Auge quer durch den Körper; darin die Spule mit Luft rundum.
- Blickfang (genau einer): die Wicklung der Fokusspule leuchtet beim Strahl, von links durch das Auge zu sehen.
- Zweiton: Creme-Oberschale über Graphit-Unterschale; die Fuge ist ein Bogen (tief in der Mitte, steigt zu beiden Spitzen), damit die
  Creme-Schale selbst als Schiffchen liest (Runde 4); Fokusrohr Graphit, Kegel `dark_metal`.
- Schichten: Unterschale 1,5 mm unter der Schale, Augenlaibung eloxiert, Spulenflansche blank, Flankenpaneel in einer Mulde.
- Grafik: ein oranger Fadenstreifen auf beiden Flanken entlang der Oberlinie; eine Schrift rechts.
- Front mehrstufig: Fokuslinse → blanke Krone → Kegel mit Stufe → Fokusrohr → eloxierter Stirnring in der Spindelspitze.
- Ergonomie: Griff BGM-1 (Socket_Hand 0/0), Energiezelle vor dem Abzugsbügel im Bauch (unten heraus), Stützhand auf dem Griffband des
  Fokusrohrs, Schaftkappe im Ovalquerschnitt. Akzent-Bedienfunktionen: Zellenhalter (1).

Herkunft der Zahlen: V = Vorgabe (Familie/Schnittstelle, BASIC-12 Pilot v2.1 bzw. `basic.common`), A = Annahme (Entwurf 0.28),
G = gemessen; Zahlen ohne Kennung sind A (Entwurf 0.28, an den Renders gesichtet).
Maße mm; f nach vorn, u nach oben, x nach links; Socket_Hand = (0, 0, 0).
"""
import math

from basic.common import (part, prof, box, cyl, cut_box, screws, mirror, rail, grip_v21, zinken, R_BODY, R_MID, R_SMALL, R_FINE)
from basic.variant import collect

META = dict(id='EXTENDED-12', num='E12', sheet_id='EA12', type='trace_rifle', type_de='Spurgewehr', type_en='Trace Rifle',
            family='BASIC', name='Shuttle', nick='Weberschiffchen', ammo='special', fire='continuous_beam',
            reference_length_m=0.806, reference_length_source='G: Hülle des Datensatzes 0.28 (BASIC-12 v2.1 0,78 m gemessen als Rahmen, V)',
            inspired_by='BASIC-12 Familie; Formgen v1 als Haltung (eine mutige Gesamtarchitektur)',
            summary='Spurgewehr als Weberschiffchen: Spindelkörper mit Auge, darin die Fokusspule auf der Strahlachse, freies Fokusrohr '
                    'mit Kegel vorn, Visier H3 (EXTENDED-Reihe).')
ASSEMBLIES = [
    dict(id='receiver', de='Hauptgehäuse', en='Receiver'),
    dict(id='barrel', de='Lauf', en='Barrel'),
    dict(id='ammo', de='Munitionsversorgung', en='Ammunition feed'),
    dict(id='sight', de='Visier', en='Sight'),
    dict(id='grip_controls', de='Griff und Bedienung', en='Grip and controls'),
    dict(id='support', de='Stützbereich', en='Support'),
    dict(id='stock', de='Schaft', en='Stock'),
]

GRIP_TOP = 40                # V: Griffoberkante BGM-1
BORE = 90                    # A: Strahlachse (BASIC-12 96, V)
RAIL_U = BORE + 32           # V: Schienenunterkante; Schiene bis BORE + 40, Visierlinie (Schiene + 26) 66 über der Achse
HOOD_MAX = BORE + 42         # V: vor dem Visier höchstens 24 mm unter der Visierlinie (wie die Haube BASIC-12)
SEAM = 44.0                  # A: tiefster Punkt der Fuge Oberschale/Unterschale (Runde 4: Fuge folgt als Bogen der Spindel)
OVAL = (30.0, 72.0, 62.0)    # A: stehendes Oval: halbe Breite, halbe Höhe, Mitte u
F0, F1 = -292, 302           # A: Spindel vom Schaftende bis zur Spitze
TUBE_R = 16.0                # V: Fokusrohr Ø 32 wie BASIC-12
TUBE1 = 452                  # A: Rohrende = Kegelansatz
TIP = 500                    # A: Stirn der Fokuslinse (Socket_Muzzle)
CELL = (94, 136)             # A: Energiezelle im Bauch vor dem Abzugsbügel (BASIC-12 86–126, V; Bügel bis f 83)
EYE = (122, 272, 29.0)       # A: Auge: Spitze hinten, Spitze vorn, halbe Höhe in der Mitte; Mitte auf der Strahlachse
SPOOL = (166, 230, 20.0)     # A: Fokusspule: Flansch hinten, Flansch vorn, Flanschradius
SUP = (330, 410)             # A: Griffband der Stützhand auf dem Fokusrohr (BASIC-12 218–300, V)



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


# Oberlinie (Seite): Schaftende → Schienensattel (eben unter der Schiene) → Scheitel über dem Auge → Spitze
TOP_LINE = spline([(F0 - 2, 97), (-226, 108), (-128, RAIL_U - 1), (70, RAIL_U), (150, 128), (205, 130), (262, 122), (F1 + 2, BORE + TUBE_R + 3)])
# Unterlinie: Spitze → Bauch (Zelle) → vor dem Abzugsbügel steil hinauf → Griff → Schaftende
BOTTOM_LINE = spline([(F1 + 2, BORE - TUBE_R - 3), (262, 54), (220, 30), (176, 12), (CELL[1], 3), (CELL[0] + 4, 6), (88, 22), (85, 36),
                      (40, 36.5), (-60, 38), (-170, 45), (F0 - 2, 55)])   # Runde 2/4: Spindel läuft hinten zusammen
# Draufsicht (halbe Breite): spitz zur Stirn, schlanker zum Schaft
PLAN_HW = spline([(F0 - 2, 17), (-222, 24), (-112, 30.5), (60, 31), (200, 31), (258, 25), (F1 + 2, 18)])


def line_u(line, f):
    pts = sorted(line)
    for (f0, u0), (f1, u1) in zip(pts, pts[1:]):
        if f0 <= f <= f1:
            return u0 + (u1 - u0) * (f - f0) / ((f1 - f0) or 1)
    return pts[0][1] if f < pts[0][0] else pts[-1][1]


def oval_x(u, a=OVAL[0], b=OVAL[1], c=OVAL[2]):
    """Halbe Breite des Ovals in Höhe u."""
    return a * math.sqrt(max(0.0, 1 - ((u - c) / b) ** 2))


def oval(a=OVAL[0], b=OVAL[1], c=OVAL[2], n=40):
    return [(a * math.cos(2 * math.pi * i / n), c + b * math.sin(2 * math.pi * i / n)) for i in range(n)]


def split(pts, u_cut, keep='above'):
    """Polygon an der Waagerechten u_cut teilen (Sutherland-Hodgman, eine Kante)."""
    def inside(q):
        return q[1] >= u_cut if keep == 'above' else q[1] <= u_cut
    out = []
    for a, b in zip(pts, pts[1:] + pts[:1]):
        if inside(a):
            out.append(a)
        if inside(a) != inside(b):
            t = (u_cut - a[1]) / (b[1] - a[1])
            out.append((a[0] + (b[0] - a[0]) * t, u_cut))
    return out


def stadium(f0, f1, u0, u1, grow=0.0, n=8):
    """Stadion (Seitenprofil) mit runden Enden: Flankenpaneel und seine Mulde."""
    r = (u1 - u0) / 2 + grow
    c = (u0 + u1) / 2
    a, b = f0 + r - grow, f1 - r + grow
    return ([(b + r * math.cos(math.radians(-90 + 180 * i / n)), c + r * math.sin(math.radians(-90 + 180 * i / n))) for i in range(n + 1)]
            + [(a + r * math.cos(math.radians(90 + 180 * i / n)), c + r * math.sin(math.radians(90 + 180 * i / n))) for i in range(n + 1)])


def conform(u0, u1, d0, d1, sx, n=6):
    """Schicht auf der Ovalflanke zwischen u0 und u1, d0 … d1 mm über der Oberfläche (negativ = darunter); sx Seite."""
    us = [u0 + (u1 - u0) * i / n for i in range(n + 1)]
    pts = [(sx * (oval_x(u) + d0), u) for u in us] + [(sx * (oval_x(u) + d1), u) for u in us[::-1]]
    return pts if sx < 0 else pts[::-1]


def eye_pts(grow=0.0, n=16):
    """Auge: Linse (zwei Kreisbögen) von EYE[0] bis EYE[1], halbe Höhe EYE[2] + grow, Mitte auf der Strahlachse."""
    f0, f1, h = EYE[0] - grow, EYE[1] + grow, EYE[2] + grow
    half = (f1 - f0) / 2
    r = (half ** 2 + h ** 2) / (2 * h)
    a = math.degrees(math.asin(half / r))
    fc = (f0 + f1) / 2
    top = [(fc + r * math.sin(math.radians(t)), BORE - (r - h) + r * math.cos(math.radians(t))) for t in
           [-a + 2 * a * i / n for i in range(n + 1)]]
    bot = [(fc + r * math.sin(math.radians(t)), BORE + (r - h) - r * math.cos(math.radians(t))) for t in
           [a - 2 * a * i / n for i in range(1, n)]]
    return top + bot


def eye_h(f, grow=0.0):
    """Halbe Höhe des Auges an der Stelle f."""
    f0, f1, h = EYE[0] - grow, EYE[1] + grow, EYE[2] + grow
    half = (f1 - f0) / 2
    r = (half ** 2 + h ** 2) / (2 * h)
    d = f - (f0 + f1) / 2
    return max(0.0, math.sqrt(max(0.0, r * r - d * d)) - (r - h))


_top_cut = dict(shape='prof', pts=TOP_LINE + [(F1 + 30, 220), (F0 - 30, 220)], w=120)
_bot_cut = dict(shape='prof', pts=BOTTOM_LINE + [(F0 - 30, -120), (F1 + 30, -120)], w=120)
_plan_cuts = [dict(shape='plan', pts=cw([(f, sx * hw) for f, hw in PLAN_HW] + [(F1 + 30, sx * 90), (F0 - 30, sx * 90)]), u0=-60, u1=220)
              for sx in (1, -1)]
_eye_cut = dict(shape='prof', pts=eye_pts(), w=120)
_SEC = oval()
# Fuge als Bogen (Runde 4): tief in der Mitte, steigt zu beiden Spitzen – die Creme-Schale selbst ist ein Schiffchen, nicht ein Balken
SEAM_LINE = spline([(F0 - 4, 66), (-160, 52), (-20, SEAM), (110, SEAM), (230, 58), (F1 + 4, 82)])
SHELL_X = _SEC
LOWER_X = [(x * (1 - 1.5 / OVAL[0]), u) for x, u in _SEC]    # 1,5 mm unter der Schale (Schichtung)
_seam_below = dict(shape='prof', pts=[(f, u - 0.5) for f, u in SEAM_LINE] + [(F1 + 30, -120), (F0 - 30, -120)], w=120)
_seam_above = dict(shape='prof', pts=[(f, u + 0.5) for f, u in SEAM_LINE] + [(F1 + 30, 220), (F0 - 30, 220)], w=120)
_cell_well = dict(shape='prof', pts=[(CELL[0] - 0.8, SEAM + 4), (CELL[1] + 0.8, SEAM + 4), (CELL[1] + 0.8, -20), (CELL[0] - 0.8, -20)], w=25.6)


def seam_u(f):
    return line_u(SEAM_LINE, f)
PANEL = (-100, -16, 66, 94)  # A: Flankenpaneel links/rechts (f0, f1, u0, u1) unter der Schiene, wo die Flanke ungeschnitten ist
BUTT = (19.0, 30.0, 76.0)    # A: Schaftkappe als Oval (halbe Breite, halbe Höhe, Mitte u)

P = []
# ---------------------------------------------------------------- Spindel: Oberschale (Creme), Unterschale (Graphit), Auge
P += [
    part('shell', 'Oberschale', 'Upper shell', 'receiver', 'xprof', 'shell',
         'Einteilkörper als Spindel: vom Schaftende bis zur Spitze ein Teil; trägt Schiene, Auge und Stirnring',
         'Grundkörper; mit der Unterschale an der Fuge verschraubt', bevel=R_BODY, f0=F0, f1=F1, cu=0, pts=SHELL_X, iface='BST-T',
         cuts=[_top_cut, _bot_cut, _seam_below, _eye_cut, dict(shape='cyl', axis='f', c=(BORE, 0), a0=F1 - 40, a1=F1 + 4, r=TUBE_R + 0.4, segs=40)]
         + _plan_cuts + [dict(shape='xprof', f0=PANEL[0], f1=PANEL[1], cu=0, pts=conform(PANEL[2], PANEL[3], -1.2, 3.0, sx)) for sx in (1, -1)]),
    part('lower', 'Unterschale', 'Lower shell', 'receiver', 'xprof', 'graphite',
         'Bauch und Kiel der Spindel: Griffmodul, Abzugsgruppe, Zellenschacht', 'unter der Oberschale, Fuge 1 mm', bevel=R_BODY,
         f0=F0 + 2, f1=F1 - 6, cu=0, pts=LOWER_X, cuts=[_top_cut, _bot_cut, _seam_above, _cell_well] + _plan_cuts),
    part('eye_liner', 'Augenlaibung', 'Eye liner', 'receiver', 'prof', 'anodized', 'Fasst das Auge innen; Lager der Spulenachse',
         'in das Auge geklebt', bevel=R_SMALL, pts=eye_pts(), w=2 * oval_x(BORE + EYE[2]) - 3.0,
         cuts=[dict(shape='prof', pts=eye_pts(-3.0), w=120)]),
]
# ---------------------------------------------------------------- Fokusspule im Auge (Blickfang), Achse, Flansche
P += [
    cyl('spool_axle', 'Spulenachse', 'Spool axle', 'barrel', 'dark_metal', 'Strahlkanal der Spule; in der Laibung gelagert',
        'vorn und hinten in der Augenlaibung', 'f', (BORE, 0), EYE[0] - 6, EYE[1] + 6, 8.0, segs=32, bevel=R_FINE, smooth=True),
    part('spool_flanges', 'Spulenflansche', 'Spool flanges', 'barrel', 'multi', 'trim', 'Blanke Flansche der Fokusspule',
         'auf der Spulenachse', bevel=0.6, smooth=True,
         items=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=f, a1=f + 5, r=SPOOL[2], r_in=7.6, segs=48) for f in (SPOOL[0], SPOOL[1] - 5)]),
    cyl('spool_core', 'Spulenkern', 'Spool core', 'barrel', 'anodized', 'Dunkler Kern unter der Wicklung', 'zwischen den Flanschen',
        'f', (BORE, 0), SPOOL[0] + 4, SPOOL[1] - 4, 11.5, segs=40, bevel=R_FINE, smooth=True),
    cyl('spool_glow', 'Fokuswicklung', 'Focus winding', 'barrel', 'energy',
        'Wicklung der Fokusspule; leuchtet beim Strahl – Blickfang im Auge', 'auf den Spulenkern gewickelt', 'f', (BORE, 0),
        SPOOL[0] + 8, SPOOL[1] - 8, 14.0, segs=48, bevel=0.4, smooth=True, move=dict(kind='glow', pivot=None, event='beam', max=3.0)),
    part('spool_bands', 'Wicklungsbänder', 'Winding bands', 'barrel', 'multi', 'dark_metal', 'Halten die Wicklung in vier Lagen',
         'um die Wicklung', bevel=0.3, smooth=True,
         items=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=f, a1=f + 3.0, r=14.8, r_in=13.6, segs=48)
                for f in [SPOOL[0] + 8 + (SPOOL[1] - SPOOL[0] - 19) * i / 3 for i in range(4)]]),
]
# ---------------------------------------------------------------- Stirn: Stirnring, Fokusrohr, Griffband, Kegel
P += [
    cyl('nose_ring', 'Stirnring', 'Nose ring', 'receiver', 'anodized', 'Fasst das Fokusrohr in der Spindelspitze',
        'in die Spitze geschraubt', 'f', (BORE, 0), F1 - 14, F1 + 8, TUBE_R + 6.5, r1=TUBE_R + 4.0, r_in=TUBE_R + 0.2, segs=48,
        bevel=R_SMALL, smooth=True),
    cyl('focus_tube', 'Fokusrohr', 'Focus tube', 'support', 'graphite', 'Umschließt den Strahlkanal; frei vor der Spindel',
        'im Stirnring verschraubt', 'f', (BORE, 0), F1 - 40, TUBE1, TUBE_R, segs=40, bevel=R_SMALL, smooth=True),
    cyl('tube_grip', 'Griffband', 'Grip band', 'support', 'rubber', 'Rutschfeste Zone für die Stützhand', 'auf das Fokusrohr gezogen',
        'f', (BORE, 0), SUP[0], SUP[1], TUBE_R + 1.5, segs=40, bevel=R_SMALL, smooth=True),
    part('grip_rims', 'Griffbandkanten', 'Grip band rims', 'support', 'multi', 'trim', 'Blanke Klemmringe an den Enden des Griffbands',
         'auf das Fokusrohr gepresst', bevel=0.3, smooth=True,
         items=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=f, a1=f + 3, r=TUBE_R + 2.6, r_in=TUBE_R - 0.2, segs=40) for f in (SUP[0] - 3, SUP[1])]),
    cyl('focus_cone', 'Fokuskegel', 'Focus cone', 'barrel', 'dark_metal', 'Bündelt den Strahl', 'auf das Fokusrohr gesteckt',
        'f', (BORE, 0), TUBE1 - 2, TIP - 12, TUBE_R + 4.5, r1=11, segs=40, bevel=R_SMALL, smooth=True),
    cyl('focus_tip', 'Fokusspitze', 'Focus tip', 'barrel', 'dark_metal', 'Schmale Stufe vor der Linse', 'vorn im Kegel',
        'f', (BORE, 0), TIP - 13, TIP - 1, 9, segs=40, bevel=R_FINE, smooth=True),
    cyl('focus_crown', 'Fokuskrone', 'Focus crown', 'barrel', 'trim', 'Blanke Stirnkante um die Linse', 'vorn an der Spitze',
        'f', (BORE, 0), TIP - 2, TIP + 0.5, 9.4, r_in=6.2, segs=40, bevel=0.4, smooth=True),
    cyl('focus_lens', 'Fokuslinse', 'Focus lens', 'barrel', 'glass_scope', 'Austrittsfenster des Strahls', 'in der Kegelspitze',
        'f', (BORE, 0), TIP - 2.5, TIP, 6.2, bevel=0, segs=32),
]
# ---------------------------------------------------------------- Flankenpaneele, Schrauben, Bolzen, Fadenstreifen, Schrift
_pu = (PANEL[2] + 1, PANEL[3] - 1)
P += [
    part('side_panels', 'Flankenpaneele', 'Flank panels', 'receiver', 'multi', 'anodized', 'Wartungsdeckel über der Steuerung',
         'in die Mulden geschraubt', bevel=R_FINE,
         items=[dict(shape='xprof', f0=PANEL[0] + 1, f1=PANEL[1] - 1, cu=0, pts=conform(PANEL[2] + 1, PANEL[3] - 1, -1.0, 0.5, sx))
                for sx in (1, -1)]),
    part('panel_screws', 'Paneelschrauben', 'Panel screws', 'receiver', 'multi', 'trim', 'Halten die Flankenpaneele', 'in den Paneelen',
         bevel=0.2, items=[dict(shape='cyl', axis='x', c=(f, u), a0=sx * (oval_x(u) - 1.6), a1=sx * (oval_x(u) - 0.1), r=1.6, segs=12)
                           for f in (PANEL[0] + 8, PANEL[1] - 8) for u in (_pu[0] + 4, _pu[1] - 4) for sx in (1, -1)]),
    part('seam_pins', 'Fugenbolzen', 'Seam pins', 'receiver', 'multi', 'metal', 'Verbinden Oberschale und Unterschale', 'quer durch die Fuge',
         bevel=0.4, items=[dict(shape='cyl', axis='x', c=(f, seam_u(f)), a0=sx * (oval_x(seam_u(f)) - 2.0), a1=sx * (oval_x(seam_u(f)) + 0.8), r=3.0, segs=16)
                           for f in (-150, 20, 200) for sx in (1, -1)]),
    part('thread_stripe', 'Fadenstreifen', 'Thread stripe', 'receiver', 'multi', 'accent', 'Lackierter Streifen entlang der Oberlinie '
         '(einziges Grafikelement)', 'lackiert', bevel=0,
         items=[dict(shape='xprof', f0=-196, f1=-112, cu=0, pts=conform(99, 102, 0.05, 0.35, sx))
                for sx in (1, -1)]),
    part('text_r', 'Schriftzug', 'Lettering', 'receiver', 'text', 'anodized', 'Kennung „BASIC  EX-12“ (einzige Schrift)',
         'aufgedruckt (dunkel auf Creme, rechts hinter dem Auge)', bevel=0, text='BASIC  EX-12', size=4.6, f=8, u=BORE - 2,
         x=-(oval_x(BORE - 2) + 0.05), side=-1, depth=0.12),
]
P += [
    part('nose_screws', 'Stirnringschrauben', 'Nose ring screws', 'receiver', 'multi', 'trim', 'Halten den Stirnring in der Spitze',
         'radial im Stirnring', bevel=0.2,
         items=[dict(shape='cyl', axis='x', c=(F1 - 4, BORE + dy), a0=sx * (TUBE_R + 4.6), a1=sx * (TUBE_R + 6.4), r=1.6, segs=12)
                for dy in (-8, 8) for sx in (1, -1)]),
    part('liner_screws', 'Laibungsschrauben', 'Liner screws', 'receiver', 'multi', 'trim', 'Halten die Augenlaibung und lagern die Spulenachse',
         'vorn und hinten am Auge, beidseitig', bevel=0.2,
         items=[dict(shape='cyl', axis='x', c=(f, BORE), a0=sx * (oval_x(BORE) - 1.4), a1=sx * (oval_x(BORE) + 0.2), r=2.0, segs=12)
                for f in (EYE[0] - 12, EYE[1] + 10) for sx in (1, -1)]),
    part('spool_nuts', 'Achsmuttern', 'Axle nuts', 'barrel', 'multi', 'trim', 'Sichern die Spule auf der Achse', 'an den Flanschen',
         bevel=0.3, smooth=True, items=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=f, a1=f + 3, r=10.5, r_in=7.9, segs=6)
                                        for f in (SPOOL[0] - 3, SPOOL[1])]),
]
# ---------------------------------------------------------------- Schiene, Visier H3
P += [dict(p, mat='anodized', attach='auf dem Schienensattel der Oberschale (fest)') for p in rail(-66, 66, RAIL_U)]
P[-1]['cuts'] = [cut_box(-58 + 14 * i, -51 + 14 * i, RAIL_U + 4, RAIL_U + 9, 30) for i in range(9)]
_sight, SIGHT_ANCHORS = zinken(-12, RAIL_U + 8, weapon_type=META['type'])
P += _sight
# ---------------------------------------------------------------- Griff, Zelle im Bauch, Zellenhalter, Schaftkappe
P += grip_v21(top=GRIP_TOP)
_cc = ((CELL[0] + CELL[1]) / 2, 20)
_cell_bot = [(f, line_u(BOTTOM_LINE, f) - 0.8) for f in (CELL[1], (CELL[0] + CELL[1]) / 2, CELL[0])]
P += [
    part('energy_cell', 'Energiezelle', 'Energy cell', 'ammo', 'prof', 'dark_metal', 'Speichert die Ladung; ihr Boden ist der Bauch der Spindel',
         'rastet im Zellenschacht ein (lösbar)', bevel=R_MID, iface='BEC-1', w=24,
         pts=[(CELL[0], SEAM + 4), (CELL[1], SEAM + 4)] + _cell_bot,
         move=dict(kind='translate', pivot=(_cc[0], _cc[1], 0), vector_mm=(0, -110, 0), event='reload', removable=True,
                   expect=((_cc[0], _cell_bot[1][1], 0), (0, -1, 0)))),
    part('cell_band', 'Zellenband', 'Cell band', 'ammo', 'prof', 'trim', 'Blankes Band über dem Zellenboden; Greifkante', 'um die Zelle',
         bevel=0.4, parent_part='energy_cell', w=25.2,
         pts=[(CELL[0] - 0.6, line_u(BOTTOM_LINE, CELL[0]) + 6), (CELL[1] + 0.6, line_u(BOTTOM_LINE, CELL[1]) + 6),
              (CELL[1] + 0.6, line_u(BOTTOM_LINE, CELL[1]) + 10), (CELL[0] - 0.6, line_u(BOTTOM_LINE, CELL[0]) + 10)]),
    part('cell_release', 'Zellenhalter', 'Cell release', 'grip_controls', 'cyl', 'accent', 'Löst die Energiezelle',
         'Druckknopf links über dem Abzugsbügel', bevel=R_FINE, axis='x', c=(CELL[0] - 14, 46), a0=oval_x(46) - 2.5,
         a1=oval_x(46) + 2.0, r=4.5, segs=20,
         move=dict(kind='translate', pivot=(CELL[0] - 14, 46, oval_x(46)), vector_mm=(0, 0, -2.5), event='reload',
                   expect=((CELL[0] - 14, 46, oval_x(46) + 2.0), (0, 0, -1)))),
    part('butt_pad', 'Schaftkappe', 'Butt pad', 'stock', 'xprof', 'rubber', 'Rutschfeste Anlage an der Schulter im Ovalquerschnitt',
         'auf das Spindelende gesteckt (überdeckt es ringsum 2–4 mm, Spitze des Schiffchens)', bevel=R_MID, f0=F0 - 14, f1=F0 + 2, cu=0,
         pts=oval(*BUTT, n=32)),
    part('stock_bolts', 'Schaftbolzen', 'Stock bolts', 'stock', 'multi', 'trim', 'Halten die Schaftkappe', 'quer durch das Spindelende',
         bevel=0.3, items=[dict(shape='cyl', axis='x', c=(F0 + 16, u), a0=sx * (min(oval_x(u), 19.5) - 1.6), a1=sx * (min(oval_x(u), 19.5) - 0.2),
                                r=2.6, segs=14) for u in (60, 92) for sx in (1, -1)]),
]
PARTS = P

# ---------------------------------------------------------------- Anker, Weltpunkte, Aktionen
ANCHORS = {
    'Socket_Hand': dict(at=(0, 0, 0), part='grip', note='Haupthand, auf der Griffachse'),
    'Socket_SupportHand': dict(at=((SUP[0] + SUP[1]) / 2, BORE - TUBE_R - 1.5, 0), part='tube_grip',
                               note='Stützhand umgreift das Fokusrohr (Griffband)'),
    'Socket_Muzzle': dict(at=(TIP, BORE, 0), part='focus_lens', note='Stirn der Fokuslinse auf der Strahlachse'),
    'Socket_Cell': dict(at=(_cc[0], 20, 0), part='energy_cell', note='Einrastpunkt der Energiezelle (Schnittstelle BEC-1)'),
}
ANCHORS.update(SIGHT_ANCHORS)
_beam = [(0, 0), (4, 1), (28, 1), (32, 0)]
ACTIONS = {
    'beam': dict(de='Strahl halten und loslassen', frames=36, step=1, keys={
        'trigger': [(0, 0), (2, 1), (28, 1), (31, 0)], 'spool_glow': _beam},
        events=[(4, 'beam_start'), (28, 'beam_end')], view=(0.8, -0.3, 0.45)),
    'reload': dict(de='Energiezelle wechseln', frames=70, keys={'cell_release': [(0, 0), (6, 1), (14, 1), (18, 0)],
                                                                'energy_cell': [(0, 0), (16, 1), (34, 1), (50, 0)]},
                   events=[(16, 'cell_out'), (50, 'cell_in'), (58, 'ready')], view=(0.8, -0.3, 0.45)),
}
EXPLODE = {'sight': (0, 110, 0), 'ammo': (0, -140, 0), 'stock': (-110, 0, 0), 'barrel': (0, 0, 120), 'support': (90, -40, 0),
           'grip_controls': (-10, -80, 0), 'receiver': (0, 0, 0)}
HERO = (0.55, -0.75, 0.30)   # A: Produktbild von links vorn – Auge mit Spule, Spindel und Fokusrohr zur Kamera
SIGHT_ID = 'H3'
EGO_GRIPS = {
    'grip':    dict(contact=(-3, -6, -16.5), palm=(0.15, 0.0, 1.0), fingers=(1.0, -0.06, 0.0), fingers_pose='trigger',
                    src='V: Griff BGM-1 wie die Familie'),
    'support': dict(contact=((SUP[0] + SUP[1]) / 2, BORE - TUBE_R - 2, -2), palm=(0.0, 1.0, -0.25), fingers=(0.08, 0.15, -1.0),
                    fingers_pose='underhand', src='A: unter dem Fokusrohr auf dem Griffband (wie BASIC-12)'),
    'mag':     dict(part='energy_cell', contact=(115, 10, 12.5), palm=(0.0, 0.0, -1.0), fingers=(1.0, 0.2, 0.0), fingers_pose='mag_hold',
                    src='A: links an der Zelle im Bauch, Hand greift von unten (wie BASIC-12)'),
    'charge':  dict(part='cell_release', contact=(CELL[0] - 14, 46, oval_x(46) + 3), palm=(0.0, 0.0, -1.0), fingers=(0.45, 0.9, 0.0),
                    fingers_pose='pinch', src='A: am Zellenhalter links (kein Ladehebel; wie BASIC-12)'),
}
EGO_LIVE = dict(trigger='trigger', bolt='', port='', glow=('spool_glow',))
EJECT = None    # Energiewaffe: keine Hülse
POINTS = collect(EJECT, EGO_GRIPS, dict(grip='grip', support='tube_grip'))
