"""Roboter im AAA-Licht: kleinster Cycles-Weg für die Abnahme eines Skins, Vorbild `tools/series_evidence.py`.

  ./ce lock gpu -- "$PWD/.venv/bin/python" tools/robot_cycles.py [RA01] [--glb <datei>] [--tag vorher] [--samples 96] [--res 1000] [--out <ordner>] [--cpu]

Die Figur kommt als fertiges GLB (Stufe `asset`, `python -m formgen.robot`), die Materialien aus BALLONs `kit.material(rolle, 'aaa')` und das
Licht aus `BB.setup_render(aaa=True)` des gepinnten Schnappschusses; Skin und `finish` hängt der Lauf nur für sich in den Kit, wie
`formgen/blender/asset_build.py`. Keine Stufe der Pipeline: Das GLB bleibt die Lieferung, dieses Bild nur der Abnahmebeleg, Ausgabe außerhalb des Repos.

<out>/<ID><tag>_{hero,nah}.png und <ID><tag>_rollen.json: je Rolle der gemessene Farbwert im Bild neben dem Hex des Skins, aus einer Rollenmaske
derselben Kamera. AgX und Key-Licht bleichen; darum wird die Palette hier abgenommen, nicht am Raster-Blatt.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from formgen import asset, ballon_kit  # noqa: E402
from formgen.robot import lines  # noqa: E402

OUT = Path.home() / "Library/Caches/CubeEscapeFormgen2/0.10/belege"
# Vorgabe BALLON 14bd78d, tools/robot_build.py: `AMBIENT`, `lights()`, Ansichten `hero`/`nah` im Hochformat 4:5
SCENE = {
    "ambient": 0.35,
    "lights": [["Key", [-3.6, -1.4, 3.2], 560, 1.6, "#FFDDB8"], ["Fill", [2.6, -2.8, 1.4], 45, 3.0, "#D2DEEC"], ["Rim", [1.8, 2.8, 2.6], 950, 1.8, "#A9D3FF"]],
    "views": {"hero": [[-1.9, -3.4, 0.62], [0.0, 0.0, 0.98], 60], "nah": [[-1.15, -1.9, 1.55], [0.0, -0.12, 1.36], 50]},
}
WRAPPER = r'''
import addon_utils, json, os, sys
job = json.load(open(sys.argv[sys.argv.index('--') + 1], encoding='utf-8'))
sys.path.insert(0, job['snapshot'])
os.environ['BASIC_OUT'] = job['out']
import bpy
from mathutils import Vector
from basic import kit
import tools.blender_build as BB
kit.reset_scene()
addon_utils.enable('io_scene_gltf2')
skin = job['skin_def']
kit.SKINS[job['skin']] = dict(skin, roles={**skin['roles'], **skin.get('aaa', {})})
kit.SKIN['name'] = job['skin']
for role, finish in skin.get('finish', {}).items():
    kit.MATERIALS[role].update(finish)
BB.setup_render(job['res'], job['samples'], aspect=(4, 5), gpu=job['gpu'], aaa=True, bloom=False, bg='mid')
sc = bpy.context.scene
for n in sc.world.node_tree.nodes:
    if n.type == 'BACKGROUND' and not n.inputs['Color'].links:
        n.inputs['Strength'].default_value *= job['scene']['ambient']
for name, loc, energy, size, color in job['scene']['lights']:
    o = bpy.data.objects[name]
    o.location, o.data.energy, o.data.size, o.data.color = loc, energy, size, kit.hex_rgba(color)[:3]
    o.rotation_euler = (Vector((0, 0, 1.0)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.import_scene.gltf(filepath=job['glb'])
parts = [o for o in sc.objects if o.type == 'MESH']
roles = sorted({o['basic_role'] for o in parts})
for o in parts:
    o.data.materials[0] = kit.material(o['basic_role'], 'aaa')
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
floor = bpy.context.active_object
floor.is_shadow_catcher = True
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
sc.collection.objects.link(cam)
sc.camera = cam


def shoot(suffix):
    for name, (pos, at, lens) in job['scene']['views'].items():
        pos, at = Vector(pos), Vector(at)
        cam.data.lens = lens
        cam.location = pos
        cam.rotation_euler = (at - pos).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(job['out'], f"{name}{suffix}.png")
        bpy.ops.render.render(write_still=True)


shoot('')
# Rollenmaske: gleiche Kamera, je Rolle ein Grauwert ohne Licht
floor.hide_render = True
sc.view_settings.view_transform, sc.view_settings.look = 'Standard', 'None'
sc.render.film_transparent = True
sc.cycles.samples, sc.cycles.use_denoising, sc.cycles.filter_width = 1, False, 0.01
for light in ('Key', 'Fill', 'Rim'):
    bpy.data.objects[light].hide_render = True
flat = {}
for i, role in enumerate(roles):
    m = bpy.data.materials.new('mask_' + role)
    m.use_nodes = True
    tree = m.node_tree
    tree.nodes.clear()
    emit, out = tree.nodes.new('ShaderNodeEmission'), tree.nodes.new('ShaderNodeOutputMaterial')
    value = (i + 1) / (len(roles) + 1)
    emit.inputs['Color'].default_value = (value, value, value, 1)
    tree.links.new(emit.outputs[0], out.inputs[0])
    flat[role] = m
for o in parts:
    o.data.materials[0] = flat[o['basic_role']]
shoot('_mask')
json.dump(roles, open(os.path.join(job['out'], 'roles.json'), 'w'))
'''


def srgb(linear):
    linear = np.asarray(linear, float)
    return np.where(linear <= .0031308, linear * 12.92, 1.055 * linear ** (1 / 2.4) - .055)


def measure(image, mask, roles, skin):
    """Je Rolle Median, Lichter und Schatten im Bild neben dem Soll-Hex; `clip` = Anteil ausgefressener Pixel."""
    rgb = np.asarray(Image.open(image).convert("RGB"), float)
    m = np.asarray(Image.open(mask).convert("RGBA"), float)
    levels = srgb((np.arange(len(roles)) + 1) / (len(roles) + 1)) * 255
    found = np.abs(m[..., 0, None] - levels).argmin(axis=-1)
    report = {}
    for i, role in enumerate(roles):
        inner = binary_erosion((found == i) & (m[..., 3] > 250), iterations=2)   # nur das Innere: Randpixel mischen sich mit dem Nachbarteil
        px = rgb[inner]
        if len(px) < 20:
            continue
        luma = px @ [.2126, .7152, .0722]
        hexa = "#%02X%02X%02X" % tuple(int(round(c)) for c in np.median(px, axis=0))
        report[role] = dict(soll=skin["roles"].get(role), bild=hexa, pixel=len(px), hell_p90=round(float(np.percentile(luma, 90))), dunkel_p10=round(float(np.percentile(luma, 10))),
                            median=round(float(np.median(luma))), clip=round(float((px.min(axis=1) >= 250).mean()), 4))
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("id", nargs="?", default="RA01")
    p.add_argument("--glb", type=Path)
    p.add_argument("--tag", default="")
    p.add_argument("--samples", type=int, default=96)
    p.add_argument("--res", type=int, default=1000)
    p.add_argument("--out", type=Path, default=OUT)
    p.add_argument("--skin", help="Skin statt des Registereintrags (Probe einer Palette, Datei skins.toml)")
    p.add_argument("--cpu", action="store_true")
    a = p.parse_args()
    entry = lines.sheets()[a.id]
    skin = a.skin or entry["skin"]
    definition = asset.skin_def(skin)
    glb = (a.glb or ROOT / "out/assets" / f"{a.id}.glb").resolve()
    a.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"formgen-robot-cycles-{a.id}-") as tmp:
        tmp = Path(tmp)
        (tmp / "wrapper.py").write_text(WRAPPER)
        job = dict(snapshot=str(ballon_kit.snapshot()), glb=str(glb), skin=skin, skin_def=definition, out=str(tmp), res=a.res, samples=a.samples, gpu=not a.cpu, scene=SCENE)
        (tmp / "job.json").write_text(json.dumps(job, ensure_ascii=False))
        run = subprocess.run([asset.settings()["blender"], "-b", "--factory-startup", "-P", str(tmp / "wrapper.py"), "--", str(tmp / "job.json")], capture_output=True, text=True)
        log = run.stdout + run.stderr
        if run.returncode or "Traceback" in log:
            raise SystemExit("\n".join(log.splitlines()[-20:]))
        roles = json.loads((tmp / "roles.json").read_text())
        report = {}
        for view in SCENE["views"]:
            target = a.out / f"{a.id}{a.tag}_{view}.png"
            target.write_bytes((tmp / f"{view}.png").read_bytes())
            report[view] = measure(tmp / f"{view}.png", tmp / f"{view}_mask.png", roles, definition)
    (a.out / f"{a.id}{a.tag}_rollen.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    for role, row in report["hero"].items():
        print(f"{role:12} Soll {row['soll']}  Bild {row['bild']}  dunkel {row['dunkel_p10']:3} median {row['median']:3} hell {row['hell_p90']:3}  ausgefressen {row['clip']:.1%}")


if __name__ == "__main__":
    main()
