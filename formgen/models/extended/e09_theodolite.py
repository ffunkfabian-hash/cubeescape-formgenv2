"""EXTENDED-09 „Theodolite“ – eigenständiges Sci-Fi-Scharfschützengewehr der BASIC-Familie (Formgen v2 0.25 „Pauldron“).

Eigenes Modell im BALLON-Kit-Vokabular (reines Python, kein bpy). Keine Teile oder Umbauten von BASIC-09: aus `basic.common` kommen nur
genormte Familienschnittstellen (Griffmodul BGM-1, Zielfernrohr Z3 „Lang“ auf zwei Schienen BRI-22, Kastenmagazin BMW-R, Schraubenköpfe)
und Hilfen (`cut_box`, `mirror`). Geladen über `formgen.extended`, gerendert mit BALLONs unverändertem `tools/blender_build.main`
(`tools/extended_render.py`).

Formsprache (Stilhandbuch BALLON §3; Auswahl und Skizzen: docs/extended.md)
- Leitmerkmal Stativ (Theodolit): Das Gewehr ist ein Messinstrument, das auf drei Punkten steht – Griff mit Magazin, der Pylon vorn
  unter dem Rumpf und das Kolbenbein; Pylon und Kolbenbein tragen Gummifüße im Rautenquerschnitt (Runde 5: keine dünnen Stifte mehr,
  Nutzer). Zwischen Magazin und Pylon spannt der Rumpf frei
  (Spannweite), davor läuft der lange Lauf frei bis zur Bremse.
- Silhouette: lang (1,18 m), gerade Deckslinie, die hinten zum Wangenkamm steigt; unten drei Stützen mit offenen Feldern dazwischen.
- Querschnitt: Raute mit Gürtel – Oberschale und Kiel laufen schräg zur Gratlinie auf Laufhöhe, dort ein senkrechter Gürtel 13 mm hoch
  (Fuge in der Mitte); oben ein schmales Deck, unten ein runder Kiel. Kolben, Pylon und Butt sind derselbe Querschnitt.
- Negativraum: die Spannweite unter dem Rumpf zwischen Magazin und Pylon; die J-Kammerbahn links (Verschluss sichtbar).
- Blickfang (genau einer): die Libelle links unter dem Zielfernrohr, ein leuchtendes Röhrchen mit Luftblase in blanken Kappen.
- Zweiton: Creme-Oberschale über Graphit-Kiel, Teilung an der Gratlinie (Gürtelfuge), vom Butt bis zur Stirn.
- Schichten: Gürtel 0,5 mm über dem Kiel, Wangenpolster und Pylonpolster als Einlagen auf den Schrägen, Stirnplatte 3 mm vor der Stirn.
- Grafik: ein Gratstreifen auf dem Gürtel beidseitig (einziges Grafikelement); eine Schrift rechts auf dem Gürtel.
- Front mehrstufig: Mündungsbremse mit zwei Kammern und Krone → freier kannelierter Lauf → Laufbuchse → Stirnplatte → Pylon darunter.
- Ergonomie: Griff BGM-1 (Socket_Hand 0/0), Stützhand am Pylon (Griffpolster), Kammerstängel links (die Stützhand repetiert, wie
  BASIC-09), Wangenkamm 26 mm unter der Visierlinie. Akzent-Bedienfunktion: Magazinhalter (1).

Herkunft der Zahlen: V = Vorgabe (Familie/Schnittstelle, BASIC-09 Pilot v2.1 bzw. `basic.common`), A = Annahme (Entwurf 0.25),
G = gemessen; Zahlen ohne Kennung sind A (Entwurf 0.25, an den Renders gesichtet).
Maße mm; f nach vorn, u nach oben, x nach links; Socket_Hand = (0, 0, 0).
"""
import math

from basic.common import (part, prof, box, cyl, cut_box, screws, mirror, rail, rifle_mag, grip_v21, lang,
                          R_BODY, R_MID, R_SMALL, R_FINE)
from basic.variant import collect

META = dict(id='EXTENDED-09', num='E09', sheet_id='EA09', type='sniper_rifle', type_de='Scharfschützengewehr', type_en='Sniper Rifle',
            family='BASIC', name='Theodolite', nick='Stativ', ammo='special', fire='bolt_action',
            reference_length_m=1.178, reference_length_source='G: Hülle des Datensatzes 0.25 (BASIC-09 1,135 m gemessen als Rahmen, V)',
            inspired_by='BASIC-09 Familie; Formgen v1 als Haltung (eine mutige Gesamtarchitektur)',
            summary='Repetier-Scharfschützengewehr als Messinstrument: Rautenrumpf auf drei Stützen (Magazin, Pylon und Kolbenbein mit Gummifüßen), '
                    'Zielfernrohr Z3 und Libelle (EXTENDED-Reihe).')
ASSEMBLIES = [
    dict(id='receiver', de='Hauptgehäuse', en='Receiver'),
    dict(id='barrel', de='Lauf', en='Barrel'),
    dict(id='ammo', de='Munitionsversorgung', en='Ammunition feed'),
    dict(id='sight', de='Visier', en='Sight'),
    dict(id='grip_controls', de='Griff und Bedienung', en='Grip and controls'),
    dict(id='support', de='Stützbereich', en='Support'),
    dict(id='stock', de='Schaft', en='Stock'),
    dict(id='mechanism', de='Bewegliche Mechanik', en='Moving mechanism'),
]

GRIP_TOP = 40            # V: Griffoberkante wie BASIC-09
BORE = 92                # A: Laufachse (BASIC-09 96, V) – auf der Gratlinie
SEAM = 88.5              # A: Gürtelfuge Oberschale/Kiel
BELT = (84.0, 97.0)      # A: senkrechter Gürtel (Unterkante Kiel-Gürtel, Oberkante Schalen-Gürtel)
HALF = 23.0              # A: halbe Breite am Gürtel (46 mm; BASIC-09 Gehäuse 40, V)
DECK_HW = 11.0           # A: halbe Deckbreite am Wangenkamm (oben 22 mm)
KEEL_HW = 6.0            # A: halbe Kielbreite unten (u −6)
COMB = 132               # A: Wangenkamm; Visierlinie 158 − 26 mm Wangenabstand
DECK = 116               # A: Deck vor dem Kamm (dort ist die Schale breiter, 33 mm)
CU = BORE + 66           # V: Visierlinie 66 mm über der Laufachse (Z3 wie BASIC-09)
BUTT, NOSE = -331, 496   # A: Kolbenende / Stirn des Rumpfs
F_OBJ = 130              # V: Ringstirn Z3 wie BASIC-09 (Augenpunkt f 40)
SEAT_F, FOOT_F = (-74, -24), (96, 134)   # A: Schienen hinten (auf dem Kamm) und vorn (auf dem Deck)
SPAN = (205, 368, 70)    # A: Spannweite f0, f1 und Unterkante u (Rumpf 46 mm hoch zwischen Magazin und Pylon)
PYLON = (398, 437, 10)   # A: Pylon unten f0, f1, Unterkante (vordere Stütze; Stützhand)
MAG = (76, 40, 44)       # A: Magazinschacht hinten f, Tiefe, Oberkante (fünf Patronen, BASIC-09 37 mm, V)
TOE = (-312, -282, -8)   # A: Kolbenbein unten f0, f1, Unterkante (trägt den Kolbenfuß)
ARCH = (-226, -130, 64)  # A: Kolbenbogen f0, f1, Scheitel u (Runde 2: der Kolben spannt wie der Rumpf zwischen Griff und Kolbenbein)
BOLT_F = (-45, 15)       # A: Verschluss in Ruhelage
HANDLE_F = -35           # A: Kammerstängel am Verschluss
KNOB = (HANDLE_F - 8, BORE - 14)   # A: Kammerknopf (f, u) links unter der Gratlinie (wie BASIC-09: schräg unten hinten)
BOLT_TRAVEL = 66         # V: Verschlussweg wie BASIC-09
BARREL = (480, 790)      # A: Lauf in der Stirn bis zur Bremse
BRAKE = (772, 832)       # A: Mündungsbremse mit zwei Kammern
LEVEL = (10, 58, 104.0)  # A: Libelle f0, f1, Höhe der Achse (links unter dem Zielfernrohr)


def upper_x(u):
    """Halbe Breite der Oberschale bei u (Schräge vom Gürtel zum Kamm)."""
    return HALF - (HALF - DECK_HW) * (u - BELT[1]) / (COMB + 1 - BELT[1])


def lower_x(u):
    """Halbe Breite des Kiels bei u (Schräge vom Gürtel zum Kiel)."""
    return KEEL_HW + (HALF - 0.5 - KEEL_HW) * (u - (-6)) / (BELT[0] - (-6))


UPPER_X = [(HALF, SEAM + 0.5), (HALF, BELT[1]), (DECK_HW, COMB + 1), (-DECK_HW, COMB + 1), (-HALF, BELT[1]), (-HALF, SEAM + 0.5)]
LOWER_X = ([(HALF - 0.5, SEAM - 0.5), (-(HALF - 0.5), SEAM - 0.5), (-(HALF - 0.5), BELT[0]), (-KEEL_HW, -6)]
           + [(-KEEL_HW + 3 - 3 * math.cos(math.radians(a)), -6 - 3.5 * math.sin(math.radians(a))) for a in (30, 60, 90)]
           + [(KEEL_HW - 3 + 3 * math.cos(math.radians(a)), -6 - 3.5 * math.sin(math.radians(a))) for a in (90, 60, 30)]
           + [(KEEL_HW, -6), (HALF - 0.5, BELT[0])])


def s_curve(a, b, n=8):
    """Weicher Übergang von a nach b (Kosinus): ineinanderlaufende Kehlen statt Stufen."""
    return [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * (1 - math.cos(math.pi * i / n)) / 2) for i in range(n + 1)]


def strip(u0, u1, t, side=1, fn=upper_x):
    """Querprofil einer Einlage auf einer Schräge zwischen u0 und u1, t mm stark (side +1 links, −1 rechts)."""
    pts = [(fn(u0), u0), (fn(u1), u1), (fn(u1) + t, u1), (fn(u0) + t, u0)]
    pts = [(side * x, u) for x, u in pts]
    return pts if side == 1 else pts[::-1]


# Oberkante der Oberschale (Seitenprofil): Kolbenkappe, Wangenkamm, Rampe aufs Deck, Deck, Stirnfase
TOP = [(BUTT - 14, 118), (BUTT, 124), (BUTT + 9, COMB), (-22, COMB)] + s_curve((-22, COMB), (18, DECK)) [1:] + [(455, DECK), (NOSE + 1, 99)]
# Unterkante des Kiels (Seitenprofil): Kolbenspitze, Kolbenlinie zum Griff, Magazinkragen, Kehle zur Spannweite, Pylon, Stirn
_UNDER = ([(BUTT - 14, 2), (BUTT, 4), (BUTT + 7, -4), (TOE[0], TOE[2]), (TOE[1], TOE[2])]
          + s_curve((TOE[1] + 4, TOE[2]), (ARCH[0], ARCH[2]))[1:] + s_curve((ARCH[1], ARCH[2]), (-58, 40.5))[0:] + [(-44, 40.5),
           (MAG[0] - 12, 40.5), (MAG[0] - 6, 31), (MAG[0] + MAG[1] + 6, 31), (MAG[0] + MAG[1] + 12, 40.5)]
          + s_curve((160, 40.5), (SPAN[0], SPAN[2]))[1:] + s_curve((SPAN[1], SPAN[2]), (PYLON[0], PYLON[2] + 4))[1:]
          + [(PYLON[0] + 4, PYLON[2]), (PYLON[1] - 4, PYLON[2])] + s_curve((PYLON[1], PYLON[2] + 4), (478, 72))[1:]
          + [(NOSE, 80), (NOSE + 1, SEAM)])
_up_cut = dict(shape='prof', pts=TOP + [(NOSE + 12, 99), (NOSE + 12, 220), (BUTT - 14, 220)], w=80)
_lo_cut = dict(shape='prof', pts=_UNDER + [(NOSE + 12, SEAM), (NOSE + 12, -60), (BUTT - 14, -60)], w=80)
# J-Kammerbahn links: senkrechter Ast für das Anheben des Stängels, Längsast für den Weg zurück (Verschluss sichtbar)
_bahn = [cut_box(HANDLE_F - 10, HANDLE_F + 8, BORE - 18, 112, 30, x=15), cut_box(HANDLE_F - BOLT_TRAVEL - 10, HANDLE_F + 8, 99, 112, 30, x=15)]
PORT = (-50, -6, 90, 106)   # A: Auswurffenster rechts in der Oberschale

FOOT_H = 9.0             # A: Sohlenhöhe (Runde 5)
FOOT_SPREAD = 7.0        # A: Sohle unten je Seite 7 mm breiter als oben (Auflage)


def FOOT_X(top, hw):
    """Querschnitt einer Sohle (x, u): oben so breit wie die Fußplatte, unten 7 mm je Seite breiter, Kanten unten gerundet."""
    b = top - FOOT_H
    return [(hw, top), (-hw, top), (-(hw + FOOT_SPREAD), b + 3), (-(hw + FOOT_SPREAD - 2.5), b), (hw + FOOT_SPREAD - 2.5, b),
            (hw + FOOT_SPREAD, b + 3)]


def FOOT_PLAN(f0, f1, top, w, r=9.0):
    """Sohle in der Draufsicht an allen vier Ecken mit r gerundet; w = halbe Breite unten."""
    out = []
    for fe, sg in ((f0, 1), (f1, -1)):
        for sx in (1, -1):
            arc = [(fe + sg * (r - r * math.cos(math.radians(a))), sx * (w - r + r * math.sin(math.radians(a)))) for a in range(0, 91, 15)]
            out.append(dict(shape='plan', pts=[(fe - sg, sx * (w - r))] + arc + [(fe + sg * r, sx * (w + 5)), (fe - sg, sx * (w + 5))],
                            u0=top - FOOT_H - 1, u1=top + 1))
    return out


P = []
# ---------------------------------------------------------------- Rumpf: Oberschale (Creme) und Kiel (Graphit), Kolben inbegriffen
P += [
    part('upper', 'Oberschale', 'Upper shell', 'receiver', 'xprof', 'shell',
         'Rautenrumpf oben vom Kolben bis zur Stirn: Wangenkamm, Deck mit den Schienen, Kammerbahn und Auswurffenster',
         'Grundkörper; mit dem Kiel an der Gürtelfuge verschraubt', bevel=R_MID, f0=BUTT, f1=NOSE, cu=0, pts=UPPER_X,
         cuts=[_up_cut, cut_box(*PORT, 20, x=-HALF + 4)] + _bahn
         + [dict(shape='cyl', axis='f', c=(LEVEL[2], upper_x(LEVEL[2]) - 1.0), a0=LEVEL[0] - 6, a1=LEVEL[1] + 6, r=6.6, segs=32)]   # Libellenmulde
         + [dict(shape='plan', pts=[(NOSE - 30, sx * 30), (NOSE + 2, sx * 30), (NOSE + 2, sx * 14), (NOSE - 30, sx * (HALF + 1))],
                 u0=BELT[1] - 1, u1=140) for sx in (1, -1)]),   # Stirn in der Draufsicht gefast
    part('lower', 'Kiel', 'Keel', 'receiver', 'xprof', 'graphite',
         'Rautenrumpf unten: Kolbenlinie, Griffmodul, Magazinkragen, Spannweite und Pylon in einem Stück',
         'unter der Oberschale, Fuge 1 mm', bevel=R_BODY, f0=BUTT, f1=NOSE, cu=0, pts=LOWER_X,
         cuts=[_lo_cut, cut_box(MAG[0] - 0.5, MAG[0] + MAG[1] + 0.5, 20, MAG[2] + 2, 25)] + _bahn[:1]
         + [dict(shape='plan', pts=[(PYLON[0] - 30, sx * 30), (PYLON[0] + 6, sx * 30), (PYLON[0] + 6, sx * 9), (PYLON[0] - 30, sx * 12)],
                 u0=-20, u1=SPAN[2] - 6) for sx in (1, -1)]   # Pylon hinten in der Draufsicht verjüngt
         + [dict(shape='plan', pts=[(PYLON[1] - 4, sx * 30), (PYLON[1] + 40, sx * 30), (PYLON[1] + 40, sx * 13), (PYLON[1] - 4, sx * 9)],
                 u0=-20, u1=SPAN[2] - 2) for sx in (1, -1)]),  # Pylon vorn verjüngt
    part('nose_plate', 'Stirnplatte', 'Nose plate', 'barrel', 'xprof', 'anodized', 'Fasst die Laufbuchse an der Stirn',
         'vorn auf den Rumpf geschraubt', bevel=R_SMALL, f0=NOSE - 1, f1=NOSE + 3, cu=0,
         pts=[(sx * x * 0.86, u) for sx in (1, -1) for x, u in ([(lower_x(76), 76), (HALF, BELT[0]), (HALF, BELT[1]), (upper_x(102), 102)][::sx])]),   # Raute wie der Rumpf
    cyl('bushing', 'Laufbuchse', 'Barrel bushing', 'barrel', 'trim', 'Blanker Ring um den Lauf an der Stirn', 'in die Stirnplatte gepresst',
        'f', (BORE, 0), NOSE + 2, NOSE + 8, 13.0, r_in=9.8, segs=40, bevel=0.5, smooth=True),
    part('cheek_pad', 'Wangenpolster', 'Cheek pad', 'stock', 'xprof', 'rubber', 'Anlage der Wange links am Kamm',
         'in die linke Schräge eingelegt', bevel=R_SMALL, f0=-250, f1=-110, cu=0, pts=strip(108, 127, 1.4)),
    part('deck_strip', 'Deckleiste', 'Deck strip', 'receiver', 'xprof', 'anodized', 'Eloxierte Leiste auf dem Deck vor dem Zielfernrohr (Runde 2)',
         'auf das Deck geschraubt', bevel=R_FINE, f0=150, f1=440, cu=0, pts=[(12, DECK - 0.5), (10.5, DECK + 2), (-10.5, DECK + 2), (-12, DECK - 0.5)]),
    part('deck_screws', 'Leistenschrauben', 'Deck strip screws', 'receiver', 'multi', 'trim', 'Halten die Deckleiste', 'in der Leiste',
         bevel=0.2, items=[dict(shape='cyl', axis='u', c=(f, sx * 6.5), a0=DECK + 1.5, a1=DECK + 2.6, r=1.5, segs=12) for f in (158, 432) for sx in (1, -1)]),
    part('belt_pins', 'Gürtelbolzen', 'Belt pins', 'receiver', 'multi', 'metal', 'Verbinden Oberschale und Kiel an der Gürtelfuge',
         'quer durch den Gürtel (lösbar)', bevel=0.4, items=mirror(screws([(-140, SEAM), (160, SEAM), (SPAN[1] - 6, SEAM)], HALF - 1, r=3.2, h=1.2))),
    part('stock_screws', 'Kolbenschrauben', 'Stock screws', 'stock', 'multi', 'trim', 'Halten das Wangenpolster',
         'in der Schale', bevel=0.2, items=screws([(-240, 117.5), (-120, 117.5)], upper_x(117.5) + 1.0, r=1.5, h=0.8)),
    part('band_side', 'Gratstreifen', 'Ridge stripe', 'receiver', 'multi', 'accent', 'Lackierter Streifen auf dem Gürtel (einziges Grafikelement)',
         'lackiert, beidseitig auf dem Gürtel', bevel=0,
         items=[dict(shape='prof', pts=[(282, 91.2), (372, 91.2), (376, 94.6), (286, 94.6)], w=0.3, x=sx * (HALF + 0.15)) for sx in (1, -1)]),
    part('text_r', 'Schriftzug', 'Lettering', 'receiver', 'text', 'anodized', 'Kennung „BASIC  EX-09“ (einzige Schrift)',
         'aufgedruckt (dunkel auf Creme, Gürtel rechts)', bevel=0, text='BASIC  EX-09', size=4.2, f=214, u=90.6, x=-HALF - 0.05,
         side=-1, depth=0.12),
]
# ---------------------------------------------------------------- Libelle (Blickfang)
_lc, _lx = LEVEL[2], upper_x(LEVEL[2]) - 1.0
P += [
    cyl('level_glass', 'Libellenröhrchen', 'Level vial', 'receiver', 'glass', 'Gläsernes Röhrchen der Libelle', 'in der Mulde zwischen den Kappen',
        'f', (_lc, _lx), LEVEL[0], LEVEL[1], 4.6, segs=32, bevel=0, smooth=True),
    part('level_fluid', 'Libelle', 'Level', 'receiver', 'cyl', 'energy',
         'Leuchtende Libelle: zeigt die Verkantung (Blase mittig = waagerecht); Blickfang links', 'im Röhrchen', bevel=0, smooth=True,
         axis='f', c=(_lc, _lx), a0=LEVEL[0] + 2, a1=LEVEL[1] - 2, r=3.6, segs=32, move=dict(kind='glow', pivot=None, event='ready', max=3.0)),
    cyl('level_bubble', 'Libellenblase', 'Level bubble', 'receiver', 'metal', 'Blase in der Libelle (blanker Kern)', 'im Röhrchen',
        'f', (_lc + 0.8, _lx), (LEVEL[0] + LEVEL[1]) / 2 - 3.5, (LEVEL[0] + LEVEL[1]) / 2 + 3.5, 3.9, segs=24, bevel=0.6, smooth=True),
    part('level_caps', 'Libellenkappen', 'Level caps', 'receiver', 'multi', 'trim', 'Blanke Kappen an den Enden des Röhrchens',
         'in die Mulde geschraubt', bevel=0.4, smooth=True,
         items=[dict(shape='cyl', axis='f', c=(_lc, _lx), a0=a, a1=a + 5, r=6.2, r_in=4.4, segs=32) for a in (LEVEL[0] - 5, LEVEL[1])]),
    part('level_ticks', 'Libellenmarken', 'Level marks', 'receiver', 'multi', 'trim', 'Drei Teilstriche über der Libelle',
         'in die Schräge geprägt', bevel=0.2,
         items=[dict(shape='box', f0=f - 0.6, f1=f + 0.6, u0=_lc + 7.5, u1=_lc + 10.5, w=1.2, x=upper_x(_lc + 9) - 0.2)
                for f in ((LEVEL[0] + LEVEL[1]) / 2 - 7, (LEVEL[0] + LEVEL[1]) / 2, (LEVEL[0] + LEVEL[1]) / 2 + 7)]),
]
# ---------------------------------------------------------------- Mechanik: Verschluss, Kammerstängel, Auswurfkante
P += [
    box('bolt', 'Verschluss', 'Bolt', 'mechanism', 'metal', 'Verriegelt die Patrone; gleitet nach dem Entriegeln zurück',
        'im Rumpf geführt (gleitet)', *BOLT_F, BORE - 8, BORE + 8, 16, bevel=R_SMALL,
        move=dict(kind='translate', pivot=(-15, BORE, 0), vector_mm=(-BOLT_TRAVEL, 0, 0), event='bolt', expect=((-15, BORE, -8), (-1, 0, 0)))),
    part('bolt_handle', 'Kammerstängel', 'Bolt handle', 'mechanism', 'tube', 'dark_metal', 'Hebel zum Entriegeln (Stützhand); zeigt schräg '
         'nach unten hinten, hebt sich 60°', 'am Verschluss (dreht um die Laufachse)', bevel=0, parent_part='bolt', r=4.2,
         path=[(HANDLE_F, BORE - 2, 1.5), (HANDLE_F - 3, BORE - 5, 22), (KNOB[0], KNOB[1], 32)],
         move=dict(kind='rotate', pivot=(HANDLE_F, BORE, 0), axis='f', range_deg=(0, 60), event='bolt',
                   expect=((KNOB[0], KNOB[1], 38), (0, 1, 0)))),
    cyl('bolt_knob', 'Kammerknopf', 'Bolt knob', 'mechanism', 'graphite', 'Griffkugel des Kammerstängels', 'am Kammerstängel',
        'x', KNOB, 30, 44, 7.5, segs=20, bevel=R_SMALL, parent_part='bolt_handle'),
    part('port_edge', 'Auswurfkante', 'Port edge', 'receiver', 'multi', 'trim', 'Blanke Lippen ober- und unterhalb des Auswurffensters',
         'in die Schale eingesetzt', bevel=0.3, items=[dict(shape='box', f0=PORT[0] - 2, f1=PORT[1] + 2, u0=u, u1=u + 1.6, w=2.0, x=-HALF + 0.6)
                                                         for u in (PORT[2] - 1.8, PORT[3] + 0.2)]),
]
# ---------------------------------------------------------------- Pylon: Griffpolster
P += [
    part('pylon_pad', 'Pylonpolster', 'Pylon grip pad', 'support', 'multi', 'rubber', 'Griffzone der Stützhand an beiden Flanken des Pylons',
         'in die Schrägen eingelegt', bevel=R_SMALL,
         items=[dict(shape='xprof', f0=PYLON[0] + 8, f1=PYLON[1] - 6, cu=0, pts=strip(22, 56, 1.4, sx, lower_x)) for sx in (1, -1)]),
]
# ---------------------------------------------------------------- Füße unter Pylon und Kolbenbein, Schaftkappe
P += [
    # Runde 5 (Nutzer: „die zwei dünnen Pinner … und den Pinn am Schaft verstehe ich nicht“): keine Stifte mehr – Pylon und Kolbenbein
    # stehen auf eigenen Füßen im Querschnitt des Rumpfs: eloxierte Fußplatte, darunter eine Gummisohle, die sich zur Auflage verbreitert.
    part('pylon_plate', 'Pylonfußplatte', 'Pylon foot plate', 'support', 'xprof', 'anodized', 'Fußplatte unter dem Pylon; trägt die Sohle',
         'unter den Pylon geschraubt', bevel=R_FINE, f0=PYLON[0] + 1, f1=PYLON[1] - 1, cu=0,
         pts=[(lower_x(PYLON[2]) + 1.5, PYLON[2] + 1.5), (-(lower_x(PYLON[2]) + 1.5), PYLON[2] + 1.5),
              (-(lower_x(PYLON[2]) + 3.0), PYLON[2] - 1.5), (lower_x(PYLON[2]) + 3.0, PYLON[2] - 1.5)]),
    part('pylon_foot', 'Pylonfuß', 'Pylon foot', 'support', 'xprof', 'rubber', 'Gummisohle: vordere Auflage des Stativs (Sandsack, Brüstung)',
         'unter die Fußplatte vulkanisiert', bevel=R_SMALL, f0=PYLON[0] - 1, f1=PYLON[1] + 1, cu=0, pts=FOOT_X(PYLON[2] - 1.5, lower_x(PYLON[2]) + 3.0),
         cuts=FOOT_PLAN(PYLON[0] - 1, PYLON[1] + 1, PYLON[2] - 1.5, lower_x(PYLON[2]) + 3.0 + FOOT_SPREAD)),
    part('toe_plate', 'Kolbenfußplatte', 'Toe foot plate', 'stock', 'xprof', 'anodized', 'Fußplatte unter dem Kolbenbein; trägt die Sohle',
         'unter das Kolbenbein geschraubt', bevel=R_FINE, f0=TOE[0] + 1, f1=TOE[1] - 1, cu=0,
         pts=[(KEEL_HW + 1.5, TOE[2] + 1.5), (-(KEEL_HW + 1.5), TOE[2] + 1.5), (-(KEEL_HW + 4.5), TOE[2] - 1.5), (KEEL_HW + 4.5, TOE[2] - 1.5)]),
    part('toe_foot', 'Kolbenfuß', 'Toe foot', 'stock', 'xprof', 'rubber', 'Gummisohle: hintere Auflage des Stativs',
         'unter die Fußplatte vulkanisiert', bevel=R_SMALL, f0=TOE[0] - 3, f1=TOE[1] + 3, cu=0, pts=FOOT_X(TOE[2] - 1.5, KEEL_HW + 4.5),
         cuts=FOOT_PLAN(TOE[0] - 3, TOE[1] + 3, TOE[2] - 1.5, KEEL_HW + 4.5 + FOOT_SPREAD)),
    part('foot_screws', 'Fußschrauben', 'Foot screws', 'support', 'multi', 'trim', 'Halten die Fußplatten',
         'seitlich in den Fußplatten', bevel=0.2,
         items=[dict(shape='cyl', axis='x', c=(f, u), a0=sx * (hw + 1.2), a1=sx * (hw + 2.4), r=1.3, segs=12)
                for f, u, hw in ((PYLON[0] + 8, PYLON[2], lower_x(PYLON[2]) + 1.5), (PYLON[1] - 8, PYLON[2], lower_x(PYLON[2]) + 1.5),
                                 (TOE[0] + 7, TOE[2], KEEL_HW + 2.5), (TOE[1] - 7, TOE[2], KEEL_HW + 2.5)) for sx in (1, -1)]),
    part('butt_pad', 'Schaftkappe', 'Butt pad', 'stock', 'xprof', 'rubber', 'Kappe im Rautenquerschnitt; Anlage an der Schulter',
         'auf das Kolbenende gesteckt', bevel=R_MID, f0=BUTT - 12, f1=BUTT + 1, cu=0,
         pts=[(DECK_HW - 1, 122.5), (HALF - 1, BELT[1]), (HALF - 1, BELT[0]), (KEEL_HW - 0.5, 4), (KEEL_HW - 3, 0.5),
              (-(KEEL_HW - 3), 0.5), (-(KEEL_HW - 0.5), 4), (-(HALF - 1), BELT[0]), (-(HALF - 1), BELT[1]), (-(DECK_HW - 1), 122.5)]),
]
# ---------------------------------------------------------------- Lauf, Mündungsbremse
P += [
    cyl('barrel', 'Lauf', 'Barrel', 'barrel', 'metal', 'Schwerer Lauf; vor der Stirn frei und kanneliert', 'im Rumpf verschraubt',
        'f', (BORE, 0), *BARREL, 9.5, segs=32, smooth=True,
        cuts=[cut_box(530, 740, BORE - 1.6, BORE + 1.6, 4, x=sx * 9.5) for sx in (1, -1)]
        + [cut_box(530, 740, BORE + 8.3, BORE + 11, 3.2), cut_box(530, 740, BORE - 11, BORE - 8.3, 3.2)]),
    cyl('muzzle', 'Mündungsbremse', 'Muzzle brake', 'barrel', 'anodized', 'Bremse mit zwei Kammern; Socket_Muzzle vorn',
        'auf das Laufende geschraubt (lösbar)', 'f', (BORE, 0), *BRAKE, 15.5, r_in=6.0, segs=40, bevel=R_SMALL, iface='BMZ-15', smooth=True,
        cuts=[cut_box(BRAKE[0] + 12, BRAKE[0] + 24, BORE - 8, BORE + 8, 40), cut_box(BRAKE[0] + 34, BRAKE[0] + 46, BORE - 8, BORE + 8, 40)]),
    cyl('muzzle_crown', 'Mündungskrone', 'Muzzle crown', 'barrel', 'trim', 'Blanke Stirnkante', 'vorn an der Bremse',
        'f', (BORE, 0), BRAKE[1] - 1, BRAKE[1] + 2, 14.5, r_in=6.5, segs=40, bevel=0.5, smooth=True),
]
# ---------------------------------------------------------------- Griff, Magazin, Schienen, Zielfernrohr Z3
P += grip_v21(top=GRIP_TOP)
P += [
    box('mag_well', 'Schachtlippe', 'Magazine well lip', 'receiver', 'trim', 'Blanke Einführkante des Magazinkragens',
        'unten am Kragen', MAG[0] - 5, MAG[0] + MAG[1] + 5, 29.5, 31.6, 2 * lower_x(31) + 1, bevel=0.6, iface='BMW-R',
        cuts=[cut_box(MAG[0] - 0.5, MAG[0] + MAG[1] + 0.5, 20, 40, 25)]),
    cyl('mag_release', 'Magazinhalter', 'Magazine release', 'grip_controls', 'accent', 'Löst das Magazin', 'Druckknopf links am Kragen',
        'x', (MAG[0] - 9, 38), lower_x(38) - 1, lower_x(38) + 3, 4.2, segs=20,
        move=dict(kind='translate', pivot=(MAG[0] - 9, 38, lower_x(38)), vector_mm=(0, 0, -2.5), event='reload',
                  expect=((MAG[0] - 9, 38, lower_x(38) + 3), (0, 0, -1)))),
]
for p in rifle_mag(MAG[0], MAG[2], depth=MAG[1], length=66, tilt=0, w=24, curve=0):
    if p['id'] == 'magazine':
        p.update(func='Kastenmagazin (5); entnehmbar', mat='graphite')   # Runde 3: Creme nur über der Gratlinie
    if p['id'] == 'magazine_base':
        p['mat'] = 'anodized'
    if p['id'] == 'magazine_round':
        p['mat'] = 'brass'
    P.append(p)
P += [dict(p, mat='anodized', attach='auf dem Wangenkamm hinter dem Augenpunkt (fest)') for p in rail(*SEAT_F, COMB)]
P += [dict(p, id='rail_front', de='Schiene vorn', en='Front rail', mat='anodized', attach='auf dem Deck unter dem Objektiv (fest)')
      for p in rail(*FOOT_F, DECK)]
_scope, SIGHT_ANCHORS = lang(F_OBJ, DECK + 8, CU, seat_u=COMB + 8)
P += _scope
PARTS = P

# ---------------------------------------------------------------- Anker, Weltpunkte, Aktionen
_sup = ((PYLON[0] + PYLON[1]) / 2 + 2, 36, 0)
ANCHORS = {
    'Socket_Hand': dict(at=(0, 0, 0), part='grip', note='Haupthand, auf der Griffachse (V: BGM-1)'),
    'Socket_SupportHand': dict(at=_sup, part='pylon_pad', note='Mitte des Pylons (Griffpolster)'),
    'Socket_Muzzle': dict(at=(BRAKE[1] + 2, BORE, 0), part='muzzle_crown', note='Stirn der Mündungskrone auf der Laufachse'),
    'Socket_MagWell': dict(at=(MAG[0] + MAG[1] / 2, 31, 0), part='mag_well', note='Einrastpunkt Magazin (Schnittstelle BMW-R)'),
    'Socket_Bolt': dict(at=(KNOB[0], KNOB[1], 40), part='bolt_knob', note='Griffpunkt Kammerknopf links (Stützhand repetiert, wie BASIC-09)'),
}
ANCHORS.update(SIGHT_ANCHORS)
EJECT = dict(at=((PORT[0] + PORT[1]) / 2, BORE + 4, -HALF), dir=(0.15, 0.6, -1.0), case='rifle',
             src='A: Auswurffenster rechts in der Oberschale beim Zurückziehen des Verschlusses (Stängel links), Hülse nach rechts, etwas hoch')
EGO_GRIPS = {
    'grip':    dict(contact=(-3, -6, -16.5), palm=(0.15, 0.0, 1.0), fingers=(1.0, -0.06, 0.0), fingers_pose='trigger',
                    src='V: Griff BGM-1 wie die Familie'),
    'support': dict(contact=(_sup[0], 30, lower_x(30) + 1.5), palm=(0.15, 0.0, -1.0), fingers=(1.0, -0.12, 0.0), fingers_pose='foregrip',
                    finger_map=dict(open='foregrip_open'), src='A: links am Pylon, Faust um den Pylon wie um einen Vordergriff'),
    'mag':     dict(part='magazine', contact=(MAG[0] + 8, -10, 12.5), palm=(0.0, 0.0, -1.0), fingers=(1.0, 0.2, 0.0), fingers_pose='mag_hold',
                    src='A: links am Kastenmagazin, Hand greift von unten hinten (wie BASIC-09)'),
    'charge':  dict(part='bolt_knob', contact=(KNOB[0], KNOB[1], 47), palm=(0.0, 0.0, -1.0), fingers=(0.45, 0.9, 0.0),
                    fingers_pose='pinch', src='A: am Kammerknopf links (Socket_Bolt), die Stützhand hebt, zieht und schiebt den Stängel'),
}
POINTS = collect(EJECT, EGO_GRIPS, dict(eject='upper', grip='grip', support='pylon_pad'))
EGO_LIVE = dict(trigger='trigger', bolt='', port='', fill=['level_fluid'])
ACTIONS = {
    'fire_cycle': dict(de='Schuss und Repetieren', frames=40, step=1, keys={
        'trigger': [(0, 0), (2, 1), (6, 0)], 'bolt_handle': [(0, 0), (10, 0), (15, 1), (27, 1), (32, 0)],
        'bolt': [(0, 0), (15, 0), (20, 1), (22, 1), (27, 0)]},
        events=[(2, 'shot'), (15, 'unlock'), (20, 'eject'), (27, 'chamber'), (32, 'ready')], view=(0.85, -0.2, 0.5)),
    'reload_empty': dict(de='Nachladen aus leerem Zustand', frames=90, keys={
        'magazine': [(0, 0), (16, 1), (34, 1), (50, 0)], 'bolt_handle': [(0, 0), (56, 0), (61, 1), (73, 1), (78, 0)],
        'bolt': [(0, 0), (61, 0), (66, 1), (68, 1), (73, 0)]},
        events=[(16, 'mag_out'), (50, 'mag_seated'), (73, 'chamber'), (80, 'ready')], view=(0.85, -0.2, 0.5)),
}
EXPLODE = {'sight': (0, 130, 0), 'ammo': (30, -140, 0), 'stock': (-120, 0, 0), 'barrel': (200, 0, 0), 'support': (60, -80, 0),
           'grip_controls': (-10, -80, 0), 'mechanism': (0, 0, 90), 'receiver': (0, 0, 0)}
HERO = (0.55, -0.72, 0.32)   # A: Produktbild von links vorn – Libelle, Kammerstängel und Pylon zur Kamera
