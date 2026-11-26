"""ZERO-02 „Facet“ – eigenständiges Sci-Fi-Automatikgewehr der BASIC-Familie (Formgen v2 0.46 „Zero“, Nutzerwahl W4).

Eigenes Modell im BALLON-Kit-Vokabular (reines Python, kein bpy). Keine Teile oder Umbauten von BASIC-01, EXTENDED-01 oder ZERO-01:
aus `basic.common` kommen nur genormte Familienschnittstellen (Griffmodul BGM-1, Holovisier H0 auf Schiene BRI-22, Magazin BMW-R,
Feuerwahlhebel, Ladehebel-Form, Schraubenköpfe) und Hilfen (`rot`, `cut_box`, `mirror`). Geladen über `formgen.extended` (Kurzname
`z02`), gerendert mit `tools/extended_render.py z02`.

Formsprache (Auswahl: docs/zero.md › ZERO-02)
- Leitmerkmal Facettenkeil: Alle Körper haben denselben sechseckigen Querschnitt aus großen ebenen Facetten. Eine untere Schräge, ein
  senkrechtes Mittelband und eine steile obere Schräge, wie ein Tarnkappenrumpf (Formgen v1 Black Ice). Von vorn liest sich die Waffe
  als gestaffelte Sechsecke, nicht als Rechtecke. Eine erhabene blanke Facettenkante auf u 120 läuft als Leitlinie über Schaft, Gehäuse
  und Haube.
- Silhouette: Der Keilschaft steigt nach hinten. Er beginnt mit einer 45°-Facette über dem Gehäuse und endet oben 12 mm höher. Unten
  wächst ein Graphit-Keil zur Schaftkappe, darüber öffnet ein waagerechter Schlitz den Creme-Teil (V1 KJ02 „Keilschaft mit Aussparung“,
  kein Fachwerkdreieck). Gehäuse und Handschutz enden vorn je mit einer Facette.
- Zweiton: Creme oben (Gehäuse, Haube, Schaft, Magazin) über Graphit unten (Unterteil, Handschutz-Unterteil, Schaftkeil). Die Fuge
  liegt an der unteren Facettenkante.
- Blickfang (genau einer): die Leuchtkante links. Über dem Verschluss wird die Leitlinie zu einem Leuchtschacht in der Facettenkante,
  hinter Glas, mit blanken Kappen (Black Ice). Die Stilprüfung R1 verwarf einen liegenden Kern als zu nah an EA01.
- Grafik: ein Chevronpaar im Mittelband vor der Haubennase; eine Schrift rechts im Mittelband des Gehäuses.
- Front mehrstufig: Haubenfacette → blanke Laufbuchse → freier, kannelierter Lauf → Achtkant-Kompensator → blanke Krone.
- Ergonomie: Griff BGM-1 (Socket_Hand 0/0), Stützhand am Handschutz vor dem facettierten Handstopp, Ladehebel links vorn im
  Mittelband, Magazinhalter und Feuerwahlhebel links; Akzent-Bedienfunktionen: Ladehebel, Magazinhalter, Feuerwahlhebel (3).

Herkunft der Zahlen: V = Vorgabe (Familie/Schnittstelle), A = Annahme (Entwurf 0.46), G = gemessen; Zahlen ohne Kennung sind A
(Entwurf 0.46, an Rasterskizzen und Renders gesichtet). Maße mm; f nach vorn, u nach oben, x nach links; Socket_Hand = (0, 0, 0).
"""
from basic.arms.ego import GRIPS as _EGO
from basic.common import (part, prof, box, cyl, rot, cut_box, screws, mirror, rail, selector, charging_handle, grip_v21,
                          reflex_sight_v21, rifle_mag, R_MID, R_SMALL, R_FINE)
from basic.variant import collect

META = dict(id='ZERO-02', num='Z02', sheet_id='ZA02', type='auto_rifle', type_de='Automatikgewehr', type_en='Auto Rifle',
            family='BASIC', name='Facet', nick='Facettenkeil', ammo='primary', fire='full_auto',
            reference_length_m=0.902, reference_length_source='G: Hülle des Datensatzes 0.46 (BASIC-01 0,92 m, EXTENDED-01 0,90 m als Rahmen, V)',
            inspired_by='BASIC-01 und EXTENDED-01 (Familie); Formgen v1 Black Ice KJ02 „Frostbite“ (Facettengehäuse, Keilschaft mit '
                        'Aussparung, Kanten an den Facetten) als Haltung',
            summary='Automatikgewehr aus großen ebenen Facetten mit steigendem Keilschaft (ZERO-Reihe).')
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

BORE = 106                    # V: Laufachse wie BASIC-01
TOP = 142                     # A: Oberkante Gehäuse = Unterkante Schiene; Visierlinie TOP + 8 + 26 = 176 → 70 über der Laufachse
BASE = 42                     # V: Unterkante Gehäuse wie BASIC-01 (Griffoberkante BGM-1)
F0, F1 = -112, 206            # A: Gehäuse hinten / vorn
H1 = 440                      # A: Haubennase
S0 = -300                     # A: Schaftende vor dem Polster
SPLIT = 92                    # A: Zweiton-Fuge an der unteren Facettenkante
BAND = (104, 120)             # A: senkrechtes Mittelband des Gehäuses (Auswurf, Ladehebel, Schrift); oben die Leitlinie u 120
HALF = 26.0                   # A: halbe Breite im Mittelband (52; Oberkante 34, Fuge 48)

# Querschnitte (x, u), cu = 0 – derselbe Sechskant für Gehäuse, Haube und Schaft (A, Entwurf 0.46)
SEC_UP = [(-22, SPLIT), (22, SPLIT), (HALF, BAND[0]), (HALF, BAND[1]), (14, TOP), (-14, TOP), (-HALF, BAND[1]), (-HALF, BAND[0])]
SEC_LO = [(-15, BASE), (15, BASE), (23, 60), (22, SPLIT), (-22, SPLIT), (-23, 60)]
HG_UP = [(-20, 100), (20, 100), (22, 108), (22, 120), (12, 130), (-12, 130), (-22, 120), (-22, 108)]
HG_LO = [(-13, 72), (13, 72), (19, 84), (19, 100), (-19, 100), (-19, 84)]


def facet(pts, w=80, x=0.0):
    """Facetten-Schnitt als Seitenprofil (quer ganz durch)."""
    return dict(shape='prof', pts=pts, w=w, x=x)


def edge(f0, f1, half, sx, u=None):
    """Erhabene blanke Facettenleiste (3 mm hoch, 1,2 mm über der Kante) auf Seite sx in Höhe u (Standard: obere Bandkante)."""
    u = BAND[1] if u is None else u
    return dict(shape='prof', pts=[(f0, u - 1.5), (f1, u - 1.5), (f1, u + 1.5), (f0, u + 1.5)], w=2.4, x=sx * (half + 0.0))


GLOW = (4, 146)               # A: Leuchtkante links in der oberen Facettenkante (Blickfang, Stilprüfung 0.46 R1: kein Kern wie EA01)
P = []
# ---------------------------------------------------------------- Gehäuse
P += [
    part('upper', 'Oberes Gehäuse', 'Upper receiver', 'receiver', 'xprof', 'shell',
         'Facettenkörper: trägt Verschluss, Leuchtkante, Schiene; Mittelband für Auswurf, Ladehebel und Schrift',
         'auf dem Unteren Gehäuse, Fuge an der unteren Facettenkante (zwei Querbolzen)', bevel=R_SMALL, f0=F0, f1=F1, cu=0, pts=SEC_UP,
         cuts=[facet([(150, TOP + 2), (F1 + 2, TOP + 2), (F1 + 2, 120)]),                       # Stirnfacette
               facet([(F0 - 2, TOP + 2), (F0 + 16, TOP + 2), (F0 - 2, 124)]),                    # Heckfacette
               cut_box(GLOW[0] - 4, GLOW[1] + 4, BAND[1] - 5, BAND[1] + 5, 8, x=HALF),         # Leuchtschacht links in der Kante
               cut_box(24, 84, BAND[0] - 2, BAND[1] - 1, 10, x=-HALF),                          # Auswurffenster rechts
               cut_box(120, 198, 107, 117, 10, x=HALF)]),                                       # Ladehebel-Nut links
    part('lower', 'Unteres Gehäuse', 'Lower receiver', 'receiver', 'xprof', 'graphite', 'Griffmodul, Abzugsgruppe, Magazinschacht',
         'unter dem Oberen Gehäuse; Magazintrichter angeformt', bevel=R_MID, f0=F0, f1=F1, cu=0, pts=SEC_LO,
         cuts=[facet([(F0 - 2, 30), (F0 - 2, 72), (F0 + 28, 30)]),                              # Heckfacette unten
               facet([(70, 41), (78, 30), (82, 18), (142, 18), (148, 30), (186, 70), (F1 + 2, 70), (F1 + 2, 10), (60, 10)]),
               cut_box(-90, -20, 66, 86, 3, x=22.9), cut_box(-90, -20, 66, 86, 3, x=-22.9)]),     # Paneelmulden
    prof('funnel', 'Magazintrichter', 'Magazine funnel', 'receiver', 'graphite', 'Führt das Magazin in den Schacht',
         'am Unteren Gehäuse angeformt', [(70, BASE + 2), (78, 30), (82, 20), (142, 20), (148, 30), (160, BASE + 2)], 44, bevel=R_MID),
    prof('mag_well', 'Schachtlippe', 'Magazine well lip', 'receiver', 'trim', 'Blanke Einführkante des Magazintrichters',
         'unten am Trichter', [(81, 17.5), (143, 17.5), (144, 21), (80, 21)], 45, bevel=0.6, iface='BMW-R'),
    box('side_panel_l', 'Seitenpaneel links', 'Side panel left', 'receiver', 'anodized', 'Wartungsdeckel der Abzugsgruppe',
        'in die Mulde geschraubt (4 Schrauben)', -88, -22, 68, 84, 1.2, bevel=R_FINE, x=21.9),
    box('side_panel_r', 'Seitenpaneel rechts', 'Side panel right', 'receiver', 'anodized', 'Wartungsdeckel der Abzugsgruppe',
        'in die Mulde geschraubt (4 Schrauben)', -88, -22, 68, 84, 1.2, bevel=R_FINE, x=-21.9),
    part('panel_screws', 'Paneelschrauben', 'Panel screws', 'receiver', 'multi', 'trim', 'Halten die Seitenpaneele', 'in den Paneelen',
         bevel=0.2, items=mirror(screws([(-83, 72), (-83, 80), (-27, 72), (-27, 80)], 22.3, r=1.4, h=0.8))),
    part('takedown_pins', 'Querbolzen', 'Takedown pins', 'receiver', 'multi', 'metal', 'Verbinden Ober- und Unterteil',
         'quer durch das Unterteil (lösbar)', bevel=0.4, items=mirror(screws([(-100, 80), (192, 80)], 22.6, r=3.6, h=1.0))),
    part('facet_edges', 'Facettenkanten', 'Facet edges', 'receiver', 'multi', 'trim',
         'Erhabene blanke Leisten an den oberen Facettenbrüchen von Schaft, Gehäuse und Haube: eine Leitlinie u 120; links wird sie '
         'über dem Verschluss zur Leuchtkante', 'in die Facettenkante gesetzt, 1,2 mm erhaben', bevel=0.4,
         items=[edge(F0 + 18, 150, HALF, -1), edge(F0 + 18, GLOW[0] - 6, HALF, 1),           # Gehäuse rechts ganz, links bis zum Schacht
                edge(S0 + 12, F0 - 12, 20, 1), edge(S0 + 12, F0 - 12, 20, -1),               # Schaft
                edge(F1 + 6, H1 - 40, 22, 1), edge(F1 + 6, H1 - 40, 22, -1)]),               # Haube
    box('edge_glow', 'Leuchtkante', 'Glow edge', 'receiver', 'energy', 'Leuchtende Facettenkante über dem Verschluss (Blickfang, Black Ice)',
        'im Leuchtschacht hinter Glas', GLOW[0], GLOW[1], BAND[1] - 3, BAND[1] + 3, 1.6, bevel=0, x=HALF - 3.6),
    box('edge_lens', 'Kantenglas', 'Edge lens', 'receiver', 'glass', 'Schützt die Leuchtkante', 'im Leuchtschacht',
        GLOW[0], GLOW[1], BAND[1] - 3.6, BAND[1] + 3.6, 0.6, bevel=0, x=HALF - 2.4),
    part('edge_caps', 'Schachtkappen', 'Channel caps', 'receiver', 'multi', 'trim', 'Fassen den Leuchtschacht an beiden Enden',
         'in den Schacht geschraubt', bevel=0.4,
         items=[dict(shape='box', f0=f, f1=f + 6, u0=BAND[1] - 5.6, u1=BAND[1] + 5.6, w=5, x=HALF - 1.6) for f in (GLOW[0] - 6, GLOW[1])]),
    box('top_cover', 'Deckplatte', 'Top cover', 'receiver', 'shell', 'Staubschutz über dem Verschluss; zweite Schicht',
        'auf das Obere Gehäuse gesetzt, Stufe 3 mm', -94, -52, TOP - 1, TOP + 3, 30, bevel=R_SMALL),
    box('counter_bezel', 'Anzeigenrahmen', 'Counter bezel', 'receiver', 'anodized', 'Fasst die Munitionsanzeige (zum Auge)',
        'auf die Deckplatte geschraubt', -88, -62, TOP + 2.6, TOP + 4.6, 18, bevel=0.6),
    box('ammo_counter', 'Munitionsanzeige', 'Ammo counter', 'receiver', 'energy', 'Füllstand oben, im Blick beim Zielen',
        'im Anzeigenrahmen', -85, -65, TOP + 4.2, TOP + 5.0, 11, bevel=0.2),
    part('mag_release', 'Magazinhalter', 'Magazine release', 'grip_controls', 'cyl', 'accent', 'Löst das Magazin',
         'Druckknopf links am Trichter', bevel=R_FINE, axis='x', c=(66, 54), a0=20, a1=24.5, r=5, segs=20,
         move=dict(kind='translate', pivot=(66, 54, 22), vector_mm=(0, 0, -2.5), event='reload')),
    part('text_r', 'Schriftzug', 'Lettering', 'receiver', 'text', 'decal', 'Kennung „BASIC ZR-02“ (einzige Schrift)',
         'aufgedruckt', bevel=0, text='BASIC  ZR-02', size=5.0, f=-96, u=112, x=-HALF - 0.05, side=-1, depth=0.12),
]
# Verschluss im Auswurffenster rechts
P += [
    box('bolt_carrier', 'Verschlussträger', 'Bolt carrier', 'mechanism', 'metal', 'Lädt und verriegelt; läuft beim Schuss zurück',
        'im Oberen Gehäuse geführt', -30, 96, 100, 122, 26, bevel=R_SMALL, cuts=[cut_box(36, 82, 108, 114, 4, x=-13)],
        move=dict(kind='translate', pivot=(30, 112, 0), vector_mm=(-42, 0, 0), event='fire')),
    prof('port_cover', 'Auswurfklappe', 'Ejection port cover', 'mechanism', 'anodized', 'Deckt das Auswurffenster ab',
         'Scharnier an der Unterkante', [(24, BAND[0] - 2), (84, BAND[0] - 2), (84, BAND[1] - 1), (30, BAND[1] - 1), (24, BAND[1] - 7)], 1.6,
         bevel=R_FINE, x=-HALF - 0.6,
         move=dict(kind='rotate', pivot=(54, BAND[0] - 2, -HALF - 1), axis='f', range_deg=(0, 75), event='fire',
                   expect=((54, BAND[1] - 1, -HALF - 1), (0, 0, -1)))),
]
# Schiene und Visier (Familienschnittstelle BRI-22 / H0)
P += [dict(p, mat='anodized') for p in rail(-48, 72, TOP)]
P[-1]['cuts'] = [cut_box(-42 + 12 * i, -36 + 12 * i, TOP + 4, TOP + 9, 30) for i in range(9)]
_sight, SIGHT_ANCHORS = reflex_sight_v21(-20, TOP + 8)
P += _sight
# ---------------------------------------------------------------- Handschutz (Facettenhaube)
P += [
    part('hg_top', 'Handschutzhaube', 'Handguard hood', 'support', 'xprof', 'shell', 'Facettenhaube über Lauf und Gasweg; Stirnfacette',
         'in das Obere Gehäuse gesteckt, zwei Schrauben', bevel=R_SMALL, f0=F1, f1=H1, cu=0, pts=HG_UP,
         cuts=[facet([(H1 - 34, 132), (H1 + 2, 132), (H1 + 2, 110)])]),
    part('hg_low', 'Handschutz', 'Handguard', 'support', 'xprof', 'graphite', 'Griffbereich der Stützhand; facettierter Handstopp vorn',
         'unter der Haube, am Unteren Gehäuse verschraubt, Fuge', bevel=R_MID, f0=F1, f1=H1 - 8, cu=0, pts=HG_LO,
         cuts=[facet([(H1 - 36, 60), (H1, 60), (H1, 100)]), cut_box(236, 372, 86, 98, 3, x=19.6), cut_box(236, 372, 86, 98, 3, x=-19.6)]),
    box('hg_cover', 'Haubenleiste', 'Hood strip', 'support', 'shell', 'Zweite Schicht auf der oberen Haubenfacette; Leitlinie von oben',
        'auf die Haube geschraubt, Stufe 2 mm', F1 + 20, H1 - 46, 129, 132, 18, bevel=R_FINE),
    prof('handstop', 'Handstopp', 'Hand stop', 'support', 'graphite', 'Facettierter Anschlag vor der Stützhand',
         'unter den Handschutz geschraubt', [(380, 73), (404, 73), (404, 64), (396, 58), (388, 58)], 24, bevel=R_SMALL),
    box('hg_vent_l', 'Kühlleiste links', 'Cooling strip left', 'support', 'dark_metal', 'Führt Laufwärme seitlich ab',
        'in die Handschutzmulde gesetzt', 238, 370, 88, 96, 1.2, bevel=R_FINE, x=17.8, cuts=[cut_box(248, 360, 90.5, 93.5, 3, x=17.8)]),
    box('hg_vent_r', 'Kühlleiste rechts', 'Cooling strip right', 'support', 'dark_metal', 'Führt Laufwärme seitlich ab',
        'in die Handschutzmulde gesetzt', 238, 370, 88, 96, 1.2, bevel=R_FINE, x=-17.8, cuts=[cut_box(248, 360, 90.5, 93.5, 3, x=-17.8)]),
    prof('hg_pad', 'Griffpolster', 'Grip pad', 'support', 'rubber', 'Rutschfeste Zone für die Stützhand', 'unten auf den Handschutz geklebt',
         [(226, 69), (376, 69), (376, 75), (226, 75)], 22, bevel=R_SMALL),
    part('hg_screws', 'Handschutzschrauben', 'Handguard screws', 'support', 'multi', 'trim', 'Halten Haube und Handschutz', 'seitlich',
         bevel=0.2, items=mirror(screws([(216, 92)], 19.4, r=1.6, h=0.8)) + mirror(screws([(216, 113)], 21.8, r=1.6, h=0.8))),
    part('chevron', 'Chevronband', 'Chevron band', 'support', 'multi', 'accent', 'Lackiertes Chevronpaar (einziges Grafikelement)',
         'lackiert, beidseitig im Mittelband vor der Haubennase', bevel=0,
         items=[dict(shape='prof', pts=[(f, 108.5), (f + 6, 108.5), (f + 12, 113), (f + 6, 117.5), (f, 117.5), (f + 6, 113)],
                     w=0.6, x=sx * 22.05) for f in (H1 - 70, H1 - 58) for sx in (1, -1)]),
]
# ---------------------------------------------------------------- Lauf und Mündung
P += [
    cyl('barrel', 'Lauf', 'Barrel', 'barrel', 'metal', 'Führt das Geschoss; kanneliert', 'im Oberen Gehäuse verschraubt',
        'f', (BORE, 0), 150, H1 + 92, 10, segs=24,
        cuts=[cut_box(H1 + 14, H1 + 76, BORE - 1.5, BORE + 1.5, 4, x=sx * 10) for sx in (1, -1)]
        + [cut_box(H1 + 14, H1 + 76, BORE + 8.6, BORE + 12, 3), cut_box(H1 + 14, H1 + 76, BORE - 12, BORE - 8.6, 3)]),
    cyl('nose_bushing', 'Laufbuchse', 'Barrel bushing', 'barrel', 'trim', 'Führt den Lauf in der Haube; blanke Stufe', 'in die Haube gepresst',
        'f', (BORE, 0), H1 - 4, H1 + 6, 13, r_in=10.2, segs=24, bevel=0.5),
    cyl('muzzle', 'Kompensator', 'Compensator', 'barrel', 'anodized', 'Achtkant-Mündungsteil mit Seitenfenstern; Socket_Muzzle',
        'auf Laufende geschraubt (lösbar)', 'f', (BORE, 0), H1 + 84, H1 + 142, 16.5, r_in=5.5, segs=8, bevel=R_SMALL, iface='BMZ-15',
        cuts=[cut_box(H1 + 102, H1 + 130, BORE - 6, BORE + 6, 44), cut_box(H1 + 104, H1 + 128, BORE + 7, BORE + 22, 8)]
        + [dict(shape='cyl', axis='f', c=(BORE, 0), a0=H1 + 88 + 4 * i, a1=H1 + 89.6 + 4 * i, r=18.5, r_in=15.6, segs=8) for i in range(2)]),
    cyl('muzzle_crown', 'Mündungskrone', 'Muzzle crown', 'barrel', 'trim', 'Blanke Stirnkante', 'vorn am Kompensator',
        'f', (BORE, 0), H1 + 140, H1 + 148, 15, r_in=6, segs=8, bevel=0.6),
]
# ---------------------------------------------------------------- Griff und Bedienung (Familienschnittstelle BGM-1)
P += grip_v21(top=BASE)
P += selector(8, 70, x=23.8)
P += [dict(p, id='selector_r', de='Feuerwahlhebel rechts', en='Fire selector right', x=-23.8) for p in selector(8, 70)]
P += charging_handle(164, 112, x=HALF + 0.5, travel=44)
# ---------------------------------------------------------------- Magazin: gerade, 10° nach vorn geneigt, Fenster
_mc, _tilt = (108, 72), 10      # V: wie EXTENDED-01 und ZERO-01 (Familie), Magazin vor dem Bügel
_m = rifle_mag(88, 72, depth=40, length=144, tilt=_tilt, w=24)
for p in _m:
    if p['id'] == 'magazine':
        p['pts'] = rot([(88, 72), (128, 72), (130, 10), (131, -62), (91, -62), (89, 10)], _mc, _tilt)
        p['de'], p['func'] = 'Magazin', 'Hält die Patronen; gerade, nach vorn geneigt; entnehmbar'
        p['cuts'] = ([dict(shape='prof', pts=rot([(98, uu), (124, uu), (124, uu + 2.2), (98, uu + 2.2)], _mc, _tilt), w=3, x=sx * 12)
                      for uu in (-36, -46) for sx in (1, -1)]
                     + [dict(shape='prof', pts=rot([(100, 36), (100, -14), (106, -20), (118, -20), (118, 36)], _mc, _tilt), w=8, x=10)])
    if p['id'] == 'magazine_base':
        p['mat'] = 'anodized'
        p['pts'] = rot([(86, -61.5), (134, -61.5), (134, -70), (128, -74), (86, -74)], _mc, _tilt)
    if p['id'] == 'magazine_round':
        p['mat'] = 'brass'
P += _m
_rounds = []
for i in range(7):
    uu0 = 30 - 6.4 * i
    ff, uu = rot([(109 + (3 if i % 2 else -3), uu0)], _mc, _tilt)[0]
    _rounds.append(dict(shape='cyl', axis='f', c=(uu, 4 if i % 2 else -2), a0=ff - 14, a1=ff + 14, r=4.4, segs=12))
P += [
    part('mag_rounds', 'Patronen im Fenster', 'Visible rounds', 'ammo', 'multi', 'brass', 'Zeigt den Füllstand', 'im Magazin',
         bevel=0.3, parent_part='magazine', items=_rounds, smooth=True),
    prof('mag_rib', 'Magazinrippe', 'Magazine rib', 'ammo', 'graphite', 'Griffkante vorn; trägt die Bodenplatte',
         'vorn am Magazin', rot([(127, 4), (133, 4), (134, -61), (128, -61)], _mc, _tilt), 20, bevel=R_FINE, parent_part='magazine'),
]
# ---------------------------------------------------------------- Keilschaft: steigt nach hinten, schräger Schlitz (V1 KJ02 als Haltung)
_slot = [(-146, 100), (S0 + 40, 100), (S0 + 40, 114), (-146, 114)]   # A: Schlitz waagerecht im Creme-Teil, 14 mm hoch (R1: kein Dreieck)
STOCK_SEC = [(-17, 50), (17, 50), (20, 96), (20, BAND[1]), (12, 154), (-12, 154), (-20, BAND[1]), (-20, 96)]   # A: Sechskant wie Gehäuse,
#    Facettenkante auf derselben Höhe u 120 wie am Gehäuse (eine Leitlinie vom Schaft bis zur Stirnfacette)
P += [
    part('stock', 'Keilschaft', 'Wedge stock', 'stock', 'xprof', 'shell',
         'Keil im selben Sechskant: Oberkante steigt mit 45°-Facette auf 154, Unterkante wächst zur Kappe; Schlitz zeigt den Negativraum',
         'an das Gehäuseende geschraubt (zwei Schrauben)', bevel=R_MID, f0=S0, f1=F0 + 4, cu=0, pts=STOCK_SEC,
         cuts=[facet([(F0 + 6, TOP), (F0 - 8, 156), (F0 + 6, 160)]),                              # 45°-Anstieg über dem Gehäuse
               facet([(F0 + 6, 90), (S0 + 40, 58), (S0 - 2, 58), (S0 - 2, 30), (F0 + 6, 30)]),     # Keil-Unterkante
               facet([(S0 - 2, 146), (S0 + 8, 156), (S0 - 2, 160)]),                              # Fersenfacette oben
               facet([(S0 - 2, 64), (S0 + 8, 56), (S0 - 2, 56)]),                                 # Fersenfacette unten
               facet([(S0 - 2, 96), (F0 + 6, 96), (F0 + 6, 20), (S0 - 2, 20)]),                    # Graphit-Keil darunter
               facet(_slot)]),
    part('stock_heel', 'Schaftkeil', 'Stock wedge', 'stock', 'xprof', 'graphite',
         'Unterer Keil im selben Sechskant; Zweiton-Fuge an der unteren Facettenkante wie am Gehäuse', 'unter den Schaft geschraubt, Fuge',
         bevel=R_MID, f0=S0, f1=F0 + 4, cu=0, pts=[(x * 0.96, u) for x, u in STOCK_SEC],
         cuts=[facet([(F0 + 6, 90), (S0 + 40, 58), (S0 - 2, 58), (S0 - 2, 30), (F0 + 6, 30)]), facet([(S0 - 2, 64), (S0 + 8, 56), (S0 - 2, 56)]),
               facet([(S0 - 2, 96), (F0 + 6, 96), (F0 + 6, 170), (S0 - 2, 170)])]),
    prof('slot_edge', 'Schlitzkante', 'Slot edge', 'stock', 'trim', 'Blanke Kante oben am Schlitz', 'in die Schlitzoberkante gesetzt',
         [(-148, 114), (S0 + 38, 114), (S0 + 38, 116.5), (-148, 116.5)], 41, bevel=0.3),
    prof('stock_joint', 'Schaftverbindung', 'Stock joint', 'stock', 'dark_metal', 'Verbindet Schaft und Gehäuse; Verriegelung',
         'Steckverbindung am Gehäuseende', [(F0 - 10, 94), (F0 + 2, 94), (F0 + 2, 136), (F0 - 10, 136)], 42, bevel=R_SMALL),
    part('stock_screws', 'Schaftschrauben', 'Stock screws', 'stock', 'multi', 'trim', 'Halten den Schaft an der Verbindung', 'seitlich',
         bevel=0.2, items=mirror(screws([(-118, 102), (-118, 128)], 20.6, r=1.8, h=0.8))),
    part('sling_socket', 'Riemenöse', 'Sling socket', 'stock', 'multi', 'trim', 'Steckaufnahme für den Riemen (beidseitig)',
         'in die Kappe gepresst', bevel=0.3, items=mirror([dict(shape='cyl', axis='x', c=(S0 + 16, 72), a0=19.4, a1=21.2, r=6.5, r_in=3.6,
                                                                 segs=20)])),
    prof('cheek_rest', 'Wangenauflage', 'Cheek rest', 'stock', 'rubber', 'Anlage für die Wange', 'auf den Schaftrücken geklebt',
         [(-272, 153), (-150, 153), (-158, 159), (-268, 159)], 24, bevel=R_MID),
    part('butt_pad', 'Schaftkappe', 'Butt pad', 'stock', 'xprof', 'rubber', 'Rutschfeste Anlage an der Schulter; Sechskant wie der Schaft',
         'auf das Schaftende gesteckt', bevel=R_MID, f0=S0 - 12, f1=S0 + 1, cu=0,
         pts=[(-17, 54), (17, 54), (21.5, 96), (21.5, BAND[1]), (13, 157), (-13, 157), (-21.5, BAND[1]), (-21.5, 96)],
         cuts=[cut_box(S0 - 13, S0 - 8, 70 + 12 * i, 73 + 12 * i, 46) for i in range(7)]),
]
PARTS = P

# ---------------------------------------------------------------- Anker, Weltpunkte, Aktionen
ANCHORS = {
    'Socket_Hand': dict(at=(0, 0, 0), part='grip', note='Haupthand, auf der Griffachse (V: BGM-1)'),
    'Socket_SupportHand': dict(at=(300, 74, 0), part='hg_low', note='Mitte Handschutz hinter dem Handstopp, Stützhand umgreift'),
    'Socket_Muzzle': dict(at=(H1 + 148, BORE, 0), part='muzzle_crown', note='Stirnfläche Mündungskrone auf der Laufachse'),
    'Socket_MagWell': dict(at=(108, 70, 0), part='mag_well', note='Einrastpunkt Magazin (Schnittstelle BMW-R)'),
    'Socket_Charge': dict(at=(180, 112, HALF + 5), part='charging_handle', note='Griffpunkt Ladehebel links vorn im Mittelband'),
}
ANCHORS.update(SIGHT_ANCHORS)
EJECT = dict(at=(54, 112, -22), dir=(0.3, 0.4, -1.0), case='rifle',
             src='A: Mitte Auswurffenster rechts (port_cover), Hülse nach rechts, etwas hoch und vorn (wie BASIC-01)')
_CONTACT = {'grip': ((-3, -6, -16.5), 'V: Griff BGM-1 wie die Familie'),
            'support': ((300, 66, -2), 'A: unter dem Griffpolster, hinter dem Handstopp'),
            'mag': ((120, -18, 12.5), 'A: linke Magazinseite'),
            'charge': ((180, 112, HALF + 5), 'A: Ladehebel links vorn im Mittelband')}
EGO_GRIPS = {k: dict(g, contact=_CONTACT[k][0], src=_CONTACT[k][1]) for k, g in _EGO.items()}
POINTS = collect(EJECT, EGO_GRIPS, dict(eject='upper', grip='grip', support='hg_pad'))
ACTIONS = {
    'fire_auto': dict(de='Dauerfeuer (Verschluss im Auswurffenster)', frames=30, step=1, keys={
        'trigger': [(0, 0), (3, 1), (27, 1), (30, 0)], 'port_cover': [(0, 0), (4, 1), (30, 1)],
        'bolt_carrier': [(0, 0), (3, 0), (5, 1), (7, 0), (9, 1), (11, 0), (13, 1), (15, 0), (17, 1), (19, 0), (21, 1), (23, 0)]},
        events=[(3, 'shot'), (7, 'shot'), (11, 'shot'), (15, 'shot'), (19, 'shot')], view=(-0.85, -0.25, 0.45)),
    'reload_empty': dict(de='Nachladen aus leerem Zustand', frames=84, keys={
        'mag_release': [(0, 0), (6, 1), (14, 0)],
        'magazine': [(0, 0), (6, 0), (18, 1), (34, 1), (50, 0)],
        'charging_handle': [(0, 0), (58, 0), (66, 1), (72, 0)],
        'port_cover': [(0, 1), (84, 1)]},
        events=[(18, 'mag_out'), (50, 'mag_seated'), (66, 'charge'), (72, 'ready')]),
}
EXPLODE = {'sight': (0, 110, 0), 'ammo': (30, -140, 0), 'stock': (-110, 0, 0), 'barrel': (150, 0, 0), 'support': (60, -40, 0),
           'grip_controls': (-10, -80, 0), 'mechanism': (0, 0, -90), 'receiver': (0, 0, 0)}
HERO = (0.78, -0.50, 0.40)   # A: Produktbild von links vorn oben – Leuchtkante (Blickfang), Facetten und Ladehebel zur Kamera
