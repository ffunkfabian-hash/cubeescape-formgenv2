"""BT10 Calyx. Konturen und Fasen sind Formannahmen für die Spielgrafik."""

from .sidearm_shell import Shell


def build(pilot):
    s = Shell("Calyx")
    # Die helle Heckschale kippt nach hinten ab. Die dunkle Schulter zieht den
    # Blick auf das lange Fenster mit seinem facettierten Kern.
    s.plate("heel", "stock", "graphite", "Dunkler Abschluss der Heckschale",
            [(-222, 74), (-209, 93), (-190, 96), (-192, 48), (-155, 17),
             (-169, 6), (-209, 18), (-226, 42)], 35, 2.5)
    s.plate("tail_fold", "stock", "shell", "Gefaltete kurze Heckschale",
            [(-216, 77), (-198, 97), (-144, 107), (-106, 124), (-69, 118),
             (-62, 91), (-103, 74), (-155, 64), (-185, 43), (-193, 28),
             (-212, 37), (-218, 53)], 38, 2.1)
    s.inlay("tail_ridge", "stock", "anodized", "Flache Falte im Heck",
            [(-201, 77), (-180, 89), (-127, 99), (-143, 91), (-192, 74)],
            18.8, 19.6)
    s.plate("backbone", "receiver", "graphite", "Geneigte Schulter",
            [(-138, 97), (-114, 122), (-76, 135), (-25, 133), (25, 130),
             (90, 118), (122, 97), (127, 64), (96, 48), (48, 47), (23, 57),
             (-24, 67), (-72, 71), (-120, 80)], 39, 2)
    s.plate("mantle", "receiver", "shell", "Schräger keramischer Schulterpanzer",
            [(-124, 108), (-95, 132), (-63, 139), (-28, 130), (29, 127),
             (76, 116), (109, 98), (89, 90), (29, 105), (-15, 103),
             (-55, 87), (-93, 87)], 43, 1.8)
    s.plate("saddle", "receiver", "dark_metal", "Kurze ebene Visierauflage",
            [(-23, 128), (-15, 136.7), (35, 136.7), (44, 130),
             (34, 124), (-14, 124)], 30, .8)
    s.inlay("signature", "receiver", "graphite", "Schriftfeld in der Schulter",
            [(-79, 113), (-62, 124), (-18, 118), (-9, 113), (-30, 108), (-67, 104)],
            21.2, 22.3)
    s.word("receiver", "shell", -45, 112, 22.5, 5.1)
    s.plate("grip_leaf", "grip_controls", "rubber", "Dunkle rückwärts geneigte Griffschale",
            [(-31, 78), (14, 67), (31, 48), (19, 25), (2, -7),
             (-2, -39), (-14, -52), (-39, -46), (-47, -35), (-35, -9),
             (-23, 21), (-18, 42), (-37, 59)], 34, 1.8)
    s.inlay("grip_relief", "grip_controls", "graphite", "Flaches Relief der Griffschale",
            [(-10, 44), (12, 42), (11, 29), (-10, -10), (-13, -33),
             (-25, -40), (-34, -33), (-22, -3)], 16.8, 17.8)

    s.plate("lower_petal", "support", "shell", "Tiefer Kelch unter dem Sichtfenster",
            [(66, 83), (103, 87), (125, 68), (156, 39), (194, 27),
             (230, 28), (267, 52), (291, 76), (317, 88), (306, 64),
             (281, 43), (253, 19), (219, 7), (182, 7), (135, 19),
             (104, 42), (77, 48), (52, 61)], 43, 1.6)
    s.plate("palm", "support", "graphite", "Dunkler Fuß der Kelchschale",
            [(135, 23), (179, 12), (220, 12), (249, 22), (264, 32),
             (252, 15), (224, 2), (183, 1), (151, 9), (127, 18)], 40, 1.1)
    # Außenmaß des BASIC-10-Referenzmodells, über beide Flanken gemessen.
    s.inlay("flank", "support", "anodized", "Erhabene Wange am Kelch",
            [(94, 62), (111, 59), (151, 26), (173, 20), (145, 22), (108, 44)],
            21.1, 46.70 / 2, .65)
    s.plate("cell_back", "ammo", "dark_metal", "Dunkler Grat hinter dem Kern",
            [(101, 76), (151, 80), (189, 81), (198, 72), (183, 66), (119, 65)],
            19, 1)
    s.plate("prism", "ammo", "energy", "Türkisfarbener facettierter Fusionskern",
            [(141, 73), (166, 90), (213, 86), (246, 68),
             (214, 50), (174, 47), (150, 57)], 27, 2.5)
    s.inlay("core_facet", "ammo", "anodized", "Metallische Facette am unteren Kernrand",
            [(148, 62), (172, 54), (213, 55), (242, 67), (216, 51), (174, 47)],
            13.1, 13.8)
    s.plate("brow", "cooling", "shell", "Obere Kelchlippe",
            [(66, 116), (98, 125), (144, 125), (174, 119), (233, 119),
             (267, 113), (256, 106), (152, 106), (112, 110), (90, 105)],
            40, 1.4)
    s.facet("straight_spine", "barrel", "dark_metal", "Gerader Steg der Front",
            97, 404, 96, 24, 23, 4, .9)
    s.facet("front_jacket", "barrel", "shell", "Gerade facettierte Frontschale",
            283, 397, 96, 37, 34, 7, 1.3)
    s.facet("end_tile", "barrel", "graphite", "Geschlossene dunkle Stirn",
            387, 416, 96, 33, 29, 6, 1)
    s.inlay("end_light", "barrel", "energy", "Kurze Lichtmarke an der Stirn",
            [(398, 98), (410, 98), (412, 95), (400, 95)], 16.3, 16.9)
    for i, f in enumerate((294, 305, 316)):
        s.inlay(f"streak_{i}", "barrel", "accent", "Schräge Flankenmarke",
                [(f, 94), (f+4, 94), (f+10, 103), (f+6, 103)], 18.3, 18.9)

    refs = {"Socket_Hand": ("grip_leaf", [0, 0, 0]),
            "Socket_SupportHand": ("palm", [206, 10, 0]),
            "Socket_Cell": ("prism", [188, 69, 0]),
            "Socket_Muzzle": ("end_tile", [416, 96, 0])}
    points = {"grip.grip": refs["Socket_Hand"], "grip.support": refs["Socket_SupportHand"],
              "grip.mag": refs["Socket_Cell"], "grip.charge": refs["Socket_Cell"]}
    return s.finish_with_pilot_sight(refs, points, pilot)
