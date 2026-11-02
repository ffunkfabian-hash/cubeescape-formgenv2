"""Baut eine Waffe mit BALLONs eigenem Werkzeug (läuft in Blender, aufgerufen von formgen/asset.py).

  blender -b --factory-startup -P formgen/blender/asset_build.py -- <job.json>

job.json: snapshot (formgen.ballon_kit), module (BALLON-Grundmodul), model (META/PARTS/ASSEMBLIES/ANCHORS/ACTIONS des Generators
oder null = Modul unverändert), id, out; optional package, skin, atlas, samples, gpu.

Nichts hier baut Geometrie oder Materialien selbst:
  1. tools/blender_build.main aus dem Schnappschuss, unverändert (kit.reset_scene, kit.build mit Fasen-Modifiern, Durchbrüchen und
     Rollenmaterialien, write_spec, glTF-Export mit angewandten Modifikatoren). Ein Generatormodell wird dafür nur für diesen Lauf
     als Modul `basic.weapons.formgen_<id>` eingehängt (alle übrigen Modulfelder vom Grundmodul). → <id>.glb, <id>.spec.json
  2. nur mit package: Spielpaket wie tools/export_unity.bake_weapon (setup_render aaa/mid, Skin, kit.set_mode('aaa'),
     bake_unity.apply_modifiers/unwrap/bake_atlas, export_unity.mesh_bounds/export_fbx/store_textures)
     → <id>.fbx, textures/, <id>.package.json. Abweichung: ohne Ego-Arme in der Szene (BALLON backt in der Ego-Szene).
"""
import importlib
import json
import os
import shutil
import sys
import types


def main():
    job = json.load(open(sys.argv[sys.argv.index('--') + 1], encoding='utf-8'))
    out, sid = job['out'], job['id']
    os.environ['BASIC_OUT'] = os.path.join(out, '_ballon_out')   # tools.paths: nichts landet in BALLONs Ausgabeordner
    sys.path.insert(0, job['snapshot'])
    import bpy
    from basic import kit
    import tools.blender_build as BB

    base = importlib.import_module(job['module'])          # Seiteneffekte des Moduls (zusätzliche Materialrollen) wie bei BALLON
    W = base
    if job.get('model'):
        W = types.ModuleType(f"basic.weapons.formgen_{sid}")
        W.__dict__.update({k: v for k, v in vars(base).items() if not k.startswith('__')})
        W.__file__ = base.__file__
        for k, v in job['model'].items():
            setattr(W, k, v)
        sys.modules[W.__name__] = W
    name = W.__name__.split('basic.', 1)[1]
    name = name.split('weapons.', 1)[1] if name.startswith('weapons.') else name
    sys.argv = ['blender_build', '--', name]
    BB.main()
    wid = W.META['id'] + (f"-{W.META['variant']}" if W.META.get('variant') else '')
    for ext in ('glb', 'spec.json'):
        shutil.copyfile(os.path.join(os.environ['BASIC_OUT'], wid, f'{wid}.{ext}'), os.path.join(out, f'{sid}.{ext}'))
    if job.get('package'):
        package(job, W, bpy, kit, BB)
    print(f"[formgen-asset] {sid}: {name} gebaut", flush=True)


def package(job, W, bpy, kit, BB):
    from basic.arms import ego as EG
    from tools import bake_unity as BK
    import tools.export_unity as EU
    out, sid = job['out'], job['id']
    tex_dir = os.path.join(out, 'textures')
    os.makedirs(tex_dir, exist_ok=True)
    objs = {p['id']: bpy.data.objects[p['id']] for p in W.PARTS}
    root = bpy.data.objects[W.META['id']]
    BB.setup_render(854, 1, gpu=job['gpu'], aaa=True, bloom=False, bg='mid')
    kit.SKIN['name'] = job['skin']
    kit.set_mode(objs, 'aaa')
    wobs = [root] + list(root.children_recursive)
    meshes = [o for o in wobs if o.type == 'MESH']
    BK.apply_modifiers(meshes)
    BK.SKIP_ROLES |= BK._skip_roles()
    bake = [o for o in meshes if BK.bakeable(o)]
    BK.unwrap(bake)
    files = BK.bake_atlas(bake, sid, job['atlas'], tex_dir, gpu=job['gpu'], samples=job['samples'])
    ids = set(objs)
    bounds = [b for k, b in EU.mesh_bounds().items() if k in ids]
    kit.SKIN['name'] = 'standard'                            # wie bake_weapon: FBX mit den Standard-AAA-Materialien
    kit.set_mode(objs, 'aaa')
    EU.export_fbx(os.path.join(out, f'{sid}.fbx'), wobs)
    S = kit.SKINS[job['skin']]
    tex = EU.store_textures(dict(weapon=dict(size=job['atlas'], objects=sorted(o.name for o in bake), **files),
                                 skins=[dict(name=job['skin'], de=S['de'], kind=S['kind'], albedo=files['albedo'], spec=files['spec'])]),
                            tex_dir)
    try:
        weapon, ego = EU.weapon_data(W, EG.profile(W)['live']), None
    except (KeyError, ValueError) as e:      # Typ ohne Ego-Klasse (Schwert, Glefe) oder fehlende Live-Teile
        weapon, ego = None, str(e)
    manifest = dict(
        format='formgenv2/weapon-package', format_version=1, id=sid, skin=job['skin'], blender=bpy.app.version_string,
        ballon=dict(module=job['module'], weapon_id=EG.weapon_id(W), parts_sha256=EU.parts_sha(W)),
        axes=EU.AXES, units='m', origin='Socket_Hand', fbx=f'{sid}.fbx', textures=tex,
        mesh_bounds=dict(objects=bounds, triangles=sum(b['tris'] for b in bounds)),
        roles={p['id']: p['mat'] for p in W.PARTS}, weapon=weapon, ego_profile_error=ego,
        bake=dict(atlas=job['atlas'], samples=job['samples'], device='gpu' if job['gpu'] else 'cpu',
                  note='ohne Ego-Arme in der Szene; sonst wie tools/export_unity.bake_weapon'))
    with open(os.path.join(out, f'{sid}.package.json'), 'w', encoding='utf-8') as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1, sort_keys=True)


main()
