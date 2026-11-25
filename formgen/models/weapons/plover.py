"""BT11 Plover. Außenkonturen und Fasen sind Entwurfsmaße des Spielmodells."""

from copy import deepcopy

from .sidearm_shell import Shell


def build(pilot):
    s = Shell("Plover")
    s.plate("tail_frame", "stock", "graphite", "Gefalteter offener Heckrahmen",
            [(-277, 107), (-252, 119), (-79, 113), (-61, 91), (-106, 67),
             (-216, 16), (-249, 13), (-273, 34)], 32, 2,
            cuts=[dict(shape="prof", w=44, pts=[(-248, 92), (-124, 92),
                       (-131, 81), (-221, 40), (-240, 40)])])
    s.plate("tail_tile", "stock", "shell", "Helle Dachkante mit abgesetzter Ferse",
            [(-281, 109), (-257, 123), (-111, 122), (-72, 114), (-91, 101),
             (-205, 103), (-252, 102), (-252, 67), (-264, 47), (-278, 57)], 37, 1.8)
    s.plate("shoulder", "receiver", "graphite", "Dunkle Schulter mit gestuftem Rücken",
            [(-118, 112), (-95, 126), (-39, 133), (64, 133), (77, 125),
             (155, 125), (192, 111), (185, 81), (98, 57), (33, 54),
             (-21, 70), (-70, 87), (-112, 89)], 39, 1.8)
    # Unterkanten der beiden originalen Z2-Füße im BASIC-11-Netz.
    s.plate("stepped_deck", "receiver", "dark_metal", "Zweistufiges Deck für das Z2",
            [(-30, 131), (-18, 138.5), (58, 138.5), (70, 130.5),
             (154, 130.5), (162, 125), (150, 121), (67, 121), (54, 129),
             (-22, 129)], 29, .7)
    s.plate("cheek", "receiver", "shell", "Versetzte Wange am Heck",
            [(-107, 111), (-80, 126), (-31, 129), (16, 126), (46, 108),
             (30, 95), (-31, 92), (-66, 95), (-91, 88)], 42, 1.6)
    s.inlay("badge", "receiver", "graphite", "Dunkles Schriftfeld",
            [(-77, 113), (-61, 121), (-11, 118), (-19, 108), (-71, 106)], 20.8, 21.8)
    s.word("receiver", "shell", -45, 111, 22, 5.7)
    s.plate("grip_panel", "grip_controls", "rubber", "Dunkle Griffinsel",
            [(-27, 76), (25, 69), (34, 44), (9, 5), (-4, -34),
             (0, -47), (-14, -55), (-42, -45), (-47, -32), (-28, 14),
             (-16, 44), (-35, 61)], 33, 1.7)
    s.plate("keel", "support", "graphite", "Tiefer Kiel mit langer freier Unterkante",
            [(37, 88), (97, 93), (201, 77), (388, 77), (468, 84), (477, 72),
             (399, 57), (246, 31), (121, 24), (81, 31), (44, 52)], 33, 1.7)
    s.plate("cell_field", "ammo", "dark_metal", "Langes Feld für das Lichtband",
            [(69, 104), (98, 114), (348, 107), (409, 95), (381, 73),
             (138, 60), (80, 73)], 30, 1.3)
    s.inlay("ribbon", "ammo", "energy", "Durchgehendes türkisfarbenes Lichtband",
            [(80, 90), (100, 95), (380, 95), (393, 91), (379, 86), (94, 86)],
            14.7, 16.3)
    # Drei verschieden lange Lamellen geben der Außenform ihren Rhythmus.
    for i, (f, bottom) in enumerate(((96, 28), (189, 36), (282, 53)), 1):
        s.inlay(f"vane_{i}", "cooling", "shell", "Schräg gefaltete Keramiklamelle",
                [(f, 106), (f+27, 112), (f+73, 112), (f+50, 102),
                 (f+7, bottom+14), (f-7, bottom), (f-36, bottom+2),
                 (f-14, bottom+19), (f+13, 99)], 14.8, 22.1, 1.1)
    s.plate("rest", "support", "rubber", "Schmale Handauflage unter den Lamellen",
            [(125, 32), (245, 38), (290, 43), (281, 32), (225, 23),
             (146, 18), (113, 21)], 35, .9)
    axis = pilot["ANCHORS"]["Socket_Muzzle"]["at"][1]
    s.facet("beam", "barrel", "dark_metal", "Freiliegender gerader Mittelsteg",
            167, 658, axis, 23, 22, 4, .8)
    s.facet("jacket", "barrel", "shell", "Lange ebene Frontschale",
            372, 608, axis, 32, 33, 6, 1.1)
    s.facet("cap", "barrel", "graphite", "Geschlossene facettierte Stirnkappe",
            642, 679, axis, 29, 27, 5, 1)
    s.inlay("front_mark", "barrel", "energy", "Helle Linie in der Stirnkappe",
            [(651, 94), (672, 94), (668, 91), (647, 91)], 14.2, 15)
    for i, f in enumerate((395, 405, 415)):
        s.inlay(f"stripe_{i}", "barrel", "accent", "Kurze schräge Kennmarke",
                [(f, 87), (f+4, 87), (f+10, 97), (f+6, 97)], 15.7, 16.5)

    refs = {"Socket_Hand": ("grip_panel", [0, 0, 0]),
            "Socket_SupportHand": ("rest", [204, 25, 0]),
            "Socket_Cell": ("cell_field", [227, 90, 0]),
            "Socket_Muzzle": ("cap", [679, axis, 0])}
    points = {"grip.grip": refs["Socket_Hand"], "grip.support": refs["Socket_SupportHand"],
              "grip.mag": refs["Socket_Cell"], "grip.charge": refs["Socket_Cell"]}
    parts, anchors, points = s.finish_with_pilot_sight(refs, points, pilot)
    objective = deepcopy(pilot["ANCHORS"]["Socket_Objective"])
    anchors["Socket_Objective"] = dict(objective, at=list(objective["at"]))
    return parts, anchors, points
