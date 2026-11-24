"""Gemeinsames Formgen-Vokabular für die sichtbaren Außenflächen der beiden Seitenwaffen."""


class Shell:
    def __init__(self, name):
        self.name = name
        self.parts = []

    def add(self, key, group, role, label, shape, bevel, **geometry):
        self.parts.append(dict(id=key, asm=group, mat=role, de=label, en=key.replace('_', ' '),
                               func=label, attach='Außenmodell ' + self.name, shape=shape,
                               bevel=bevel, segs_bevel=3, **geometry))

    def plate(self, key, group, role, label, points, width, bevel=1.5, **geometry):
        self.add(key, group, role, label, 'prof', bevel, pts=points, w=width, **geometry)

    def inlay(self, key, group, role, label, points, inner, outer, bevel=.45):
        for side, suffix in ((1, 'l'), (-1, 'r')):
            self.plate(f'{key}_{suffix}', group, role, label, points, outer-inner,
                       bevel, x=side*(inner+outer)/2)

    def facet(self, key, group, role, label, start, end, level, width, height, corner, bevel=1):
        a, b = width/2, height/2
        rim = [(-a+corner,-b), (a-corner,-b), (a,-b+corner), (a,b-corner),
               (a-corner,b), (-a+corner,b), (-a,b-corner), (-a,-b+corner)]
        self.add(key, group, role, label, 'xprof', bevel, f0=start, f1=end, cu=level, pts=rim)

    def word(self, group, role, f, u, x, size):
        for side, suffix in ((1,'l'),(-1,'r')):
            self.add('word_'+suffix, group, role, 'Modellschriftzug', 'text', 0,
                     text=self.name.upper(), f=f, u=u, x=side*x, side=side,
                     depth=.22, size=size, align='CENTER')

    def finish(self, anchors, points):
        return (self.parts,
                {k:dict(part=p, at=list(at), source='Annahme: Bezugspunkt des Spielmodells') for k,(p,at) in anchors.items()},
                {k:dict(part=p, at=list(at)) for k,(p,at) in points.items()})
