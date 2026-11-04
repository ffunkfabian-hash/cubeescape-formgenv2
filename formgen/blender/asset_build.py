"""Baut eine Waffe mit BALLONs eigenem Werkzeug (läuft in Blender, aufgerufen von formgen/asset.py).

  blender -b --factory-startup -P formgen/blender/asset_build.py -- <job.json>

job.json: snapshot (formgen.ballon_kit), module (BALLON-Grundmodul), model (META/PARTS/ASSEMBLIES/ANCHORS/POINTS/ACTIONS des
Generators oder null = Modul unverändert), id, out; optional package, skin, skin_def (Skin einer Design-Serie, Form wie kit.SKINS), atlas,
samples, gpu, package_version (= formgen.asset.BAKE).

Nichts hier baut Geometrie oder Materialien selbst; alle Aufrufe sind BALLONs Schnittstellen ab 0.41 (docs/formgen-schnittstelle.md):
  1. tools/blender_build.main aus dem Schnappschuss, unverändert (kit.reset_scene, kit.build mit Fasen-Modifiern, Durchbrüchen und
     Rollenmaterialien, write_spec, glTF-Export mit angewandten Modifikatoren). Ein Generatormodell geht als Datensatz hinein
     (`main(W=model, base=Grundmodul)`, intern basic/variant.as_module: übrige Modulfelder vom Grundmodul, Weltpunkte aus POINTS);
     ohne Modell der Modulname wie auf BALLONs Kommandozeile. → <id>.glb, <id>.spec.json
  2. nur mit package: Spielpaket über tools/export_unity.bake_weapon (Atlas ohne Arme, arms=False – Regel beider Wege ab BALLON
     0.41; Skin der Linie als Atlasfarbe, FBX mit Standard-AAA-Materialien), export_unity.mesh_bounds/store_textures/weapon_data/
     parts_sha → <id>.fbx, textures/, <id>.package.json (formgenv2/weapon-package 2: mit Datensatz `model`).
"""
import importlib
import json
import os
import shutil
import sys

def main():
    job = json.load(open(sys.argv[sys.argv.index('--') + 1], encoding='utf-8'))
    out, sid = job['out'], job['id']
    os.environ['BASIC_OUT'] = os.path.join(out, '_ballon_out')   # tools.paths: nichts landet in BALLONs Ausgabeordner
    sys.path.insert(0, job['snapshot'])
    import bpy
    from basic import kit, variant
    import tools.blender_build as BB

    base = importlib.import_module(job['module'])          # Seiteneffekte des Moduls (zusätzliche Materialrollen) wie bei BALLON
    name = job['module'].split('basic.', 1)[1]
    name = name.split('weapons.', 1)[1] if name.startswith('weapons.') else name
    if job.get('model'):
        BB.main(W=job['model'], base=base, argv=[])
        W = variant.as_module(job['model'], base)            # dasselbe Modul wie in BB.main, für das Paket
    else:
        BB.main(argv=[name])
        W = base
    wid = W.META['id'] + (f"-{W.META['variant']}" if W.META.get('variant') else '')
    for ext in ('glb', 'spec.json'):
        shutil.copyfile(os.path.join(os.environ['BASIC_OUT'], wid, f'{wid}.{ext}'), os.path.join(out, f'{sid}.{ext}'))
    if job.get('package'):
        package(job, W, bpy, kit, BB)
    print(f"[formgen-asset] {sid}: {name} gebaut", flush=True)


def dataset(job, W):
    """Datensatz für Paket 2: das Generatormodell, im Modulweg (model null) die Datenfelder des Moduls selbst (POINTS leer, wenn das
    Modul keine trägt) – ein selbst erzeugtes Paket ist so immer lesbar (formgen.asset.read_package)."""
    if job.get('model'):
        return job['model']
    from basic import variant
    return json.loads(json.dumps({k: getattr(W, k, {} if k in ('POINTS', 'ACTIONS') else None) for k in variant.DATA_FIELDS}))


def package(job, W, bpy, kit, BB):
    from basic.arms import ego as EG
    import tools.export_unity as EU
    out, sid = job['out'], job['id']
    tex_dir = os.path.join(out, 'textures')
    os.makedirs(tex_dir, exist_ok=True)
    objs = {p['id']: bpy.data.objects[p['id']] for p in W.PARTS}
    root = bpy.data.objects[W.META['id']]
    BB.setup_render(854, 1, gpu=job['gpu'], aaa=True, bloom=False, bg='mid')
    if job.get('skin_def'):                                 # Palette einer Design-Serie: nur für diesen Lauf im Kit, BALLON bleibt unberührt
        kit.SKINS[job['skin']] = job['skin_def']
    kit.SKIN['name'] = job['skin']                          # Atlasfarbe = Skin der Linie; bake_weapon setzt danach Standard (FBX)
    kit.set_mode(objs, 'aaa')
    tex = EU.bake_weapon(root, tex_dir, sid, fbx=os.path.join(out, f'{sid}.fbx'), skins=False, gpu=job['gpu'], arms=False,
                         objs=objs, size=job['atlas'], samples=job['samples'])
    S = kit.SKINS[job['skin']]
    tex['skins'] = [dict(name=job['skin'], de=S['de'], kind=S['kind'], albedo=tex['weapon']['albedo'], spec=tex['weapon']['spec'])]
    tex = EU.store_textures(tex, tex_dir)
    ids = set(objs)
    bounds = [b for k, b in EU.mesh_bounds().items() if k in ids]
    try:
        weapon, ego = EU.weapon_data(W, EG.profile(W)['live']), None
    except (KeyError, ValueError) as e:      # Typ ohne Ego-Klasse (Schwert, Glefe) oder fehlende Live-Teile
        weapon, ego = None, str(e)
    manifest = dict(
        format='formgenv2/weapon-package', format_version=job['package_version'], id=sid, skin=job['skin'], blender=bpy.app.version_string,
        ballon=dict(module=job['module'], weapon_id=EG.weapon_id(W), parts_sha256=EU.parts_sha(W)),
        axes=EU.AXES, units='m', origin='Socket_Hand', fbx=f'{sid}.fbx', textures=tex,
        mesh_bounds=dict(objects=bounds, triangles=sum(b['tris'] for b in bounds)),
        roles={p['id']: p['mat'] for p in W.PARTS}, weapon=weapon, ego_profile_error=ego, model=dataset(job, W),
        bake=dict(atlas=job['atlas'], samples=job['samples'], device='gpu' if job['gpu'] else 'cpu', arms=False,
                  note='tools/export_unity.bake_weapon ohne Ego-Szene, Atlas ohne Arme (BALLON 0.41)'))
    with open(os.path.join(out, f'{sid}.package.json'), 'w', encoding='utf-8') as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1, sort_keys=True)


main()
