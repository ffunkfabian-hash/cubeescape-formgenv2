"""Waffen-Assets über BALLONs Blender-Kit: 0.5 „Forge“ (Machbarkeitsnachweis), 0.6 „Hangar“ (Stufe asset, Bake, Piloten).

Ohne Blender: Kitmodell aus `generator.vary`, Schlüssel, Kit-Schnappschuss, Asset-Cache Treffer/Fehltreffer (Blender ersetzt),
Bake-Schlüssel, GPU-Sperre, ZIP. Mit vorhandenen Ergebnissen (Mac, nach `pipeline` und `tools/line_a_parity.py`): Linie A
bytegleich zu BALLONs Neubau am Pin.
"""
import hashlib
import io
import json
import os
import shutil
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from formgen import asset, ballon, ballon_kit, generator, pipeline, raster, variants
from formgen.cache import canonical

try:
    SNAP, KIT = ballon.snapshot(), ballon_kit.snapshot()
except ballon.BallonError as error:   # z. B. Cloud ohne BALLON-Checkout
    SNAP, KIT, REASON = None, None, str(error)
else:
    REASON = ""
OUT = asset.ROOT / "out"
PARITY = asset.EVIDENCE / "belege/line_a_parity.json"


def kit_model(sid):
    entry = variants.sheets()[sid]
    model, run, base = asset.variant_model(entry, SNAP)
    return ballon.load(SNAP, entry["num"], base), model


def package_manifest(version: int, sid: str = "BX01") -> dict:
    """Kleinstes Manifest wie formgen/blender/asset_build.py: Format 1 (0.6) ohne, Format 2 (0.7) mit Datensatz `model`."""
    tex = {k: f"{sid}_{k}.png" for k in ("albedo", "spec", "normal", "ao")}
    m = {"format": asset.PACKAGE, "format_version": version, "id": sid, "skin": "standard", "weapon": {"parts": []},
         "fbx": f"{sid}.fbx", "textures": {"weapon": tex, "skins": [{"name": "standard", "albedo": tex["albedo"], "spec": tex["spec"]}]}}
    if version >= 2:
        m["model"] = {"META": {"id": "BASIC-01"}, "PARTS": [{"id": "grip", "asm": "grip"}], "ASSEMBLIES": [{"id": "grip"}],
                      "ANCHORS": {"Socket_Hand": {"at": [0, 0, 0], "part": "grip"}},
                      "POINTS": {"grip.grip": {"at": [0.0, 10, -2.5], "part": "grip"}}, "ACTIONS": {}}
    return m


def package_folder(folder: Path, manifest: dict) -> None:
    """Paketordner mit allen Dateien, die das Manifest nennt (Inhalt egal)."""
    (folder / "textures").mkdir(parents=True, exist_ok=True)
    (folder / f"{manifest['id']}.package.json").write_text(json.dumps(manifest))
    for name in asset.package_files(manifest):
        (folder / name).write_bytes(b"x")


def with_model(**fields) -> dict:
    """Paket 2 mit geänderten Feldern im Datensatz."""
    m = package_manifest(2)
    m["model"] = {**m["model"], **fields}
    return m


def fake_glb(payload: dict) -> bytes:
    """Minimale GLB (nur JSON-Chunk) – reicht für glb_info/Index."""
    chunk = json.dumps({"asset": {"version": "2.0"}, "nodes": [{"name": "Root"}], "extras": payload}).encode()
    chunk += b" " * (-len(chunk) % 4)
    body = struct.pack("<II", len(chunk), 0x4E4F534A) + chunk
    return b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body


def skin_sample(bin_chunk=b"\x01\x02\x03\x04") -> bytes:
    """GLB mit Rollenmaterialien wie BALLONs Export und einem BIN-Block."""
    glow = {"name": "MT_energy_color", "extras": {"basic_role": "energy"}, "emissiveFactor": [0.15, 0.87, 1.0],
            "pbrMetallicRoughness": {"baseColorFactor": [0.114, 0.651, 0.745, 1]}}
    glass = {"name": "MT_glass_color", "extras": {"basic_role": "glass"}, "pbrMetallicRoughness": {"baseColorFactor": [0.5, 0.7, 0.8, 0.12]}}
    shell = {"name": "MT_shell_color", "extras": {"basic_role": "shell"},
             "pbrMetallicRoughness": {"baseColorFactor": [0.68, 0.6, 0.45, 1], "metallicFactor": 0, "roughnessFactor": 0.55}}
    metal = {"name": "MT_metal_color", "extras": {"basic_role": "metal"}, "pbrMetallicRoughness": {"baseColorFactor": [0.26, 0.28, 0.31, 1]}}
    chunk = json.dumps({"asset": {"version": "2.0"}, "materials": [shell, metal, glow, glass]}).encode()
    chunk += b" " * (-len(chunk) % 4)
    body = struct.pack("<II", len(chunk), 0x4E4F534A) + chunk + struct.pack("<II", len(bin_chunk), 0x004E4942) + bin_chunk
    return b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body


def skin_materials(data: bytes) -> dict:
    size = struct.unpack("<I", data[12:16])[0]
    return {m["extras"]["basic_role"]: m for m in json.loads(data[20:20 + size])["materials"]}


class SkinGlbTests(unittest.TestCase):
    def test_linear_rgb_matches_blenders_export(self):
        for got, want in zip(asset.linear_rgb("#E0651E"), (0.7454042, 0.1301365, 0.0129830)):     # MT_accent_color der Stufe asset
            self.assertAlmostEqual(got, want, places=5)

    def test_standard_returns_the_same_bytes(self):
        data = skin_sample()
        self.assertEqual(asset.skin_glb(data, asset.skin_style("standard")), data)

    def test_skin_colors_only_its_roles_and_keeps_the_mesh_chunk(self):
        data = skin_sample()
        result = asset.skin_glb(data, asset.skin_style("wueste"))
        before, after = skin_materials(data), skin_materials(result)
        self.assertEqual(after["shell"]["pbrMetallicRoughness"]["baseColorFactor"], [*asset.linear_rgb("#B8A27E"), 1])
        self.assertEqual(after["metal"], before["metal"])
        self.assertEqual(after["glass"], before["glass"])
        self.assertEqual(struct.unpack("<I", result[8:12])[0], len(result))
        self.assertEqual(len(result) % 4, 0)
        self.assertTrue(result.endswith(struct.pack("<II", 4, 0x004E4942) + b"\x01\x02\x03\x04"))
        self.assertEqual(result[:8], data[:8])

    def test_glow_follows_the_skin_at_the_same_brightness(self):
        after = skin_materials(asset.skin_glb(skin_sample(), asset.skin_style("perle")))["energy"]
        rgb = asset.linear_rgb("#FF5A3A")
        self.assertEqual(after["pbrMetallicRoughness"]["baseColorFactor"], [*rgb, 1])
        self.assertAlmostEqual(max(after["emissiveFactor"]), 1.0)
        for got, want in zip(after["emissiveFactor"], rgb):
            self.assertAlmostEqual(got, want / max(rgb))

    def test_metal_shell_and_pattern_ground_tone(self):
        shell = skin_materials(asset.skin_glb(skin_sample(), asset.skin_style("eloxal")))["shell"]["pbrMetallicRoughness"]
        self.assertEqual((shell["metallicFactor"], shell["roughnessFactor"]), (0.85, 0.32))
        shell = skin_materials(asset.skin_glb(skin_sample(), asset.skin_style("tarnung")))["shell"]["pbrMetallicRoughness"]
        self.assertEqual(shell["baseColorFactor"], [*asset.linear_rgb("#6F7360"), 1])

    def test_every_line_gets_the_colors_the_sheet_shows(self):
        data = raster.palette()
        for entry in variants.load():
            for role, color in asset.skin_style(entry["skin"])["roles"].items():
                if not data["skins"][entry["skin"]].get("pattern") or role != "shell":
                    self.assertEqual(color, raster.material({"role": role}, entry["skin"], data)["color"], (entry["letter"], role))


    @unittest.skipIf(KIT is None, REASON)
    def test_metal_shell_values_match_the_pinned_kit(self):
        values = asset.METAL_SHELL
        self.assertIn(f"d.update(metal={values['metallicFactor']}, rough={values['roughnessFactor']})", (KIT / "basic/kit.py").read_text(encoding="utf-8"))


@unittest.skipUnless((OUT / "assets/index.json").is_file(), "keine gebauten GLBs unter out/assets")
class BuiltGlbSkinTests(unittest.TestCase):
    def test_built_glbs_carry_the_skin_of_their_line(self):
        checked = 0
        for sid, entry in variants.sheets().items():
            path = OUT / f"assets/{sid}.glb"
            if not path.is_file():
                continue
            style = asset.skin_style(entry["variant"]["skin"])
            materials = asset.glb_json(path)["materials"]
            self.assertTrue(all("basic_role" in m.get("extras", {}) for m in materials), sid)
            for material in materials:
                color = style["roles"].get(material["extras"]["basic_role"])
                if color:
                    for got, want in zip(material["pbrMetallicRoughness"]["baseColorFactor"], asset.linear_rgb(color)):
                        self.assertAlmostEqual(got, want, places=4, msg=f"{sid} {material['name']}")
                    checked += 1
        self.assertGreater(checked, 0)


@unittest.skipIf(SNAP is None, REASON)
class KitModelTests(unittest.TestCase):
    def test_trestle_aaa_uses_bt01_dataset_and_tracks_its_sources(self):
        from formgen import extended
        # EX-18 reserviert die bestehende BT01-ID; es gibt kein zweites EA18-Modell.
        self.assertEqual(extended.PIPELINE_SHEETS, {"e18": "BT01"})
        self.assertFalse(extended.PIPELINE_SHEETS.keys() & extended.MODELS.keys())
        self.assertFalse(extended.PIPELINE_SHEETS.keys() & extended.SHEETS.keys())
        sheets = {**extended.SHEETS, **extended.PIPELINE_SHEETS}
        self.assertEqual(len(sheets), len(set(sheets.values())))
        self.assertNotIn("EA18", sheets.values())
        self.assertEqual(extended.sheet_id("e18"), "BT01")
        for key, sid in extended.SHEETS.items():
            self.assertEqual(extended.sheet_id(key), sid)
        _, exported = kit_model("BT01")
        self.assertEqual(canonical(extended.load("e18", SNAP)), canonical(exported))
        source = extended.source("e18", SNAP)
        for name in ("formgen/models/weapons/trestle.py", "formgen/models/weapons/legacy_shared.py",
                     "basic/common.py"):
            with self.subTest(source=name):
                self.assertIn(name, source["files"])
                root = SNAP if name.startswith("basic/") else asset.ROOT
                self.assertEqual(source["files"][name], hashlib.sha256((root / name).read_bytes()).hexdigest())
        self.assertEqual(source["source_sha256"], hashlib.sha256(canonical(source["files"])).hexdigest())

    def test_trestle_exports_its_static_shell_with_standard_h0_and_game_sockets(self):
        data, result = kit_model("BT01")
        self.assertEqual(result["META"]["id"], "BT01")
        self.assertEqual(result["META"]["variant"], "EXTENDED-18")
        self.assertFalse(result["ACTIONS"])
        self.assertEqual(set(result["POINTS"]), set(data["POINTS"]))
        parts = {part["id"]: part for part in result["PARTS"]}
        self.assertTrue({"arch", "fore_cuff", "face", "handle", "cassette"} <= parts.keys())
        self.assertFalse(any(key.startswith("optic_") for key in parts))
        self.assertEqual(parts["rail"]["iface"], "BRI-22")
        self.assertEqual(len(parts["rail"]["cuts"]), 6)
        # Nutzerentscheid 24.11.2026: H0 unverändert auf BRI-22, Linie +105 mm.
        kit_parts, kit_anchors = ballon.call(SNAP, "reflex_sight_v21", -10, 140, weapon_type="auto_rifle")
        def geometry(value):
            if isinstance(value, dict):
                return {key: geometry(item) for key, item in value.items() if key != "move"}
            if isinstance(value, (tuple, list)):
                return [geometry(item) for item in value]
            return round(value, 9) if isinstance(value, float) else value
        for part in kit_parts:
            self.assertEqual(geometry(parts[part["id"]]), geometry(part), part["id"])
        imported = {part["id"] for part in kit_parts} | {
            "rail", "selector", "selector_r", "charging_handle", "mag_release", "takedown_pins"}
        original = {part["id"] for part in data["PARTS"]}
        self.assertEqual(original & parts.keys(), imported, "Nur deklarierte Kit-Gleichteile aus BASIC-01")
        self.assertFalse(any("move" in part for part in parts.values()))
        anchors = result["ANCHORS"]
        for name, point in kit_anchors.items():
            for key, value in point.items():
                self.assertEqual(geometry(anchors[name][key]), geometry(value), (name, key))
        expected = {"Socket_Hand": ("handle", [0, 0, 0]),
                    "Socket_Muzzle": ("face", [419, 61, 0]),
                    "Socket_Eye": ("sight_frame", [-59.6, 166, 0]),
                    "Socket_Sight": ("sight_body", [-9, 166, 0]),
                    "Socket_Reticle": ("sight_glass", [30.4, 166, 0]),
                    "Socket_Charge": ("charging_handle", [133, 77, 26.1]),
                    "Socket_MagWell": ("keel", [98, 39, 0])}
        for name, (part, at) in expected.items():
            self.assertEqual(anchors[name]["part"], part)
            for got, want in zip(anchors[name]["at"], at):
                self.assertAlmostEqual(got, want, msg=name)
        self.assertEqual(anchors["Socket_Eye"]["at"][1] - anchors["Socket_Muzzle"]["at"][1], 105)
        self.assertAlmostEqual(anchors["Socket_Reticle"]["at"][0] - anchors["Socket_Eye"]["at"][0], 90)
        self.assertEqual(result["POINTS"]["grip.charge"]["at"], anchors["Socket_Charge"]["at"])
        for group in (anchors, result["POINTS"]):
            self.assertTrue(all(point["part"] in parts for point in group.values()))

    def test_trestle_family_keeps_its_geometry_and_existing_anchors(self):
        from formgen.models.weapons import cairn, heron, swift, vesper
        # BT02 ab 0.26, BT03 ab 0.27. Bei BT03 wird das Z1 zusätzlich und vollständig
        # gegen die gepinnte BA03-Quelle geprüft, einschließlich ihrer plattformspezifischen Float-Werte.
        cases = (("BT02", vesper, "7729de5c3a94ec44c1d80dfbd3505c11cfff89b0d6d3fcab836b4381aba45d35",
                  "sight_frame", [-109.6, 161, 0]),
                 ("BT03", heron, "c0c6e9b816e594295acec2bd824991ee2f531c18fb8e15093ddc9b158d0086b1",
                  "scope_objective", [-18.0, 161, 0]),
                 ("BT04", cairn, "bd2d752f8ea5c4e2e59c3d7e365d76bb2164e1656410468e302d17ab1db99737",
                  "glass_tile", [-60, 118, 0]),
                 ("BT05", swift, "5db7f8d754ca498b21d13eebb67722facce20c81f2db3f5090632d64397f7a87",
                  "eye_tile", [-42, 100, 0]))
        for sid, design, digest, eye_part, eye_at in cases:
            with self.subTest(sid=sid):
                parts, anchors, points = design.build()
                frozen = [p for p in parts if p["asm"] != "sight"] if sid == "BT03" else parts
                geometry = [{k: v for k, v in p.items() if k not in ("de", "en", "func", "attach")} for p in frozen]
                self.assertEqual(hashlib.sha256(canonical(geometry)).hexdigest(), digest)
                self.assertEqual(anchors["Socket_Eye"]["part"], eye_part)
                self.assertEqual(anchors["Socket_Eye"]["at"], eye_at)
                ids = {p["id"] for p in parts}
                for group in (anchors, points):
                    self.assertTrue(all(point["part"] in ids for point in group.values()))
                _, exported = kit_model(sid)
                self.assertEqual(exported["META"]["id"], sid)
                self.assertEqual(exported["META"]["nick"], design.__name__.split(".")[-1].title())
                self.assertEqual(set(exported["ANCHORS"]), set(anchors))
                hand = anchors["Socket_Hand"]["at"]
                for name, point in anchors.items():
                    self.assertEqual(exported["ANCHORS"][name]["part"], point["part"])
                    self.assertEqual(exported["ANCHORS"][name]["at"],
                                     [point["at"][i] - hand[i] for i in range(3)])

    def test_vesper_is_a_static_pulse_rifle_with_its_own_shell(self):
        pilot, model = kit_model("BT02")
        self.assertEqual(model["META"]["nick"], "Vesper")
        self.assertEqual(model["META"]["id"], "BT02")
        self.assertEqual(set(model["POINTS"]), set(pilot["POINTS"]))
        self.assertFalse(model["ACTIONS"])
        parts = {p["id"]: p for p in model["PARTS"]}
        for i, key in enumerate(("pulse_mantle", "pulse_middle", "pulse_front")):
            self.assertIn("cuts", parts[key])
            for side in ("l", "r"):
                self.assertEqual(parts[f"pulse_line_{i}_{side}"]["mat"], "energy")
        self.assertEqual({p["mat"] for k, p in parts.items() if k.startswith("pulse_line_")}, {"energy"})
        self.assertEqual(len([k for k in parts if k.startswith("porcelain_")]), 6)

    def test_vesper_uses_complete_basic_02_sight_and_its_anchors(self):
        pilot, model = kit_model("BT02")
        source = {p["id"]: p for p in pilot["PARTS"] if p["asm"] == "sight"}
        actual = {p["id"]: p for p in model["PARTS"] if p["asm"] == "sight"}
        self.assertEqual(set(source), set(actual))
        self.assertFalse(any(p["id"].startswith("optic_") for p in model["PARTS"]))

        # Nutzerwechsel zum BA02-H4: vollständige Kit-Geometrie und Hierarchie
        # nach derselben starren Verschiebung für alle Teile vergleichen.
        def quantized(v):
            if isinstance(v, dict):
                return {k: quantized(n) for k, n in v.items()}
            if isinstance(v, (tuple, list)):
                return [quantized(n) for n in v]
            return round(v, 6) if isinstance(v, float) else v

        delta = [-28, -26, 0]  # Platzierung im exportierten Koordinatensystem von BT02
        for key, part in source.items():
            with self.subTest(part=key):
                for axis, shift in enumerate(delta[:2]):
                    generator._map(part, axis, lambda value: value + shift)
                self.assertEqual(quantized(actual[key]), quantized(part))
        for key in ("Socket_Eye", "Socket_Sight", "Socket_Reticle"):
            expected, anchor = pilot["ANCHORS"][key], model["ANCHORS"][key]
            self.assertEqual(anchor["part"], expected["part"])
            for v, base, shift in zip(anchor["at"], expected["at"], delta):
                self.assertAlmostEqual(v, base + shift)
        self.assertTrue(model["ANCHORS"]["Socket_Eye"]["std"])
        self.assertEqual(model["ANCHORS"]["Socket_Eye"]["sight_type"], "reflex")

    def test_heron_export_matches_scout_family_and_shows_both_beak_halves(self):
        pilot, model = kit_model("BT03")
        self.assertEqual(model["META"]["nick"], "Heron")
        self.assertEqual(model["META"]["type"], "scout_rifle")
        self.assertEqual(set(model["POINTS"]), set(pilot["POINTS"]))
        self.assertFalse(model["ACTIONS"])
        parts = {part["id"]: part for part in model["PARTS"]}
        self.assertTrue({"upper_beak", "lower_beak", "scope_tube", "scope_glass"} <= parts.keys())
        self.assertNotIn("sensor_body", parts)
        self.assertEqual(parts["upper_beak"]["asm"], "barrel")
        self.assertEqual(parts["lower_beak"]["asm"], "support")

    def test_heron_exports_every_original_scout_scope_part_and_socket(self):
        from formgen.models.weapons import heron
        pilot, exported = kit_model("BT03")
        parts, anchors, _ = heron.build(pilot)
        donor = {p["id"]: p for p in pilot["PARTS"] if p["asm"] == "sight"}
        self.assertEqual({p["id"]: p for p in parts if p["asm"] == "sight"}, donor)
        self.assertEqual({p["id"] for p in exported["PARTS"] if p["asm"] == "sight"}, donor.keys())
        self.assertEqual(len(donor), 18)
        hand = anchors["Socket_Hand"]["at"]
        for key in ("Socket_Eye", "Socket_Sight", "Socket_Reticle", "Socket_Objective"):
            original = pilot["ANCHORS"][key]
            actual = exported["ANCHORS"][key]
            self.assertEqual(actual["part"], original["part"])
            self.assertEqual(actual["at"], [v - off for v, off in zip(original["at"], hand)])
        self.assertTrue(exported["ANCHORS"]["Socket_Eye"]["std"])
        self.assertEqual(exported["ANCHORS"]["Socket_Eye"]["sight_type"], "scope")

    def test_extended_sidearms_use_their_own_static_silhouette(self):
        for sid, name, feature in (("BT04", "Cairn", "coin_l"), ("BT05", "Swift", "grip_cheek")):
            with self.subTest(sid=sid):
                pilot, model = kit_model(sid)
                self.assertEqual(model["META"]["id"], sid)
                self.assertEqual(model["META"]["nick"], name)
                self.assertEqual(set(model["POINTS"]), set(pilot["POINTS"]))
                self.assertFalse(model["ACTIONS"])
                self.assertIn(feature, {p["id"] for p in model["PARTS"]})

    def test_baseline_is_ballons_dataset_for_all_types(self):
        # Linie A = BALLONs Grundmodul bit für bit (Pilot bzw. Formstudie; inkl. r_in der Zielfernrohre, Baugruppen wie deklariert)
        for num in ballon.TYPES:
            with self.subTest(num=num):
                data, model = kit_model(f"BA{num}")
                for key in ("META", "PARTS", "ASSEMBLIES", "ANCHORS", "ACTIONS"):
                    self.assertEqual(canonical(model[key]), canonical(data[key] or {}), key)
                self.assertEqual(data["META"].get("variant") == "v2.1", num not in ("16", "17"))

    def test_variant_keeps_metadata_and_filters_actions(self):
        data, model = kit_model("BC08")                      # Pilot BASIC-08 führt `vent_rib` als Teil
        ids = {p["id"] for p in model["PARTS"]}
        dropped = {p["id"] for p in data["PARTS"]} - ids
        self.assertTrue(dropped and all(i.startswith("vent_") for i in dropped), dropped)
        original = {p["id"]: p for p in data["PARTS"]}
        for p in model["PARTS"]:
            self.assertNotIn("name_en", p)
            for key in ("de", "en", "func", "attach", "mat", "asm"):
                self.assertEqual(p.get(key), original[p["id"]].get(key))
        for action in model["ACTIONS"].values():
            self.assertLessEqual(set(action.get("keys") or {}), ids)
        self.assertEqual(model["ASSEMBLIES"], data["ASSEMBLIES"])

    def test_block_parts_carry_ballon_metadata(self):
        # Bausteinteile (Visier, Schaft S2, Leuchtlinie) kommen aus common.py mit de/en/func/attach – write_spec braucht sie
        for sid in ("BD01", "BF01", "BG02", "BH02"):
            with self.subTest(sid=sid):
                data, model = kit_model(sid)
                added = [p for p in model["PARTS"] if p["id"] not in {q["id"] for q in data["PARTS"]}]
                self.assertTrue(added)
                for p in added:
                    self.assertTrue(all(k in p for k in ("de", "en", "func", "attach", "mat", "asm", "shape")), p["id"])

    def test_only_r_in_adaptations_are_reverted(self):
        data = ballon.load(SNAP, "01")
        model = {"PARTS": [dict(p) for p in data["PARTS"]], "ANCHORS": data["ANCHORS"]}
        part = data["PARTS"][0]["id"]
        model["PARTS"][0]["mat"] = "sight_anod"                                              # Gestaltung der Variante (0.4)
        model["PARTS"][0]["r_in"] = 1.0
        run = {"notes": [{"part": part, "kind": "Annahme", "field": "mat", "ballon": data["PARTS"][0]["mat"], "v2": "sight_anod"},
                         {"part": part, "kind": "Annahme", "field": "r_in", "ballon": 2.5, "v2": 1.0},
                         {"kind": "Annahme", "field": "base", "ballon": "pilot", "v2": "standard"}]}
        out = asset.kit_model(data, model, run)
        self.assertEqual((out["PARTS"][0]["mat"], out["PARTS"][0]["r_in"]), ("sight_anod", 2.5))

    def test_undeclared_assembly_is_an_error(self):
        data = ballon.load(SNAP, "01")
        model = {"PARTS": [dict(data["PARTS"][0], asm="erfunden")], "ANCHORS": {}}
        with self.assertRaises(ValueError):
            asset.kit_model(data, model, {"notes": []})

    def test_variant_changes_geometry(self):
        _, a = kit_model("BA01")
        _, b = kit_model("BB01")
        self.assertNotEqual(canonical(a["PARTS"]), canonical(b["PARTS"]))
        self.assertGreater(b["ANCHORS"]["Socket_Muzzle"]["at"][0], a["ANCHORS"]["Socket_Muzzle"]["at"][0])


@unittest.skipIf(SNAP is None, REASON)
class PlanTests(unittest.TestCase):
    def plan(self, ids, **cfg):
        with mock.patch.object(asset, "blender_version", lambda binary: "Blender 5.2.2 LTS"):
            return asset.plan(asset.select(ids), KIT, SNAP, {**asset.DEFAULTS, **cfg})

    def test_keys_are_stable_and_per_sheet(self):
        a, b = self.plan(["BA01", "BB01"]), self.plan(["BA01", "BB01"])
        self.assertEqual([x.key for x in a], [x.key for x in b])
        self.assertNotEqual(a[0].key, a[1].key)
        self.assertEqual([x.output for x in a], ["assets/BA01.glb", "assets/BB01.glb"])
        self.assertEqual((a[0].inputs["module"], a[0].inputs["base"]), ("basic.pilot.w01_auto_rifle_v21", "v21"))
        self.assertEqual(self.plan(["BA16"])[0].inputs["module"], "basic.weapons.w16_sword")

    def test_key_follows_blender_version_and_code(self):
        base = self.plan(["BA01"])[0]
        with mock.patch.object(asset, "blender_version", lambda binary: "Blender 5.3.0"):
            other = asset.plan(asset.select(["BA01"]), KIT, SNAP, dict(asset.DEFAULTS))[0]
        self.assertNotEqual(base.key, other.key)
        self.assertEqual(base.source, other.source)
        asset.code_hash.cache_clear()
        with mock.patch.object(asset, "file_hash", lambda path: "x" if path.name == "asset_build.py" else "y"):
            changed = self.plan(["BA01"])[0]
        asset.code_hash.cache_clear()
        self.assertNotEqual(base.key, changed.key)

    def test_backend_hash_is_content_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy_dir = Path(tmp) / "kit"
            shutil.copytree(KIT / "basic", copy_dir / "basic")
            shutil.copytree(KIT / "tools", copy_dir / "tools")
            self.assertEqual(ballon_kit.backend_hash(copy_dir), ballon_kit.backend_hash(KIT))
            files = ballon_kit.closure_files(copy_dir, [copy_dir / f for f in ballon_kit.BACKEND])
            self.assertIn("basic/kit.py", files)
            self.assertIn("tools/bake_unity.py", files)
            with (copy_dir / "basic/kit.py").open("a") as stream:
                stream.write("\n# geändert\n")
            self.assertNotEqual(ballon_kit.backend_hash(copy_dir), ballon_kit.backend_hash(KIT))

    def test_newest_pilot(self):
        self.assertEqual(ballon_kit.pilot_file(KIT, "01").name, "w01_auto_rifle_v21.py")   # v21 vor v2
        self.assertIsNone(ballon_kit.pilot_file(KIT, "16"))                                 # Schwert ohne Pilot


class ToolSafetyTests(unittest.TestCase):
    def test_pilot_check_verdict_fails_on_any_gap(self):
        import sys
        sys.path.insert(0, str(asset.ROOT / "tools"))
        import kit_pilot_check as K
        good = {"built": True, "equal": True}
        self.assertEqual(K.verdict({"pilots": {"A": good, "B": good}}), 0)
        self.assertEqual(K.verdict({"pilots": {}}), 1)                                       # leere Auswahl
        self.assertEqual(K.verdict({"pilots": {"A": good, "B": {"built": True, "equal": False}}}), 1)
        self.assertEqual(K.verdict({"pilots": {"A": good, "B": {"built": True, "ego_json": "keine Referenz"}}}), 1)
        self.assertEqual(K.verdict({"pilots": {"A": {"built": False, "error": "x"}}}), 1)

    def test_unpack_refuses_foreign_folder_and_replaces_own(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            package_folder(src, package_manifest(2))
            zpath = Path(tmp) / "BX01.bake.zip"
            zpath.write_bytes(asset.zip_folder(src))
            dest = Path(tmp) / "pakete"
            foreign = dest / "BX01"
            foreign.mkdir(parents=True)
            (foreign / "notiz.txt").write_text("fremd")
            with self.assertRaises(RuntimeError):
                asset.unpack(zpath, dest)
            self.assertTrue((foreign / "notiz.txt").is_file())
            (foreign / "notiz.txt").unlink()
            (foreign / "BX01.package.json").write_text("{}")                                   # eigenes altes Paket
            asset.unpack(zpath, dest)
            self.assertEqual(json.loads((foreign / "BX01.package.json").read_text()), package_manifest(2))
            self.assertEqual(sorted(p.name for p in dest.iterdir()), ["BX01"])               # kein Temp-Rest

    def test_unpack_refuses_unreadable_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "pakete"
            (dest / "BX01").mkdir(parents=True)
            (dest / "BX01/BX01.package.json").write_text('{"alt": 1}')
            broken_points = with_model(POINTS={"grip.grip": {"at": "kaputt", "part": "grip"}})
            for manifest in ({"neu": 1}, package_manifest(3), dict(package_manifest(2), id="BX02"), None, [1, 2],
                             dict(package_manifest(2), weapon=None), with_model(ASSEMBLIES=[]), broken_points, "ohne Dateien"):
                src = Path(tmp) / "src"
                shutil.rmtree(src, ignore_errors=True)
                src.mkdir()
                if manifest == "ohne Dateien":                                  # gültiges Manifest, aber FBX/Texturen fehlen im ZIP
                    (src / "BX01.package.json").write_text(json.dumps(package_manifest(2)))
                elif isinstance(manifest, dict) and manifest.get("model") is broken_points["model"]:
                    package_folder(src, manifest)                              # Dateien vollständig, nur der Datensatz ist kaputt
                else:
                    (src / ("BX01.package.json" if manifest is not None else "liesmich.txt")).write_text(json.dumps(manifest))
                zpath = Path(tmp) / "BX01.bake.zip"
                zpath.write_bytes(asset.zip_folder(src))
                with self.subTest(manifest=manifest), self.assertRaises(asset.PackageError):
                    asset.unpack(zpath, dest)
                self.assertEqual(json.loads((dest / "BX01/BX01.package.json").read_text()), {"alt": 1})

    def test_unpack_keeps_old_package_on_broken_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "pakete"
            (dest / "BX01").mkdir(parents=True)
            (dest / "BX01/BX01.package.json").write_text('{"alt": 1}')
            broken = Path(tmp) / "BX01.bake.zip"
            broken.write_bytes(b"PK\x03\x04kaputt")
            with self.assertRaises(zipfile.BadZipFile):
                asset.unpack(broken, dest)
            self.assertEqual(json.loads((dest / "BX01/BX01.package.json").read_text()), {"alt": 1})
            self.assertEqual(sorted(p.name for p in dest.iterdir()), ["BX01"])               # kein Temp-Rest

    def test_zip_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a", Path(tmp) / "b"
            for folder, order in ((a, ("x", "y/z")), (b, ("y/z", "x"))):
                for name in order:
                    (folder / name).parent.mkdir(parents=True, exist_ok=True)
                    (folder / name).write_bytes(name.encode())
            os.utime(a / "x", (1, 1))
            self.assertEqual(asset.zip_folder(a), asset.zip_folder(b))
            self.assertEqual(zipfile.ZipFile(io.BytesIO(asset.zip_folder(a))).namelist(), ["x", "y/z"])

    def test_package_formats_one_and_two_are_readable(self):
        old = asset.read_package(package_manifest(1), "BX01")                  # 0.6: lesbar, Weltpunkte der Grundform
        self.assertIsNone(old["model"])
        self.assertIn("Grundform", old["points"])
        new = asset.read_package(package_manifest(2), "BX01")
        self.assertEqual(new["model"]["POINTS"]["grip.grip"]["part"], "grip")
        self.assertIn("POINTS", new["points"])
        self.assertEqual(asset.BAKE, 2)                                         # geschrieben wird 2 (eigener Cacheschlüssel)
        for bad in (dict(package_manifest(2), model=None),
                    {**package_manifest(2), "model": {k: v for k, v in package_manifest(2)["model"].items() if k != "POINTS"}},
                    {**package_manifest(2), "model": {**package_manifest(2)["model"],
                                                      "POINTS": {"grip.grip": {"at": [0, 0, 0], "part": "fehlt"}}}},
                    dict(package_manifest(1), format="anders"),
                    dict(package_manifest(2), weapon=None, ego_profile_error="BASIC-16 ohne Ego-Klasse"),   # Richter 0.7 Nr. 1
                    dict(package_manifest(1), weapon=None),
                    with_model(PARTS=[]), with_model(PARTS={}), with_model(META={}),
                    # Richter 0.7 Runde 3: Anker und Weltpunkte vollständig prüfen
                    with_model(POINTS={"grip.grip": {"part": "grip"}}),
                    with_model(POINTS={"grip.grip": {"at": "kaputt", "part": "grip"}}),
                    with_model(POINTS={"grip.grip": {"at": [0, 0], "part": "grip"}}),
                    with_model(POINTS={"grip.grip": {"at": [0, float("nan"), 0], "part": "grip"}}),
                    with_model(POINTS={"grip.grip": {"at": [0, True, 0], "part": "grip"}}),
                    with_model(POINTS={"grip.grip": None}),
                    with_model(ANCHORS={"Socket_Hand": {"at": [0, 0, 0], "part": "fehlt"}}),
                    with_model(PARTS=[{"id": "grip", "asm": "grip"}, {"id": "grip", "asm": "grip"}]),
                    with_model(PARTS=[{"id": "grip", "asm": "anders"}]),
                    with_model(ACTIONS=[]), "kein Objekt"):
            with self.subTest(bad=bad), self.assertRaises(asset.PackageError):
                asset.read_package(bad, "BX01")

    def test_bake_needs_gpu_lock(self):
        self.assertTrue(asset.gpu_locked({"CE_HEAVY_HELD": "blender,1"}))
        self.assertTrue(asset.gpu_locked({"CE_HEAVY_HELD": "gpu"}))
        self.assertFalse(asset.gpu_locked({"CE_HEAVY_HELD": "blender"}))
        self.assertFalse(asset.gpu_locked({}))
        art = asset.Artifact("BX01", "asset_bake", "s", {"blender": "B"}, {}, "assets/BX01.bake.zip", "", {"blender": "b", "gpu": True})
        with mock.patch.object(asset, "blender_version", lambda binary: "B"), mock.patch.dict(os.environ, {"CE_HEAVY_HELD": ""}), \
                mock.patch.object(asset, "run_blender") as run:
            with self.assertRaises(RuntimeError):
                asset.build_bake(art)
            run.assert_not_called()


@unittest.skipIf(SNAP is None, REASON)
class AssetCacheTests(unittest.TestCase):
    """Stufe asset in der Pipeline: Treffer/Fehltreffer nur aus Inhalten; Blender durch eine Attrappe ersetzt."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out, self.cache = Path(self.tmp.name) / "out", Path(self.tmp.name) / "cache"
        self.calls = []
        patches = [mock.patch.object(asset, "blender_version", lambda binary: "Blender 5.2.2 LTS"),
                   mock.patch.object(asset, "run_blender", self.blender)]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def blender(self, job, binary):
        self.calls.append((job["id"], bool(job.get("package"))))
        if job.get("package"):
            Path(job["out"], f"{job['id']}.package.json").write_text(json.dumps({"skin": job["skin"], "atlas": job["atlas"]}))
        else:
            Path(job["out"], f"{job['id']}.glb").write_bytes(fake_glb({"id": job["id"], "model": canonical(job["model"]).decode()}))
        return ""

    def run_pipeline(self, ids, entries=None, **kw):
        selection = pipeline.select(ids, entries=entries)
        res, _ = pipeline.run(selection, self.out, self.cache, ("geometry", "asset"), log=lambda _: 0, **kw)
        return {r.output: r.built for r in res if r.output.startswith("assets/")}

    def test_second_run_hits_and_parameter_change_misses_only_that_sheet(self):
        first = self.run_pipeline(["BA01", "BB01"])
        self.assertEqual(first, {"assets/BA01.glb": True, "assets/BB01.glb": True})
        self.assertEqual(self.run_pipeline(["BA01", "BB01"]), {"assets/BA01.glb": False, "assets/BB01.glb": False})
        entries = variants.load()
        next(v for v in entries if v["letter"] == "B")["params"]["front"] = 1.2
        self.assertEqual(self.run_pipeline(["BA01", "BB01"], entries), {"assets/BA01.glb": False, "assets/BB01.glb": True})
        index = json.loads((self.out / "assets/index.json").read_text())
        self.assertEqual(set(index["assets"]), {"BA01", "BB01"})
        self.assertEqual(index["assets"]["BA01"]["base"], "v21")
        self.assertEqual([c for c in self.calls if c[1]], [])                                 # ohne --bake kein Bake

    def test_bake_only_on_request_and_cached(self):
        with mock.patch.dict(os.environ, {"CE_HEAVY_HELD": "1"}):
            built = self.run_pipeline(["BA01", "BD01"], bake=["BD01"])
            again = self.run_pipeline(["BA01", "BD01"], bake=["BD01"])
        self.assertEqual(built, {"assets/BA01.glb": True, "assets/BD01.glb": True, "assets/BD01.bake.zip": True})
        self.assertEqual(set(again.values()), {False})
        self.assertEqual(sorted(c for c in self.calls if c[1]), [("BD01", True)])
        index = json.loads((self.out / "assets/index.json").read_text())
        self.assertEqual(index["assets"]["BD01"]["bake"]["skin"], "eloxal")
        self.assertNotIn("bake", index["assets"]["BA01"])
        with zipfile.ZipFile(self.out / "assets/BD01.bake.zip") as archive:
            self.assertEqual(json.loads(archive.read("BD01.package.json"))["atlas"], 4096)

    def test_other_skin_rebuilds_the_glb(self):
        self.run_pipeline(["BD01"])
        self.assertEqual(self.run_pipeline(["BD01"]), {"assets/BD01.glb": False})
        entries = variants.load()
        next(v for v in entries if v["letter"] == "D")["skin"] = "nacht"
        self.assertEqual(self.run_pipeline(["BD01"], entries), {"assets/BD01.glb": True})

    def test_index_drops_bake_of_older_glb_or_other_skin(self):
        with mock.patch.dict(os.environ, {"CE_HEAVY_HELD": "1"}):
            self.run_pipeline(["BD01"], bake=["BD01"])
        self.assertIn("bake", json.loads((self.out / "assets/index.json").read_text())["assets"]["BD01"])
        entries = variants.load()
        next(v for v in entries if v["letter"] == "D")["skin"] = "nacht"                    # gleiche Form, anderer Skin
        self.run_pipeline(["BD01"], entries)
        self.assertNotIn("bake", json.loads((self.out / "assets/index.json").read_text())["assets"]["BD01"])
        with mock.patch.dict(os.environ, {"CE_HEAVY_HELD": "1"}):
            self.run_pipeline(["BD01"], bake=["BD01"])
        asset.code_hash.cache_clear()                                                         # anderer Asset-Code → neue GLB
        try:
            with mock.patch.object(asset, "file_hash", lambda path, real=asset.file_hash: "x" if Path(path).name == "asset_build.py"
                                   else real(path)):
                self.run_pipeline(["BD01"])
        finally:
            asset.code_hash.cache_clear()
        self.assertNotIn("bake", json.loads((self.out / "assets/index.json").read_text())["assets"]["BD01"])

    def test_failed_bake_after_new_glb_leaves_no_stale_index(self):
        with mock.patch.dict(os.environ, {"CE_HEAVY_HELD": "1"}):
            self.run_pipeline(["BD01"], bake=["BD01"])
        entries = variants.load()
        next(v for v in entries if v["letter"] == "D")["params"]["front"] = 1.2          # neue Geometrie → neue GLB
        with mock.patch.dict(os.environ, {"CE_HEAVY_HELD": ""}), self.assertRaises(RuntimeError):
            self.run_pipeline(["BD01"], entries, bake=["BD01"])                        # Bake scheitert (keine GPU-Sperre)
        entry = json.loads((self.out / "assets/index.json").read_text())["assets"]["BD01"]
        self.assertEqual(entry["sha256"], asset.file_hash(self.out / "assets/BD01.glb"))   # Index zeigt die neue GLB
        self.assertNotIn("bake", entry)                                                       # und keinen alten Bake

    def test_failure_in_batch_leaves_index_true_to_files(self):
        # Richter 0.6 Runde 3: zwei Blätter mit Bake, beide GLB neu; das erste gelingt, das zweite scheitert
        with mock.patch.dict(os.environ, {"CE_HEAVY_HELD": "1"}):
            self.run_pipeline(["BA01", "BD01"], bake=["BA01", "BD01"])
        entries = variants.load()
        for v in entries:
            if v["letter"] in "AD":
                v["params"]["front"] = 1.2
        fake = self.blender

        def failing(job, binary):
            if job["id"] == "BD01":
                raise RuntimeError("Blender abgestürzt")
            return fake(job, binary)
        with mock.patch.object(asset, "run_blender", failing), self.assertRaises(RuntimeError):
            self.run_pipeline(["BA01", "BD01"], entries)
        index = json.loads((self.out / "assets/index.json").read_text())["assets"]
        self.assertNotIn("BA01", index)                                    # ersetzte GLB ohne passenden Eintrag: entfällt
        self.assertEqual(index["BD01"]["sha256"], asset.file_hash(self.out / "assets/BD01.glb"))   # alte GLB blieb
        self.assertEqual(index["BD01"]["bake"]["sha256"], asset.file_hash(self.out / "assets/BD01.bake.zip"))
        for sid, entry in index.items():
            self.assertEqual(entry["sha256"], asset.file_hash(self.out / "assets" / entry["glb"]), sid)
        self.run_pipeline(["BA01", "BD01"], entries)                       # nächster erfolgreicher Lauf ergänzt wieder
        index = json.loads((self.out / "assets/index.json").read_text())["assets"]
        self.assertEqual(set(index), {"BA01", "BD01"})
        self.assertFalse(any("bake" in e for e in index.values()))         # Bakes gehörten zu den alten GLB

    def test_reconcile_drops_entries_without_matching_files(self):
        folder = self.out / "assets"
        folder.mkdir(parents=True)
        (folder / "BA01.glb").write_bytes(b"neu")
        (folder / "BB01.glb").write_bytes(b"gleich")
        (folder / "BB01.bake.zip").write_bytes(b"zip")
        sha = asset.file_hash
        assets = {"BA01": {"glb": "BA01.glb", "sha256": "alt", "key": "k"},
                  "BB01": {"glb": "BB01.glb", "sha256": sha(folder / "BB01.glb"), "key": "k",
                           "bake": {"zip": "BB01.bake.zip", "sha256": sha(folder / "BB01.bake.zip"), "glb_key": "anders"}},
                  "BC01": {"glb": "BC01.glb", "sha256": "x", "key": "k"}}
        kept = asset.reconcile(self.out, assets)
        self.assertEqual(set(kept), {"BB01"})
        self.assertNotIn("bake", kept["BB01"])

    def test_bake_key_follows_device_and_atlas_not_source(self):
        glb = asset.plan(asset.select(["BA01"]), KIT, SNAP, dict(asset.DEFAULTS))
        gpu = asset.bake_plan(glb, dict(asset.DEFAULTS))[0]
        cpu = asset.bake_plan(glb, dict(asset.DEFAULTS), gpu=False)[0]
        small = asset.bake_plan(glb, dict(asset.DEFAULTS, atlas=1024))[0]
        self.assertEqual({gpu.source, cpu.source, small.source}, {glb[0].source})
        self.assertEqual(len({gpu.key, cpu.key, small.key, glb[0].key}), 4)


@unittest.skipUnless((OUT / "assets/BA01.glb").is_file() and PARITY.is_file(),
                     "Ergebnisse fehlen (Mac: ce lock blender -- python -m formgen.pipeline --stages geometry,asset; "
                     "tools/line_a_parity.py)")
class BuiltAssetTests(unittest.TestCase):
    def test_line_a_byte_equal_to_ballon_rebuild(self):
        # Linie A jedes Typs bytegleich zu BALLONs eigenem Bau des unveränderten Grundmoduls am Pin (tools/line_a_parity.py)
        report = json.loads(PARITY.read_text())
        self.assertEqual(report["ballon_commit"], ballon.config()["commit"])
        self.assertEqual(sorted(report["types"]), list(ballon.TYPES))
        for num, entry in report["types"].items():
            with self.subTest(num=num):
                self.assertTrue(entry["bytes_equal"] and entry["equal"] and entry["spec_equal"], entry)
                self.assertEqual(asset.file_hash(OUT / f"assets/BA{num}.glb"), asset.file_hash(Path(entry["rebuild"])))

    def test_moved_anchor_is_detected(self):
        import struct
        import sys
        sys.path.insert(0, str(asset.ROOT / "tools"))
        import ballon_compare
        data = (OUT / "assets/BA01.glb").read_bytes()
        n = struct.unpack_from("<I", data, 12)[0]
        g = json.loads(data[20:20 + n])
        node = next(x for x in g["nodes"] if x.get("name") == "Socket_Muzzle")
        node["translation"] = [v + (0.002 if i == 1 else 0.0) for i, v in enumerate(node.get("translation", [0, 0, 0]))]
        chunk = json.dumps(g).encode()
        chunk += b" " * (-len(chunk) % 4)
        rest = data[20 + n:]
        body = struct.pack("<II", len(chunk), 0x4E4F534A) + chunk + rest
        with tempfile.TemporaryDirectory() as tmp:
            moved = Path(tmp) / "moved.glb"
            moved.write_bytes(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)
            r = ballon_compare.compare_asset(moved, OUT / "assets/BA01.glb")
        self.assertTrue(r["meshes_equal"] and r["positions_equal"])
        self.assertFalse(r["nodes_equal"])
        self.assertEqual(r["nodes_differing"], ["Socket_Muzzle"])
        self.assertFalse(r["equal"])

    def test_swapped_mesh_geometry_is_detected(self):
        # zwei Netze gleicher Dreieckszahl und gleichen Materials tauschen ihre Geometrie: global gleich, je Netz nicht
        import struct
        import sys
        sys.path.insert(0, str(asset.ROOT / "tools"))
        import ballon_compare
        data = (OUT / "assets/BA01.glb").read_bytes()
        n = struct.unpack_from("<I", data, 12)[0]
        g = json.loads(data[20:20 + n])
        nodes = {x["name"]: x for x in g["nodes"] if "mesh" in x}
        info = asset.glb_info(OUT / "assets/BA01.glb")["meshes"]
        pairs = {}
        for name, prims in info.items():
            pairs.setdefault((prims[0]["triangles"], prims[0]["material"], len(prims)), []).append(name)
        a, b = next(v for v in pairs.values() if len(v) >= 2)[:2]
        a_mesh, a_tr = nodes[a]["mesh"], {k: nodes[a].get(k) for k in ("translation", "rotation", "scale")}
        nodes[a]["mesh"], nodes[b]["mesh"] = nodes[b]["mesh"], a_mesh
        for k in ("translation", "rotation", "scale"):
            nodes[a][k], nodes[b][k] = nodes[b].get(k), a_tr[k]
            for x in (nodes[a], nodes[b]):
                if x[k] is None:
                    del x[k]
        chunk = json.dumps(g).encode()
        chunk += b" " * (-len(chunk) % 4)
        body = struct.pack("<II", len(chunk), 0x4E4F534A) + chunk + data[20 + n:]
        with tempfile.TemporaryDirectory() as tmp:
            swapped = Path(tmp) / "swapped.glb"
            swapped.write_bytes(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)
            r = ballon_compare.compare_asset(swapped, OUT / "assets/BA01.glb")
        self.assertTrue(r["meshes_equal"], (a, b))
        self.assertFalse(r["positions_equal"])
        self.assertFalse(r["equal"])

    def test_asset_reference_follows_glb_dir(self):
        import sys
        sys.path.insert(0, str(asset.ROOT / "tools"))
        import ballon_compare
        with tempfile.TemporaryDirectory() as tmp:
            ref = Path(tmp) / "BASIC-01-v2.1"                                                # Linie A steht auf dem Piloten
            ref.mkdir()
            shutil.copyfile(OUT / "assets/BA01.glb", ref / "BASIC-01-v2.1.glb")
            report = Path(tmp) / "r.json"
            code = ballon_compare.main(["--asset", "BA01", "--glb-dir", tmp, "--out", str(report)])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(report.read_text())["BA01"]["ballon_glb"], str(ref / "BASIC-01-v2.1.glb"))

    def test_index_matches_files(self):
        index = json.loads((OUT / "assets/index.json").read_text())
        self.assertEqual(index["format_version"], 2)
        for sid, entry in index["assets"].items():
            glb = OUT / "assets" / entry["glb"]
            self.assertEqual(asset.file_hash(glb), entry["sha256"], sid)
            self.assertEqual(asset.glb_info(glb)["triangles"], entry["triangles"], sid)
            if "bake" in entry:
                self.assertEqual(asset.file_hash(OUT / "assets" / entry["bake"]["zip"]), entry["bake"]["sha256"], sid)


if __name__ == "__main__":
    unittest.main()
