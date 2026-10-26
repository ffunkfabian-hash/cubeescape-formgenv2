"""R01 Becken und Gürtel, editierbar im Welt-Autorenraum (f,u,x), mm.

Front-/Rückenpixel bestimmen Breite und Höhe; die beiden Seiten bestimmen
Tiefe. Einheitlich k=1924/3653, Seiten nur an der Helmoberkante ausgerichtet.
1924 mm bleibt ein Entwurfsmaß, keine reale Bildkalibrierung. Verdeckte
Flächen, Wandstärken und Lager sind ausdrücklich Konstruktionsannahmen.
"""

PROVENANCE = {
    'kind': 'gemessen',
    'source': 'robot-ortho-front/back/side-right/side-left.png, 4096², 26.10.2026; Pixelmessung mit vorgegebener Entwurfshöhe',
    'height_mm': {'kind': 'Vorgabe', 'value': 1924, 'source': 'massfigur-v2 Entwurf, keine reale Maschinenmessung'},
    'registration': {'mm_per_px': 1924 / 3653, 'front_ground_y_px': 3876,
                     'front_center_x_px': 2048, 'front_top_y_px': 223,
                     'right_top_y_px': 216, 'left_top_y_px': 218,
                     'right_f0_px': 2150, 'left_f0_px': 1946},
    'front_measurements': 'Taillengrenze y1615≈1191mm; zentrale Schale y1620..1827≈1188..1079mm, x1920..2176; schwarzer Leistenkörper bis y2004≈986mm; Flankenschalen x1727..1890 gespiegelt, y1560..1723≈1220..1134mm.',
    'side_measurements': 'side-right vordere Leistenschale x1757..1788, Gürtel x1855..1966; f=(2150-x)*1924/3653. Verdeckte Rücktiefe aus Gegenansicht ergänzt; keine Skalierung auf Seiten-Gesamthöhe.',
    'construction': 'Annahme: 5mm geschlossene Schalen, 2mm mittlere Fuge, 3mm Schichtfuge; gerundete Kontrollpunkte zwischen Pixelstützstellen. Form-B Facetten; massfigur-v2 nur Schalenprinzip, keine Geometrieübernahme.',
    'hidden_geometry': 'Annahme: verdeckter Beckenkern und Lagerträger. Hüftachsen gehören legs; lower_body liefert ihre innere Anbindung. Gemeinsame Anker f45/u1080/x±142; Taille f45/u1190/x0.',
}
PARTS = []
ANCHORS = {}


def _part(name, role, source, **shape):
    ident = 'lower_' + name
    PARTS.append(dict(id=ident, assembly='lower_body', role=role, bevel=0,
                      provenance={'kind': 'Annahme', 'source': source}, **shape))
    return ident


def _core(rows):
    """Eight-sided horizontal sections: u, half-width, front, back."""
    rings = []
    for u, width, front, back in rows:
        depth = front - back
        rings.append([[f, u, x] for f, x in (
            (back, -.72 * width), (back + .17 * depth, -width),
            (front - .18 * depth, -width), (front, -.72 * width),
            (front, .72 * width), (front - .18 * depth, width),
            (back + .17 * depth, width), (back, .72 * width))])
    return dict(shape='loft', rings=rings)


def _panel(outline, rear=False, wall=5):
    """Closed folded plate; inner skin is physically offset along f.

    outline is a convex list (f,u,x), with an explicit fan ridge. Inner and
    outer skins plus all perimeter walls form one watertight volume.
    """
    direction = -1 if rear else 1
    n = len(outline)
    centre = [sum(p[i] for p in outline) / n for i in range(3)]
    centre[0] += direction * 3
    outer = [list(p) for p in outline] + [centre]
    inner = [[f - direction * wall, u, x] for f, u, x in outer]
    offset = n + 1
    faces = [[i, (i + 1) % n, n] for i in range(n)]
    faces += [[offset + i for i in reversed(face)] for face in faces[:]]
    faces += [[(i + 1) % n, i, i + offset, (i + 1) % n + offset]
              for i in range(n)]
    area = sum(a[2] * b[1] - a[1] * b[2]
               for a, b in zip(outline, outline[1:] + outline[:1]))
    if area * direction < 0:
        faces = [list(reversed(face)) for face in faces]
    return dict(shape='surface', vertices=outer + inner, faces=faces, wall_mm=wall)


pelvis = _part('pelvis_core', 'graphite',
    PROVENANCE['front_measurements'] + ' ' + PROVENANCE['hidden_geometry'],
    **_core([(987, 39, 126, -52), (997, 54, 148, -64),
             (1050, 67, 173, -73), (1100, 84, 188, -79),
             (1160, 133, 194, -80), (1190, 119, 176, -67)]))

# Lower torso terminates at this shared datum. The side belt wings rise above
# it alongside the abdomen, as visible in the front image.
ANCHORS['Socket_Waist'] = {
    'at': [45, 1190, 0], 'part': pelvis,
    'source': 'Gemessen: Front Trennkante y1615 bei k1924/3653≈1191; gerundet1190. Annahme f45.'}

for side, sign in (('r', -1), ('l', 1)):
    support = _part('hip_mount_' + side, 'dark_metal', PROVENANCE['hidden_geometry'],
        shape='hull', points=[[f, u, sign * x] for f, u, x in (
            (-4, 1040, 63), (94, 1040, 63), (-8, 1136, 70),
            (110, 1136, 70), (-4, 1040, 103), (94, 1040, 103),
            (-8, 1136, 103), (110, 1136, 103))])
    ANCHORS['Socket_HipMount_' + side.upper()] = {
        'at': [45, 1080, sign * 142], 'part': support,
        'source': 'Gemeinsame Registrierung: Hüftanker45/1080/±142; legs besitzt Gelenkachse, lower_body den inneren Träger.'}
    for rear in (False, True):
        face = 'rear' if rear else 'front'
        # Opposed shells intentionally have different depths, not a mirrored
        # whole pelvis. Front and rear silhouettes share measured widths.
        def depth(front):
            return -80 - (front - 182) * .45 if rear else front

        plate = [(201, 1079, 36), (203, 1085, 43), (212, 1154, 59),
                 (213, 1162, 66), (204, 1187, 60), (204, 1187, 1),
                 (201, 1079, 1)]
        _part('groin_' + face + '_' + side, 'shell',
              PROVENANCE['front_measurements'] + ' ' + PROVENANCE['construction'],
              **_panel([[depth(f), u, sign*x] for f, u, x in plate], rear))
        lip = [(215, 1157, 1), (215, 1157, 61), (211, 1166, 68),
               (206, 1187, 63), (206, 1187, 1)]
        _part('belt_lip_' + face + '_' + side, 'shell',
              'Gemessen: helle Querleiste über Leistenplatte y1620..1680; Annahme getrennte 5mm Auflage mit Form-B Facette.',
              **_panel([[depth(f) + (-3 if rear else 3), u, sign*x] for f, u, x in lip], rear))
        flank = [(166, 1134, 111), (130, 1166, 169),
                 (116, 1177, 174), (129, 1220, 144),
                 (184, 1193, 86)]
        _part('belt_flank_' + face + '_' + side, 'shell',
              PROVENANCE['front_measurements'] + ' ' + PROVENANCE['side_measurements'] + ' ' + PROVENANCE['construction'],
              **_panel([[depth(f), u, sign*x] for f, u, x in flank], rear))
