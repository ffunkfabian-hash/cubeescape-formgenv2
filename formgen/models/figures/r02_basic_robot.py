"""R02 Frost – Montage der fünf Baugruppen nach dem weiß/blauen Blatt.

Vorgabe Höhe 2000 mm (Nutzerentscheidung 27.10.2026). Front verbindlich für
Höhen/Breiten, Profile für Tiefe, Rücken für das Rückenmodul; Herkunft und
Restabweichungen in docs/herkunft-r02.md, Vertrag docs/robot-contract-r02.md.
Explosionsversätze sind Annahmen zur Darstellung, keine Konstruktionsmaße.
"""
from copy import deepcopy
from formgen.models.figures.r02_parts import legs, lower_body, upper_body, head, arms

INFO = dict(id='R02', kind='figure', name_de='Frost Roboter', variant='Blatt weiß/blau',
            status='draft_not_accepted', line_style='ink',
            provenance=dict(kind='Vorgabe', source='Höhe 2000mm Nutzervorgabe; weiß/blaues Sechs-Ansichten-Blatt, Frontpriorität gemäß docs/herkunft-r02.md'),
            sources={name: module.PROVENANCE for name, module in
                     [('legs', legs), ('lower_body', lower_body), ('upper_body', upper_body), ('head', head), ('arms', arms)]})
ASSEMBLIES = [dict(id=name, de=label, explode=offset,
                   provenance=dict(kind='Annahme', source='Explosionsversatz zur getrennten Darstellung, mm(f,u,x)'))
              for name, label, offset in [('legs', 'Beine', [0, -120, 0]),
                                          ('lower_body', 'Unterkörper', [0, 0, 0]),
                                          ('upper_body', 'Oberkörper', [0, 160, 0]),
                                          ('head', 'Kopf', [0, 320, 0]),
                                          ('arms', 'Arme', [280, 160, 0])]]
PARTS = []
ANCHORS = {}
for module in (legs, lower_body, upper_body, head, arms):
    PARTS.extend(deepcopy(module.PARTS))
    for name, anchor in module.ANCHORS.items():
        if name in ANCHORS:
            if anchor['at'] != ANCHORS[name]['at']:
                raise ValueError('Baugruppenanschluss widerspricht sich: '+name)
            # Keep the parent's bearing; retain the child's mating datum too.
            ANCHORS[name+'_Child'] = deepcopy(anchor)
        else:
            ANCHORS[name] = deepcopy(anchor)
ANCHORS['Socket_Ground'] = dict(at=[0, 0, 0], part=legs.PARTS[0]['id'],
                                source='Vorgabe: gemeinsamer Boden u=0 aus Frontsohlen')
