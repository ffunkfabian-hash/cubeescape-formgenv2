"""EXTENDED-01 „Spearhead“ – eigenständiges Sci-Fi-Automatikgewehr der BASIC-Familie (Formgen v2 0.15).

Eigenes Modell im BALLON-Kit-Vokabular (reines Python, kein bpy; Formen aus `basic/kit.build_shape`). Keine Teile oder Umbauten von
BASIC-01: aus `basic.common` kommen nur genormte Familienschnittstellen (Griffmodul BGM-1, Holovisier H0 auf Schiene BRI-22,
Feuerwahlhebel, Ladehebel-Form, Schraubenköpfe) und Hilfen (`rot`, `cut_box`, `mirror`). Geladen über `formgen.extended`, gerendert
mit BALLONs unverändertem `tools/blender_build.main` (`tools/extended_render.py`).

Formsprache (Stilhandbuch BALLON §3; Auswahl und Skizzen: docs/extended.md)
- Leitmerkmal: Speerspitze. Die Oberlinie fällt ab dem Gehäuse nach vorn, die Unterlinie steigt vom Handschutz zur Spitze; in der
  Draufsicht verjüngt sich die Klinge von 44 auf 20 mm. Höhe an der Fuge Gehäuse/Klinge 80 mm, vor der Stirnfase (f 500) 27 mm.
- Negativraum: ein durchgehender, nach vorn zulaufender Fuller-Schlitz quer durch die Creme-Klinge zeigt Lauf und Kühlringe vor dem
  Graphitboden des Handschutzes;
  dazu der Dreiecksdurchbruch im Fachwerkschaft mit sichtbarem Puffer.
- Schichten: Mittelrippe (eloxiert) 2,5 mm über der Klinge, Deckplatte 3 mm über dem Gehäuse, Seitenpaneele in Mulden, Kernrahmen
  1,7 mm vorstehend, Munitionsanzeige auf der Deckplatte (zum Auge); Unterteil 1 mm je Seite schmaler als das Oberteil.
- Zweiton: Creme oben (Gehäuse, Klinge, Schaft, Magazin) über Graphit unten (Unterteil, Handschutz); die Trennfuge ist eine Gerade,
  die vom Schaft zur Spitze leicht steigt (Teilung am Gehäuse 58:42, gesamt etwa 65:35).
- Blickfang (genau einer): Energiekern links als langgezogenes Sechseck mit Spitze nach vorn (Speermotiv), Glas, blanker Rahmen.
- Grafik: ein Chevronpaar (Akzent) an der Klingenwurzel vor dem Schlitz, nach vorn zeigend; eine Schrift rechts am Gehäuse.
- Front mehrstufig: Klingenspitze mit Fasen oben/unten und in der Draufsicht, blanke Laufbuchse, kurzer freier Lauf, sechskantiger
  Kompensator mit Schlitzen und blanker Krone.
- Ergonomie: Griff BGM-1 wie die Familie (Socket_Hand 0/0), Handstopp-Sporn unten am Handschutz vor der Stützhand, Gummipolster,
  Ladehebel vorn links (Stützhand), Magazinhalter links; Akzent-Bedienfunktionen: Ladehebel, Magazinhalter, Feuerwahlhebel (3).

Herkunft der Zahlen: V = Vorgabe (Familie/Schnittstelle, BASIC-01 Pilot v2.1 bzw. `basic.common`), A = Annahme (Entwurf 0.15),
G = gemessen; Zahlen ohne Kennung sind A (Entwurf 0.15, an den Renders r1–r3 gesichtet). Maße mm; f nach vorn, u nach oben, x nach links; Socket_Hand = (0, 0, 0).
"""
from basic.arms.ego import GRIPS as _EGO
from basic.common import (part, prof, box, cyl, rot, cut_box, screws, mirror, rail, selector, charging_handle, grip_v21,
                          reflex_sight_v21, rifle_mag, R_BODY, R_MID, R_SMALL, R_FINE)
from basic.variant import collect

META = dict(id='EXTENDED-01', num='E01', type='auto_rifle', type_de='Automatikgewehr', type_en='Auto Rifle', family='BASIC',
            name='Spearhead', nick='Speerspitze', ammo='primary', fire='full_auto',
            reference_length_m=0.901, reference_length_source='A: Entwurf 0.15 (BASIC-01 0,93 m als Rahmen, V)',
            inspired_by='BASIC-01 Familie; Formgen v1 Keil (g02) und Facetten (KJ02) als Haltung',
            summary='Automatikgewehr mit Speerspitzen-Klinge, Fuller-Schlitz und Fachwerkschaft (EXTENDED-Reihe).')
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

BORE = 106           # V: Laufachse wie BASIC-01 (gleiche Griff-Lauf-Geometrie der Familie)
TOP = 142            # A: Oberkante Gehäuse = Unterkante Schiene; Visierlinie TOP + 8 + 26 = 176 → 70 über der Laufachse (Vertrag 60–80)
F_REAR, F_JOIN, F_TIP = -124, 196, 512   # A: Gehäuseende, Fuge Gehäuse/Klinge, Klingenspitze
HALF = 22.0          # V: halbe Gehäusebreite (BASIC-01 Oberteil 44)


def split(f):
    """A: Trennfuge Creme/Graphit, eine Gerade von u 86 (Gehäuseende) bis u 108,3 (Handschutzende f 436)."""
    return 86 + (f - F_REAR) * (108.3 - 86) / (436 - F_REAR)


def top(f):
    """A: Oberlinie der Klinge, fällt von TOP (Fuge) auf u 122 (f 500)."""
    return TOP - (f - F_JOIN) * 20 / (500 - F_JOIN)


def bottom(f):
    """A: Unterlinie des Handschutzes, steigt von u 62 (Fuge) auf u 74 (f 388)."""
    return 62 + (f - F_JOIN) * 12 / (388 - F_JOIN)


def taper(stations, u0, u1, out=60.0):
    """Draufsicht-Verjüngung als Schneidkörper: stations [(f, halbe Breite)…] (nach f geordnet); schneidet beidseitig alles außerhalb.
    Polygone gegen den Uhrzeigersinn in (f, x), wie BALLONs Handschutz (mesh_plan dreht nicht selbst)."""
    left = [(f, w) for f, w in stations] + [(stations[-1][0], out), (stations[0][0], out)]
    right = [(stations[0][0], -out), (stations[-1][0], -out)] + [(f, -w) for f, w in stations[::-1]]
    return [dict(shape='plan', pts=left, u0=u0, u1=u1), dict(shape='plan', pts=right, u0=u0, u1=u1)]


def lozenge(fc, uc, length, height, tip, grow=0.0):
    """Langgezogenes Sechseck mit Spitzen vorn/hinten (Kernmotiv); grow vergrößert gleichmäßig (Rahmen, Glas)."""
    L, H, t = length / 2 + grow * 1.6, height / 2 + grow, tip + grow * 0.6
    return [(fc - L, uc), (fc - L + t, uc - H), (fc + L - t, uc - H), (fc + L, uc), (fc + L - t, uc + H), (fc - L + t, uc + H)]


# Klinge (Draufsicht): A – 44 → 34 an der Handschutzfront, 28 an der Spitzenfase, 20 an der Stirn
BLADE_W = [(F_JOIN - 8, HALF + 0.6), (F_JOIN + 6, HALF), (436, 17.0), (500, 14.0), (F_TIP, 10.0), (F_TIP + 10, 10.0)]
GUARD_W = [(F_JOIN - 8, HALF - 0.4), (F_JOIN + 6, HALF - 1.0), (436, 16.0), (446, 16.0)]   # A: je Seite 1 mm unter der Klinge


def half_blade(f):
    for (f0, w0), (f1, w1) in zip(BLADE_W, BLADE_W[1:]):
        if f0 <= f <= f1:
            return w0 + (w1 - w0) * (f - f0) / (f1 - f0)
    raise ValueError(f)


# Fuller-Schlitz (A, Runde 2): in der Creme-Klinge, Unterkante 3 mm unter der Trennfuge (Graphitboden sichtbar), Oberkante fällt von
# u 130 auf 120 – 30 mm hoch hinten, 13 mm vorn; quer durch, Hintergrund über dem Lauf sichtbar
SLOT_F = (246, 420)
SLOT = [(SLOT_F[0], split(SLOT_F[0]) - 3), (SLOT_F[1], split(SLOT_F[1]) - 3), (SLOT_F[1], 120.0), (SLOT_F[0], 130.0)]
SLOT_CUT = dict(shape='prof', pts=SLOT, w=80)
CORE = dict(fc=62, uc=118, length=72, height=24, tip=16)   # A: Kern links, Fenster f 26–98, u 106–130

P = []
# ---------------------------------------------------------------- Gehäuse
P += [
    prof('upper', 'Oberes Gehäuse', 'Upper receiver', 'receiver', 'shell', 'Tragkörper für Verschluss, Kern, Schiene und Klinge',
         'auf dem Unteren Gehäuse, Trennfuge schräg (zwei Querbolzen)',
         [(F_REAR, split(F_REAR)), (F_JOIN, split(F_JOIN)), (F_JOIN, TOP), (-112, TOP), (F_REAR, 131)], 2 * HALF,
         cuts=[dict(shape='prof', pts=lozenge(**CORE), w=8, x=HALF),                   # Kernfenster links
               cut_box(28, 88, 104, 126, 18, x=-HALF),                                 # Auswurffenster rechts
               cut_box(104, F_JOIN + 1, 121, 133, 10, x=HALF),                         # Ladehebel-Nut links (vorn, Stützhand)
               cut_box(-112, -44, 102, 132, 3.0, x=HALF + 0.6), cut_box(-112, -44, 102, 132, 3.0, x=-HALF - 0.6)]),   # Paneelmulden
    prof('lower', 'Unteres Gehäuse', 'Lower receiver', 'receiver', 'graphite', 'Griffmodul, Abzugsgruppe, Magazinschacht',
         'unter dem Oberen Gehäuse; Magazintrichter angeformt, Front steigt zum Handschutz',
         [(F_REAR, 66), (-66, 42), (70, 42), (78, 30), (82, 20), (142, 20), (148, 30), (182, 58), (F_JOIN, 62),
          (F_JOIN, split(F_JOIN)), (F_REAR, split(F_REAR))], 2 * HALF - 2,
         cuts=[dict(shape='prof', pts=[(-112, 70), (-72, 52), (-40, 52), (-40, 78), (-112, 80)], w=4, x=sx * 21.5) for sx in (1, -1)]
         + [dict(shape='prof', pts=[(150, 46), (172, 62), (186, 66), (186, 84), (150, 84)], w=4, x=sx * 21.5) for sx in (1, -1)]),
    prof('mag_well', 'Schachtlippe', 'Magazine well lip', 'receiver', 'trim', 'Blanke Einführkante des Magazintrichters',
         'unten am Trichter des Unterteils', [(81, 17.5), (143, 17.5), (144, 21), (80, 21)], 43, bevel=0.6, iface='BMW-R'),
    box('side_panel_l', 'Seitenpaneel links', 'Side panel left', 'receiver', 'anodized', 'Wartungsdeckel über dem Verschlussweg',
        'in die Mulde geschraubt (4 Schrauben)', -110, -46, 104, 130, 1.2, bevel=R_FINE, x=HALF - 0.8),
    box('side_panel_r', 'Seitenpaneel rechts', 'Side panel right', 'receiver', 'anodized', 'Wartungsdeckel über dem Verschlussweg',
        'in die Mulde geschraubt (4 Schrauben)', -110, -46, 104, 130, 1.2, bevel=R_FINE, x=-HALF + 0.8),
    part('panel_screws', 'Paneelschrauben', 'Panel screws', 'receiver', 'multi', 'trim', 'Halten die Seitenpaneele', 'in den Paneelen',
         bevel=0.2, items=mirror(screws([(-105, 109), (-105, 125), (-51, 109), (-51, 125)], HALF - 0.2, r=1.6, h=0.8))),
    part('takedown_pins', 'Querbolzen', 'Takedown pins', 'receiver', 'multi', 'metal', 'Verbinden Ober- und Unterteil',
         'quer durch das Unterteil (lösbar)', bevel=0.4, items=mirror(screws([(-108, 78), (166, 78)], HALF - 1, r=3.6, h=1.0))),
    box('top_cover', 'Deckplatte', 'Top cover', 'receiver', 'shell', 'Staubschutz über dem Verschluss; zweite Schicht',
        'auf das Obere Gehäuse gesetzt, Stufe 3 mm', -116, -48, TOP - 1, TOP + 3, 36, bevel=R_SMALL),
    box('top_cover_trim', 'Deckplatten-Kante', 'Top cover trim', 'receiver', 'trim', 'Blanke Zierkante der Deckplatte',
        'vorn an der Deckplatte', -52, -47, TOP - 1, TOP + 3.6, 37, bevel=0.4),
    box('counter_bezel', 'Anzeigenrahmen', 'Counter bezel', 'receiver', 'anodized', 'Fasst die Munitionsanzeige (zum Auge)',
        'auf die Deckplatte geschraubt', -102, -66, TOP + 2.6, TOP + 4.6, 22, bevel=0.6),
    box('ammo_counter', 'Munitionsanzeige', 'Ammo counter', 'receiver', 'energy', 'Füllstand oben, im Blick beim Zielen',
        'im Anzeigenrahmen', -98, -70, TOP + 4.2, TOP + 5.0, 15, bevel=0.2),
    prof('core_glow', 'Energiekern', 'Energy core', 'receiver', 'energy', 'Leuchtende Antriebszelle (Blickfang)', 'hinter dem Kernglas',
         lozenge(**CORE, grow=-1.5), 1.6, bevel=0, x=HALF - 3.4),
    prof('core_lens', 'Kernglas', 'Core lens', 'receiver', 'glass', 'Schützt den Kern', 'im Kernfenster', lozenge(**CORE, grow=-0.4),
         0.6, bevel=0, x=HALF - 1.6),
    prof('core_frame', 'Kernrahmen', 'Core frame', 'receiver', 'trim', 'Fasst das Kernfenster; Spitze nach vorn',
         'um das Kernfenster geschraubt', lozenge(**CORE, grow=3.2), 2.6, bevel=0.6, x=HALF + 0.4,
         cuts=[dict(shape='prof', pts=lozenge(**CORE, grow=0.2), w=10, x=HALF + 0.4)]),
    part('core_screws', 'Rahmenschrauben', 'Frame screws', 'receiver', 'multi', 'dark_metal', 'Halten den Kernrahmen',
         'im Kernrahmen', bevel=0.2, items=screws([(36, 108.4), (36, 127.6), (88, 108.4), (88, 127.6)], HALF + 1.7, r=1.1, h=0.5)),
    part('mag_release', 'Magazinhalter', 'Magazine release', 'grip_controls', 'cyl', 'accent', 'Löst das Magazin',
         'Druckknopf links', bevel=R_FINE, axis='x', c=(66, 60), a0=19, a1=23.5, r=5, segs=20,
         move=dict(kind='translate', pivot=(66, 60, 21), vector_mm=(0, 0, -2.5), event='reload')),
    # A (Runde 3): freie Gehäusefläche rechts zwischen Auswurffenster (88) und Fuge (196); linksbündig, läuft nach vorn bis ≈ 154
    part('text_r', 'Schriftzug', 'Lettering', 'receiver', 'text', 'decal', 'Kennung „BASIC EX-01“ (einzige Schrift)',
         'aufgedruckt', bevel=0, text='BASIC  EX-01', size=5.0, f=118, u=128.5, x=-HALF - 0.05, side=-1, depth=0.12),
]
# Verschluss im Auswurffenster rechts
P += [
    box('bolt_carrier', 'Verschlussträger', 'Bolt carrier', 'mechanism', 'metal', 'Lädt und verriegelt; läuft beim Schuss zurück',
        'im Oberen Gehäuse geführt', -30, 96, 100, 124, 26, bevel=R_SMALL, cuts=[cut_box(36, 82, 108, 116, 4, x=-13)],
        move=dict(kind='translate', pivot=(30, 112, 0), vector_mm=(-42, 0, 0), event='fire')),
    prof('port_cover', 'Auswurfklappe', 'Ejection port cover', 'mechanism', 'anodized', 'Deckt das Auswurffenster ab',
         'Scharnier an der Unterkante', [(28, 104), (88, 104), (88, 126), (34, 126), (28, 120)], 1.6, bevel=R_FINE, x=-HALF - 0.6,
         move=dict(kind='rotate', pivot=(58, 104, -HALF - 1), axis='f', range_deg=(0, 75), event='fire',
                   expect=((58, 126, -HALF - 1), (0, 0, -1)))),
]
# Schiene und Visier (Familienschnittstelle BRI-22 / H0)
P += [dict(p, mat='anodized') for p in rail(-40, 60, TOP)]
P[-1]['cuts'] = [cut_box(-34 + 12 * i, -28 + 12 * i, TOP + 4, TOP + 9, 30) for i in range(8)]
_sight, SIGHT_ANCHORS = reflex_sight_v21(-6, TOP + 8)
P += _sight
# ---------------------------------------------------------------- Klinge, Mittelrippe, Handschutz
P += [
    prof('blade', 'Klinge', 'Blade shroud', 'receiver', 'shell',
         'Speerspitze: Haube über Lauf und Gasweg, verjüngt nach vorn; Fuller-Schlitz zeigt den Lauf',
         'an das Obere Gehäuse geschraubt (Fuge), vorn um die Laufbuchse geschlossen',
         [(F_JOIN, split(F_JOIN)), (436, split(436)), (436, 86), (470, 89), (500, 95), (F_TIP, 101), (F_TIP, 113), (500, top(500)),
          (F_JOIN, TOP)], 2 * HALF, bevel=R_SMALL,
         cuts=[SLOT_CUT] + taper(BLADE_W, 60, 160)),
    prof('spine', 'Mittelrippe', 'Spine rib', 'receiver', 'anodized', 'Versteift die Klinge; Leitlinie bis zur Spitze',
         'auf Gehäuse und Klinge geschraubt, Stufe 2,5 mm',
         [(66, TOP - 1), (F_JOIN, TOP - 1), (492, top(492) - 1), (484, top(484) + 2.5), (F_JOIN, TOP + 2.5), (72, TOP + 2.5)], 14,
         bevel=R_FINE, cuts=taper([(60, 7.4), (F_JOIN, 7.0), (496, 2.6)], 100, 160)),
    part('spine_screws', 'Rippenschrauben', 'Spine screws', 'receiver', 'multi', 'trim', 'Halten die Mittelrippe', 'in der Rippe',
         bevel=0.2, items=[dict(shape='cyl', axis='u', c=(f, 0), a0=(top(f) if f > F_JOIN else TOP) + 2, a1=(top(f) if f > F_JOIN else TOP) + 3,
                                r=1.5, segs=12) for f in (80, 190, 330, 470)]),
    prof('handguard', 'Handschutz', 'Handguard', 'support', 'graphite',
         'Griffbereich der Stützhand; verjüngt nach vorn, Handstopp-Sporn vorn unten', 'an Unterteil und Klinge verschraubt, Fuge',
         [(F_JOIN, 62), (388, bottom(388)), (396, 66), (414, 64), (426, 76), (436, 86), (436, split(436)), (F_JOIN, split(F_JOIN))],
         2 * HALF - 2, bevel=R_MID, cuts=[SLOT_CUT] + taper(GUARD_W, 40, 140)),
    prof('handguard_grip', 'Griffpolster', 'Grip pad', 'support', 'rubber', 'Rutschfeste Zone für die Stützhand',
         'unten auf den Handschutz geklebt', [(226, bottom(226) - 2), (350, bottom(350) - 2), (350, bottom(350) + 3), (226, bottom(226) + 3)],
         32, bevel=R_SMALL),
    part('handguard_screws', 'Handschutzschrauben', 'Handguard screws', 'support', 'multi', 'trim', 'Halten den Handschutz',
         'seitlich', bevel=0.2, items=mirror(screws([(206, 74), (206, 90)], HALF - 1.2, r=1.8, h=0.8))),
    part('chevron', 'Chevronband', 'Chevron band', 'receiver', 'multi', 'accent', 'Lackiertes Chevronpaar (einziges Grafikelement)',
         'lackiert, beidseitig an der Klingenflanke', bevel=0,
         items=[dict(shape='prof', pts=[(f, 106), (f + 9, 106), (f + 21, 119), (f + 9, 132), (f, 132), (f + 12, 119)],
                     w=0.6, x=sx * (half_blade(f + 10.5) + 0.05)) for f in (204, 222) for sx in (1, -1)]),
]
# ---------------------------------------------------------------- Lauf, Kühlringe, Mündung
P += [
    cyl('barrel', 'Lauf', 'Barrel', 'barrel', 'metal', 'Führt das Geschoss; kanneliert', 'im Oberen Gehäuse verschraubt',
        'f', (BORE, 0), 150, 548, 10, segs=24,
        cuts=[cut_box(518, 538, BORE - 1.5, BORE + 1.5, 4, x=sx * 10) for sx in (1, -1)]
        + [cut_box(518, 538, BORE + 8.6, BORE + 12, 3), cut_box(518, 538, BORE - 12, BORE - 8.6, 3)]),
    part('heatsink', 'Kühlringe', 'Heat sink', 'barrel', 'multi', 'dark_metal', 'Führt Laufwärme ab; im Fuller-Schlitz sichtbar',
         'auf den Lauf gepresst', bevel=0.4, smooth=True,
         items=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=262 + 34 * i, a1=270 + 34 * i, r=12.5, segs=24) for i in range(5)]),
    cyl('nose_bushing', 'Laufbuchse', 'Barrel bushing', 'barrel', 'trim', 'Führt den Lauf in der Klingenspitze; blanke Stufe',
        'in die Klingenspitze gepresst', 'f', (BORE, 0), F_TIP - 4, F_TIP + 3, 12.5, r_in=10.2, segs=24, bevel=0.5),
    cyl('muzzle', 'Kompensator', 'Compensator', 'barrel', 'anodized', 'Sechskant-Mündungsteil mit Schlitzen; Socket_Muzzle',
        'auf Laufende geschraubt (lösbar)', 'f', (BORE, 0), 540, 598, 16, r_in=5.5, segs=6, bevel=R_SMALL, iface='BMZ-15',
        cuts=[cut_box(562 + 10 * i, 568 + 10 * i, BORE + 5, BORE + 22, 12) for i in range(3)]
        + [cut_box(564, 590, BORE - 4, BORE + 4, 44)]
        + [dict(shape='cyl', axis='f', c=(BORE, 0), a0=544 + 4 * i, a1=545.6 + 4 * i, r=18, r_in=15.2, segs=6) for i in range(3)]),
    cyl('muzzle_crown', 'Mündungskrone', 'Muzzle crown', 'barrel', 'trim', 'Blanke Stirnkante', 'vorn am Kompensator',
        'f', (BORE, 0), 596, 604, 14.5, r_in=6, segs=6, bevel=0.6),
]
# ---------------------------------------------------------------- Griff und Bedienung (Familienschnittstelle BGM-1)
P += grip_v21(top=42)
P += selector(8, 70, x=HALF + 0.5)
P += [dict(p, id='selector_r', de='Feuerwahlhebel rechts', en='Fire selector right', x=-HALF - 0.5) for p in selector(8, 70)]
P += charging_handle(164, 127, x=HALF + 0.5, travel=58)
# ---------------------------------------------------------------- Magazin: gerade, 10° nach vorn geneigt, Fenster, Bodenplatte mit Spitze
_mc, _tilt = (108, 72), 10      # A: Neigung 10° (BASIC-01 8° mit Krümmung)
_m = rifle_mag(88, 72, depth=40, length=144, tilt=_tilt, w=24)
for p in _m:
    if p['id'] == 'magazine':
        p['pts'] = rot([(88, 72), (128, 72), (130, 10), (131, -62), (91, -62), (89, 10)], _mc, _tilt)
        p['de'], p['func'] = 'Magazin', 'Hält die Patronen; gerade, nach vorn geneigt; entnehmbar'
        p['cuts'] = ([dict(shape='prof', pts=rot([(98, uu), (124, uu), (124, uu + 2.2), (98, uu + 2.2)], _mc, _tilt), w=3, x=sx * 12)
                      for uu in (-34, -44, -54) for sx in (1, -1)]
                     + [dict(shape='prof', pts=rot([(100, 36), (100, -14), (106, -20), (118, -20), (118, 36)], _mc, _tilt), w=8, x=10)])
    if p['id'] == 'magazine_base':
        p['mat'] = 'anodized'
        p['pts'] = rot([(87, -61.5), (133, -61.5), (150, -67), (138, -73), (87, -73)], _mc, _tilt)
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
# ---------------------------------------------------------------- Schaft: Fachwerk mit sichtbarem Puffer
_sl = lambda f: 136 - (-150 - f) * 10 / 126 if f < -150 else 136   # noqa: E731 – A: Oberkante Schaftrücken, fällt nach hinten
P += [
    box('stock_joint', 'Schaftverbindung', 'Stock joint', 'stock', 'dark_metal', 'Verbindet Schaft und Gehäuse; Verriegelung',
        'Steckverbindung am Gehäuseende', -137, F_REAR + 1, 74, 134, 32, bevel=R_SMALL),
    prof('stock', 'Fachwerkschaft', 'Truss stock', 'stock', 'shell',
         'Dreiecksfachwerk: Rücken in Linie mit dem Gehäuse, Strebe zum Schaftfuß; Durchbruch zeigt den Puffer',
         'an der Schaftverbindung verschraubt',
         [(-136, 80), (-136, 136), (-150, _sl(-150)), (-276, _sl(-276)), (-284, 120), (-284, 26), (-276, 20), (-250, 24)], 34,
         bevel=R_MID, cuts=[dict(shape='prof', pts=[(-154, 92), (-154, 126), (-266, _sl(-266) - 9), (-266, 42), (-252, 40)], w=60)]),
    cyl('buffer_body', 'Puffergehäuse', 'Buffer body', 'stock', 'anodized', 'Rückstoßpuffer in Laufachse, im Durchbruch sichtbar',
        'in der Schaftverbindung', 'f', (BORE, 0), -236, -136, 9, segs=24, bevel=R_FINE,
        cuts=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=-226 + 14 * i, a1=-223 + 14 * i, r=11, r_in=8.2, segs=24) for i in range(4)]),
    cyl('buffer_rod', 'Pufferstange', 'Buffer rod', 'stock', 'trim', 'Kolbenstange des Puffers', 'zwischen Puffer und Schaftkappe',
        'f', (BORE, 0), -268, -234, 3.5, segs=16, bevel=0.4),
    prof('cheek_rest', 'Wangenauflage', 'Cheek rest', 'stock', 'rubber', 'Anlage für die Wange', 'auf den Schaftrücken geklebt',
         [(-256, _sl(-256) - 1), (-176, _sl(-176) - 1), (-180, _sl(-180) + 5), (-252, _sl(-252) + 5)], 24, bevel=R_MID),
    part('stock_screws', 'Schaftschrauben', 'Stock screws', 'stock', 'multi', 'trim', 'Halten den Schaft an der Verbindung',
         'seitlich am Schaft', bevel=0.2, items=mirror(screws([(-144, 90), (-144, 126)], 17.0, r=1.8, h=0.8))),
    prof('butt_pad', 'Schaftkappe', 'Butt pad', 'stock', 'rubber', 'Rutschfeste Anlage an der Schulter', 'auf das Schaftende gesteckt',
         [(-283, 16), (-283, 128), (-292, 126), (-297, 118), (-297, 24), (-292, 18)], 38, bevel=R_MID,
         cuts=[cut_box(-298, -293, 30 + 13 * i, 33 + 13 * i, 44) for i in range(7)]),
]
PARTS = P

# ---------------------------------------------------------------- Anker, Weltpunkte, Aktionen
ANCHORS = {
    'Socket_Hand': dict(at=(0, 0, 0), part='grip', note='Haupthand, auf der Griffachse (V: BGM-1)'),
    'Socket_SupportHand': dict(at=(290, 80, 0), part='handguard', note='Mitte Handschutz hinter dem Handstopp, Stützhand umgreift'),
    'Socket_Muzzle': dict(at=(604, BORE, 0), part='muzzle_crown', note='Stirnfläche Mündungskrone auf der Laufachse'),
    'Socket_MagWell': dict(at=(108, 70, 0), part='mag_well', note='Einrastpunkt Magazin (Schnittstelle BMW-R)'),
    'Socket_Charge': dict(at=(180, 127, HALF + 5), part='charging_handle', note='Griffpunkt Ladehebel vorn links (Stützhand)'),
}
ANCHORS.update(SIGHT_ANCHORS)
EJECT = dict(at=(58, 115, -20), dir=(0.3, 0.4, -1.0), case='rifle',
             src='A: Mitte Auswurffenster rechts (port_cover), Hülse nach rechts, etwas hoch und vorn (wie BASIC-01)')
# Ego-Griffe (A): Richtungen und Fingerstellungen der Familie (basic.arms.ego.GRIPS), Kontaktpunkte auf den Flächen dieses Modells
_CONTACT = {'grip': ((-3, -6, -16.5), 'V: Griff BGM-1 wie die Familie'),
            'support': ((292, bottom(292) - 2, -2), 'A: unter dem Griffpolster, hinter dem Handstopp'),
            'mag': ((120, -18, 12.5), 'A: linke Magazinseite'),
            'charge': ((180, 127, HALF + 5), 'A: Ladehebel vorn links')}
EGO_GRIPS = {k: dict(g, contact=_CONTACT[k][0], src=_CONTACT[k][1]) for k, g in _EGO.items()}
POINTS = collect(EJECT, EGO_GRIPS, dict(eject='upper', grip='grip', support='handguard_grip'))
ACTIONS = {
    'fire_auto': dict(de='Dauerfeuer (Verschluss sichtbar)', frames=30, step=1, keys={
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
EXPLODE = {'sight': (0, 110, 0), 'ammo': (30, -140, 0), 'stock': (-110, 0, 0), 'barrel': (150, 0, 0), 'support': (0, -60, 0),
           'grip_controls': (-10, -80, 0), 'mechanism': (0, 0, -90), 'receiver': (0, 0, 0)}
HERO = (0.78, -0.50, 0.40)   # A: Produktbild von links vorn oben – Kern (Blickfang) und Ladehebel zur Kamera
