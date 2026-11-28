"""BT13 Moraine. Konturen und Fasen sind gestalterische Annahmen für die Spielgrafik."""

from .sidearm_shell import Shell


def build(pilot):
    s = Shell("Moraine")
    s.plate("heel", "stock", "graphite", "Abgestufte dunkle Ferse",
            [(-221, 107), (-204, 126), (-163, 129), (-149, 105),
             (-180, 88), (-185, 54), (-200, 39), (-216, 43)], 39, 2)
    s.plate("ledge", "stock", "shell", "Kurze überhängende Heckstufe",
            [(-223, 107), (-202, 132), (-158, 136), (-135, 127), (-79, 121),
             (-59, 99), (-100, 97), (-146, 113), (-180, 109), (-198, 84),
             (-218, 83)], 42, 1.8)
    s.plate("ridge", "receiver", "graphite", "Dunkler Rücken zwischen den Stufen",
            [(-160, 119), (-128, 137), (-84, 146), (-10, 145), (24, 138),
             (71, 142), (118, 139), (170, 121), (204, 100), (166, 84),
             (84, 83), (36, 76), (-12, 66), (-49, 82), (-87, 104)], 45, 2)
    s.plate("shoulder", "receiver", "shell", "Zweigeteilte helle Schulterkante",
            [(-148, 129), (-114, 143), (-81, 149), (-13, 145), (17, 137),
             (63, 141), (96, 136), (73, 125), (20, 122), (-17, 129),
             (-67, 121), (-92, 115), (-121, 120)], 48, 1.5)
    # W1-Fuß an der gemessenen Unterkante des BASIC-13-Referenznetzes.
    s.plate("saddle", "receiver", "dark_metal", "Ebener Sitz für die D-Linse",
            [(-76, 145), (-65, 152.5), (-9, 152.5), (1, 146),
             (-13, 140), (-64, 141)], 30, .7)
    s.inlay("badge", "receiver", "graphite", "Schriftfeld an der Schulter",
            [(-118, 132), (-99, 140), (-43, 138), (-50, 130), (-99, 125)],
            23.8, 25.1)
    s.word("receiver", "shell", -79, 131, 25.3, 5.5)
    s.plate("hand_piece", "grip_controls", "rubber", "Dunkle freistehende Griffinsel",
            [(-40, 84), (-1, 90), (20, 74), (25, 55), (11, 28), (0, -8),
             (1, -33), (-12, -47), (-42, -43), (-51, -29), (-35, 14),
             (-22, 48), (-41, 63)], 34, 1.8)
    s.inlay("hand_inset", "grip_controls", "graphite", "Schräges Griffrelief",
            [(-11, 49), (9, 49), (8, 31), (-14, -17), (-19, -32),
             (-31, -29), (-27, -10)], 16.8, 17.8)

    s.plate("stone", "ammo", "graphite", "Geschlossener facettierter Mittelkörper",
            [(36, 103), (72, 134), (119, 142), (176, 135), (209, 114),
             (228, 80), (215, 39), (180, 8), (133, -2), (86, 7),
             (49, 35), (31, 68)], 90, 4)
    s.inlay("scree", "ammo", "shell", "Helle versetzte Schicht am Mittelkörper",
            [(39, 87), (62, 113), (106, 134), (157, 132), (194, 118),
             (212, 98), (180, 99), (145, 88), (101, 63), (62, 50),
             (43, 57)], 44, 56.5, 2)
    s.inlay("basalt", "ammo", "dark_metal", "Dunkle Basaltfacette unter der Querfuge",
            [(53, 55), (91, 63), (142, 91), (180, 101), (210, 97),
             (216, 78), (197, 51), (166, 26), (123, 16), (78, 28)], 44.5, 58.5, 2)
    # Die zwei kleinsten Seitenfacetten bestimmen das Außenmaß wie im BA13-GLB.
    s.inlay("boss", "ammo", "anodized", "Kleine erhabene Seitenfacette",
            [(92, 57), (135, 81), (174, 92), (187, 84), (159, 57),
             (123, 43), (98, 44)], 58, 141.83 / 2, 1.5)
    s.inlay("seam", "mechanism", "energy", "Türkise Spur auf der hellen Facette",
            [(60, 78), (98, 87), (137, 106), (160, 110),
             (141, 103), (101, 81), (62, 72)], 56.3, 57.4)
    s.plate("fore_rest", "support", "graphite", "Abgesetzte kurze Handauflage",
            [(195, 79), (224, 93), (298, 99), (317, 87),
             (304, 73), (246, 68), (216, 52), (196, 56)], 42, 1.4)
    axis = pilot["ANCHORS"]["Socket_Muzzle"]["at"][1]
    s.facet("spine", "barrel", "dark_metal", "Gerader dunkler Frontsteg",
            185, 398, axis, 33, 30, 6, .9)
    s.facet("jacket", "barrel", "shell", "Helle kantige Frontschale",
            220, 357, axis, 51, 48, 10, 1.4)
    s.facet("cap", "barrel", "graphite", "Geschlossene gerade Stirnkappe",
            378, 401, axis, 42, 38, 7, 1)
    for i, f in enumerate((237, 248, 259)):
        s.inlay(f"mark_{i}", "barrel", "accent", "Kurze Flankenmarke",
                [(f, 108), (f+4, 108), (f+11, 118), (f+7, 118)], 25.2, 26)
    refs = {"Socket_Hand": ("hand_piece", [0, 0, 0]),
            "Socket_SupportHand": ("fore_rest", [253, 77, 0]),
            "Socket_Muzzle": ("cap", [401, axis, 0]),
            "Socket_LoadingGate": ("boss_l", [132, 64, 70])}
    points = {"grip.grip": refs["Socket_Hand"], "grip.support": refs["Socket_SupportHand"],
              "grip.mag": ("stone", [129, 74, 0]), "grip.gate": refs["Socket_LoadingGate"],
              "grip.charge": refs["Socket_LoadingGate"], "eject": refs["Socket_LoadingGate"]}
    return s.finish_with_pilot_sight(refs, points, pilot)
