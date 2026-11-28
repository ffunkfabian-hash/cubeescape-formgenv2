"""Lark (BT07). Die Außenkonturen sind freie Formannahmen für die sichtbare Spielhülle."""

from copy import deepcopy

from .sidearm_shell import Shell

# Formannahme für die kompakte Silhouette der dritten Skizze.
LIMB_FACTOR = 0.67


def build(pilot):
    parts = deepcopy(pilot["PARTS"])
    body = {part["id"]: part for part in parts}
    body["riser"]["mat"] = "graphite"
    body["text_l"]["text"] = "LARK"

    shell = Shell("Lark")
    # Die sichtbare Außenschale erhält ein geknicktes Profil mit eingezogener
    # Mitte. Die Aussparung des B1 und seine seitliche Ausladung stammen vom Piloten.
    body["riser"]["pts"] = [
        (-19, -218), (29, -218), (54, -184), (66, -126), (52, -76),
        (21, -43), (12, -26), (12, 29), (39, 54), (67, 79),
        (74, 139), (56, 180), (24, 218), (-17, 218),
        (-40, 181), (-52, 149), (-46, 115), (-24, 60),
        (-22, 29), (-22, -42), (-43, -74), (-56, -117),
        (-53, -170), (-32, -199),
    ]
    body["riser"]["cuts"].append(dict(
        shape="prof", w=102,
        pts=[(-24, 122), (-13, 94), (9, 72), (33, 78), (43, 102),
             (36, 124), (9, 155), (-8, 158), (-21, 146)],
    ))
    # Breite helle Schultern und ein zurückgesetztes dunkles Endstück bilden
    # die neue Silhouette. Die Formen sind ausschließlich äußere Verkleidung.
    shoulder = [(-87, 393), (-32, 376), (22, 355), (51, 322),
                (75, 274), (76, 226), (57, 184), (30, 166),
                (5, 181), (-21, 209), (-24, 247), (-9, 292),
                (-19, 327), (-57, 362), (-88, 382)]
    notch = [(4, 227), (23, 209), (47, 225), (49, 258),
             (30, 290), (8, 305), (17, 267)]
    shell.plate("crown", "riser", "shell", "Helle geknickte Schulter",
                shoulder, 37, 2.3, cuts=[dict(shape="prof", pts=notch, w=43)])
    lower = [(-91, -369), (-53, -326), (-25, -291), (-21, -261),
             (-44, -215), (-45, -184), (-26, -150), (8, -131),
             (43, -145), (67, -179), (70, -214), (51, -258),
             (23, -301), (-26, -346), (-76, -371)]
    shell.plate("skirt", "riser", "shell", "Unterer abgesetzter Schalenbogen",
                lower, 35, 2.3)
    shell.inlay("shoulder_inset", "riser", "graphite", "Dunkles Schulterfeld",
                [(-45, 362), (10, 337), (37, 312), (56, 276),
                 (50, 301), (29, 333), (-3, 351)], 18.0, 19.1, .7)
    # Seitlich eingelassene Anzeige mit zwei hellen Segmenten. In Spielansicht
    # bildet sie einen Akzent am unteren Gehäuse, abseits des Pinvisiers.
    pod = [(-29, -201), (-16, -223), (23, -239), (40, -225),
           (44, -199), (29, -172), (9, -165), (-20, -178)]
    shell.inlay("status_pod", "riser", "graphite", "Statuskapsel", pod, 17, 21.8, 1.4)
    for index, level in enumerate((-203, -194)):
        shell.inlay(f"status_bar_{index}", "riser", "energy", "Lichtsegment",
                    [(-12, level), (17, level - 11), (20, level - 7),
                     (-9, level + 5)], 21.5, 22.5, .4)
    parts.extend(shell.parts)

    anchors = deepcopy(pilot["ANCHORS"])
    points = deepcopy(pilot["POINTS"])
    for record in (*anchors.values(), *points.values()):
        record["at"] = list(record["at"])
    return parts, anchors, points
