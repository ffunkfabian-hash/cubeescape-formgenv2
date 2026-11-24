"""EXTENDED-06 „Wishbone“ – eigenständige Sci-Fi-Maschinenpistole der BASIC-Familie (Formgen v2 0.22 „Torrent“).

Eigenes Modell im BALLON-Kit-Vokabular (reines Python, kein bpy). Keine Teile oder Umbauten von BASIC-06: aus `basic.common` kommen nur
genormte Familienschnittstellen (Griffmodul BGM-1, Holovisier H2 „Pille“ auf Schiene BRI-22, Gewehrmagazin an BMW-R, Feuerwahlhebel,
Ladehebel-Form, Schraubenköpfe) und Hilfen (`rot`, `cut_box`, `mirror`). Geladen über `formgen.extended`, gerendert mit BALLONs
unverändertem `tools/blender_build.main` (`tools/extended_render.py`).

Formsprache (Stilhandbuch BALLON §3; Auswahl und Skizzen: docs/extended.md)
- Leitmerkmal Gabelbein: Der Magazinschacht ist zugleich Vordergriff und steht um RAKE = 24° nach vorn gespreizt, der Griff BGM-1 um 15°
  nach hinten. Griff und Schacht bilden unter dem kurzen Gehäuse ein Λ. Die Stirn liegt parallel zum Schacht (unten weiter vorn, „Kinnstirn“).
  Kurz und wendig: 0,415 m, der Kolben ist im Gehäuse angeformt und verjüngt sich hinter einer Wangenstufe.
- Querschnitt: T. Das Creme-Deck (48 mm) kragt je Seite 6 mm über den Graphit-Rumpf (36 mm), die Unterkante des Überstands ist gefast;
  die Schattenkante läuft als Linie von der Kolbenkappe bis zur Stirn.
- Negativraum: der Gabelzwickel, ein trapezförmiger Abzugsraum zwischen Griff, Schacht, Rumpf und Abzugsbügel, der vom Griff bis an den
  Schacht reicht; darunter öffnet sich das Λ.
- Blickfang (genau einer): das Λ-Fenster links am Deck, eine dreieckige Munitionsanzeige hinter Glas im blanken Rahmen. Seine
  Hinterkante steht 15° wie der Griff, die Vorderkante 24° wie der Schacht: das Fenster wiederholt das Gabelbein.
- Zweiton: Creme-Deck über die ganze Länge (Kolben bis Stirn) über dem Graphit-Rumpf, Graphit-Schacht; Teilung etwa 55:45 in der Seite,
  oben und im Hero-Winkel deutlich mehr Creme.
- Schichten: Deck 6 mm über dem Rumpf (T), Rückenleiste 3 mm über den Deckflanken, Wangenstufe 12 mm, Seitenpaneele in Mulden am
  Kolben, Stirnplatte 2 mm vor der Stirn, Griffpolster auf dem Schacht.
- Grafik: ein Längsstreifen hinten am Deck (beidseitig); eine Schrift rechts vorn am Deck.
- Front mehrstufig: Kinnstirn mit eloxierter Stirnplatte, blanke Laufbuchse, runder Kompensator mit Seitenports, blanke Krone.
- Ergonomie: Griff BGM-1 (Socket_Hand 0/0), Stützhand am Schacht (Griffpolster vorn und hinten), Ladehebel links am Deck, Magazinhalter
  links am Schacht über dem Polster; Akzent-Bedienfunktionen: Ladehebel, Magazinhalter, Feuerwahlhebel (3).

Herkunft der Zahlen: V = Vorgabe (Familie/Schnittstelle, BASIC-06 Pilot v2.1 bzw. `basic.common`), A = Annahme (Entwurf 0.22),
G = gemessen; Zahlen ohne Kennung sind A (Entwurf 0.22, an den Renders gesichtet).
Maße mm; f nach vorn, u nach oben, x nach links; Socket_Hand = (0, 0, 0).
"""
import math

from basic.common import (part, prof, box, cyl, rot, cut_box, screws, mirror, rail, selector, charging_handle, grip_v21,
                          holo_pille, rifle_mag, R_MID, R_SMALL, R_FINE)
from basic.variant import collect

META = dict(id='EXTENDED-06', num='E06', sheet_id='EA06', type='submachine_gun', type_de='Maschinenpistole', type_en='Submachine Gun',
            family='BASIC', name='Wishbone', nick='Gabelbein', ammo='primary', fire='full_auto',
            reference_length_m=0.415, reference_length_source='G: Hülle des Datensatzes 0.22 (kompakt; BASIC-06 0,547 m gemessen als Rahmen, V)',
            inspired_by='BASIC-06 Familie; Formgen v1 als Haltung (eine mutige Gesamtarchitektur)',
            summary='Kompakte Maschinenpistole als Gabelbein: gespreizter Magazinschacht als Vordergriff, T-Deck und Kinnstirn '
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

GRIP_TOP = 40        # V: Oberkante Griff BGM-1 wie BASIC-06
BORE = 78            # A: Laufachse (BASIC-06 82, V); tiefer, damit das Deck hoch bleibt und die Visierlinie im Vertrag
SPLIT = 78           # A: Fuge Rumpf/Deck (Rumpf bis 77, Deck ab 78)
TOP = 116            # A: Oberkante Deck = Unterkante Schiene; Visierlinie TOP + 8 + 26 = 150, 72 mm über der Laufachse (Vertrag 60–80)
LOW = 40             # V: Unterkante Rumpf auf der Griffoberkante
HALF_D = 24.0        # A: halbe Deckbreite (48 mm; Runde 2: 46 → 48, der T-Überstand las sich zu schwach)
HALF_L = 18.0        # A: halbe Rumpfbreite (36 mm); Überstand des Decks 6 mm je Seite (T)
RAKE = 24.0          # A: Spreizung des Schachts nach vorn (Leitmerkmal); Griff BGM-1 15° nach hinten (V)
T = math.tan(math.radians(RAKE))
TG = math.tan(math.radians(15))
BUTT = -190          # A: Kolbenende (Kappe bis −199)
CHEEK = (-88, 104)   # A (Runde 2, Runde 4 tiefer): Wangenstufe – hinter f −88 liegt das Deck 12 mm tiefer (Kolbenrücken)
SPINE = (10.0, 3.0)  # A (Runde 4/5): Rückenleiste 20 mm breit, 3 mm auf dem Deck (eigenes Teil; r4 als Schnitt gab Schattierungsfehler)
WELL = (84, 132)     # A: Hinter- und Vorderkante des Schachts auf u = LOW (48 mm waagerecht, 44 mm quer zur Schachtachse)
WELL_LOW = -34       # A: Unterkante Schacht (Länge 74 mm auf der Achse gemessen ≈ 81 mm: eine Hand breit)
FACE0 = 182          # A: Stirn auf u = LOW; die Stirn steigt mit RAKE nach hinten


def rake(f40, u):
    """Linie mit RAKE: Lage f bei u, wenn sie auf u = LOW bei f40 liegt (unten weiter vorn)."""
    return f40 + (LOW - u) * T


def face(u):
    """Kinnstirn: parallel zum Schacht."""
    return rake(FACE0, u)


def para(f40a, f40b, u0, u1):
    """Parallelogramm mit RAKE zwischen den Linien f40a und f40b von u0 bis u1."""
    return [(rake(f40a, u0), u0), (rake(f40b, u0), u0), (rake(f40b, u1), u1), (rake(f40a, u1), u1)]


# Λ-Fenster (Blickfang): Dreieck mit Spitze oben; Hinterkante 15° (Griff), Vorderkante 24° (Schacht). A: Grundlinie u 86, Spitze u 109.
WIN_APEX = (-14.0, 109.0)    # Runde 4: Grundlinie über der Fase, Spitze so, dass der Rahmen unter der Deckflanke bleibt (r3 stand er 12 mm darüber)
WIN_BASE = 86.0
WIN_CLIP = TOP - SPINE[1] - 0.6   # A: Rahmen und Schacht oben gekappt (stumpfe Spitze), Rand unter der Deckflanke


def tri(d=0.0, apex=WIN_APEX, base=WIN_BASE, clip=None):
    """Dreieck des Λ-Fensters, um d nach außen versetzt (Rahmen d > 0, Glas/Anzeige d < 0); Seiten 15° und 24°; über `clip` gekappt."""
    fa, ua = apex
    kg, kt = math.hypot(1, TG), math.hypot(1, T)   # Normalabstand d je Schräge in f umgerechnet

    def rear(u):
        return fa - (ua - u) * TG - d * kg

    def front(u):
        return fa + (ua - u) * T + d * kt
    u_top = ua + d * (kg + kt) / (TG + T)          # Schnitt der versetzten Schrägen
    b = base - d
    if clip is not None and u_top > clip:
        return [(rear(b), b), (front(b), b), (front(clip), clip), (rear(clip), clip)]
    return [(rear(b), b), (front(b), b), (rear(u_top), u_top)]


P = []
# ---------------------------------------------------------------- Deck (Creme, T-Überstand) und Rumpf (Graphit)
_chamfer = [dict(shape='xprof', pts=[(sx * (HALF_D - 4), SPLIT - 12), (sx * (HALF_D + 20), SPLIT - 12), (sx * (HALF_D + 20), SPLIT + 4),
                                     (sx * HALF_D, SPLIT + 4), (sx * (HALF_D - 4), SPLIT)][::sx], f0=BUTT - 20, f1=FACE0 + 20, cu=0)
            for sx in (1, -1)]   # A: Fase 4 × 4 unter dem Überstand – die Schattenkante des T
_port = (22, 72, 84, 100)     # A: Auswurffenster rechts am Deck (f0, f1, u0, u1)
P += [
    prof('upper', 'Deck', 'Deck', 'receiver', 'shell',
         'Oberer Gehäuseteil von der Kolbenkappe bis zur Stirn; trägt Schiene, Visier und das Λ-Fenster; kragt je Seite 5 mm über den Rumpf',
         'auf dem Rumpf, Fuge 1 mm (zwei Querbolzen)',
         [(BUTT, SPLIT), (face(SPLIT), SPLIT), (face(TOP - SPINE[1]), TOP - SPINE[1]), (CHEEK[0], TOP - SPINE[1]), (CHEEK[0] - 8, CHEEK[1]),
          (BUTT + 10, CHEEK[1]),
          (BUTT, CHEEK[1] - 10)], 2 * HALF_D, bevel=R_MID,
         cuts=_chamfer
         + [cut_box(*_port[:2], *_port[2:], 16, x=-HALF_D)]                                             # Auswurffenster rechts
         + [cut_box(-148, -96, 88, 96, 10, x=HALF_D)]                                                 # Ladehebel-Nut links hinten
         + [dict(shape='prof', pts=tri(2.4, clip=WIN_CLIP - 0.6), w=8, x=HALF_D)]),                                          # Fensterschacht 4 mm tief
    prof('lower', 'Rumpf', 'Lower body', 'receiver', 'graphite',
         'Griffmodul, Abzugsgruppe, Kolbenunterteil und Schachtansatz; schmaler als das Deck (T)', 'unter dem Deck, Fuge 1 mm',
         [(BUTT, 68), (-40, LOW), (face(LOW), LOW), (face(SPLIT - 1), SPLIT - 1), (BUTT, SPLIT - 1)], 2 * HALF_L, bevel=R_MID,
         cuts=[cut_box(-136, -60, 60, 74, 3.0, x=sx * (HALF_L + 0.6)) for sx in (1, -1)]                 # Paneel-Mulden
         + [dict(shape='prof', pts=para(WELL[0] + 6, WELL[1] - 6, LOW - 2, LOW + 18), w=26)]),          # Schachtöffnung oben
    box('side_panel_l', 'Kolbenpaneel links', 'Butt panel left', 'stock', 'anodized', 'Wartungsdeckel über dem Puffer',
        'in die Mulde geschraubt (4 Schrauben)', -134, -62, 62, 72, 1.2, bevel=R_FINE, x=HALF_L - 0.8),
    box('side_panel_r', 'Kolbenpaneel rechts', 'Butt panel right', 'stock', 'anodized', 'Wartungsdeckel über dem Puffer',
        'in die Mulde geschraubt (4 Schrauben)', -134, -62, 62, 72, 1.2, bevel=R_FINE, x=-HALF_L + 0.8),
    part('panel_screws', 'Paneelschrauben', 'Panel screws', 'stock', 'multi', 'trim', 'Halten die Kolbenpaneele', 'in den Paneelen',
         bevel=0.2, items=mirror(screws([(-129, 65), (-129, 69), (-67, 65), (-67, 69)], HALF_L - 0.2, r=1.5, h=0.8))),
    part('takedown_pins', 'Querbolzen', 'Takedown pins', 'receiver', 'multi', 'metal', 'Verbinden Deck und Rumpf',
         'quer durch den Rumpf (lösbar)', bevel=0.4, items=mirror(screws([(-60, 70), (150, 70)], HALF_L - 1, r=3.4, h=1.0))),
    prof('butt_pad', 'Kolbenkappe', 'Butt pad', 'stock', 'rubber', 'Rutschfeste Anlage an der Schulter', 'auf das Kolbenende gesteckt',
         [(BUTT + 1, 69), (BUTT + 1, CHEEK[1] - 3), (BUTT - 4, CHEEK[1] - 4), (BUTT - 10, CHEEK[1] - 10), (BUTT - 12, CHEEK[1] - 18),
          (BUTT - 12, 75), (BUTT - 9, 71), (BUTT - 5, 69)], 2 * HALF_D - 2,
         bevel=R_MID, cuts=[cut_box(BUTT - 15, BUTT - 9, 77 + 7 * i, 80 + 7 * i, 60) for i in range(3)]),   # Runde 2: Kappe so breit wie das Deck
]
P.append(prof('spine', 'Rückenleiste', 'Spine', 'receiver', 'shell', 'Erhöhte Leiste auf dem Deck; trägt Schiene und Visier (Schichtung)',
              'auf das Deck geschraubt', [(CHEEK[0] + 6, TOP - SPINE[1] - 0.5), (face(TOP - SPINE[1] - 0.5), TOP - SPINE[1] - 0.5),
                                         (face(TOP), TOP), (CHEEK[0] + 9, TOP)], 2 * SPINE[0], bevel=R_SMALL))
# Λ-Fenster links am Deck (Blickfang): Rahmen blank, Glas, Anzeige im Schacht, dunkler Grund
P += [
    prof('window_frame', 'Fensterrahmen', 'Window frame', 'receiver', 'trim', 'Blanker Rahmen des Λ-Fensters', 'um das Fenster geschraubt',
         tri(3.6, clip=WIN_CLIP), 1.6, bevel=0.5, x=HALF_D + 0.5, cuts=[dict(shape='prof', pts=tri(1.4), w=6, x=HALF_D)]),
    prof('window_lens', 'Fensterglas', 'Window glass', 'receiver', 'glass', 'Schützt die Anzeige', 'im Rahmen', tri(1.8, clip=WIN_CLIP - 0.8), 0.6, bevel=0,
         x=HALF_D - 1.2),
    prof('window_back', 'Fenstergrund', 'Window well', 'receiver', 'dark_metal', 'Dunkler Grund hinter der Anzeige',
         'im Fensterschacht, 4 mm hinter dem Glas', tri(2.4, clip=WIN_CLIP - 0.6), 1.0, bevel=0, x=HALF_D - 4.5),
    part('ammo_counter', 'Munitionsanzeige', 'Ammo counter', 'receiver', 'prof', 'energy',
         'Füllstand des Magazins als leuchtendes Dreieck; Blickfang links', 'im Λ-Fenster hinter dem Glas', bevel=0.3, pts=tri(-0.6),
         w=1.4, x=HALF_D - 3.2, move=dict(kind='glow', pivot=None, event='fire', max=5.0)),
]
# Schiene, Visier H2 „Pille“, Verschluss, Auswurfklappe
P += [dict(p, mat='anodized') for p in rail(-64, 40, TOP)]   # Runde 2: Schiene nur unter dem Visier (r1 lief sie wie bei BASIC-01 über das ganze Deck)
P[-1]['cuts'] = [cut_box(-58 + 12 * i, -52 + 12 * i, TOP + 4, TOP + 9, 30) for i in range(8)]
_sight, SIGHT_ANCHORS = holo_pille(-46, TOP + 8, weapon_type='submachine_gun')
P += _sight
P += [
    box('bolt', 'Verschluss', 'Bolt', 'mechanism', 'metal', 'Lädt und verriegelt; läuft beim Schuss zurück', 'im Deck geführt',
        -20, 70, 84, 100, 22, bevel=R_SMALL, move=dict(kind='translate', pivot=(47, 92, 0), vector_mm=(-30, 0, 0), event='fire')),
    prof('port_cover', 'Auswurfklappe', 'Ejection port cover', 'mechanism', 'anodized', 'Deckt das Auswurffenster ab',
         'Scharnier an der Unterkante', [(_port[0], _port[2]), (_port[1], _port[2]), (_port[1], _port[3]), (_port[0], _port[3])], 1.6,
         bevel=R_FINE, x=-HALF_D - 0.6,
         move=dict(kind='rotate', pivot=(47, _port[2], -HALF_D - 1), axis='f', range_deg=(0, 75), event='fire',
                   expect=((47, _port[3], -HALF_D - 1), (0, 0, -1)))),
    part('deck_stripe', 'Längsstreifen', 'Deck stripe', 'stock', 'multi', 'accent', 'Lackierter Längsstreifen (einziges Grafikelement)',
         'lackiert, links vorn am Deck', bevel=0,
         items=[dict(shape='prof', pts=[(50, 100), (130, 100), (128, 104.5), (50, 104.5)], w=0.3, x=HALF_D + 0.15)]),   # Runde 2: links vorn
    part('text_r', 'Schriftzug', 'Lettering', 'receiver', 'text', 'decal', 'Kennung „BASIC  EX-06“ (einzige Schrift)',
         'aufgedruckt', bevel=0, text='BASIC  EX-06', size=4.2, f=84, u=103, x=-HALF_D - 0.05, side=-1, depth=0.12),
]
# ---------------------------------------------------------------- Stirn, Lauf, Mündung
P += [
    prof('face_plate', 'Stirnplatte', 'Face plate', 'barrel', 'anodized', 'Stirnschild um die Laufbuchse; zweite Schicht',
         'auf die Kinnstirn geschraubt, 2 mm vorstehend', [(face(LOW + 6) - 4, LOW + 6), (face(LOW + 6) + 2, LOW + 6),
                                                          (face(TOP - 8) + 2, TOP - 8), (face(TOP - 8) - 4, TOP - 8)], 32, bevel=R_SMALL),
    part('face_screws', 'Stirnschrauben', 'Face screws', 'barrel', 'multi', 'trim', 'Halten die Stirnplatte', 'seitlich an der Stirn',
         bevel=0.2, items=mirror(screws([(face(56) - 9, 56), (face(100) - 9, 100)], HALF_L - 0.2, r=1.6, h=0.8))),
    cyl('barrel', 'Lauf', 'Barrel', 'barrel', 'metal', 'Führt das Geschoss', 'im Rumpf verschraubt', 'f', (BORE, 0), 60, face(BORE) + 8, 7.5,
        segs=24),
    cyl('bushing', 'Laufbuchse', 'Barrel bushing', 'barrel', 'trim', 'Führt den Lauf in der Stirn; blanke Stufe', 'in die Stirnplatte gepresst',
        'f', (BORE, 0), face(BORE) - 4, face(BORE) + 7, 12.5, r_in=7.8, segs=32, bevel=0.5),
    cyl('muzzle', 'Kompensator', 'Compensator', 'barrel', 'anodized', 'Runder Kompensator mit drei Seitenports je Seite; Socket_Muzzle vorn',
        'auf Laufende geschraubt (lösbar)', 'f', (BORE, 0), face(BORE) + 6, face(BORE) + 44, 13.5, r_in=5, segs=32, bevel=R_SMALL,
        iface='BMZ-15', cuts=[cut_box(face(BORE) + 14 + 9 * i, face(BORE) + 19 + 9 * i, BORE - 5, BORE + 5, 40) for i in range(3)]),
    cyl('muzzle_crown', 'Mündungskrone', 'Muzzle crown', 'barrel', 'trim', 'Blanke Stirnkante', 'vorn am Kompensator',
        'f', (BORE, 0), face(BORE) + 43, face(BORE) + 48, 12.5, r_in=5.5, segs=32, bevel=0.6),
]
# ---------------------------------------------------------------- Griff BGM-1, Abzugsbügel bis an den Schacht, Bedienung
for p in grip_v21(top=GRIP_TOP):
    if p['id'] == 'trigger_guard':   # A: Bügel läuft unten bis an die Schachthinterkante und schließt den Gabelzwickel (kein Vorderpfosten)
        g0 = GRIP_TOP * TG + 18
        p.update(pts=[(g0 - 10, 5), (rake(WELL[0], 5) + 1.5, 5), (rake(WELL[0], 14) + 1.5, 14), (g0 - 8, 14)], w=14,   # hinten bis in den Griff
                 attach='Griff vorn und Schacht hinten (fest)')
    P.append(p)
P += selector(-26, 62, x=HALF_L + 0.5)
P += [dict(p, id='selector_r', de='Feuerwahlhebel rechts', en='Fire selector right', x=-HALF_L - 0.5) for p in selector(-26, 62)]
P += charging_handle(-136, 92, x=HALF_D + 0.5, travel=40)   # Runde 2: hinten links, r1 drängte er sich neben das Λ-Fenster
# ---------------------------------------------------------------- Schacht als Vordergriff, Magazin (BMW-R)
_mc = ((WELL[0] + WELL[1]) / 2, LOW)       # Magazinachse durch die Schachtmitte auf u = LOW
P += [
    prof('mag_well', 'Schachtgriff', 'Magazine well grip', 'support', 'graphite',
         'Magazinschacht und Vordergriff in einem; um RAKE nach vorn gespreizt (Gabelbein); Socket_SupportHand',
         'am Rumpf angeformt (fest)', para(WELL[0], WELL[1], WELL_LOW, LOW + 2), 2 * HALF_L + 2, bevel=R_MID,
         cuts=[dict(shape='prof', pts=para(WELL[0] + 7, WELL[1] - 7, WELL_LOW - 4, LOW + 4), w=27)]),
    prof('well_lip', 'Schachtlippe', 'Magazine well lip', 'ammo', 'trim', 'Blanke Einführkante unten am Schacht',
         'unten am Schachtgriff', para(WELL[0] - 1.5, WELL[1] + 1.5, WELL_LOW - 3, WELL_LOW + 0.5), 2 * HALF_L + 3, bevel=0.6, iface='BMW-R',
         cuts=[dict(shape='prof', pts=para(WELL[0] + 7, WELL[1] - 7, WELL_LOW - 5, WELL_LOW + 2), w=27)]),
    prof('well_pad', 'Griffpolster', 'Grip pad', 'support', 'rubber', 'Rutschfeste Vorderseite des Schachtgriffs (Finger der Stützhand)',
         'vorn auf den Schachtgriff geklebt', para(WELL[1] - 3, WELL[1] + 2.5, WELL_LOW + 6, LOW - 6), 2 * HALF_L - 4, bevel=R_SMALL,
         cuts=[dict(shape='prof', pts=para(WELL[1] - 6, WELL[1] + 6, u, u + 3), w=60) for u in (-20, -6, 8, 22)]),
    prof('well_pad_r', 'Daumenpolster', 'Thumb pad', 'support', 'rubber', 'Rutschfeste Hinterseite des Schachtgriffs (Handballen)',
         'hinten auf den Schachtgriff geklebt', para(WELL[0] - 2.5, WELL[0] + 3, WELL_LOW + 6, 20), 2 * HALF_L - 4, bevel=R_SMALL),
    part('mag_release', 'Magazinhalter', 'Magazine release', 'grip_controls', 'cyl', 'accent', 'Löst das Magazin im Schachtgriff',
         'Druckknopf links am Schachtgriff, Daumen der Stützhand', bevel=R_FINE, axis='x', c=(rake(WELL[0], 28) + 14, 28),
         a0=HALF_L, a1=HALF_L + 4.5, r=4.5, segs=20,
         move=dict(kind='translate', pivot=(rake(WELL[0], 28) + 14, 28, HALF_L + 2), vector_mm=(0, 0, -2.5), event='reload')),
]
_m = rifle_mag(_mc[0] - 15, LOW, depth=30, length=158, tilt=RAKE, w=24, curve=0)
_win_u = [LOW - 92 - 6.2 * i for i in range(5)]   # A: Patronen im Fenster unter dem Schacht (Magazinachse, vor der Drehung)
for p in _m:
    if p['id'] == 'magazine':
        p['de'], p['func'] = 'Magazin', 'Gerades Doppelreihenmagazin, um RAKE gespreizt; tritt unten aus dem Schachtgriff; entnehmbar'
        p['cuts'] = [dict(shape='prof', pts=rot([(_mc[0] - 8, LOW - 86), (_mc[0] + 8, LOW - 86), (_mc[0] + 8, LOW - 120),
                                                  (_mc[0] - 8, LOW - 120)], _mc, RAKE), w=8, x=12)]
    if p['id'] == 'magazine_base':
        p['mat'] = 'anodized'
    if p['id'] == 'magazine_round':
        p['mat'] = 'brass'
P += _m
P += [
    part('mag_rounds', 'Patronen im Fenster', 'Visible rounds', 'ammo', 'multi', 'brass', 'Zeigt den Füllstand', 'im Magazin',
         bevel=0.3, parent_part='magazine', smooth=True,
         items=[dict(shape='cyl', axis='f', c=(rot([(_mc[0], u)], _mc, RAKE)[0][1], 4 if i % 2 else -2),
                     a0=rot([(_mc[0], u)], _mc, RAKE)[0][0] - 11, a1=rot([(_mc[0], u)], _mc, RAKE)[0][0] + 11, r=4.4, segs=12)
                for i, u in enumerate(_win_u)]),
]
PARTS = P

# ---------------------------------------------------------------- Anker, Weltpunkte, Aktionen
_sup = (rake(_mc[0], 4), 4)
ANCHORS = {
    'Socket_Hand': dict(at=(0, 0, 0), part='grip', note='Haupthand, auf der Griffachse (V: BGM-1)'),
    'Socket_SupportHand': dict(at=_sup, part='mag_well', note='Mitte Schachtgriff (Stützhand am gespreizten Schacht)'),
    'Socket_Muzzle': dict(at=(face(BORE) + 48, BORE, 0), part='muzzle_crown', note='Stirn der Mündungskrone auf der Laufachse'),
    'Socket_MagWell': dict(at=_mc, part='mag_well', note='Einrastpunkt Magazin (Schnittstelle BMW-R) im Schachtgriff'),
    'Socket_Charge': dict(at=(-124, 92, HALF_D + 5), part='charging_handle', note='Griffpunkt Ladehebel links (Stützhand)'),
}
ANCHORS.update(SIGHT_ANCHORS)
EJECT = dict(at=(47, 92, -HALF_D + 1), dir=(0.3, 0.4, -1.0), case='pistol',
             src='A: Mitte Auswurffenster rechts am Deck (port_cover), Kurzpatrone nach rechts, etwas hoch und vorn (wie BASIC-06)')
_mag_contact = rot([(_mc[0], LOW - 100)], _mc, RAKE)[0]
EGO_GRIPS = {
    'grip':    dict(contact=(-3, -6, -16.5), palm=(0.15, 0.0, 1.0), fingers=(1.0, -0.06, 0.0), fingers_pose='trigger',
                    src='V: Griff BGM-1 wie die Familie (gleiche Lage zu Socket_Hand)'),
    'support': dict(contact=(_sup[0] - 4, _sup[1], HALF_L + 1.5), palm=(0.15, 0.0, -1.0), fingers=(0.91, 0.32, 0.0), fingers_pose='foregrip',
                    finger_map=dict(open='foregrip_open'),
                    src='A: links am Schachtgriff, Faust um den gespreizten Schacht, Finger quer zur Schachtachse (wie BASIC-06 am Vordergriff)'),
    'mag':     dict(part='magazine', contact=(_mag_contact[0], _mag_contact[1], 12.5), palm=(0.0, 0.0, -1.0), fingers=(0.91, 0.41, 0.0),
                    fingers_pose='mag_hold', src='A: links am Magazin unter dem Schachtgriff, Hand greift von unten'),
    'charge':  dict(part='charging_handle', contact=(-124, 92, HALF_D + 5), palm=(0.0, 0.0, -1.0), fingers=(0.45, 0.9, 0.0),
                    fingers_pose='pinch', src='A: am Ladehebel links (Socket_Charge)'),
}
POINTS = collect(EJECT, EGO_GRIPS, dict(eject='upper', grip='grip', support='mag_well'))
EGO_LIVE = dict(trigger='trigger', bolt='bolt', port='port_cover')
ACTIONS = {
    'fire_auto': dict(de='Dauerfeuer (Verschluss, Auswurfklappe, Λ-Anzeige)', frames=24, step=1, keys={
        'trigger': [(0, 0), (2, 1), (20, 1), (23, 0)], 'port_cover': [(0, 0), (3, 1), (24, 1)],
        'bolt': [(0, 0), (2, 0), (3, 1), (4, 0), (5, 1), (6, 0), (7, 1), (8, 0), (10, 1), (11, 0), (12, 1), (13, 0)]},
        events=[(2, 'shot'), (5, 'shot'), (7, 'shot'), (10, 'shot'), (12, 'shot')], view=(-0.85, -0.25, 0.45)),
    'reload_empty': dict(de='Nachladen aus leerem Zustand', frames=78, keys={
        'magazine': [(0, 0), (16, 1), (32, 1), (48, 0)], 'charging_handle': [(0, 0), (56, 0), (62, 1), (68, 0)]},
        events=[(16, 'mag_out'), (48, 'mag_seated'), (62, 'charge'), (70, 'ready')]),
}
EXPLODE = {'sight': (0, 100, 0), 'ammo': (60, -150, 0), 'stock': (-90, 0, 0), 'barrel': (120, 0, 0), 'support': (30, -60, 0),
           'grip_controls': (-10, -80, 0), 'mechanism': (0, 0, -90), 'receiver': (0, 0, 0)}
HERO = (0.62, -0.62, 0.40)   # A: Produktbild von links vorn oben – Λ-Fenster, Gabelbein und Kinnstirn zur Kamera
