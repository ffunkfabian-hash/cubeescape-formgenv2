"""BT09 Avocet. Außenkonturen und Stufen sind Formannahmen für die Spielgrafik."""

from copy import deepcopy

from .sidearm_shell import Shell


def build(pilot):
    s = Shell("Avocet")
    # Das Heck bildet eine kurze offene Sichel. Die gerade Front trägt zwei
    # versetzte Keramikflächen mit einem schmalen dunklen Zwischenraum.
    s.plate("crescent", "stock", "shell", "Sichelförmige Heckschale",
            [(-306, 111), (-286, 129), (-248, 140), (-207, 138), (-149, 123),
             (-94, 112), (-43, 106), (-40, 88), (-92, 89), (-147, 100),
             (-205, 111), (-240, 111), (-265, 100), (-273, 77), (-267, 52),
             (-243, 42), (-214, 34), (-206, 25), (-214, 21), (-245, 26),
             (-280, 28), (-304, 58), (-313, 88)], 36, 2.5)
    s.plate("tail_shadow", "stock", "graphite", "Dunkle Außenkante der Sichel",
            [(-308, 112), (-301, 117), (-304, 92), (-298, 69), (-280, 43),
             (-255, 34), (-223, 25), (-214, 21), (-239, 22), (-278, 32), (-301, 49),
             (-315, 77), (-316, 95)], 39, 1.4)
    s.plate("sweep", "receiver", "graphite", "Schwebend auslaufender Rücken",
            [(-145, 107), (-104, 125), (-65, 138), (-27, 138), (8, 127),
             (91, 127), (154, 119), (290, 106), (386, 103), (432, 98),
             (398, 84), (266, 78), (167, 64), (96, 45), (46, 42),
             (2, 55), (-48, 76), (-104, 85)], 37, 2.0)
    s.plate("deck", "receiver", "dark_metal", "Zweistufiger Visierrücken",
            [(-78, 133), (-65, 140), (-26, 140), (6, 131), (94, 129),
             (134, 129), (148, 123), (99, 123), (2, 123), (-32, 134)], 28, 1)
    s.plate("wing", "receiver", "shell", "Vorgezogene helle Flanke",
            [(-119, 112), (-74, 130), (-45, 133), (10, 118), (94, 116),
             (191, 106), (232, 97), (196, 87), (121, 83), (50, 64),
             (21, 61), (-18, 75), (-67, 92)], 40, 1.8)
    s.plate("hand_piece", "grip_controls", "graphite", "Geschwungene Griffinsel",
            [(-31, 80), (26, 66), (38, 48), (30, 27), (4, -21),
             (1, -42), (12, -54), (5, -61), (-23, -56), (-44, -43),
             (-42, -26), (-19, 24), (-16, 43), (-34, 59)], 32, 2)
    s.inlay("grip_leaf", "grip_controls", "rubber", "Blattförmiges Griffrelief",
            [(-7, 40), (18, 42), (21, 31), (-6, -19), (-12, -38),
             (-8, -48), (-28, -41), (-29, -28), (-9, 17)], 15.7, 17.4)
    s.plate("pendant", "ammo", "graphite", "Kurzes facettiertes Energiesiegel",
            [(60, 65), (112, 74), (125, 52), (102, 19), (73, 2),
             (59, 7), (52, 30)], 35, 1.7)
    s.inlay("seal", "ammo", "energy", "Schräge Lichtmarke",
            [(66, 28), (94, 37), (85, 27), (65, 19)], 17.2, 18)
    s.plate("palm_leaf", "support", "graphite", "Abgesetzte dunkle Handauflage",
            [(142, 76), (232, 92), (370, 96), (347, 80), (259, 65),
             (197, 50), (153, 48), (129, 57)], 38, 1.7)
    s.facet("quill", "barrel", "dark_metal", "Gerader facettierter Mittelsteg",
            188, 764, 96, 24, 25, 5, 1.1)
    s.plate("flight", "support", "shell", "Nach hinten gestufte Keramikflanke",
            [(164, 84), (233, 105), (315, 111), (415, 111), (400, 101),
             (320, 99), (276, 82), (242, 68), (188, 59), (199, 70),
             (163, 66), (181, 78), (155, 75)], 34, 1.3)
    s.plate("long_tile", "barrel", "shell", "Längsfeld auf dem Mittelsteg",
            [(431, 109), (455, 112), (681, 112), (697, 106), (692, 101),
             (484, 101), (454, 97), (414, 97)], 27, 1.1)
    s.facet("tip", "barrel", "graphite", "Kurze bündige Stirnkappe",
            739, 780, 96, 30, 32, 6, 1.2)
    s.inlay("front_glint", "barrel", "energy", "Lichtmarke in der Stirnkappe",
            [(749, 99), (769, 99), (773, 96), (753, 96)], 14.8, 15.4)
    s.inlay("badge", "receiver", "graphite", "Dunkles Schriftfeld",
            [(-70, 111), (-50, 121), (12, 107), (24, 101), (-37, 102)], 19.7, 20.7)
    s.word("receiver", "shell", -24, 104, 20.8, 5.2)
    for i, f in enumerate((72, 84, 96)):
        s.inlay(f"quill_mark_{i}", "receiver", "accent", "Schmale Flankenmarke",
                [(f, 95), (f+4, 95), (f+12, 107), (f+8, 107)], 19.8, 20.6)

    refs = {"Socket_Hand": ("hand_piece", [0, 0, 0]),
            "Socket_SupportHand": ("palm_leaf", [253, 67, 0]),
            "Socket_Muzzle": ("tip", [780, 96, 0]),
            "Socket_MagWell": ("pendant", [84, 32, 0]),
            "Socket_Bolt": ("wing", [30, 92, 20])}
    points = {"grip.grip": refs["Socket_Hand"], "grip.support": refs["Socket_SupportHand"],
              "grip.mag": refs["Socket_MagWell"], "grip.charge": refs["Socket_Bolt"],
              "eject": ("wing", [33, 95, -20])}
    parts, anchors, points = s.finish_with_pilot_sight(refs, points, pilot)
    anchors["Socket_Objective"] = deepcopy(pilot["ANCHORS"]["Socket_Objective"])
    anchors["Socket_Objective"]["at"] = list(anchors["Socket_Objective"]["at"])
    return parts, anchors, points
