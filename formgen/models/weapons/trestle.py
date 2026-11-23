"""EXTENDED-02. Eigenständige Außenhaut für den BASIC-01-Spieltyp.

Alle Konturen, Querschnitte, Fugen, Beschriftungen und Fasen sind freie
gestalterische Annahmen in Formgen-Autoreneinheiten. Die Typ- und Materialrollen
stammen aus BASIC-01. Der reduzierte obere Bügel und der Keil unter seinem
vorderen Fuß lassen den Mittelraum auch von schräg oben offen.
"""


def build():
    parts = []

    def add(key, group, role, label, shape, bevel, **geometry):
        parts.append(dict(id=key, asm=group, mat=role, de=label, en=key.replace('_', ' '),
                          func=label, attach='Außenmodell EXTENDED-02', shape=shape,
                          bevel=bevel, segs_bevel=3, **geometry))

    def plate(key, group, role, label, pts, width, bevel=2, x=0):
        add(key, group, role, label, 'prof', bevel, pts=pts, w=width, x=x)

    def section(key, group, role, label, start, end, level, width, height, corner, bevel=1):
        a, b = width / 2, height / 2
        pts = [(-a+corner, -b), (a-corner, -b), (a, -b+corner), (a, b-corner),
               (a-corner, b), (-a+corner, b), (-a, b-corner), (-a, -b+corner)]
        add(key, group, role, label, 'xprof', bevel, f0=start, f1=end, cu=level, pts=pts)

    # Rückengehäuse: kurzer, tiefer Absatz und abgesetzte, weiche Schulterkante.
    plate('heel', 'stock', 'graphite', 'Schulterkante',
          [(-297, 119), (-279, 128), (-262, 121), (-267, 31), (-278, 16), (-299, 20), (-305, 32)], 53, 5)
    plate('cheek', 'stock', 'shell', 'Wangenkörper',
          [(-287, 118), (-262, 131), (-196, 132), (-115, 117), (-70, 88), (-95, 65),
           (-151, 80), (-232, 82), (-272, 50), (-288, 43)], 47, 4)
    plate('heel_spur', 'stock', 'dark_metal', 'Untere Schaftstrebe',
          [(-286, 31), (-276, 18), (-251, 23), (-149, 69), (-125, 84), (-153, 88), (-257, 49)], 29, 2.5)
    plate('comb', 'stock', 'graphite', 'Weiche Wangenauflage',
          [(-274, 125), (-251, 137), (-199, 138), (-141, 127), (-130, 120), (-198, 130), (-263, 129)], 35, 2)
    # Die Außenschalen verjüngen sich entlang des Rückens in zwei Stufen.
    plate('keel', 'receiver', 'graphite', 'Unterer Gehäusekiel',
          [(-156, 90), (-116, 116), (2, 104), (93, 93), (148, 76), (131, 55), (86, 49),
           (64, 34), (17, 33), (-1, 50), (-50, 57), (-76, 73), (-132, 71)], 55, 4)
    plate('flank', 'receiver', 'shell', 'Hintere Gehäuseschale',
          [(-168, 98), (-140, 120), (-76, 128), (19, 112), (43, 94), (20, 72), (-57, 76), (-89, 88), (-149, 85)], 60, 3.2)
    plate('throat', 'support', 'dark_metal', 'Freiliegende Mittelschicht',
          [(9, 99), (68, 110), (164, 105), (223, 99), (273, 90), (273, 74), (216, 67), (109, 69), (17, 79)], 43, 2.5)
    plate('fore_cuff', 'support', 'shell', 'Vordere Keilschale',
          [(81, 88), (110, 108), (208, 112), (276, 100), (306, 85), (297, 72), (258, 69),
           (209, 78), (133, 75), (104, 67), (86, 70)], 61, 3)
    plate('palm', 'support', 'graphite', 'Vordere Griffmulde',
          [(82, 72), (112, 81), (199, 83), (231, 75), (210, 58), (188, 54), (122, 55), (102, 49), (90, 52)], 49, 3)
    # Durchblick unter der tragenden Brücke. Die Füße greifen in beide Schalen.
    plate('arch_liner', 'receiver', 'graphite', 'Dunkle Brückenunterkante',
          [(-118, 116), (-55, 166), (-36, 178), (72, 179), (93, 171), (162, 110), (141, 102),
           (74, 157), (-35, 157), (-89, 115)], 40, 2.6)
    plate('arch', 'receiver', 'shell', 'Offene Rückenbrücke',
          [(-127, 119), (-63, 172), (-40, 185), (66, 185), (90, 179), (164, 116), (154, 105),
           (133, 110), (72, 165), (-35, 165), (-90, 121)], 47, 3)
    # Umlaufender Lack folgt derselben Schräge auf beiden Wangen und dem Rücken.
    for i, (f, width) in enumerate(((-89, 13), (-69, 4))):
        def band_top(at):
            return 119 + (at + 127) * 53 / 64 + 0.6
        def band_bottom(at):
            return 121 + (at + 90) * 44 / 55 + 0.7
        plate(f'arch_band_{i}', 'receiver', 'accent', 'Brückenmarkierung',
              [(f, band_top(f)), (f+width, band_top(f+width)),
               (f+width+8, band_bottom(f+width+8)), (f+8, band_bottom(f+8))], 48.1, 0.6)
    plate('crown', 'sight', 'dark_metal', 'Eingelassene Scheitelleiste',
          [(-48, 181), (-34, 188), (59, 188), (75, 183), (58, 182), (-34, 182)], 31, 1.5)
    section('sight_tile', 'sight', 'anodized', 'Optisches Keramikfenster', -27, -7, 188, 26, 6, 2, 0.7)
    section('sight_lens', 'sight', 'energy', 'Optikindikator', -26, -24, 191, 13, 1.4, 0.5, 0.2)
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

        skin('badge', 'receiver', 'anodized', 'Typenschild',
             [(-131, 104), (-117, 116), (-67, 120), (-53, 115), (-61, 97), (-118, 96)], 30, 2.5)
        skin('seam', 'receiver', 'dark_metal', 'Schalenfuge',
             [(-51, 119), (10, 109), (28, 98), (25, 96), (8, 106), (-52, 116)], 30)
        skin('cheek_insert', 'stock', 'anodized', 'Schaftintarsie',
             [(-261, 95), (-246, 108), (-185, 111), (-164, 105), (-190, 103), (-242, 101)], 23.5)
        skin('cassette_plate', 'ammo', 'shell', 'Kassettenwange',
             [(65, 43), (94, 47), (104, 14), (122, -22), (111, -31), (96, -24), (79, 8)], 21, 2.5)
        for i in range(3):
            f, u=83+i*4, 18-i*9
            skin(f'index_{i}', 'ammo', 'anodized', 'Indexstrich', [(f, u), (f+14, u+3), (f+15, u+0.5), (f+1, u-2.5)], 23.2, 0.9, 0.15)
        skin('fore_insert', 'support', 'graphite', 'Versenktes Seitenfeld',
             [(153, 93), (163, 102), (235, 102), (260, 96), (253, 87), (178, 88)], 30.5, 2.4)
        for i in range(5):
            f=177+i*13
            skin(f'louvre_{i}', 'support', 'dark_metal', 'Staffellamelle',
                 [(f, 90), (f+6, 90), (f+11, 99), (f+5, 99)], 32.7, 1.8, 0.5)
        for i, (f, u) in enumerate(((-143, 98), (17, 89), (129, 90), (275, 84))):
            base=30 if i<2 else 30.5
            add(f'stud_{suffix}_{i}', 'receiver' if i<2 else 'support', 'dark_metal', 'Bündiger Sechskant',
                'cyl', 0.3, axis='x', c=(f, u), a0=min(side*(base-0.3), side*(base+1)),
                a1=max(side*(base-0.3), side*(base+1)), r=2.3, segs=6)
        skin('index_case', 'receiver', 'anodized', 'Anzeigefassung',
             [(9, 71), (22, 81), (69, 77), (74, 72), (66, 64), (24, 64)], 27.5, 2.2)
        for i in range(3):
            f=30+i*9
            skin(f'status_{i}', 'receiver', 'energy' if i<2 else 'metal', 'Statussegment',
                 [(f, 69), (f+4.5, 69), (f+7.5, 74), (f+3, 74)], 29.4, 1, 0.2)
        skin('grip_cheek', 'grip_controls', 'rubber', 'Weiche Griffwange',
             [(-27, 39), (-15, 44), (-13, 31), (-23, -13), (-34, -18), (-38, -15)], 19, 2.6, 1)
        for i in range(3):
            f, u=-32+i*2, -4+i*10
            skin(f'grip_rib_{i}', 'grip_controls', 'graphite', 'Griffrille',
                 [(f, u), (f+8, u+3), (f+9, u+5), (f+1, u+2)], 21.2, 1, 0.35)
        # Zentrierung lässt Schrift auf beiden Flanken lesbar bleiben.
        for key, group, role, word, f, u, x, size in (
                ('name', 'receiver', 'shell', 'TRESTLE', -93, 103, 32.4, 8),
                ('id', 'support', 'graphite', 'EXT / 02', 272, 93, 30.65, 5.5)):
            add(f'{key}_{suffix}', group, role, 'Typografie', 'text', 0, text=word,
                f=f, u=u, x=side*x, side=side, depth=0.35, size=size, align='CENTER')

    anchors = {
        'Socket_Hand': ('handle', -20, 23), 'Socket_SupportHand': ('palm', 158, 67),
        'Socket_Muzzle': ('face', 399, 84), 'Socket_Eye': ('arch_liner', -38, 161),
    }
    anchors = {k: dict(part=p, at=[f, u, 0], source='Annahme: Bezugspunkt des Spielmodells')
               for k, (p, f, u) in anchors.items()}
    # Stabile Editor-Bezüge des Spieltyps. Die Positionen liegen auf den neuen Außenflächen.
    points = {
        'grip.grip': ('handle', [-20, 23, 0]),
        'grip.support': ('palm', [158, 67, 0]),
        'grip.mag': ('cassette', [100, -10, 0]),
        'grip.charge': ('flank', [-30, 100, 29]),
        'eject': ('index_case_r', [42, 72, -29]),
    }
    return parts, anchors, {name: dict(part=part, at=at) for name, (part, at) in points.items()}
