"""R01 BASIC – Montage der fünf editierbaren Baugruppen, neutraler Entwurf.

Vorgabe aus massfigur-v2: Höhe1924mm. Alte Entwurfswerte Schultern520/1560,
Hals1665, Taille1160, Hüfte1020, Beine420/420 sind KEINE aktuellen Messwerte;
sie wurden durch die vier Orthos gemäß docs/herkunft-roboter.md ersetzt.
Front bestimmt Gelenkhöhen, Standbreite und Fußhöhe; Seiten Tiefe/Profil,
Rücken das Rückenmodul. B liefert nur Schalenprinzipien.
Explosionsversätze sind Annahmen zur Darstellung, keine Konstruktionsmaße.
"""
from copy import deepcopy
from formgen.models.figures.r01_parts import legs, lower_body, upper_body, head, arms

INFO = dict(id='R01', kind='figure', name_de='BASIC Roboter', variant='Ortho-Entwurf',
            status='draft_not_accepted',
            provenance=dict(kind='Vorgabe', source='Höhe1924mm aus massfigur-v2; neue vier Orthos und Frontpriorität gemäß docs/herkunft-roboter.md'),
            sources={name: module.PROVENANCE for name, module in
                     [('legs',legs),('lower_body',lower_body),('upper_body',upper_body),('head',head),('arms',arms)]})
ASSEMBLIES = [dict(id=name,de=label,explode=offset,
                  provenance=dict(kind='Annahme',source='Explosionsversatz zur getrennten Darstellung, mm(f,u,x)'))
              for name,label,offset in [('legs','Beine',[0,-120,0]),
                                       ('lower_body','Unterkörper',[0,0,0]),
                                       ('upper_body','Oberkörper',[0,160,0]),
                                       ('head','Kopf',[0,320,0]),
                                       ('arms','Arme',[280,160,0])]]
PARTS = []
ANCHORS = {}
for module in (legs,lower_body,upper_body,head,arms):
    PARTS.extend(deepcopy(module.PARTS))
    for name, anchor in module.ANCHORS.items():
        if name in ANCHORS:
            if anchor['at'] != ANCHORS[name]['at']:
                raise ValueError('Baugruppenanschluss widerspricht sich: '+name)
            # Keep the parent's bearing; retain the child's mating datum too.
            ANCHORS[name+'_Child'] = deepcopy(anchor)
        else:
            ANCHORS[name] = deepcopy(anchor)
ANCHORS['Socket_Ground'] = dict(at=[0,0,0],part=legs.PARTS[0]['id'],
                              source='Vorgabe: gemeinsamer Boden u=0 aus Frontsohlen')
from formgen.models.figures import r01_poses
ANCHORS['Socket_Hand_R'] = r01_poses.hand_socket()
ANCHORS['Socket_Hand'] = deepcopy(ANCHORS['Socket_Hand_R'])
POSES = r01_poses.build_poses(PARTS,ANCHORS)
