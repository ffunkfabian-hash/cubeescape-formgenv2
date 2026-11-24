"""EXTENDED-08 „Brace“ – eigenständige Sci-Fi-Schrotflinte der BASIC-Familie (Formgen v2 0.23 „Breacher“).

Eigenes Modell im BALLON-Kit-Vokabular (reines Python, kein bpy). Keine Teile oder Umbauten von BASIC-08: aus `basic.common` kommen nur
genormte Familienschnittstellen (Griffmodul BGM-1, Kimme/Korn K2 „Hörner“ auf Schiene BRI-22, Schraubenköpfe) und Hilfen (`cut_box`,
`mirror`). Geladen über `formgen.extended`, gerendert mit BALLONs unverändertem `tools/blender_build.main` (`tools/extended_render.py`).

Formsprache (Stilhandbuch BALLON §3; Auswahl und Skizzen: docs/extended.md)
- Leitmerkmal Brille: zwei Glattläufe liegen nebeneinander (Doppelflinte), eine Pumpe repetiert beide Kammern. Die Streuung liest sich als
  Breite: zwei Bohrungen nebeneinander statt einer Garbe aus einem Trichter. Die Brille kehrt im Querschnitt, im Mündungsjoch und im
  Blickfang (Zwillingsauge) wieder.
- Silhouette: flach und lang (0,78 m), gerade Oberlinie vom Kolben bis zum Joch; der Schiebemantel (Pumpe) ist die große Masse vor dem
  Gehäuse, davor laufen die beiden Läufe frei bis zum Joch.
- Querschnitt: liegendes Stadion mit zwei Bohrungen (Mantel, Joch); Gehäuse 66 mm breit (BASIC-08 42 mm).
- Negativraum: der Brillenspalt, die 12 mm breite Gasse zwischen den freien Läufen vom Mantel bis zum Joch (von oben und unten offen);
  dazu der Hubspalt zwischen Gehäuse und Mantel, in dem Läufe und Führungsstangen frei liegen.
- Blickfang (genau einer): das Zwillingsauge links am Gehäuse, zwei runde Kammeranzeigen in einer Achter-Fassung; je Lauf leuchtet eine.
- Zweiton: Creme oben (Gehäuse, Kammkappe des Kolbens) über Graphit (Unteres Gehäuse, Kolben, Schiebemantel); Joch eloxiert.
- Schichten: Mantel 2 mm unter der Oberlinie, Gummiauflagen 1,2 mm auf den Mantelflanken, Joch 6 mm breiter als die Laufpaare, Paneele in
  Mulden am Kolben, Laufkragen vor dem Gehäuse.
- Grafik: zwei parallele Querstreifen vorn am Gehäuse (beidseitig); eine Schrift rechts am Gehäuse.
- Front mehrstufig: Joch mit Fasen und Kornsockel → zwei blanke Kronen mit dunklen Bohrungen → Brillenspalt → Stirn des Mantels mit
  Handstopp.
- Ergonomie: Griff BGM-1 (Socket_Hand 0/0), Stützhand unter dem Mantel (folgt ihm beim Repetieren), Ladeklappe unten im Ladeschacht,
  Pumpenriegel links unter dem Daumen, Laufwähler oben hinten am Gehäuse (wie der Schieber einer Doppelflinte); Akzent-Bedienfunktionen:
  Pumpenriegel, Laufwähler (2).

Herkunft der Zahlen: V = Vorgabe (Familie/Schnittstelle, BASIC-08 Pilot v2.1 bzw. `basic.common`), A = Annahme (Entwurf 0.23),
G = gemessen; Zahlen ohne Kennung sind A (Entwurf 0.23, an den Renders gesichtet).
Maße mm; f nach vorn, u nach oben, x nach links; Socket_Hand = (0, 0, 0).
"""
import math

from basic.common import part, prof, box, cyl, cut_box, screws, mirror, rail, grip_v21, hoerner, R_MID, R_SMALL, R_FINE
from basic.variant import collect

META = dict(id='EXTENDED-08', num='E08', sheet_id='EA08', type='shotgun', type_de='Schrotflinte', type_en='Shotgun',
            family='BASIC', name='Brace', nick='Brille', ammo='special', fire='pump_action',
            reference_length_m=0.784, reference_length_source='G: Hülle des Datensatzes 0.23 (BASIC-08 0,87 m gemessen als Rahmen, V)',
            inspired_by='BASIC-08 Familie; Formgen v1 F04 „Rubinpumpe“ als Haltung (Läufe nebeneinander)',
            summary='Vorderschaftrepetierflinte mit zwei Läufen nebeneinander im Schiebemantel und Mündungsjoch (EXTENDED-Reihe).')
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

GRIP_TOP = 44            # V: Griffoberkante wie BASIC-08
BORE = 100               # V: Laufachse wie BASIC-08
BX = 18.0                # A: Läufe bei x = ±18 → Brillenspalt 12 mm (Nutzer Welle 1: nicht zu zart)
BAR_R = 12.0             # A: Lauf Ø 24 (BASIC-08 Ø 25, V)
BORE_R = 9.0             # A: Bohrung Ø 18 (Kaliber 12)
SPLIT = 68               # A: Fuge Gehäuse (Creme) / Unteres Gehäuse (Graphit)
UC = 102                 # A: Mitte der Kammerwülste des Gehäuses (Runde 2: Brillen-Querschnitt statt Kasten)
TOP = 120                # A: Oberkante Mittelsteg; Schiene bis 128 = Träger der Kimme (V: BASIC-08 DECK 128, Linie + 11)
DECK = TOP + 8
HALF = 33.0              # A: halbe Gehäusebreite (66 mm: zwei Kammern nebeneinander); Wülste r 15 bis u 117
RF = (-76, 150)          # A: Gehäuse hinten / vorn
PUMP = (214, 434)        # A: Schiebemantel in Ruhelage f0, f1 (Runde 5: 240 → 220 mm)
PUMP_U = (56, 100)       # A: Mantel unten / Mitte der Wülste (Wülste r 17 bis u 117, 3 mm unter dem Steg)
PUMP_HALF = 35.0         # A: halbe Mantelbreite (Läufe außen ±30, Wand 5)
TRAVEL = 56              # A: Hub (BASIC-08 72, V); Mantel bleibt 2 mm vor den Laufkragen (Richter R2: bei 62 lief er 4 mm hinein)
YOKE = (512, 538)        # A: Mündungsjoch f0, f1 (Runde 5: freie Läufe 78 mm)
YOKE_U = (80, 100)       # A: Joch unten / Mitte der Brillenwülste (r 18 bis u 118)
CROWN = YOKE[1] + 2      # Stirn der Kronen
PORT = (26, 92, 80, 106)  # A: Auswurffenster rechts (f0, f1, u0, u1)
GATE = (100, 136)        # A: Ladeklappe im Ladeschacht
EYES = [(-38.0, 85.0), (-14.0, 85.0)]   # A: Zwillingsauge (Mitten der Kammeranzeigen), links auf der Gehäuseflanke, kameranah
EYE_R = 8.0
REC = (-62, 130, SPLIT + 4, UC - 6)   # A: Flankenfeld (f0, f1, u0, u1), 2,4 mm unter den Kammerwülsten (Runde 9: Schulterstufe)
REC_D = 2.4              # A: Tiefe des Flankenfelds (Schichtung 2–3 mm)
FLANK = HALF - REC_D     # Fläche im Flankenfeld (Schrift, Paneele)


def twin(hw, u0, rb, uc, rw=0.0, ru=None, n=16):
    """Brillen-Querschnitt (x, u): Flanken ±hw von u0 (Radius rb unten) bis uc, oben zwei Wülste um (±BX, uc) mit Radius hw − BX,
    die tangential in die Flanken laufen; optional ein Mittelsteg der halben Breite rw bis ru (trägt die Schiene)."""
    rh = hw - BX
    ru = uc if ru is None else ru
    a_in = math.degrees(math.acos(max(-1.0, (rw - BX) / rh))) if rw else 180.0
    pts = [(hw - rb + rb * math.cos(math.radians(270 + 90 * i / n)), u0 + rb + rb * math.sin(math.radians(270 + 90 * i / n))) for i in range(n + 1)]
    pts += [(BX + rh * math.cos(math.radians(a_in * i / n)), uc + rh * math.sin(math.radians(a_in * i / n))) for i in range(n + 1)]
    if rw:
        pts += [(rw, ru), (-rw, ru)]
    pts += [(-BX + rh * math.cos(math.radians(180 - a_in + a_in * i / n)), uc + rh * math.sin(math.radians(180 - a_in + a_in * i / n)))
            for i in range(n + 1)]
    pts += [(-hw + rb + rb * math.cos(math.radians(180 + 90 * i / n)), u0 + rb + rb * math.sin(math.radians(180 + 90 * i / n))) for i in range(n + 1)]
    return pts


def circle(cx, cu, r, n=24):
    return [(cx + r * math.cos(2 * math.pi * i / n), cu + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def bores(r, n=24):
    return [circle(sx * BX, BORE, r, n) for sx in (1, -1)]


P = []
# ---------------------------------------------------------------- Gehäuse (zwei Kammern), Unteres Gehäuse mit Ladeschacht, Mechanik
P += [
    part('upper', 'Gehäuse', 'Upper receiver', 'receiver', 'xprof', 'shell',
         'Breites Verschlussgehäuse; Querschnitt Brille: zwei Kammerwülste und ein Mittelsteg mit der Schiene', 'Grundkörper',
         bevel=R_MID, f0=RF[0], f1=RF[1], cu=0, pts=twin(HALF, SPLIT, 4, UC, rw=8, ru=TOP),   # Runde 3/5: Steg 16 mm zwischen den Kammerwülsten
         cuts=[cut_box(*PORT, 20, x=-HALF),                                                          # Auswurffenster rechts
               cut_box(EYES[0][0] - 13, EYES[1][0] + 13, EYES[0][1] - 12, EYES[0][1] + 12, 3.0, x=HALF + 0.6),   # Mulde der Fassung
               cut_box(*REC, 2 * REC_D, x=HALF), cut_box(*REC, 2 * REC_D, x=-HALF),                   # Flankenfelder (Runde 9)
               dict(shape='prof', pts=[(RF[0] - 1, TOP + 1), (RF[0] + 12, TOP + 1), (RF[0] - 1, TOP - 14)], w=2 * HALF + 2)]   # Heckfase
         + [cut_box(RF[0] + 6, RF[1] + 1, UC - 1.2, UC + 1.2, 3.0, x=sx * (HALF + 0.6)) for sx in (1, -1)]),   # Schulterfuge (Runde 4)
    prof('lower', 'Unteres Gehäuse', 'Lower receiver', 'receiver', 'graphite', 'Griffmodul, Abzug, Ladeschacht mit Ladeklappe',
         'unter dem Gehäuse, Fuge 1 mm', [(RF[0] + 10, SPLIT - 1), (RF[1], SPLIT - 1), (RF[1], 46), (GATE[1] + 6, 34), (GATE[0] - 6, 34),
                                         (GATE[0] - 12, 42), (GATE[0] - 12, GRIP_TOP), (-52, GRIP_TOP), (RF[0] + 10, 58)], 2 * HALF - 4,
         bevel=R_MID),
    box('bolt', 'Verschluss', 'Bolt', 'mechanism', 'metal', 'Doppelverschluss; läuft mit dem Mantel zurück (im Fenster sichtbar)',
        'im Gehäuse geführt', PORT[0] - 4, PORT[1] - 2, 88, 108, 2 * HALF - 14, bevel=R_SMALL,
        move=dict(kind='translate', pivot=((PORT[0] + PORT[1]) / 2, BORE, 0), vector_mm=(-TRAVEL, 0, 0), event='pump',
                  expect=((PORT[1] - 2, BORE, -HALF + 7), (-1, 0, 0)))),
    box('side_panel_r', 'Seitenpaneel rechts', 'Side panel right', 'receiver', 'anodized', 'Wartungsdeckel über dem Schloss',
        'im Flankenfeld verschraubt (4 Schrauben)', -56, 18, 75, 93, 1.2, bevel=R_FINE, x=-FLANK - 0.5),
    box('side_panel_l', 'Seitenpaneel links', 'Side panel left', 'receiver', 'anodized', 'Deckel über dem Kammerwähler',
        'im Flankenfeld verschraubt (4 Schrauben)', 8, 118, 75, 93, 1.2, bevel=R_FINE, x=FLANK + 0.5),
    part('panel_screws', 'Paneelschrauben', 'Panel screws', 'receiver', 'multi', 'trim', 'Halten die Seitenpaneele', 'in den Paneelen',
         bevel=0.2, items=screws([(-52, 78), (-52, 90), (14, 78), (14, 90)], -FLANK - 1.1, r=1.6, h=0.8)
         + screws([(12, 78), (12, 90), (114, 78), (114, 90)], FLANK + 1.1, r=1.6, h=0.8)),
    part('takedown_pins', 'Querbolzen', 'Takedown pins', 'receiver', 'multi', 'metal', 'Verbinden Gehäuse und Unteres Gehäuse',
         'quer durch das Untere Gehäuse (lösbar)', bevel=0.4, items=mirror(screws([(RF[0] + 18, 62), (RF[1] - 10, 60)], HALF - 2, r=3.4, h=1.0))),
    box('loading_gate', 'Ladeklappe', 'Loading gate', 'ammo', 'dark_metal', 'Öffnung unten zum Einschieben einzelner Patronen',
        'im Boden des Ladeschachts (federnd)', GATE[0], GATE[1], 33.4, 35, 30, bevel=R_FINE),
    part('eye_bezel', 'Augenfassung', 'Eye bezel', 'receiver', 'multi', 'trim', 'Blanke Achter-Fassung der beiden Kammeranzeigen',
         'in die Mulde links geschraubt', bevel=0.4,
         items=[dict(shape='cyl', axis='x', c=c, a0=HALF - 2.2, a1=HALF + 0.8, r=EYE_R + 3.2, r_in=EYE_R + 0.4, segs=32) for c in EYES]
         + [dict(shape='box', f0=EYES[0][0], f1=EYES[1][0], u0=EYES[0][1] - EYE_R - 3.2, u1=EYES[0][1] - EYE_R + 0.4, w=3.0, x=HALF - 0.7),
            dict(shape='box', f0=EYES[0][0], f1=EYES[1][0], u0=EYES[0][1] + EYE_R - 0.4, u1=EYES[0][1] + EYE_R + 3.2, w=3.0, x=HALF - 0.7)]),
    part('eye_glass', 'Augenglas', 'Eye glass', 'receiver', 'multi', 'glass', 'Schützt die Kammeranzeigen', 'in der Fassung', bevel=0,
         items=[dict(shape='cyl', axis='x', c=c, a0=HALF - 0.6, a1=HALF - 0.1, r=EYE_R + 0.4, segs=32) for c in EYES]),
    part('chamber_eyes', 'Zwillingsauge', 'Twin eye', 'receiver', 'multi', 'energy',
         'Je Lauf eine Kammeranzeige (geladen leuchtet); Blickfang links', 'unter dem Glas in der Fassung', bevel=0.3,
         items=[dict(shape='cyl', axis='x', c=c, a0=HALF - 2.4, a1=HALF - 0.8, r=EYE_R, segs=32) for c in EYES],
         move=dict(kind='glow', pivot=None, event='fire', max=4.0)),
    cyl('pump_release', 'Pumpenriegel', 'Action release', 'grip_controls', 'accent', 'Gibt den Mantel ohne Schuss frei (Daumen)',
        'Druckknopf links am Unteren Gehäuse', 'x', (70, 60), HALF - 2.5, HALF + 1.5, 4.0, segs=20,
        move=dict(kind='translate', pivot=(70, 60, HALF - 2), vector_mm=(0, 0, -2.0), event='unlock', expect=((70, 60, HALF + 1.5), (0, 0, -1)))),
    prof('barrel_selector', 'Laufwähler', 'Barrel selector', 'grip_controls', 'accent', 'Wählt links, rechts oder beide Läufe (Daumen)',
         'oben hinten auf dem Gehäuse, drehbar', [(RF[0] + 2, TOP - 0.5), (RF[0] + 14, TOP - 0.5), (RF[0] + 12, TOP + 4), (RF[0] + 4, TOP + 4)],
         14, bevel=R_FINE,
         move=dict(kind='rotate', pivot=(RF[0] + 8, TOP, 0), axis='u', range_deg=(-25, 25), event='select',
                   expect=((RF[0] + 14, TOP + 2, 0), (0, 0, 1)))),
    part('band_side', 'Zwillingsstreifen', 'Twin stripes', 'receiver', 'multi', 'accent', 'Zwei lackierte Querstreifen (einziges Grafikelement)',
         'lackiert, beidseitig vorn am Gehäuse', bevel=0,
         items=[dict(shape='prof', pts=[(f, SPLIT + 4), (f + 5, SPLIT + 4), (f + 5, UC - 2), (f, UC - 2)], w=0.3, x=sx * (HALF + 0.15))
                for f in (133, 141) for sx in (1, -1)]),
    part('text_r', 'Schriftzug', 'Lettering', 'receiver', 'text', 'anodized', 'Kennung „BASIC  EX-08“ (einzige Schrift)',
         'aufgedruckt (dunkel auf Creme)', bevel=0, text='BASIC  EX-08', size=4.4, f=PORT[1] + 3, u=79, x=-FLANK - 0.05, side=-1, depth=0.12),
]
P += [dict(p, mat='anodized', attach='auf dem Mittelsteg (fest)') for p in rail(-44, -10, TOP)]   # Runde 5: Schiene nur unter der Kimme, der Creme-Steg trägt die Linie
# ---------------------------------------------------------------- Läufe, Laufkragen, Mündungsjoch (Brille)
P += [
    part('barrel', 'Läufe', 'Barrels', 'barrel', 'multi', 'metal', 'Zwei Glattläufe nebeneinander für Streuschrot', 'im Gehäuse verschraubt',
         bevel=0.3, items=[dict(shape='cyl', axis='f', c=(BORE, sx * BX), a0=RF[1] - 6, a1=CROWN - 1, r=BAR_R, r_in=BORE_R, segs=32)
                           for sx in (1, -1)]),
    part('barrel_collars', 'Laufkragen', 'Barrel collars', 'barrel', 'multi', 'trim', 'Blanke Kragen, wo die Läufe aus dem Gehäuse treten',
         'vorn am Gehäuse auf die Läufe gepresst', bevel=0.4,
         items=[dict(shape='cyl', axis='f', c=(BORE, sx * BX), a0=RF[1] - 1, a1=RF[1] + 6, r=BAR_R + 2.5, r_in=BAR_R - 0.3, segs=32)
                for sx in (1, -1)]),
    part('muzzle', 'Mündungsjoch', 'Muzzle yoke', 'barrel', 'xprof', 'anodized', 'Hält beide Laufenden; trägt den Kornsockel',
         'auf die Laufenden geschraubt (lösbar)', bevel=R_SMALL, f0=YOKE[0], f1=YOKE[1], cu=0, pts=twin(PUMP_HALF + 1, YOKE_U[0], 10, YOKE_U[1], rw=7, ru=YOKE_U[1] + 8),
         cuts=[dict(shape='xprof', f0=YOKE[0] - 1, f1=YOKE[1] + 1, cu=0, pts=h) for h in bores(BAR_R + 0.2)]),
    part('muzzle_crown', 'Mündungskronen', 'Muzzle crowns', 'barrel', 'multi', 'trim', 'Blanke Stirnkanten der beiden Bohrungen',
         'vorn am Joch', bevel=0.5,
         items=[dict(shape='cyl', axis='f', c=(BORE, sx * BX), a0=YOKE[1] - 1, a1=CROWN, r=BAR_R + 1.5, r_in=BORE_R + 0.3, segs=32)
                for sx in (1, -1)]),
    prof('sight_post_base', 'Kornsockel', 'Front sight base', 'barrel', 'anodized', 'Hebt das Korn auf die Höhe der Schiene',
         'auf dem Mittelsteg des Jochs', [(YOKE[0] + 2, YOKE_U[1] + 7), (YOKE[1] - 2, YOKE_U[1] + 7), (YOKE[1] - 4, DECK), (YOKE[0] + 6, DECK)], 14,
         bevel=R_FINE),
]
# ---------------------------------------------------------------- Schiebemantel (Pumpe) mit Gummiauflagen, Handstopp und Führungsstangen
_pm = dict(kind='translate', pivot=((PUMP[0] + PUMP[1]) / 2, 70, 0), vector_mm=(-TRAVEL, 0, 0), event='pump')
P += [
    part('pump', 'Schiebemantel (Pumpe)', 'Pump shroud', 'mechanism', 'xprof', 'graphite',
         'Umschließt beide Läufe und die Röhrenmagazine; die Stützhand repetiert: zurück und vor', 'gleitet auf den Läufen',
         bevel=R_MID, f0=PUMP[0] + 9, f1=PUMP[1] - 11, cu=0, pts=twin(PUMP_HALF, PUMP_U[0], 14, PUMP_U[1], rw=4, ru=PUMP_U[1] + 6),
         cuts=[dict(shape='xprof', f0=PUMP[0], f1=PUMP[1], cu=0, pts=h) for h in bores(BAR_R + 0.4)]
         + [cut_box(PUMP[0] + 24, PUMP[1] - 30, 64, 100, 2 * 1.6, x=sx * PUMP_HALF) for sx in (1, -1)],   # Griffelder (Runde 9)
         move=dict(_pm, expect=((PUMP[0] + 120, PUMP_U[0], 0), (-1, 0, 0)))),
    part('pump_rear', 'Mantelkragen hinten', 'Shroud rear collar', 'mechanism', 'xprof', 'anodized',
         'Hinterkante des Mantels, 1,5 mm über dem Körper, gefast', 'hinten auf den Mantel geschraubt', bevel=R_SMALL,
         f0=PUMP[0], f1=PUMP[0] + 10, cu=0, pts=twin(PUMP_HALF + 1.5, PUMP_U[0] - 1.5, 15, PUMP_U[1], rw=4, ru=PUMP_U[1] + 7.5),
         cuts=[dict(shape='xprof', f0=PUMP[0] - 1, f1=PUMP[0] + 11, cu=0, pts=h) for h in bores(BAR_R + 0.4)], parent_part='pump'),
    part('pump_front', 'Mantelstirn', 'Shroud nose', 'mechanism', 'xprof', 'anodized',
         'Stirn des Mantels: 2,5 mm über dem Körper, Fase zu den Läufen', 'vorn auf den Mantel geschraubt', bevel=R_MID,
         f0=PUMP[1] - 12, f1=PUMP[1], cu=0, pts=twin(PUMP_HALF + 2.5, PUMP_U[0] - 2.5, 16, PUMP_U[1], rw=4, ru=PUMP_U[1] + 8.5),
         cuts=[dict(shape='xprof', f0=PUMP[1] - 13, f1=PUMP[1] + 1, cu=0, pts=h) for h in bores(BAR_R + 0.4)], parent_part='pump'),
    part('pump_pad', 'Griffrippen', 'Grip ribs', 'mechanism', 'multi', 'rubber', 'Drei Längsrippen je Flanke für die Stützhand',
         'in die Griffelder des Mantels geklebt', bevel=0.6, parent_part='pump',
         items=[dict(shape='box', f0=PUMP[0] + 26, f1=PUMP[1] - 32, u0=u, u1=u + 7, w=2.4, x=sx * (PUMP_HALF - 0.4))
                for u in (67, 79, 91) for sx in (1, -1)]),
    box('pump_spine', 'Mittelleiste', 'Shroud spine', 'mechanism', 'anodized', 'Leiste in der Senke zwischen den Wülsten',
        'oben in die Mantelsenke geschraubt', PUMP[0] + 14, PUMP[1] - 16, PUMP_U[1] + 5.5, PUMP_U[1] + 8.5, 8, bevel=R_FINE, parent_part='pump'),
    part('pump_screws', 'Kragenschrauben', 'Collar screws', 'mechanism', 'multi', 'trim', 'Halten Stirn und Hinterkante', 'seitlich an den Kragen',
         bevel=0.2, parent_part='pump',
         items=mirror(screws([(PUMP[0] + 5, 66), (PUMP[0] + 5, 92), (PUMP[1] - 6, 66), (PUMP[1] - 6, 92)], PUMP_HALF + 1.2, r=1.6, h=0.8))),
    prof('pump_stop', 'Handstopp', 'Hand stop', 'mechanism', 'graphite', 'Lippe vorn unter dem Mantel; hält die Stützhand',
         'vorn unter die Mantelstirn angeformt', [(PUMP[1] - 30, PUMP_U[0] + 4), (PUMP[1], PUMP_U[0] + 4), (PUMP[1], PUMP_U[0] - 8),
                                                  (PUMP[1] - 8, PUMP_U[0] - 12), (PUMP[1] - 18, PUMP_U[0] - 10)], 2 * PUMP_HALF - 16,
         bevel=R_SMALL, parent_part='pump'),
    part('action_bars', 'Führungsstangen', 'Action bars', 'mechanism', 'multi', 'metal', 'Übertragen den Mantel auf den Doppelverschluss',
         'am Mantel, laufen ins Gehäuse', bevel=0.3, parent_part='pump',
         items=[dict(shape='box', f0=RF[1] - 6, f1=PUMP[0] + 6, u0=64, u1=70, w=3.0, x=sx * 12) for sx in (1, -1)]),
]
# ---------------------------------------------------------------- Patrone (Laden), Griff, Kolben
P += [
    cyl('shell_round', 'Patrone', 'Shell', 'ammo', 'accent', 'Einzelne Schrotpatrone (beim Laden sichtbar)',
        'wird durch die Ladeklappe in ein Röhrenmagazin geschoben', 'f', (50, 0), GATE[0], GATE[0] + 44, 9.5, bevel=R_FINE, segs=20,
        move=dict(kind='translate', pivot=(GATE[0] + 20, 50, 0), vector_mm=(-24, -58, 0), event='load_shell', removable=True,
                  note='Ruhelage = im Ladeschacht (verdeckt); Aktion beginnt außen unter der Ladeklappe',
                  expect=((GATE[0] + 44, 50, 0), (0, -1, 0)))),
    cyl('shell_head', 'Patronenboden', 'Shell head', 'ammo', 'brass', 'Messingboden der Patrone', 'an der Patrone',
        'f', (50, 0), GATE[0] - 6, GATE[0] + 0.5, 9.8, bevel=0.5, segs=20, parent_part='shell_round'),
]
P += grip_v21(top=GRIP_TOP)
_S0 = RF[0]
L_STOCK = 158            # A: Kolbenlänge bis zur Kappe (Runde 5: 176 → 158, Gesamtlänge 0,79 m)
_SB = _S0 - L_STOCK
# Runde 9 (Koordination: Kolben aus dem Leitmotiv, gestalteter Übergang): Spaltkolben. Ein Hals nimmt die Kammerwülste des Gehäuses auf
# und teilt sich in zwei Wangen, unter jedem Wulst eine; zwischen ihnen bleibt der Kolbenspalt offen – die Brille im Kolben.
SLOT = 12.0              # A: Kolbenspalt, so breit wie der Brillenspalt
CHEEK = 16.0             # A: Wangenbreite je Seite
_CX = SLOT / 2 + CHEEK / 2
_NECK = _S0 - 30         # A: Ende des Halses
_TOPL = [(_NECK, TOP - 8), (_SB, TOP - 10)]                        # A: Kammlinie der Wangen
_BOT = [(_NECK, 58), (_NECK - 34, 64), (_SB + 24, 30), (_SB, 30)]  # A: Unterlinie: Hals steigt, dann fällt sie zur Kolbenspitze (Runde 10)
_CAPH = 16               # A: Höhe der Creme-Kammkappe auf jeder Wange
_cheek = [(_NECK + 1, _TOPL[0][1] - _CAPH - 1), (_SB, _TOPL[1][1] - _CAPH - 1), _BOT[3], _BOT[2], _BOT[1], (_NECK + 1, _BOT[0][1])]
_cap = [(_NECK + 1, _TOPL[0][1]), (_SB, _TOPL[1][1]), (_SB, _TOPL[1][1] - _CAPH), (_NECK + 1, _TOPL[0][1] - _CAPH)]
P += [
    part('stock_neck', 'Kolbenhals', 'Stock neck', 'stock', 'xprof', 'graphite',
         'Übergang vom Gehäuse: nimmt die zwei Kammerwülste auf und teilt sich in die Wangen', 'mit zwei Bolzen an das Gehäuse (fest)',
         bevel=R_MID, f0=_NECK, f1=_S0 + 1, cu=0, pts=twin(HALF - 2, 56, 6, UC - 4, rw=0),
         cuts=[dict(shape='prof', pts=[(_NECK - 1, TOP - 8), (_S0 + 2, TOP - 4), (_S0 + 2, TOP + 20), (_NECK - 1, TOP + 20)], w=80),
               dict(shape='prof', pts=[(_NECK - 1, 30), (_S0 + 2, 30), (_S0 + 2, 56), (_NECK - 1, 58.5)], w=80),
               cut_box(_NECK - 1, _NECK + 14, 40, 130, SLOT)]                          # Spalt beginnt im Hals
         + [dict(shape='plan', pts=[(_NECK - 1, sx * (_CX + CHEEK / 2)), (_S0 - 6, sx * (HALF - 2)), (_S0 - 6, sx * (HALF + 4)),
                                    (_NECK - 1, sx * (HALF + 4))], u0=30, u1=140) for sx in (1, -1)]),   # Hals verjüngt sich zu den Wangen
    part('stock', 'Kolbenkamm', 'Stock comb', 'stock', 'multi', 'shell', 'Creme-Kammkappen der beiden Wangen; Wangenauflage',
         'auf die Wangen geschraubt, Fuge 1 mm', bevel=R_MID, items=[dict(shape='prof', pts=_cap, w=CHEEK, x=sx * _CX) for sx in (1, -1)]),
    part('stock_keel', 'Kolbenwangen', 'Stock cheeks', 'stock', 'multi', 'graphite', 'Zwei Wangen mit offenem Kolbenspalt dazwischen',
         'am Kolbenhals angeformt', bevel=R_MID, items=[dict(shape='prof', pts=_cheek, w=CHEEK, x=sx * _CX) for sx in (1, -1)]),
    prof('butt_pad', 'Kolbenkappe', 'Butt pad', 'stock', 'rubber', 'Rutschfeste Anlage an der Schulter; schließt beide Wangen',
         'auf die Wangenenden gesteckt', [(_SB + 1, 30), (_SB + 1, TOP - 10), (_SB - 6, TOP - 12), (_SB - 10, TOP - 20), (_SB - 10, 38),
                                          (_SB - 6, 31)], 2 * (SLOT / 2 + CHEEK) + 2, bevel=R_MID),
    part('stock_bolts', 'Kolbenbolzen', 'Stock bolts', 'stock', 'multi', 'trim', 'Halten den Hals am Gehäuse', 'quer durch den Kolbenhals',
         bevel=0.3, items=mirror(screws([(_S0 - 12, 90), (_S0 - 12, 66)], HALF - 2 - 0.2, r=2.4, h=1.0))),
    part('cheek_screws', 'Wangenschrauben', 'Cheek screws', 'stock', 'multi', 'trim', 'Halten die Kammkappen', 'außen an den Wangen',
         bevel=0.2, items=mirror(screws([(_NECK - 14, TOP - 16), (_SB + 18, TOP - 18)], _CX + CHEEK / 2 + 0.2, r=1.6, h=0.8))),
]
# ---------------------------------------------------------------- Visier K2 „Hörner“: Kimme auf der Schiene, Korn auf dem Joch
_sight, SIGHT_ANCHORS = hoerner(-36, YOKE[1] - 12, DECK, front_w=12)
P += _sight
PARTS = P

# ---------------------------------------------------------------- Anker, Weltpunkte, Aktionen
_sup = ((PUMP[0] + PUMP[1]) / 2 + 20, PUMP_U[0], 0)
ANCHORS = {
    'Socket_Hand': dict(at=(0, 0, 0), part='grip', note='Haupthand, auf der Griffachse (V: BGM-1)'),
    'Socket_SupportHand': dict(at=_sup, part='pump', note='Unterseite des Schiebemantels; bewegt sich mit ihm'),
    'Socket_Muzzle': dict(at=(CROWN, BORE, 0), part='muzzle_crown', note='Mitte zwischen den beiden Kronen auf Laufhöhe (zwei Bohrungen)'),
    'Socket_LoadingGate': dict(at=((GATE[0] + GATE[1]) / 2, 34, 0), part='loading_gate', note='Patronen einzeln von unten'),
}
ANCHORS.update(SIGHT_ANCHORS)
EJECT = dict(at=((PORT[0] + PORT[1]) / 2, BORE, -HALF), dir=(0.15, 0.55, -1.0), case='shotshell',
             src='A: Auswurffenster rechts im Gehäuse beim Zurückziehen des Mantels, Hülse nach rechts, etwas hoch und vorn (wie BASIC-08)')
EGO_GRIPS = {
    'grip':    dict(contact=(-3, -6, -16.5), palm=(0.15, 0.0, 1.0), fingers=(1.0, -0.06, 0.0), fingers_pose='trigger',
                    src='V: Griff BGM-1 wie die Familie'),
    'support': dict(part='pump', contact=(_sup[0], PUMP_U[0] - 1.5, -2), palm=(0.0, 1.0, -0.25), fingers=(0.08, 0.15, -1.0),
                    fingers_pose='underhand', src='A: unter dem Schiebemantel hinter dem Handstopp; folgt dem Mantel'),
    'mag':     dict(part='shell_round', contact=(GATE[0] + 22, 39.5, 0), palm=(0.0, 1.0, 0.0), fingers=(1.0, 0.0, 0.0), fingers_pose='pinch',
                    src='A: unter der Patrone (Ruhelage im Ladeschacht), Hand von unten, schiebt sie durch die Ladeklappe'),
    'charge':  dict(part='pump_release', contact=(70, 60, HALF + 1.5), palm=(0.0, 0.0, -1.0), fingers=(0.45, 0.9, 0.0),
                    fingers_pose='pinch', src='A: am Pumpenriegel links (vom Nachladen nicht genutzt)'),
}
POINTS = collect(EJECT, EGO_GRIPS, dict(eject='upper', grip='grip'))
EGO_LIVE = dict(trigger='trigger', bolt='', port='', fill=['chamber_eyes'])
ACTIONS = {
    'fire_pump': dict(de='Schuss und Repetieren (Mantel zurück und vor, beide Kammern)', frames=30, step=1, keys={
        'trigger': [(0, 0), (2, 1), (6, 0)], 'pump': [(0, 0), (8, 0), (14, 1), (22, 0)], 'bolt': [(0, 0), (8, 0), (14, 1), (22, 0)]},
        events=[(2, 'shot'), (14, 'eject'), (22, 'ready')], view=(-0.85, -0.25, 0.45)),
    'load_shell': dict(de='Eine Patrone laden (wiederholt je Patrone)', frames=24, step=2, keys={
        'shell_round': [(0, 1), (8, 1), (18, 0)]}, events=[(18, 'shell_in')], view=(-0.7, -0.3, -0.55)),
}
EXPLODE = {'sight': (0, 90, 0), 'ammo': (0, -120, 0), 'stock': (-110, 0, 0), 'barrel': (150, 0, 0), 'support': (0, 0, 0),
           'grip_controls': (-10, -80, 0), 'mechanism': (60, -70, 0), 'receiver': (0, 0, 0)}
HERO = (0.55, -0.70, 0.35)   # A: Produktbild von links vorn – Zwillingsauge, Brillenspalt und Joch zur Kamera
