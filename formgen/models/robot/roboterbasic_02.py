"""RoboterBasic-02, gemessen aus robot_v2.blend; keine Laufzeitbindung an Blender.

Grundgeometrie und Pivots sind gemessen, SHA256 siehe SOURCE. Gelenkgrenzen,
Darstellung, Profilzuordnung und Schulterversatz sind deklarierte Annahmen;
Arm-Freiraeume folgen Vorgabe01 mit angenommenem Spiel. Nutzer bestaetigt
am 05.11.2026 eigene Herkunft aller Vorlagen (nano image banana).
Die Datendatei enthaelt einzelne Kit-Formen, keine Gesamtfigur als Mesh.
"""
from __future__ import annotations

from copy import deepcopy
import json
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from formgen.models.robot import arm, body, rig
from formgen.models.robot import roboterbasic_02_parameters as profiles

SOURCE = 'robot_v2.blend SHA256 67a350c19aec60241c86d0b2b0937469960d06c52422275844dcb8a24400d578; headless Weltgeometrie, Frame 1, Blender 5.2.2'
HEIGHT = 1848.919751
SHOULDER_INSET = 20.0  # Annahme zur direkten Nutzerkorrektur: jede Schulter 20mm nach innen.
SHOULDER_WIDTH = 600.000084 - 2*SHOULDER_INSET
ARM_LENGTH = 556.210017335
LEG_LENGTH = 907.782963632
HEAD_SIZE = 236.918
NECK_LENGTH = 70.0  # Annahme: Halslaenge fuer body.py, am Bild gewaehlt; 01 nutzt 48
SHAPES_FILE = Path(__file__).with_name('roboterbasic_02_shapes.json')
SHAPES_FILE_2 = Path(__file__).with_name('roboterbasic_02_shapes_2.json')    # zweite Hälfte der Teile: je Datei unter der Grenze von 5 MB
DATA_FILES = (SHAPES_FILE, SHAPES_FILE_2)
_DATA = json.loads(SHAPES_FILE.read_text())
_DATA['parts'] += json.loads(SHAPES_FILE_2.read_text())['parts']
_BONES = _DATA['bones']


def _point(name, end='head'):
    return np.array(_BONES[name][end], float)


def _length(name):
    return float(np.linalg.norm(_point(name, 'tail') - _point(name)))


_UPPER, _FORE = _length('upperarm_R'), _length('forearm_R')
_THIGH, _SHIN = _length('thigh_R'), _length('shin_R')
_MEASURED_HEIGHT=HEIGHT
_MEASURED_ARM_LENGTH=_UPPER+_FORE
_MEASURED_LEG_LENGTH=_THIGH+_SHIN
_MEASURED_HEAD_SIZE=HEAD_SIZE
_WAIST, _NECK, _PELVIS = (_point(n) for n in ('spine', 'neck', 'hips'))
_TORSO_BASIS=rig.frame(_WAIST,_NECK,(0,-1,0))
_SHOULDER_LOCAL=_TORSO_BASIS.T@(_point('upperarm_L')-_WAIST)
_HIP_CENTER=(_point('thigh_R')+_point('thigh_L'))/2
_HIP_Z=float(_HIP_CENTER[2]-_PELVIS[2])
_HIP_TO_WAIST=(_WAIST-_HIP_CENTER)/np.linalg.norm(_WAIST-_HIP_CENTER)
# Inverse der gemeinsamen 01-Skelettdefinition: die Steuerpunkte reproduzieren
# die gemessenen Gelenke; sie sind nicht blind kopierte Blender-Bone-Urspruenge.
_PELVIS_CONTROL=_HIP_CENTER-_HIP_TO_WAIST*_HIP_Z

REFERENCE_PARAMS = dict(
    dimensions=dict(height=HEIGHT, shoulder_width=SHOULDER_WIDTH, arm_length=ARM_LENGTH,
                    leg_length=LEG_LENGTH, head_size=HEAD_SIZE),
    skeleton=dict(waist=_WAIST.tolist(), neck=_NECK.tolist(), pelvis=_PELVIS_CONTROL.tolist(),
        head_h=HEIGHT-_NECK[2], head_off=[0, 0], torso_hint=[0, -1, 0], head_hint=[0, -1, 0],
        shoulder=[SHOULDER_WIDTH/2,float(_SHOULDER_LOCAL[1]),float(_SHOULDER_LOCAL[2])],
        hip_x=abs(_point('thigh_R')[0]),hip_z=_HIP_Z, thigh=_THIGH, shin=_SHIN,
        foot_h=float(_point('foot_R')[2]),
        ankles={s:_point('foot_'+s)[:2].tolist() for s in 'RL'},
        toes={s:_point('foot_'+s, 'tail')[:2].tolist() for s in 'RL'},
        knee_pole={s:(_point('shin_'+s)-(_point('thigh_'+s)+_point('foot_'+s))/2).tolist() for s in 'RL'}),
    arm_bulk=1.0,
    pose=dict(upper=((_point('upperarm_L','tail')-_point('upperarm_L'))*[-1,1,1]).tolist(),
              fore=((_point('forearm_L','tail')-_point('forearm_L'))*[-1,1,1]).tolist(),
              fingers='relaxed', shoulder_open=0, origin='gemessen'),
    head=dict(neck=NECK_LENGTH),
)
REFERENCE_PARAMS.update(profiles.extras())
# Vorgabe01 cf294c4: gemeinsame A-Position; die Winkel sind Entwurfsannahmen,
# keine Messung der Blend-Datei. Die gemessene Haltung bleibt separat erhalten.
A_ANGLE, A_ELBOW, A_FORE_Y = 40, 4, -0.08
_HANG = math.degrees(math.atan(REFERENCE_PARAMS['pose']['upper'][0] / REFERENCE_PARAMS['pose']['upper'][2]))
PARAMS = deepcopy(REFERENCE_PARAMS)
PARAMS['skeleton'].update(
    neck=[_WAIST[0], _WAIST[1], _NECK[2]],
    pelvis=[_WAIST[0], _WAIST[1], _PELVIS_CONTROL[2]],
    knee_pole={s:[0, -1, 0] for s in 'RL'})
PARAMS['pose'] = dict(
    upper=(-math.sin(math.radians(A_ANGLE)), 0.0, -math.cos(math.radians(A_ANGLE))),
    fore=(-math.sin(math.radians(A_ANGLE-A_ELBOW)), A_FORE_Y, -math.cos(math.radians(A_ANGLE-A_ELBOW))),
    fingers='relaxed', shoulder_open=A_ANGLE-_HANG, origin='Annahme')
GROUPS = dict(head='Kopf', upper_body='Oberkörper', arms='Arme', legs='Beine')
ASSEMBLIES = [dict(id=n, de=de, group=group, group_de=GROUPS[group], explode=e,
    provenance=dict(kind='Vorgabe',source='RoboterBasic-01 cf294c4, zwei Ebenen; Explosionsversatz Annahme, mm f/u/x'))
    for n,de,group,e in [
        ('head','Kopf','head',[0,300,0]),
        ('upper_body','Oberkörper','upper_body',[0,0,0]),
        ('pelvis','Becken','upper_body',[0,-90,0]),
        ('shoulders','Schulter','arms',[0,140,0]),
        ('upper_arms','Oberarm','arms',[200,60,0]),
        ('forearms','Unterarm','arms',[330,0,0]),
        ('hands','Hände','arms',[460,-60,0]),
        ('thighs','Oberschenkel','legs',[0,-200,0]),
        ('shins','Unterschenkel','legs',[0,-380,0]),
        ('feet','Füße','legs',[0,-560,0])]]


# Vorgabe01 cf294c4, anatomische Zuordnung der gemessenen Quellsegmente.
ASSEMBLY_BINDINGS = (
    ('head','head'), ('neck','head'), ('shoulder_','shoulders'),
    ('pauldron_','shoulders'), ('upperarm_','upper_arms'),
    ('forearm_','forearms'), ('hand_','hands'), ('finger','hands'),
    ('thumb','hands'), ('thigh_','thighs'), ('shin_','shins'),
    ('kneecap_','shins'), ('foot_','feet'), ('hips','pelvis'),
    ('spine','pelvis'), ('chest','upper_body'))


def _assembly(row):
    """Source bone → current 01 single-part assembly; source IDs stay stable."""
    for prefix,assembly in ASSEMBLY_BINDINGS:
        if row['bone'].startswith(prefix):return assembly
    raise ValueError('Quellsegment ohne Einzelteil-Zuordnung: '+row['bone'])


def _frames(params):
    skeleton=deepcopy(params['skeleton'])
    leg_ratio=params['dimensions']['leg_length']/_MEASURED_LEG_LENGTH
    rise=params['dimensions']['leg_length']-_MEASURED_LEG_LENGTH
    for key in ('waist','neck','pelvis'):
        skeleton[key]=list(skeleton[key]);skeleton[key][2]+=rise
    skeleton['thigh']*=leg_ratio
    skeleton['shin']*=leg_ratio
    skeleton['shoulder']=list(skeleton['shoulder'])
    skeleton['shoulder'][0]*=params['dimensions']['shoulder_width']/SHOULDER_WIDTH
    for key in ('ankles','toes'):
        skeleton[key]={s:tuple(v) for s,v in skeleton[key].items()}
    sk=body.skeleton(skeleton)
    frames=rig.body_segments(sk)
    lengths=SimpleNamespace(**{k:getattr(arm,k) for k in dir(arm) if not k.startswith('__')})
    arm_ratio=params['dimensions']['arm_length']/_MEASURED_ARM_LENGTH
    lengths.UPPER_MM, lengths.FORE_MM = _UPPER*arm_ratio, _FORE*arm_ratio
    frames.update(rig.arm_segments(sk,lengths,params['pose']))
    return frames


_SOURCE_PARAMS=deepcopy(REFERENCE_PARAMS)
_SOURCE_PARAMS['skeleton']['shoulder'][0]=abs(float(_SHOULDER_LOCAL[0]))
_SOURCE_PARAMS['dimensions'].update(height=_MEASURED_HEIGHT,arm_length=_MEASURED_ARM_LENGTH,
                                    leg_length=_MEASURED_LEG_LENGTH,head_size=_MEASURED_HEAD_SIZE)
_BASE_FRAMES = _frames(_SOURCE_PARAMS)


def _segment(bone):
    if bone in ('head','neck'):return 'head'
    if bone=='chest' or bone.startswith(('shoulder','pauldron')):return 'torso'
    if bone in ('hips','spine'):return 'pelvis'
    for source,dest in [('upperarm','upper'),('forearm','fore'),('hand','hand')]:
        if bone.startswith(source+'_'):return 'arm_'+bone[-1]+'_'+dest
    if bone.startswith(('thigh','shin','foot')):return bone
    if bone.startswith('kneecap_'):return 'shin_'+bone[-1]
    for source,dest in [('fingertip',2),('fingermid',1),('finger',0)]:
        if bone.startswith(source):return f'arm_{bone[-1]}_f{int(bone[len(source)])-1}_{dest}'
    for source,dest in [('thumbtip',2),('thumbmid',1),('thumb',0)]:
        if bone.startswith(source+'_'):return f'arm_{bone[-1]}_t_{dest}'
    raise ValueError('Unbekanntes Segment: '+bone)


def _xyz(points):
    p=np.asarray(points,float)
    return p[..., [2,0,1]]*[1,-1,1]


def _fux(points):
    p=np.asarray(points,float)
    return np.round(p[..., [1,2,0]]*[-1,1,1],6).tolist()


def _map_shape(shape, transform):
    out=deepcopy(shape)
    for key in ('points','vertices','rings'):
        if key in out:out[key]=_fux(transform(_xyz(out[key])))
    for key in ('items','cuts'):
        if key in out:out[key]=[_map_shape(s,transform) for s in out[key]]
    return out


def _templates():
    """Left templates reference the right measurement; true asymmetries remain separate."""
    rows={r['id']:r for r in _DATA['parts']}
    def reflected(source):
        shape=_map_shape(source,lambda v:v*[-1,1,1])
        def reverse_faces(s):
            if 'faces' in s:s['faces']=[list(reversed(f)) for f in s['faces']]
            for key in ('items','cuts'):
                for child in s.get(key,[]):reverse_faces(child)
        reverse_faces(shape)
        return shape
    for raw in _DATA['parts']:
        if 'mirror_of' in raw:
            right=rows[raw['mirror_of']]
            shape=reflected({k:right[k] for k in ('shape','points','vertices','faces','rings','cuts','items') if k in right})
            combined=dict(right,**shape)
            if 'pre_boolean_shape' in right:combined['pre_boolean_shape']=reflected(right['pre_boolean_shape'])
            if 'source_boolean_cuts' in right:
                combined['source_boolean_cuts']=[reflected(c) for c in right['source_boolean_cuts']]
                for cut in combined['source_boolean_cuts']:
                    cut['source_object']=cut['source_object'].replace('_R','_L',1)
            combined.update({k:v for k,v in raw.items() if k!='mirror_of'})
            yield combined
        else:yield deepcopy(raw)


_TEMPLATES = list(_templates())


def _transform(params, row, frames):
    seg=row.get('frame',_segment(row['bone']))
    base_R,base_o,_,_=_BASE_FRAMES[seg]
    new_R,new_o,_,_=frames[seg]
    shoulder_mount=row.get('mount_frame') if row['bone'].startswith(('shoulder_','pauldron_')) else None
    if shoulder_mount:
        # Same shoulder_open convention as 01: rotate the cap around the joint,
        # mirrored per side. Translation uses the corrected inner socket once.
        side=row['bone'][-1]
        base_R=_BASE_FRAMES['torso'][0]
        base_o=_BASE_FRAMES[shoulder_mount][1]
        angle=params['pose']['shoulder_open']*(-1 if side=='R' else 1)
        new_R=frames['torso'][0]@rig.rot_axis('y',angle)
        new_o=frames[shoulder_mount][1]
    dim=params['dimensions']
    arm_length=dim['arm_length']/_MEASURED_ARM_LENGTH
    leg_length=dim['leg_length']/_MEASURED_LEG_LENGTH
    head_size=dim['head_size']/_MEASURED_HEAD_SIZE
    neck=_NECK+frames['head'][1]-_BASE_FRAMES['head'][1]

    def apply(v):
        original_shape=v.shape
        v=v.reshape(-1,3)
        local=(v-base_o)@base_R
        if row.get('length_scale',True):
            if seg.startswith('thigh_'):local[:,2]*=params['skeleton']['thigh']/_THIGH*leg_length
            if seg.startswith('shin_'):local[:,2]*=params['skeleton']['shin']/_SHIN*leg_length
        if seg.endswith('_fore') or row.get('apply_arm_bulk',False):
            local[:,:2]*=params['arm_bulk']
        if seg.endswith(('_upper','_fore')) and row.get('length_scale',True):local[:,2]*=arm_length
        v=local@new_R.T+new_o
        if row.get('mount_frame') and not shoulder_mount:
            mount=row['mount_frame']
            R0,o0,_,_=_BASE_FRAMES['torso']
            Rt,ot,_,_=frames['torso']
            inherited=(_BASE_FRAMES[mount][1]-o0)@R0@Rt.T+ot
            v+=frames[mount][1]-inherited
        if row['bone']=='neck':
            v[:,:2]=neck[:2]+(v[:,:2]-neck[:2])*params['head']['neck']/70.0
        if row['assembly']=='head':v=neck+(v-neck)*head_size
        v[:,2]*=dim['height']/_MEASURED_HEIGHT
        return v.reshape(original_shape)
    return apply


def parts(params=PARAMS):
    frames=_frames(params);out=[]
    for row in profiles.templates(params,PARAMS,_TEMPLATES,_BASE_FRAMES):
        shape={k:row[k] for k in ('shape','points','vertices','faces','rings','cuts','items') if k in row}
        p=_map_shape(shape,_transform(params,row,frames))
        p.update(id=row['id'],assembly=_assembly(row),role=row['role'],label=row['source_object'],
                 source_object=row['source_object'],segment=row['bone'],bevel=0,
                 provenance=deepcopy(row.get('provenance',dict(kind='gemessen',source=SOURCE))))
        if row['assembly']=='arms' or row.get('mount_frame'):
            p['transform_provenance']=dict(kind='Annahme',source=f'Nutzerkorrektur: Schultern naeher zur Brust, Default je{SHOULDER_INSET:g}mm innen; Gelenk-/Armkette folgt dem Kontrollskelett.')
        if 'surface_reason' in row:p['surface_reason']=row['surface_reason']
        if 'parent_part' in row:p['parent_part']=row['parent_part']
        out.append(p)
    ids={p['id'] for p in out}
    parents={p['id']:p.get('parent_part') for p in _TEMPLATES}
    for part in out:
        parent=part.get('parent_part')
        while parent and parent not in ids:parent=parents.get(parent)
        if parent:part['parent_part']=parent
        else:part.pop('parent_part',None)
    return out


def anchors(params=PARAMS):
    frames=_frames(params)
    rows={p['source_object']:p for p in _TEMPLATES}
    choices=[('Neck','Neck','neck'),('Waist','Waist','spine')]
    for side in 'RL':
        choices.extend([(f'Hip_{side}',f'HipJoint_{side}',f'thigh_{side}'),
                        (f'Knee_{side}',f'KneeJoint_{side}',f'shin_{side}'),
                        (f'Ankle_{side}',f'AnkleCore_{side}',f'foot_{side}'),
                        (f'Shoulder_{side}',f'ShoulderJoint_{side}',f'upperarm_{side}'),
                        (f'Elbow_{side}',f'Elbow_{side}',f'forearm_{side}'),
                        (f'Wrist_{side}',f'WristCuff_{side}',f'hand_{side}')])
    result={}
    for name,obj,bone in choices:
        row=rows[obj];point=_transform(params,row,frames)(_point(bone))
        result['Socket_'+name]=dict(at=_fux(point),part=row['id'],source=SOURCE)
    result['Socket_Hand']=deepcopy(result['Socket_Wrist_R'])
    return result


def joints(params=PARAMS):
    """Limits are assumptions, degrees about author axes; no animation claim."""
    out=[]
    for name,anchor in anchors(params).items():
        if name=='Socket_Hand':continue
        limit=((-90,90),(-45,45),(-45,45))
        if 'Knee' in name:limit=((0,0),(0,0),(0,135))
        out.append(dict(socket=name,part=anchor['part'],pivot=anchor['at'],
                        limits_deg=dict(zip(('f','u','x'),limit)),
                        provenance=dict(kind='Annahme',source='Entwurfsgrenzen, nicht aus statischer Quelldatei gemessen')))
    # The remaining anatomical pivots, including every finger segment, stay data.
    covered={'neck','spine'}|{b+'_'+s for b in ('thigh','shin','foot','upperarm','forearm','hand') for s in 'RL'}
    frames=_frames(params)
    for bone in sorted({p['bone'] for p in _TEMPLATES}-covered):
        row=next(p for p in _TEMPLATES if p['bone']==bone)
        pivot=_fux(_transform(params,row,frames)(_point(bone)))
        out.append(dict(bone=bone,part=row['id'],pivot=pivot,
                        limits_deg=dict(f=[-30,30],u=[-30,30],x=[0,100]),
                        provenance=dict(kind='Annahme',source='Pivot gemessen laut SOURCE; Grenzen Entwurf, keine Bewegungsfreigabe')))
    return out


def document(params=PARAMS, *, sheet_id='RoboterBasic-02', line='basic', name='RoboterBasic-02'):
    """No sheet ID allocated; integration supplies sheet_id explicitly."""
    return dict(info=dict(id=sheet_id,kind='figure',name_de=name,line=line,status='draft',
                         provenance=dict(kind='gemessen',source=SOURCE),joints=joints(params),
                         parameter_provenance=profiles.PROVENANCE,
                         stance=dict(kind=params['pose']['origin'],source=(SOURCE+'; Schulterkorrektur je20mm innen'
                             if params['pose']['origin']=='gemessen' else 'Vorgabe01 cf294c4: A-Position; Winkel und Stand Annahme')),
                         user_corrections=dict(shoulder_inset_mm=SHOULDER_INSET,extra_bridges=False),
                         authorship='Nutzerbestaetigung 05.11.2026: alle Quellen selbst mit nano image banana erstellt'),
                parts=parts(params),assemblies=deepcopy(ASSEMBLIES),anchors=anchors(params),
                poses={'idle':dict(part_transforms={},note=('Gemessene Referenzhaltung mit Schulterkorrektur'
                    if params['pose']['origin']=='gemessen' else 'A-Position aus PARAMS')+'; keine Bewegungsabnahme')},
                warnings=profiles.warnings(params,PARAMS))


_doc=document()
INFO,PARTS,ANCHORS,POSES=(_doc[k] for k in ('info','parts','anchors','poses'))
