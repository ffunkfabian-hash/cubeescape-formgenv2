"""Roboter-Pipeline: Register → Modell → Geometrie → GLB → Spec/Prompts → Ansichten → Blatt → Vorschau, unabhängig von BALLON und Blender.

  python -m formgen.robot                 # alle Linien; danach die Website neu bauen: python -m formgen.viewer
  python -m formgen.robot RA01 --force

Jede Stufe ist ein Cacheeintrag (formgen/cache.py); ohne --force nur Fehlendes. Eigenständig, damit Waffenschlüssel unberührt bleiben.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
from pathlib import Path

from .. import build, versions
from ..cache import Artifact, canonical, file_hash, run_artifacts
from . import bevel, glb, lines, spec

ROOT = build.ROOT
ROBOT = 2                 # Stufenstand der Roboter-Pipeline (eigene Konstante: versions.py steht in allen Waffenschlüsseln)
STAGES = ('geometry', 'asset', 'specs', 'prompts', 'views', 'fonts', 'sheets', 'previews')
IMAGE_STAGES = ('prompts', 'views', 'fonts', 'sheets', 'previews')
CODE = ('formgen/robot/pipeline.py', 'formgen/robot/bevel.py', 'formgen/robot/glb.py', 'formgen/robot/spec.py', 'formgen/robot/lines.py')


def source_hash(entry) -> str:
    """Modul und Closure des Typs, seine DATA_FILES und der Registereintrag; ein zweiter Typ lässt die Schlüssel des ersten unberührt."""
    module = lines.module_of(entry)
    hashes = {str(Path(k).relative_to(ROOT)): v for k, v in build.source_hashes(Path(module.__file__)).items()}
    hashes.update({str(Path(f).relative_to(ROOT)): file_hash(Path(f)) for f in module.DATA_FILES})
    for engine in ('formgen/geom.py', 'formgen/model.py'):      # wie der Waffenschlüssel: Auswertung gehört zur Geometrie
        hashes.update({str(Path(k).relative_to(ROOT)): v for k, v in build.source_hashes(ROOT / engine).items()})
    return hashlib.sha256(canonical({'files': hashes, 'entry': entry})).hexdigest()


def document_for(sid, entry):
    module = lines.module_of(entry)
    document = module.document(lines.merge(module.PARAMS, entry['params']), sheet_id=sid, line=entry['line']['name'].lower(), name=entry['type']['name_de'])
    document['info']['skin'] = entry['skin']        # Materialkacheln des Blatts zeigen die Farben des Skins
    return document


def build_geometry(artifact: Artifact) -> bytes:
    document = bevel.evaluate(document_for(artifact.model_id, artifact.inputs['entry']))
    return canonical(lines.check_document(document)) + b'\n'


def build_asset(artifact: Artifact) -> bytes:
    document = json.loads(Path(artifact.inputs['geometry_path']).read_bytes())
    return glb.build(document, artifact.inputs['entry']['skin'])


def build_robot_spec(artifact: Artifact) -> bytes:
    document = json.loads(Path(artifact.inputs['geometry_path']).read_bytes())
    return json.dumps(spec.build(document, artifact.inputs['entry']), indent=1, ensure_ascii=False, sort_keys=True).encode() + b'\n'


def _code() -> str:
    return hashlib.sha256(canonical({c: file_hash(ROOT / c) for c in CODE})).hexdigest()


def _coded(artifacts):
    """Bildstufen und Blatt: build.py nimmt keinen Code in den Schlüssel; wie in formgen.pipeline Closure und Umgebung ergänzen."""
    from .. import pipeline as weapons
    out = []
    for a in artifacts:
        extra = {'code': weapons.code_hash(weapons.CODE[a.kind])}
        if a.kind in weapons.IMAGE_STAGES:
            extra['env'] = weapons.environment()
        out.append(dataclasses.replace(a, params={**a.params, **extra}))
    return out


def run(selection, out, cache, force=False, log=print, stages=STAGES):
    out = Path(out)
    results = []

    def stage(name, artifacts):
        if name not in stages:
            return
        res = run_artifacts(artifacts, out, Path(cache), force=force)
        log(f'{name:9} {sum(r.built for r in res):4} gebaut · {sum(not r.built for r in res):4} aus dem Cache')
        results.extend(res)

    stage('geometry', [Artifact(sid, 'geometry', source_hash(e), {'code': _code()},
                                {'MODEL': versions.MODEL, 'GEOM': versions.GEOM, 'ROBOT': ROBOT}, f'geometry/{sid}.json',
                                'formgen.robot.pipeline:build_geometry', {'entry': e}) for sid, e in selection.items()])
    derived = lambda sid, e: {'geometry_path': str((out / 'geometry' / f'{sid}.json').resolve()), 'entry': e}
    stage('asset', [Artifact(sid, 'asset', file_hash(out / 'geometry' / f'{sid}.json'), {'code': _code(), 'skin': e['skin'], 'skin_sha': file_hash(ROOT / 'skins.toml')},
                             {'ROBOT': ROBOT}, f'assets/{sid}.glb', 'formgen.robot.pipeline:build_asset', derived(sid, e)) for sid, e in selection.items()])
    stage('specs', [Artifact(sid, 'specs', file_hash(out / 'geometry' / f'{sid}.json'), {'code': _code(), 'entry': e, 'skin_sha': file_hash(ROOT / 'skins.toml')}, {'ROBOT': ROBOT}, f'specs/{sid}.spec.json',
                             'formgen.robot.pipeline:build_robot_spec', derived(sid, e)) for sid, e in selection.items()])
    ids = list(selection)
    if not set(stages) & set(IMAGE_STAGES):
        return results
    stage('prompts', _coded(build.downstream_plan(ids, out, 'prompts')))
    views = []
    for sid, e in selection.items():
        views += build.downstream_plan([sid], out, 'views', skin=e['skin'])
    stage('views', _coded(views))
    stage('fonts', build.font_plan())
    stage('sheets', _coded(build.downstream_plan(ids, out, 'sheets')))
    previews = []
    for sid, e in selection.items():
        previews += build.downstream_plan([sid], out, 'previews', skin=e['skin'])
    stage('previews', _coded(previews))
    return results


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('ids', nargs='*', help='Blatt-IDs (RA01 …); ohne Angabe alle Linien')
    p.add_argument('--out', type=Path, default=ROOT / 'out')
    p.add_argument('--cache', type=Path, default=build.DEFAULT_CACHE)
    p.add_argument('--force', action='store_true')
    p.add_argument('--list', action='store_true', help='Register anzeigen (Blatt, Linie, Typ, Skin, Parameter) und beenden; baut nichts')
    p.add_argument('--stages', help='Kommagetrennt aus ' + ','.join(STAGES) + '; ohne Angabe alle. Ohne Bildstufen braucht der Lauf keine Sperre.')
    a = p.parse_args(argv)
    sheets = lines.sheets()
    if a.list:
        for sid, e in sheets.items():
            print(f"{sid}  Linie {e['line']['letter']} {e['line']['name']:<12} {e['type']['name_de']:<16} Skin {e['skin']:<13} {json.dumps(e['params'], sort_keys=True) if e['params'] else '-'}")
        return 0
    unknown = [i for i in a.ids if i not in sheets]
    if unknown:
        raise SystemExit(f"Unbekannte Blatt-ID: {', '.join(unknown)}")
    run({i: sheets[i] for i in a.ids} if a.ids else sheets, a.out, a.cache, a.force, stages=a.stages.split(',') if a.stages else STAGES)
    return 0
