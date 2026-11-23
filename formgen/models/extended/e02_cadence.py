"""EXTENDED-02 „Cadence“ – eigenständiges Sci-Fi-Impulsgewehr der BASIC-Familie (Formgen v2 0.17 „Outrider“).

Eigenes Modell im BALLON-Kit-Vokabular (reines Python, kein bpy). Keine Teile oder Umbauten von BASIC-02: aus `basic.common` kommen nur
genormte Familienschnittstellen (Griffmodul BGM-1, Holovisier H4 „Kasten“ auf Schiene BRI-22, Gewehrmagazin an BMW-R, Feuerwahlhebel,
Ladehebel-Form, Schraubenköpfe) und Hilfen (`rot`, `cut_box`, `mirror`). Geladen über `formgen.extended`, gerendert mit BALLONs
unverändertem `tools/blender_build.main` (`tools/extended_render.py`).

Formsprache (Stilhandbuch BALLON §3; Auswahl und Skizzen: docs/extended.md)
- Leitmerkmal: Monoblock-Bullpup als Parallelogramm. Die Creme-Kolbenschale trägt Kolben, Verschluss und Deck, davor sitzt 6 mm tiefer
  die Kammerhaube; Kolbenende, Stirn, Taktschlitze, Leuchtbalken, Magazin und beide schrägen Fugen neigen sich alle um LEAN = 15° nach
  vorn, so viel wie der Griff BGM-1. Das Magazin sitzt hinter dem Griff; die Waffe ist 0,70 m kurz und hoch.
- Querschnitt: Trapez. Breite Schulterfasen laufen über die ganze Länge (oben 30 statt 46 mm), das Graphit-Fahrgestell darunter ist
  1 mm je Seite schmaler.
- Negativraum: drei schräge Taktschlitze quer und oben offen durch die Kammerhaube zeigen Lauf und Impulsspulen, je Salvenschuss
  eine Spule; der Takt steht damit auch in der Oberlinie.
- Blickfang (genau einer): das Taktfenster links am Kolben, ein Parallelogramm mit drei Leuchtbalken hinter Glas in einem blanken
  Rahmen; die Balken leuchten nacheinander je Salvenschuss (eine Leuchtfunktion „Salvenanzeige“).
- Zweiton: Creme oben über die ganze Länge und als Kolbenblock hinter dem Magazin; Graphit-Fahrgestell darunter von der schrägen Fuge
  hinter dem Magazin bis zur Stirn (Teilung etwa 65:35).
- Schichten: Kammerhaube 6 mm unter dem Kolbendeck und 1 mm je Seite schmaler (schräge Fuge), Seitenpaneele in Mulden am Kolben
  (rechts Wartungsdeckel, links Träger des Taktfensters), Stirnplatte 1,5 mm vor der Stirn, Wangenauflage, Schiene und Visier auf dem Deck.
- Grafik: ein schräges Stirnband parallel zur Stirn (beidseitig); eine Schrift rechts an der Vorderkammer.
- Front mehrstufig: vorgeneigte Stirn mit eloxierter Stirnplatte, blanke Laufbuchse, achtkantige Mündung mit Schlitzen, dunkle Spitze,
  blanke Krone.
- Ergonomie: Griff BGM-1 (Socket_Hand 0/0), Handstopp-Lippe unter der Stirn, Gummipolster unter dem Vorderschaft, Ladehebel vorn links
  (Stützhand), Magazinhalter links vor dem Schacht; Akzent-Bedienfunktionen: Ladehebel, Magazinhalter, Feuerwahlhebel (3).

Herkunft der Zahlen: V = Vorgabe (Familie/Schnittstelle, BASIC-02 Pilot v2.1 bzw. `basic.common`), A = Annahme (Entwurf 0.17),
G = gemessen; Zahlen ohne Kennung sind A (Entwurf 0.17, an den Renders r1–r3 gesichtet).
Maße mm; f nach vorn, u nach oben, x nach links; Socket_Hand = (0, 0, 0).
"""
import math

from basic.arms.ego import GRIPS as _EGO
from basic.common import (part, prof, box, cyl, rot, cut_box, screws, mirror, rail, selector, charging_handle, grip_v21,
                          holo_kasten, rifle_mag, R_BODY, R_MID, R_SMALL, R_FINE)
from basic.variant import collect

META = dict(id='EXTENDED-02', num='E02', sheet_id='EA02', type='pulse_rifle', type_de='Impulsgewehr', type_en='Pulse Rifle',
            family='BASIC', name='Cadence', nick='Taktgeber', ammo='primary', fire='burst', burst=3,
            reference_length_m=0.703, reference_length_source='A: Entwurf 0.17 (Bullpup; BASIC-02 0,86 m als Rahmen, V)',
            inspired_by='BASIC-02 Familie; Formgen v1 Bullpup (f02) als Haltung',
            summary='Impulsgewehr als Bullpup-Monoblock mit Parallelogramm-Silhouette und drei Taktschlitzen (EXTENDED-Reihe).')
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

BORE = 100           # V: Laufachse wie BASIC-02
TOP = 130            # A: Oberkante Kolbendeck = Unterkante Schiene; Visierlinie über H4 64 mm über der Laufachse (Vertrag 60–80)
CH_TOP = 124         # A: Oberkante Kammerhaube, 6 mm unter dem Kolbendeck (Stufe an der schrägen Fuge, Runde 2)
SPLIT = 86           # A: Fuge Creme/Graphit am Vorderteil (Vorderkammer 44 mm Creme über 24 mm Graphit)
LOW = 8              # A: Unterkante Kolben
FRONT_LOW = 62       # A: Unterkante Vorderschaft
HALF = 23.0          # A: halbe Breite der Schale (BASIC-02 44, V, plus 1 mm je Seite für die Schulterfasen)
LEAN = 15.0          # V: Neigung des Griffs BGM-1; hier für Kolben, Stirn, Schlitze, Fuge und Magazin (Leitmerkmal)
T = math.tan(math.radians(LEAN))
SHOULDER = (8.0, 10.0)   # A: Schulterfase (quer, hoch) → Deck oben 2 × (HALF − 8) = 30 mm


def butt(u):
    """A: Kolbenlinie, unten f −300 (Länge), oben 33 mm weiter vorn."""
    return -300 + (u - LOW) * T


def front(u):
    """A: Stirnlinie, unten f 330 (Unterkante Vorderschaft), oben 18,8 mm weiter vorn."""
    return 330 + (u - FRONT_LOW) * T


def seam(u):
    """A: schräge Fuge zwischen Kolbenblock (Creme) und Fahrgestell (Graphit) hinter dem Magazinschacht."""
    return -206 + (u - LOW) * T


def step(u):
    """A (Runde 2): schräge Fuge zwischen Kolbenschale und Kammerhaube über dem Fahrgestellende."""
    return 92 + (u - SPLIT) * T


def lean_poly(f0, width, u0, u1):
    """Parallelogramm mit LEAN: Unterkante f0 … f0 + width bei u0, Oberkante um (u1 − u0)·T nach vorn versetzt."""
    d = (u1 - u0) * T
    return [(f0, u0), (f0 + width, u0), (f0 + width + d, u1), (f0 + d, u1)]


def shoulders(f0, f1, half, top, size=SHOULDER):
    """Schulterfasen als Querprofil-Schneidkörper (beidseitig) über f0 … f1."""
    dx, du = size
    return [dict(shape='xprof', pts=[(sx * (half - dx), top), (sx * half, top - du), (sx * (half + 20), top - du),
                                     (sx * (half + 20), top + 20), (sx * (half - dx), top + 20)][::sx], f0=f0, f1=f1, cu=0)
            for sx in (1, -1)]


# Taktschlitze (A, Runde 3): drei Parallelogramme quer durch die Kammer, Unterkante 8 mm unter der Fuge (Graphit), oben offen durch
# die Haube (Runde 2 endeten sie 8 mm unter der Haube und lasen sich von oben als Taschen); Teilung 40 mm, Breite 15 mm. Die Spulen
# sitzen auf der Laufachse in der Schlitzmitte und sind von oben und von der Seite sichtbar.
SLOT_F = (184, 224, 264)
SLOTS = [lean_poly(f, 15, SPLIT - 8, CH_TOP + 6) for f in SLOT_F]
SLOT_CUTS = [dict(shape='prof', pts=s, w=80) for s in SLOTS]
COIL_F = [f + 7.5 + (BORE - (SPLIT - 8)) * T for f in SLOT_F]
# Kolbenpaneele (A): Parallelogramm in der Kolbenflanke, 16 mm hinter der Kolbenlinie, 14 mm vor der Fuge
PANEL = (24, 84)
PANEL_POLY = [(butt(PANEL[0]) + 16, PANEL[0]), (seam(PANEL[0]) - 14, PANEL[0]), (seam(PANEL[1]) - 14, PANEL[1]),
              (butt(PANEL[1]) + 16, PANEL[1])]
WINDOW = (34, 74)                       # A (Runde 2): Taktfenster im linken Paneel, 40 × 50 mm
WIN_F0 = butt(WINDOW[0]) + 22
WIN_W = 50


def inset(poly, d):
    """Parallelogramm um d nach innen (Rahmen, Glas)."""
    (a, u0), (b, _), (_, u1), _ = poly
    return [(a + d, u0 + d), (b - d, u0 + d), (b - d + (u1 - u0 - 2 * d) * T, u1 - d), (a + d + (u1 - u0 - 2 * d) * T, u1 - d)]


WIN = lean_poly(WIN_F0, WIN_W, *WINDOW)

P = []
# ---------------------------------------------------------------- Kolbenschale (Kolben, Verschluss, Deck) und Kammerhaube
P += [
    prof('upper', 'Kolbenschale', 'Butt shell', 'receiver', 'shell',
         'Kolben, Verschluss und Deck in einem Teil; trägt Schiene, Paneele und Taktfenster',
         'auf dem Fahrgestell, Fuge schräg hinter dem Schacht (zwei Querbolzen)',
         [(butt(LOW), LOW), (seam(LOW), LOW), (seam(SPLIT), SPLIT), (step(SPLIT), SPLIT), (step(TOP), TOP), (butt(TOP), TOP)],
         2 * HALF, bevel=R_BODY,
         cuts=shoulders(-320, 160, HALF, TOP)
         + [dict(shape='prof', pts=inset(PANEL_POLY, -1.0), w=6, x=sx * HALF) for sx in (1, -1)]      # Paneelmulden 3 mm
         + [dict(shape='prof', pts=inset(WIN, -0.2), w=14, x=HALF)]                                    # Fensterschacht bis x 16
         + [dict(shape='prof', pts=lean_poly(-172, 52, 92, 116), w=18, x=-HALF)]),                     # Auswurffenster rechts
    prof('chamber', 'Kammerhaube', 'Chamber hood', 'barrel', 'shell',
         'Haube über Lauf und Impulsspulen; 6 mm unter dem Kolbendeck, drei Taktschlitze',
         'an Kolbenschale und Vorderschaft geschraubt, schräge Fuge 1 mm',
         [(step(SPLIT) + 1, SPLIT), (front(SPLIT), SPLIT), (front(CH_TOP), CH_TOP), (step(CH_TOP) + 1, CH_TOP)], 2 * HALF - 2,
         bevel=R_MID,   # A (Runde 4): R_BODY ließ die Haubensegmente zwischen den Schlitzen wie lose Kissen wirken
         cuts=shoulders(60, 380, HALF - 1, CH_TOP) + SLOT_CUTS
         + [dict(shape='prof', pts=[(100, 100), (158, 100), (158, 112), (100, 112)], w=10, x=HALF - 1)]),   # Ladehebel-Nut links
    prof('lower', 'Fahrgestell', 'Chassis', 'receiver', 'graphite', 'Griffmodul, Abzugsgruppe, Magazinschacht',
         'unter der Schale; Schacht angeformt, steigt am Griff und vor dem Abzugsbügel',
         [(seam(LOW) + 1, LOW), (-116, LOW), (-104, 26), (-60, 36), (-24, 40), (88, 40), (98, 62), (100, 62), (100, SPLIT),
          (seam(SPLIT) + 1, SPLIT)], 2 * HALF - 2, bevel=R_MID,
         cuts=[dict(shape='prof', pts=lean_poly(-176, 42, LOW - 2, LOW + 34), w=28)]),                  # Schacht von unten
    prof('mag_well', 'Schachtlippe', 'Magazine well lip', 'receiver', 'trim', 'Blanke Einführkante des Magazinschachts',
         'unten am Schacht des Fahrgestells', lean_poly(-179, 48, LOW - 3, LOW + 0.5), 2 * HALF - 1, bevel=0.6, iface='BMW-R',
         cuts=[dict(shape='prof', pts=lean_poly(-176, 42, LOW - 4, LOW + 2), w=28)]),
    prof('side_panel_r', 'Kolbenpaneel rechts', 'Butt panel right', 'receiver', 'anodized', 'Wartungsdeckel über dem Antrieb',
         'in die Mulde geschraubt (4 Schrauben)', PANEL_POLY, 1.2, bevel=R_FINE, x=-HALF + 0.8),
    part('panel_screws', 'Paneelschrauben', 'Panel screws', 'receiver', 'multi', 'trim', 'Halten das rechte Paneel', 'im Paneel',
         bevel=0.2, items=screws([(PANEL_POLY[0][0] + 6, PANEL[0] + 6), (PANEL_POLY[1][0] - 6, PANEL[0] + 6),
                                  (PANEL_POLY[3][0] + 6, PANEL[1] - 6), (PANEL_POLY[2][0] - 6, PANEL[1] - 6)], -HALF + 0.2, r=1.6, h=0.8)),
    prof('window_panel', 'Fensterpaneel', 'Window panel', 'receiver', 'anodized', 'Trägt das Taktfenster; Wartungsdeckel links',
         'in die Mulde geschraubt (2 Schrauben)', PANEL_POLY, 1.2, bevel=R_FINE, x=HALF - 0.8,
         cuts=[dict(shape='prof', pts=inset(WIN, -1.4), w=4, x=HALF)]),
    part('window_screws', 'Fensterschrauben', 'Window screws', 'receiver', 'multi', 'trim', 'Halten das linke Paneel', 'im Paneel',
         bevel=0.2, items=screws([(PANEL_POLY[0][0] + 6, PANEL[0] + 5), (PANEL_POLY[2][0] - 6, PANEL[1] - 5)], HALF + 0.2, r=1.6, h=0.8)),
    prof('window_frame', 'Fensterrahmen', 'Window frame', 'receiver', 'trim', 'Blanker Rahmen des Taktfensters',
         'um das Fenster im Paneel geschraubt', inset(WIN, -3.6), 1.6, bevel=0.5, x=HALF + 0.4,
         cuts=[dict(shape='prof', pts=inset(WIN, -0.2), w=6, x=HALF)]),
    prof('window_lens', 'Fensterglas', 'Window glass', 'receiver', 'glass', 'Schützt die Leuchtbalken', 'im Rahmen',
         inset(WIN, -0.6), 0.6, bevel=0, x=HALF - 1.2),
    prof('window_back', 'Fenstergrund', 'Window well', 'receiver', 'dark_metal', 'Dunkler Grund hinter den Leuchtbalken',
         'im Fensterschacht, 5 mm hinter dem Glas', inset(WIN, -1.0), 1.0, bevel=0, x=16.5),
]
# Salvenanzeige (Blickfang): drei schräge Leuchtbalken im Taktfenster, je Schuss einer
_bar = lambda i: lean_poly(WIN_F0 + 5 + 15 * i, 10, WINDOW[0] + 5, WINDOW[1] - 5)   # noqa: E731 – A: Balken 10 mm, Teilung 15
P += [part(f'burst_{i + 1}', f'Salvenanzeige {i + 1}', f'Burst pip {i + 1}', 'receiver', 'prof', 'energy',
           f'Leuchtet beim {i + 1}. Impuls der Salve', 'im Taktfenster hinter dem Glas', bevel=0.3, pts=_bar(i), w=1.4,
           x=18.0, move=dict(kind='glow', pivot=None, event='fire', max=5.0)) for i in range(3)]
# Deck: Wangenauflage, Schiene, Visier H4
P += [
    prof('cheek_rest', 'Wangenauflage', 'Cheek rest', 'stock', 'rubber', 'Anlage für die Wange auf dem Kolbendeck',
         'auf das Deck geklebt', [(-232, TOP - 1), (-146, TOP - 1), (-150, TOP + 3.5), (-228, TOP + 3.5)], 22, bevel=R_SMALL),
    prof('butt_pad', 'Kolbenkappe', 'Butt pad', 'stock', 'rubber', 'Rutschfeste Anlage an der Schulter, um LEAN geneigt',
         'auf das Kolbenende gesteckt', [(butt(LOW + 2) + 1, LOW + 2), (butt(TOP - 2) + 1, TOP - 2), (butt(TOP - 2) - 8, TOP - 4),
                                        (butt(TOP - 6) - 11, TOP - 8), (butt(LOW + 6) - 11, LOW + 6), (butt(LOW + 4) - 8, LOW + 2)],
         2 * HALF - 4, bevel=R_MID,
         cuts=[cut_box(butt(20 + 14 * i) - 14, butt(20 + 14 * i) - 8, 20 + 14 * i, 23 + 14 * i, 60) for i in range(7)]),
]
P += [dict(p, mat='anodized') for p in rail(-92, 18, TOP)]
P[-1]['cuts'] = [cut_box(-86 + 12 * i, -80 + 12 * i, TOP + 4, TOP + 9, 30) for i in range(9)]
_sight, SIGHT_ANCHORS = holo_kasten(-60, TOP + 8, weapon_type='pulse_rifle')
P += _sight
# Verschluss im Auswurffenster rechts (hinter dem Griff, Bullpup)
P += [
    box('bolt_carrier', 'Verschlussträger', 'Bolt carrier', 'mechanism', 'metal', 'Lädt und verriegelt; läuft je Impuls zurück',
        'in der Schale geführt', -240, -96, 94, 116, 26, bevel=R_SMALL, cuts=[cut_box(-170, -112, 100, 110, 4, x=-13)],
        move=dict(kind='translate', pivot=(-150, 104, 0), vector_mm=(-30, 0, 0), event='fire')),
    prof('port_cover', 'Auswurfklappe', 'Ejection port cover', 'mechanism', 'anodized', 'Deckt das Auswurffenster ab',
         'Scharnier an der Unterkante', lean_poly(-172, 52, 92, 116), 1.6, bevel=R_FINE, x=-HALF - 0.6,
         move=dict(kind='rotate', pivot=(-140, 92, -HALF - 1), axis='f', range_deg=(0, 75), event='fire',
                   expect=((-140 + 24 * T, 116, -HALF - 1), (0, 0, -1)))),
]
# ---------------------------------------------------------------- Vorderschaft, Stirn, Lauf, Spulen, Mündung
P += [
    prof('handguard', 'Vorderschaft', 'Forend', 'support', 'graphite',
         'Griffbereich der Stützhand unter der Vorderkammer; Handstopp-Lippe unter der Stirn', 'am Fahrgestell und an der Schale, Fuge',
         [(101, FRONT_LOW), (298, FRONT_LOW), (306, FRONT_LOW - 10), (front(FRONT_LOW - 10), FRONT_LOW - 10), (front(SPLIT), SPLIT),
          (101, SPLIT)], 2 * HALF - 2, bevel=R_MID, cuts=SLOT_CUTS),
    prof('handguard_grip', 'Griffpolster', 'Grip pad', 'support', 'rubber', 'Rutschfeste Zone für die Stützhand',
         'unten auf den Vorderschaft geklebt', [(176, FRONT_LOW - 3.5), (288, FRONT_LOW - 3.5), (288, FRONT_LOW + 2), (176, FRONT_LOW + 2)],
         34, bevel=R_SMALL),
    prof('face_plate', 'Stirnplatte', 'Face plate', 'barrel', 'anodized', 'Stirnschild um die Laufbuchse; zweite Schicht',
         'auf die Stirn geschraubt, 1,5 mm vorstehend',
         [(front(FRONT_LOW - 6) - 4, FRONT_LOW - 6), (front(FRONT_LOW - 6) + 1.5, FRONT_LOW - 6), (front(CH_TOP - 6) + 1.5, CH_TOP - 6),
          (front(CH_TOP - 6) - 4, CH_TOP - 6)], 34, bevel=R_SMALL),
    part('front_band', 'Stirnband', 'Front band', 'barrel', 'multi', 'accent', 'Lackiertes Schrägband parallel zur Stirn (einziges Grafikelement)',
         'lackiert, beidseitig an der Vorderkammer', bevel=0,
         items=[dict(shape='prof', pts=lean_poly(front(SPLIT + 3) - 24, 7, SPLIT + 3, CH_TOP - 11), w=0.6, x=sx * (HALF - 0.95))
                for sx in (1, -1)]),
    part('text_r', 'Schriftzug', 'Lettering', 'barrel', 'text', 'decal', 'Kennung „BASIC  EX-02“ (einzige Schrift)',
         'aufgedruckt', bevel=0, text='BASIC  EX-02', size=4.4, f=108, u=102.5, x=-HALF + 0.95, side=-1, depth=0.12),
    part('chamber_screws', 'Haubenschrauben', 'Hood screws', 'barrel', 'multi', 'trim', 'Halten Kammerhaube und Vorderschaft',
         'seitlich vor den Taktschlitzen', bevel=0.2, items=mirror(screws([(170, 92), (170, 108)], HALF - 1.2, r=1.7, h=0.8))),
    part('takedown_pins', 'Querbolzen', 'Takedown pins', 'receiver', 'multi', 'metal', 'Verbinden Schale und Fahrgestell',
         'quer durch das Fahrgestell (lösbar)', bevel=0.4, items=mirror(screws([(-104, 74), (82, 74)], HALF - 1, r=3.6, h=1.0))),
    cyl('barrel', 'Lauf', 'Barrel', 'barrel', 'metal', 'Führt das Geschoss; kanneliert', 'im Verschlussgehäuse verschraubt',
        'f', (BORE, 0), -100, 352, 8, segs=24,
        cuts=[cut_box(140, 240, BORE - 1.4, BORE + 1.4, 4, x=sx * 8) for sx in (1, -1)]),
    part('pulse_coils', 'Impulsspulen', 'Pulse coils', 'barrel', 'multi', 'dark_metal',
         'Formen die Dreier-Salve; je Taktschlitz eine', 'auf den Lauf gepresst', bevel=0.5, smooth=True,
         items=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=f - 3.5, a1=f + 2.5, r=15, r_in=8, segs=32) for f in COIL_F]),   # V: r 15 wie BASIC-02
    part('coil_rings', 'Spulenringe', 'Coil rings', 'barrel', 'multi', 'trim', 'Blanke Stirnringe der Spulen', 'an den Spulen',
         bevel=0.3, smooth=True,
         items=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=f + 2.4, a1=f + 4.4, r=15.6, r_in=12, segs=32) for f in COIL_F]),
    cyl('bushing', 'Laufbuchse', 'Barrel bushing', 'barrel', 'trim', 'Führt den Lauf in der Stirn; blanke Stufe',
        'in die Stirnplatte gepresst', 'f', (BORE, 0), front(BORE) - 6, front(BORE) + 5, 13, r_in=8.2, segs=32, bevel=0.5),
    cyl('muzzle', 'Mündung', 'Muzzle', 'barrel', 'anodized', 'Achtkantige Mündungsstufe mit Schlitzen; Socket_Muzzle vorn',
        'auf Laufende geschraubt (lösbar)', 'f', (BORE, 0), front(BORE) + 4, front(BORE) + 36, 12, r_in=5.5, segs=8, bevel=R_SMALL,
        iface='BMZ-15', cuts=[cut_box(front(BORE) + 12 + 7 * i, front(BORE) + 16 + 7 * i, BORE + 5, BORE + 16, 10) for i in range(3)]),
    cyl('muzzle_tip', 'Mündungsspitze', 'Muzzle tip', 'barrel', 'dark_metal', 'Zweite, schmalere Stufe', 'vorn auf der Mündung',
        'f', (BORE, 0), front(BORE) + 36, front(BORE) + 50, 9.5, r_in=5, segs=8, bevel=R_SMALL),
    cyl('muzzle_crown', 'Mündungskrone', 'Muzzle crown', 'barrel', 'trim', 'Blanke Stirnkante', 'vorn an der Spitze',
        'f', (BORE, 0), front(BORE) + 49, front(BORE) + 54, 9, r_in=5.5, segs=8, bevel=0.6),
]
# ---------------------------------------------------------------- Griff, Bedienung (BGM-1), Magazin hinter dem Griff
P += grip_v21(top=40)
P += selector(8, 64, x=HALF - 0.5)
P += [dict(p, id='selector_r', de='Feuerwahlhebel rechts', en='Fire selector right', x=-HALF + 0.5) for p in selector(8, 64)]
P += charging_handle(122, 106, x=HALF - 0.5, travel=22)
P.append(part('mag_release', 'Magazinhalter', 'Magazine release', 'grip_controls', 'cyl', 'accent', 'Löst das Magazin',
              'Druckknopf links vor dem Schacht', bevel=R_FINE, axis='x', c=(-118, 24), a0=HALF - 3, a1=HALF + 2, r=5, segs=20,
              move=dict(kind='translate', pivot=(-118, 24, HALF), vector_mm=(0, 0, -2.5), event='reload')))
_mf, _mu, _tilt = -175, 40, -LEAN   # A: Schacht f −175 … −135, Oberkante im Schacht u 40, Magazin um LEAN geneigt (unten nach hinten)
_mc = (_mf + 20, _mu)
_m = rifle_mag(_mf, _mu, depth=40, length=104, tilt=_tilt, w=24, curve=0)
for p in _m:
    if p['id'] == 'magazine':
        p['de'], p['func'] = 'Magazin', 'Hält die Patronen; gerade, um LEAN geneigt; entnehmbar'
        p['cuts'] = ([dict(shape='prof', pts=rot([(_mf + 6, uu), (_mf + 34, uu), (_mf + 34, uu + 2.2), (_mf + 6, uu + 2.2)], _mc, _tilt),
                           w=3, x=sx * 12) for uu in (-30, -40) for sx in (1, -1)]
                     + [dict(shape='prof', pts=rot([(_mf + 12, 4), (_mf + 30, 4), (_mf + 30, -20), (_mf + 12, -20)], _mc, _tilt), w=8, x=10)])
    if p['id'] == 'magazine_base':
        p['mat'] = 'anodized'
    if p['id'] == 'magazine_round':
        p['mat'] = 'brass'
P += _m
P += [
    part('mag_rounds', 'Patronen im Fenster', 'Visible rounds', 'ammo', 'multi', 'brass', 'Zeigt den Füllstand', 'im Magazin',
         bevel=0.3, parent_part='magazine', smooth=True,
         items=[dict(shape='cyl', axis='f', c=(rot([(_mf + 21, 0 - 5.4 * i)], _mc, _tilt)[0][1], 4 if i % 2 else -2),
                     a0=rot([(_mf + 21, 0 - 5.4 * i)], _mc, _tilt)[0][0] - 13, a1=rot([(_mf + 21, 0 - 5.4 * i)], _mc, _tilt)[0][0] + 13,
                     r=4.4, segs=12) for i in range(4)]),
]
PARTS = P

# ---------------------------------------------------------------- Anker, Weltpunkte, Aktionen
ANCHORS = {
    'Socket_Hand': dict(at=(0, 0, 0), part='grip', note='Haupthand, auf der Griffachse (V: BGM-1)'),
    'Socket_SupportHand': dict(at=(232, 74, 0), part='handguard', note='Mitte Vorderschaft hinter der Handstopp-Lippe'),
    'Socket_Muzzle': dict(at=(front(BORE) + 54, BORE, 0), part='muzzle_crown', note='Stirn der Mündungskrone auf der Laufachse'),
    'Socket_MagWell': dict(at=_mc, part='mag_well', note='Einrastpunkt Magazin (Schnittstelle BMW-R), hinter dem Griff'),
    'Socket_Charge': dict(at=(140, 106, HALF + 4), part='charging_handle', note='Griffpunkt Ladehebel vorn links (Stützhand)'),
}
ANCHORS.update(SIGHT_ANCHORS)
EJECT = dict(at=(-140, 104, -HALF + 2), dir=(0.3, 0.4, -1.0), case='rifle',
             src='A: Mitte Auswurffenster rechts hinter dem Griff (port_cover), Hülse nach rechts, etwas hoch und vorn')
_CONTACT = {'grip': ((-3, -6, -16.5), 'V: Griff BGM-1 wie die Familie'),
            'support': ((232, FRONT_LOW - 3.5, -2), 'A: unter dem Griffpolster, hinter der Handstopp-Lippe'),
            'mag': ((-150, -10, 12.5), 'A: linke Magazinseite hinter dem Griff'),
            'charge': ((140, 106, HALF + 4), 'A: Ladehebel vorn links an der Kammerhaube')}
EGO_GRIPS = {k: dict(g, contact=_CONTACT[k][0], src=_CONTACT[k][1]) for k, g in _EGO.items()}
POINTS = collect(EJECT, EGO_GRIPS, dict(eject='upper', grip='grip', support='handguard_grip'))
ACTIONS = {
    'fire_burst': dict(de='Dreier-Salve (Verschluss, Taktfenster)', frames=24, step=1, keys={
        'trigger': [(0, 0), (2, 1), (16, 1), (19, 0)],
        'burst_1': [(0, 0), (2, 1), (12, 1), (22, 0)], 'burst_2': [(0, 0), (4, 0), (6, 1), (12, 1), (22, 0)],
        'burst_3': [(0, 0), (8, 0), (10, 1), (12, 1), (22, 0)], 'port_cover': [(0, 0), (3, 1), (24, 1)],
        'bolt_carrier': [(0, 0), (2, 0), (3, 1), (5, 0), (6, 0), (7, 1), (9, 0), (10, 0), (11, 1), (13, 0)]},
        events=[(2, 'shot'), (6, 'shot'), (10, 'shot'), (23, 'ready')], view=(0.8, -0.3, 0.45)),
    'reload_empty': dict(de='Nachladen aus leerem Zustand', frames=84, keys={
        'mag_release': [(0, 0), (6, 1), (14, 0)],
        'magazine': [(0, 0), (6, 0), (18, 1), (34, 1), (50, 0)],
        'charging_handle': [(0, 0), (58, 0), (66, 1), (72, 0)],
        'port_cover': [(0, 1), (84, 1)]},
        events=[(18, 'mag_out'), (50, 'mag_seated'), (66, 'charge'), (72, 'ready')]),
}
EXPLODE = {'sight': (0, 110, 0), 'ammo': (-20, -140, 0), 'stock': (-90, 0, 0), 'barrel': (140, 0, 0), 'support': (40, -60, 0),
           'grip_controls': (10, -80, 0), 'mechanism': (0, 0, -90), 'receiver': (0, 0, 0)}
HERO = (0.62, -0.62, 0.40)   # A: Produktbild von links vorn oben – Taktschlitze, Stirn und Taktfenster zur Kamera
