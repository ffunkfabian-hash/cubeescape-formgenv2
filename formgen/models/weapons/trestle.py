"""EXTENDED-18. Eigenständige Außenhaut für den BASIC-01-Spieltyp.

Alle Konturen, Querschnitte, Fugen, Beschriftungen und Fasen sind freie
gestalterische Annahmen in Formgen-Autoreneinheiten. Die Typ- und Materialrollen
stammen aus BASIC-01. Die abgestufte Vorderschale und der eigene Graphit-Brückenfuß halten
den Mittelraum auch von schräg oben offen. Variante A ist der Nutzerentscheid
vom 23.11.2026: Frontachse u 84, H0 auf BRI-22 und Scheitelleiste, Visierlinie
u 189 (105 mm über der Frontachse; bewusste Abweichung vom BASIC-Standard).
Kitgeometrie: basic.common aus dem gepinnten BALLON-Snapshot, Lage = Annahme.
Sämtliche Teile bleiben statisch; Socket_* sind virtuelle Spielbezugspunkte.
"""


def build():
    parts = []

    def add(key, group, role, label, shape, bevel, **geometry):
        parts.append(dict(id=key, asm=group, mat=role, de=label, en=key.replace('_', ' '),
                          func=label, attach='Außenmodell EXTENDED-18', shape=shape,
                          bevel=bevel, segs_bevel=3, **geometry))

    def plate(key, group, role, label, pts, width, bevel=2, x=0, **geometry):
        add(key, group, role, label, 'prof', bevel, pts=pts, w=width, x=x, **geometry)

    def section(key, group, role, label, start, end, level, width, height, corner, bevel=1):
        a, b = width / 2, height / 2
        pts = [(-a+corner, -b), (a-corner, -b), (a, -b+corner), (a, b-corner),
               (a-corner, b), (-a+corner, b), (-a, b-corner), (-a, -b+corner)]
        add(key, group, role, label, 'xprof', bevel, f0=start, f1=end, cu=level, pts=pts)

    # Rückengehäuse: kurzer, tiefer Absatz und abgesetzte, weiche Schulterkante.
    plate('heel', 'stock', 'graphite', 'Schulterkante',
          [(-297, 119), (-279, 128), (-262, 121), (-267, 31), (-278, 16), (-299, 20), (-305, 32)], 53, 5)
    plate('cheek', 'stock', 'shell', 'Wangenkörper',
          [(-286, 117), (-262, 131), (-198, 132), (-177, 128), (-166, 121),
           (-183, 96), (-183, 83), (-231, 82), (-270, 51), (-285, 45)], 47, 3)
    plate('heel_spur', 'stock', 'dark_metal', 'Untere Schaftstrebe',
          [(-286, 31), (-276, 18), (-251, 23), (-149, 69), (-125, 84), (-153, 88), (-257, 49)], 29, 2.5)
    plate('comb', 'stock', 'graphite', 'Weiche Wangenauflage',
          [(-274, 125), (-251, 137), (-199, 138), (-175, 131), (-170, 125), (-199, 130), (-263, 129)], 35, 2)
    # Der schmalere Kiel erscheint zwischen den gegensinnig abgestuften Außenkörpern.
    plate('keel', 'receiver', 'graphite', 'Unterer Gehäusekiel',
          [(-199, 105), (-185, 122), (-164, 124), (-125, 117), (-93, 112), (2, 103),
           (87, 89), (122, 82), (113, 60), (86, 49), (64, 34), (17, 33), (-1, 50),
           (-50, 57), (-76, 73), (-162, 76), (-185, 83)], 44, 3)
    badge_outline = [(-131, 104), (-117, 116), (-67, 120), (-53, 115), (-61, 97), (-118, 96)]
    badge_recess = [(-134, 104), (-118, 118), (-67, 122), (-50, 116), (-60, 95), (-119, 94)]
    plate('flank', 'receiver', 'shell', 'Hintere Gehäuseschale',
          [(-172, 97), (-151, 125), (-78, 128), (19, 112), (47, 94), (32, 76),
           (-39, 75), (-64, 82), (-89, 88), (-172, 86)], 60, 3.2,
          cuts=[dict(shape='prof', pts=badge_recess, w=10, x=x) for x in (-31, 31)])
    plate('throat', 'support', 'dark_metal', 'Freiliegende Mittelschicht',
          [(11, 98), (39, 106), (67, 106), (84, 101), (148, 101), (206, 107),
           (264, 96), (289, 87), (284, 77), (214, 78), (122, 71), (91, 65),
           (73, 71), (28, 77)], 43, 2)
    # Das große Seitenfenster liegt in der Schale. Seine Rückwand und die fünf
    # Lamellen sitzen auf der tieferen Ebene des Mittelkörpers.
    window = [(147, 95), (159, 104), (231, 104), (258, 99), (248, 85), (166, 85), (147, 89)]
    plate('fore_cuff', 'support', 'shell', 'Vordere Keilschale',
          [(87, 69), (90, 105), (96, 111), (125, 113), (165, 114), (208, 112),
           (276, 100), (302, 87), (293, 72), (258, 69), (224, 77), (143, 76),
           (115, 66)], 61, 4.5,
          cuts=[dict(shape='prof', pts=window, w=74)])
    plate('palm', 'support', 'graphite', 'Vordere Griffmulde',
          [(102, 65), (140, 76), (221, 77), (229, 73), (210, 58), (188, 54),
           (128, 55), (110, 51), (98, 54)], 47, 2.5)
    # Flacher Rücken mit freiem Scheitel. Die Füße greifen in beide Schalen.
    plate('arch_liner', 'receiver', 'graphite', 'Dunkle Brückenunterkante',
          [(-118, 116), (-64, 142), (-51, 146), (88, 146), (109, 139), (147, 118), (111, 118),
           (83, 133), (-44, 133), (-89, 115)], 40, 2)
    plate('arch', 'receiver', 'shell', 'Offene Rückenbrücke',
          [(-127, 119), (-60, 149), (-49, 152), (85, 152), (103, 147), (154, 121), (154, 118),
           (120, 118), (84, 139), (-43, 139), (-90, 121)], 47, 2)
    # Senkrechte Doppelkante neben dem Indexfeld; unter dem stumpfen Bein
    # bleibt ein eigener, je Seite 5 mm eingerückter Graphitsockel sichtbar.
    plate('cuff_step', 'support', 'shell', 'Schalenabsatz',
          [(81, 70), (84, 105), (90, 110), (92, 110), (88, 69)], 53, 3)
    plate('arch_foot', 'receiver', 'graphite', 'Brückenfuß',
          [(126, 112.5), (157, 112.5), (157, 114.5), (154, 118.4),
           (129, 118.4), (126, 115.5)], 37, 1.5)
    # Umlaufender Lack folgt derselben Schräge auf beiden Wangen und dem Rücken.
    for i, (f, width) in enumerate(((-89, 13), (-69, 4))):
        def band_top(at):
            return 119 + (at + 127) * 30 / 67 + 0.6
        def band_bottom(at):
            return 121 + (at + 90) * 18 / 47 + 0.7
        plate(f'arch_band_{i}', 'receiver', 'accent', 'Brückenmarkierung',
              [(f, band_top(f)), (f+width, band_top(f+width)),
               (f+width+8, band_bottom(f+width+8)), (f+8, band_bottom(f+8))], 48.1, 0.6)
    plate('crown', 'sight', 'dark_metal', 'Eingelassene Scheitelleiste',
          [(-56, 150), (-44, 155), (81, 155), (93, 150), (80, 149), (-43, 149)], 35, 1)
    # Der kleine Lichtindex sitzt in der Wange; die Oberseite bleibt durchgehend eben.
    plate('sight_tile', 'sight', 'anodized', 'Seitliches Keramikfenster',
          [(-32, 143), (-29, 148), (-9, 148), (-12, 143)], 1.8, 0.5, x=-23.7)
    plate('sight_lens', 'sight', 'energy', 'Optikindikator',
          [(-28, 144), (-27, 146.5), (-19, 146.5), (-20, 144)], 0.8, 0.25, x=-24.7)
    # Kurzer, facettierter Abschluss mit geschlossener Stirn und zwei Lichtfeldern.
    section('nose_neck', 'barrel', 'dark_metal', 'Facettierter Hals', 265, 352, 84, 39, 31, 7, 2)
    section('nose_band', 'barrel', 'metal', 'Heller Trennring', 325, 334, 84, 43, 34, 8)
    section('prow', 'barrel', 'graphite', 'Prismatische Stirnkappe', 341, 397, 84, 50, 39, 10, 2.5)
    section('prow_bezel', 'barrel', 'dark_metal', 'Stirnfassung', 378, 396, 84, 55, 43, 10, 1.5)
    for i in range(3):
        section(f'prow_flute_{i}', 'barrel', 'anodized', 'Facettenring', 346+i*9, 350+i*9, 84, 52, 40.5, 10, 0.7)
    section('face', 'barrel', 'anodized', 'Geschlossene Stirnfläche', 395, 399, 84, 46, 36, 9)
    for index, level in enumerate((80, 88)):
        section(f'face_light_{index}', 'barrel', 'energy', 'Lichtfeld', 398.8, 399.7, level, 21, 2.4, 0.8, 0.3)

    plate('handle', 'grip_controls', 'graphite', 'Hinterer Griff',
          [(-19, 74), (18, 68), (4, 41), (-7, 14), (-12, -19), (-4, -23), (-8, -31), (-43, -30),
           (-48, -22), (-38, 17), (-35, 39)], 38, 3)
    plate('loop', 'grip_controls', 'dark_metal', 'Offener Griffbügel',
          [(-15, 8), (21, 9), (49, 31), (59, 55), (52, 60), (44, 38), (18, 17), (-12, 17)], 18, 1.8)
    plate('trigger_switch', 'grip_controls', 'graphite', 'Abzugskontur',
          [(6, 54), (16, 55), (18, 40), (28, 30), (24, 28), (12, 35)], 12, 1.5)
    plate('cassette', 'ammo', 'graphite', 'Geneigte Kassette',
          [(53, 59), (102, 65), (111, 23), (125, -12), (143, -38), (138, -48), (98, -56), (81, -29), (63, 13)], 42, 3)
    plate('shoe', 'ammo', 'dark_metal', 'Kassettenfuß',
          [(90, -43), (133, -34), (146, -39), (144, -49), (100, -60), (92, -55)], 48, 2)
    for side, suffix in ((1, 'l'), (-1, 'r')):
        def skin(key, group, role, label, pts, base, thickness=2, bevel=0.7):
            plate(key+'_'+suffix, group, role, label, pts, thickness, bevel, side*(base+thickness/2-0.25))

        skin('badge', 'receiver', 'anodized', 'Eingelassenes Typenschild', badge_outline, 26, 3)
        skin('seam', 'receiver', 'dark_metal', 'Schalenfuge',
             [(-51, 119), (10, 109), (28, 98), (25, 96), (8, 106), (-52, 116)], 30)
        skin('cheek_insert', 'stock', 'anodized', 'Schaftintarsie',
             [(-261, 95), (-246, 108), (-199, 111), (-187, 107), (-199, 103), (-242, 101)], 23.5)
        skin('cassette_plate', 'ammo', 'shell', 'Kassettenwange',
             [(68, 33), (93, 42), (104, 14), (122, -22), (111, -31), (96, -24), (79, 8)], 21, 2.5)
        for i in range(3):
            f, u=83+i*4, 18-i*9
            skin(f'index_{i}', 'ammo', 'anodized', 'Indexstrich', [(f, u), (f+14, u+3), (f+15, u+0.5), (f+1, u-2.5)], 23.2, 0.9, 0.15)
        skin('fore_insert', 'support', 'graphite', 'Versenktes Seitenfeld',
             [(145, 95), (159, 105), (233, 105), (260, 99), (249, 84), (165, 84), (146, 88)], 21.5, 1.8)
        for i in range(5):
            f=177+i*13
            skin(f'louvre_{i}', 'support', 'dark_metal', 'Staffellamelle',
                 [(f, 87), (f+5, 87), (f+12, 102), (f+7, 102)], 23, 3.2, 0.7)
        skin('index_case', 'receiver', 'anodized', 'Anzeigefassung',
             [(28, 70), (39, 80), (69, 77), (74, 72), (66, 64), (35, 64)], 22, 2.2)
        for i in range(3):
            f=40+i*7
            skin(f'status_{i}', 'receiver', 'energy' if i<2 else 'metal', 'Statussegment',
                 [(f, 69), (f+3.5, 69), (f+6, 74), (f+2.5, 74)], 24, 1, 0.2)
        skin('grip_cheek', 'grip_controls', 'rubber', 'Weiche Griffwange',
             [(-27, 39), (-15, 44), (-13, 31), (-23, -13), (-34, -18), (-38, -15)], 19, 2.6, 1)
        for i in range(3):
            f, u=-32+i*2, -4+i*10
            skin(f'grip_rib_{i}', 'grip_controls', 'graphite', 'Griffrille',
                 [(f, u), (f+8, u+3), (f+9, u+5), (f+1, u+2)], 21.2, 1, 0.35)
        add('name_' + suffix, 'receiver', 'shell', 'Typografie', 'text', 0, text='TRESTLE',
            f=-93, u=103, x=side*28.85, side=side, depth=0.35, size=8, align='CENTER')

    # BASIC-Schrift wie an der BASIC-01-Haube: nur rechts, aufgedruckt,
    # linksbündig. Dunkle Rolle auf heller Schale; TRESTLE-Typenschild bleibt.
    add('text_r', 'receiver', 'anodized', 'Kennung (BASIC-Schrift)', 'text', 0,
        text='BASIC  EX-18', f=18, u=143.6, x=-23.55, side=-1, depth=0.12, size=4.4)

    # Der Aufrufer bindet den gepinnten Snapshot nur für diesen Build ein.
    from basic.common import (rail, reflex_sight_v21, selector, charging_handle,
                              screws, mirror, cut_box, part as kit_part)

    # BRI-22 auf der Scheitelleiste; sechs Querschlitze im BASIC-12-mm-Raster.
    rail_parts = rail(-50, 34, 155)
    rail_parts[0]['cuts'] = [cut_box(-44 + 12*i, -38 + 12*i, 159, 164, 30)
                             for i in range(6)]
    parts += [dict(q, mat='anodized') for q in rail_parts]
    sight, sight_anchors = reflex_sight_v21(-30, 163, weapon_type='auto_rifle')
    parts += sight
    parts += selector(-8, 88, x=31.5)
    parts += [dict(q, id='selector_r', de='Feuerwahlhebel rechts', en='Fire selector right', x=-31.5)
              for q in selector(-8, 88)]
    parts += charging_handle(98, 100, x=33.5, travel=24)
    parts.append(kit_part('mag_release', 'Magazinhalter', 'Magazine release', 'grip_controls', 'cyl', 'accent',
                          'Statisches Kitdetail', 'Druckknopf links', bevel=0.8,
                          axis='x', c=(40, 56), a0=20.5, a1=25, r=4.5, segs=20))
    parts.append(kit_part('shell_screws', 'Schalenschrauben', 'Shell screws', 'receiver', 'multi', 'trim',
                          'Statische Schalendetails', 'seitlich', bevel=0.2,
                          items=mirror(screws([(-143, 98), (17, 89)], 30, r=1.8, h=0.8))
                          + mirror(screws([(129, 90), (275, 84)], 30.5, r=1.8, h=0.8))))
    parts.append(kit_part('takedown_pins', 'Querbolzen', 'Takedown pins', 'receiver', 'multi', 'metal',
                          'Statisches Kitdetail', 'quer durch den Kiel', bevel=0.4,
                          items=mirror(screws([(-120, 81)], 21.4, r=3.6, h=1))))
    # Kitgeometrie übernehmen, ohne Bewegungsverträge an das statische Asset
    # zu hängen. Die virtuellen Sockets erzeugen selbst keinerlei Mechanik.
    for part in parts:
        part.pop('move', None)

    anchors = {
        'Socket_Hand': ('handle', [-20, 23, 0]),
        'Socket_SupportHand': ('palm', [158, 67, 0]),
        'Socket_Muzzle': ('face', [399, 84, 0]),
        'Socket_Charge': ('charging_handle', [113, 100, 38]),
        'Socket_MagWell': ('keel', [78, 62, 0]),
    }
    anchors = {k: dict(part=p, at=at, source='Annahme: virtueller Bezugspunkt des statischen Spielmodells')
               for k, (p, at) in anchors.items()}
    for key, anchor in sight_anchors.items():
        anchors[key] = dict(anchor, at=list(anchor['at']),
                            source='Vorgabe: Visier-Standard (basic.common.reflex_sight_v21)')
    # Stabile Editor-Bezüge des Spieltyps; keine beweglichen Baugruppen.
    points = {
        'grip.grip': ('handle', [-20, 23, 0]),
        'grip.support': ('palm', [158, 67, 0]),
        'grip.mag': ('cassette', [100, -10, 0]),
        'grip.charge': ('charging_handle', [113, 100, 38]),
        'eject': ('index_case_r', [42, 72, -23]),
    }
    return parts, anchors, {name: dict(part=part, at=at) for name, (part, at) in points.items()}
