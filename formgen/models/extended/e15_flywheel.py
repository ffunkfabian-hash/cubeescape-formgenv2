"""EXTENDED-15 „Flywheel“ – eigenständiges Sci-Fi-Maschinengewehr der BASIC-Familie (Formgen v2 0.22 „Torrent“).

Eigenes Modell im BALLON-Kit-Vokabular (reines Python, kein bpy). Keine Teile oder Umbauten von BASIC-15: aus `basic.common` kommen nur
genormte Familienschnittstellen (Griffmodul BGM-1, Holovisier H6 „Achteck“ L auf Schiene BRI-22, Einhängung BAB-1, Feuerwahl-/Ladehebel-Form,
Schraubenköpfe) und Hilfen (`cut_box`, `mirror`). Geladen über `formgen.extended`, gerendert mit BALLONs unverändertem
`tools/blender_build.main` (`tools/extended_render.py`).

Formsprache (Stilhandbuch BALLON §3; Auswahl und Skizzen: docs/extended.md)
- Leitmerkmal Schwungrad: Die Munition sitzt in einer großen Gurttrommel (Ø 156, quer zur Laufachse) unter dem Gehäuse zwischen Griff und
  Stützhand. Fünf Speichen auf der Creme-Stirnscheibe und eine offene Nabe machen sie zum Rad; der Kreis ist in der Seite die
  beherrschende Form.
- Silhouette: lang (0,98 m) und schwer, gerade Oberlinie vom Kolben bis zum Mantelträger, darunter das Rad, vorn der gerippte Mantel.
- Querschnitt: Kreuz. Der Kühlmantel trägt vier Längsrippen (oben, unten, links, rechts) um einen runden Kern; das Gehäuse dahinter ist ein
  breiter Kasten (56 mm).
- Negativraum: die offene Nabe (Ø 36) quer durch die Trommel; die Luft zwischen den Mantelrippen.
- Blickfang (genau einer): die Leuchtspeiche links an der Trommel, eine leuchtende Speiche hinter Glas im blanken Rahmen; sie zeigt
  den Füllstand. Die vier übrigen Speichen sind dunkle Rippen.
- Zweiton: Creme oben (Gehäuse, Deckel, Mantelträger, Kolben, Rippen, Trommelscheiben) über Graphit (Unteres Gehäuse, Handschutz,
  Trommelkranz, Mantelkern).
- Schichten: Zuführdeckel 12 mm über dem Gehäuse, Seitenpaneele in Mulden, Trommelscheiben 2 mm über dem Kranz, Speichen 2 mm über der
  Scheibe, Mantelträger 8 mm unter dem Gehäuse.
- Grafik: ein Band quer über den Kolben (beidseitig); eine Schrift rechts am Gehäuse vorn.
- Front mehrstufig: gefaste Rippenenden, eloxierter Mantelkragen, runde Bremse mit Kreuzports, blanke Krone.
- Ergonomie: Griff BGM-1 (Socket_Hand 0/0), Stützhand unter dem Mantelträger vor dem Rad, Trommelgriff vorn an der Trommel, Ladehebel
  links hinten, Deckelriegel hinten am Deckel; Akzent-Bedienfunktionen: Ladehebel, Deckelriegel, Feuerwahlhebel (3).

Herkunft der Zahlen: V = Vorgabe (Familie/Schnittstelle, BASIC-15 Pilot v2.1 bzw. `basic.common`), A = Annahme (Entwurf 0.22),
G = gemessen; Zahlen ohne Kennung sind A (Entwurf 0.22, an den Renders gesichtet).
Maße mm; f nach vorn, u nach oben, x nach links; Socket_Hand = (0, 0, 0).
"""
import math

from basic.common import (part, prof, box, cyl, cut_box, screws, mirror, rail, selector, charging_handle, grip_v21, achteck,
                          R_MID, R_SMALL, R_FINE)
from basic.variant import collect

META = dict(id='EXTENDED-15', num='E15', sheet_id='EA15', type='machine_gun', type_de='Maschinengewehr', type_en='Machine Gun',
            family='BASIC', name='Flywheel', nick='Schwungrad', ammo='heavy', fire='full_auto_belt',
            reference_length_m=0.978, reference_length_source='G: Hülle des Datensatzes 0.22 (BASIC-15 0,96 m gemessen als Rahmen, V)',
            inspired_by='BASIC-15 Familie; Formgen v1 als Haltung (eine mutige Gesamtarchitektur)',
            summary='Maschinengewehr mit großer Gurttrommel als Schwungrad unter dem Gehäuse und geripptem Kühlmantel (EXTENDED-Reihe).')
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

GRIP_TOP = 40          # V: Oberkante Griff BGM-1
BORE = 100             # A: Laufachse (BASIC-15 106, V)
TOP = 128              # A: Oberkante Gehäuse; Deckel bis 140, Schiene bis 148, Visierlinie 174 = 74 mm über der Laufachse (Vertrag 60–80)
SPLIT = 76             # A: Fuge Gehäuse (Creme) / Unteres Gehäuse (Graphit)
HALF = 28.0            # A: halbe Gehäusebreite (56 mm; BASIC-15 52, V)
REC0, REC1 = -150, 236  # A: Gehäuse hinten / vorn
CARRIER = (236, 318, 84, 120)   # A: Mantelträger f0, f1, u0, u1 (8 mm unter dem Gehäuse)
COVER = (-56, 150, TOP, TOP + 12)
COVER_PIV = (150, TOP + 4)
DRUM_C = (160.0, -28.0)  # A: Trommelmitte (f, u); vorn 8 mm Luft zum Abzugsbügel, oben auf der Einhängeplatte
DRUM_R = 78.0            # A: Trommelradius (Ø 156); Inhalt etwa wie der Kasten von BASIC-15
DRUM_X = (-24.0, 36.0)   # A: Trommelbreite 60 mm, 6 mm nach links versetzt (Gurt läuft links ins Gehäuse)
DRUM_XC = sum(DRUM_X) / 2
HUB_R = 18.0             # A: offene Nabe Ø 36 (Negativraum)
FEED = (112, 164, 94, 116)   # A: Zuführfenster links
PORT = (96, 140, 84, 104)    # A: Auswurffenster rechts
LINK_PORT = (106, 132, 108, 116)
JACKET = (318, 560)      # A: Kühlmantel f (Runde 2: 288 → 242 mm, r1 las sich das MG als langer dünner Stab)
CORE_R = 22.0            # A: Mantelkern (Ø 44; Runde 2 von Ø 38)
FIN = (40.0, 10.0)       # A: Rippen bis r 40, 10 mm dick (Nutzer Welle 1: nicht zu zart; Runde 2 von r 36 × 8)
MUZ = (572, 634)         # A: Bremse
SPOKES = [45 + 72 * i for i in range(5)]   # A: Speichenwinkel (Grad, 0 = vorn, gegen den Uhrzeigersinn in der linken Ansicht nach oben)
GLOW = SPOKES[0]         # A: die Leuchtspeiche zeigt nach vorn oben (kameranah im Hero)


def polar(r, deg):
    a = math.radians(deg)
    return (DRUM_C[0] + r * math.cos(a), DRUM_C[1] + r * math.sin(a))


def spoke(deg, r0, r1, w):
    """Speiche als Seitenprofil (Rechteck entlang des Radius)."""
    a = math.radians(deg)
    n = (-math.sin(a) * w / 2, math.cos(a) * w / 2)
    p0, p1 = polar(r0, deg), polar(r1, deg)
    return [(p0[0] + n[0], p0[1] + n[1]), (p1[0] + n[0], p1[1] + n[1]), (p1[0] - n[0], p1[1] - n[1]), (p0[0] - n[0], p0[1] - n[1])]


FACE_X = {1: DRUM_X[1] + 2, -1: DRUM_X[0] - 2}   # Außenseite der Trommelscheiben links/rechts


def drum_cyl(a0, a1, r, **kw):
    return dict(shape='cyl', axis='x', c=DRUM_C, a0=a0, a1=a1, r=r, segs=48, **kw)


P = []
# ---------------------------------------------------------------- Gehäuse, Deckel, Mechanik
P += [
    prof('receiver', 'Gehäuse', 'Receiver', 'receiver', 'shell', 'Breiter Tragkörper; Zuführung links, Auswurf rechts',
         'Grundkörper; mit dem Unteren Gehäuse über zwei Querbolzen (fest)',
         [(REC0, SPLIT), (REC1, SPLIT), (REC1, TOP - 6), (REC1 - 6, TOP), (REC0 + 10, TOP), (REC0, TOP - 10)], 2 * HALF, bevel=R_MID,
         cuts=[cut_box(*FEED[:2], *FEED[2:], 12, x=HALF), cut_box(*PORT[:2], *PORT[2:], 12, x=-HALF),
               cut_box(*LINK_PORT[:2], *LINK_PORT[2:], 12, x=-HALF),
               cut_box(-132, -80, 110, 118, 10, x=HALF),                                                 # Ladehebel-Nut links
               cut_box(-136, -50, 84, 104, 3.0, x=HALF + 0.6), cut_box(-136, -50, 84, 104, 3.0, x=-HALF - 0.6),   # Paneel-Mulden
               cut_box(FEED[0] - 2, FEED[1] + 2, TOP - 6, TOP + 2, 2 * HALF - 8)]),                     # Öffnung unter dem Deckel
    prof('lower', 'Unteres Gehäuse', 'Lower receiver', 'receiver', 'graphite', 'Griffmodul, Abzugsgruppe, Trommelaufnahme',
         'unter dem Gehäuse, Fuge 1 mm',
         [(REC0, 60), (-70, GRIP_TOP), (48, GRIP_TOP), (62, 54), (REC1 - 4, 54), (REC1, 62), (REC1, SPLIT - 1), (REC0, SPLIT - 1)],
         2 * HALF - 4, bevel=R_MID),
    box('side_panel_l', 'Seitenpaneel links', 'Side panel left', 'receiver', 'anodized', 'Wartungsdeckel über dem Puffer',
        'in die Mulde geschraubt (4 Schrauben)', -134, -52, 86, 102, 1.2, bevel=R_FINE, x=HALF - 0.8),
    box('side_panel_r', 'Seitenpaneel rechts', 'Side panel right', 'receiver', 'anodized', 'Wartungsdeckel über dem Puffer',
        'in die Mulde geschraubt (4 Schrauben)', -134, -52, 86, 102, 1.2, bevel=R_FINE, x=-HALF + 0.8),
    part('panel_screws', 'Paneelschrauben', 'Panel screws', 'receiver', 'multi', 'trim', 'Halten die Seitenpaneele', 'in den Paneelen',
         bevel=0.2, items=mirror(screws([(-129, 90), (-129, 98), (-57, 90), (-57, 98)], HALF - 0.2, r=1.6, h=0.8))),
    part('takedown_pins', 'Querbolzen', 'Takedown pins', 'receiver', 'multi', 'metal', 'Verbinden Gehäuse und Unteres Gehäuse',
         'quer durch das Gehäuse (lösbar)', bevel=0.4, items=mirror(screws([(-136, 68), (222, 68)], HALF - 2, r=3.6, h=1.0))),
    prof('feed_cover', 'Zuführdeckel', 'Feed cover', 'mechanism', 'shell', 'Hält den Gurt in der Zuführung; trägt das Visier',
         'Scharnier vorn, öffnet hinten nach oben', [(COVER[0], COVER[2]), (COVER[1], COVER[2]), (COVER[1], COVER[3] - 4),
                                                     (COVER[1] - 8, COVER[3]), (COVER[0] + 8, COVER[3]), (COVER[0], COVER[3] - 5)], 2 * HALF - 8,
         bevel=R_SMALL,
         move=dict(kind='rotate', pivot=(COVER_PIV[0], COVER_PIV[1], 0), axis='x', range_deg=(0, -62), event='reload',
                   expect=((COVER[0] + 8, COVER[3], 0), (0, 1, 0)))),
    cyl('cover_hinge', 'Deckelscharnier', 'Cover hinge', 'mechanism', 'trim', 'Drehachse des Deckels', 'vorn quer durch das Gehäuse',
        'x', COVER_PIV, -HALF - 0.8, HALF + 0.8, 4.0, segs=20, bevel=0.4),
    prof('cover_latch', 'Deckelriegel', 'Cover latch', 'mechanism', 'accent', 'Verriegelt den Deckel; zum Öffnen nach vorn drücken',
         'hinten am Deckel', [(COVER[0] - 7, COVER[2] + 1), (COVER[0] + 1, COVER[2] + 1), (COVER[0] + 1, COVER[3] - 3),
                              (COVER[0] - 4, COVER[3] - 3)], 30, bevel=R_FINE, parent_part='feed_cover',
         move=dict(kind='translate', pivot=(COVER[0] - 3, COVER[2] + 6, 0), vector_mm=(4, 0, 0), event='reload')),
    box('feed_tray', 'Zuführschale', 'Feed tray', 'ammo', 'dark_metal', 'Führt den Gurt quer ins Gehäuse', 'unter dem Deckel im Gehäuse',
        FEED[0] - 2, FEED[1] + 2, TOP - 8, TOP - 6, 2 * HALF - 8, bevel=R_FINE),
    box('bolt', 'Verschluss', 'Bolt', 'mechanism', 'metal', 'Lädt und verriegelt; läuft beim Schuss zurück', 'im Gehäuse geführt',
        PORT[0] - 40, PORT[1] - 2, 88, 100, 30, bevel=R_SMALL,
        move=dict(kind='translate', pivot=(PORT[0], 94, 0), vector_mm=(-40, 0, 0), event='fire',
                  expect=((PORT[1] - 2, 94, 0), (-1, 0, 0)))),
    prof('port_cover', 'Auswurfklappe', 'Ejection port cover', 'mechanism', 'anodized', 'Deckt das Auswurffenster ab',
         'Scharnier an der Unterkante', [(PORT[0], PORT[2]), (PORT[1], PORT[2]), (PORT[1], PORT[3]), (PORT[0], PORT[3])], 1.6,
         bevel=R_FINE, x=-HALF - 0.6,
         move=dict(kind='rotate', pivot=((PORT[0] + PORT[1]) / 2, PORT[2], -HALF - 1.4), axis='f', range_deg=(0, 75), event='fire',
                   expect=(((PORT[0] + PORT[1]) / 2, PORT[3], -HALF - 1.4), (0, 0, -1)))),
    part('text_r', 'Schriftzug', 'Lettering', 'receiver', 'text', 'decal', 'Kennung „BASIC  EX-15“ (einzige Schrift)',
         'aufgedruckt', bevel=0, text='BASIC  EX-15', size=5.0, f=150, u=88, x=-HALF - 0.05, side=-1, depth=0.12),
]
P += charging_handle(-124, 114, x=HALF + 0.5, travel=60)
P += [dict(p, mat='anodized', parent_part='feed_cover') for p in rail(-40, 70, COVER[3])]
P[-1]['cuts'] = [cut_box(-34 + 12 * i, -28 + 12 * i, COVER[3] + 4, COVER[3] + 9, 30) for i in range(9)]
_sight, SIGHT_ANCHORS = achteck(-34, COVER[3] + 8, 'L', weapon_type='machine_gun')
for p in _sight:
    if p['id'] == 'sight_mount':
        p['parent_part'] = 'feed_cover'
P += _sight
# ---------------------------------------------------------------- Gurttrommel (Schwungrad, BAB-1)
_dc = DRUM_C
P += [
    box('drum_hanger', 'Einhängeplatte', 'Drum hanger', 'receiver', 'trim', 'Blanke Platte, an der die Trommel eingehängt wird',
        'unter dem Unteren Gehäuse', _dc[0] - 40, _dc[0] + 40, 47, 54.5, 44, bevel=0.6, x=DRUM_XC, iface='BAB-1'),
    part('ammo_box', 'Gurttrommel', 'Belt drum', 'ammo', 'cyl', 'graphite',
         'Trommel mit aufgerolltem Gurt; austauschbar; Kranz der Trommel', 'unter dem Gehäuse eingehängt (lösbar)', bevel=R_MID,
         iface='BAB-1', axis='x', c=_dc, a0=DRUM_X[0], a1=DRUM_X[1], r=DRUM_R, segs=48,
         cuts=[drum_cyl(DRUM_X[0] - 1, DRUM_X[1] + 1, HUB_R)],
         move=dict(kind='translate', pivot=(_dc[0], _dc[1], DRUM_XC), vector_mm=(0, -110, 60), event='reload', removable=True,
                   expect=((_dc[0], _dc[1] - DRUM_R, DRUM_XC), (0, -1, 0)))),
] + [
    part(f'drum_face_{s}', f'Trommelscheibe {de}', f'Drum face {en}', 'ammo', 'cyl', 'shell',
         'Creme-Stirnscheibe der Trommel; trägt die Speichen', f'{de} auf den Kranz geschraubt, 2 mm vorstehend', bevel=R_SMALL,
         parent_part='ammo_box', axis='x', c=_dc, a0=a0, a1=a1, r=DRUM_R - 7, segs=48, cuts=[drum_cyl(min(a0, a1) - 1, max(a0, a1) + 1, HUB_R + 3)])
    for s, de, en, a0, a1 in (('l', 'links', 'left', DRUM_X[1] - 1, DRUM_X[1] + 2), ('r', 'rechts', 'right', DRUM_X[0] - 2, DRUM_X[0] + 1))
] + [
    part('hub_rings', 'Nabenringe', 'Hub rings', 'ammo', 'multi', 'trim', 'Blanke Fassung der offenen Nabe', 'beidseitig in der Nabe',
         bevel=0.4, parent_part='ammo_box',
         items=[dict(drum_cyl(DRUM_X[1] + 1, DRUM_X[1] + 3.5, HUB_R + 4, r_in=HUB_R), segs=32),
                dict(drum_cyl(DRUM_X[0] - 3.5, DRUM_X[0] - 1, HUB_R + 4, r_in=HUB_R), segs=32)]),
    part('hub_sleeve', 'Nabenhülse', 'Hub sleeve', 'ammo', 'cyl', 'dark_metal', 'Innenwand der offenen Nabe', 'durch die Trommel',
         bevel=0.3, parent_part='ammo_box', axis='x', c=_dc, a0=DRUM_X[0] - 0.5, a1=DRUM_X[1] + 0.5, r=HUB_R + 0.6, r_in=HUB_R, segs=32),
    part('spokes', 'Speichen', 'Spokes', 'ammo', 'multi', 'graphite', 'Versteifungsrippen der Scheiben (dunkel)', 'auf die Scheiben gepresst',
         bevel=R_FINE, parent_part='ammo_box',
         items=[dict(shape='prof', pts=spoke(a, HUB_R + 6, DRUM_R - 11, 9), w=2.4, x=FACE_X[sx] + sx * 1.0)
                for a in SPOKES for sx in (1, -1) if not (sx > 0 and a == GLOW)]),
    prof('spoke_frame', 'Speichenrahmen', 'Spoke frame', 'ammo', 'trim', 'Blanker Rahmen der Leuchtspeiche', 'links auf die Scheibe geschraubt',
         spoke(GLOW, HUB_R + 4, DRUM_R - 9, 15), 1.6, bevel=0.5, x=DRUM_X[1] + 2.6, parent_part='ammo_box',
         cuts=[dict(shape='prof', pts=spoke(GLOW, HUB_R + 7, DRUM_R - 12, 9), w=6, x=DRUM_X[1] + 2.6)]),
    prof('spoke_glass', 'Speichenglas', 'Spoke glass', 'ammo', 'glass', 'Schützt die Leuchtspeiche', 'im Rahmen',
         spoke(GLOW, HUB_R + 6.6, DRUM_R - 11.6, 9.6), 0.6, bevel=0, x=DRUM_X[1] + 2.4, parent_part='ammo_box'),
    part('glow_spoke', 'Leuchtspeiche', 'Glow spoke', 'ammo', 'prof', 'energy',
         'Füllstand der Trommel als leuchtende Speiche; Blickfang links', 'unter dem Glas in der Scheibe', bevel=0.3,
         pts=spoke(GLOW, HUB_R + 8, DRUM_R - 13, 6.5), w=1.2, x=DRUM_X[1] + 1.6, parent_part='ammo_box',
         move=dict(kind='glow', pivot=None, event='fire', max=5.0)),
    prof('drum_grip', 'Trommelgriff', 'Drum grip', 'ammo', 'anodized', 'Griffleiste vorn an der Trommel (Trommel ziehen)',
         'vorn am Kranz verschraubt', [(polar(DRUM_R, -20)[0] - 4, polar(DRUM_R, -20)[1]), (polar(DRUM_R + 7, -14)[0], polar(DRUM_R + 7, -14)[1]),
                                       (polar(DRUM_R + 7, 14)[0], polar(DRUM_R + 7, 14)[1]), (polar(DRUM_R, 20)[0] - 4, polar(DRUM_R, 20)[1])],
         24, bevel=R_SMALL, x=DRUM_XC, parent_part='ammo_box'),   # Runde 3: 34 → 24 mm breit, r2 wirkte er wie ein angesetzter Klotz
    prof('feed_neck', 'Zuführhals', 'Feed neck', 'ammo', 'anodized', 'Geschlossener Gurtweg von der Trommel ins Zuführfenster',
         'links zwischen Trommel und Gehäuse verschraubt (Runde 3: unten so schmal wie der Gurtaustritt, oben so breit wie das Fenster)',
         [(DRUM_C[0] - 22, 50), (DRUM_C[0] + 2, 50), (FEED[1] + 4, FEED[2] - 6), (FEED[1] + 4, FEED[3] - 4), (FEED[1] - 4, FEED[3] + 1),
          (FEED[0] + 4, FEED[3] + 1), (FEED[0] - 4, FEED[3] - 4), (FEED[0] - 4, FEED[2] - 6)], 12, bevel=R_SMALL, x=HALF + 5),
    part('neck_screws', 'Halsschrauben', 'Neck screws', 'ammo', 'multi', 'trim', 'Halten den Zuführhals', 'außen am Zuführhals',
         bevel=0.2, items=screws([(FEED[0] + 4, FEED[3] - 6), (FEED[1] - 4, FEED[3] - 6), (DRUM_C[0] - 10, 58)], HALF + 11.2, r=1.7, h=0.8)),
]
# ---------------------------------------------------------------- Mantelträger, Handschutz, Kühlmantel (Kreuz), Mündung
_fin_v = lambda u0, u1: [(JACKET[0], u0), (JACKET[1] - 10, u0), (JACKET[1], u0 + (6 if u0 > BORE else 0)),   # noqa: E731
                         (JACKET[1], u1 - (6 if u0 < BORE else 0)), (JACKET[1] - 10, u1), (JACKET[0], u1)]
_fin_h = lambda sx: [(JACKET[0], sx * (CORE_R - 2)), (JACKET[1] - 10, sx * (CORE_R - 2)), (JACKET[1], sx * (FIN[0] - 6)),   # noqa: E731
                     (JACKET[1], sx * FIN[0]), (JACKET[0], sx * FIN[0])]
P += [
    prof('carrier', 'Mantelträger', 'Jacket carrier', 'support', 'shell', 'Trägt Lauf und Kühlmantel vor dem Gehäuse; 8 mm unter dem Gehäuse',
         'an das Gehäuse geschraubt, Fuge 1 mm', [(CARRIER[0] + 1, CARRIER[2]), (CARRIER[1], CARRIER[2]), (CARRIER[1], CARRIER[3] - 6),
                                                   (CARRIER[1] - 6, CARRIER[3]), (CARRIER[0] + 1, CARRIER[3])], 2 * HALF - 6, bevel=R_MID,
         cuts=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=CARRIER[1] - 10, a1=CARRIER[1] + 1, r=CORE_R + 1, segs=32)]),
    prof('handguard', 'Handschutz', 'Handguard', 'support', 'graphite', 'Griffbereich der Stützhand unter dem Mantelträger vor dem Rad',
         'unter den Mantelträger geschraubt, Fuge 1 mm', [(REC1 + 6, 56), (CARRIER[1] - 4, 56), (CARRIER[1], 64), (CARRIER[1], CARRIER[2] - 1),
                                                          (REC1 + 1, CARRIER[2] - 1), (REC1 + 1, 62)], 2 * HALF - 10, bevel=R_MID),
    prof('handguard_pad', 'Griffpolster', 'Grip pad', 'support', 'rubber', 'Rutschfeste Zone für die Stützhand', 'unten auf den Handschutz geklebt',
         [(REC1 + 14, 52.5), (CARRIER[1] - 10, 52.5), (CARRIER[1] - 10, 58), (REC1 + 14, 58)], 2 * HALF - 16, bevel=R_SMALL),
    part('carrier_screws', 'Trägerschrauben', 'Carrier screws', 'support', 'multi', 'trim', 'Halten Mantelträger und Handschutz', 'seitlich',
         bevel=0.2, items=mirror(screws([(CARRIER[0] + 10, 92), (CARRIER[0] + 10, 112), (CARRIER[1] - 12, 92)], HALF - 3.2, r=1.8, h=0.8))),
    cyl('barrel_nut', 'Laufmutter', 'Barrel nut', 'barrel', 'trim', 'Spannt den Lauf im Mantelträger', 'vorn am Mantelträger',
        'f', (BORE, 0), CARRIER[1] - 2, CARRIER[1] + 6, CORE_R + 5, segs=32, bevel=0.6),
    cyl('jacket_core', 'Mantelkern', 'Jacket core', 'barrel', 'graphite', 'Runder Kern des Kühlmantels um den Lauf',
        'auf die Laufmutter geschraubt', 'f', (BORE, 0), JACKET[0], JACKET[1] + 4, CORE_R, segs=32, bevel=R_SMALL),
    part('jacket_fins', 'Mantelrippen', 'Jacket fins', 'barrel', 'multi', 'shell', 'Hochrippen oben und unten des Kreuzes (Creme); führen Laufwärme ab',
         'auf den Kern geschweißt', bevel=R_SMALL,
         items=[dict(shape='prof', pts=_fin_v(BORE + CORE_R - 2, BORE + FIN[0]), w=FIN[1]),
                dict(shape='prof', pts=_fin_v(BORE - FIN[0], BORE - CORE_R + 2), w=FIN[1])]),
    part('jacket_fins_side', 'Seitenrippen', 'Side fins', 'barrel', 'multi', 'graphite',
         'Waagerechte Rippen des Kreuzes, dunkel gegen die hellen Hochrippen (Runde 2)', 'auf den Kern geschweißt', bevel=R_SMALL,
         items=[dict(shape='plan', pts=_fin_h(sx)[::sx], u0=BORE - FIN[1] / 2, u1=BORE + FIN[1] / 2) for sx in (1, -1)]),
    cyl('jacket_collar', 'Mantelkragen', 'Jacket collar', 'barrel', 'anodized', 'Kragen vor den Rippen; zweite Stufe der Front',
        'vorn auf den Kern geschraubt', 'f', (BORE, 0), JACKET[1] + 2, MUZ[0] + 2, 27, segs=32, bevel=R_SMALL),
    cyl('barrel', 'Lauf', 'Barrel', 'barrel', 'metal', 'Führt das Geschoss; im Kern', 'im Gehäuse verschraubt',
        'f', (BORE, 0), 150, MUZ[0] + 4, 10, segs=24, smooth=True),
    cyl('muzzle', 'Mündungsbremse', 'Muzzle brake', 'barrel', 'anodized', 'Runde Bremse mit Kreuzports; Socket_Muzzle',
        'auf Laufende geschraubt (lösbar)', 'f', (BORE, 0), MUZ[0], MUZ[1], 18, r_in=6, segs=24, bevel=R_SMALL, iface='BMZ-15',
        cuts=[cut_box(MUZ[0] + 16 + 14 * i, MUZ[0] + 25 + 14 * i, BORE - 5, BORE + 5, 50) for i in range(3)]
        + [cut_box(MUZ[0] + 16 + 14 * i, MUZ[0] + 25 + 14 * i, BORE - 25, BORE + 25, 10) for i in range(3)]),
    cyl('muzzle_crown', 'Mündungskrone', 'Muzzle crown', 'barrel', 'trim', 'Blanke Stirnkante', 'vorn an der Bremse',
        'f', (BORE, 0), MUZ[1] - 2, MUZ[1] + 4, 16.5, r_in=6.5, segs=24, bevel=0.6),
]
# ---------------------------------------------------------------- Griff, Bedienung, Kolben
P += grip_v21(top=GRIP_TOP)
P += selector(-26, 62, x=HALF - 1.5)
P += [dict(p, id='selector_r', de='Feuerwahlhebel rechts', en='Fire selector right', x=-HALF + 1.5) for p in selector(-26, 62)]
_S0 = REC0   # Kolbenwurzel
L_STOCK = 180          # A: Kolbenlänge (Runde 2 von 206; mit Kappe 190)
P += [
    prof('stock', 'Kolben', 'Stock', 'stock', 'shell', 'Schwerer Vollkolben, Oberteil; Anlage an Wange und Schulter',
         'mit zwei Bolzen an das Gehäuse (fest)', [(_S0 + 1, 78), (_S0 - L_STOCK, 72), (_S0 - L_STOCK, 118), (_S0 - L_STOCK + 8, 125),
                                                     (_S0 + 1, 125)], 2 * HALF - 14, bevel=R_MID),
    prof('stock_keel', 'Kolbenkiel', 'Stock keel', 'stock', 'graphite', 'Unterteil des Kolbens; Anlage der Stützhand unter dem Kolben',
         'unter das Kolbenoberteil geschraubt, Fuge 1 mm (Runde 2: ersetzt die Seitenpaneele, die wie Fenster wirkten)',
         [(_S0 + 1, 60), (_S0 - 110, 48), (_S0 - L_STOCK, 46), (_S0 - L_STOCK, 71), (_S0 + 1, 77)], 2 * HALF - 16, bevel=R_MID),
    prof('butt_pad', 'Kolbenkappe', 'Butt pad', 'stock', 'rubber', 'Rutschfeste Anlage an der Schulter', 'auf das Kolbenende gesteckt',
         [(_S0 - L_STOCK + 1, 48), (_S0 - L_STOCK + 1, 120), (_S0 - L_STOCK - 6, 118), (_S0 - L_STOCK - 10, 110), (_S0 - L_STOCK - 10, 56),
          (_S0 - L_STOCK - 6, 50)], 2 * HALF - 12, bevel=R_MID,
         cuts=[cut_box(_S0 - L_STOCK - 13, _S0 - L_STOCK - 6, 60 + 10 * i, 64 + 10 * i, 60) for i in range(5)]),
    part('stock_band', 'Kolbenband', 'Stock band', 'stock', 'multi', 'accent', 'Lackiertes Querband (einziges Grafikelement)',
         'lackiert, beidseitig vorn am Kolben', bevel=0,
         items=[dict(shape='prof', pts=[(_S0 - 34, 96), (_S0 - 22, 96), (_S0 - 22, 122), (_S0 - 34, 122)], w=0.3, x=sx * (HALF - 6.85))
                for sx in (1, -1)]),
    part('stock_bolts', 'Kolbenbolzen', 'Stock bolts', 'stock', 'multi', 'trim', 'Halten den Kolben am Gehäuse', 'quer durch die Kolbenwurzel',
         bevel=0.3, items=mirror(screws([(_S0 - 12, 112), (_S0 - 12, 88), (_S0 - 12, 66)], HALF - 7.2, r=2.4, h=1.0))),
]
PARTS = P

# ---------------------------------------------------------------- Anker, Weltpunkte, Aktionen
_drum_low = (_dc[0], _dc[1] - DRUM_R, DRUM_XC)
ANCHORS = {
    'Socket_Hand': dict(at=(0, 0, 0), part='grip', note='Haupthand, auf der Griffachse (V: BGM-1)'),
    'Socket_SupportHand': dict(at=(278, 52.5, 0), part='handguard_pad', note='Griffpolster unter dem Mantelträger vor dem Rad'),
    'Socket_Muzzle': dict(at=(MUZ[1] + 4, BORE, 0), part='muzzle_crown', note='Stirn der Mündungskrone auf der Laufachse'),
    'Socket_FeedCover': dict(at=(COVER[0] + 8, COVER[3], 0), part='feed_cover', note='Griffpunkt zum Öffnen'),
    'Socket_AmmoBox': dict(at=_drum_low, part='ammo_box', note='Griffpunkt unten am Trommelkranz (Schnittstelle BAB-1)'),
    'Socket_Charge': dict(at=(-112, 114, HALF + 5), part='charging_handle', note='Griffpunkt Ladehebel links (Stützhand)'),
}
ANCHORS.update(SIGHT_ANCHORS)
EJECT = dict(at=((PORT[0] + PORT[1]) / 2, (PORT[2] + PORT[3]) / 2, -HALF), dir=(0.15, -0.3, -1.0), case='rifle',
             src='A: Auswurffenster rechts unter der Klappe port_cover, Hülse nach rechts und etwas nach unten (wie BASIC-15)',
             links=dict(at=((LINK_PORT[0] + LINK_PORT[1]) / 2, (LINK_PORT[2] + LINK_PORT[3]) / 2, -HALF), dir=(0.1, 0.35, -1.0),
                        case='belt_link', src='A: Gliederauswurf rechts über dem Auswurffenster, Glied nach rechts und etwas hoch'))
EGO_GRIPS = {
    'grip':    dict(contact=(-3, -6, -16.5), palm=(0.15, 0.0, 1.0), fingers=(1.0, -0.06, 0.0), fingers_pose='trigger',
                    src='V: Griff BGM-1 wie die Familie'),
    'support': dict(contact=(278, 52.5, -2), palm=(0.0, 1.0, -0.25), fingers=(0.08, 0.15, -1.0), fingers_pose='underhand',
                    src='A: unter dem Griffpolster des Handschutzes vor dem Rad'),
    'mag':     dict(part='ammo_box', contact=(_dc[0] + 20, _dc[1] - 40, DRUM_X[1] + 2.5), palm=(0.0, 0.0, -1.0), fingers=(1.0, 0.2, 0.0),
                    fingers_pose='mag_hold', src='A: links auf der Trommelscheibe unter der Nabe, Hand greift von vorn unten'),
    'charge':  dict(part='charging_handle', contact=(-112, 114, HALF + 5.5), palm=(0.0, 0.0, -1.0), fingers=(0.45, 0.9, 0.0),
                    fingers_pose='pinch', src='A: am Ladehebel links'),
    'cover':   dict(part='feed_cover', contact=(COVER[0] + 12, COVER[3] + 0.5, 12), palm=(0.0, -1.0, 0.0), fingers=(1.0, 0.0, -0.2),
                    fingers_pose='pinch', src='A: hinten auf dem Zuführdeckel am Deckelriegel (Socket_FeedCover)'),
}
POINTS = collect(EJECT, EGO_GRIPS, dict(eject='receiver', links='receiver', grip='grip', support='handguard_pad'))
EGO_LIVE = dict(trigger='trigger', bolt='bolt', port='port_cover', fill=['glow_spoke'])
_shots = [3, 7, 11, 15, 19]
ACTIONS = {
    'fire_auto': dict(de='Dauerfeuer (Verschluss, Auswurfklappe, Leuchtspeiche)', frames=30, step=1, keys={
        'trigger': [(0, 0), (3, 1), (27, 1), (30, 0)], 'port_cover': [(0, 0), (4, 1), (30, 1)],
        'bolt': [(0, 0), (3, 0)] + [k for s in _shots for k in ((s + 2, 1), (s + 4, 0))]},
        events=[(s, 'shot') for s in _shots], view=(-0.85, -0.25, 0.45)),
    'reload': dict(de='Deckel auf, Trommel tauschen, Gurt einlegen, Deckel zu', frames=150, keys={
        'feed_cover': [(0, 0), (16, 1), (118, 1), (134, 0)], 'ammo_box': [(0, 0), (24, 0), (44, 1), (76, 1), (100, 0)]},
        events=[(16, 'cover_open'), (44, 'box_out'), (100, 'box_in'), (112, 'belt_seated'), (134, 'cover_closed')],
        view=(0.75, -0.35, 0.55)),
}
EXPLODE = {'sight': (0, 120, 0), 'mechanism': (0, 70, 0), 'ammo': (0, -160, 40), 'stock': (-110, 0, 0), 'barrel': (160, 0, 0),
           'support': (60, -50, 0), 'grip_controls': (-10, -80, 0), 'receiver': (0, 0, 0)}
HERO = (0.55, -0.70, 0.35)   # A: Produktbild von links vorn – Rad mit Leuchtspeiche, Mantelrippen und Front zur Kamera
