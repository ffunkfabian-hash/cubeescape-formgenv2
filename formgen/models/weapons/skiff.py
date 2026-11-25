"""BT08 Skiff. Konturen, Fasen und Reliefs sind gestalterische Annahmen für das Spielmodell."""

from .sidearm_shell import Shell


# Zeit in BALLON-Frames bei 30 Hz. Die Zellbewegung ist ein fiktionaler
# Teleporteffekt im Spiel; die zweite Zelle beginnt verdeckt im Rumpf.
CELL_OUT = 44
CELL_SEAT = (22.7 + 26) / 2
COMMIT = 36
END = 45


def reload_action():
    return dict(de="Lichtzelle wechseln", frames=END,
                keys={"cheek_l": [(0, 0), (4, 0), (11, 1), (17, -CELL_SEAT / CELL_OUT),
                                  (END, -CELL_SEAT / CELL_OUT)],
                      "charged_cell": [(0, 0), (17, 0), (24, 1 + CELL_SEAT / CELL_OUT),
                                       (COMMIT, CELL_SEAT / CELL_OUT), (END, CELL_SEAT / CELL_OUT)],
                      "charge_signal": [(0, 0), (COMMIT - .5, 0), (COMMIT, 1), (END, 1)]},
                events=[(17, "cell_exchange"), (COMMIT, "rounds_in")], view=(.9, .4, .25))


def add_cell_pack(s, key, group, offset, charged):
    """Beide Wechselmodule tragen sechs Speicherzellen am animierten Rahmen."""
    # Lokale Kontur entlang der ansteigenden Kufe. Alle Maße sind Formannahmen.
    def profile(points):
        return [(300 + u, 32 + .17 * u + v) for u, v in points]

    outline = profile([(-44, -1), (-38, -8), (-29, -11), (29, -11), (39, -6),
                       (44, 1), (37, 9), (29, 11), (-29, 11), (-39, 7)])
    # Zwei Dreierreihen, eine separat modellierte Speicherzelle pro Spielschuss.
    openings = []
    for row in (4.8, -4.8):
        for col in (-20, -1, 18):
            openings.append(profile([(col-8, row-.8), (col-5.6, row-3.4),
                                     (col+5.4, row-3.4), (col+8, row-.7),
                                     (col+7.6, row+1.2), (col+5, row+3.4),
                                     (col-5.6, row+3.4), (col-8, row+1)]))
    cap = profile([(30, -7), (37, -5), (42, 1), (37, 7), (32, 8), (34, 1)])
    face = offset + 26 - CELL_SEAT
    s.plate(key, group, "shell", "Keramikrahmen des Wechselmoduls", outline, 9, 1.0,
            x=face - 4.5, cuts=[dict(shape="prof", pts=w, w=13, x=face-4.5) for w in [*openings, cap]],
            move=dict(kind="translate", vector_mm=(0, 0, CELL_OUT)))
    for number, contour in enumerate(openings, 1):
        s.plate(f"{key}_cell_{number}", group, "energy" if charged else "dark_metal",
                f"Speicherzelle {number}", contour, 7.6, .6, x=face-4.5, parent_part=key)
    s.plate(key + "_cap", group, "graphite", "Dunkle Stirnkappe", cap, 8.5, .45,
            x=face-4.5, parent_part=key)
    mark = profile([(35, -2.8), (37, -2.8), (39, .5), (36.7, 3.2), (35, 3.2), (37, .5)])
    s.plate(key + "_mark", group, "energy" if charged else "accent", "Ladungsmarke",
            mark, .12, .04, x=face-.18, parent_part=key)


def build(pilot):
    s = Shell("Skiff")
    s.plate("stern", "stock", "shell", "Helles Heck mit versetztem Fenster",
            [(-171, 73), (-154, 91), (-120, 105), (-78, 106), (-45, 97),
             (-22, 75), (-26, 52), (-65, 21), (-140, -9), (-165, -6), (-176, 10)],
            38, 2.6, cuts=[dict(shape="prof", w=47, pts=[
                (-150, 57), (-131, 72), (-91, 83), (-65, 81), (-53, 68),
                (-73, 49), (-132, 21), (-151, 22)])])
    s.plate("heel_trim", "stock", "graphite", "Dunkle hintere Fassung",
            [(-177, 55), (-170, 71), (-162, 64), (-166, 19), (-158, 3),
             (-140, -3), (-148, -13), (-172, -10), (-181, 4)], 40, 1.6)
    s.plate("hand_piece", "grip_controls", "graphite", "Geneigte Griffinsel",
            [(-22, 59), (20, 57), (36, 38), (26, 11), (7, -45), (-9, -63),
             (-40, -60), (-48, -48), (-36, -17), (-21, 18), (-31, 35)], 34, 2)
    s.inlay("hand_inset", "grip_controls", "rubber", "Dunkle Grifffläche",
            [(-11, 33), (12, 35), (16, 20), (0, -27), (-15, -48),
             (-34, -46), (-29, -29), (-13, 11)], 16.6, 18.1)
    s.plate("hull", "receiver", "graphite", "Dunkler Rumpf",
            [(-86, 87), (-63, 113), (-28, 124), (36, 120), (94, 112),
             (147, 107), (222, 98), (279, 88), (304, 70), (267, 48),
             (164, 32), (106, 30), (60, 38), (20, 47), (-26, 54)], 41, 2.7)
    s.plate("mantle", "receiver", "shell", "Gestufter heller Rücken",
            [(-86, 89), (-64, 115), (-38, 128), (-17, 128), (4, 124),
             (51, 123), (88, 115), (158, 111), (210, 101), (240, 89),
             (214, 85), (156, 93), (90, 94), (40, 102), (-2, 100),
             (-37, 89), (-65, 81)], 45, 1.7)
    s.plate("spine", "barrel", "dark_metal", "Flacher First mit abgesetztem Bug",
            [(145, 102), (202, 111), (420, 108), (518, 118), (566, 128),
             (594, 128), (610, 115), (615, 99), (598, 85), (550, 80),
             (496, 83), (414, 89), (234, 93), (186, 87)], 33, 1.9)
    s.plate("keel", "support", "shell", "Helle Kufe mit langem Durchblick",
            [(130, 45), (174, 52), (238, 65), (293, 62), (345, 59),
             (427, 63), (493, 76), (550, 101), (594, 110), (608, 103),
             (590, 82), (541, 62), (468, 39), (370, 22), (276, 10),
             (203, 11), (159, 21), (128, 33)], 43, 2)
    s.plate("palm", "support", "rubber", "Abgesetzte Handauflage",
            [(251, 32), (289, 41), (338, 45), (364, 40), (354, 29),
             (315, 17), (264, 15), (245, 21)], 46, 1.2)
    # Die beiden Wangen an der Kufe bilden das gemessene Außenmaß von BA08.
    cheek = [(255, 25), (279, 38), (317, 43), (347, 41), (337, 31),
             (307, 25), (266, 19)]
    s.plate("cheek_r", "support", "graphite", "Dunkle Kufenwange", cheek,
            26 - 22.7, .9, x=-CELL_SEAT)
    add_cell_pack(s, "cheek_l", "support", CELL_SEAT, charged=False)
    add_cell_pack(s, "charged_cell", "ammo", 0, charged=True)
    s.plate("charge_signal", "support", "energy", "Ladebestätigung auf der Kufe",
            [(366, 36), (377, 38), (385, 43), (374, 41)], .6, .2, x=20,
            move=dict(kind="translate", vector_mm=(0, 0, 2)))
    s.facet("nose", "barrel", "graphite", "Geschlossene Stirnfacette",
            606, 616, 100, 32, 25, 5, 1)
    s.inlay("badge", "receiver", "graphite", "Dunkles Namensfeld",
            [(-14, 109), (0, 119), (36, 118), (51, 112), (32, 107), (1, 105)],
            22.1, 23.1, .5)
    s.word("receiver", "shell", 16, 109, 23.3, 5)
    s.inlay("keel_light", "support", "energy", "Lichtfuge in der Kufe",
            [(381, 38), (417, 44), (428, 49), (390, 43)], 21.2, 22.1)
    for i, forward in enumerate((83, 96)):
        s.inlay(f"mark_{i}", "receiver", "accent", "Schräge Keramikmarke",
                [(forward, 102), (forward+5, 102), (forward+13, 110),
                 (forward+8, 110)], 22.2, 23.1)

    refs = {"Socket_Hand": ("hand_piece", [0, 0, 0]),
            "Socket_SupportHand": ("palm", [310, 26, 0]),
            "Socket_Muzzle": ("nose", [616, 100, 0]),
            "Socket_LoadingGate": ("palm", [302, 32, 23])}
    points = {"grip.grip": refs["Socket_Hand"], "grip.support": refs["Socket_SupportHand"],
              "grip.mag": refs["Socket_LoadingGate"], "grip.charge": refs["Socket_LoadingGate"],
              "eject": ("hull", [65, 81, -20.5])}
    return s.finish_with_pilot_sight(refs, points, pilot)
