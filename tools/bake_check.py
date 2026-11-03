"""AAA-Bake gegen BALLONs Unity-Atlas von BASIC-01 (0.6 „Hangar“): Texturen vergleichen und Hero-Bilder rendern.

  ~/Claude/cubeescape-nexogen/ce lock gpu -- .venv/bin/python tools/bake_check.py BA01 BD01

Referenz: BALLONs eingecheckter Unity-Export am Pin (`unity/Assets/Ballon/Generated/Textures/weapon_*` = Atlas BASIC-01-v2.1,
`BASIC-01-v2.1.fbx`), per `git show` nur gelesen. Vergleich je Kanal auf den belegten Texeln (Alpha/Albedo ≠ Hintergrund beider
Atlanten): mittlere absolute Abweichung (0–255), Anteil Texel > 8 Stufen, PSNR. BA01 (Pilot unverändert, Skin standard) muss dem
Standardatlas entsprechen; BD01 (gestreckt, Leuchtlinie, Skin eloxal) hat eine andere Abwicklung – dort nur Mittelwerte der
belegten Texel gegen `weapon_eloxal_*` (Farbe/Glanz) als Plausibilität. Hero-Bilder: FBX + Atlas in Blender (Cycles, AgX,
Hintergrund mittelgrau, ohne Bloom), Vorschau-Shader aus Albedo · AO, Spiegelfarbe/Glätte und Normalen (Annäherung an URP
Specular, nicht Unitys Shader). Ausgabe: <EVIDENCE>/belege/bake_check.json, hero_<ID>.png, hero_BALLON-BASIC-01.png, bake_hero.png.
"""
import argparse
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from formgen import asset, ballon  # noqa: E402

UNITY = "unity/Assets/Ballon/Generated"
REF_FILES = {"albedo": "Textures/weapon_albedo.jpg", "spec": "Textures/weapon_spec.png", "normal": "Textures/weapon_normal.png",
             "ao": "Textures/weapon_ao.png", "eloxal_albedo": "Textures/weapon_eloxal_albedo.jpg",
             "eloxal_spec": "Textures/weapon_eloxal_spec.png", "fbx": "BASIC-01-v2.1.fbx"}

RENDER = r'''
import bpy, json, math, sys
from mathutils import Vector
job = json.load(open(sys.argv[sys.argv.index('--') + 1]))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=job['fbx'])
obs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
def img(path, color):
    im = bpy.data.images.load(path)
    im.colorspace_settings.name = 'sRGB' if color else 'Non-Color'
    return im
mat = bpy.data.materials.new('atlas'); mat.use_nodes = True
nt = mat.node_tree; N = nt.nodes; L = nt.links
bsdf = N['Principled BSDF']
def tex(path, color):
    t = N.new('ShaderNodeTexImage'); t.image = img(path, color); return t
al, sp, nm, ao = tex(job['albedo'], True), tex(job['spec'], True), tex(job['normal'], False), tex(job['ao'], False)
mix = N.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs['Factor'].default_value = 1.0
L.new(al.outputs['Color'], mix.inputs['A']); L.new(ao.outputs['Color'], mix.inputs['B'])
L.new(mix.outputs['Result'], bsdf.inputs['Base Color'])
inv = N.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
L.new(sp.outputs['Alpha'], inv.inputs[1]); L.new(inv.outputs['Value'], bsdf.inputs['Roughness'])
L.new(sp.outputs['Color'], bsdf.inputs['Specular Tint'])
nmap = N.new('ShaderNodeNormalMap'); L.new(nm.outputs['Color'], nmap.inputs['Color']); L.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
for o in obs:
    if o.data.uv_layers:
        o.data.materials.clear(); o.data.materials.append(mat)
pts = [o.matrix_world @ Vector(c) for o in obs for c in o.bound_box]
lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
c = (lo + hi) / 2; size = max(hi - lo)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); bpy.context.scene.collection.objects.link(cam)
cam.data.lens = 50
# FBX in Unity-Achsen (BALLON export_fbx: axis_forward -Z, axis_up Y) zurückgelesen: Länge −Z = vorn, −Y = oben, X = Seite
from mathutils import Matrix
up = Vector((0, -1, 0))
d = Vector(job['dir']).normalized()
cam.location = c + d * size * 1.55
z = (cam.location - c).normalized(); x = up.cross(z).normalized(); y = z.cross(x)
cam.matrix_world = Matrix((x, y, z)).transposed().to_4x4()
cam.location = c + d * size * 1.55
bpy.context.scene.camera = cam
for direction, energy in (((0.6, -1.0, -0.4), 3.0), ((-0.8, -0.3, 0.6), 1.2)):   # Licht von oben-vorn-seitlich, Gegenlicht
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = energy
    sun.rotation_euler = (-Vector(direction)).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.collection.objects.link(sun)
w = bpy.data.worlds.new('w'); bpy.context.scene.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.18, 0.18, 0.18, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.6
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = job['samples']
if job['gpu']:
    pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'METAL'; pr.get_devices()
    for dv in pr.devices: dv.use = dv.type == 'METAL'
    sc.cycles.device = 'GPU'
sc.view_settings.view_transform = 'AgX'
sc.render.resolution_x, sc.render.resolution_y = job['size']
sc.render.film_transparent = False
sc.render.filepath = job['png']
bpy.ops.render.render(write_still=True)
print('[bake_check] gerendert', job['png'], flush=True)
'''


def ballon_file(rel: str, folder: Path) -> Path:
    cfg = ballon.config()
    data = subprocess.run(["git", "-C", str(cfg["repo"]), "show", f"{cfg['commit']}:{UNITY}/{rel}"], capture_output=True,
                          check=True).stdout
    path = folder / Path(rel).name
    path.write_bytes(data)
    return path


def load(path: Path, size=None) -> np.ndarray:
    im = Image.open(path).convert("RGBA")
    if size and im.size != size:
        im = im.resize(size, Image.Resampling.BOX)
    return np.asarray(im, np.float32)


def used(a: np.ndarray) -> np.ndarray:
    """Belegte Texel: Albedo weicht vom Hintergrund (Ecke links oben) ab."""
    return np.abs(a[..., :3] - a[0, 0, :3]).sum(-1) > 3


def fit(mask: np.ndarray, shape) -> np.ndarray:
    """Maske auf die Texturgröße (BALLONs store_textures legt Karten je Art in eigener Größe ab, z. B. AO 2048²)."""
    return mask if mask.shape == tuple(shape[:2]) else np.asarray(Image.fromarray(mask).resize((shape[1], shape[0])))


def compare(mine: Path, ref: Path, mask) -> dict:
    a = load(mine)
    b = load(ref, (a.shape[1], a.shape[0]))
    d = np.abs(a - b)[fit(mask, a.shape)][:, :3]
    mse = float((d ** 2).mean())
    return {"size": [a.shape[1], a.shape[0]], "mean_abs": round(float(d.mean()), 2), "over_8": round(float((d.max(1) > 8).mean()), 4),
            "psnr_db": round(10 * np.log10(255 ** 2 / mse), 1) if mse else None}


def stats(path: Path, mask) -> list:
    a = load(path)
    return [round(float(x), 1) for x in a[fit(mask, a.shape)][:, :4].mean(0)]


def render(job: dict, blender: str, tmp: Path) -> None:
    script, spec = tmp / "render.py", tmp / f"{Path(job['png']).stem}.json"
    script.write_text(RENDER)
    spec.write_text(json.dumps(job))
    run = subprocess.run([blender, "-b", "--factory-startup", "-P", str(script), "--", str(spec)], capture_output=True, text=True)
    if run.returncode or "[bake_check] gerendert" not in run.stdout:
        raise RuntimeError("\n".join((run.stdout + run.stderr).splitlines()[-20:]))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("ids", nargs="+")
    p.add_argument("--out-dir", type=Path, default=ROOT / "out")
    p.add_argument("--evidence", type=Path, default=asset.EVIDENCE / "belege")
    p.add_argument("--samples", type=int, default=64)
    p.add_argument("--cpu", action="store_true")
    a = p.parse_args(argv)
    cfg = asset.settings()
    a.evidence.mkdir(parents=True, exist_ok=True)
    report = {"ballon_commit": ballon.config()["commit"], "reference": f"{UNITY}/{{Textures/weapon_*, BASIC-01-v2.1.fbx}}", "sheets": {}}
    heroes = []
    # FBX-Rahmen: Seite +X, etwas von oben (−Y), von vorn (−Z)
    view = {"dir": [1.0, -0.35, -0.6], "size": [1280, 720], "samples": a.samples, "gpu": not a.cpu}
    with tempfile.TemporaryDirectory(prefix="formgen-bakecheck-") as tmp:
        tmp = Path(tmp)
        ref = {k: ballon_file(v, tmp) for k, v in REF_FILES.items()}
        ref_mask = used(load(ref["albedo"]))
        png = a.evidence / "hero_BALLON-BASIC-01.png"
        render({**view, "fbx": str(ref["fbx"]), "albedo": str(ref["albedo"]), "spec": str(ref["spec"]), "normal": str(ref["normal"]),
                "ao": str(ref["ao"]), "png": str(png)}, cfg["blender"], tmp)
        heroes.append(("BALLON BASIC-01-v2.1 · Unity-Atlas", png))
        for sid in a.ids:
            folder = tmp / sid
            with zipfile.ZipFile(a.out_dir / f"assets/{sid}.bake.zip") as archive:
                archive.extractall(folder)
            manifest = json.loads((folder / f"{sid}.package.json").read_text())
            tex = manifest["textures"]["weapon"]
            files = {k: folder / "textures" / tex[k] for k in ("albedo", "spec", "normal", "ao")}
            mine_albedo = load(files["albedo"])
            mask = used(mine_albedo) & fit(ref_mask, mine_albedo.shape)
            entry = {"skin": manifest["skin"], "atlas": manifest["bake"]["atlas"], "triangles": manifest["mesh_bounds"]["triangles"],
                     "objects": len(manifest["textures"]["weapon"]["objects"]), "files": {k: v.name for k, v in files.items()},
                     "weapon_block": manifest["weapon"] is not None}
            if manifest["skin"] == "standard":
                entry["vs_ballon"] = {k: compare(files[k], ref[k], mask) for k in ("albedo", "spec", "normal", "ao")}
            else:
                mine_mask = used(load(files["albedo"]))
                entry["mean_used"] = {"albedo": stats(files["albedo"], mine_mask), "spec": stats(files["spec"], mine_mask),
                                      f"ballon_{manifest['skin']}_albedo": stats(ref.get(f"{manifest['skin']}_albedo", ref["albedo"]), ref_mask),
                                      f"ballon_{manifest['skin']}_spec": stats(ref.get(f"{manifest['skin']}_spec", ref["spec"]), ref_mask)}
            report["sheets"][sid] = entry
            png = a.evidence / f"hero_{sid}.png"
            render({**view, "fbx": str(folder / manifest["fbx"]), **{k: str(v) for k, v in files.items()}, "png": str(png)},
                   cfg["blender"], tmp)
            heroes.append((f"{sid} · {manifest['skin']} · Formgen v2 0.6 Bake", png))
            print(sid, json.dumps(entry.get("vs_ballon") or entry.get("mean_used"), ensure_ascii=False))
    tiles = [Image.open(p).convert("RGB").resize((640, 360)) for _, p in heroes]
    sheet = Image.new("RGB", (640 * len(tiles), 400), "#7a7a7a")
    d = ImageDraw.Draw(sheet)
    for i, ((label, _), t) in enumerate(zip(heroes, tiles)):
        sheet.paste(t, (640 * i, 0)); d.text((640 * i + 12, 372), label, fill="#ffffff")
    sheet.save(a.evidence / "bake_hero.png")
    (a.evidence / "bake_check.json").write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
    print(a.evidence / "bake_check.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
