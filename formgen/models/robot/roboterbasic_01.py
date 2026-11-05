"""RoboterBasic-01: Basic-Typ 1 der Roboter (Blatt RA01), Grundform wie BA01 bei den Waffen.

Autorenmaße in mm. Herkunft: die Zahlen in REFERENCE_PARAMS sind Vorgabe aus BALLON Commit 14bd78d, Studie a_waechter (einmalig übertragen,
BALLON bleibt Lesereferenz); der Nutzer hat diesen Körper mit Helm H 80 als Ziel gesetzt. Der Helm liegt als Flächendaten in
helmet_h80.json vor (gemessen aus RoboterBasic-01.glb der Sicherung vom 05.11.2026): dafür gibt es keine Kit-Quelle. PARAMS ändert davon nur die Haltung (A-Position, Annahme).
Linien setzen nur Einträge von PARAMS (data/robots.toml, formgen/robot/lines.py), nie Teile von Hand. Schnittstelle eines Typs: docs/robot.md.
"""
from __future__ import annotations

import copy
import json
import math
import re
from pathlib import Path

import numpy as np

from formgen.models.robot import arm, body, kit, rig

SOURCE = 'BALLON 14bd78d basic/robot/studies/a_waechter.py, Nutzerziel RoboterBasic-01 (05.11.2026)'
HELMET = Path(__file__).with_name('helmet_h80.json')
DATA_FILES = (HELMET,)      # Schnittstelle Basic-Typ: Datendateien des Modells, gehen in den Cache-Schlüssel

REFERENCE_PARAMS = dict(
    skeleton=dict(waist=(0, 0, 1010), neck=(22, -18, 1405), pelvis=(22, 0, 834), head_h=270, head_off=(-14, 6),
                  torso_hint=(0.2, -1, 0), head_hint=(0.42, -1, 0), shoulder=(276, 0, 300),
                  hip_x=120, hip_z=40, thigh=395, shin=385, foot_h=112,
                  ankles={'R': (-170, -70), 'L': (150, 12)}, toes={'R': (-236, -224), 'L': (190, -150)},
                  knee_pole={'R': (-0.3, -1, 0), 'L': (0.1, -1, 0)}),
    arm_bulk=1.30,                     # Querschnitt Ober-/Unterarm zusätzlich zu arm.ARM_BULK
    arm_drop=('upper_body', 'upper_shell'),
    upper_arm=dict(rows=[(10, 62, 60, 0), (150, 70, 68, 2), (290, 56, 54, 0)], ball=60, shell=(-110, 110), ch=20),
    pose=dict(upper=(-0.24, 0.04, -1.0), fore=(-0.05, -0.32, -1.0), fingers='relaxed', shoulder_open=0, origin='Vorgabe'),
    head=dict(neck=48),
    torso=dict(
        core=[(30, 112, 88, -2), (120, 150, 106, 0), (230, 192, 122, -4), (280, 204, 118, -6), (330, 176, 106, -8), (380, 120, 88, -10)],
        core_ch=44, waist=(86, 68), abdomen='plates', waist_pistons=True, lights=True, gorget=(372, 140, 108, 12), bridges=(176, 352, 190, 14),
        collar=[(360, 132, 98, -10), (410, 104, 86, -8), (428, 92, 80, -8)],
        chest=dict(a=(-74, 74), full=170, tip=118, mid=(240, 300), top=352, t=12, plate=226, stripe=280, emblem=True, vents=(306, 318, 330)),
        back=dict(kind='pack', z=(150, 220, 350), y=-150, nozzle_x=66,
                  rows=[(150, 112, 52, 0), (200, 132, 62, -6), (300, 136, 64, -8), (360, 110, 50, -4)]),
        SX=276, SZ=300, joint_r=58,
        pauldron=dict(rows=[(250, 104, 124, -6, 40), (290, 120, 134, -6, 30), (340, 118, 130, -6, 12), (375, 98, 112, -6, -4),
                            (392, 60, 76, -6, -14)],
                      flare=[(180, 116, 132, -6, 50), (256, 100, 116, -6, 40)], flare2=[(120, 104, 120, -6, 56), (196, 92, 108, -6, 48)],
                      flare_span=112, band=260, med=(272, 26), stripes=True, tilt=16, ch=34, grooves=(312, 326, 340))),
    pelvis=dict(
        pel=[(-30, 140, 94, -2), (50, 154, 100, -2), (130, 124, 86, -2), (190, 100, 76, -2)], belt=(118, 146, 128, 90),
        front=dict(full=20, tip=-90, a=30), side=dict(rows=[(-110, 236, 118, -4), (-20, 200, 108, -4), (110, 168, 100, -4)], span=32, layer=True, center=80),
        hip_x=120, hip_z=40, hip_r=50, butt=True, belt_boxes=True, pel_ch=34),
    legs=dict(
        LT=395, LS=385, foot_h=112, thigh_ch=26, shin_ch=24, knee_ch=20,
        thigh=[(-12, 76, 82, 0), (110, 94, 100, 2), (280, 84, 88, 0), (395, 66, 70, 0)], thigh_shell=(-112, 34), thigh_seams=(200,),
        knee_r=56, kneecap=[(-64, 54, 60), (-20, 64, 70), (36, 66, 72), (80, 60, 66)],
        shin=[(30, 72, 76, 0), (140, 82, 88, -4), (280, 68, 72, -2), (385, 58, 60, 0)], shin_shell=(-96, 96),
        calf=True, ankle_pistons=True, lights=True, ankle_r=40,
        foot=[(-100, 64, 44, -66), (-30, 70, 56, -56), (70, 72, 48, -64), (160, 66, 34, -78), (222, 54, 22, -88)]),
)

# Zwei Ebenen nach Nutzerentscheid 05.11.2026: zehn Einzelteile (Feld `assembly`) und darüber vier Baugruppen (Feld `group`); je Einzelteil beide
# Körperseiten, das Becken gehört zur Baugruppe Oberkörper. Explosion nur zur Darstellung.
GROUPS = dict(head='Kopf', upper_body='Oberkörper', arms='Arme', legs='Beine')
# Grundhaltung A-Position (Nutzerentscheid 05.11.2026). Herkunft Annahme, alle übrigen Zahlen wie REFERENCE_PARAMS: Rumpf, Becken und Kopf gerade
# (Versätze 0), Füße parallel mit ±165 mm Knöchelabstand und 30 mm Auswärtsstellung, Knie nach vorn, Arme A_ANGLE vom Körper, Unterarm A_ELBOW Grad
# näher am Körper und A_FORE_Y leicht nach vorn. REFERENCE_PARAMS ist die Haltung des Referenz-GLB (Kontrapost) und die der Silhouettenabnahme.
A_ANGLE, A_ELBOW, A_FORE_Y = 40, 4, -0.08
_HANG = math.degrees(math.atan(REFERENCE_PARAMS['pose']['upper'][0] / REFERENCE_PARAMS['pose']['upper'][2]))   # Oberarmwinkel der Referenz, Mittel beider Seiten im Rumpfrahmen; die Schulterteile öffnen nur um die Differenz
PARAMS = dict(REFERENCE_PARAMS,
              skeleton=dict(REFERENCE_PARAMS['skeleton'], neck=(0, -18, 1405), pelvis=(0, 0, 834), head_off=(0, 6), torso_hint=(0, -1, 0), head_hint=(0, -1, 0),
                            ankles={'R': (-165, 0), 'L': (165, 0)}, toes={'R': (-195, -165), 'L': (195, -165)},
                            knee_pole={'R': (0, -1, 0), 'L': (0, -1, 0)}),
              pose=dict(upper=(-math.sin(math.radians(A_ANGLE)), 0.0, -math.cos(math.radians(A_ANGLE))),
                        fore=(-math.sin(math.radians(A_ANGLE - A_ELBOW)), A_FORE_Y, -math.cos(math.radians(A_ANGLE - A_ELBOW))), fingers='relaxed',
                        shoulder_open=A_ANGLE - _HANG, origin='Annahme'))

ASSEMBLIES = [
    dict(id='head', de='Kopf', group='head', explode=[0, 300, 0]),
    dict(id='upper_body', de='Oberkörper', group='upper_body', explode=[0, 0, 0]),
    dict(id='pelvis', de='Becken', group='upper_body', explode=[0, -90, 0]),
    dict(id='shoulders', de='Schulter', group='arms', explode=[0, 140, 0]),
    dict(id='upper_arms', de='Oberarm', group='arms', explode=[200, 60, 0]),
    dict(id='forearms', de='Unterarm', group='arms', explode=[330, 0, 0]),
    dict(id='hands', de='Hände', group='arms', explode=[460, -60, 0]),
    dict(id='thighs', de='Oberschenkel', group='legs', explode=[0, -200, 0]),
    dict(id='shins', de='Unterschenkel', group='legs', explode=[0, -380, 0]),
    dict(id='feet', de='Füße', group='legs', explode=[0, -560, 0]),
]
for _a in ASSEMBLIES:
    _a['group_de'] = GROUPS[_a['group']]
    _a['provenance'] = dict(kind='Annahme', source='Explosionsversatz nur zur Darstellung, mm (f,u,x)')

_TRUNK = dict(head='head', torso='upper_body', pelvis='pelvis', thigh='thighs', shin='shins', foot='feet')
_ARM = dict(upper='upper_arms', fore='forearms')


def _assembly(pid, kind):
    """Einzelteil eines Bauteils; zur Schulter gehören die Teile von Segment SHOULDER_* der Referenz (21 je Seite), beschrieben im Rumpf- bzw. Oberarmrahmen."""
    if pid.startswith(('pauldron_', 'shoulder_')):
        return 'shoulders'
    if kind == 'hand' or re.fullmatch(r'(f\d|t)_\d', kind):
        return 'hands'
    found = _TRUNK.get(kind) or _ARM.get(kind)
    if not found:
        raise ValueError(f'{pid}: Segment {kind} gehört zu keinem Einzelteil')
    return found


def _helmet(frames):
    """Helmteile im Kopfrahmen → Weltmaße. Der Kopfrahmen folgt dem Skelett, darum bleiben Linien mit anderen Proportionen möglich."""
    R, o, _, _ = frames['head']
    data = json.loads(HELMET.read_text())
    scale = 1 / data['units_per_mm']
    out = []
    for p in data['parts']:
        points = np.array(p['vertices'], float) * scale
        out.append(dict(id=p['id'], assembly='head', role=p['role'], label=p['label'], bevel=0, smooth=True, segment='head', side='C',
                        form='surface', shape='surface', vertices=kit.to_fux(R, o, points), faces=p['faces'],
                        provenance=dict(kind='gemessen', source=data['source'])))
    return out


def rig_of(params):
    sk = body.skeleton(params['skeleton'])
    frames = rig.body_segments(sk)
    frames.update(rig.arm_segments(sk, arm, params['pose']))
    return sk, frames


def _shoulder_frame(side, torso, joint_local, degrees):
    """Schulterteile sind im Rumpfrahmen beschrieben. Beim Öffnen der Arme drehen sie um das Schultergelenk, je Seite gespiegelt um die Rumpf-Vorderachse."""
    R, o = torso
    if not degrees:
        return R, o
    turn = rig.rot_axis('y', -degrees if side == 'R' else degrees)
    joint = np.array(joint_local, float) * ((1, 1, 1) if side == 'R' else (-1, 1, 1))
    return R @ turn, o + R @ (joint - turn @ joint)


def parts(params=PARAMS):
    sk, frames = rig_of(params)
    head = body.head(params['head'])
    trunk = body.torso(params['torso']) + body.pelvis(params['pelvis']) + body.legs(params['legs'])
    limbs = arm._bulk([p for p in arm.parts() if p[0] not in set(params['arm_drop'])], params['arm_bulk']) + body.upper_arm(params['upper_arm'])
    out = []
    for name, (R, o, side, kind) in frames.items():
        if name.startswith('arm_'):
            continue
        sx = -1 if side == 'L' else 1
        for pid, de, seg, form, role, p in head + trunk:
            if seg == kind:
                frame_ = (R, o)
                if _assembly(pid, kind) == 'shoulders':
                    frame_ = _shoulder_frame('L' if re.match(r'(pauldron|shoulder)_l', pid) else 'R', (R, o), sk['SHOULDER_LOCAL'], params['pose']['shoulder_open'])
                out.append(kit.part(f'{name}_{pid}' if side != 'C' else pid, de, name, form, role, p, frame_, sx, _assembly(pid, kind), side))
    for side, sx in (('R', 1), ('L', -1)):
        for pid, de, seg, form, role, p in limbs:
            R, o, _, _ = frames[f'arm_{side}_{seg}']
            out.append(kit.part(f'arm_{side}_{pid}', de, f'arm_{side}_{seg}', form, role, p, (R, o), sx, _assembly(pid, seg), side))
    return out + _helmet(frames)


def anchors(params=PARAMS):
    sk, frames = rig_of(params)
    src = 'Skelett aus PARAMS.skeleton (' + SOURCE + ')'

    def a(point, part):
        (f, u, x), = kit.to_fux(np.eye(3), np.zeros(3), [point])
        return dict(at=[f, u, x], part=part, source=src)
    sh = rig.shoulders(sk)
    out = {'Socket_Neck': a(sk['NECK'], 'neck'), 'Socket_Waist': a(sk['WAIST'], 'waist_core')}
    for side in 'RL':
        hip, knee, ankle, _ = sk['JOINTS'][side]
        out[f'Socket_Hip_{side}'] = a(hip, f'thigh_{side}_hip_ball')
        out[f'Socket_Knee_{side}'] = a(knee, f'thigh_{side}_thigh_core')
        out[f'Socket_Ankle_{side}'] = a(ankle, f'foot_{side}_foot_core')
        out[f'Socket_Shoulder_{side}'] = a(sh[side], f'arm_{side}_upper_core')
        out[f'Socket_Elbow_{side}'] = a(frames[f'arm_{side}_fore'][1], f'arm_{side}_elbow')
        out[f'Socket_Wrist_{side}'] = a(frames[f'arm_{side}_hand'][1], f'arm_{side}_palm')
    out['Socket_Hand'] = dict(out['Socket_Wrist_R'])     # Waffenanbindung offen; sheet_figure erwartet diesen Namen
    return out


def document(params=PARAMS, *, sheet_id='RA01', line='basic', name='RoboterBasic-01'):
    """Kit-Dokument einer Linie; params ist vollständig (Basis + Register)."""
    return dict(info=dict(id=sheet_id, kind='figure', name_de=name, line=line, status='draft',
                          provenance=dict(kind='Vorgabe', source=SOURCE),
                          stance=dict(kind=params['pose']['origin'],
                                      source='Referenzhaltung aus ' + SOURCE if params['pose']['origin'] == 'Vorgabe' else 'A-Position, Nutzerentscheid 05.11.2026; Winkel und Standbreite Annahme')),
                parts=parts(params), assemblies=copy.deepcopy(ASSEMBLIES), anchors=anchors(params),
                poses={'idle': dict(part_transforms={}, note='Grundhaltung des Modells: A-Position aus PARAMS')})


_doc = document()
INFO, PARTS, ANCHORS, POSES = _doc['info'], _doc['parts'], _doc['anchors'], _doc['poses']
