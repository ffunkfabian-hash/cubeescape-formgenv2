"""ZERO-03 „Cascade“ – eigenständiges Sci-Fi-Impulsgewehr der BASIC-Familie (Formgen v2 0.49 „Cascade“, Nutzerwahl P1 mit Schaft S2a).

Eigenes Modell im BALLON-Kit-Vokabular (reines Python, kein bpy). Keine Teile oder Umbauten von BASIC-02, EXTENDED-02, ZERO-01 oder
ZERO-02: aus `basic.common` kommen nur genormte Familienschnittstellen (Griffmodul BGM-1, Holovisier H4 „Kasten“ auf Schiene BRI-22,
Magazin BMW-R, Feuerwahlhebel, Ladehebel-Form, Schraubenköpfe) und Hilfen (`rot`, `cut_box`, `mirror`). Geladen über
`formgen.extended` (Kurzname `z03`), gerendert mit `tools/extended_render.py z03`.

Formsprache (Auswahl: docs/zero.md › ZERO-03)
- Leitmerkmal Staffel: Der Körper fällt in Stufen nach vorn ab – Deck (Gehäuse und Schaft bündig) u 136 → Handschutz u 118 → Nase
  u 108 – und wird mit jeder Stufe schmaler (50 → 40 → 32 mm), in der Seite wie in der Draufsicht; die Unterlinie staffelt mit
  (66 → 70 → 86). Jede Stufenfläche ist eine 45°-Fase; Gehäuse, Handschutz, Schaft und Kappe haben den Stufenquerschnitt (die Flanke
  springt oben 45° ein).
- Drei Impulse in der Form: In der Schaftfuge und in beiden Stufenflächen sitzt je ein Leuchtstreifen, alle drei 45° nach vorn fallend. Bei der Dreier-Salve
  leuchten sie nacheinander von hinten nach vorn auf (Salvenanzeige = Blickfang, eine Leuchtfunktion).
- Silhouette: flaches Deck über die ganze Länge, kein Kamm über dem Gehäuse (Nutzer: Schaft geht nicht nach oben). Der Schaft ist ein
  Creme-Balken mit schräger Graphit-Strebe vom Griff zum Kolbenpfosten; dazwischen ein geschlossenes Daumenloch.
- Zweiton: Creme oben (Gehäuse, Handschutz, Schaftbalken, Magazin) über Graphit unten (Unterteil, Handschutz-Unterteil, Strebe),
  Fuge auf u 88; die Nase ist eloxiert (dritte Stufe, eigene Rolle).
- Grafik: ein Chevronpaar am Handschutz; eine Schrift rechts am Gehäuse.
- Front mehrstufig: Stufenfläche → eloxierte Nase mit 45°-Stirn → blanker Emitterring mit Leuchtspalt → Achtkant-Mündung → Krone.
- Ergonomie: Griff BGM-1 (Socket_Hand 0/0), Stützhand am Handschutz vor dem Handstopp, Ladehebel links vorn, Magazinhalter und
  Feuerwahlhebel links; Akzent-Bedienfunktionen: Ladehebel, Magazinhalter, Feuerwahlhebel (3).

Herkunft der Zahlen: V = Vorgabe (Familie/Schnittstelle, BASIC-02), A = Annahme (Entwurf 0.49), G = gemessen; Zahlen ohne Kennung sind A
(Entwurf 0.49, an Rasterskizzen und Renders gesichtet). Maße mm; f nach vorn, u nach oben, x nach links; Socket_Hand = (0, 0, 0).
"""
from basic.arms.ego import GRIPS as _EGO
from basic.common import (part, prof, box, cyl, rot, cut_box, screws, mirror, rail, selector, charging_handle, grip_v21,
                          holo_kasten, rifle_mag, R_MID, R_SMALL, R_FINE)
from basic.variant import collect

META = dict(id='ZERO-03', num='Z03', sheet_id='ZA03', type='pulse_rifle', type_de='Impulsgewehr', type_en='Pulse Rifle',
            family='BASIC', name='Cascade', nick='Staffel', ammo='primary', fire='burst', burst=3,
            reference_length_m=0.824, reference_length_source='G: Hülle des Datensatzes 0.49 (BASIC-02 0,82 m, EXTENDED-02 0,70 m als Rahmen, V)',
            inspired_by='BASIC-02 und EXTENDED-02 (Familie, Impulsgewehr mit Dreier-Salve); Formideen P1–P4 (Nutzerwahl P1 „Staffel“, Schaft S2a)',
            summary='Impulsgewehr, dessen Körper in drei leuchtenden Stufen nach vorn abfällt, mit Daumenloch-Schaft (ZERO-Reihe).')
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

BORE = 100                    # V: Laufachse wie BASIC-02
TOP = 136                     # A: Deck = Oberkante Gehäuse und Schaft (bündig); Visierlinie über H4 70 über der Laufachse (Stilprüfung R1: Stufen höher)
HG_TOP, NOSE_TOP = 118, 108   # A: zweite und dritte Stufe (je 45°-Fase davor)
BASE = 42                     # V: Unterkante Gehäuse (Griffoberkante BGM-1)
SPLIT = 88                    # A: Zweiton-Fuge Creme/Graphit
HALF, HG_HALF, NOSE_HALF = 25.0, 20.0, 16.0   # A: Breiten der drei Stufen 50 / 40 / 32 (Staffel auch in der Draufsicht; Stilprüfung R1)
F0 = -110                     # A: Gehäuse hinten (Unterteil, Strebenansatz)
STEP1 = (176, 194)            # A: erste Stufenfläche f (Deck → Handschutz, 18 mm)
STEP2 = (334, 348)            # A: zweite Stufenfläche f (Handschutz → Nase)
NOSE_F1 = 432                 # A: Nasenstirn
S0 = -300                     # A: Schaftende vor der Kappe
G1, G2 = (HG_TOP + 2, TOP - 2), (NOSE_TOP + 2, HG_TOP - 2)   # A: Leuchtnuten fast über die volle Stufenfläche (Stilprüfung R1)
LEDGE, HG_LEDGE, STOCK_LEDGE = 116, 106, 120   # A: Höhe der Flankenstufe an Gehäuse, Handschutz, Schaftbalken (3 / 2,5 / 3 mm ein)
SEAM = ((-142, TOP), (-110, 104))   # A: Schaftfuge 45°, fällt nach vorn wie die Stufen (oben → unten; Stilprüfung R1), 6 mm breit
SEAM_W, BEAM_LOW = 6, 104          # A: Fugenbreite; Unterkante Schaftbalken = Oberkante Daumenloch
HG_LOW, NOSE_LOW = 70, 86          # A: Unterlinie staffelt mit (Gehäuse 66 → Handschutz 70 → Nase 86)
STRUT_HALF = 18.0                  # A: Strebe schmaler als der Balken (Rücken zeigt drei Breiten; Stilprüfung R1)
POST = -270                   # A: Vorderkante Kolbenpfosten (Daumenloch hinten)


def chamfer(f0, f1, u, half, d, up=True):
    """45°-Fase an beiden Längskanten oben (up) oder unten, als Querprofil-Schnitt."""
    s = 1 if up else -1
    return [dict(shape='xprof', f0=f0, f1=f1, cu=0, pts=[(sx * (half - d), u + s), (sx * (half + 2), u + s), (sx * (half + 2), u - s * (d + 2))])
            for sx in (1, -1)]


def ledge(f0, f1, u, half, d=3.0):
    """Stufenquerschnitt: Die Flanke springt ab u mit einer 45°-Kante um d nach innen (Staffel auch von vorn); als Querprofil-Schnitt."""
    return [dict(shape='xprof', f0=f0, f1=f1, cu=0, pts=[(sx * (half + 2), u - d - 2), (sx * (half - d), u), (sx * (half - d), 400),
                                                         (sx * (half + 2), 400)]) for sx in (1, -1)]


def face_strip(f_top, u_top, u0, u1, lift):
    """Streifen auf einer 45°-Fläche, die bei (f_top, u_top) oben beginnt und nach vorn unten fällt; u0–u1 Höhe, lift = Abstand zur Fläche."""
    a, b = (f_top + u_top - u1, u1), (f_top + u_top - u0, u0)
    return [a, b, (b[0] + lift, b[1] + lift), (a[0] + lift, a[1] + lift)]


def groove(f_top, u_top, uu, depth):
    """Nut in einer 45°-Stufenfläche (uu = u0, u1), depth < 0 = in den Körper; als Schnitt 1 mm über die Fläche hinaus."""
    return face_strip(f_top, u_top, uu[0], uu[1], depth)


def groove_cut(f_top, u_top, uu, depth=-4.0):
    a, b, c, d = face_strip(f_top, u_top, uu[0], uu[1], depth)
    return dict(shape='prof', pts=[(a[0] + 1, a[1] + 1), (b[0] + 1, b[1] + 1), c, d], w=80)


P = []
# ---------------------------------------------------------------- Gehäuse
P += [
    prof('upper', 'Oberes Gehäuse', 'Upper receiver', 'receiver', 'shell',
         'Trägt Verschluss, Schiene und erste Stufe; hinten die 45°-Schaftfuge, vorn die erste Stufenfläche',
         'auf dem Unteren Gehäuse, Fuge u 88 (zwei Querbolzen)',
         [(F0, SPLIT), (STEP1[1], SPLIT), (STEP1[1], HG_TOP), (STEP1[0], TOP), SEAM[0], SEAM[1]],
         2 * HALF, bevel=R_SMALL,
         cuts=chamfer(SEAM[0][0] - 2, STEP1[0] + 2, TOP, HALF, 8) + ledge(SEAM[0][0] - 2, STEP1[1] + 2, LEDGE, HALF)
         + [groove_cut(STEP1[0], TOP, G1),                                   # Leuchtnut erste Stufe
            cut_box(24, 84, 93, 108, 10, x=-HALF),                          # Auswurffenster rechts (unter der Flankenstufe)
            cut_box(112, 170, 95, 109, 10, x=HALF),                         # Ladehebel-Nut links (unter der Flankenstufe)
            cut_box(-90, -10, 94, 104, 3, x=HALF), cut_box(-90, -10, 94, 104, 3, x=-HALF)]),   # Mulden der Deckleisten
    prof('lower', 'Unteres Gehäuse', 'Lower receiver', 'receiver', 'graphite', 'Griffmodul, Abzugsgruppe, Magazinschacht',
         'unter dem Oberen Gehäuse; Magazintrichter angeformt',
         [(F0, SPLIT), (F0, 46), (F0 + 14, BASE), (70, BASE), (76, 30), (80, 20), (130, 20), (134, 30), (170, 66), (STEP1[1], 66),
          (STEP1[1], SPLIT)], 2 * HALF - 2, bevel=R_MID,
         cuts=chamfer(F0 - 2, STEP1[1] + 2, BASE, HALF - 1, 5, up=False)
         + [cut_box(-90, -20, 56, 80, 3, x=HALF - 1), cut_box(-90, -20, 56, 80, 3, x=-HALF + 1)]),   # Paneelmulden
    prof('mag_well', 'Schachtlippe', 'Magazine well lip', 'receiver', 'trim', 'Blanke Einführkante des Magazintrichters',
         'unten am Trichter', [(80, 17.5), (130, 17.5), (131, 21), (79, 21)], 2 * HALF - 3, bevel=0.6, iface='BMW-R'),
    box('side_panel_l', 'Seitenpaneel links', 'Side panel left', 'receiver', 'anodized', 'Wartungsdeckel der Abzugsgruppe',
        'in die Mulde geschraubt (4 Schrauben)', -88, -22, 58, 78, 1.2, bevel=R_FINE, x=HALF - 2.1),
    box('side_panel_r', 'Seitenpaneel rechts', 'Side panel right', 'receiver', 'anodized', 'Wartungsdeckel der Abzugsgruppe',
        'in die Mulde geschraubt (4 Schrauben)', -88, -22, 58, 78, 1.2, bevel=R_FINE, x=-HALF + 2.1),
    part('panel_screws', 'Paneelschrauben', 'Panel screws', 'receiver', 'multi', 'trim', 'Halten die Seitenpaneele', 'in den Paneelen',
         bevel=0.2, items=mirror(screws([(-83, 62), (-83, 74), (-27, 62), (-27, 74)], HALF - 1.4, r=1.4, h=0.8))),
    part('takedown_pins', 'Querbolzen', 'Takedown pins', 'receiver', 'multi', 'metal', 'Verbinden Ober- und Unterteil',
         'quer durch das Unterteil (lösbar)', bevel=0.4, items=mirror(screws([(-100, 80), (178, 78)], HALF - 0.4, r=3.6, h=1.0))),
    box('deck_strip_l', 'Deckleiste links', 'Deck strip left', 'receiver', 'anodized', 'Zweite Schicht unter der Deckfase; Wartungsdeckel',
        'in die Mulde gesetzt', -88, -12, 95, 103, 1.2, bevel=R_FINE, x=HALF - 0.8),
    box('deck_strip_r', 'Deckleiste rechts', 'Deck strip right', 'receiver', 'anodized', 'Zweite Schicht unter der Deckfase; Wartungsdeckel',
        'in die Mulde gesetzt', -88, -12, 95, 103, 1.2, bevel=R_FINE, x=-HALF + 0.8),
    box('counter_bezel', 'Anzeigenrahmen', 'Counter bezel', 'receiver', 'anodized', 'Fasst die Munitionsanzeige (zum Auge)',
        'auf das Deck geschraubt', -104, -80, TOP - 0.4, TOP + 1.6, 18, bevel=0.6),
    box('ammo_counter', 'Munitionsanzeige', 'Ammo counter', 'receiver', 'energy', 'Füllstand oben, im Blick beim Zielen',
        'im Anzeigenrahmen', -101, -83, TOP + 1.2, TOP + 2.0, 11, bevel=0.2),
    part('mag_release', 'Magazinhalter', 'Magazine release', 'grip_controls', 'cyl', 'accent', 'Löst das Magazin',
         'Druckknopf links am Trichter', bevel=R_FINE, axis='x', c=(64, 52), a0=HALF - 3, a1=HALF + 1.5, r=5, segs=20,
         move=dict(kind='translate', pivot=(64, 52, HALF), vector_mm=(0, 0, -2.5), event='reload')),
    part('text_r', 'Schriftzug', 'Lettering', 'receiver', 'text', 'decal', 'Kennung „BASIC ZP-03“ (einzige Schrift)',
         'aufgedruckt', bevel=0, text='BASIC  ZP-03', size=5.0, f=-96, u=121, x=-HALF + 2.95, side=-1, depth=0.12),
]
# Verschluss im Auswurffenster rechts
P += [
    box('bolt_carrier', 'Verschlussträger', 'Bolt carrier', 'mechanism', 'metal', 'Lädt und verriegelt; läuft je Impuls zurück',
        'im Oberen Gehäuse geführt', -30, 96, 92, 116, 2 * HALF - 6, bevel=R_SMALL, cuts=[cut_box(34, 80, 98, 103, 4, x=-HALF + 3)],
        move=dict(kind='translate', pivot=(30, 104, 0), vector_mm=(-36, 0, 0), event='fire')),
    prof('port_cover', 'Auswurfklappe', 'Ejection port cover', 'mechanism', 'anodized', 'Deckt das Auswurffenster ab',
         'Scharnier an der Unterkante', [(24, 93), (84, 93), (84, 108), (30, 108), (24, 103)], 1.6, bevel=R_FINE, x=-HALF - 0.6,
         move=dict(kind='rotate', pivot=(54, 93, -HALF - 1), axis='f', range_deg=(0, 75), event='fire',
                   expect=((54, 108, -HALF - 1), (0, 0, -1)))),
]
# Schiene und Visier (Familienschnittstelle BRI-22 / H4 „Kasten“ wie BASIC-02)
P += [dict(p, mat='anodized') for p in rail(-76, 20, TOP)]
P[-1]['cuts'] = [cut_box(-70 + 12 * i, -64 + 12 * i, TOP + 4, TOP + 9, 30) for i in range(7)]
_sight, SIGHT_ANCHORS = holo_kasten(-50, TOP + 8, weapon_type='pulse_rifle')
P += _sight
# ---------------------------------------------------------------- Handschutz (zweite Stufe) und Nase (dritte Stufe)
P += [
    prof('hg', 'Handschutz', 'Handguard', 'support', 'shell', 'Zweite Stufe über dem Lauf; vorn die zweite Stufenfläche',
         'in das Obere Gehäuse gesteckt, zwei Schrauben',
         [(STEP1[1], SPLIT), (STEP2[1], SPLIT), (STEP2[1], NOSE_TOP - 4), (STEP2[0], HG_TOP), (STEP1[1], HG_TOP)], 2 * HG_HALF,
         bevel=R_SMALL, cuts=chamfer(STEP1[1] - 2, STEP2[0] + 2, HG_TOP, HG_HALF, 7) + ledge(STEP1[1] - 2, STEP2[1] + 2, HG_LEDGE, HG_HALF, 2.5)
         + [groove_cut(STEP2[0], HG_TOP, G2), cut_box(214, 298, 90, 103, 3, x=HG_HALF), cut_box(214, 298, 90, 103, 3, x=-HG_HALF)]),
    prof('hg_low', 'Handschutz unten', 'Lower handguard', 'support', 'graphite', 'Griffbereich der Stützhand',
         'unter dem Handschutz, am Unteren Gehäuse verschraubt, Fuge u 88',
         [(STEP1[1], SPLIT), (STEP1[1], HG_LOW), (STEP2[1] - 8, HG_LOW), (STEP2[1], HG_LOW + 8), (STEP2[1], SPLIT)], 2 * HG_HALF - 2,
         bevel=R_MID, cuts=chamfer(STEP1[1] - 2, STEP2[1] - 6, HG_LOW, HG_HALF - 1, 4, up=False)),
    box('hg_vent_l', 'Kühlleiste links', 'Cooling strip left', 'support', 'dark_metal', 'Führt Laufwärme seitlich ab',
        'in die Handschutzmulde gesetzt', 216, 296, 91.5, 101.5, 1.2, bevel=R_FINE, x=HG_HALF - 1.6,
        cuts=[cut_box(222 + 12 * i, 230 + 12 * i, 94, 99, 3, x=HG_HALF - 1.6) for i in range(6)]),
    box('hg_vent_r', 'Kühlleiste rechts', 'Cooling strip right', 'support', 'dark_metal', 'Führt Laufwärme seitlich ab',
        'in die Handschutzmulde gesetzt', 216, 296, 91.5, 101.5, 1.2, bevel=R_FINE, x=-HG_HALF + 1.6,
        cuts=[cut_box(222 + 12 * i, 230 + 12 * i, 94, 99, 3, x=-HG_HALF + 1.6) for i in range(6)]),
    prof('hg_pad', 'Griffpolster', 'Grip pad', 'support', 'rubber', 'Rutschfeste Zone für die Stützhand', 'unten auf den Handschutz geklebt',
         [(204, HG_LOW - 3), (306, HG_LOW - 3), (306, HG_LOW + 3), (204, HG_LOW + 3)], 28, bevel=R_SMALL),
    prof('handstop', 'Handstopp', 'Hand stop', 'support', 'graphite', 'Anschlag vor der Stützhand, 45° wie die Stufen',
         'unter den Handschutz geschraubt', [(308, HG_LOW + 1), (330, HG_LOW + 1), (330, 60), (322, 52), (316, 52)], 2 * HG_HALF - 8, bevel=R_SMALL),
    part('hg_screws', 'Handschutzschrauben', 'Handguard screws', 'support', 'multi', 'trim', 'Halten Handschutz und Unterteil', 'seitlich',
         bevel=0.2, items=mirror(screws([(200, 78)], HG_HALF - 0.6, r=1.6, h=0.8)) + mirror(screws([(200, 98)], HG_HALF + 0.2, r=1.6, h=0.8))),
    part('chevron', 'Chevronband', 'Chevron band', 'support', 'multi', 'accent', 'Lackiertes Chevronpaar (einziges Grafikelement)',
         'lackiert, beidseitig vor der Kühlleiste', bevel=0,
         items=[dict(shape='prof', pts=[(f, 93), (f + 6, 93), (f + 12, 97), (f + 6, 101), (f, 101), (f + 6, 97)],
                     w=0.6, x=sx * (HG_HALF + 0.05)) for f in (304, 316) for sx in (1, -1)]),
    prof('nose', 'Nase', 'Nose', 'support', 'anodized', 'Dritte Stufe: Laufführung und Emitterträger; 45°-Stirn',
         'vor den Handschutz geschraubt (zwei Schrauben); Stirn oben und unten 45°',
         [(STEP2[1] - 6, NOSE_LOW), (NOSE_F1 - 8, NOSE_LOW), (NOSE_F1, NOSE_LOW + 8), (NOSE_F1, NOSE_TOP - 8), (NOSE_F1 - 8, NOSE_TOP),
          (STEP2[1] - 6, NOSE_TOP)], 2 * NOSE_HALF,
         bevel=R_SMALL, cuts=chamfer(STEP2[1] - 8, NOSE_F1 + 2, NOSE_TOP, NOSE_HALF, 4) + chamfer(STEP2[1] - 8, NOSE_F1 + 2, NOSE_LOW, NOSE_HALF, 4, up=False)),
    part('nose_screws', 'Nasenschrauben', 'Nose screws', 'support', 'multi', 'trim', 'Halten die Nase am Handschutz', 'seitlich',
         bevel=0.2, items=mirror(screws([(362, 97)], NOSE_HALF - 0.6, r=1.6, h=0.8))),
]
# ---------------------------------------------------------------- Drei Impulse: Leuchtstreifen in Schaftfuge und Stufenflächen (Blickfang)
_GLOW = dict(kind='glow', pivot=None, event='fire', max=5.0)
P += [
    prof('pulse_1', 'Impulsfuge', 'Pulse seam', 'receiver', 'energy', 'Leuchtet beim 1. Impuls der Salve; 45°-Fuge zwischen Schaft und Gehäuse',
         'in der Schaftfuge hinter dem Schaftbalken', [(SEAM[0][0] - SEAM_W, TOP), SEAM[0], SEAM[1], (SEAM[1][0] - SEAM_W, BEAM_LOW)],
         2 * HALF - 7, bevel=0, move=_GLOW, cuts=chamfer(SEAM[0][0] - SEAM_W - 2, SEAM[1][0] + 2, TOP, HALF, 8)),   # bündig mit der Deckfase (Stilprüfung R2)
    prof('pulse_2', 'Erste Impulsstufe', 'First pulse step', 'receiver', 'energy', 'Leuchtet beim 2. Impuls der Salve',
         'in einer Nut der ersten Stufenfläche, quer ganz durch (45°-Lichtlinie auch in der Seite)', groove(STEP1[0], TOP, G1, -3.5), 2 * HALF - 7, bevel=0,
         move=_GLOW),
    prof('pulse_3', 'Zweite Impulsstufe', 'Second pulse step', 'support', 'energy', 'Leuchtet beim 3. Impuls der Salve',
         'in einer Nut der zweiten Stufenfläche, quer ganz durch', groove(STEP2[0], HG_TOP, G2, -3.5), 2 * HG_HALF - 6,
         bevel=0, move=_GLOW),
    part('step_caps', 'Stufenkanten', 'Step edges', 'receiver', 'multi', 'trim', 'Blanke Kanten an den Oberkanten der Stufenflächen',
         'auf die Stufenkante gesetzt', bevel=0.3,
         items=[dict(shape='prof', pts=face_strip(STEP1[0], TOP, TOP - 2.4, TOP - 0.4, 0.8), w=2 * HALF - 18),
                dict(shape='prof', pts=face_strip(STEP2[0], HG_TOP, HG_TOP - 2.4, HG_TOP - 0.4, 0.8), w=2 * HG_HALF - 16)]),
]
# ---------------------------------------------------------------- Lauf, Emitter und Mündung
_E = NOSE_F1 + 2              # A: Emitterring direkt vor der Nasenstirn
P += [
    cyl('barrel', 'Lauf', 'Barrel', 'barrel', 'metal', 'Führt den Impuls; kanneliert', 'im Oberen Gehäuse verschraubt',
        'f', (BORE, 0), 150, _E + 46, 7, segs=24,
        cuts=[cut_box(_E + 18, _E + 34, BORE - 1.2, BORE + 1.2, 4, x=sx * 7) for sx in (1, -1)]),
    cyl('emitter_ring', 'Emitterring', 'Emitter ring', 'barrel', 'trim', 'Blanker Ring vor der Nase; fasst den Leuchtspalt',
        'auf den Lauf geschraubt', 'f', (BORE, 0), _E, _E + 14, 14, r_in=7.2, segs=32, bevel=0.6,
        cuts=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=_E + 5, a1=_E + 9, r=15, r_in=12.5, segs=32)]),
    cyl('emitter_glow', 'Emitterspalt', 'Emitter gap', 'barrel', 'energy', 'Leuchtet mit der Salve (Austritt des Impulses)',
        'im Emitterring', 'f', (BORE, 0), _E + 5.2, _E + 8.8, 12.8, r_in=8, segs=32, move=_GLOW),
    cyl('muzzle', 'Mündung', 'Muzzle', 'barrel', 'anodized', 'Achtkant-Mündung mit Seitenfenstern; Socket_Muzzle',
        'auf Laufende geschraubt (lösbar)', 'f', (BORE, 0), _E + 40, _E + 74, 12, r_in=5, segs=8, bevel=R_SMALL, iface='BMZ-15',
        cuts=[cut_box(_E + 48, _E + 66, BORE - 4, BORE + 4, 30), cut_box(_E + 50, _E + 64, BORE + 5, BORE + 16, 6)]),
    cyl('muzzle_crown', 'Mündungskrone', 'Muzzle crown', 'barrel', 'trim', 'Blanke Stirnkante', 'vorn an der Mündung',
        'f', (BORE, 0), _E + 72, _E + 78, 11, r_in=5.5, segs=8, bevel=0.6),
]
# ---------------------------------------------------------------- Griff und Bedienung (Familienschnittstelle BGM-1)
P += grip_v21(top=BASE)
P += selector(8, 64, x=HALF + 0.5)
P += [dict(p, id='selector_r', de='Feuerwahlhebel rechts', en='Fire selector right', x=-HALF - 0.5) for p in selector(8, 64)]
P += charging_handle(150, 102, x=HALF + 0.5, travel=36)
# ---------------------------------------------------------------- Magazin: gerade, 8° nach vorn geneigt, Fenster (Familie)
_mc, _tilt = (105, 70), 8       # A: Magazin vor dem Bügel wie BASIC-02
_m = rifle_mag(86, 70, depth=38, length=128, tilt=_tilt, w=24)
for p in _m:
    if p['id'] == 'magazine':
        p['pts'] = rot([(86, 70), (124, 70), (126, 10), (127, -58), (89, -58), (87, 10)], _mc, _tilt)
        p['de'], p['func'] = 'Magazin', 'Hält die Impulspatronen; gerade, nach vorn geneigt; entnehmbar'
        p['cuts'] = ([dict(shape='prof', pts=rot([(96, uu), (120, uu), (120, uu + 2.2), (96, uu + 2.2)], _mc, _tilt), w=3, x=sx * 12)
                      for uu in (-34, -44) for sx in (1, -1)]
                     + [dict(shape='prof', pts=rot([(98, 34), (98, -12), (104, -18), (114, -18), (114, 34)], _mc, _tilt), w=8, x=10)])
    if p['id'] == 'magazine_base':
        p['mat'] = 'anodized'
        p['pts'] = rot([(84, -57.5), (130, -57.5), (130, -66), (124, -70), (84, -70)], _mc, _tilt)
    if p['id'] == 'magazine_round':
        p['mat'] = 'brass'
P += _m
_rounds = []
for i in range(7):
    uu0 = 28 - 6.4 * i
    ff, uu = rot([(106 + (3 if i % 2 else -3), uu0)], _mc, _tilt)[0]
    _rounds.append(dict(shape='cyl', axis='f', c=(uu, 4 if i % 2 else -2), a0=ff - 12, a1=ff + 12, r=4.4, segs=12))
P += [
    part('mag_rounds', 'Patronen im Fenster', 'Visible rounds', 'ammo', 'multi', 'brass', 'Zeigt den Füllstand', 'im Magazin',
         bevel=0.3, parent_part='magazine', items=_rounds, smooth=True),
    prof('mag_rib', 'Magazinrippe', 'Magazine rib', 'ammo', 'graphite', 'Griffkante vorn; trägt die Bodenplatte',
         'vorn am Magazin', rot([(123, 4), (129, 4), (130, -57), (124, -57)], _mc, _tilt), 20, bevel=R_FINE, parent_part='magazine'),
]
# ---------------------------------------------------------------- Schaft S2a: Creme-Balken bündig mit dem Deck, Strebe, Daumenloch
P += [
    prof('stock', 'Schaftbalken', 'Stock beam', 'stock', 'shell', 'Creme-Balken bündig mit dem Deck; trägt die Wangenauflage',
         'hinter der Impulsfuge an das Gehäuse geschraubt (zwei Schrauben)',
         [(S0, BEAM_LOW), (SEAM[1][0] - SEAM_W, BEAM_LOW), (SEAM[0][0] - SEAM_W, TOP), (S0, TOP)], 2 * HALF, bevel=R_MID,
         cuts=chamfer(S0 - 2, SEAM[1][0], TOP, HALF, 8) + ledge(S0 - 2, SEAM[1][0], STOCK_LEDGE, HALF)
         + [cut_box(-250, -170, 105.5, 113.5, 3, x=HALF), cut_box(-250, -170, 105.5, 113.5, 3, x=-HALF)]),
    box('stock_inlay_l', 'Schafteinlage links', 'Stock inlay left', 'stock', 'anodized', 'Zweite Schicht in der Schaftmulde',
        'in die Mulde geklebt', -248, -172, 106.5, 112.5, 1.2, bevel=R_FINE, x=HALF - 0.8),
    box('stock_inlay_r', 'Schafteinlage rechts', 'Stock inlay right', 'stock', 'anodized', 'Zweite Schicht in der Schaftmulde',
        'in die Mulde geklebt', -248, -172, 106.5, 112.5, 1.2, bevel=R_FINE, x=-HALF + 0.8),
    prof('stock_strut', 'Schaftstrebe', 'Stock strut', 'stock', 'graphite',
         'Schräge Strebe vom Griffansatz zum Kolbenpfosten; schließt das Daumenloch', 'am Unteren Gehäuse und unter dem Balken verschraubt',
         [(F0, 46), (F0 - 40, 46), (S0, 70), (S0, BEAM_LOW), (POST, BEAM_LOW), (POST, 84), (F0 - 40, 70), (F0, 70)], 2 * STRUT_HALF,
         bevel=R_MID, cuts=chamfer(S0 - 2, F0, 46, STRUT_HALF, 4, up=False)),
    part('stock_screws', 'Schaftschrauben', 'Stock screws', 'stock', 'multi', 'trim', 'Halten Balken und Strebe', 'seitlich',
         bevel=0.2, items=mirror(screws([(-150, 109)], HALF + 0.2, r=1.8, h=0.8))
         + mirror(screws([(POST - 15, 96), (F0 - 20, 58)], STRUT_HALF + 0.2, r=1.8, h=0.8))),
    part('sling_socket', 'Riemenöse', 'Sling socket', 'stock', 'multi', 'trim', 'Steckaufnahme für den Riemen (beidseitig)',
         'in den Kolbenpfosten gepresst', bevel=0.3,
         items=mirror([dict(shape='cyl', axis='x', c=(S0 + 14, 80), a0=STRUT_HALF - 1.6, a1=STRUT_HALF + 0.2, r=6, r_in=3.4, segs=20)])),
    prof('cheek_rest', 'Wangenauflage', 'Cheek rest', 'stock', 'rubber', 'Anlage für die Wange', 'auf den Schaftbalken geklebt',
         [(-250, TOP - 1), (-170, TOP - 1), (-176, TOP + 4), (-246, TOP + 4)], 26, bevel=R_MID),
    prof('butt_pad', 'Schaftkappe', 'Butt pad', 'stock', 'rubber', 'Rutschfeste Anlage an der Schulter', 'auf Balken und Pfosten gesteckt',
         [(S0 + 1, 66), (S0 + 1, TOP + 2), (S0 - 7, TOP), (S0 - 12, TOP - 7), (S0 - 12, 75), (S0 - 7, 68)], 2 * HALF - 2, bevel=R_MID,
         cuts=[cut_box(S0 - 13, S0 - 8, 80 + 11 * i, 83 + 11 * i, 2 * HALF + 2) for i in range(5)] + ledge(S0 - 14, S0 + 2, STOCK_LEDGE, HALF - 1)),
]
PARTS = P

# ---------------------------------------------------------------- Anker, Weltpunkte, Aktionen
ANCHORS = {
    'Socket_Hand': dict(at=(0, 0, 0), part='grip', note='Haupthand, auf der Griffachse (V: BGM-1)'),
    'Socket_SupportHand': dict(at=(258, 74, 0), part='hg_low', note='Mitte Handschutz hinter dem Handstopp, Stützhand umgreift'),
    'Socket_Muzzle': dict(at=(_E + 78, BORE, 0), part='muzzle_crown', note='Stirnfläche Mündungskrone auf der Laufachse'),
    'Socket_MagWell': dict(at=_mc, part='mag_well', note='Einrastpunkt Magazin (Schnittstelle BMW-R)'),
    'Socket_Charge': dict(at=(166, 102, HALF + 5), part='charging_handle', note='Griffpunkt Ladehebel links vorn'),
}
ANCHORS.update(SIGHT_ANCHORS)
EJECT = dict(at=(54, 100, -HALF + 1), dir=(0.3, 0.4, -1.0), case='rifle',
             src='A: Mitte Auswurffenster rechts (port_cover), Hülse nach rechts, etwas hoch und vorn (wie BASIC-02)')
_CONTACT = {'grip': ((-3, -6, -16.5), 'V: Griff BGM-1 wie die Familie'),
            'support': ((258, HG_LOW, -2), 'A: unter dem Griffpolster, hinter dem Handstopp'),
            'mag': ((116, -18, 12.5), 'A: linke Magazinseite'),
            'charge': ((166, 102, HALF + 5), 'A: Ladehebel links vorn')}
EGO_GRIPS = {k: dict(g, contact=_CONTACT[k][0], src=_CONTACT[k][1]) for k, g in _EGO.items()}
POINTS = collect(EJECT, EGO_GRIPS, dict(eject='upper', grip='grip', support='hg_pad'))
ACTIONS = {
    'fire_burst': dict(de='Dreier-Salve (Verschluss, Impulsstufen von hinten nach vorn)', frames=24, step=1, keys={
        'trigger': [(0, 0), (2, 1), (16, 1), (19, 0)],
        'pulse_1': [(0, 0), (2, 1), (12, 1), (22, 0)], 'pulse_2': [(0, 0), (4, 0), (6, 1), (12, 1), (22, 0)],
        'pulse_3': [(0, 0), (8, 0), (10, 1), (12, 1), (22, 0)],
        'emitter_glow': [(0, 0), (2, 1), (3, 0), (6, 1), (7, 0), (10, 1), (11, 0)],
        'port_cover': [(0, 0), (3, 1), (24, 1)],
        'bolt_carrier': [(0, 0), (2, 0), (3, 1), (5, 0), (6, 0), (7, 1), (9, 0), (10, 0), (11, 1), (13, 0)]},
        events=[(2, 'shot'), (6, 'shot'), (10, 'shot'), (23, 'ready')], view=(0.8, -0.3, 0.45)),
    'reload_empty': dict(de='Nachladen aus leerem Zustand', frames=84, keys={
        'mag_release': [(0, 0), (6, 1), (14, 0)],
        'magazine': [(0, 0), (6, 0), (18, 1), (34, 1), (50, 0)],
        'charging_handle': [(0, 0), (58, 0), (66, 1), (72, 0)],
        'port_cover': [(0, 1), (84, 1)]},
        events=[(18, 'mag_out'), (50, 'mag_seated'), (66, 'charge'), (72, 'ready')]),
}
EXPLODE = {'sight': (0, 110, 0), 'ammo': (30, -140, 0), 'stock': (-110, 0, 0), 'barrel': (150, 0, 0), 'support': (60, -40, 0),
           'grip_controls': (-10, -80, 0), 'mechanism': (0, 0, -90), 'receiver': (0, 0, 0)}
HERO = (0.72, -0.55, 0.42)   # A: Produktbild von links vorn oben – Stufenflächen mit Impulsstreifen und Daumenloch zur Kamera
