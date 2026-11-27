"""DaVinci-01 „Linea“ – Premium-Automatikgewehr, erstes Modell der Serie DaVinci (Formgen v2 0.52 „Atelier“).

Reines Spiel-Asset für Cube Escape / KYBOS (keine reale Herstellung). Eigenes Modell im BALLON-Kit-Vokabular (reines Python, kein bpy).
Keine Teile oder Umbauten von BASIC-01 oder EXTENDED-01: aus `basic.common` kommen nur genormte Familienschnittstellen (Griffmodul
BGM-1, Holovisier H0 auf Schiene BRI-22, Gewehrmagazin BMW-R, Feuerwahlhebel, Ladehebel-Form, Schraubenköpfe) und Hilfen. Geladen über
`formgen.davinci`, Vorschau über den v2-Raster, Export über BALLONs unverändertes `tools/blender_build.main` (ohne Ansichten).

Formsprache (Auswahl unter drei Blockouts: docs/davinci.md)
- Leitmerkmal 1 „Linea“: eine einzige gerade Oberlinie von der Schaftkappe bis zur Stirn (u = TOP über 806 mm), betont durch die
  Rückenleiste aus dunklem Titan und die Goldlinie (Grafikband) darunter. Darunter steigen genau zwei Schrägen im selben Winkel (SLOPE
  18°), gespiegelt um den Griff: die Strebe des Daumenlochschafts steigt vom Griffboden nach hinten zur Schaftkappe, die Nase des
  Vorderschafts nach vorn zur Stirn (dazu das Unterteil hinten). Alle übrigen langen Kanten sind waagerecht oder senkrecht.
- Leitmerkmal 2 „Vesica“: eine Schlossplatte als Spitzoval (Schnitt zweier Kreise) auf beiden Gehäuseseiten, links mit dem runden
  Energiekern (Oculus) als Schmuckstein über der vorderen Spitze – der eine Blickfang, kameranah links (Runde 1: mittig las er sich
  als Auge). Platten als Intarsie ohne sichtbare Schrauben.
- Negativraum: der große Durchbruch im Daumenlochschaft (Schleife aus Kamm, Kolbenrücken und Strebe), die Strebe endet am Griffboden.
- Schichten: Rückenleiste 2,5 mm auf der Schale, Schlossplatten 0,6 mm über ihrer Mulde, Wangenpolster 0,7 mm auf den Kammflanken,
  Unterteil und Vorderschaft je Seite 1 mm schmaler als die Schale.
- Zweiton und Material: Schale `shell` (Gehäuse, Schaft, Magazin; in Sfumato Nachtpetrol) über `graphite` (Unterteil, Vorderschaft,
  Wangenpolster; in Sfumato Elfenbein, umgekehrter Zweiton dunkel über hell); Schlossplatten, Abzugsbügel und Griffboden `anodized`;
  Schrauben und Kanten blank (`trim`), Goldlinie und Schrift `decal`. Teilung am Gehäuse 54:42 (Fuge u 84); Seitenanteil Schale 61 %,
  Graphit 19 % (G, extended_lines.role_shares).
- Querschnitte: Schulterfasen 7 × 10 mm an Schale und Schaft über die ganze Länge (Deck 32 bzw. 26 mm), Kielfasen am Vorderschaft und
  am Unterteil, Draufsicht-Verjüngung der Front von 46 auf 38 mm.
- Front mehrstufig: Nasenkappe mit 18°-Unterkante und Stirnfase, blanke Laufbuchse, freier Lauf, Kompensator mit Ringnuten und Ports,
  blanke Krone.
- Budgets: 1 Blickfang, 2 Leuchtfunktionen (Kern, Munitionsanzeige), 1 Grafikband (Goldlinie), 1 Schrift (rechts), 3 Akzent-Bedien-
  funktionen (Feuerwahlhebel, Magazinhalter, Ladehebel).

Herkunft der Zahlen: V = Vorgabe (Familie/Schnittstelle, BASIC-01 Pilot v2.1 bzw. `basic.common`, Design-Kanon), A = Annahme (Entwurf
0.52, an den Rastervorschauen gesichtet), G = gemessen. Zahlen ohne Kennung sind A. Maße mm; f nach vorn, u nach oben, x nach links;
Socket_Hand = (0, 0, 0).
"""
import math

from basic.arms.ego import GRIPS as _EGO
from basic.common import (part, prof, box, cyl, cut_box, screws, mirror, rail, selector, charging_handle, grip_v21,
                          reflex_sight_v21, rifle_mag, R_BODY, R_MID, R_SMALL, R_FINE)
from basic.variant import collect

META = dict(id='DAVINCI-01', num='D01', sheet_id='DA01', series='DaVinci', type='auto_rifle', type_de='Automatikgewehr',
            type_en='Auto Rifle', family='BASIC', name='DaVinci', nick='Linea', skin='sfumato', ammo='primary', fire='full_auto',
            reference_length_m=0.906, reference_length_source='G: Hülle des Netzes (formgen.kanon), Rahmen BASIC-01 0,93 m (V)',
            inspired_by='BASIC-Familie (Materialrollen, Schichtung, Radien); Formgen v1 als Haltung (eine mutige Geste)',
            summary='Premium-Automatikgewehr: gerade Linea-Oberlinie, Daumenlochschaft, Vesica-Schlossplatte mit Oculus-Kern.')
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

BORE = 106           # V: Laufachse wie BASIC-01/EXTENDED-01 (gleiche Griff-Lauf-Geometrie der Familie)
TOP = 138            # A: die Linea; Schiene auf der Rückenleiste (TOP + 2,5), Visierlinie TOP + 10,5 + 26 = 174,5 → 68,5 über der Laufachse
SPLIT = 84           # A: Zweiton-Fuge Schale/Graphit (waagerecht wie die Linea)
F_REAR, F_CAP, F_NOSE = -128, 466, 506   # A: Gehäuseende (Schaftfuge), Fuge Vorderschaft/Nasenkappe, Stirn
F_BUTT = -298        # A: Schaftende vor Zwischenlage und Kappe (Gesamtlänge ≈ 906 wie BASIC-01)
HALF = 23.0          # A: halbe Schalenbreite (BASIC-01 Oberteil 44, hier 46 für die Schulterfasen)
SLOPE = math.tan(math.radians(18))   # A: einziger Schrägwinkel (Schaftstrebe und Nase)
FORE_LOW, F_RISE = 52, 380           # A: Unterkante Vorderschaft, Beginn der Nasenschräge
REAR_LOW = 42 + (-56 - F_REAR) * SLOPE   # A: Unterteil hinten steigt im Linea-Winkel zum Schaft (u ≈ 65,4)


def nose_low(f):
    """A: Unterkante Vorderschaft/Nase – waagerecht bis F_RISE, dann 18° steigend."""
    return FORE_LOW + max(0.0, f - F_RISE) * SLOPE


def strut_low(f):
    """A: Unterkante der Schaftstrebe – 18° vom Griffboden (f −46, u −76) zur Schaftkappe."""
    return -76 + (-46 - f) * SLOPE


def strut_high(f):
    """A: Oberkante der Strebe, 30 mm über der Unterkante (≈ 28,5 mm Wandstärke senkrecht zur Strebe)."""
    return strut_low(f) + 30


def vesica(fc, uc, length, height, grow=0.0, n=12):
    """Spitzoval (Vesica): Schnitt zweier Kreise, Spitzen vorn/hinten. grow vergrößert gleichmäßig (Mulde, Platte)."""
    a, h = length / 2 + grow, height / 2 + grow
    r = (a * a + h * h) / (2 * h)       # Kreisradius aus halber Sehne a und Pfeilhöhe h
    t = math.asin(a / r)
    top = [(fc + r * math.sin(-t + 2 * t * i / n), uc + h - r + r * math.cos(-t + 2 * t * i / n)) for i in range(n + 1)]
    low = [(f, 2 * uc - u) for f, u in top[1:-1]]
    return top[::-1] + low      # hinten → oben nach vorn … gegen den Uhrzeigersinn geschlossen


def shoulders(f0, f1, half, top, w=7.0, h=10.0):
    """Schulterfasen als Querprofil-Schnitt beidseitig: w breit, h hoch (gestalteter Querschnitt, Kanon › 2)."""
    return [dict(shape='xprof', f0=f0, f1=f1, cu=0, pts=[(sx * (half - w), top + 1), (sx * (half + 2), top + 1), (sx * (half + 2), top - h)])
            for sx in (1, -1)]


def keel(f0, f1, half, low, w=6.0, h=9.0):
    """Kielfasen unten beidseitig (Querprofil-Schnitt)."""
    return [dict(shape='xprof', f0=f0, f1=f1, cu=0, pts=[(sx * (half - w), low - 1), (sx * (half + 2), low - 1), (sx * (half + 2), low + h)])
            for sx in (1, -1)]


def cw(pts):
    """Draufsicht-Profil (f, x) im Uhrzeigersinn (Kanon › 3: einheitliche Laufrichtung über cw())."""
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))
    return list(pts[::-1]) if area > 0 else list(pts)


def taper(stations, u0, u1, out=60.0):
    """Draufsicht-Verjüngung als Schneidkörper beidseitig: stations [(f, halbe Breite)…] nach f geordnet."""
    left = [(f, w) for f, w in stations] + [(stations[-1][0], out), (stations[0][0], out)]
    right = [(stations[0][0], -out), (stations[-1][0], -out)] + [(f, -w) for f, w in stations[::-1]]
    return [dict(shape='plan', pts=cw(left), u0=u0, u1=u1), dict(shape='plan', pts=cw(right), u0=u0, u1=u1)]


# Schlossplatte (A): Spitzoval 140 × 28 mm hinter dem Griff, Mitte f −50/u 108 (10 mm Abstand zur Fuge). Kern Ø 21 als Schmuckstein über der vorderen Spitze
# (Runde 1: mittig gesetzt las sich Platte + Kern als Auge, Kanon › 6 „liest sich als …“)
VES = dict(fc=-50, uc=108, length=140, height=28)
CORE_R = 10.5        # A: Kernfenster (Oculus), Rahmen Ø 27
CORE_C = (VES['fc'] + 62, VES['uc'])
BAND = 124.6        # A: Goldlinie 1,4 mm hoch, 2 mm über der Platte, 2 mm unter der Schulterfase (TOP − 10)   # A: Mitte 8 mm hinter der Plattenspitze, die Spitze läuft unter den Rahmen
FRONT_W = [(300, HALF), (F_CAP, 19.0), (F_NOSE + 4, 19.0)]          # A: Draufsicht Schale/Kappe 46 → 38
GUARD_W = [(300, HALF - 1), (F_CAP, 18.0), (F_CAP + 4, 18.0)]       # A: Vorderschaft je Seite 1 mm schmaler
# A: Seitenmulde des Vorderschafts; die Vorderkante läuft parallel zur Nase (18°), sonst waagerecht/senkrecht
RELIEF = [(196, 61), (F_RISE + 6, 61), (F_RISE + 6 + 14 / SLOPE, 75), (196, 75)]

P = []
# ---------------------------------------------------------------- Gehäuse (Schale über Graphit)
P += [
    prof('upper', 'Oberes Gehäuse', 'Upper receiver', 'receiver', 'shell',
         'Tragkörper für Verschluss, Kern, Lauf und Rückenleiste; trägt die Linea bis zur Nasenkappe',
         'auf Unterteil und Vorderschaft, Fuge waagerecht (zwei Querbolzen)',
         [(F_REAR, SPLIT), (F_CAP, SPLIT), (F_CAP, TOP), (F_REAR, TOP)], 2 * HALF, bevel=R_BODY,
         cuts=shoulders(F_REAR - 1, F_CAP + 1, HALF, TOP) + taper(FRONT_W, SPLIT - 2, TOP + 2)
         + [dict(shape='prof', pts=vesica(**VES, grow=0.6), w=2.0, x=sx * HALF) for sx in (1, -1)]          # Plattenmulden 1 mm
         + [dict(shape='cyl', axis='x', c=CORE_C, a0=HALF - 7, a1=HALF + 2, r=CORE_R, segs=32),   # Kernfenster links
            cut_box(28, 84, 94, 116, 18, x=-HALF),                                                          # Auswurffenster rechts
            cut_box(92, 192, 99, 113, 10, x=HALF)]),                                                        # Ladehebel-Nut links
    prof('lower', 'Unteres Gehäuse', 'Lower receiver', 'receiver', 'graphite', 'Griffmodul, Abzugsgruppe, Magazinschacht',
         'unter dem Oberen Gehäuse; Magazintrichter angeformt',
         [(F_REAR, SPLIT), (F_REAR, REAR_LOW), (-56, 42), (80, 42), (84, 22), (142, 22), (148, 36), (156, FORE_LOW), (156, SPLIT)],
         2 * HALF - 2, bevel=R_BODY, cuts=keel(-56, 80, HALF - 1, 42)),
    prof('mag_well', 'Schachtlippe', 'Magazine well lip', 'receiver', 'trim', 'Blanke Einführkante des Magazintrichters',
         'unten am Trichter des Unterteils', [(83, 19.5), (143, 19.5), (144, 23), (82, 23)], 43, bevel=0.6, iface='BMW-R'),
    part('takedown_pins', 'Querbolzen', 'Takedown pins', 'receiver', 'multi', 'metal', 'Verbinden Ober- und Unterteil',
         'quer durch das Unterteil (lösbar)', bevel=0.4, items=mirror(screws([(-116, 74), (148, 72)], HALF - 1, r=3.4, h=1.0))),
    box('spine', 'Rückenleiste', 'Spine', 'receiver', 'dark_metal', 'Versteift die Schale; trägt die Schiene; Leitlinie der Linea',
        'auf das Obere Gehäuse geschraubt, Stufe 2,5 mm', -118, 456, TOP - 1, TOP + 2.5, 16, bevel=1.2),
    box('spine_cap', 'Leistenkappe', 'Spine end cap', 'receiver', 'trim', 'Blanker Abschluss der Rückenleiste vorn',
        'vorn auf der Leiste', 456, 461, TOP - 1, TOP + 2.9, 16.8, bevel=0.5),
    box('counter_bezel', 'Anzeigenrahmen', 'Counter bezel', 'receiver', 'anodized', 'Fasst die Munitionsanzeige (zum Auge)',
        'in die Rückenleiste gesetzt', -112, -82, TOP + 2.0, TOP + 3.6, 13, bevel=0.5),
    box('ammo_counter', 'Munitionsanzeige', 'Ammo counter', 'receiver', 'energy', 'Füllstand oben, im Blick beim Zielen',
        'im Anzeigenrahmen', -108, -86, TOP + 3.2, TOP + 3.9, 8, bevel=0.2),
]
# Vesica-Schlossplatten und Oculus-Kern (Blickfang links)
P += [
    prof('plate_l', 'Schlossplatte links', 'Side plate left', 'receiver', 'anodized', 'Deckt Verschlussweg und Kern; Leitmerkmal Vesica',
         'in die Mulde eingelegt, ohne sichtbare Schrauben; vorn hält der Kernrahmen', vesica(**VES), 1.6, bevel=R_FINE, x=HALF - 0.2,
         cuts=[dict(shape='cyl', axis='x', c=CORE_C, a0=HALF - 3, a1=HALF + 3, r=CORE_R + 0.5, segs=32)]),
    prof('plate_r', 'Schlossplatte rechts', 'Side plate right', 'receiver', 'anodized', 'Deckt den Verschlussweg rechts',
         'in die Mulde eingelegt, ohne sichtbare Schrauben (Intarsie)', vesica(**VES), 1.6, bevel=R_FINE, x=-HALF + 0.2),
    cyl('core_frame', 'Kernrahmen', 'Core bezel', 'receiver', 'trim', 'Blanker Ring um den Oculus (Champagner)',
        'in die Schlossplatte gesetzt', 'x', CORE_C, HALF - 1.0, HALF + 1.8, CORE_R + 3.0, r_in=CORE_R - 0.6,
        segs=32, bevel=0.6),
    cyl('core_glow', 'Energiekern', 'Energy core', 'receiver', 'energy', 'Leuchtende Antriebszelle (Blickfang, Oculus)',
        'hinter dem Kernglas', 'x', CORE_C, HALF - 6.0, HALF - 4.4, CORE_R - 0.4, segs=32, bevel=0),
    cyl('core_lens', 'Kernglas', 'Core lens', 'receiver', 'glass', 'Schützt den Kern', 'im Kernrahmen', 'x', CORE_C,
        HALF - 1.4, HALF - 0.8, CORE_R - 0.2, segs=32, bevel=0),
    cyl('core_hub', 'Kernnabe', 'Core hub', 'receiver', 'dark_metal', 'Mittelstück der Zelle; teilt das Leuchten in einen Ring',
        'auf die Zelle gesetzt', 'x', CORE_C, HALF - 4.6, HALF - 3.0, 4.2, segs=24, bevel=0.3),
    part('linea_band', 'Goldlinie', 'Linea stripe', 'receiver', 'multi', 'decal', 'Feine Linie unter der Schulterfase (einziges Grafikband)',
         'aufgedruckt, beidseitig', bevel=0,
         items=[dict(shape='prof', pts=[(F_REAR + 8, BAND), (296, BAND), (296, BAND + 1.4), (F_REAR + 8, BAND + 1.4)], w=0.6,
                     x=sx * (HALF + 0.05)) for sx in (1, -1)]),
    # A: freie Schalenfläche rechts am Vorderschaft (f 172 … ≈ 230), Fuge 84 und Goldlinie 121 frei; linksbündig, läuft nach vorn
    part('text_r', 'Schriftzug', 'Lettering', 'receiver', 'text', 'decal', 'Kennung „DAVINCI-01 ED.I“ (einzige Schrift, Editionsmarke)',
         'aufgedruckt', bevel=0, text='DAVINCI-01  ED.I', size=4.6, f=176, u=104, x=-HALF - 0.05, side=-1, depth=0.12),
]
# Verschluss im Auswurffenster rechts
P += [
    box('bolt_carrier', 'Verschlussträger', 'Bolt carrier', 'mechanism', 'metal', 'Lädt und verriegelt; läuft beim Schuss zurück',
        'im Oberen Gehäuse geführt', -20, 96, 96, 116, 26, bevel=R_SMALL, cuts=[cut_box(36, 78, 101, 111, 4, x=-13)],
        move=dict(kind='translate', pivot=(40, 106, 0), vector_mm=(-42, 0, 0), event='fire')),
    prof('port_cover', 'Auswurfklappe', 'Ejection port cover', 'mechanism', 'dark_metal', 'Deckt das Auswurffenster ab',
         'Scharnier an der Unterkante', [(28, 94), (84, 94), (84, 116), (34, 116), (28, 110)], 1.6, bevel=R_FINE, x=-HALF - 0.6,
         move=dict(kind='rotate', pivot=(56, 94, -HALF - 1), axis='f', range_deg=(0, 75), event='fire',
                   expect=((56, 116, -HALF - 1), (0, 0, -1)))),
]
# Schiene und Visier (Familienschnittstelle BRI-22 / H0) auf der Rückenleiste
P += rail(-36, 56, TOP + 2.5)
P[-1]['cuts'] = [cut_box(-30 + 12 * i, -24 + 12 * i, TOP + 6.5, TOP + 11.5, 30) for i in range(7)]
_sight, SIGHT_ANCHORS = reflex_sight_v21(-4, TOP + 10.5)
P += _sight
# ---------------------------------------------------------------- Vorderschaft und Nase
P += [
    prof('handguard', 'Vorderschaft', 'Fore-end', 'support', 'graphite',
         'Griffbereich der Stützhand; Nase steigt im Linea-Winkel 18°', 'an Unterteil und Schale verschraubt, Fuge',
         [(157, FORE_LOW), (F_RISE, FORE_LOW), (F_CAP, nose_low(F_CAP)), (F_CAP, SPLIT), (157, SPLIT)], 2 * HALF - 2, bevel=R_MID,
         cuts=keel(156, F_RISE + 30, HALF - 1, FORE_LOW) + taper(GUARD_W, FORE_LOW - 2, SPLIT + 2)
         + [dict(shape='prof', pts=RELIEF, w=2.4, x=sx * (HALF - 1)) for sx in (1, -1)]),   # Seitenmulde 1,2 mm
    prof('handguard_grip', 'Griffpolster', 'Grip pad', 'support', 'rubber', 'Rutschfeste Zone für die Stützhand',
         'unten auf den Vorderschaft geklebt', [(212, FORE_LOW - 3), (364, FORE_LOW - 3), (364, FORE_LOW + 3), (212, FORE_LOW + 3)],
         30, bevel=R_SMALL),
    part('handguard_screws', 'Vorderschaftschrauben', 'Fore-end screws', 'support', 'multi', 'trim', 'Halten den Vorderschaft',
         'seitlich', bevel=0.2, items=mirror(screws([(170, 64), (170, 76)], HALF - 1.2, r=1.7, h=0.7))),
    prof('nose_cap', 'Nasenkappe', 'Nose cap', 'barrel', 'dark_metal', 'Schließt Schale und Vorderschaft; führt den Lauf; Stirnfase',
         'auf Schale und Vorderschaft geschraubt (Fuge)',
         [(F_CAP, nose_low(F_CAP)), (494, nose_low(494)), (F_NOSE, 98), (F_NOSE, 126), (494, TOP), (F_CAP, TOP)], 38, bevel=R_MID,
         cuts=shoulders(F_CAP - 1, F_NOSE + 1, 19.0, TOP, w=6.0, h=9.0)),
    cyl('nose_bushing', 'Laufbuchse', 'Barrel bushing', 'barrel', 'trim', 'Führt den Lauf in der Nasenkappe; blanke Stufe',
        'in die Nasenkappe gepresst', 'f', (BORE, 0), F_NOSE - 4, F_NOSE + 3, 12.5, r_in=10.2, segs=32, bevel=0.5),
]
# ---------------------------------------------------------------- Lauf und Mündung
P += [
    cyl('barrel', 'Lauf', 'Barrel', 'barrel', 'metal', 'Führt das Geschoss', 'im Oberen Gehäuse verschraubt',
        'f', (BORE, 0), 150, 540, 10, segs=32),
    cyl('muzzle', 'Kompensator', 'Compensator', 'barrel', 'dark_metal', 'Rundes Mündungsteil mit Ringnuten und Ports; Socket_Muzzle',
        'auf Laufende geschraubt (lösbar)', 'f', (BORE, 0), 534, 590, 15, r_in=5.5, segs=24, bevel=R_SMALL, iface='BMZ-15',
        cuts=[dict(shape='cyl', axis='f', c=(BORE, 0), a0=540 + 5 * i, a1=541.8 + 5 * i, r=17, r_in=13.6, segs=24) for i in range(3)]
        + [cut_box(560 + 9 * i, 565 + 9 * i, BORE + 4, BORE + 20, 9) for i in range(3)]
        + [cut_box(562, 584, BORE - 3.5, BORE + 3.5, 40)]),
    cyl('muzzle_crown', 'Mündungskrone', 'Muzzle crown', 'barrel', 'trim', 'Blanke Stirnkante', 'vorn am Kompensator',
        'f', (BORE, 0), 588, 594, 13.5, r_in=6, segs=24, bevel=0.6),
]
# ---------------------------------------------------------------- Griff und Bedienung (Familienschnittstelle BGM-1)
P += grip_v21(top=42)
P += selector(8, 70, x=HALF - 1 + 1.5)
P += [dict(p, id='selector_r', de='Feuerwahlhebel rechts', en='Fire selector right', x=-HALF + 1 - 1.5) for p in selector(8, 70)]
P += charging_handle(158, 106, x=HALF + 0.5, travel=58)
P += [part('mag_release', 'Magazinhalter', 'Magazine release', 'grip_controls', 'cyl', 'accent', 'Löst das Magazin',
           'Druckknopf links', bevel=R_FINE, axis='x', c=(70, 58), a0=HALF - 2, a1=HALF + 2.5, r=5, segs=24,
           move=dict(kind='translate', pivot=(70, 58, HALF), vector_mm=(0, 0, -2.5), event='reload'))]
# ---------------------------------------------------------------- Magazin: gerade, 8° nach vorn (V: BMW-R), Sichtschlitze, Patronen
_m = rifle_mag(88, 66, depth=40, length=128, tilt=8, w=24)
for p in _m:
    if p['id'] == 'magazine':
        p['cuts'] = [dict(shape='prof', pts=[(98 - 0.14 * (uu - 66), uu), (122 - 0.14 * (uu - 66), uu), (122 - 0.14 * (uu + 2.4 - 66), uu + 2.4),
                                             (98 - 0.14 * (uu + 2.4 - 66), uu + 2.4)], w=3, x=sx * 12)
                     for uu in (-24, -34, -44) for sx in (1, -1)]
    if p['id'] == 'magazine_base':
        p['mat'] = 'dark_metal'
    if p['id'] == 'magazine_round':
        p['mat'] = 'brass'
P += _m
# ---------------------------------------------------------------- Schaft: Daumenloch-Schleife in der Linea
_web = [(-46, -76), (-40, -64), (-37, -52), (-33, -22), (-21, 12), (-12, 42)]   # V: 1 mm hinter dem Griffrücken BGM-1 (grip_v21)
STOCK_HALF = 21.0    # A: Schaft 42 mm, Deck 28 mm nach der Schulterfase
HOLE = [(-140, TOP - 30), (-264, TOP - 30), (-276, TOP - 42), (-276, strut_high(-276) + 10), (-264, strut_high(-264)),
        (-62, strut_high(-62)), (-50, -36), (-46, -20), (-36, 12), (-46, 40), (-86, 54), (-140, 66)]
P += [
    prof('stock', 'Daumenlochschaft', 'Thumbhole stock', 'stock', 'shell',
         'Schleife aus Kamm, Kolbenrücken und Strebe; Oberkante setzt die Linea fort, Strebe im Linea-Winkel zum Griffboden',
         'an der Schaftverbindung verschraubt, Strebe am Griffboden', [(F_REAR, TOP), (F_BUTT, TOP), (F_BUTT, strut_low(F_BUTT))]
         + _web + [(-56, 42), (F_REAR, REAR_LOW)], 2 * STOCK_HALF, bevel=R_BODY,
         cuts=[dict(shape='prof', pts=HOLE, w=60)] + shoulders(F_BUTT - 1, F_REAR + 1, STOCK_HALF, TOP)),
    part('stock_collar', 'Schaftverbindung', 'Stock collar', 'stock', 'xprof', 'dark_metal',
         'Verriegelt Schaft und Gehäuse; Materialwechsel', 'Ring um die Fuge Gehäuse/Schaft', bevel=R_FINE,
         f0=F_REAR - 6, f1=F_REAR + 4, cu=0,
         pts=[(-HALF + 0.6, 60), (HALF - 0.6, 60), (HALF + 0.7, 66), (HALF + 0.7, TOP - 10.5),
              (HALF - 7.2, TOP + 0.6), (-HALF + 7.2, TOP + 0.6), (-HALF - 0.7, TOP - 10.5), (-HALF - 0.7, 66)]),
    part('cheek_pads', 'Wangenpolster', 'Cheek pads', 'stock', 'multi', 'graphite',
         'Anlage für die Wange, beidseitig; hell wie das Fahrgestell (Runde 3: dunkel las es sich als Loch im Kamm)',
         'auf die Kammflanken geklebt', bevel=R_SMALL,
         items=[dict(shape='prof', pts=[(-258, TOP - 26), (-170, TOP - 26), (-170, TOP - 12), (-258, TOP - 12)], w=1.4,
                     x=sx * (STOCK_HALF + 0.0)) for sx in (1, -1)]),
    part('sling_cups', 'Riemenaufnahmen', 'Sling cups', 'stock', 'multi', 'dark_metal', 'Schnellkupplung für den Trageriemen',
         'eingepresst, beidseitig am Kolbenrücken und vorn am Vorderschaft', bevel=0.3,
         items=mirror([dict(shape='cyl', axis='x', c=(-287, 72), a0=STOCK_HALF - 1.5, a1=STOCK_HALF + 1.2, r=6.0, r_in=2.6, segs=16),
                       dict(shape='cyl', axis='x', c=(436, 76), a0=18.2 - 1.5, a1=18.2 + 1.2, r=5.5, r_in=2.4, segs=16)])),
    part('stock_screws', 'Schaftschrauben', 'Stock screws', 'stock', 'multi', 'trim', 'Halten den Schaft an der Verbindung',
         'seitlich am Schaftpfosten', bevel=0.2, items=mirror(screws([(-134, 80), (-134, 100)], STOCK_HALF, r=1.7, h=0.7))),
    prof('butt_spacer', 'Zwischenlage', 'Butt spacer', 'stock', 'trim', 'Blanke Lage zwischen Schaft und Kappe',
         'zwischen Schaft und Kappe', [(F_BUTT, strut_low(F_BUTT) + 1), (F_BUTT, TOP - 0.5), (F_BUTT - 2.5, TOP - 0.5),
                                       (F_BUTT - 2.5, strut_low(F_BUTT) + 1)], 2 * STOCK_HALF - 1, bevel=0.4),
    prof('butt_pad', 'Schaftkappe', 'Butt pad', 'stock', 'rubber', 'Rutschfeste Anlage an der Schulter', 'auf das Schaftende gesteckt',
         [(F_BUTT - 2.5, strut_low(F_BUTT) - 1), (F_BUTT - 2.5, TOP), (F_BUTT - 9, TOP - 1), (F_BUTT - 13, TOP - 8),
          (F_BUTT - 13, strut_low(F_BUTT) + 8), (F_BUTT - 9, strut_low(F_BUTT) + 1)], 2 * STOCK_HALF + 1, bevel=R_MID,
         cuts=[cut_box(F_BUTT - 14, F_BUTT - 10, 22 + 14 * i, 25 + 14 * i, 50) for i in range(8)]),
]
PARTS = P

# ---------------------------------------------------------------- Anker, Weltpunkte, Aktionen
ANCHORS = {
    'Socket_Hand': dict(at=(0, 0, 0), part='grip', note='Haupthand, auf der Griffachse (V: BGM-1)'),
    'Socket_SupportHand': dict(at=(288, 70, 0), part='handguard', note='Mitte Vorderschaft über dem Griffpolster, Stützhand umgreift'),
    'Socket_Muzzle': dict(at=(594, BORE, 0), part='muzzle_crown', note='Stirnfläche Mündungskrone auf der Laufachse'),
    'Socket_MagWell': dict(at=(108, 66, 0), part='mag_well', note='Einrastpunkt Magazin (Schnittstelle BMW-R)'),
    'Socket_Charge': dict(at=(174, 106, HALF + 5), part='charging_handle', note='Griffpunkt Ladehebel vorn links (Stützhand)'),
}
ANCHORS.update(SIGHT_ANCHORS)
EJECT = dict(at=(56, 105, -20), dir=(0.3, 0.4, -1.0), case='rifle',
             src='A: Mitte Auswurffenster rechts (port_cover), Hülse nach rechts, etwas hoch und vorn (wie BASIC-01)')
_CONTACT = {'grip': ((-3, -6, -16.5), 'V: Griff BGM-1 wie die Familie'),
            'support': ((290, FORE_LOW - 3, -2), 'A: unter dem Griffpolster'),
            'mag': ((120, -18, 12.5), 'A: linke Magazinseite'),
            'charge': ((174, 106, HALF + 5), 'A: Ladehebel vorn links')}
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
HERO = (0.78, -0.50, 0.40)   # A: Produktbild von links vorn oben – Oculus (Blickfang) und Ladehebel zur Kamera
