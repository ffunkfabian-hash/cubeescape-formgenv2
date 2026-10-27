"""R02 Kopf: Hals, Helm, Gesichtsplatte, Visier, Ohrkapseln.

Front gemessen (±85..±115). Profil A und B sind am Kopf um 12 mm gegeneinander
verschoben (A −110..152, B −98..165 bei u1870, gleiche Tiefe 262 mm):
gemittelt, Abweichung ±6 mm in herkunft-r02.md ausgewiesen.
"""
from formgen.models.figures.r02_parts.common import PROVENANCE as COMMON, rows_loft, mirror, disc

PROVENANCE = {
    **COMMON,
    'profile_conflict': {'kind': 'gemessen', 'source': 'Profil A/B Kopf um 12 mm in f versetzt (u1790..1990); Mittelwert verwendet'},
    'visor': {'kind': 'gemessen', 'source': 'Frontfarbbild Visier u≈1838..1885, x±78; Gesichtsplatte dunkel u1745..1838'},
}
PARTS = []
ANCHORS = {}


def _part(name, role, source, shape, sides=False):
    items = [('_l', shape), ('_r', mirror(shape))] if sides else [('', shape)]
    for suffix, s in items:
        PARTS.append(dict(id='head_'+name+suffix, assembly='head', role=role, bevel=0,
                          provenance={'kind': 'gemessen', 'source': source}, **s))


def _sym(rows, cx=.3, cf=.3):
    return rows_loft([(u, -w, w, fb, ff) for u, w, fb, ff in rows], cx, cf)


_part('neck', 'frost_frame', 'Annahme: verdeckter Hals unter Schal, r≈60', _sym([(1740, 62, -70, 60), (1800, 58, -66, 60)]))
HELMET = [(1785, 90, -72, 120), (1800, 102, -71, 128), (1820, 106, -85, 135), (1840, 113, -98, 140),
          (1860, 113, -103, 141), (1890, 113, -104, 141), (1895, 111, -103, 150), (1900, 109, -102, 157),
          (1910, 101, -95, 155), (1920, 100, -93, 152), (1930, 99, -90, 149), (1940, 97, -85, 144),
          (1950, 93, -79, 133), (1960, 88, -72, 125), (1970, 76, -62, 114), (1980, 64, -49, 100),
          (1990, 49, -30, 79), (1998, 25, -12, 50)]
_part('helmet', 'frost_shell', 'Front ±90..115 u1785..1998; Profil gemittelt; unter der Stirnkante u<1895 vorn zurückgesetzt für Gesicht/Visier (Annahme)', _sym(HELMET))
FACE = [(1745, 70, 40, 128), (1770, 86, 40, 143), (1785, 90, 40, 148), (1800, 98, 40, 151),
        (1820, 100, 40, 155), (1838, 104, 40, 157)]
_part('face_plate', 'frost_frame', 'Front Kinn/Gesicht u1745..1838; Profil Kinn vorn 135..157', _sym(FACE, .3, .25))
_part('visor', 'frost_visor', PROVENANCE['visor']['source'],
      _sym([(1838, 100, 60, 157), (1860, 104, 60, 158), (1885, 104, 60, 157), (1895, 98, 60, 150)], .25, .15))
_part('ear', 'frost_shell', 'Front Ohrkapseln ±115 u1840..1890; Profil Ohrscheibe Mitte f≈5', disc('x', (5, 1865), 100, 116, 34, 24), sides=True)

ANCHORS['Socket_Neck'] = dict(at=[0, 1760, 0], part='head_neck', source='gemessen: Schaloberkante u≈1760')
