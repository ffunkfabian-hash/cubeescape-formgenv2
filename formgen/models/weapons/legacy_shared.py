"""Unveränderte Griff-/Visier-Gleichteile der ursprünglichen Trestle-Familie.

Vesper und Heron behalten ihre Außenflächen unabhängig vom BASIC-Pass an BT01.
Alle Maße sind die bisherigen Formannahmen; diese IDs bleiben bestehen.
"""


def build(*, optic_base=154):
    parts = []

    def add(key, group, role, label, shape, bevel, **geometry):
        parts.append(dict(id=key, asm=group, mat=role, de=label, en=key.replace('_', ' '),
                          func=label, attach='Gleichteil der T-Linie', shape=shape,
                          bevel=bevel, segs_bevel=3, **geometry))

    def plate(key, group, role, label, pts, width, bevel=2, x=0, **geometry):
        add(key, group, role, label, 'prof', bevel, pts=pts, w=width, x=x, **geometry)

    def section(key, group, role, label, start, end, level, width, height, corner, bevel=1):
        a, b = width / 2, height / 2
        pts = [(-a+corner, -b), (a-corner, -b), (a, -b+corner), (a, b-corner),
               (a-corner, b), (-a+corner, b), (-a, b-corner), (-a, -b+corner)]
        add(key, group, role, label, 'xprof', bevel, f0=start, f1=end, cu=level, pts=pts)

    # Alle Fensterteile beziehen sich auf dieselbe Auflage. Der Standardwert
    # erhält den Sitz der Bestandsmodelle. Die Form des Rahmens bleibt identisch.
    u = optic_base
    plate('optic_foot', 'sight', 'graphite', 'Visierfuß',
          [(-40,u),(18,u),(17,u+4),(8,u+7),(-29,u+7),(-40,u+4)], 36, 1.4)
    add('optic_hood', 'sight', 'anodized', 'Facettierter Fensterrahmen', 'frame', 0.8,
        f0=-28, f1=-12, cu=u+15, ow=42, oh=31, iw=33, ih=22, r_out=4, r_in=2)
    section('optic_pane', 'sight', 'glass', 'Getönte Sichtscheibe', -21, -19.5, u+15, 35, 24, 3, 0.3)
    for side, suffix in ((1, 'l'), (-1, 'r')):
        plate('optic_cheek_' + suffix, 'sight', 'dark_metal', 'Visierwange',
              [(-32,u+3),(-27,u+21),(-17,u+21),(2,u+6),(8,u+3)], 3, 0.8, x=side*19.8)
    plate('handle', 'grip_controls', 'graphite', 'Hinterer Griff',
          [(-19, 74), (18, 68), (4, 41), (-7, 14), (-12, -19), (-4, -23), (-8, -31), (-43, -30),
           (-48, -22), (-38, 17), (-35, 39)], 38, 3)
    plate('loop', 'grip_controls', 'dark_metal', 'Offener Griffbügel',
          [(-15, 8), (21, 9), (49, 31), (59, 55), (52, 60), (44, 38), (18, 17), (-12, 17)], 18, 1.8)
    plate('trigger_switch', 'grip_controls', 'graphite', 'Abzugskontur',
          [(6, 54), (16, 55), (18, 40), (28, 30), (24, 28), (12, 35)], 12, 1.5)
    for side, suffix in ((1, 'l'), (-1, 'r')):
        def skin(key, group, role, label, pts, base, thickness=2, bevel=0.7):
            plate(key+'_'+suffix, group, role, label, pts, thickness, bevel, side*(base+thickness/2-0.25))

        skin('grip_cheek', 'grip_controls', 'rubber', 'Weiche Griffwange',
             [(-27, 39), (-15, 44), (-13, 31), (-23, -13), (-34, -18), (-38, -15)], 19, 2.6, 1)
        for i in range(3):
            f, u=-32+i*2, -4+i*10
            skin(f'grip_rib_{i}', 'grip_controls', 'graphite', 'Griffrille',
                 [(f, u), (f+8, u+3), (f+9, u+5), (f+1, u+2)], 21.2, 1, 0.35)
    return parts
