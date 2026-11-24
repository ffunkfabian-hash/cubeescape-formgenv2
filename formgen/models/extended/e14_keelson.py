"""EXTENDED-14 „Keelson“ – eigenständiger Sci-Fi-Raketenwerfer der BASIC-Familie (Formgen v2 0.25 „Pauldron“).

Eigenes Modell im BALLON-Kit-Vokabular (reines Python, kein bpy). Keine Teile oder Umbauten von BASIC-14: aus `basic.common` kommen nur
genormte Familienschnittstellen (Griffmodul BGM-1, Visier W2 „Entfernung“ mit `side_mount` auf Schiene BRI-22, Schraubenköpfe) und Hilfen
(`cut_box`, `mirror`). Geladen über `formgen.extended`, gerendert mit BALLONs unverändertem `tools/blender_build.main`
(`tools/extended_render.py`).

Formsprache (Stilhandbuch BALLON §3; Auswahl und Skizzen: docs/extended.md)
- Leitmerkmal Rumpf: Das Startrohr liegt als Deck auf einem tiefen Kiel – ein Körper mit Tropfenquerschnitt (oben rund um die
  Bohrung, die Flanken laufen 18° zum Kiel zusammen). Die Kiellinie ist ein flacher Bauch: tief unter der Stützhand, steigt nach vorn
  zur Tropfenstirn und nach hinten zum Griff. Das Volumen sitzt unter der Achse, damit die Sicht am Seitenvisier frei bleibt wie bei
  BASIC-14 (Stilhandbuch: Rohrwand ≥ 20 mm neben der Visierlinie).
- Silhouette: gerade Decklinie vom Kegel bis zur Stirn, darunter der Bauch; dahinter das schlanke Abgasrohr über der Schulter mit dem
  Schultersattel – ein zweiter, kleiner Kiel im selben Querschnitt, unten hohl für die Schulter.
- Querschnitt: Tropfen – Kreis r 46 um die Bohrung, Flanken tangential zum Kiel; Kielschale 1,5 mm unter der Rumpfschale abgesetzt.
- Negativraum: die Schulterbucht unter dem Abgasrohr zwischen Rumpf und Sattel und der Sattelbogen über der Schulter; dazu der
  Ladeschacht oben unter der Klappe.
- Blickfang (genau einer): die Zielerfassungsraute links neben dem Visierausleger, leuchtet bei Bereitschaft.
- Zweiton: Creme-Rumpfschale über Graphit-Kiel; Abgasrohr, Sattel und Griff Graphit.
- Schichten: Kielschale 1,5 mm unter der Schale, Kielpaneele in Mulden, Stirnplatte 3 mm vor der Stirn, Ladeklappe 2,6 mm über der Schale.
- Grafik: eine orange Wasserlinie auf beiden Kielflanken (einziges Grafikelement); eine Schrift rechts auf der Schale.
- Front mehrstufig: Tropfenstirn mit Fase → eloxierte Stirnplatte → blanker Bohrungsring → dunkles Futterrohr; unter der Bohrung das
  Fenster des Entfernungsmessers.
- Ergonomie: Griff BGM-1 (Socket_Hand 0/0) unter dem Rumpfheck, Stützhand unter dem Bauch (Griffkiel), Schultersattel auf der Schulter,
  Ladeklappe oben schwenkt nach rechts, Klappenknopf links (wie BASIC-14). Akzent-Bedienfunktionen: Klappenknopf, Sicherung (2).

Herkunft der Zahlen: V = Vorgabe (Familie/Schnittstelle, BASIC-14 Pilot v2.1 bzw. `basic.common`), A = Annahme (Entwurf 0.25),
G = gemessen; Zahlen ohne Kennung sind A (Entwurf 0.25, an den Renders gesichtet).
Maße mm; f nach vorn, u nach oben, x nach links; Socket_Hand = (0, 0, 0).
"""
import math

from basic.common import (part, prof, box, cyl, cut_box, screws, mirror, rail, grip_v21, sight_line, entfernung, side_mount,
                          R_BODY, R_MID, R_SMALL, R_FINE)
from basic.variant import collect

META = dict(id='EXTENDED-14', num='E14', sheet_id='EA14', type='rocket_launcher', type_de='Raketenwerfer', type_en='Rocket Launcher',
            family='BASIC', name='Keelson', nick='Rumpf', ammo='heavy', fire='single_shot',
            reference_length_m=0.919, reference_length_source='G: Hülle des Datensatzes 0.25 (BASIC-14 0,91 m gemessen als Rahmen, V)',
            inspired_by='BASIC-14 Familie; Formgen v1 als Haltung (eine mutige Gesamtarchitektur)',
            summary='Raketenwerfer mit Rumpf: Startrohr als Deck auf einem tiefen Kiel im Tropfenquerschnitt, Abgasrohr über der Schulter '
                    'mit Schultersattel, Visier W2 seitlich (EXTENDED-Reihe).')
ASSEMBLIES = [
    dict(id='receiver', de='Hauptgehäuse', en='Receiver'),
    dict(id='barrel', de='Startrohr', en='Launch tube'),
    dict(id='ammo', de='Munitionsversorgung', en='Ammunition feed'),
    dict(id='sight', de='Visier', en='Sight'),
    dict(id='grip_controls', de='Griff und Bedienung', en='Grip and controls'),
    dict(id='support', de='Stützbereich', en='Support'),
    dict(id='stock', de='Schaft', en='Stock'),
    dict(id='mechanism', de='Bewegliche Mechanik', en='Moving mechanism'),
]

GRIP_TOP = 40            # V: Griffoberkante wie BASIC-14
BORE = 140               # A: Rohrachse (BASIC-14 112, V); der Kiel füllt den Raum bis zum Griff
R_HULL = 46.0            # A: Rumpfschale um die Bohrung (Ø 92 wie das BASIC-Startrohr, V: Wand ≥ 20 mm neben der Visierlinie)
R_IN = 28.0              # V: Bohrung Ø 56 wie BASIC-14
R_REAR = 31.0            # A: Abgasrohr Ø 62 (BASIC-14 Heckrohr Ø 66, V)
FLANK = 18.0             # A: Flankenwinkel des Tropfens gegen die Senkrechte
SEAM = 100.5             # A: Fuge Rumpfschale/Kiel
SIDE = 66.0              # V: Visier seitlich links, Visierlinie auf Achshöhe 66 mm neben der Achse (66 ± 4)
DECK = BORE - sight_line(0)   # V: Schienenoberkante am Visierausleger (Holo: Schiene + 26)
ARM = (2, 40)            # A: Visierausleger f0, f1
F0, F1 = -12, 540        # A: Rumpfschale von der Kegelfuge bis zur Stirn
CONE = (-96, F0)         # A: Kegel Abgasrohr → Rumpf (Runde 2: länger, läuft in die Schale)
REAR0 = -350             # A: Ende des Abgasrohrs; Heckring dahinter
SLOT = (80, 236, 27)     # V: Ladeschacht oben wie BASIC-14 (f0, f1, halbe Breite)
HATCH = (SLOT[0] - 2, SLOT[1] + 2, 30, R_HULL + 2.6)
HATCH_HINGE = (sum(SLOT[:2]) / 2, BORE + 38, -33)
R0, R1, R2 = 84, 172, 232     # A: Rakete im Schacht: Heck, Beginn Gefechtskopf, Spitze (148 mm; BASIC-14 156 mm, V); passt in den Schacht
LOWER = 240              # V: Hub der Rakete beim Einsetzen von oben (wie BASIC-14)
SADDLE = (-336, -150)    # A: Schultersattel f0, f1
LOCK = (66, 106, float(BORE))   # A: Zielerfassungsraute f0, f1, Mitte u (links vor dem Visier; Richter R1: auf Achshöhe, wo die Schale am steilsten ist)
RANGE_WIN = (90, 101)    # A: Fenster des Entfernungsmessers in der Stirn unter der Bohrung (u0, u1; Runde 3: lag in der Bohrung)

_t = math.tan(math.radians(FLANK))
_tp = (R_HULL * math.cos(math.radians(FLANK)), BORE - R_HULL * math.sin(math.radians(FLANK)))   # Tangentenpunkt der Flanke


def hull_x(u, r=R_HULL, c=BORE):
    """Halbe Breite des Tropfens bei u (unter dem Tangentenpunkt: Flanke, darüber Kreis)."""
    tp = (r * math.cos(math.radians(FLANK)), c - r * math.sin(math.radians(FLANK)))
    if u <= tp[1]:
        return tp[0] - (tp[1] - u) * _t
    return math.sqrt(max(0.0, r * r - (u - c) ** 2))


def drop(r, c, bottom, top=None, inset=0.0, n=24):
    """Tropfenquerschnitt (x, u): Kreisbogen r um c über dem Tangentenpunkt, Flanken bis bottom (runder Kiel); top schneidet oben ab."""
    a0 = -FLANK
    arc = [(r * math.cos(math.radians(a0 + (180 + 2 * FLANK) * i / n)), c + r * math.sin(math.radians(a0 + (180 + 2 * FLANK) * i / n)))
           for i in range(n + 1)]
    xb = hull_x(bottom + 4, r, c)
    pts = [(xb, bottom + 4)] + arc + [(-xb, bottom + 4), (-xb + 2.5, bottom), (xb - 2.5, bottom)]
    if top is not None:
        pts = [(x, min(u, top)) for x, u in pts]
        out = []
        for q in pts:
            if not out or abs(q[0] - out[-1][0]) > 1e-6 or abs(q[1] - out[-1][1]) > 1e-6:
                out.append(q)
        pts = out
    if inset:
        pts = [(x - math.copysign(inset, x) if abs(x) > inset else x, u) for x, u in pts]
    return pts


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


def s_curve(a, b, n=8):
    return [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * (1 - math.cos(math.pi * i / n)) / 2) for i in range(n + 1)]


_SEC = drop(R_HULL, BORE, 8)        # Kielspitze u 8 (Flanken treffen sich erst bei u −9; Test: Profil ohne Kreuzung)
SHELL_X = split(_SEC, SEAM + 0.5, 'above')
KEEL_X = [(x - math.copysign(1.5, x), u) for x, u in split(_SEC, SEAM - 0.5, 'below')]   # 1,5 mm unter der Schale (Schichtung)
# Kiellinie (Seitenprofil, Unterkante): Heck über dem Griff, Bauch unter der Stützhand, steigt zur Tropfenstirn
KEEL_LINE = ([(-112, 109)] + s_curve((-112, 109), (-44, GRIP_TOP + 0.5), n=10)[1:] + [(60, GRIP_TOP + 0.5)]   # Runde 2: Kielhacke statt Stufe
             + s_curve((60, GRIP_TOP + 0.5), (230, 16))[1:] + s_curve((290, 16), (F1, 78), n=12)[0:] + [(F1 + 1, SEAM)])
_keel_cut = dict(shape='prof', pts=KEEL_LINE + [(F1 + 14, SEAM), (F1 + 14, -80), (-130, -80), (-130, 109)], w=120)
SUP = (258, 16)          # A: Stützhand unter dem Bauch (tiefster Punkt)

_lx = hull_x(LOCK[2] + 15.5)   # A: engste Stelle der gewölbten Schale über die Rautenhöhe (Richter R1: flache Mulde lag sonst über der Leuchte)
LOCK_FLOOR = _lx - 3.2         # A: Muldenboden; Leuchte, Glas und Rahmen liegen davor und unter der Schale

P = []
# ---------------------------------------------------------------- Rumpf: Schale (Creme), Kiel (Graphit), Kegel, Abgasrohr
_bore_cut = dict(shape='cyl', axis='f', c=(BORE, 0), a0=F0 - 2, a1=F1 + 8, r=R_IN, segs=48)
P += [
    part('hull', 'Rumpfschale', 'Hull shell', 'barrel', 'xprof', 'shell',
         'Startrohr als Deck: Tropfen oben um die Bohrung, trägt Visierausleger, Ladeschacht und Stirn',
         'Grundkörper; mit dem Kiel an der Fuge verschraubt', bevel=R_MID, f0=F0, f1=F1, cu=0, pts=SHELL_X,
         cuts=[_bore_cut, cut_box(SLOT[0], SLOT[1], BORE + 6, BORE + R_HULL + 4, 2 * SLOT[2]),
               dict(shape='prof', pts=[(LOCK[0] - 5, LOCK[2]), ((LOCK[0] + LOCK[1]) / 2, LOCK[2] + 15), (LOCK[1] + 5, LOCK[2]),
                                       ((LOCK[0] + LOCK[1]) / 2, LOCK[2] - 15)], w=12.0, x=LOCK_FLOOR + 6.0)]   # Mulde der Raute
         + [dict(shape='prof', pts=[(F1 - 14, BORE + R_HULL + 2), (F1 + 2, BORE + R_HULL + 2), (F1 + 2, BORE + R_HULL - 8)], w=120)]),   # Stirnfase oben
    part('keel', 'Kiel', 'Keel', 'receiver', 'xprof', 'graphite',
         'Tiefer Kiel unter dem Startrohr: Elektronik, Batterie, Gegenmasse; trägt Griffmodul und Stützhand',
         'unter der Rumpfschale, Fuge 1 mm', bevel=R_BODY, f0=-112, f1=F1, cu=0, pts=KEEL_X,
         cuts=[_keel_cut, dict(shape='cyl', axis='f', c=(BORE, 0), a0=-120, a1=F0 + 1, r=R_REAR + 1.0, segs=48)]
         + [cut_box(f0, f0 + 64, 56, 84, 4.0, x=sx * (hull_x(70) - 1.5)) for f0 in (110, 330) for sx in (1, -1)]),   # Paneelmulden
    cyl('tube_cone', 'Rumpfkegel', 'Hull cone', 'barrel', 'shell', 'Übergang Abgasrohr → Rumpf', 'hinten an der Rumpfschale angeformt',
        'f', (BORE, 0), CONE[0], CONE[1] + 0.5, R_REAR + 0.6, r1=R_HULL, r_in=R_IN, segs=48, bevel=R_SMALL, smooth=True),
    cyl('rear_tube', 'Abgasrohr', 'Exhaust tube', 'stock', 'graphite', 'Schlankes Rohr über der Schulter; leitet den Rückstrahl nach hinten',
        'im Rumpfkegel verschraubt', 'f', (BORE, 0), REAR0, CONE[0] + 2, R_REAR, r_in=R_IN - 2, segs=48, bevel=R_SMALL, smooth=True),
    cyl('bore_plug', 'Rohrboden', 'Bore plug', 'barrel', 'graphite', 'Schließt die Bohrung hinter dem Schacht (Trennscheibe zum Abgasrohr)',
        'in den Kegel eingepresst', 'f', (BORE, 0), CONE[1] - 6, CONE[1] - 2, R_IN, segs=48, bevel=R_FINE, smooth=True),
    cyl('liner', 'Futterrohr', 'Bore liner', 'barrel', 'dark_metal', 'Dunkles Futter der Bohrung', 'in die Rumpfschale gepresst',
        'f', (BORE, 0), F1 - 30, F1 + 1.5, R_IN + 0.4, r_in=R_IN - 1.5, segs=48, bevel=R_FINE, smooth=True),
    part('nose_plate', 'Stirnplatte', 'Nose plate', 'barrel', 'xprof', 'anodized', 'Tropfenförmige Stirnplatte um Bohrung und Entfernungsmesser',
         'vorn auf Schale und Kiel geschraubt', bevel=R_SMALL, f0=F1 - 1, f1=F1 + 3, cu=0,
         pts=drop(R_HULL - 6, BORE, 82, top=BORE + R_HULL - 12),
         cuts=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=F1 - 3, a1=F1 + 5, r=R_IN + 4, segs=48)]),
    cyl('bore_ring', 'Bohrungsring', 'Bore ring', 'barrel', 'trim', 'Blanke Kante um die Bohrung', 'in die Stirnplatte gepresst',
        'f', (BORE, 0), F1 + 2, F1 + 5, R_IN + 4.5, r_in=R_IN + 0.5, segs=48, bevel=0.4, smooth=True),
    part('range_window', 'Entfernungsmesser', 'Rangefinder window', 'barrel', 'xprof', 'glass_scope', 'Fenster des Entfernungsmessers unter der Bohrung',
         'in die Stirnplatte eingelassen', bevel=0.4, f0=F1 + 2, f1=F1 + 3.6, cu=0,
         pts=[(10, RANGE_WIN[0]), (10, RANGE_WIN[1]), (-10, RANGE_WIN[1]), (-10, RANGE_WIN[0])]),
    part('range_frame', 'Messfensterrahmen', 'Rangefinder frame', 'barrel', 'xprof', 'trim', 'Blanker Rahmen des Messfensters', 'um das Fenster',
         bevel=0.3, f0=F1 + 2.5, f1=F1 + 4.4, cu=0,
         pts=[(12.5, RANGE_WIN[0] - 2.5), (12.5, RANGE_WIN[1] + 2.5), (-12.5, RANGE_WIN[1] + 2.5), (-12.5, RANGE_WIN[0] - 2.5)],
         cuts=[dict(shape='box', f0=F1, f1=F1 + 8, u0=RANGE_WIN[0], u1=RANGE_WIN[1], w=20)]),
]
# ---------------------------------------------------------------- Kielpaneele, Schrauben, Wasserlinie, Schrift
P += [
    part('keel_panels', 'Kielpaneele', 'Keel panels', 'receiver', 'multi', 'anodized', 'Wartungsdeckel über Batterie und Elektronik',
         'in die Mulden geschraubt', bevel=R_FINE,
         items=[dict(shape='xprof', f0=f0 + 1, f1=f0 + 63, cu=0,
                     pts=[(sx * (hull_x(57) - 1.5 - 2.2), 57), (sx * (hull_x(83) - 1.5 - 2.2), 83), (sx * (hull_x(83) - 1.5 - 0.6), 83),
                          (sx * (hull_x(57) - 1.5 - 0.6), 57)][::sx]) for f0 in (110, 330) for sx in (1, -1)]),
    part('panel_screws', 'Paneelschrauben', 'Panel screws', 'receiver', 'multi', 'trim', 'Halten die Kielpaneele', 'in den Paneelen',
         bevel=0.2, items=[dict(shape='cyl', axis='x', c=(f0 + df, u), a0=sx * (hull_x(u) - 1.5 - 1.2), a1=sx * (hull_x(u) - 1.5 + 0.2), r=1.5, segs=12)
            for f0 in (110, 330) for df in (6, 58) for u in (62, 78) for sx in (1, -1)]),
    part('seam_pins', 'Fugenbolzen', 'Seam pins', 'receiver', 'multi', 'metal', 'Verbinden Rumpfschale und Kiel', 'quer durch die Fuge (lösbar)',
         bevel=0.4, items=[dict(shape='cyl', axis='x', c=(f, SEAM), a0=sx * (hull_x(SEAM) - 2.0), a1=sx * (hull_x(SEAM) + 0.8), r=3.0, segs=16)
                           for f in (20, 300, 500) for sx in (1, -1)]),
    part('waterline', 'Wasserlinie', 'Waterline stripe', 'receiver', 'multi', 'accent', 'Lackierter Streifen auf beiden Kielflanken (einziges Grafikelement)',
         'lackiert', bevel=0,
         items=[dict(shape='xprof', f0=200, f1=480, cu=0, pts=[(sx * (hull_x(91) - 1.5 + 0.05), 91), (sx * (hull_x(95) - 1.5 + 0.05), 95),
                                                              (sx * (hull_x(95) - 1.5 + 0.35), 95), (sx * (hull_x(91) - 1.5 + 0.35), 91)][::sx])
                for sx in (1, -1)]),
    part('text_r', 'Schriftzug', 'Lettering', 'receiver', 'text', 'anodized', 'Kennung „BASIC  EX-14“ (einzige Schrift)',
         'aufgedruckt (dunkel auf Creme, Schale rechts)', bevel=0, text='BASIC  EX-14', size=5.0, f=300, u=BORE - 2, x=-R_HULL - 0.05,
         side=-1, depth=0.12),
]
# ---------------------------------------------------------------- Zielerfassungsraute (Blickfang)
_lm = (LOCK[0] + LOCK[1]) / 2


def diamond(d):
    return [(LOCK[0] - d, LOCK[2]), (_lm, LOCK[2] - 12 - d * 0.6), (LOCK[1] + d, LOCK[2]), (_lm, LOCK[2] + 12 + d * 0.6)]


P += [
    part('lock_frame', 'Rautenrahmen', 'Lock frame', 'receiver', 'prof', 'trim', 'Blanker Rahmen der Zielerfassungsraute',
         'in die Mulde geschraubt', bevel=0.4, pts=diamond(3.0), w=1.6, x=LOCK_FLOOR + 2.2,
         cuts=[dict(shape='prof', pts=diamond(0.4), w=6, x=LOCK_FLOOR + 2.2)]),
    prof('lock_glass', 'Rautenglas', 'Lock glass', 'receiver', 'glass', 'Schützt die Anzeige', 'im Rahmen', diamond(0.4), 0.6, bevel=0,
         x=LOCK_FLOOR + 2.0),
    part('lock_light', 'Zielerfassung', 'Target lock', 'receiver', 'prof', 'energy',
         'Leuchtende Raute: Rakete geladen und Ziel erfasst; Blickfang links neben dem Visier', 'unter dem Glas in der Mulde', bevel=0.3,
         pts=diamond(-2.0), w=1.2, x=LOCK_FLOOR + 0.6, move=dict(kind='glow', pivot=None, event='ready', max=5.0)),
]
# ---------------------------------------------------------------- Heck: Heckring, Düse
RING_R = R_REAR + 5
P += [
    cyl('rear_ring', 'Heckring', 'Rear ring', 'stock', 'dark_metal', 'Verstärkt das Ende des Abgasrohrs', 'auf das Abgasrohr gepresst',
        'f', (BORE, 0), REAR0 - 12, REAR0 + 10, RING_R, r_in=R_IN - 2, segs=48, bevel=R_SMALL, smooth=True),
    cyl('nozzle', 'Heckdüse', 'Exhaust nozzle', 'stock', 'anodized', 'Kurze Düse hinter dem Heckring (zieht sich zusammen, kein Trichter)',
        'in den Heckring geschraubt', 'f', (BORE, 0), REAR0 - 26, REAR0 - 11, RING_R - 2, r1=RING_R - 1, r_in=R_IN - 5, segs=48, bevel=R_SMALL,
        smooth=True),
    cyl('nozzle_rim', 'Düsenkante', 'Nozzle rim', 'stock', 'trim', 'Blanke Kante der Heckdüse', 'hinten an der Düse',
        'f', (BORE, 0), REAR0 - 27, REAR0 - 25, R_IN - 1, r_in=R_IN - 5.5, segs=48, bevel=0.3, smooth=True),
]
# ---------------------------------------------------------------- Schultersattel: kleiner Kiel im selben Querschnitt, unten hohl
_SAD = drop(R_REAR + 6, BORE, 66, top=BORE + 6)   # Runde 3: Wiege unter dem Rohr, oben offen (zwei Spannbänder)
_sad_line = ([(SADDLE[0] - 2, BORE - R_REAR + 4)] + s_curve((SADDLE[0], BORE - R_REAR + 2), (SADDLE[0] + 34, 72))[1:]   # Runde 2: Keilenden
             + s_curve((SADDLE[0] + 38, 72), ((SADDLE[0] + SADDLE[1]) / 2, 94), n=6)[1:]
             + s_curve(((SADDLE[0] + SADDLE[1]) / 2, 94), (SADDLE[1] - 38, 72), n=6)[1:] + s_curve((SADDLE[1] - 34, 72), (SADDLE[1], BORE - R_REAR + 2))
             + [(SADDLE[1] + 2, BORE - R_REAR + 4)])
_pad = [q for q in _sad_line if SADDLE[0] + 30 <= q[0] <= SADDLE[1] - 30]
P += [
    part('saddle', 'Schultersattel', 'Shoulder saddle', 'stock', 'xprof', 'graphite',
         'Liegt auf der Schulter: Tropfen um das Abgasrohr, unten ein Bogen über der Schulter', 'um das Abgasrohr geklemmt',
         bevel=R_BODY, f0=SADDLE[0], f1=SADDLE[1], cu=0, pts=_SAD,
         cuts=[dict(shape='prof', pts=_sad_line + [(SADDLE[1] + 2, 0), (SADDLE[0] - 2, 0)], w=120),
               dict(shape='cyl', axis='f', c=(BORE, 0), a0=SADDLE[0] - 1, a1=SADDLE[1] + 1, r=R_REAR - 0.5, segs=48)]
         + [dict(shape='plan', pts=[(f, sx * 60), (f + sg * 22, sx * 60), (f, sx * (hull_x(80, R_REAR + 6) - 6))], u0=60, u1=BORE + 50)
            for f, sg in ((SADDLE[0] - 1, 1), (SADDLE[1] + 1, -1)) for sx in (1, -1)]),
    part('saddle_pad', 'Sattelpolster', 'Saddle pad', 'stock', 'multi', 'rubber', 'Polster im Sattelbogen auf der Schulter',
         'in den Bogen geklebt', bevel=R_SMALL,
         items=[dict(shape='prof', pts=[(q[0], q[1] - 2.5) for q in _pad] + [(q[0], q[1] + 1.0) for q in _pad[::-1]], w=26)]),
    part('saddle_straps', 'Spannbänder', 'Saddle straps', 'stock', 'multi', 'anodized', 'Spannen die Wiege um das Abgasrohr',
         'um Abgasrohr und Wiege', bevel=R_FINE, smooth=True,
         items=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=f, a1=f + 12, r=R_REAR + 2.2, r_in=R_REAR - 0.2, segs=48)
                for f in (SADDLE[0] + 30, SADDLE[1] - 42)]),
    part('saddle_screws', 'Sattelschrauben', 'Saddle screws', 'stock', 'multi', 'trim', 'Spannschrauben der Bänder',
         'seitlich an den Bändern', bevel=0.2, items=mirror(screws([(SADDLE[0] + 36, BORE), (SADDLE[1] - 36, BORE)], R_REAR + 2.6, r=1.8, h=0.8))),
]
# ---------------------------------------------------------------- Visierausleger, Schiene, Visier W2 seitlich links
P += [
    part('sight_arm', 'Visierausleger', 'Sight outrigger', 'support', 'xprof', 'anodized', 'Trägt die Schiene 66 mm links neben der Rohrachse',
         'aus der Rumpfschale gewachsen (verschraubt)', bevel=R_SMALL, f0=ARM[0], f1=ARM[1], cu=0,
         pts=[(R_HULL - 8, DECK - 22), (SIDE + 11, DECK - 16), (SIDE + 11, DECK - 8), (R_HULL - 8, DECK - 2)]),
]
_rail = [dict(p, mat='anodized', x=SIDE, attach='auf dem Visierausleger (fest)') for p in rail(ARM[0] - 2, ARM[0] + 48, DECK - 8)]
P += _rail
_sight, SIGHT_ANCHORS = side_mount(*entfernung(ARM[0], DECK, weapon_type='rocket_launcher'), SIDE)
P += _sight
# ---------------------------------------------------------------- Ladeschacht oben (wie BASIC-14: Rakete von oben, Klappe nach rechts)
P += [
    part('load_hatch', 'Ladeklappe', 'Loading hatch', 'mechanism', 'cyl', 'graphite', 'Deckt den Ladeschacht oben im Startrohr; schwenkt '
         'zum Laden nach rechts auf', 'Scharnier rechts am Schacht', bevel=R_FINE, smooth=True, axis='f', c=(BORE, 0), a0=HATCH[0],
         a1=HATCH[1], r=HATCH[3], r_in=R_HULL + 0.6, segs=64,
         cuts=[cut_box(HATCH[0] - 2, HATCH[1] + 2, BORE - 60, BORE + 60, 40, x=HATCH[2] + 20),
               cut_box(HATCH[0] - 2, HATCH[1] + 2, BORE - 60, BORE + 60, 40, x=-(HATCH[2] + 20)),
               cut_box(HATCH[0] - 2, HATCH[1] + 2, BORE - 60, BORE + 10, 2 * HATCH[2] + 4)],
         move=dict(kind='rotate', pivot=HATCH_HINGE, axis='f', range_deg=(0, 115), event='reload',
                   expect=((HATCH_HINGE[0], BORE + R_HULL, HATCH[2]), (0, 1, -0.3)))),
    part('hatch_hinge', 'Ladeklappenscharnier', 'Hatch hinge', 'mechanism', 'cyl', 'dark_metal', 'Lagert die Ladeklappe rechts',
         'rechts am Schacht angeformt', bevel=R_FINE, smooth=True, axis='f', c=HATCH_HINGE[1:], a0=HATCH[0] + 20, a1=HATCH[1] - 20,
         r=3.2, segs=20),
    part('hatch_ribs', 'Klappenrippen', 'Hatch ribs', 'mechanism', 'multi', 'dark_metal', 'Drei Querrippen auf der Ladeklappe (Griff und Steifigkeit)',
         'auf die Ladeklappe geschraubt', bevel=R_FINE, parent_part='load_hatch',
         items=[dict(shape='box', f0=f, f1=f + 6, u0=BORE + R_HULL + 1.5, u1=BORE + R_HULL + 5, w=36) for f in (104, 154, 204)]),
    part('cap_release', 'Klappenknopf', 'Hatch release', 'grip_controls', 'cyl', 'accent', 'Verriegelt die Ladeklappe',
         'Druckknopf links am Rumpf hinter dem Schacht', bevel=R_FINE, axis='x', c=(SLOT[0] - 14, BORE + 20), a0=hull_x(BORE + 20) - 3,
         a1=hull_x(BORE + 20) + 2.5, r=4.5, segs=20,
         move=dict(kind='translate', pivot=(SLOT[0] - 14, BORE + 20, hull_x(BORE + 20)), vector_mm=(0, 0, -2.5), event='reload',
                   expect=((SLOT[0] - 14, BORE + 20, hull_x(BORE + 20) + 2.5), (0, 0, -1)))),
]
# ---------------------------------------------------------------- Griff, Sicherung, Griffkiel (Stützhand)
P += grip_v21(top=GRIP_TOP)
P += [
    cyl('safety', 'Sicherung', 'Safety', 'grip_controls', 'accent', 'Sichert den Abzug (Daumen der Haupthand)', 'Kipphebel links über dem Griff',
        'x', (-6, 54), hull_x(54) - 1.5 - 1, hull_x(54) - 1.5 + 3, 4.0, segs=20,
        move=dict(kind='rotate', pivot=(-6, 54, hull_x(54) - 1.5), axis='x', range_deg=(0, 45), event='safety')),
    part('keel_grip', 'Griffkiel', 'Keel grip', 'support', 'multi', 'rubber', 'Rutschfeste Zone unter dem Bauch für die Stützhand',
         'unten auf den Kiel geklebt', bevel=R_SMALL,
         items=[dict(shape='xprof', f0=SUP[0] - 52 + 18 * i, f1=SUP[0] - 40 + 18 * i, cu=0,
                     pts=[(11.5, SUP[1] - 2.5), (-11.5, SUP[1] - 2.5), (-14, SUP[1] + 8), (14, SUP[1] + 8)]) for i in range(6)]),
]
# ---------------------------------------------------------------- Rakete (hülsenlos)
P += [
    part('rocket', 'Rakete', 'Rocket', 'ammo', 'multi', 'dark_metal', 'Eine kurze Rakete im Schacht; verlässt das Rohr ganz (keine Hülse)',
         'im Schacht unter der Ladeklappe', bevel=R_SMALL, smooth=True, caseless=True,
         items=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=R0, a1=R1, r=R_IN - 2, segs=32)]
         + [dict(shape='box', f0=R0, f1=R0 + 30, u0=BORE - 0.8, u1=BORE + 0.8, w=2 * (R_IN - 2)),
            dict(shape='box', f0=R0, f1=R0 + 30, u0=BORE - R_IN + 2, u1=BORE + R_IN - 2, w=1.6)],
         move=dict(kind='translate', pivot=(0, BORE, 0), vector_mm=(0, LOWER, 0), event='reload', removable=True,
                   note='Ruhelage = geladen; die Ladeaktion senkt sie von oben in den Schacht (wie BASIC-14)',
                   expect=((R0, BORE + R_IN - 2, 0), (0, 1, 0)))),
    cyl('rocket_head', 'Gefechtskopf', 'Warhead', 'ammo', 'anodized', 'Gefechtskopf der Rakete (im offenen Schacht zu sehen)',
        'vorn an der Rakete', 'f', (BORE, 0), R1, R2, R_IN - 2, r1=9, segs=32, bevel=R_SMALL, smooth=True, parent_part='rocket'),
]
PARTS = P

# ---------------------------------------------------------------- Anker, Weltpunkte, Aktionen
ANCHORS = {
    'Socket_Hand': dict(at=(0, 0, 0), part='grip', note='Haupthand, auf der Griffachse (V: BGM-1)'),
    'Socket_SupportHand': dict(at=(SUP[0], SUP[1] - 3, 0), part='keel_grip', note='Unterseite des Bauchs (Griffkiel)'),
    'Socket_Muzzle': dict(at=(F1 + 5, BORE, 0), part='bore_ring', note='Stirn des Bohrungsrings auf der Rohrachse'),
    'Socket_Breech': dict(at=(REAR0 - 12, BORE, 0), part='rear_ring', note='Heck (Düse, fest; geladen wird oben im Schacht)'),
}
ANCHORS.update(SIGHT_ANCHORS)
EGO_GRIPS = {
    'grip':    dict(contact=(-3, -6, -16.5), palm=(0.15, 0.0, 1.0), fingers=(1.0, -0.06, 0.0), fingers_pose='trigger',
                    src='V: Griff BGM-1 wie die Familie'),
    'support': dict(contact=(SUP[0], SUP[1] - 4.5, -2), palm=(0.0, 1.0, -0.25), fingers=(0.08, 0.15, -1.0), fingers_pose='underhand',
                    src='A: unter dem Bauch auf dem Griffkiel'),
    'mag':     dict(part='rocket', contact=(R0 + 22, BORE + R_IN - 1, 4), palm=(0.0, -1.0, -0.1), fingers=(0.25, 0.0, -1.0), fingers_pose='mag_hold',
                    src='A: auf dem hinteren Drittel der Rakete, Hand von oben (wie BASIC-14)'),
    'push':    dict(part='rocket', contact=(R0 + 64, BORE + R_IN - 1, 0), palm=(0.0, -1.0, 0.0), fingers=(1.0, 0.0, -0.15), fingers_pose='open',
                    src='A: flache Hand drückt die Rakete von oben in den Sitz (wie BASIC-14)'),
    'cap':     dict(part='load_hatch', contact=(158, BORE + R_HULL + 3, 18), palm=(0.0, -1.0, -0.2), fingers=(1.0, 0.0, -0.1), fingers_pose='open',
                    src='A: flache Hand auf der Ladeklappe, drückt sie zu (folgt der Klappe)'),
    'charge':  dict(contact=(SLOT[0] - 14, BORE + 20, hull_x(BORE + 20) + 4), palm=(0.0, 0.0, -1.0), fingers=(0.45, 0.9, 0.0),
                    fingers_pose='pinch', src='A: am Klappenknopf links hinter dem Schacht (verriegelt)'),
}
EGO_LIVE = dict(trigger='trigger', bolt='', port='', fill=['lock_light'])
EJECT = None    # hülsenlos: die Rakete verlässt das Rohr ganz (wie BASIC-14)
POINTS = collect(EJECT, EGO_GRIPS, dict(grip='grip', support='keel_grip', charge='hull'))
ACTIONS = {
    'fire': dict(de='Abschuss', frames=12, step=1, keys={'trigger': [(0, 0), (2, 1), (6, 0)],
                                                         'lock_light': [(0, 1), (2, 1), (4, 0), (12, 0)]},
                 events=[(2, 'launch')]),
    'reload': dict(de='Ladeklappe auf, Rakete von oben in den Schacht senken, Klappe zu, verriegeln', frames=100, keys={
        'load_hatch': [(0, 0), (14, 1), (70, 1), (82, 0)], 'rocket': [(0, 1), (24, 1), (60, 0)],
        'cap_release': [(0, 0), (84, 0), (88, 1), (94, 0)], 'lock_light': [(0, 0), (88, 0), (92, 1), (100, 1)]},
        events=[(14, 'hatch_open'), (60, 'rocket_in'), (82, 'hatch_closed'), (92, 'ready')], view=(0.2, 0.85, 0.5)),
}
EXPLODE = {'sight': (0, 110, 0), 'mechanism': (0, 90, -60), 'ammo': (0, 0, 130), 'barrel': (120, 0, 0), 'support': (60, -60, 0),
           'stock': (-120, -40, 0), 'grip_controls': (-10, -80, 0), 'receiver': (0, -60, 0)}
HERO = (0.55, -0.72, 0.30)   # A: Produktbild von links vorn – Raute, Visier, Bauch und Tropfenstirn zur Kamera
SIGHT_ID = 'W2'
