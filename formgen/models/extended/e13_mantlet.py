"""EXTENDED-13 „Mantlet“ – eigenständiger Sci-Fi-Granatwerfer der BASIC-Familie (Formgen v2 0.23 „Breacher“).

Eigenes Modell im BALLON-Kit-Vokabular (reines Python, kein bpy). Keine Teile oder Umbauten von BASIC-13: aus `basic.common` kommen nur
genormte Familienschnittstellen (Griffmodul BGM-1, Visier W1 „D-Linse“ auf Schiene BRI-22, Ladehebel-Form, Schraubenköpfe) und Hilfen
(`cut_box`, `mirror`). Geladen über `formgen.extended`, gerendert mit BALLONs unverändertem `tools/blender_build.main`
(`tools/extended_render.py`).

Formsprache (Stilhandbuch BALLON §3; Auswahl und Skizzen: docs/extended.md)
- Leitmerkmal Panzerhaube: Über dem Verschluss wölbt sich eine schwere Creme-Haube wie ein Helm. Hinten steigt sie aus dem Kolben,
  oben sitzt das Visier in einer Gasse durch die Wölbung, vorn kragt sie als Schirm über die Stirn (Blende), aus der der dicke Lauf
  tritt. Die Wölbung nimmt den Bogenschuss auf; ein Bogenstreifen auf den Flanken folgt ihr.
- Silhouette: kurz und gedrungen (0,65 m); der Kolben setzt die Haube als drei Creme-Schalen fort (Runde 12), Kuppel über einem großen Kastenmagazin vor dem Griff, kurzer dicker Lauf.
- Querschnitt: U – zwei Haubenflanken beiderseits der Visiergasse mit blanken Gassenkanten; Lauf rund Ø 54.
- Negativraum: die Visiergasse, ein 34 mm breiter Kanal durch die Wölbung vom Visiersitz bis zum Schirm, durch den das Visier blickt;
  dazu der Schatten unter dem Schirm über dem Lauf.
- Blickfang (genau einer): die Ladeanzeige links an der Haube, ein Leuchtfenster in Geschossform (Spitzbogen nach vorn); sie leuchtet, wenn
  eine Granate in der Kammer liegt.
- Zweiton: die Creme-Haube ist die einzige helle Masse über einem Graphit-Fahrgestell (Unteres Gehäuse, Magazin, Lauf, Kolben).
- Schichten: Schirm 34 mm über der Stirn, Gassenboden 1,6 mm über dem Gassengrund, Blendenkragen 3,5 mm um den Lauf, Paneele in
  Mulden, Magazinboden 3 mm breiter als das Magazin.
- Grafik: der Bogenstreifen beidseitig (einziges Grafikelement); eine Schrift rechts hinten an der Haube.
- Front mehrstufig: gefaster Mündungsring mit Krone → dicker Lauf über dem Handschutzkiel → Blendenkragen → Stirn → Schirm darüber.
- Ergonomie: Griff BGM-1 (Socket_Hand 0/0), Stützhand am Handschutzkiel unter dem Lauf, Magazinhalter links vorn am Magazinschacht,
  Ladehebel links an der Haube; Akzent-Bedienfunktionen: Magazinhalter, Ladehebel (2).

Herkunft der Zahlen: V = Vorgabe (Familie/Schnittstelle, BASIC-13 Pilot v2.1 bzw. `basic.common`), A = Annahme (Entwurf 0.23),
G = gemessen; Zahlen ohne Kennung sind A (Entwurf 0.23, an den Renders gesichtet).
Maße mm; f nach vorn, u nach oben, x nach links; Socket_Hand = (0, 0, 0).
"""
import math

from basic.common import (part, prof, box, cyl, cut_box, screws, mirror, rail, charging_handle, grip_v21, d_linse,
                          R_BODY, R_MID, R_SMALL, R_FINE)
from basic.variant import collect

META = dict(id='EXTENDED-13', num='E13', sheet_id='EA13', type='grenade_launcher', type_de='Granatwerfer', type_en='Grenade Launcher',
            family='BASIC', name='Mantlet', nick='Panzerhaube', ammo='heavy', fire='semi_auto',
            reference_length_m=0.648, reference_length_source='G: Hülle des Datensatzes 0.23 (BASIC-13 0,67 m gemessen als Rahmen, V)',
            inspired_by='BASIC-13 Familie; Formgen v1 als Haltung (eine mutige Gesamtarchitektur)',
            summary='Halbautomatischer Granatwerfer mit Panzerhaube über dem Verschluss, Kastenmagazin und dickem Lauf aus der Blende '
                    '(EXTENDED-Reihe).')
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

GRIP_TOP = 40            # V: Griffoberkante wie BASIC-13
BORE = 102               # A: Laufachse (BASIC-13 112, V)
BAR_R = 27.0             # A: Lauf Ø 54 (BASIC-13 Ø 60, V); Runde 5: schlanker, damit die Haube ihn an der Stirn fasst
CH_R = 21.5              # V: Bohrung Ø 43 (40-mm-Granate, BASIC-13 CH_R)
HALF = 32.0              # A: halbe Haubenbreite (64 mm; BASIC-13 Gehäuse 48, V)
SPLIT = 70               # A: Unterkante der Haube hinten / Fuge zum Unteren Gehäuse
H0, H1 = -100, 224       # A: Haube hinten / Stirn unten (die Stirn ist 10 mm zurückgeneigt; Runde 4: 20 mm weiter vorn, Magazin vor dem Bügel)
APEX = (30.0, 176.0)     # A: Scheitel der Haubenflanken (f, u) auf Höhe der Visierlinie; die Visiergasse hält die Sicht frei
REAR_U = 124             # A: Haube hinten auf Kammhöhe; dort setzt die Kolbenschale bündig an (Runde 12)
BROW = (248.0, 150.0)    # A: Schirmspitze (Runde 3: Haube kragt über die Stirn vor wie ein Helmschirm; Runde 7: Scheitel vor, Schirm 10 mm tiefer)
BROW_LOW = 138           # A: Unterkante der Schirmstirn (Runde 9: Schirm 12 mm stark an der Spitze, 22 mm an der Stirn, Fase 8 mm)
BROW_UNDER = 137         # A: Unterseite des Schirms über dem Blendenkragen (u 132,5)
FACE_TOP = (214.0, 146.0)  # A: Stirn oben unter dem Schirm (14 mm über dem Blendenkragen)
CHIN = 56                # A: Unterkante der Stirn (Blende reicht unter den Lauf)
RAIL_U = 150             # A: Schienenoberkante in der Visiergasse; Visierlinie 176 = 74 mm über der Laufachse (Vertrag 60–80)
GASSE = 17.0             # A: halbe Breite der Visiergasse (34 mm; Glas 26 mm)
SADDLE = (-58, 22)       # A: Sitz des Visiers am hinteren Ende der Gasse (f0, f1)
BARREL = (170, 352)      # A: Lauf f0 (in der Haube) / f1
MUZ = (346, 372)         # A: Mündungsring
GUARD = (240, 330)       # A: Handschutzkiel unter dem Lauf (Stützhand)
MAG = (90, 200, -22)     # A: Magazin f0, f1, Boden u (zwei Granaten übereinander, Ø 42 + Wand); 7 mm vor dem Abzugsbügel (Runde 4)
MAG_W = 52               # A: Magazinbreite
PORT = (88, 150, 82, 116)   # A: Auswurffenster rechts (Hülse 40 mm)
PORT_SLIDE = 64          # A: Weg des Auswurfschiebers nach vorn (Fenster 62 mm lang); Richter R5: öffnet vor dem Auswurf
LAMP = (34, 86, 98)      # A: Ladeanzeige f0, Spitze f1, Mitte u (Geschossform)
STOCK_W = (54.0, 50.0, 46.0)  # A: Breite der Kolbenschalen (Runde 12); die Haube verjüngt sich hinten auf 56 mm


def hood_top(f):
    """Oberkante der Haube (Helm): zwei Viertelellipsen um den Scheitel; vorn fällt sie senkrecht in die Schirmspitze."""
    if f <= APEX[0]:
        a, b, u0 = APEX[0] - H0, APEX[1] - REAR_U, REAR_U
    else:
        a, b, u0 = BROW[0] - APEX[0], APEX[1] - BROW[1], BROW[1]
    return u0 + b * math.sqrt(max(0.0, 1 - ((f - APEX[0]) / a) ** 2))


def hood_curve(f0, f1, du=0.0, n=24):
    return [(f0 + (f1 - f0) * i / n, hood_top(f0 + (f1 - f0) * i / n) + du) for i in range(n + 1)]


_FT = BROW[0]
# Runde 9 (Koordination: der Schirm wirkte wie ein aufgelegtes Blech): der Schirm wächst mit einer Kehle aus der Stirn, hat 12–22 mm
# Materialstärke, eine Nase vorn, eine Fase unten und gerundete Ecken in der Draufsicht.
HOOD = ([(H0, SPLIT), (MAG[0] - 6, SPLIT), (MAG[0] - 6, 64), (MAG[1] + 8, 64), (MAG[1] + 20, CHIN), (H1, CHIN), FACE_TOP,
         (FACE_TOP[0] + 3, BROW_UNDER + 4), (FACE_TOP[0] + 10, BROW_UNDER), (BROW[0] - 12, BROW_UNDER), (BROW[0] - 2, BROW_LOW),
         (BROW[0] + 2, BROW[1] - 4)] + hood_curve(BROW[0], H0, n=40))
BROW_R = 14.0            # A: Eckradius des Schirms in der Draufsicht
GASSE_FLOOR = 160        # A: Boden der Gasse vor dem Visiersitz (Glasunterkante 163); der Schirm (u 156) bleibt ganz


def ogive(f0, f1, uc, h):
    """Geschossform: hinten gerade, vorn Spitzbogen (Seitenprofil)."""
    r = h / 2
    pts = [(f0, uc - r), (f0 + (f1 - f0) * 0.45, uc - r)]
    for i in range(1, 9):
        t = i / 8
        pts.append((f0 + (f1 - f0) * (0.45 + 0.55 * math.sin(t * math.pi / 2)), uc - r * math.cos(t * math.pi / 2)))
    for i in range(7, 0, -1):
        t = i / 8
        pts.append((f0 + (f1 - f0) * (0.45 + 0.55 * math.sin(t * math.pi / 2)), uc + r * math.cos(t * math.pi / 2)))
    return pts + [(f0 + (f1 - f0) * 0.45, uc + r), (f0, uc + r)]


def offset(pts, d):
    """Polygon grob um d aufweiten (Mittelpunkt-Skalierung je Achse; genügt für Rahmen und Mulden konvexer Formen)."""
    fs, us = [p[0] for p in pts], [p[1] for p in pts]
    cf, cu = (min(fs) + max(fs)) / 2, (min(us) + max(us)) / 2
    sf, su = (max(fs) - min(fs)) / 2, (max(us) - min(us)) / 2
    return [(cf + (f - cf) * (sf + d) / sf, cu + (u - cu) * (su + d) / su) for f, u in pts]


_lamp = ogive(LAMP[0], LAMP[1], LAMP[2], 16)
P = []
# ---------------------------------------------------------------- Panzerhaube, Kamm, Unteres Gehäuse, Mechanik
P += [
    prof('hood', 'Panzerhaube', 'Mantlet hood', 'receiver', 'shell',
         'Schwere Haube über Verschluss und Kammer; Stirn als Blende um den Lauf, oben der Visiersattel',
         'Grundkörper; mit dem Unteren Gehäuse über zwei Querbolzen (fest)', HOOD, 2 * HALF, bevel=R_MID,
         cuts=[cut_box(*PORT, 24, x=-HALF),                                                          # Auswurffenster rechts
               dict(shape='prof', pts=offset(_lamp, 3.5), w=6.0, x=HALF + 0.6),                      # Mulde der Ladeanzeige
               cut_box(-90, -30, 80, 104, 3.0, x=HALF + 0.6), cut_box(-90, -30, 80, 104, 3.0, x=-HALF - 0.6),   # Paneelmulden
               cut_box(SADDLE[0], SADDLE[1], RAIL_U - 8.6, 220, 2 * GASSE),                              # Visiersitz
               cut_box(SADDLE[1] - 1, BROW[0] + 3, GASSE_FLOOR, 220, 2 * GASSE),                       # Visiergasse
               cut_box(-84, 6, 104.5, 119.5, 6.0, x=HALF)]                                           # Nut des Ladehebels (Runde 9)
         + [dict(shape='xprof', f0=FACE_TOP[0] - 14, f1=BROW[0] + 4, cu=0,                            # Fase unter den Schirmkanten
                 pts=[(sx * (HALF + 1), 124), (sx * (HALF + 1), BROW_UNDER + 7), (sx * (HALF - 7), 124)][::sx]) for sx in (1, -1)]
         + [dict(shape='plan', pts=[(BROW[0] - BROW_R, sx * (HALF + 1))]
                 + [(BROW[0] - BROW_R + BROW_R * math.sin(math.radians(a)), sx * (HALF - BROW_R + BROW_R * math.cos(math.radians(a))))
                    for a in range(0, 91, 15)] + [(BROW[0] + 4, sx * (HALF - BROW_R)), (BROW[0] + 4, sx * (HALF + 1))],
                 u0=BROW_UNDER - 2, u1=180) for sx in (1, -1)]
         + [dict(shape='plan', pts=[(H0 - 1, sx * (STOCK_W[0] / 2 + 1)), (H0 + 50, sx * (HALF + 0.5)), (H0 + 50, sx * (HALF + 4)),
                                    (H0 - 1, sx * (HALF + 4))], u0=SPLIT - 1, u1=200) for sx in (1, -1)]   # hinten verjüngt (Runde 12)
         + [dict(shape='xprof', f0=H0 - 1, f1=H1 + 2, cu=0, pts=[(sx * (HALF - 3), 50), (sx * (HALF + 2), 50), (sx * (HALF + 2), 80),
                                                                  (sx * (HALF + 0.5), 80)][::sx]) for sx in (1, -1)]),   # Unterkante eingezogen
    box('gasse_floor', 'Gassenboden', 'Sight channel floor', 'receiver', 'anodized', 'Boden der Visiergasse; trägt die Schiene',
        'im Visiersitz verschraubt', SADDLE[0] + 1, SADDLE[1] - 1, RAIL_U - 9.6, RAIL_U - 8.0, 2 * GASSE - 0.4, bevel=R_FINE),
    part('gasse_edges', 'Gassenkanten', 'Channel edges', 'receiver', 'multi', 'trim', 'Blanke Kanten der Visiergasse',
         'oben auf die Gassenwände geklebt', bevel=0.3,
         items=[dict(shape='prof', pts=hood_curve(SADDLE[0] + 2, 222, -1.2) + hood_curve(222, SADDLE[0] + 2, 0.6), w=3.0,   # R1: ohne Umkehr
                     x=sx * (GASSE + 1.5)) for sx in (1, -1)]),
    prof('lower', 'Unteres Gehäuse', 'Lower receiver', 'receiver', 'graphite', 'Griffmodul, Abzugsgruppe, Magazinschacht',
         'unter der Haube, Fuge 1 mm', [(H0 + 8, SPLIT - 1), (MAG[0] - 7, SPLIT - 1), (MAG[0] - 7, 63), (MAG[1] + 7, 63),
                                       (MAG[1] + 7, 44), (MAG[0] - 7, 44), (MAG[0] - 7, GRIP_TOP), (-62, GRIP_TOP), (H0 + 8, 64)],
         2 * HALF - 4, bevel=R_BODY, cuts=[dict(shape='xprof', f0=H0, f1=MAG[1] + 8, cu=0,
                                               pts=[(sx * (HALF - 3.5), SPLIT - 4), (sx * (HALF + 2), SPLIT - 4), (sx * (HALF + 2), 30),
                                                    (sx * (HALF - 9), 30)][::sx]) for sx in (1, -1)]),   # Runde 12: Flanken eingezogen
    prof('mag_well', 'Magazinschacht', 'Magazine well', 'ammo', 'graphite', 'Führt das Kastenmagazin; Lippe vorn',
         'unter der Haube angeformt', [(MAG[0] - 7, 64), (MAG[1] + 7, 64), (MAG[1] + 7, 34), (MAG[1] + 2, 30), (MAG[0] - 7, 30)],
         MAG_W + 8, bevel=R_MID, cuts=[cut_box(MAG[0] - 0.5, MAG[1] + 0.5, 20, 64.5, MAG_W + 0.8)]
         + [dict(shape='plan', pts=[(MAG[1] - 4, sx * (MAG_W / 2 + 5)), (MAG[1] + 8, sx * (MAG_W / 2 - 4)), (MAG[1] + 8, sx * 40),
                                    (MAG[1] - 4, sx * 40)], u0=20, u1=70) for sx in (1, -1)]),   # Runde 12: Lippe vorn gefast
    box('side_panel_l', 'Seitenpaneel links', 'Side panel left', 'receiver', 'anodized', 'Wartungsdeckel über dem Schloss',
        'in die Mulde geschraubt (4 Schrauben)', -88, -32, 82, 102, 1.2, bevel=R_FINE, x=HALF - 0.8),
    box('side_panel_r', 'Seitenpaneel rechts', 'Side panel right', 'receiver', 'anodized', 'Wartungsdeckel über dem Schloss',
        'in die Mulde geschraubt (4 Schrauben)', -88, -32, 82, 102, 1.2, bevel=R_FINE, x=-HALF + 0.8),
    part('panel_screws', 'Paneelschrauben', 'Panel screws', 'receiver', 'multi', 'trim', 'Halten die Seitenpaneele', 'in den Paneelen',
         bevel=0.2, items=mirror(screws([(-84, 86), (-84, 98), (-36, 86), (-36, 98)], HALF - 0.2, r=1.6, h=0.8))),
    part('takedown_pins', 'Querbolzen', 'Takedown pins', 'receiver', 'multi', 'metal', 'Verbinden Haube und Unteres Gehäuse',
         'quer durch das Untere Gehäuse (lösbar)', bevel=0.4, items=mirror(screws([(H0 + 16, 62), (MAG[1] + 2, 66)], HALF - 1, r=3.6, h=1.0))),
    cyl('mouth_ring', 'Blendenkragen', 'Mantlet collar', 'barrel', 'anodized', 'Fasst den Lauf in der Haubenstirn',
        'in die Stirn geschraubt', 'f', (BORE, 0), FACE_TOP[0] - 4, H1 + 3, BAR_R + 3.5, r_in=BAR_R - 0.5, segs=48, bevel=0.8, smooth=True),
    box('bolt', 'Verschluss', 'Bolt', 'mechanism', 'metal', 'Lädt die Granate aus dem Magazin; läuft beim Schuss zurück',
        'in der Haube geführt', PORT[0] - 50, PORT[1] - 2, 86, 112, 40, bevel=R_SMALL,
        move=dict(kind='translate', pivot=((PORT[0] + PORT[1]) / 2, BORE, 0), vector_mm=(-56, 0, 0), event='fire',
                  expect=((PORT[1] - 2, BORE, -20), (-1, 0, 0)))),
    part('lamp_frame', 'Anzeigenrahmen', 'Lamp frame', 'receiver', 'prof', 'trim', 'Blanker Rahmen der Ladeanzeige',
         'in die Mulde links geschraubt', bevel=0.5, pts=offset(_lamp, 3.0), w=1.6, x=HALF - 1.6,
         cuts=[dict(shape='prof', pts=offset(_lamp, 0.4), w=6, x=HALF - 1.6)]),
    prof('lamp_glass', 'Anzeigenglas', 'Lamp glass', 'receiver', 'glass', 'Schützt die Ladeanzeige', 'im Rahmen',
         offset(_lamp, 0.4), 0.6, bevel=0, x=HALF - 1.9),
    part('chamber_lamp', 'Ladeanzeige', 'Chamber lamp', 'receiver', 'prof', 'energy',
         'Leuchtet in Geschossform, wenn eine Granate in der Kammer liegt; Blickfang links', 'unter dem Glas in der Mulde', bevel=0.3,
         pts=_lamp, w=1.2, x=HALF - 2.8, move=dict(kind='glow', pivot=None, event='fire', max=4.0)),
    cyl('mag_release', 'Magazinhalter', 'Magazine release', 'grip_controls', 'accent', 'Gibt das Magazin frei (Stützhand)',
        'Druckknopf links vorn am Magazinschacht', 'x', (MAG[1] - 6, 52), MAG_W / 2 + 3.5, MAG_W / 2 + 7, 4.5, segs=20,
        move=dict(kind='translate', pivot=(MAG[1] - 6, 52, MAG_W / 2 + 4), vector_mm=(0, 0, -2.5), event='reload',
                  expect=((MAG[1] - 6, 52, MAG_W / 2 + 7), (0, 0, -1)))),
    part('arc_stripe', 'Bogenstreifen', 'Arc stripe', 'receiver', 'multi', 'accent', 'Lackierter Streifen parallel zur Wölbung (einziges Grafikelement)',
         'lackiert, beidseitig auf den Haubenflanken', bevel=0,
         items=[dict(shape='prof', pts=hood_curve(-74, 160, -14) + hood_curve(160, -74, -19), w=0.3, x=sx * (HALF + 0.15)) for sx in (1, -1)]),
    part('text_r', 'Schriftzug', 'Lettering', 'receiver', 'text', 'anodized', 'Kennung „BASIC  EX-13“ (einzige Schrift)',
         'aufgedruckt (dunkel auf Creme)', bevel=0, text='BASIC  EX-13', size=5.0, f=-24, u=86, x=-HALF - 0.05, side=-1, depth=0.12),
]
P += [
    prof('port_cover', 'Auswurfschieber', 'Ejection port slide', 'mechanism', 'anodized', 'Deckt das Auswurffenster ab; gleitet zum Schuss nach vorn',
         'in zwei Leisten außen am Fenster geführt', [(PORT[0] - 1, PORT[2] - 1), (PORT[1] + 1, PORT[2] - 1), (PORT[1] + 1, PORT[3] + 1),
                                                      (PORT[0] - 1, PORT[3] + 1)], 1.6, bevel=R_FINE, x=-HALF - 0.9,
         move=dict(kind='translate', pivot=((PORT[0] + PORT[1]) / 2, PORT[2], -HALF - 0.9), vector_mm=(PORT_SLIDE, 0, 0), event='fire',
                   expect=((PORT[1] + 1, (PORT[2] + PORT[3]) / 2, -HALF - 0.9), (1, 0, 0)))),
    part('port_rails', 'Schieberleisten', 'Slide rails', 'mechanism', 'multi', 'trim', 'Führen den Auswurfschieber', 'über und unter dem Fenster',
         bevel=0.3, items=[dict(shape='box', f0=PORT[0] - 3, f1=PORT[1] + PORT_SLIDE + 3, u0=u, u1=u + 3, w=2.2, x=-HALF - 1.1)
                           for u in (PORT[2] - 4, PORT[3] + 1)]),
]
P += charging_handle(-26, 112, x=HALF + 0.5, travel=56)
P[-1]['cuts'] = []
P += [dict(p, mat='dark_metal', attach='auf dem Gassenboden (fest)') for p in rail(SADDLE[0] + 4, SADDLE[1] - 4, RAIL_U - 8)]
# Visier W1 „D-Linse“ (Familienbaustein für Granatwerfer, wie BASIC-13)
_sight, SIGHT_ANCHORS = d_linse(SADDLE[0] + 6, RAIL_U, weapon_type='grenade_launcher')
P += _sight
# ---------------------------------------------------------------- Kastenmagazin mit zwei Granaten
P += [
    prof('magazine', 'Kastenmagazin', 'Box magazine', 'ammo', 'graphite', 'Zwei 40-mm-Granaten übereinander; austauschbar',
         'im Magazinschacht (lösbar)', [(MAG[0], 66), (MAG[1], 66)] + [(MAG[1] - 34 + 34 * math.cos(math.radians(a)),
                                                                          MAG[2] + 34 + 34 * math.sin(math.radians(a))) for a in range(0, -91, -15)]
         + [(MAG[0], MAG[2])], MAG_W, bevel=R_BODY,
         cuts=[dict(shape='plan', pts=[(MAG[1] - 14, sx * (MAG_W / 2 + 1)), (MAG[1] + 1, sx * (MAG_W / 2 - 10)), (MAG[1] + 1, sx * 40),
                                       (MAG[1] - 14, sx * 40)], u0=MAG[2] - 1, u1=67) for sx in (1, -1)]   # Vorderkante gefast (Runde 12)
         + [dict(shape='plan', pts=[(MAG[0] - 1, sx * (MAG_W / 2 - 4)), (MAG[0] + 6, sx * (MAG_W / 2 + 1)), (MAG[0] - 1, sx * (MAG_W / 2 + 1))],
                 u0=MAG[2] - 1, u1=67) for sx in (1, -1)]
         + [dict(shape='xprof', f0=MAG[0] - 1, f1=MAG[1] + 1, cu=0, pts=[(sx * (MAG_W / 2 - 5), MAG[2] - 1), (sx * (MAG_W / 2 + 1), MAG[2] - 1),
                                                                     (sx * (MAG_W / 2 + 1), MAG[2] + 24)][::sx]) for sx in (1, -1)],
         move=dict(kind='translate', pivot=((MAG[0] + MAG[1]) / 2, MAG[2], 0), vector_mm=(0, -120, 0), event='reload', removable=True,
                   expect=(((MAG[0] + MAG[1]) / 2, MAG[2], 0), (0, -1, 0)))),
    prof('mag_floor', 'Magazinboden', 'Magazine floor plate', 'ammo', 'rubber', 'Griffiger Boden; schützt beim Aufsetzen',
         'unten auf das Magazin geschraubt', [(MAG[0] - 1.5, MAG[2] + 6), (MAG[1] - 36, MAG[2] + 6), (MAG[1] - 34, MAG[2] - 4),
                                             (MAG[0] - 1.5, MAG[2] - 4)], MAG_W + 3, bevel=R_SMALL, parent_part='magazine'),
    part('mag_plates', 'Magazinplatten', 'Magazine side plates', 'ammo', 'multi', 'anodized', 'Verstärken die Magazinwände',
         'seitlich auf das Magazin geschraubt', bevel=R_FINE, parent_part='magazine',
         items=[dict(shape='box', f0=MAG[0] + 10, f1=MAG[1] - 44, u0=MAG[2] + 26, u1=52, w=1.2, x=sx * (MAG_W / 2 + 0.4)) for sx in (1, -1)]),
    part('mag_screws', 'Magazinschrauben', 'Magazine screws', 'ammo', 'multi', 'trim', 'Halten die Magazinplatten', 'in den Platten',
         bevel=0.2, parent_part='magazine',
         items=mirror(screws([(MAG[0] + 15, MAG[2] + 31), (MAG[0] + 15, 47), (MAG[1] - 49, MAG[2] + 31), (MAG[1] - 49, 47)],
                             MAG_W / 2 + 1.0, r=1.6, h=0.8))),
    cyl('grenade', 'Granate', 'Grenade', 'ammo', 'dark_metal', 'Oberste Granate (an den Magazinlippen sichtbar)', 'im Magazin oben',
        'f', (BORE - 54, 0), MAG[0] + 34, MAG[0] + 96, 20.0, r1=12.0, segs=24, bevel=R_SMALL, smooth=True, parent_part='magazine'),
]
# ---------------------------------------------------------------- Lauf, Griffmanschette, Mündung
P += [
    cyl('barrel', 'Abschusslauf', 'Launch tube', 'barrel', 'graphite', 'Kurzer dicker Lauf; tritt aus der Blende',
        'in der Haube verschraubt', 'f', (BORE, 0), BARREL[0], BARREL[1], BAR_R, r_in=CH_R, segs=48, bevel=R_SMALL, smooth=True),
    prof('forend', 'Handschutzkiel', 'Handguard keel', 'support', 'graphite', 'Flacher Kiel unter dem Lauf für die Stützhand',
         'unter den Lauf geschraubt', [(GUARD[0], BORE - BAR_R + 4), (GUARD[1], BORE - BAR_R + 4), (GUARD[1], BORE - BAR_R - 12),
                                     (GUARD[1] - 6, BORE - BAR_R - 18), (GUARD[0] + 10, BORE - BAR_R - 14), (GUARD[0], BORE - BAR_R - 6)], 36,
         bevel=R_BODY, cuts=[dict(shape='xprof', f0=GUARD[0] - 1, f1=GUARD[1] + 1, cu=0,
                                  pts=[(sx * 10, BORE - BAR_R - 20), (sx * 19, BORE - BAR_R - 20), (sx * 19, BORE - BAR_R - 2)][::sx])
                             for sx in (1, -1)]),   # Runde 12: Kielquerschnitt, unten verjüngt
    prof('forend_pad', 'Griffpolster', 'Grip pad', 'support', 'rubber', 'Rutschfeste Unterseite des Kiels', 'unten auf den Kiel geklebt',
         [(GUARD[0] + 14, BORE - BAR_R - 12), (GUARD[1] - 12, BORE - BAR_R - 14.5), (GUARD[1] - 12, BORE - BAR_R - 18),
          (GUARD[0] + 14, BORE - BAR_R - 16)], 28, bevel=R_SMALL),
    part('forend_screws', 'Kielschrauben', 'Keel screws', 'support', 'multi', 'trim', 'Halten den Handschutzkiel am Lauf', 'seitlich am Kiel',
         bevel=0.2, items=mirror(screws([(GUARD[0] + 8, BORE - BAR_R - 2), (GUARD[1] - 8, BORE - BAR_R - 2)], 18.2, r=1.8, h=0.8))),
    cyl('muzzle', 'Mündungsring', 'Muzzle ring', 'barrel', 'anodized', 'Verstärkt die Mündung; vorn gefast',
        'auf das Laufende geschraubt', 'f', (BORE, 0), MUZ[0], MUZ[1] - 1, BAR_R + 5, r_in=CH_R, segs=48, bevel=R_MID, smooth=True),
    cyl('muzzle_crown', 'Mündungskrone', 'Muzzle crown', 'barrel', 'trim', 'Blanke Stirnkante um die Bohrung', 'vorn an der Mündungsstufe',
        'f', (BORE, 0), MUZ[1] - 2, MUZ[1] + 2, BAR_R - 2, r_in=CH_R + 0.5, segs=48, bevel=0.5, smooth=True),
]
# ---------------------------------------------------------------- Griff, Kolben
P += grip_v21(top=GRIP_TOP)
_S0, L_STOCK = H0, 162      # A: Kolbenlänge bis zur Kappe
_SB = _S0 - L_STOCK
_COMB = 124                 # A: Kammhöhe (Visierlinie 176 − 52 mm Wangenabstand)
# Runde 12 (Koordination: die Lamellen wirkten wie Klötze auf der alten Platte, ein angesetztes Teil): Der Kolben setzt die Haube fort.
# Drei Creme-Schalen im Querschnitt der Haube – gerundete Schultern, Kammrinne als Fortsetzung der Visiergasse, eingezogene Unterkante –
# werden nach hinten je 3 mm niedriger und 4 mm schmaler, jede steckt 6 mm in der vorigen; kein Kern darunter.
LAMES = [(_S0 + 8, _S0 - 52, _COMB, STOCK_W[0]), (_S0 - 46, _S0 - 106, _COMB - 3, STOCK_W[1]), (_S0 - 100, _SB + 2, _COMB - 6, STOCK_W[2])]
_UNDER = [(_S0 + 9, 66.0), (_SB + 26, 30.0), (_SB, 32.0)]   # A: Unterlinie des Kolbens: schlanker Hals unter der Haube, fällt zur Schulter (r13)


def under(f, lift=0.0):
    (fa, ua), (fb, ub) = _UNDER[0], _UNDER[1]
    return ua + (ub - ua) * (fa - f) / (fa - fb) + lift


def shell_section(w, top, bottom):
    """Querschnitt einer Kolbenschale (x, u): Schultern r 10, Kammrinne 14 mm breit und 2,5 mm tief, Unterkante 4 mm eingezogen."""
    hw, r, n = w / 2, 10.0, 6
    pts = [(hw - 4 - 6 + 6 * math.cos(math.radians(270 + 90 * i / n)), bottom + 6 + 6 * math.sin(math.radians(270 + 90 * i / n))) for i in range(n + 1)]
    pts += [(hw, top - 30)]
    pts += [(hw - r + r * math.cos(math.radians(90 * i / n)), top - r + r * math.sin(math.radians(90 * i / n))) for i in range(n + 1)]
    pts += [(7, top), (5, top - 2.5), (-5, top - 2.5), (-7, top)]
    pts += [(-hw + r + r * math.cos(math.radians(90 + 90 * i / n)), top - r + r * math.sin(math.radians(90 + 90 * i / n))) for i in range(n + 1)]
    pts += [(-hw, top - 30)]
    pts += [(-hw + 4 + 6 + 6 * math.cos(math.radians(180 + 90 * i / n)), bottom + 6 + 6 * math.sin(math.radians(180 + 90 * i / n))) for i in range(n + 1)]
    return pts


def shell(pid, de, en, k, func):
    f0, f1, top, w = LAMES[k]
    rear = [(f1 - 1, top + 5), (f1 + 10, top + 5), (f1, top - 12)]          # Hinterkante oben schräg (Schindel)
    return part(pid, de, en, 'stock', 'xprof', 'shell', func, 'steckt 6 mm in der vorigen Schale bzw. in der Haube', bevel=R_MID,
                f0=f1, f1=f0, cu=0, pts=shell_section(w, top, under(f1, 2 * k) - 1),
                cuts=[dict(shape='prof', pts=[(f1 - 1, 10), (f0 + 1, 10), (f0 + 1, under(f0, 2 * k)), (f1 - 1, under(f1, 2 * k))], w=w + 4),
                      dict(shape='prof', pts=rear, w=w + 4)])


P += [
    shell('stock', 'Kolbenschale', 'Stock shell', 0, 'Erste Schale des Kolbens; trägt die Wange, wächst aus der Haube'),
    shell('stock_seg2', 'Kolbenschale Mitte', 'Stock shell middle', 1, 'Zweite Schale; 3 mm tiefer, 4 mm schmaler'),
    shell('stock_seg3', 'Kolbenschale hinten', 'Stock shell rear', 2, 'Dritte Schale; trägt die Schaftkappe'),
    prof('butt_pad', 'Kolbenkappe', 'Butt pad', 'stock', 'rubber', 'Schaftkappe, gerundet und 4 mm zurückgeneigt', 'auf die hintere Schale gesteckt',
         [(_SB + 3, 31), (_SB + 3, _COMB - 8), (_SB - 6, _COMB - 10), (_SB - 12, _COMB - 20), (_SB - 10, 40), (_SB - 4, 31)],
         STOCK_W[2] - 4, bevel=R_BODY),
]
PARTS = P

# ---------------------------------------------------------------- Anker, Weltpunkte, Aktionen
_sup = ((GUARD[0] + GUARD[1]) / 2, BORE - BAR_R - 17, 0)
ANCHORS = {
    'Socket_Hand': dict(at=(0, 0, 0), part='grip', note='Haupthand, auf der Griffachse (V: BGM-1)'),
    'Socket_SupportHand': dict(at=_sup, part='forend', note='Unterseite des Handschutzkiels'),
    'Socket_Muzzle': dict(at=(MUZ[1] + 2, BORE, 0), part='muzzle_crown', note='Stirn der Mündungskrone auf der Laufachse'),
    'Socket_LoadingGate': dict(at=((MAG[0] + MAG[1]) / 2, MAG[2], 0), part='magazine', note='Magazinboden; Magazin von unten einsetzen'),
}
ANCHORS.update(SIGHT_ANCHORS)
EJECT = dict(at=((PORT[0] + PORT[1]) / 2, BORE, -HALF), dir=(0.1, 0.25, -1.0), case='grenade_40',
             src='A: Auswurffenster rechts in der Haube; die leere Hülse fällt je Schuss nach rechts (Halbautomat mit Kastenmagazin)')
EGO_GRIPS = {
    'grip':    dict(contact=(-3, -6, -16.5), palm=(0.15, 0.0, 1.0), fingers=(1.0, -0.06, 0.0), fingers_pose='trigger',
                    src='V: Griff BGM-1 wie die Familie'),
    'support': dict(contact=(_sup[0], _sup[1] - 1.5, -2), palm=(0.0, 1.0, -0.25), fingers=(0.08, 0.15, -1.0), fingers_pose='underhand',
                    src='A: unter dem Handschutzkiel des Laufs'),
    'mag':     dict(part='magazine', contact=((MAG[0] + MAG[1]) / 2, 20, MAG_W / 2 + 0.5), palm=(0.0, 0.0, -1.0), fingers=(1.0, 0.2, 0.0),
                    fingers_pose='mag_hold', src='A: links am Kastenmagazin, Hand greift von links unten'),
    'gate':    dict(contact=(MAG[1] - 6, 52, MAG_W / 2 + 7.5), palm=(0.0, 0.0, -1.0), fingers=(0.45, 0.9, 0.0), fingers_pose='pinch',
                    src='A: am Magazinhalter links vorn am Schacht'),
    'charge':  dict(part='charging_handle', contact=(-14, 112, HALF + 5.5), palm=(0.0, 0.0, -1.0), fingers=(0.45, 0.9, 0.0),
                    fingers_pose='pinch', src='A: am Ladehebel links an der Haube'),
}
POINTS = collect(EJECT, EGO_GRIPS, dict(eject='hood', grip='grip', support='forend', gate='mag_release'))
EGO_LIVE = dict(trigger='trigger', bolt='bolt', port='port_cover', fill=['chamber_lamp'])
ACTIONS = {
    'fire': dict(de='Schuss; Verschluss zurück, Hülse aus, nächste Granate aus dem Magazin', frames=18, step=1, keys={
        'trigger': [(0, 0), (2, 1), (6, 0)], 'bolt': [(0, 0), (3, 0), (7, 1), (12, 0)],
        'port_cover': [(0, 0), (3, 0), (5, 1), (13, 1), (16, 0)]}, events=[(2, 'shot'), (7, 'eject')],
        view=(-0.85, -0.25, 0.45)),
    'reload': dict(de='Magazinhalter, Magazin heraus und neu einsetzen, Ladehebel ziehen', frames=90, keys={
        'mag_release': [(0, 0), (4, 1), (10, 1), (14, 0)], 'magazine': [(0, 0), (10, 0), (26, 1), (56, 1), (70, 0)],
        'charging_handle': [(0, 0), (74, 0), (80, 1), (86, 0)]},
        events=[(26, 'mag_out'), (70, 'mag_in'), (86, 'chambered')], view=(0.6, 0.75, 0.45)),
}
EXPLODE = {'sight': (0, 110, 0), 'mechanism': (0, 60, 90), 'barrel': (130, 0, 0), 'ammo': (0, -130, 0), 'support': (130, -40, 0),
           'stock': (-110, 0, 0), 'grip_controls': (-10, -80, 0), 'receiver': (0, 0, 0)}
HERO = (0.55, -0.70, 0.35)   # A: Produktbild von links vorn – Haube mit Ladeanzeige, Blende und Lauf zur Kamera
