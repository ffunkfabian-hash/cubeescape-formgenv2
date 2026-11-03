"""Waffen-Assets über BALLONs Blender-Kit: 0.5 „Forge“ (Machbarkeitsnachweis), 0.6 „Hangar“ (Stufe asset, Bake, Piloten).

Ohne Blender: Kitmodell aus `generator.vary`, Schlüssel, Kit-Schnappschuss, Asset-Cache Treffer/Fehltreffer (Blender ersetzt),
Bake-Schlüssel, GPU-Sperre, ZIP. Mit vorhandenen Ergebnissen (Mac, nach `pipeline` und `tools/line_a_parity.py`): Linie A
bytegleich zu BALLONs Neubau am Pin.
"""
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

from formgen import asset, ballon, ballon_kit, generator, pipeline, variants
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


@unittest.skipIf(SNAP is None, REASON)
class KitModelTests(unittest.TestCase):
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

    def test_index_drops_bake_of_older_glb_or_other_skin(self):
        with mock.patch.dict(os.environ, {"CE_HEAVY_HELD": "1"}):
            self.run_pipeline(["BD01"], bake=["BD01"])
        self.assertIn("bake", json.loads((self.out / "assets/index.json").read_text())["assets"]["BD01"])
        entries = variants.load()
        next(v for v in entries if v["letter"] == "D")["skin"] = "nacht"                    # gleiche GLB, anderer Skin
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
