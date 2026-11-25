"""BT12 Filament. Außenkonturen, Winkel und Fasen sind Formannahmen fürs Spielmodell."""

from math import cos, radians, sin

from .sidearm_shell import Shell


def halo(outer, inner):
    """Seitliches C-Profil mit freier Mitte und einer Öffnung zum Heck."""
    angles = [radians(-148 + i * 296 / 32) for i in range(33)]
    return [(157 + radius * cos(a), 66 + radius * sin(a))
            for radius, arc in ((outer, angles), (inner, reversed(angles))) for a in arc]


def build(pilot):
    s = Shell("Filament")
    s.plate("tail_blade", "stock", "shell", "Flache, nach hinten auslaufende Keramikfahne",
            [(-254, 85), (-231, 100), (-158, 109), (-99, 128), (-63, 125),
             (-53, 108), (-96, 94), (-148, 86), (-205, 84), (-239, 73)], 35, 2)
    s.plate("tail_edge", "stock", "graphite", "Dunkle Unterkante mit kurzer Ferse",
            [(-256, 85), (-243, 91), (-236, 82), (-188, 87), (-123, 91),
             (-140, 80), (-211, 72), (-236, 58), (-247, 56)], 34, 1.6)
    s.plate("bridge", "receiver", "graphite", "Dunkler Rücken über dem offenen Leuchtring",
            [(-128, 108), (-86, 129), (-38, 133), (53, 130), (128, 125),
             (170, 123), (199, 111), (215, 96), (201, 88), (170, 106),
             (125, 109), (67, 103), (27, 84), (-12, 75), (-71, 88)], 35, 1.8)
    s.plate("mantle", "receiver", "shell", "Lange Keramikschulter mit flachem Scheitel",
            [(-126, 111), (-84, 133), (-43, 134), (18, 127), (56, 130),
             (141, 126), (169, 118), (137, 113), (66, 115), (14, 103),
             (-31, 99), (-77, 110)], 40, 1.5)
    # Die Unterseite des H3-Fußes liegt im gepinnten BASIC-12 bei u=136,5.
    s.plate("deck", "receiver", "dark_metal", "Bündige Auflage für das H3",
            [(-27, 130), (-17, 136.5), (39, 136.5), (50, 130),
             (37, 125), (-19, 124)], 27, .7)
    s.inlay("badge", "receiver", "graphite", "Schriftfeld in der Schulter",
            [(-86, 119), (-73, 126), (-13, 123), (-23, 114), (-77, 113)], 19.7, 20.7)
    s.word("receiver", "shell", -49, 117, 21, 5.5)
    s.plate("grip", "grip_controls", "rubber", "Abgesetzte schlanke Griffinsel",
            [(-36, 84), (7, 90), (26, 65), (20, 45), (3, 9), (-4, -23),
             (2, -37), (-9, -47), (-36, -41), (-45, -28), (-30, 13),
             (-22, 47), (-42, 66)], 32, 1.7)
    s.inlay("grip_inset", "grip_controls", "graphite", "Schmales Flankenrelief",
            [(-10, 50), (9, 52), (4, 33), (-12, -7), (-13, -25),
             (-26, -31), (-30, -24)], 15.6, 16.7)
    s.plate("halo_back", "ammo", "graphite", "Nach hinten offener Ring mit Durchblick",
            halo(53, 36), 39, 1.1)
    # Außenmaß der beiden Leuchtflanken zusammen wie BASIC-12 im GLB.
    s.inlay("halo_light", "ammo", "energy", "Leuchtspur auf beiden Ringflanken",
            halo(48, 43), 19.1, 48.8 / 2, .7)
    s.plate("lower_ribbon", "support", "shell", "Unter dem Ring nach hinten auslaufender Schweif",
            [(49, 9), (79, 18), (115, 22), (151, 20), (174, 24), (202, 47),
             (229, 83), (260, 98), (276, 87), (243, 67), (216, 33),
             (186, 12), (157, 5), (107, 10), (76, 10), (43, 4)], 37, 1.4)
    s.plate("palm", "support", "rubber", "Dunkle Handauflage vor dem Ring",
            [(205, 44), (233, 76), (268, 92), (302, 87), (287, 73),
             (249, 64), (225, 44), (207, 36)], 39, 1)
    axis = pilot["ANCHORS"]["Socket_Muzzle"]["at"][1]
    s.facet("axis_body", "barrel", "dark_metal", "Gerader dunkler Laufsteg",
            198, 471, axis, 24, 24, 5, .9)
    s.facet("front_tile", "barrel", "shell", "Abgesetzte gerade Frontschale",
            254, 406, axis, 33, 33, 6, 1.1)
    s.facet("nose", "barrel", "graphite", "Schmale eingefasste Stirn",
            447, 475, axis, 31, 30, 6, 1)
    s.facet("glint", "barrel", "energy", "Bündiges leuchtendes Stirnfeld",
            474, 476, axis, 23, 22, 5, .3)
    for i, f in enumerate((271, 281, 291)):
        s.inlay(f"stripe_{i}", "barrel", "accent", "Schräge Flankenmarkierung",
                [(f, 92), (f+3, 92), (f+9, 101), (f+6, 101)], 16.2, 17)
    refs = {"Socket_Hand": ("grip", [0, 0, 0]),
            "Socket_SupportHand": ("palm", [251, 72, 0]),
            "Socket_Muzzle": ("glint", [476, axis, 0]),
            "Socket_Cell": ("halo_back", [202, 66, 0])}
    points = {"grip.grip": refs["Socket_Hand"], "grip.support": refs["Socket_SupportHand"],
              "grip.mag": refs["Socket_Cell"], "grip.charge": refs["Socket_Cell"]}
    return s.finish_with_pilot_sight(refs, points, pilot)
