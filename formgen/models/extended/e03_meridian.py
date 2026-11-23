"""EXTENDED-03 „Meridian“ – eigenständiges Sci-Fi-Spähergewehr der BASIC-Familie (Formgen v2 0.17 „Outrider“).

Eigenes Modell im BALLON-Kit-Vokabular (reines Python, kein bpy). Keine Teile oder Umbauten von BASIC-03: aus `basic.common` kommen nur
genormte Familienschnittstellen (Griffmodul BGM-1, Zielfernrohr Z1 „Tropfen“ auf zwei Schienen BRI-22, Gewehrmagazin an BMW-R,
Feuerwahlhebel, Ladehebel-Form, Schraubenköpfe) und Hilfen (`cut_box`, `mirror`, `rot`). Geladen über `formgen.extended`, gerendert mit
BALLONs unverändertem `tools/blender_build.main` (`tools/extended_render.py`).

Formsprache (Stilhandbuch BALLON §3; Auswahl und Skizzen: docs/extended.md)
- Leitmerkmal: koaxiale Rohrlinie. Rohrschaft, Gehäusetrommel und Vorderrohr liegen auf einer Achse, der Laufachse; das Zielfernrohr
  läuft parallel darüber. Ober- und Unterlinie sind vom Kolben bis zur Stirn gerade und parallel, nur Griff und Magazin hängen darunter.
- Querschnitt: Kreis. Die Gehäusetrommel hat seitliche Flächen für Auswurf, Paneele und Schrift (Kreis mit Flächen), das Vorderrohr
  ist rund und oben kanneliert; vier Längsrillen.
- Negativraum: die Wangenbrücke über dem Rohrschaft (ein Fenster 82 × 11 mm quer durch) und der offene Raum unter dem Rohrschaft
  zwischen Griff und Schulterplatte.
- Blickfang (genau einer): die Meridianlinie, eine Ladeanzeige als Leuchtlinie in der oberen linken Rille des Vorderrohrs.
- Zweiton: Creme für Trommel, Vorderrohr und Wangenbrücke über Graphit für Fahrgestell, Handschale, Rohrschaft und Schulterplatte.
- Schichten: Trommel 4 mm über dem Vorderrohr mit blankem Kupplungsring, Handschale 2,5 mm über dem Rohr, Seitenpaneele in Mulden der
  Flächen, Stirnkappe 2 mm zurückgesetzt.
- Grafik: ein lackierter Ring um das Vorderrohr vor der Handschale; eine Schrift rechts auf der Trommelfläche.
- Front mehrstufig: runde Rohrstirn mit Fase, eloxierte Stirnkappe, blanke Krone, eingelassene dunkle Mündung (integrierter Dämpfer).
- Ergonomie: Griff BGM-1 (Socket_Hand 0/0), Handschale mit Gummistreifen für die Stützhand, Ladehebel links an der Trommel vorn
  (Stützhand), Magazinhalter links; Akzent-Bedienfunktionen: Ladehebel, Magazinhalter, Feuerwahlhebel (3).

Herkunft der Zahlen: V = Vorgabe (Familie/Schnittstelle, BASIC-03 Pilot v2.1 bzw. `basic.common`), A = Annahme (Entwurf 0.17),
G = gemessen; Zahlen ohne Kennung sind A (Entwurf 0.17, an den Renders r1–r3 gesichtet).
Maße mm; f nach vorn, u nach oben, x nach links; Socket_Hand = (0, 0, 0).
"""
import math

from basic.arms.ego import GRIPS as _EGO
from basic.common import (part, prof, box, cyl, rot, cut_box, screws, mirror, rail, selector, charging_handle, grip_v21,
                          scope_tropfen, rifle_mag, R_MID, R_SMALL, R_FINE)
from basic.variant import collect

META = dict(id='EXTENDED-03', num='E03', sheet_id='EA03', type='scout_rifle', type_de='Scout-Gewehr', type_en='Scout Rifle',
            family='BASIC', name='Meridian', nick='Mittellinie', ammo='primary', fire='semi',
            reference_length_m=0.915, reference_length_source='A: Entwurf 0.17 (BASIC-03 1,02 m als Rahmen, V)',
            inspired_by='BASIC-03 Familie; Formgen v1 Langwaffen mit einer durchgehenden Linie als Haltung',
            summary='Spähergewehr als koaxiale Rohrlinie mit Rohrschaft, kanneliertem Vorderrohr und Meridianlinie (EXTENDED-Reihe).')
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

BORE = 96            # V: Laufachse wie BASIC-03
R_DRUM = 26.0        # A: Gehäusetrommel
FLAT = 23.0          # A (Runde 2): Seitenflächen der Trommel bei |x| = 23 (Sehne u 83,9 … 108,1); r1 mit 20 wirkte kastig
R_TUBE = 22.0        # A: Vorderrohr, 4 mm unter der Trommel (Stufe)
R_SLEEVE = 25.5      # A (Runde 2): Handschale 3,5 mm über dem Rohr; r1 mit 2,5 las sich als flache Leiste
F_REAR, F_JOIN, F_FACE = -114, 196, 600   # A: Trommelende, Kupplung Trommel/Vorderrohr, Rohrstirn
RAIL_U = 120         # A: Schienen in die Trommel versenkt (Oberkante 128)
CU = 160             # V: Visierhöhe 66 ± 4 → 64 mm über der Laufachse (BASIC-03 65)
F_OBJ = 74           # A: Ringstirn des Objektivs; Augenpunkt 90 mm dahinter (f −16, über dem Griff)
SEAT_F = (-54, -20)  # A: hintere Schiene unter dem Rohrsattel (hinter dem Augenpunkt)
FOOT_F = (40, 78)    # A: vordere Schiene unter dem Klemmfuß
STOCK_END = -300     # A: Schulterplatte hinten (Schaftlänge ab Abzug ≈ 315 mm wie BASIC-03)
FLUTES = (40, 75, 105, 140)   # A: Rillenwinkel in Grad (0 = links waagrecht, 90 = oben); die linke obere trägt die Meridianlinie
FLUTE_F = (214, 556)


def flute(deg, depth_in, depth_out, half_w, r=R_TUBE):
    """Rille im Rohr als Querprofil um die Laufachse: radial von r − depth_in bis r + depth_out, tangential ± half_w."""
    a = math.radians(deg)
    n, t = (math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a))

    def pt(rad, tan):
        return (round(n[0] * rad + t[0] * tan, 3), round(BORE + n[1] * rad + t[1] * tan, 3))
    return [pt(r - depth_in, -half_w), pt(r - depth_in, half_w), pt(r + depth_out, half_w), pt(r + depth_out, -half_w)]


def flats(f0, f1, half, r):
    """Seitenflächen: schneidet die Trommel außerhalb |x| = half (beidseitig)."""
    return [cut_box(f0, f1, BORE - r - 2, BORE + r + 2, 2 * r, x=sx * (half + r)) for sx in (1, -1)]


P = []
# ---------------------------------------------------------------- Gehäusetrommel und Fahrgestell
P += [
    cyl('drum', 'Gehäusetrommel', 'Receiver drum', 'receiver', 'shell',
        'Rundes Gehäuse auf der Laufachse; Seitenflächen für Auswurf, Paneele, Schrift', 'auf dem Fahrgestell (zwei Querbolzen)',
        'f', (BORE, 0), F_REAR, F_JOIN, R_DRUM, segs=48, bevel=R_MID,
        cuts=flats(F_REAR - 2, F_JOIN + 2, FLAT, R_DRUM)
        + [cut_box(22, 72, 87, 105, 8, x=-FLAT),                                  # Auswurffenster rechts
           cut_box(100, 166, 96, 106, 8, x=FLAT),                                 # Ladehebel-Nut links vorn
           cut_box(-104, -32, 86, 106, 3.0, x=FLAT + 0.6), cut_box(-104, -32, 86, 106, 3.0, x=-FLAT - 0.6)]),   # Paneelmulden
    cyl('drum_cap', 'Trommeldeckel', 'Drum end cap', 'receiver', 'dark_metal', 'Schließt die Trommel hinten; trägt den Rohrschaft',
        'in die Trommel geschraubt', 'f', (BORE, 0), F_REAR - 8, F_REAR + 2, R_DRUM - 2.5, segs=48, bevel=R_SMALL),
    prof('lower', 'Fahrgestell', 'Chassis', 'receiver', 'graphite', 'Griffmodul, Abzugsgruppe, Magazinschacht',
         'unter der Trommel, Fuge 1 mm; Schacht angeformt, Front läuft in die Trommel',
         [(F_REAR + 4, 86), (F_REAR + 4, 74), (-76, 44), (82, 44), (88, 30), (92, 22), (128, 22), (134, 32), (150, 66), (186, 76),
          (186, 86)], 2 * FLAT - 2, bevel=R_MID),
    prof('mag_well', 'Schachtlippe', 'Magazine well lip', 'receiver', 'trim', 'Blanke Einführkante des Magazinschachts',
         'unten am Schacht des Fahrgestells', [(91, 19.5), (129, 19.5), (130, 23), (90, 23)], 2 * FLAT - 1, bevel=0.6, iface='BMW-R'),
    box('side_panel_l', 'Seitenpaneel links', 'Side panel left', 'receiver', 'anodized', 'Wartungsdeckel über dem Verschlussweg',
        'in die Mulde geschraubt (4 Schrauben)', -102, -34, 87.5, 104.5, 1.2, bevel=R_FINE, x=FLAT - 0.8),
    box('side_panel_r', 'Seitenpaneel rechts', 'Side panel right', 'receiver', 'anodized', 'Wartungsdeckel über dem Verschlussweg',
        'in die Mulde geschraubt (4 Schrauben)', -102, -34, 87.5, 104.5, 1.2, bevel=R_FINE, x=-FLAT + 0.8),
    part('panel_screws', 'Paneelschrauben', 'Panel screws', 'receiver', 'multi', 'trim', 'Halten die Seitenpaneele', 'in den Paneelen',
         bevel=0.2, items=mirror(screws([(-97, 91.5), (-97, 100.5), (-39, 91.5), (-39, 100.5)], FLAT - 0.2, r=1.5, h=0.8))),
    part('takedown_pins', 'Querbolzen', 'Takedown pins', 'receiver', 'multi', 'metal', 'Verbinden Trommel und Fahrgestell',
         'quer durch das Fahrgestell (lösbar)', bevel=0.4, items=mirror(screws([(-100, 78), (170, 78)], FLAT - 1, r=3.4, h=1.0))),
    cyl('coupling', 'Kupplungsring', 'Coupling ring', 'barrel', 'trim', 'Verschraubt das Vorderrohr mit der Trommel; blanke Stufe',
        'zwischen Trommel und Vorderrohr', 'f', (BORE, 0), F_JOIN - 1, F_JOIN + 7, R_TUBE + 1.8, segs=48, bevel=0.5),
    part('mag_release', 'Magazinhalter', 'Magazine release', 'grip_controls', 'cyl', 'accent', 'Löst das Magazin',
         'Druckknopf links', bevel=R_FINE, axis='x', c=(84, 58), a0=FLAT - 3, a1=FLAT + 2.5, r=4.5, segs=20,
         move=dict(kind='translate', pivot=(84, 58, FLAT), vector_mm=(0, 0, -2.5), event='reload')),
    part('text_r', 'Schriftzug', 'Lettering', 'receiver', 'text', 'decal', 'Kennung „BASIC  EX-03“ (einzige Schrift)',
         'aufgedruckt', bevel=0, text='BASIC  EX-03', size=4.0, f=84, u=90, x=-FLAT - 0.05, side=-1, depth=0.12),
    box('bolt', 'Verschluss', 'Bolt', 'mechanism', 'metal', 'Lädt und verriegelt; läuft beim Schuss zurück', 'in der Trommel geführt',
        -30, 76, 89, 103, 20, bevel=R_SMALL, move=dict(kind='translate', pivot=(20, 96, 0), vector_mm=(-34, 0, 0), event='fire')),
    prof('port_cover', 'Auswurfklappe', 'Ejection port cover', 'mechanism', 'anodized', 'Deckt das Auswurffenster ab',
         'Scharnier an der Unterkante', [(22, 87), (72, 87), (72, 105), (22, 105)], 1.6, bevel=R_FINE, x=-FLAT - 0.6,
         move=dict(kind='rotate', pivot=(47, 87, -FLAT - 1), axis='f', range_deg=(0, 75), event='fire',
                   expect=((47, 105, -FLAT - 1), (0, 0, -1)))),
]
# Schienen BRI-22 (in die Trommel versenkt) und Zielfernrohr Z1 „Tropfen“ (Familie, Konzept A)
P += [dict(p, mat='anodized', attach='in die Trommel hinter dem Augenpunkt versenkt (fest)') for p in rail(*SEAT_F, RAIL_U)]
P += [dict(p, id='rail_front', de='Schiene vorn', en='Front rail', mat='anodized', attach='in die Trommel unter dem Objektiv versenkt (fest)')
      for p in rail(*FOOT_F, RAIL_U)]
_scope, SIGHT_ANCHORS = scope_tropfen(F_OBJ, RAIL_U + 8, CU, weapon_type='scout_rifle', seat_u=RAIL_U + 8)
P += _scope
# ---------------------------------------------------------------- Vorderrohr, Handschale, Stirn
_ring_f = 436    # A (Runde 3): direkt vor der Handschale (Kontrast am Graphit); r2 bei f 452 ging im Creme unter
P += [
    cyl('tube', 'Vorderrohr', 'Fore tube', 'barrel', 'shell',
        'Rundes Vorderrohr um Lauf und Dämpfer; oben vier Längsrillen', 'in den Kupplungsring geschraubt',
        'f', (BORE, 0), F_JOIN + 6, F_FACE, R_TUBE, segs=48, bevel=R_MID,
        cuts=[dict(shape='xprof', pts=flute(d, 2.4, 3.0, 3.0), f0=FLUTE_F[0], f1=FLUTE_F[1], cu=0) for d in FLUTES]
        + [dict(shape='cyl', axis='f', c=(BORE, 0), a0=F_FACE - 10, a1=F_FACE + 4, r=R_TUBE - 2.4, segs=48)]),   # Stirnmulde für die Kappe
    part('meridian', 'Meridianlinie', 'Meridian line', 'receiver', 'xprof', 'energy',
         'Ladeanzeige: leuchtet, wenn eine Patrone im Lager ist (Blickfang)', 'im Grund der linken oberen Rille', bevel=0,
         pts=flute(FLUTES[0], 2.35, -1.3, 2.3), f0=226, f1=372, cu=0,
         move=dict(kind='glow', pivot=None, event='chamber', max=4.0)),
    cyl('handguard', 'Handschale', 'Handguard shell', 'support', 'graphite', 'Untere Schale um das Vorderrohr; Griffbereich der Stützhand',
        'um das Vorderrohr geklemmt, Oberkante 2 mm über der Laufachse', 'f', (BORE, 0), F_JOIN + 14, 430, R_SLEEVE,
        r_in=R_TUBE - 0.5, segs=48, bevel=R_MID, cuts=[cut_box(F_JOIN + 10, 440, BORE + 2, BORE + 40, 70)]
        + [dict(shape='cyl', axis='x', c=(f, BORE - 12), a0=-40, a1=40, r=4.5, segs=24) for f in range(244, 404, 26)]),   # Lochreihe (Runde 3)
    prof('handguard_grip', 'Griffstreifen', 'Grip strip', 'support', 'rubber', 'Rutschfeste Zone für die Stützhand',
         'unten in die Handschale geklebt', [(248, 69), (392, 69), (392, 74), (248, 74)], 20, bevel=R_SMALL),
    part('handguard_screws', 'Schalenschrauben', 'Shell screws', 'support', 'multi', 'trim', 'Klemmen die Handschale',
         'seitlich an der Schale', bevel=0.2, items=mirror(screws([(222, 92), (414, 92)], R_SLEEVE - 0.6, r=1.6, h=0.8))),
    cyl('band', 'Farbring', 'Paint ring', 'barrel', 'accent', 'Lackierter Ring um das Vorderrohr (einziges Grafikelement)',
        'lackiert', 'f', (BORE, 0), _ring_f, _ring_f + 12, R_TUBE + 0.05, r_in=R_TUBE - 1, segs=48, bevel=0,
        cuts=[dict(shape='xprof', pts=flute(d, 2.4, 3.0, 3.0), f0=_ring_f - 1, f1=_ring_f + 13, cu=0) for d in FLUTES]),
    cyl('face_cap', 'Stirnkappe', 'Face cap', 'barrel', 'anodized', 'Stirnabschluss des Vorderrohrs; zweite Stufe',
        'in die Stirnmulde geschraubt', 'f', (BORE, 0), F_FACE - 9, F_FACE + 3, R_TUBE - 2.6, r_in=12, segs=48, bevel=R_SMALL),
    cyl('crown', 'Stirnkrone', 'Face crown', 'barrel', 'trim', 'Blanke Innenkante der Stirnkappe', 'in der Stirnkappe',
        'f', (BORE, 0), F_FACE - 2, F_FACE + 3.6, 12.4, r_in=10, segs=48, bevel=0.4),
    cyl('barrel', 'Lauf', 'Barrel', 'barrel', 'metal', 'Führt das Geschoss; frei schwingend im Vorderrohr', 'in der Trommel verschraubt',
        'f', (BORE, 0), F_JOIN - 20, F_FACE - 30, 7.5, segs=24),
    cyl('muzzle', 'Mündung', 'Muzzle', 'barrel', 'dark_metal', 'Eingelassene Mündung des integrierten Dämpfers; Socket_Muzzle vorn',
        'auf Laufende geschraubt (lösbar, BMZ-15)', 'f', (BORE, 0), F_FACE - 32, F_FACE + 1, 10, r_in=4.5, segs=24, bevel=R_SMALL,
        iface='BMZ-15', cuts=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=F_FACE - 2 - 3 * i, a1=F_FACE - 1 - 3 * i, r=11, r_in=8.6, segs=24)
                              for i in range(3)]),
]
# ---------------------------------------------------------------- Griff, Bedienung, Magazin
P += grip_v21(top=44)
P += selector(6, 62, x=FLAT + 0.5)
P += [dict(p, id='selector_r', de='Feuerwahlhebel rechts', en='Fire selector right', x=-FLAT - 0.5) for p in selector(6, 62)]
P += charging_handle(124, 103, x=FLAT + 0.5, travel=24)
_mf, _mu, _tilt = 92, 60, 6     # A: Schacht f 92 … 128 (V BASIC-03), Magazin 6° nach vorn
_mc = (_mf + 18, _mu)
_m = rifle_mag(_mf, _mu, depth=36, length=74, tilt=_tilt, w=22, curve=0)
for p in _m:
    if p['id'] == 'magazine':
        p['de'], p['func'] = 'Magazin', 'Kurzes Kastenmagazin (8); entnehmbar'
        p['cuts'] = [dict(shape='prof', pts=rot([(_mf + 8, 48), (_mf + 24, 48), (_mf + 24, 12), (_mf + 8, 12)], _mc, _tilt), w=8, x=9.5)]
    if p['id'] == 'magazine_base':
        p['mat'] = 'anodized'
    if p['id'] == 'magazine_round':
        p['mat'] = 'brass'
P += _m
P.append(part('mag_rounds', 'Patronen im Fenster', 'Visible rounds', 'ammo', 'multi', 'brass', 'Zeigt den Füllstand', 'im Magazin',
              bevel=0.3, parent_part='magazine', smooth=True,
              items=[dict(shape='cyl', axis='f', c=(rot([(_mf + 16, 42 - 6 * i)], _mc, _tilt)[0][1], 3 if i % 2 else -2),
                          a0=rot([(_mf + 16, 42 - 6 * i)], _mc, _tilt)[0][0] - 12, a1=rot([(_mf + 16, 42 - 6 * i)], _mc, _tilt)[0][0] + 12,
                          r=4.2, segs=12) for i in range(5)]))
# ---------------------------------------------------------------- Rohrschaft, Wangenbrücke, Schulterplatte
BRIDGE = (-262, -150)
P += [
    cyl('stock_tube', 'Rohrschaft', 'Stock tube', 'stock', 'graphite', 'Schaftrohr auf der Laufachse (koaxial)',
        'in den Trommeldeckel geschraubt', 'f', (BORE, 0), STOCK_END + 8, F_REAR - 6, 14, segs=40, bevel=R_SMALL),
    cyl('stock_ring', 'Schaftring', 'Stock ring', 'stock', 'trim', 'Blanker Klemmring am Rohrschaft', 'am Trommeldeckel',
        'f', (BORE, 0), F_REAR - 16, F_REAR - 8, 15.6, r_in=13.6, segs=40, bevel=0.4),
    prof('cheek_bridge', 'Wangenbrücke', 'Cheek bridge', 'stock', 'shell', 'Erhöhte Wangenanlage für das Zielfernrohr; offenes Fenster',
         'mit zwei Stegen auf den Rohrschaft geschraubt',
         [(BRIDGE[0] - 10, BORE + 9), (BRIDGE[1] + 12, BORE + 9), (BRIDGE[1] + 2, BORE + 30), (BRIDGE[1] - 4, BORE + 36),
          (BRIDGE[0] + 6, BORE + 36), (BRIDGE[0], BORE + 30)], 26, bevel=R_MID,   # A (Runde 2): Rampen zum Rohr; r1 wirkte lose
         cuts=[dict(shape='prof', pts=[(BRIDGE[0] + 14, BORE + 15), (BRIDGE[1] - 14, BORE + 15), (BRIDGE[1] - 14, BORE + 26),
                                       (BRIDGE[0] + 14, BORE + 26)], w=60)]),
    prof('cheek_pad', 'Wangenauflage', 'Cheek pad', 'stock', 'rubber', 'Weiche Anlage für die Wange', 'auf die Wangenbrücke geklebt',
         [(BRIDGE[0] + 10, BORE + 35), (BRIDGE[1] - 8, BORE + 35), (BRIDGE[1] - 10, BORE + 39), (BRIDGE[0] + 12, BORE + 39)], 20,
         bevel=R_SMALL),
    part('bridge_screws', 'Brückenschrauben', 'Bridge screws', 'stock', 'multi', 'trim', 'Halten die Wangenbrücke', 'in den Stegen',
         bevel=0.2, items=mirror(screws([(BRIDGE[0] + 7, BORE + 20), (BRIDGE[1] - 7, BORE + 20)], 13.0, r=1.6, h=0.8))),
    prof('butt_plate', 'Schulterplatte', 'Butt plate', 'stock', 'graphite', 'Trägt die Schulterkappe; Rohrschaft endet mittig',
         'auf das Rohrende geschraubt', [(STOCK_END, 36), (STOCK_END + 12, 40), (STOCK_END + 14, 120), (STOCK_END + 10, 128),
                                        (STOCK_END, 128)], 34, bevel=R_MID),
    prof('butt_pad', 'Schulterkappe', 'Butt pad', 'stock', 'rubber', 'Rutschfeste Anlage an der Schulter', 'auf die Schulterplatte gesteckt',
         [(STOCK_END + 1, 34), (STOCK_END + 1, 130), (STOCK_END - 8, 128), (STOCK_END - 11, 120), (STOCK_END - 11, 42), (STOCK_END - 8, 36)],
         38, bevel=R_MID, cuts=[cut_box(STOCK_END - 13, STOCK_END - 7, 44 + 13 * i, 47 + 13 * i, 44) for i in range(6)]),
]
PARTS = P

# ---------------------------------------------------------------- Anker, Weltpunkte, Aktionen
ANCHORS = {
    'Socket_Hand': dict(at=(0, 0, 0), part='grip', note='Haupthand, auf der Griffachse (V: BGM-1)'),
    'Socket_SupportHand': dict(at=(320, 74, 0), part='handguard', note='Mitte Handschale über dem Griffstreifen'),
    'Socket_Muzzle': dict(at=(F_FACE + 1, BORE, 0), part='muzzle', note='Stirn der eingelassenen Mündung auf der Laufachse'),
    'Socket_MagWell': dict(at=_mc, part='mag_well', note='Einrastpunkt Magazin (Schnittstelle BMW-R)'),
    'Socket_Charge': dict(at=(140, 103, FLAT + 5), part='charging_handle', note='Griffpunkt Ladehebel links vorn (Stützhand)'),
}
ANCHORS.update(SIGHT_ANCHORS)
EJECT = dict(at=(47, 96, -FLAT + 2), dir=(0.3, 0.4, -1.0), case='rifle',
             src='A: Mitte Auswurffenster rechts in der Trommelfläche (port_cover), Hülse nach rechts, etwas hoch und vorn')
_CONTACT = {'grip': ((-3, -6, -16.5), 'V: Griff BGM-1 wie die Familie'),
            'support': ((320, 69, -2), 'A: unter dem Griffstreifen der Handschale'),
            'mag': ((114, 12, 11.5), 'A: linke Seite des Kastenmagazins'),
            'charge': ((140, 103, FLAT + 5), 'A: Ladehebel links vorn')}
EGO_GRIPS = {k: dict(g, contact=_CONTACT[k][0], src=_CONTACT[k][1]) for k, g in _EGO.items()}
POINTS = collect(EJECT, EGO_GRIPS, dict(eject='drum', grip='grip', support='handguard_grip'))
ACTIONS = {
    'fire_semi': dict(de='Einzelschuss (Verschluss, Meridianlinie)', frames=12, step=1, keys={
        'trigger': [(0, 0), (2, 1), (6, 1), (9, 0)], 'port_cover': [(0, 0), (3, 1), (12, 1)],
        'bolt': [(0, 0), (2, 0), (3, 1), (6, 0)], 'meridian': [(0, 1), (2, 0), (5, 1), (12, 1)]},
        events=[(2, 'shot')], view=(-0.85, -0.25, 0.45)),
    'reload_empty': dict(de='Nachladen aus leerem Zustand', frames=80, keys={
        'mag_release': [(0, 0), (6, 1), (14, 0)],
        'magazine': [(0, 0), (6, 0), (16, 1), (32, 1), (48, 0)],
        'charging_handle': [(0, 0), (56, 0), (64, 1), (70, 0)],
        'meridian': [(0, 0), (66, 0), (70, 1), (80, 1)],
        'port_cover': [(0, 1), (80, 1)]},
        events=[(16, 'mag_out'), (48, 'mag_seated'), (64, 'charge'), (72, 'ready')]),
}
EXPLODE = {'sight': (0, 120, 0), 'ammo': (30, -140, 0), 'stock': (-110, 0, 0), 'barrel': (160, 0, 0), 'support': (60, -60, 0),
           'grip_controls': (-10, -80, 0), 'mechanism': (0, 0, -90), 'receiver': (0, 0, 0)}
HERO = (0.74, -0.52, 0.40)   # A: Produktbild von links vorn oben – Meridianlinie, Rohrstirn und Ladehebel zur Kamera
